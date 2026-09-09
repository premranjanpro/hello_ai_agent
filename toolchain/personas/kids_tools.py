"""
kids_tools.py - Dedicated In-Memory Tools for Kids Learning & Rhymes Persona.
"""

import logging
import random
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.kids")


class KidsLearningToolsMixin:
    """Kids quiz, stories, and educational play tools."""

    @llm.ai_callable(description="Launch an exciting child-friendly quiz question on animals, space, colors, or math with instant praise.")
    async def play_interactive_quiz(
        self,
        topic: Annotated[str, "Topic of quiz: 'animals', 'space', 'colors', 'math'"] = "animals",
        question_level: Annotated[str, "Difficulty: 'easy' or 'medium'"] = "easy",
    ) -> str:
        logger.info(f"🎨 [Tool] play_interactive_quiz: topic='{topic}' ({question_level})")

        quizzes = {
            "animals": [
                ("Who is known as the King of the Jungle?", "Lion"),
                ("Which bird can fly backwards?", "Hummingbird"),
                ("Which animal has a long neck?", "Giraffe")
            ],
            "space": [
                ("Which planet is known as the Red Planet?", "Mars"),
                ("What gives us light and warmth during the day?", "The Sun")
            ]
        }
        pool = quizzes.get(topic.lower(), quizzes["animals"])
        q, a = random.choice(pool)

        self.session_data["quiz_progress"] = {
            "topic": topic,
            "currentQuestion": q,
            "expectedAnswer": a,
            "score": self.session_data.get("quiz_progress", {}).get("score", 0) + 1
        }
        self.record_tool_invocation("play_interactive_quiz", {"topic": topic, "question": q})

        return f"Yay, quiz time! Question: {q} Batayiye, iska answer kya hai?"
