"""
interactive_ui_emitter.py - Declarative Multimodal UI Event Emitter over LiveKit DataChannel.

Provides a standardized protocol for publishing rich interactive UI sheets (quizzes, media cards,
news cards, alphabet flashcards, mini-games) directly to the mobile / web calling screen.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("toolchain.interactive.emitter")


class InteractiveUiEmitterMixin:
    """Provides methods to emit structured Server-Driven UI (SDUI) packets to the active LiveKit room."""

    async def emit_interactive_sheet(self, sheet_payload: Dict[str, Any]) -> bool:
        """
        Publishes a declarative interactive sheet payload over LiveKit WebRTC DataChannel.
        Flutter app listens for type == 'interactive_sheet' and dynamically renders the component.
        """
        # Ensure standardized root envelope while preserving ALL domain payload keys
        payload = dict(sheet_payload)
        payload["type"] = "interactive_sheet"
        payload["action"] = sheet_payload.get("action", "open")
        payload["sheet_id"] = sheet_payload.get("sheet_id", "sheet_default")
        payload["component"] = sheet_payload.get("component", "banner")
        payload["title"] = sheet_payload.get("title", "")
        payload["subtitle"] = sheet_payload.get("subtitle", "")
        payload["badge"] = sheet_payload.get("badge", "")
        payload["auto_dismiss_seconds"] = sheet_payload.get("auto_dismiss_seconds", 0)
        payload["speech_hint"] = sheet_payload.get("speech_hint", "")

        # Store in session memory for context tracking
        if not hasattr(self, "session_data"):
            self.session_data = {}
        self.session_data["active_interactive_sheet"] = payload

        # Broadcast via LiveKit DataChannel if room is connected
        room = getattr(self, "room", None)
        if room and hasattr(room, "local_participant") and room.local_participant:
            try:
                raw_bytes = json.dumps(payload).encode("utf-8")
                await room.local_participant.publish_data(raw_bytes, reliable=True)
                logger.info(f"📱 [InteractiveUI] Published '{payload['component']}' sheet (id={payload['sheet_id']}) to LiveKit room.")
                return True
            except Exception as e:
                logger.warning(f"⚠️ [InteractiveUI] Failed to publish sheet packet: {e}")
        else:
            logger.debug("ℹ️ [InteractiveUI] No active LiveKit room participant connected to broadcast sheet; stored in session.")

        return False

    async def dismiss_interactive_sheet(self, sheet_id: str = "") -> bool:
        """Closes any active bottom sheet on the mobile/web screen."""
        payload = {
            "type": "interactive_sheet",
            "action": "close",
            "sheet_id": sheet_id or (self.session_data.get("active_interactive_sheet") or {}).get("sheet_id", "all")
        }

        if hasattr(self, "session_data"):
            self.session_data["active_interactive_sheet"] = None

        room = getattr(self, "room", None)
        if room and hasattr(room, "local_participant") and room.local_participant:
            try:
                raw_bytes = json.dumps(payload).encode("utf-8")
                await room.local_participant.publish_data(raw_bytes, reliable=True)
                logger.info(f"📱 [InteractiveUI] Published 'close' sheet event.")
                return True
            except Exception as e:
                logger.warning(f"⚠️ [InteractiveUI] Failed to publish sheet close: {e}")

        return False
