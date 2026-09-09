"""
events/speech_events.py - Speech Committed Handlers for User and Agent.
Manages real-time transcription history, hierarchical long-conversation memory,
fact/entity preservation, and graceful call disconnection upon goodbye completion.
"""

import asyncio
import logging
import re
import aiohttp
from typing import Optional, Any, List, Dict
from livekit.agents import llm
from livekit import rtc

from events.base import CallEventSession
from events.data_channel import CaptionBroadcaster

logger = logging.getLogger("events.speech")

VERBATIM_MESSAGE_WINDOW = 20  # Keep latest 20 messages verbatim for deep contextual continuity


class SpeechEventHandler:
    """Attaches speech lifecycle event listeners to VoicePipelineAgent with hierarchical long-conversation memory."""

    def __init__(
        self,
        agent: Any,
        room: rtc.Room,
        session: CallEventSession,
        tools_ctx: Optional[Any] = None,
        api_base_url: str = "http://localhost:5063",
        watchdog: Optional[Any] = None,
    ):
        self.agent = agent
        self.room = room
        self.session = session
        self.tools_ctx = tools_ctx
        self.api_base_url = api_base_url.rstrip("/")
        self.watchdog = watchdog
        self._rolling_summary_points: List[str] = []
        self._extracted_facts: Dict[str, str] = {}
        self._turn_count: int = 0
        self._last_checkpoint_turn: int = 0

    def bind(self):
        disconnect_regex = re.compile(
            r'\b(call\s*disconnect|disconnect\s*call|disconnect|call\s*cut|call\s*end|'
            r'phone\s*rakh|call\s*kaat|hang\s*up|(?:call|phone)\s*band\s*kar\s*do|(?:call|phone)\s*kaat\s*do|'
            r'alvida|bye\s*bye\s*didi|bye\s*bye\s*call)\b',
            re.IGNORECASE
        )

        @self.agent.on("user_started_speaking")
        def on_user_start():
            logger.info("🗣️ Caller started speaking...")
            if self.watchdog:
                self.watchdog.on_user_started_speaking()

        @self.agent.on("user_stopped_speaking")
        def on_user_stop():
            logger.info("🤫 Caller stopped speaking, transcribing with Groq...")

        @self.agent.on("agent_started_speaking")
        def on_agent_start():
            logger.info("🔊 AI agent started speaking...")
            if self.watchdog:
                self.watchdog.on_agent_started_speaking()

        @self.agent.on("agent_stopped_speaking")
        def on_agent_stop():
            logger.info("👂 AI agent finished speaking, actively listening for caller...")
            if self.watchdog:
                self.watchdog.on_agent_stopped_speaking()

        @self.agent.on("error")
        def on_agent_error(err):
            logger.error(f"❌ VoicePipeline error event: {err}")

        @self.agent.on("user_speech_committed")
        def on_user_speech(msg: llm.ChatMessage):
            if self.watchdog:
                self.watchdog.on_user_speech_committed()
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            clean_text = text.strip()
            if clean_text and not clean_text.startswith("PAST USER MEMORY"):
                self.session.append_turn("user", clean_text)
                self._extract_key_facts(clean_text)

                if self.tools_ctx and hasattr(self.tools_ctx, "cancel_quiz_timer"):
                    self.tools_ctx.cancel_quiz_timer()

                # Disconnect Intent Guard: Detect if user explicitly commanded hangup/disconnect
                if disconnect_regex.search(clean_text):
                    logger.info(f"🛑 [SpeechEventHandler] Disconnect intent detected from caller: '{clean_text}'")
                    self.session.disconnect_pending = True
                    if self.tools_ctx:
                        self.tools_ctx.disconnect_pending = True

            asyncio.create_task(CaptionBroadcaster.broadcast(self.room, "user", clean_text))

        @self.agent.on("agent_speech_committed")
        def on_agent_speech(msg: llm.ChatMessage):
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            clean_text = text.strip()
            if clean_text and not clean_text.startswith("PAST USER MEMORY"):
                self.session.append_turn("assistant", clean_text)
                self._turn_count += 1
                if self.tools_ctx and hasattr(self.tools_ctx, "session_data"):
                    self.tools_ctx.session_data["last_assistant_text"] = clean_text

                # Also detect if assistant announced farewell or call disconnect
                if disconnect_regex.search(clean_text) and self.session.disconnect_pending:
                    logger.info(f"🛑 [SpeechEventHandler] Assistant farewell completed: '{clean_text}'")

            asyncio.create_task(CaptionBroadcaster.broadcast(self.room, "assistant", clean_text))

            # 1. Hierarchical Context Management: Preserves full dialogue history for long calls
            self._prune_and_summarize_context()

            # 2. Periodic In-Call Memory Checkpoint (Every 5 turns)
            if (self._turn_count - self._last_checkpoint_turn) >= 5:
                self._last_checkpoint_turn = self._turn_count
                asyncio.create_task(self._checkpoint_in_call_memory())

            # 3. Trigger Graceful Disconnect if flagged by Tool, User Intent, or Farewell
            tool_disconnect = False
            if self.tools_ctx:
                tool_disconnect = getattr(self.tools_ctx, "disconnect_pending", False) or getattr(getattr(self.tools_ctx, "session", None), "disconnect_pending", False)

            if self.session.disconnect_pending or tool_disconnect:
                logger.info("[SpeechEventHandler] Goodbye completed. Executing graceful room disconnect in 1.2s...")

                async def _delayed_disconnect():
                    await asyncio.sleep(1.2)
                    try:
                        # Broadcast final call_ended packet to data channel so Flutter app & Web Admin close screen immediately
                        import json
                        payload = json.dumps({"type": "call_ended", "reason": "user_requested_disconnect"}).encode('utf-8')
                        await self.room.local_participant.publish_data(payload, reliable=True)
                        logger.info("[SpeechEventHandler] Published 'call_ended' to LiveKit data channel.")
                    except Exception as ex:
                        logger.warning(f"[SpeechEventHandler] Data broadcast notice: {ex}")

                    try:
                        await self.room.disconnect()
                        logger.info("[SpeechEventHandler] LiveKit room disconnected gracefully.")
                    except Exception as e:
                        logger.warning(f"[SpeechEventHandler] Room disconnect notice: {e}")

                asyncio.create_task(_delayed_disconnect())

    def _extract_key_facts(self, user_text: str):
        """Lightweight in-flight entity and fact tracker to prevent memory loss in long calls."""
        text_lower = user_text.lower()

        # Name extraction (only extract once if not already discovered)
        if "caller_name" not in self._extracted_facts:
            name_match = re.search(r'(?:mera naam|my name is|i am|this is)\s+([A-Za-z]+)', text_lower)
            if name_match:
                extracted_name = name_match.group(1).capitalize()
                stopwords = ["ek", "kya", "toh", "haan", "calling", "speaking", "the", "a", "an", "aur", "main"]
                if extracted_name.lower() not in stopwords:
                    self._extracted_facts["caller_name"] = extracted_name

        # Location / City extraction (keep primary location)
        if "location" not in self._extracted_facts:
            city_match = re.search(r'\b(noida|delhi|mumbai|bangalore|bengaluru|pune|hyderabad|kolkata|chennai|gurgaon|jaipur|lucknow|ahmedabad)\b', text_lower)
            if city_match:
                self._extracted_facts["location"] = city_match.group(1).capitalize()

        # Budget / Price extraction
        if "budget" not in self._extracted_facts:
            budget_match = re.search(r'(?:budget|cost|fee|kharcha)\s*(?:hai|is|around|lagbhag|of|me)?\s*[:=]?\s*(?:rs\.?|inr)?\s*(\d+[\d,]*)', text_lower)
            if not budget_match:
                budget_match = re.search(r'(\d+[\d,]*)\s*(?:rupaye|rs\.?|inr|hazaar|k|lakh)', text_lower)
            if budget_match:
                self._extracted_facts["budget"] = budget_match.group(1).strip()

    def _prune_and_summarize_context(self):
        """
        Hierarchical Long-Call Context Window.
        Maintains the latest 20 dialogue messages verbatim,
        and compresses older turns into high-fidelity topic bullet points and entity facts.
        Enables 30+ minute long calls without token overflow or memory wipeout.
        """
        try:
            msgs = self.agent.chat_ctx.messages
            chat_msgs = [m for m in msgs if m.role in ["user", "assistant"]]

            if len(chat_msgs) > VERBATIM_MESSAGE_WINDOW:
                # Old turns that are moving outside the verbatim window
                to_prune = chat_msgs[:-VERBATIM_MESSAGE_WINDOW]
                for m in to_prune:
                    content = m.content if isinstance(m.content, str) else str(m.content)
                    content = content.strip()
                    if content and len(content) > 3:
                        prefix = "Caller" if m.role == "user" else "AI"
                        # Keep full meaningful sentence up to 220 chars (no destructive 90-char chopping)
                        clean_line = content[:220].strip()
                        compact_note = f"{prefix}: {clean_line}"
                        if compact_note not in self._rolling_summary_points:
                            self._rolling_summary_points.append(compact_note)

                # Cap rolling summary to latest 12 key points
                if len(self._rolling_summary_points) > 12:
                    self._rolling_summary_points = self._rolling_summary_points[-12:]

                # Extract base system prompt
                system_msgs = [m for m in msgs if m.role == "system" and not str(m.content).startswith("[LONG-CALL PERSISTENT CONTEXT")]
                primary_system = system_msgs[0] if system_msgs else None

                # Build updated message list
                updated_messages = []
                if primary_system:
                    updated_messages.append(primary_system)

                # Inject persistent entity facts + ongoing conversation memory
                context_sections = []
                if self._extracted_facts:
                    facts_str = ", ".join(f"{k}: {v}" for k, v in self._extracted_facts.items())
                    context_sections.append(f"• KEY CALLER FACTS: {facts_str}")

                if self._rolling_summary_points:
                    points_str = "\n".join(f"• {p}" for p in self._rolling_summary_points)
                    context_sections.append(f"• EARLIER DISCUSSION HIGHLIGHTS:\n{points_str}")

                if context_sections:
                    summary_text = (
                        "[LONG-CALL PERSISTENT CONTEXT & PREVIOUS DISCUSSION HIGHLIGHTS]:\n"
                        + "\n\n".join(context_sections)
                        + "\nINSTRUCTION: Maintain full continuity with these earlier facts throughout the call."
                    )
                    updated_messages.append(llm.ChatMessage(role="system", content=summary_text))

                # Append the latest 20 dialogue messages verbatim, ensuring no dangling tool_calls without responses
                for m in chat_msgs[-VERBATIM_MESSAGE_WINDOW:]:
                    c = getattr(m, "content", "")
                    c_str = c if isinstance(c, str) else str(c or "")
                    if getattr(m, "role", "") == "assistant" and getattr(m, "tool_calls", None):
                        updated_messages.append(llm.ChatMessage(role="assistant", content=c_str))
                    else:
                        updated_messages.append(m)

                # Rebuild chat context in place
                self.agent.chat_ctx.messages.clear()
                self.agent.chat_ctx.messages.extend(updated_messages)
                logger.debug(
                    f"[SpeechEventHandler] Hierarchical context updated: "
                    f"{len(self._extracted_facts)} facts, {len(self._rolling_summary_points)} summary notes, "
                    f"and {len(chat_msgs[-VERBATIM_MESSAGE_WINDOW:])} verbatim turns retained."
                )
        except Exception as e:
            logger.warning(f"[SpeechEventHandler] Error updating long-call context: {e}")

    async def _checkpoint_in_call_memory(self):
        """Silently checkpoints conversation memory to backend API to prevent data loss on network drops."""
        if not self.session.call_id or not self.session.caller_id:
            return

        try:
            url = f"{self.api_base_url}/api/ai/memory/save"
            turns_payload = [
                {"role": t["role"], "content": t["content"]}
                for t in self.session.turns[-16:]
            ]
            summary_memo = " | ".join(self._rolling_summary_points[-6:]) if self._rolling_summary_points else "Active multi-turn conversation."
            payload = {
                "callId": self.session.call_id,
                "userId": self.session.clean_caller_id,
                "personaId": self.session.persona_id,
                "turns": turns_payload,
                "memorySummary": f"[In-Call Checkpoint]: {summary_memo}",
            }
            async with aiohttp.ClientSession() as http_sess:
                async with http_sess.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                    if resp.status == 200:
                        logger.info(f"[SpeechEventHandler] In-call memory check-pointed at turn {self._turn_count}.")
        except Exception as e:
            logger.debug(f"[SpeechEventHandler] In-call checkpoint notice: {e}")
