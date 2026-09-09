"""
orchestrator/family_memory_manager.py - Scalable & Flexible Family Entity Manager.
Handles fetching, formatting, extracting, and persisting family member relationships,
favorite colors, favorite foods, hobbies, ages, and custom preferences.
"""

import re
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger("orchestrator.family")

class FamilyMemoryManager:
    """Manages caller family graph and personal entity tracking across calls."""

    def __init__(self, api_base_url: str = "http://localhost:5063"):
        self.api_base_url = api_base_url.rstrip("/")

    async def fetch_family_members(self, user_id: str) -> List[Dict[str, Any]]:
        """Loads all recorded family members for the caller."""
        if not user_id:
            return []

        clean_user_id = user_id.replace("admin_", "")
        url = f"{self.api_base_url}/api/ai/user-family?userId={clean_user_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=2.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"[FamilyManager] Loaded {len(data)} family members for user {clean_user_id}")
                        return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"[FamilyManager] Failed to fetch family members: {e}")
        return []

    async def save_family_member(
        self,
        user_id: str,
        relation: str,
        name: str,
        nickname: Optional[str] = None,
        age: Optional[int] = None,
        birthday: Optional[str] = None,
        favorite_color: Optional[str] = None,
        favorite_food: Optional[str] = None,
        hobbies: Optional[str] = None,
        health_notes: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Upserts a family member into backend database."""
        if not user_id or not relation or not name:
            return False

        clean_user_id = user_id.replace("admin_", "")
        url = f"{self.api_base_url}/api/ai/user-family"
        payload = {
            "userId": clean_user_id,
            "relation": relation.strip().lower(),
            "name": name.strip(),
            "nickname": nickname or "",
            "age": age,
            "birthday": birthday or "",
            "favoriteColor": favorite_color or "",
            "favoriteFood": favorite_food or "",
            "hobbies": hobbies or "",
            "healthNotes": health_notes or "",
            "preferencesJson": json.dumps(preferences or {}),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        logger.info(f"[FamilyManager] Saved family member: {name} ({relation}) for {clean_user_id}")
                        return True
        except Exception as e:
            logger.warning(f"[FamilyManager] Failed to save family member: {e}")
        return False

    async def extract_and_save_family_members(self, turns: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """
        Scans dialogue turns for mentions of family members (Mummy, Papa, Brother, Sister, etc.)
        and automatically persists them to hello_api database so they are permanently remembered.
        """
        if not turns or not user_id:
            return []

        clean_user_id = user_id.replace("admin_", "")
        user_texts = [
            t.get("content", "") for t in turns
            if t.get("role") in ["user", "caller"] and t.get("content")
        ]
        combined = " . ".join(user_texts)

        # Regex patterns for family member extraction (Hindi, Hinglish, English)
        patterns = [
            # Hindi / Hinglish: "meri mummy ka naam Sunita hai", "papa ka naam Rajesh hai"
            (r'(?:meri|mere)?\s*(mummy|mata|mother|mom|papa|pita|father|dad|bhai|brother|behan|sister|beta|beti|son|daughter|dada|dadi|wife|husband|patni|pati)\s*(?:ji)?\s*(?:ka\s*naam|naam|hai)?\s*(?:is|hai|:)?\s*([A-Za-z\u0900-\u097F]{2,20})', 1, 2),
            # "Mummy Sunita hai", "Papa Ramesh hain"
            (r'\b(mummy|papa|bhai|behan|dada|dadi)\s+([A-Za-z\u0900-\u097F]{2,20})\s+(?:hain|hai|ji)\b', 1, 2),
            # English: "my mother's name is Pooja", "my brother is Rohan"
            (r'(?:my\s+)?(mother|father|mom|dad|brother|sister|son|daughter|wife|husband)\s*(?:\'s\s*name\s*is|\s+is|\s*name\s*is)\s+([A-Za-z]{2,20})', 1, 2),
            # "naam hai Pooja (mummy)", "bhai Kabir"
            (r'\b(bhai|behan|beta|beti)\s+([A-Za-z]{2,20})\b', 1, 2),
        ]

        stopwords = {
            "ka", "ki", "ke", "hai", "hain", "hoon", "the", "ek", "kya", "aur", "toh", "se", "bhi",
            "name", "is", "my", "and", "the", "a", "an", "yes", "no", "nahi", "haan", "bol", "batao",
            "sunao", "achha", "theek", "hello", "hi", "didi", "champ"
        }

        relation_normalize = {
            "mummy": "mother",
            "mata": "mother",
            "mom": "mother",
            "mother": "mother",
            "papa": "father",
            "pita": "father",
            "dad": "father",
            "father": "father",
            "bhai": "brother",
            "brother": "brother",
            "behan": "sister",
            "sister": "sister",
            "beta": "son",
            "son": "son",
            "beti": "daughter",
            "daughter": "daughter",
            "dadi": "grandmother",
            "dada": "grandfather",
            "patni": "wife",
            "wife": "wife",
            "pati": "husband",
            "husband": "husband",
        }

        discovered = []
        for pat, rel_idx, name_idx in patterns:
            for match in re.finditer(pat, combined, re.IGNORECASE):
                raw_rel = match.group(rel_idx).lower().strip()
                raw_name = match.group(name_idx).strip().capitalize()

                if raw_name.lower() in stopwords or len(raw_name) < 2:
                    continue

                canonical_rel = relation_normalize.get(raw_rel, raw_rel)
                if not any(d["relation"] == canonical_rel and d["name"].lower() == raw_name.lower() for d in discovered):
                    discovered.append({
                        "relation": canonical_rel,
                        "name": raw_name,
                        "raw_relation": raw_rel
                    })

        saved_members = []
        for item in discovered:
            ok = await self.save_family_member(
                user_id=clean_user_id,
                relation=item["relation"],
                name=item["name"]
            )
            if ok:
                saved_members.append(item)
                logger.info(f"👨‍👩‍👧 [FamilyManager] Automatically extracted & saved family member: {item['name']} ({item['relation']})")

        return saved_members

    @staticmethod
    def format_family_prompt_context(family_members: List[Dict[str, Any]]) -> str:
        """Formats family profile into high-relevance prompt instructions."""
        if not family_members:
            return (
                "CALLER FAMILY KNOWLEDGE:\n"
                "- No family members recorded yet.\n"
                "- INSTRUCTION: When having casual or caring chat, naturally ask the caller about their family "
                "('Aapke ghar mein kaun kaun hai?', 'Bachon ya mummy papa ke baare mein bataiye'). "
                "If they mention family members, their names, favorite colors, favorite food or hobbies, acknowledge warmly and remember them.\n"
            )

        lines = ["CALLER FAMILY PROFILE (PERSISTENT MEMORY - ALREADY RECORDED):"]
        for m in family_members:
            rel = m.get("relation", "").capitalize()
            name = m.get("name", "")
            details = []
            if m.get("age"):
                details.append(f"Age: {m['age']}")
            if m.get("favorite_color"):
                details.append(f"Fav Color: {m['favorite_color']}")
            if m.get("favorite_food"):
                details.append(f"Fav Food: {m['favorite_food']}")
            if m.get("hobbies"):
                details.append(f"Hobbies: {m['hobbies']}")
            if m.get("health_notes"):
                details.append(f"Health: {m['health_notes']}")

            detail_str = f" ({', '.join(details)})" if details else ""
            lines.append(f"- {rel}: {name}{detail_str}")

        lines.append(
            "- CRITICAL CONVERSATION RULE: You ALREADY know and remember these family members! "
            "NEVER ask 'Aapke mummy/papa/family ka kya naam hai?' or 'Aapke ghar me kaun kaun hai?' because they already told you! "
            "Address or inquire about them warmly by their name (e.g. 'Mummy Pooja kaisi hain?', 'Papa Rajesh kaise hain?', 'Kabir bhai kaisa hai?'). "
            "Treat them like real people you know and care about!"
        )
        return "\n".join(lines) + "\n"
