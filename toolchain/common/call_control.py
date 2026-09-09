"""
call_control.py - Universal Call Control Tools (Graceful Disconnect, Language, Speed, Repeat, Pause).
"""

import logging
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.common.call_control")


class CallControlToolsMixin:
    """Provides universal call control tools to any FunctionContext."""

    @llm.ai_callable(description="Disconnect and end the phone call when caller says 'call disconnect', 'call kaat do', 'hang up', 'phone rakh do', 'disconnect ho jao', 'bye bye', or asks to end the call.")
    async def disconnect_call(
        self,
        reason: Annotated[str, "Reason for disconnecting (e.g. 'user_requested_disconnect', 'caller_requested_hangup')"] = "user_requested_disconnect",
    ) -> str:
        logger.info(f"🛑 [Tool] disconnect_call invoked: reason='{reason}'")
        self.record_tool_invocation("disconnect_call", {"reason": reason})
        self.request_disconnect(reason=reason)

        # Broadcast call_ended packet immediately so Flutter app & Web Admin immediately terminate
        if hasattr(self, "room") and self.room:
            try:
                import json
                import asyncio
                payload = json.dumps({"type": "call_ended", "reason": reason}).encode('utf-8')
                asyncio.create_task(self.room.local_participant.publish_data(payload, reliable=True))
                logger.info("[Tool] Published 'call_ended' data packet to LiveKit room.")
            except Exception as e:
                logger.warning(f"[Tool] Failed to publish call_ended packet: {e}")

        farewell_phrases = {
            "hindi": "Aapse baat karke bahut achha laga. Call disconnect ki ja rahi hai, Namaste!",
            "english": "It was wonderful speaking with you. Disconnecting the call now, goodbye!",
            "hinglish": "Aapse baat karke achha laga! Call disconnect kar rahi hoon, bye bye!"
        }
        return farewell_phrases.get(getattr(self, "current_language", "hinglish"), farewell_phrases["hinglish"])

    # Retained as internal helper methods without @llm.ai_callable to save ~800 input tokens per turn on Groq Free Tier
    async def repeat_last_message(self) -> str:
        logger.info("🔁 [Tool] repeat_last_message invoked")
        self.record_tool_invocation("repeat_last_message", {})
        last_turn = self.session_data.get("last_assistant_text")
        if last_turn:
            return f"Ji bilkul, maine kaha tha: {last_turn}"
        return "Ji main repeat kar deti hoon. Aap batayiye main aapki kaise madad kar sakti hoon?"

    async def set_call_language(
        self,
        language: Annotated[str, "Target language: 'hindi', 'english', or 'hinglish'"],
    ) -> str:
        clean_lang = language.strip().lower()
        if "eng" in clean_lang:
            clean_lang = "english"
        elif "hin" in clean_lang and "gl" not in clean_lang:
            clean_lang = "hindi"
        else:
            clean_lang = "hinglish"

        logger.info(f"🌐 [Tool] set_call_language: switched to '{clean_lang}'")
        self.record_tool_invocation("set_call_language", {"language": clean_lang})
        self.current_language = clean_lang

        if clean_lang == "hindi":
            return "Ji bilkul, ab main aapse shuddh aur saral Hindi me baat karungi. Batayiye kaise madad karoon?"
        elif clean_lang == "english":
            return "Sure! I will continue our conversation in clear English now. How can I assist you?"
        return "Bilkul, ab hum natural Hinglish me baat karenge. Batayiye aage kya discuss karna hai?"

    async def adjust_speaking_speed(
        self,
        speed: Annotated[str, "Speed preference: 'fast' (+20%), 'normal' (+0%), or 'slow' (-15%)"] = "normal",
    ) -> str:
        clean_speed = speed.lower().strip()
        logger.info(f"⚡ [Tool] adjust_speaking_speed: '{clean_speed}'")
        self.record_tool_invocation("adjust_speaking_speed", {"speed": clean_speed})

        if "fast" in clean_speed or "jaldi" in clean_speed:
            self.current_rate = "+20%"
            return "Theek hai, ab se main thoda tez bolungi. Aage batayiye!"
        elif "slow" in clean_speed or "dheere" in clean_speed:
            self.current_rate = "-15%"
            return "Theek hai ji, ab main aaram se aur dheere bolungi taaki aap aasaani se samajh sakein."
        else:
            self.current_rate = "+0%"
            return "Speaking speed normal pace par set ho gayi hai."

    async def mute_pause_assistant(
        self,
        duration_seconds: Annotated[int, "Pause duration in seconds (e.g. 15, 30, 60)"] = 30,
    ) -> str:
        logger.info(f"⏸️ [Tool] mute_pause_assistant: holding for {duration_seconds}s")
        self.record_tool_invocation("mute_pause_assistant", {"duration_seconds": duration_seconds})
        return f"Ji bilkul, main {duration_seconds} seconds ke liye hold par hoon. Jab aap ready hon, bas 'Hello' boliyega!"

    async def schedule_callback_request(
        self,
        delay_minutes: Annotated[int, "Delay in minutes before calling back (e.g. 10, 15, 30, 60)"] = 15,
        preferred_time: Annotated[str, "Time or description requested by user (e.g. '15 minute baad', 'shaam ko', 'kal subah')"] = "thode der baad",
        disconnect_now: Annotated[bool, "Whether to end the call gracefully after setting callback"] = True,
    ) -> str:
        logger.info(f"⏰ [Tool] schedule_callback_request: delay={delay_minutes}m, time='{preferred_time}', disconnect={disconnect_now}")
        self.session_data["callback_request"] = {
            "delayMinutes": delay_minutes,
            "preferredTime": preferred_time,
            "disconnectNow": disconnect_now,
        }
        self.record_tool_invocation("schedule_callback_request", {"delay": delay_minutes, "preferred_time": preferred_time})

        if disconnect_now:
            self.request_disconnect(reason="user_requested_callback_later")

        lang = getattr(self, "current_language", "hinglish")
        if lang == "hindi":
            return f"Ji bilkul, koi baat nahi! Maine note kar liya hai, main aapko {preferred_time} dobara call karti hoon. Apna dhyaan rakhiyega, Namaste!"
        elif lang == "english":
            return f"No problem at all! I have noted this down and will call you back in {preferred_time}. Have a great time, goodbye!"
        return f"Koi baat nahi ji! Maine note kar liya hai, main aapko {preferred_time} call back karungi. Have a nice time, bye bye!"

