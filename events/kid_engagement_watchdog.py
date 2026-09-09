"""
events/kid_engagement_watchdog.py - Kid Proactive Engagement & Gentle Sleep Engine.
Ensures AI stays in active 'WAKEUP' state during child pauses, nudging periodically with
interactive prompts, fun animal sounds, rhymes, and curiosity challenges.
If child remains completely inactive after prolonged silence (~60s), transitions to gentle 'SLEEP' mode.
"""

import asyncio
import json
import logging
import random
from typing import Optional, Any, List

from livekit import rtc
from events.base import CallEventSession
from events.data_channel import CaptionBroadcaster

logger = logging.getLogger("events.watchdog")


class KidEngagementWatchdog:
    """
    Monitors child interaction silence during voice calls.
    Keeps AI actively engaged ('WAKEUP' mode) by proactively speaking if the child pauses.
    Gracefully transitions to 'SLEEP' mode and ends call after long persistent silence.
    """

    # Staged silence timeouts (seconds to wait after AI speech ends before nudging)
    INITIAL_SILENCE_DELAY = 8.5    # Nudge 1: 8.5s after agent stops speaking
    FOLLOWUP_SILENCE_DELAY = 10.5  # Nudges 2-4: 10.5s between consecutive nudges
    MAX_UNANSWERED_NUDGES = 4     # At 5th silence event (~55-60s total silence) -> Enter Sleep mode

    def __init__(
        self,
        agent: Any,
        room: rtc.Room,
        session: CallEventSession,
        tools_ctx: Optional[Any] = None,
        known_name: str = "",
    ):
        self.agent = agent
        self.room = room
        self.session = session
        self.tools_ctx = tools_ctx
        self.known_name = known_name or getattr(session, "clean_caller_id", "")
        if self.known_name.isdigit() or len(self.known_name) > 15:
            self.known_name = ""  # If it's a raw UUID/phone, don't use as name

        self.consecutive_silence_count: int = 0
        self.sleep_farewell_delay: float = 2.2
        self._watchdog_task: Optional[asyncio.Task] = None
        self._is_agent_speaking: bool = False
        self._is_user_speaking: bool = False
        self._is_sleeping: bool = False
        self._is_stopped: bool = False

    def get_child_salutation(self) -> str:
        """Returns personalized salutation."""
        if self.known_name:
            return f"{self.known_name} superstar"
        return "superstar"

    def cancel_timer(self):
        """Cancels any pending silence countdown."""
        if self._watchdog_task and not self._watchdog_task.done():
            self._watchdog_task.cancel()
        self._watchdog_task = None

    def on_user_started_speaking(self):
        """Called when child begins speaking."""
        self._is_user_speaking = True
        self.cancel_timer()
        logger.debug("🗣️ [Watchdog] Child started speaking. Watchdog paused.")

    def on_user_speech_committed(self):
        """Called when child's speech turn is committed."""
        self._is_user_speaking = False
        self.consecutive_silence_count = 0  # Child responded! Reset streak
        self.cancel_timer()
        logger.info("👶 [Watchdog] Child speech received. Engagement streak reset to 0.")

    def on_user_interaction(self, source: str = "ui"):
        """Called when child taps an option, button, or game card."""
        self.consecutive_silence_count = 0  # Child interacted! Reset streak
        self.cancel_timer()
        logger.info(f"👆 [Watchdog] Child {source} interaction received. Engagement streak reset to 0.")

    def on_agent_started_speaking(self):
        """Called when AI begins speaking."""
        self._is_agent_speaking = True
        self.cancel_timer()
        logger.debug("🔊 [Watchdog] AI started speaking. Watchdog paused.")

    def on_agent_stopped_speaking(self):
        """Called when AI finishes speaking. Arms silence countdown."""
        self._is_agent_speaking = False
        if self._is_stopped or self._is_sleeping or getattr(self.session, "disconnect_pending", False):
            return

        # Check if an active interactive bottom sheet quiz is already handling inactivity
        if self._is_quiz_handling_inactivity():
            logger.debug("📋 [Watchdog] Visual quiz sheet active. Deferring to quiz inactivity handler.")
            return

        self.arm_silence_timer()

    def _is_quiz_handling_inactivity(self) -> bool:
        """Checks if a visual quiz sheet is actively open and managing child thinking time."""
        if self.tools_ctx and hasattr(self.tools_ctx, "session_data"):
            quiz = self.tools_ctx.session_data.get("active_visual_quiz")
            if quiz and not quiz.get("answered"):
                return True
        return False

    def arm_silence_timer(self):
        """Schedules the next proactive engagement nudge."""
        self.cancel_timer()
        if self._is_stopped or self._is_sleeping or getattr(self.session, "disconnect_pending", False):
            return

        delay = self.INITIAL_SILENCE_DELAY if self.consecutive_silence_count == 0 else self.FOLLOWUP_SILENCE_DELAY

        async def _silence_countdown():
            try:
                await asyncio.sleep(delay)
                if self._is_stopped or self._is_sleeping or getattr(self.session, "disconnect_pending", False):
                    return
                if self._is_user_speaking or self._is_agent_speaking:
                    return
                if self._is_quiz_handling_inactivity():
                    return

                await self._trigger_proactive_nudge()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"⚠️ [Watchdog] Silence countdown notice: {e}")

        self._watchdog_task = asyncio.create_task(_silence_countdown())
        logger.debug(f"⏱️ [Watchdog] Silence timer armed for {delay}s (Streak: {self.consecutive_silence_count}).")

    async def _trigger_proactive_nudge(self):
        """Fires the appropriate engagement nudge or enters sleep mode."""
        self.consecutive_silence_count += 1
        name = self.get_child_salutation()

        # Check if max unanswered nudges reached -> ENTER SLEEP MODE
        if self.consecutive_silence_count > self.MAX_UNANSWERED_NUDGES:
            await self._enter_sleep_mode()
            return

        logger.info(f"✨ [Watchdog] Proactive Wakeup Nudge #{self.consecutive_silence_count} triggered for {name}.")
        prompt_text = self._build_nudge_prompt(self.consecutive_silence_count, name)

        try:
            # Broadcast subtitle caption
            if self.room:
                asyncio.create_task(CaptionBroadcaster.broadcast(self.room, "assistant", prompt_text))

            # Speak nudge with barge-in allowed so child can interrupt at any moment!
            if self.agent and hasattr(self.agent, "say"):
                await self.agent.say(prompt_text, allow_interruptions=True)
        except Exception as e:
            logger.warning(f"⚠️ [Watchdog] Error speaking proactive nudge: {e}")

    def _build_nudge_prompt(self, stage: int, name: str) -> str:
        """Generates age-appropriate, playful Hinglish nudges for young children."""
        stage_1_prompts = [
            f"Arey {name}! Kahan kho gaye champ? Chalo mujhe batao billi kaise bolti hai? Meow Meow!",
            f"Arey waah {name}! Chalo ek mazedaar sher ki aawaz nikalein! Sher kaise dahadta hai? Grrrr!",
            f"Arey {name}! Kya aap sun rahe ho? Chalo batao doggy kaise bolta hai? Bhow Bhow!",
            f"Superstar {name}! Chalo mujhe batao mendhak kaise bolta hai? Tring Tring ya Tarter?",
        ]

        stage_2_prompts = [
            f"Acha {name}, jaldi se batao 'A' for kya hota hai? Apple ya Ball?",
            f"Chalo mere sath 1 2 3 bolte hain! Ek, do, teen... ab aap bolo!",
            f"Batao champ, Machhli kahan rehti hai? Paani me ya hawa me?",
            f"Arey waah {name}! 'C' for Cat hota hai ya Cow? Dono hi hote hain na!",
        ]

        stage_3_prompts = [
            f"Chalo ek mast Chanda mama ki kavita gaate hain! Chanda mama door ke, puye pakaye boor ke!",
            f"Machhli jal ki rani hai, jeevan uska paani hai! Haath lagao toh darr jayegi, bahar nikalo toh marr jayegi!",
            f"Titli udi, bus pe chadi, seat na mili toh rone lagi! Driver ne bola aaja mere paas, titli boli na baba na!",
        ]

        stage_4_prompts = [
            f"Champ {name}! Kya aapko drawing karna hai ya mere sath koi mazedaar game khelna hai?",
            f"Arey superstar, Puruva AI aapka wait kar rahi hai! Kuch bolo na pyare dost!",
            f"Agar aap sun rahe ho {name}, toh jaldi se bolo 'Haan Didi'!",
        ]

        if stage == 1:
            return random.choice(stage_1_prompts)
        elif stage == 2:
            return random.choice(stage_2_prompts)
        elif stage == 3:
            return random.choice(stage_3_prompts)
        else:
            return random.choice(stage_4_prompts)

    async def _enter_sleep_mode(self):
        """
        Transitions AI into SLEEP mode when child does not respond after ~60s of total silence.
        Plays a sweet, warm goodbye and gracefully ends the call.
        """
        if self._is_sleeping:
            return
        self._is_sleeping = True
        self.session.disconnect_pending = True
        name = self.get_child_salutation()

        logger.info(f"🌙 [Watchdog] Child inactive after {self.consecutive_silence_count} nudges. Entering SLEEP mode...")

        sleep_speech = (
            f"Lagta hai mere pyare {name} ko neend aa rahi hai ya aap khelne chale gaye! "
            f"Koi baat nahi champion, ab aap aaram karo. Jab bhi mann kare Puruva AI ko call karna! "
            f"Bye-bye champ, sweet dreams!"
        )

        try:
            # Broadcast final caption
            if self.room:
                asyncio.create_task(CaptionBroadcaster.broadcast(self.room, "assistant", sleep_speech))

            # Speak farewell without interruption
            if self.agent and hasattr(self.agent, "say"):
                await self.agent.say(sleep_speech, allow_interruptions=False)

            # Wait for TTS playback to wrap up on device
            await asyncio.sleep(self.sleep_farewell_delay)

            # Broadcast call_ended data channel packet
            if self.room and self.room.local_participant:
                payload = json.dumps({"type": "call_ended", "reason": "inactivity_sleep"}).encode("utf-8")
                await self.room.local_participant.publish_data(payload, reliable=True)
                logger.info("📡 [Watchdog] Published call_ended packet (reason: inactivity_sleep)")

            # Gracefully disconnect room
            if self.room:
                await self.room.disconnect()
                logger.info("🚪 [Watchdog] Room disconnected gracefully after sleep farewell.")
        except Exception as e:
            logger.warning(f"⚠️ [Watchdog] Error during sleep farewell: {e}")

    def stop(self):
        """Stops the watchdog completely upon call termination."""
        self._is_stopped = True
        self.cancel_timer()
        logger.debug("🛑 [Watchdog] KidEngagementWatchdog stopped.")
