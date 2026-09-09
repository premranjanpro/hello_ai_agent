"""
companion_tools.py - Dedicated In-Memory Tools for Romantic & Companion Personas.
"""

import logging
import time
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.companion")


class CompanionToolsMixin:
    """Companion, empathetic listening, and personal affinity tools."""

    @llm.ai_callable(description="Save a meaningful personal detail, milestone, mood, or favorite thing shared by the caller in memory.")
    async def save_personal_milestone(
        self,
        category: Annotated[str, "Milestone category: 'mood', 'favorite_food_or_music', 'life_update'"],
        detail: Annotated[str, "The heartfelt detail or preference shared by the caller"],
    ) -> str:
        logger.info(f"💖 [Tool] save_personal_milestone: [{category}] {detail}")
        self.session_data["personal_milestones"].append({
            "category": category,
            "detail": detail,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.record_tool_invocation("save_personal_milestone", {"category": category, "detail": detail})

    # Retained as helper methods without @llm.ai_callable to save prompt tokens
    async def suggest_relaxation_activity(
        self,
        current_mood: Annotated[str, "Current mood or emotion expressed by caller"],
    ) -> str:
        logger.info(f"💖 [Tool] suggest_relaxation_activity: mood='{current_mood}'")
        self.record_tool_invocation("suggest_relaxation_activity", {"mood": current_mood})
        return "Aap ek gehri saans lijiye, thoda paani pee lijiye aur apni aankhein band karke 2 minute shaanti se baithiye. Main yahin hoon aapke saath."

    async def teach_kids(
        self,
        subject: Annotated[str, "Topic to teach: 'math_tables' (pahade), 'alphabets', 'moral_story', 'riddles' (paheliyan)"],
        subtopic: Annotated[str, "Specific item, e.g. 'table of 2', 'letter B', 'thirsty crow', 'animal riddle'"],
    ) -> str:
        logger.info(f"🎓 [Tool] teach_kids: subject={subject}, subtopic={subtopic}")
        self.record_tool_invocation("teach_kids", {"subject": subject, "subtopic": subtopic})

        if "table" in subject or "math" in subject:
            return f"Bohot badiya beta! Chalo milke {subtopic} bolte hain! Ek baar mere saath bolo, phir aapki baari!"
        elif "story" in subject or "kahani" in subject:
            return f"Ek bohot mazedar kahani sunati hoon: {subtopic}! Dhyan se sunna, aakhri me ek sawal puchungi!"
        else:
            return f"Shabash! Chalo ab hum {subtopic} seekhenge maze ke saath! Kya aap ready ho?"

