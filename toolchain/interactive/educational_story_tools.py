"""
educational_story_tools.py - Massive Interactive Educational & Multi-Scene Storytelling Toolchain.

Supports:
1. 15 Learning Card Categories (Animals, Birds, Vegetables, Fruits, Flowers, Vehicles, Appliances, Toys, Healthy vs Unhealthy Food)
   with "Seen?" vs "Eaten?" interactive questions.
2. Multi-Scene Dynamic Storytelling:
   - Each story is divided into sequential scenes.
   - Every scene has its own specific high-definition image and narration text!
   - Dynamic real-time image switching in the bottom sheet as the story progresses.
   - Stepper dots (Scene 1 of 4) and Next/Prev scene controls.
3. 100 Rhymes (Hindi Balgeet + English Nursery Rhymes) with Actions and Lyrics.
4. Smart Activity History & Anti-Repetition Engine.
"""

import os
import json
import random
import logging
from typing import Annotated, Dict, Any, List, Optional
from livekit.agents import llm

logger = logging.getLogger("toolchain.interactive.educational")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
KIDS_DATA_DIR = os.path.join(DATA_DIR, "kids")

def _load_json(primary_file: str, fallback_file: str) -> List[Dict[str, Any]]:
    # Check kids directory first, then root data directory
    p1 = os.path.join(KIDS_DATA_DIR, primary_file)
    if os.path.exists(p1):
        try:
            with open(p1, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {p1}: {e}")

    p2 = os.path.join(DATA_DIR, fallback_file)
    if os.path.exists(p2):
        try:
            with open(p2, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {p2}: {e}")
    return []

LEARNING_CARDS = _load_json("learning_cards.json", "learning_cards_bank.json")
RHYMES = _load_json("rhymes.json", "rhymes_bank.json")
STORIES = _load_json("stories.json", "stories_bank.json")


class EducationalStoryToolsMixin:
    """Multimodal educational content, rhymes, and interactive multi-scene story narration toolchain."""

    def _ensure_history_state(self):
        if not hasattr(self, "session_data"):
            self.session_data = {}
        if "activity_history" not in self.session_data:
            self.session_data["activity_history"] = {
                "seen_ids": [],
                "last_type": "story",
                "favorites": []
            }
        if "current_story" not in self.session_data:
            self.session_data["current_story"] = {
                "story_id": "",
                "scene_idx": 0,
                "total_scenes": 1,
                "story_data": {}
            }
        if "kids_gamification" not in self.session_data:
            self.session_data["kids_gamification"] = {
                "stars": 0,
                "level": 1,
                "level_title": "Junior Explorer 🥈",
                "curriculum_tier": "primary",
                "topics_explored": [],
                "words_learned": []
            }

    @llm.ai_callable(description="Show an interactive learning card across 15 categories (pet_animal, wild_animal, bird, snake, vegetable, fruit, flower, vehicle, home_appliances, toys, food_item, chocolate, chips, healthy_food, unhealthy_food) with 'Seen?' or 'Eaten?' questions, habitat facts, and taste description.")
    async def show_learning_card(
        self,
        item_name: Annotated[str, "Name of item (e.g. 'Lion', 'Mor', 'Gajar', 'Aam', 'Train', 'Fridge', 'Teddy', 'Almonds')"] = "",
        category: Annotated[str, "Category: 'pet_animal', 'wild_animal', 'bird', 'snake', 'vegetable', 'fruit', 'flower', 'vehicle', 'home_appliances', 'toys', 'food_item', 'chocolate', 'chips', 'healthy_food', 'unhealthy_food', or 'any'"] = "any",
    ) -> str:
        logger.info(f"🎨 [EduTool] show_learning_card: item='{item_name}', cat='{category}'")
        self.record_tool_invocation("show_learning_card", {"item": item_name, "category": category})
        self._ensure_history_state()

        clean_item = item_name.lower().strip()
        clean_cat = category.lower().strip()

        matched = None
        if clean_item:
            for card in LEARNING_CARDS:
                if clean_item in card.get("english_name", "").lower() or clean_item in card.get("hindi_name", "").lower():
                    matched = card
                    break

        if not matched:
            pool = [c for c in LEARNING_CARDS if clean_cat in ["any", "", "all"] or c.get("category", "").lower() == clean_cat or clean_cat in c.get("category", "").lower()]
            if not pool:
                pool = LEARNING_CARDS
            seen = self.session_data["activity_history"]["seen_ids"]
            available = [c for c in pool if c.get("id") not in seen]
            matched = random.choice(available if available else pool)

        self.session_data["activity_history"]["seen_ids"].append(matched.get("id", ""))
        self.session_data["activity_history"]["last_type"] = "card"

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Card: {matched.get('english_name', '')}")
        gam["stars"] = gam.get("stars", 0) + 1

        q_type = matched.get("question_type", "seen")
        yes_label = "Haan Khaya Hai! 😋" if q_type == "eaten" else "Haan Dekha Hai! 👀"
        no_label = "Nahi Khaya 🧐" if q_type == "eaten" else "Nahi Dekha 🧐"

        sheet_payload = {
            "action": "open",
            "sheet_id": f"card_{matched.get('id', '')}",
            "component": "learning_card_interactive",
            "title": f"{matched.get('english_name', '')} • {matched.get('hindi_name', '')}",
            "subtitle": f"Category: {matched.get('category', '').replace('_', ' ').capitalize()}",
            "badge": "LEARNING CARD",
            "bgm_track": "playful_tinkle",
            "auto_dismiss_seconds": 25,
            "media": {
                "image_url": matched.get("image_url", ""),
                "caption": matched.get("fun_fact", ""),
                "aspect_ratio": 1.4
            },
            "learning_card": {
                "id": matched.get("id", ""),
                "category": matched.get("category", ""),
                "english_name": matched.get("english_name", ""),
                "hindi_name": matched.get("hindi_name", ""),
                "question_type": q_type,
                "interactive_question": matched.get("interactive_question", f"Kya tumne {matched.get('english_name', '')} dekha hai?"),
                "where_found": matched.get("where_found", ""),
                "taste_or_health": matched.get("taste_or_health", ""),
                "sound": matched.get("sound", ""),
                "fun_fact": matched.get("fun_fact", "")
            },
            "gamification": {
                "stars": gam.get("stars", 1),
                "level": gam.get("level", 1),
                "level_title": gam.get("level_title", "Junior Explorer 🥈"),
                "sfx": "celebration_fanfare"
            },
            "interactive_input": {
                "type": "action_bar",
                "actions": [
                    {"id": f"{q_type}_yes", "label": yes_label, "action": f"{q_type}_yes"},
                    {"id": f"{q_type}_no", "label": no_label, "action": f"{q_type}_no"},
                    {"id": "next_card", "label": "Agla Card ➡️", "action": "next_card"},
                    {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
                ]
            },
            "speech_hint": matched.get("speech", "")
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return matched.get("speech", f"Ye dekhiye screen par {matched.get('english_name')}! {matched.get('interactive_question')}")

    @llm.ai_callable(description="Narrate a rich moral story (Panchatantra, Akbar Birbal, Jataka Tales) with dynamic scene-by-scene image switching. Call whenever the child asks for a story, kahani, katha, or tale.")
    async def narrate_story(
        self,
        story_name: Annotated[str, "Name of the story, e.g. 'Pyaasa Kauwa', 'Kharghosh Aur Kachhua', 'Sher Aur Chuha', 'Birbal Ki Khichdi'"] = "",
        category: Annotated[str, "Category: 'Panchatantra', 'Aesop Fables', 'Jataka Tales', 'Historical & Wisdom', or 'any'"] = "any",
        scene_number: Annotated[int, "Specific scene number (default 1)"] = 1,
    ) -> str:
        logger.info(f"📖 [EduTool] narrate_story: name='{story_name}', cat='{category}', scene={scene_number}")
        self.record_tool_invocation("narrate_story", {"story_name": story_name, "category": category, "scene_number": scene_number})
        self._ensure_history_state()

        clean_name = story_name.lower().strip()
        clean_cat = category.lower().strip()

        matched = None
        if clean_name:
            for s in STORIES:
                if clean_name in s.get("title", "").lower() or clean_name in s.get("hindi_title", "").lower():
                    matched = s
                    break

        if not matched:
            pool = [s for s in STORIES if clean_cat in ["any", "", "all"] or clean_cat in s.get("category", "").lower()]
            if not pool:
                pool = STORIES
            seen = self.session_data["activity_history"]["seen_ids"]
            available = [s for s in pool if s.get("id") not in seen]
            matched = random.choice(available if available else pool)

        self.session_data["activity_history"]["seen_ids"].append(matched.get("id", ""))
        self.session_data["activity_history"]["last_type"] = "story"

        scenes = matched.get("scenes", [])
        if not scenes:
            # Fallback legacy paragraphs to scenes
            paras = matched.get("paragraphs", ["Ek pyari si kahani."])
            scenes = [
                {
                    "scene_num": i + 1,
                    "title": f"Scene {i + 1}",
                    "text": p,
                    "image_url": matched.get("image_url", "https://images.unsplash.com/photo-1544816155-12df9643f363?w=800&q=80"),
                    "speech": p
                }
                for i, p in enumerate(paras)
            ]

        total_scenes = len(scenes)
        target_idx = max(0, min(scene_number - 1, total_scenes - 1))
        current_scene = scenes[target_idx]

        # Save active story state for next_story_scene / prev_story_scene
        self.session_data["current_story"] = {
            "story_id": matched.get("id", "story_1"),
            "scene_idx": target_idx,
            "total_scenes": total_scenes,
            "story_data": matched,
            "scenes": scenes
        }

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Story: {matched.get('title', '')}")
        gam["stars"] = gam.get("stars", 0) + 1

        sheet_payload = {
            "action": "open",
            "sheet_id": f"story_{matched.get('id')}_s{current_scene.get('scene_num', target_idx + 1)}",
            "component": "story_scene",
            "title": f"📖 {matched.get('title', '')}",
            "subtitle": f"Scene {target_idx + 1} of {total_scenes} • {current_scene.get('title', '')}",
            "badge": f"SCENE {target_idx + 1}/{total_scenes}",
            "bgm_track": "story_calm",
            "auto_dismiss_seconds": 90,
            "media": {
                "image_url": current_scene.get("image_url", matched.get("image_url", "")),
                "caption": f"Seekh: {matched.get('moral', '')}",
                "aspect_ratio": 1.5
            },
            "story_scene": {
                "story_id": matched.get("id"),
                "title": matched.get("title"),
                "moral": matched.get("moral"),
                "scene_num": target_idx + 1,
                "total_scenes": total_scenes,
                "scene_title": current_scene.get("title", f"Scene {target_idx + 1}"),
                "text": current_scene.get("text", ""),
                "image_url": current_scene.get("image_url", ""),
                "karaoke_enabled": True,
                "words_per_minute": 115
            },
            "gamification": {
                "stars": gam.get("stars", 1),
                "level": gam.get("level", 1),
                "level_title": gam.get("level_title", "Junior Explorer 🥈")
            },
            "interactive_input": {
                "type": "action_bar",
                "actions": [
                    {"id": "story_prev_scene", "label": "⬅️ Piche", "action": "story_prev_scene"},
                    {"id": "story_next_scene", "label": "Aage ➡️", "action": "story_next_scene"},
                    {"id": "next_story", "label": "Nayi Kahani 🔄", "action": "next_story"},
                    {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
                ]
            },
            "speech_hint": current_scene.get("speech", current_scene.get("text", ""))
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        intro = f"Chalo, main aapko kahani sunati hoon: '{matched.get('title')}'! Dekhiye screen par pehla scene! " if target_idx == 0 else ""
        narration = current_scene.get('speech', current_scene.get('text', ''))
        return f"{intro}{narration}\n(Instruction: Read this story narration out loud to the child with joyful expression now!)"

    async def next_story_scene(self) -> str:
        logger.info("⏭️ [EduTool] next_story_scene")
        self.record_tool_invocation("next_story_scene", {})
        self._ensure_history_state()

        curr = self.session_data.get("current_story", {})
        scenes = curr.get("scenes", [])
        if not scenes:
            return await self.narrate_story()

        idx = curr.get("scene_idx", 0) + 1
        total = curr.get("total_scenes", len(scenes))
        story_data = curr.get("story_data", {})

        if idx >= total:
            # Reached end of story, celebrate moral and bonus stars!
            gam = self.session_data["kids_gamification"]
            gam["stars"] = gam.get("stars", 0) + 3
            moral = story_data.get("moral", "Achhe bano aur sabki madad karo.")
            return (
                f"Kahani yahan poori hoti hai! Kaisi lagi kahani? "
                f"Is kahani se hame seekh milti hai: {moral}! "
                f"Aapne bohot dhyaan se kahani suni, isliye aapko milte hain 3 Bonus Stars ⭐⭐⭐! "
                f"Kya aap ek aur nayi kahani sunna chahenge?"
            )

        curr["scene_idx"] = idx
        return await self.narrate_story(story_name=story_data.get("title", ""), scene_number=idx + 1)

    async def prev_story_scene(self) -> str:
        logger.info("⏮️ [EduTool] prev_story_scene")
        self.record_tool_invocation("prev_story_scene", {})
        self._ensure_history_state()

        curr = self.session_data.get("current_story", {})
        scenes = curr.get("scenes", [])
        if not scenes:
            return await self.narrate_story()

        idx = max(0, curr.get("scene_idx", 0) - 1)
        story_data = curr.get("story_data", {})
        curr["scene_idx"] = idx
        return await self.narrate_story(story_name=story_data.get("title", ""), scene_number=idx + 1)

    @llm.ai_callable(description="Recite a melodious nursery rhyme with colorful illustrations, lyrics, and karaoke. Call whenever the child asks for a poem, rhyme, kavita, or balgeet.")
    async def recite_rhyme(
        self,
        rhyme_name: Annotated[str, "Name of rhyme, e.g. 'Chanda Mama', 'Twinkle Twinkle', 'Machhli Jal Ki Rani', 'Titli Udi'"] = "",
        language: Annotated[str, "Language: 'hindi', 'english', or 'any'"] = "hindi",
    ) -> str:
        logger.info(f"🎶 [EduTool] recite_rhyme: name='{rhyme_name}', lang='{language}'")
        self.record_tool_invocation("recite_rhyme", {"rhyme_name": rhyme_name, "language": language})
        self._ensure_history_state()

        clean_name = rhyme_name.lower().strip()
        clean_lang = language.lower().strip()

        matched = None
        if clean_name:
            for r in RHYMES:
                if clean_name in r.get("title", "").lower():
                    matched = r
                    break

        if not matched:
            pool = [r for r in RHYMES if clean_lang in ["any", "", "all"] or r.get("language", "").lower() == clean_lang]
            if not pool:
                pool = RHYMES
            seen = self.session_data["activity_history"]["seen_ids"]
            available = [r for r in pool if r.get("id") not in seen]
            matched = random.choice(available if available else pool)

        self.session_data["activity_history"]["seen_ids"].append(matched.get("id", ""))
        self.session_data["activity_history"]["last_type"] = "rhyme"

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Rhyme: {matched.get('title', '')}")
        gam["stars"] = gam.get("stars", 0) + 1

        sheet_payload = {
            "action": "open",
            "sheet_id": f"rhyme_{matched.get('id')}",
            "component": "news",
            "title": f"🎶 {matched.get('title')}",
            "subtitle": f"Language: {matched.get('language', 'Hindi').capitalize()} Rhyme",
            "badge": "NURSERY RHYME",
            "bgm_track": "playful_tinkle",
            "auto_dismiss_seconds": 35,
            "media": {
                "image_url": matched.get("image_url", ""),
                "caption": matched.get("title", ""),
                "aspect_ratio": 1.4
            },
            "quick_facts": [
                f"Lyrics: {matched.get('lyrics', '')}",
                "Gao mere sath milkar!"
            ],
            "gamification": {
                "stars": gam.get("stars", 1),
                "level": gam.get("level", 1),
                "level_title": gam.get("level_title", "Junior Explorer 🥈")
            },
            "interactive_input": {
                "type": "action_bar",
                "actions": [
                    {"id": "next_rhyme", "label": "Next Rhyme 🎶", "action": "next_rhyme"},
                    {"id": "sing_again", "label": "Sing Again 🔁", "action": "sing_again"},
                    {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
                ]
            },
            "speech_hint": matched.get("speech", "")
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return matched.get("speech", f"Aao gaate hain: {matched.get('title')}!")

    async def next_activity(
        self,
        preferred_type: Annotated[str, "Preference: 'story', 'rhyme', 'card'"] = "random",
    ) -> str:
        logger.info(f"⏭️ [EduTool] next_activity: preferred='{preferred_type}'")
        self.record_tool_invocation("next_activity", {"type": preferred_type})
        self._ensure_history_state()

        p_type = preferred_type.lower().strip()
        if p_type in ["random", "", "all"]:
            last_type = self.session_data["activity_history"].get("last_type", "story")
            types = ["story", "rhyme", "card"]
            remaining = [t for t in types if t != last_type]
            p_type = random.choice(remaining)

        if any(w in p_type for w in ["rhyme", "poem", "geet", "sing"]):
            return await self.recite_rhyme(language="hindi")
        elif any(w in p_type for w in ["card", "animal", "phal", "fruit", "veg"]):
            return await self.show_learning_card()
        else:
            return await self.narrate_story()
