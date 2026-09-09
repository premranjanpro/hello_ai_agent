"""
events/data_channel.py - WebRTC Data Channel Subtitle / Caption Broadcaster.
Broadcasts real-time spoken text to web and mobile clients reliably.
"""

import json
import logging
from typing import Optional
from livekit import rtc

logger = logging.getLogger("events.datachannel")


class CaptionBroadcaster:
    """Broadcasts user and agent captions over LiveKit room DataChannel."""

    @staticmethod
    async def broadcast(room: rtc.Room, role: str, text: str):
        if not text or not text.strip() or not room.local_participant:
            return

        clean = text.strip()
        # Ignore system prompt or memory injection text
        if clean.startswith("PAST USER MEMORY") or clean.startswith("System:"):
            return

        try:
            payload = json.dumps({
                "type": "caption",
                "role": role,
                "text": clean,
            }).encode("utf-8")
            await room.local_participant.publish_data(payload, reliable=True)
        except Exception as e:
            logger.debug(f"[CaptionBroadcaster] Caption publish notice: {e}")
