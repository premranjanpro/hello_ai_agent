"""
tutor_tools.py - Dedicated In-Memory Tools for Spoken English Tutor Persona.
"""

import logging
import time
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.tutor")


class EnglishTutorToolsMixin:
    """Spoken English coaching, pronunciation, and grammar correction tools."""

    @llm.ai_callable(description="Log English speaking feedback with correct phrasing and a quick grammar or pronunciation tip in session memory.")
    async def log_english_learning_feedback(
        self,
        spoken_phrase: Annotated[str, "The sentence spoken by the learner"],
        correct_version: Annotated[str, "The natural and grammatically correct English phrasing"],
        grammar_tip: Annotated[str, "A brief 1-sentence tip on why this phrasing is better"],
    ) -> str:
        logger.info(f"🗣️ [Tool] log_english_learning_feedback: '{spoken_phrase}' -> '{correct_version}'")
        self.session_data["english_feedback"].append({
            "spoken": spoken_phrase,
            "corrected": correct_version,
            "tip": grammar_tip,
            "timestamp": time.time()
        })
        self.record_tool_invocation("log_english_learning_feedback", {"corrected": correct_version})

        return f"Nice try! You can say: '{correct_version}'. Tip: {grammar_tip}"
