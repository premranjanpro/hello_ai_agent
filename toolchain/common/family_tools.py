"""
toolchain/common/family_tools.py - Family Memory Management Toolchain.
Enables AI personas to dynamically record and recall caller family members,
their favorite colors, foods, hobbies, ages, and personal details.
"""

import json
import logging
from typing import Optional
from livekit.agents import llm
from orchestrator.family_memory_manager import FamilyMemoryManager

logger = logging.getLogger("tools.family")

class FamilyToolsMixin:
    """Toolchain mixin for managing caller family memory."""

    @llm.ai_callable(
        description="Record or update details of a caller's family member (relation, name, favorite color, favorite food, hobbies, age, health notes)."
    )
    async def record_family_member(
        self,
        relation: str,
        name: str,
        favorite_color: str = "",
        favorite_food: str = "",
        hobbies: str = "",
        age: int = 0,
        health_notes: str = "",
    ) -> str:
        """Saves a family member with all personal preferences into database."""
        logger.info(f"👨‍👩‍👧 [FamilyTools] Recording family member: {name} ({relation})")
        user_id = getattr(self, "user_id", "") or "default_user"
        api_base_url = getattr(self, "api_base_url", "http://localhost:5063")

        mgr = FamilyMemoryManager(api_base_url=api_base_url)
        success = await mgr.save_family_member(
            user_id=user_id,
            relation=relation,
            name=name,
            age=age if age > 0 else None,
            favorite_color=favorite_color or None,
            favorite_food=favorite_food or None,
            hobbies=hobbies or None,
            health_notes=health_notes or None,
        )

        details = []
        if favorite_color: details.append(f"favorite color {favorite_color}")
        if favorite_food: details.append(f"likes {favorite_food}")
        if hobbies: details.append(f"hobbies include {hobbies}")
        if age > 0: details.append(f"age {age}")

        det_str = f" with {', '.join(details)}" if details else ""
        if success:
            return f"Successfully saved {name} ({relation}){det_str} to caller's persistent memory."
        return f"Noted {name} ({relation}){det_str} in conversation."

    @llm.ai_callable(
        description="Recall recorded details about caller's family members (e.g. what food their mother likes, son's hobbies)."
    )
    async def recall_family_info(self, relation: str = "") -> str:
        """Retrieves stored details about the caller's family."""
        user_id = getattr(self, "user_id", "") or "default_user"
        api_base_url = getattr(self, "api_base_url", "http://localhost:5063")

        mgr = FamilyMemoryManager(api_base_url=api_base_url)
        members = await mgr.fetch_family_members(user_id=user_id)
        if not members:
            return "No family members are currently recorded for this caller."

        target_rel = relation.lower().strip() if relation else None
        matched = []
        for m in members:
            if target_rel and target_rel not in m.get("relation", "").lower():
                continue
            matched.append(
                f"{m.get('name')} ({m.get('relation')}): Fav Color: {m.get('favorite_color') or 'N/A'}, "
                f"Fav Food: {m.get('favorite_food') or 'N/A'}, Hobbies: {m.get('hobbies') or 'N/A'}, "
                f"Health: {m.get('health_notes') or 'N/A'}"
            )

        if not matched:
            return f"No recorded details found for family relation '{relation}'."
        return "Family details:\n" + "\n".join(matched)
