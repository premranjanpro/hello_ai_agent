"""
events/base.py - Base data classes and session state for the event system.
"""

from dataclasses import dataclass, field
import time
from typing import List, Dict, Any, Optional


@dataclass
class CallEventSession:
    """Encapsulates runtime state, turn history, and call flags across event listeners."""

    call_id: str
    caller_id: str
    clean_caller_id: str
    persona_id: str
    language: str
    gender: str
    start_time: float = field(default_factory=time.time)
    turns: List[Dict[str, str]] = field(default_factory=list)
    disconnect_pending: bool = False
    recording_file: str = ""
    active_character: Optional[Dict[str, Any]] = None
    known_name: str = ""

    def append_turn(self, role: str, content: str):
        if content and content.strip():
            self.turns.append({"role": role, "content": content.strip()})

    @property
    def duration_seconds(self) -> int:
        return max(1, int(time.time() - self.start_time))
