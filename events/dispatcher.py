"""
events/dispatcher.py - Central Event Dispatcher for AI Voice Calls.
Glues together speech events, data channel broadcasting, recording streams, and room disconnects.
"""

import logging
from typing import Optional, Any
from livekit import rtc

from events.base import CallEventSession
from events.speech_events import SpeechEventHandler
from events.call_events import CallLifecycleHandler
from events.kid_engagement_watchdog import KidEngagementWatchdog
from pipeline.audio_recorder import AudioRecorder

logger = logging.getLogger("events.dispatcher")


class EventDispatcher:
    """Central dispatcher binding all event handlers to the voice pipeline agent and room."""

    @classmethod
    def bind(
        cls,
        agent: Any,
        room: rtc.Room,
        participant: rtc.RemoteParticipant,
        session: CallEventSession,
        recorder: AudioRecorder,
        tools_ctx: Optional[Any] = None,
        api_base_url: str = "http://localhost:5063",
    ) -> CallLifecycleHandler:
        logger.info(f"[EventDispatcher] Binding event handlers for call {session.call_id}")

        # Initialize KidEngagementWatchdog for kids learning calls (proactive engagement & sleep engine)
        watchdog = None
        if "kids" in getattr(session, "persona_id", "").lower():
            watchdog = KidEngagementWatchdog(
                agent=agent,
                room=room,
                session=session,
                tools_ctx=tools_ctx,
                known_name=getattr(session, "known_name", ""),
            )
            logger.info(f"✨ [EventDispatcher] KidEngagementWatchdog active for persona '{session.persona_id}'.")

        speech_handler = SpeechEventHandler(
            agent=agent,
            room=room,
            session=session,
            tools_ctx=tools_ctx,
            api_base_url=api_base_url,
            watchdog=watchdog,
        )
        speech_handler.bind()

        call_handler = CallLifecycleHandler(
            agent=agent,
            room=room,
            participant=participant,
            session=session,
            recorder=recorder,
            tools_ctx=tools_ctx,
            api_base_url=api_base_url,
            watchdog=watchdog,
        )
        call_handler.bind()

        return call_handler
