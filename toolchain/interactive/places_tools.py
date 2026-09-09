"""
places_tools.py - Multimodal Virtual India Tour for Kids (50+ Iconic Destinations).
Emits swipeable multi-image galleries, fun facts, and joyful feminine voice tours.
"""

import os
import json
import logging
from typing import Annotated, Dict, Any, List, Optional
from livekit.agents import llm

logger = logging.getLogger("toolchain.interactive.places")

KIDS_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "kids")
PLACES_JSON_PATH = os.path.join(KIDS_DATA_DIR, "places_explorer.json")

def _load_places_explorer() -> List[Dict[str, Any]]:
    if os.path.exists(PLACES_JSON_PATH):
        try:
            with open(PLACES_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {PLACES_JSON_PATH}: {e}")
    return []

PLACES_BANK: List[Dict[str, Any]] = _load_places_explorer()


class InteractivePlacesToolsMixin:
    """Virtual tour guide across 50+ famous and exciting Indian landmarks for kids."""

    def _ensure_places_state(self):
        if not hasattr(self, "session_data"):
            self.session_data = {}
        if "places_tour" not in self.session_data:
            self.session_data["places_tour"] = {
                "active_place_id": "place_darjeeling_toy_train",
                "current_index": 0,
                "visited_places": []
            }

    def _find_place_by_query(self, query: str) -> Dict[str, Any]:
        q = query.lower().strip()
        if not PLACES_BANK:
            return {}

        # 1. Exact ID or name match
        for p in PLACES_BANK:
            if p.get("id", "").lower() == q or p.get("name", "").lower() == q:
                return p

        # 2. Match landmark name in query
        for p in PLACES_BANK:
            name = p.get("name", "").lower()
            if name and (name in q or q in name):
                return p

        # 3. Category or thematic keyword match
        keywords_map = {
            "toy train": ["darjeeling", "ooty", "shimla", "rail"],
            "train": ["darjeeling", "ooty", "shimla", "pamban", "rail"],
            "zoo": ["delhi_zoo", "mysore_zoo", "vandaloor", "nehru_zoo"],
            "tiger": ["ranthambore", "jim_corbett", "sunderbans", "delhi_zoo"],
            "lion": ["gir", "vandaloor"],
            "genda": ["kaziranga"],
            "rhino": ["kaziranga"],
            "elephant": ["periyar", "coorg", "mysore_palace"],
            "haathi": ["periyar", "coorg", "amer_fort", "mysore_palace"],
            "planetarium": ["planetarium"],
            "space": ["planetarium", "science_city"],
            "taare": ["planetarium"],
            "science": ["science_city", "gujarat_science_city", "visvesvaraya"],
            "robot": ["gujarat_science_city"],
            "dinosaur": ["science_city_kolkata"],
            "snow": ["gulmarg", "manali", "rohtang", "ladakh"],
            "barf": ["gulmarg", "manali", "rohtang", "ladakh"],
            "snowman": ["gulmarg", "manali"],
            "beach": ["goa", "andaman", "marine_drive", "kanyakumari"],
            "samundar": ["goa", "andaman", "marine_drive", "gateway_of_india", "kanyakumari"],
            "dolphin": ["goa_dolphin_beach"],
            "houseboat": ["kerala_houseboat"],
            "taj mahal": ["taj_mahal"],
            "tajmahal": ["taj_mahal"],
            "lal qila": ["red_fort"],
            "red fort": ["red_fort"],
            "india gate": ["india_gate"],
            "golden temple": ["golden_temple"],
            "statue of unity": ["statue_of_unity"],
            "darjeeling": ["darjeeling"],
            "agra": ["taj_mahal"],
            "delhi": ["delhi_zoo", "red_fort", "india_gate", "nehru_planetarium"],
            "mumbai": ["gateway_of_india", "marine_drive", "csmt_mumbai"],
            "kolkata": ["science_city_kolkata", "victoria_memorial"],
            "jaipur": ["hawa_mahal", "amer_fort", "jantar_mantar"],
            "tasveer": ["darjeeling", "taj_mahal"],
            "tasveere": ["darjeeling", "taj_mahal"],
            "photo": ["darjeeling", "taj_mahal"],
            "image": ["darjeeling", "taj_mahal"],
            "picture": ["darjeeling", "taj_mahal"],
            # Devanagari Hindi keywords
            "तस्वीर": ["darjeeling", "taj_mahal"],
            "तस्वीरें": ["darjeeling", "taj_mahal"],
            "फोटो": ["darjeeling", "taj_mahal"],
            "इमेज": ["darjeeling", "taj_mahal"],
            "ताजमहल": ["taj_mahal"],
            "ताज महल": ["taj_mahal"],
            "आगरा": ["taj_mahal"],
            "दार्जिलिंग": ["darjeeling"],
            "टॉय ट्रेन": ["darjeeling", "ooty", "shimla"],
            "टॉयट्रेन": ["darjeeling", "ooty", "shimla"],
            "ऊटी": ["ooty"],
            "चिड़ियाघर": ["delhi_zoo", "mysore_zoo"],
            "ज़ू": ["delhi_zoo"],
            "जू": ["delhi_zoo"],
            "तारामंडल": ["planetarium"],
            "गुलमर्ग": ["gulmarg"],
            "बर्फ": ["gulmarg", "manali"],
            "गोवा": ["goa"],
            "डॉल्फ़िन": ["goa_dolphin_beach"],
            "हाउसबोट": ["kerala_houseboat"],
            "लाल किला": ["red_fort"],
            "लालकिला": ["red_fort"],
            "इंडिया गेट": ["india_gate"],
            "स्वर्ण मंदिर": ["golden_temple"],
            "हवा महल": ["hawa_mahal"],
        }

        for kw, target_slugs in keywords_map.items():
            if kw in q:
                for slug in target_slugs:
                    for p in PLACES_BANK:
                        if slug in p.get("id", "").lower() or slug in p.get("name", "").lower():
                            return p

        # Default to first place
        return PLACES_BANK[0]

    @llm.ai_callable(description="Show photos, pictures, multi-image galleries, or take child on virtual tour of famous Indian places & monuments (Taj Mahal Agra, Darjeeling Toy Train, Delhi Zoo, Nehru Planetarium, Kashmir Snow, Goa Dolphins, Kerala Houseboat, etc.). Call whenever child asks for photos, images, pictures, places to explore, or mentions visiting a place.")
    async def explore_india_place(
        self,
        place_name: Annotated[str, "Name or keyword of place, e.g. 'darjeeling', 'toy train', 'delhi zoo', 'taj mahal', 'snow man', 'planetarium', 'goa'"] = "darjeeling",
    ) -> str:
        """Emits a rich multi-image gallery bottom sheet for any Indian kid-friendly place."""
        logger.info(f"🗺️ [PlacesTool] explore_india_place: query='{place_name}'")
        self._ensure_places_state()

        matched = self._find_place_by_query(place_name)
        if not matched:
            return "Arrey waah champ! Chalo hum India ke khoobsurat tourist spots ghoomte hain! Aapko toy train dekhni hai ya jungle zoo?"

        state_tour = self.session_data["places_tour"]
        state_tour["active_place_id"] = matched["id"]
        if matched["id"] in [p["id"] for p in PLACES_BANK]:
            state_tour["current_index"] = [p["id"] for p in PLACES_BANK].index(matched["id"])
        if matched["id"] not in state_tour["visited_places"]:
            state_tour["visited_places"].append(matched["id"])

        gallery = matched.get("gallery_images", [])
        facts = matched.get("kids_facts", [])

        sheet_payload = {
            "action": "open",
            "sheet_id": f"place_{matched['id']}",
            "component": "places_gallery",
            "title": matched["name"],
            "subtitle": f"📍 {matched.get('city', '')}, {matched.get('state', '')}",
            "badge": f"{matched.get('emoji', '🗺️')} {matched.get('category', 'VIRTUAL TOUR').upper()}",
            "auto_dismiss_seconds": 60,
            "place": {
                "id": matched["id"],
                "name": matched["name"],
                "city": matched.get("city", ""),
                "state": matched.get("state", ""),
                "emoji": matched.get("emoji", "🗺️"),
                "gallery_images": gallery,
                "kids_hook": matched.get("kids_hook", ""),
                "kids_facts": facts,
                "curiosity_question": matched.get("curiosity_question", ""),
            },
            "media": {
                "image_url": gallery[0] if gallery else "",
                "gallery_images": gallery,
                "caption": f"📸 {matched['name']} • {matched.get('city', '')}",
            },
            "quick_facts": facts,
            "options": matched.get("action_chips", [
                {"id": "next_place", "label": "Next Jagah ➡️", "action": "next_place"},
                {"id": "sound_place", "label": "🔊 Suno", "action": "sound_place"},
            ]),
            "speech_hint": matched.get("voice_speech", "")
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        speech = matched.get("voice_speech", f"Ye dekhiye screen par {matched['name']} ki sundar tasveerein! Chalo ghoomte hain!")
        return f"{speech}\n(Instruction: Enthusiastically speak this out loud to the child now so they look at the screen photos!)"

    async def next_india_place(self) -> str:
        """Moves sequentially to the next landmark in the 52 places explorer bank."""
        self._ensure_places_state()
        if not PLACES_BANK:
            return "Chalo koi naya jagah dhoondte hain!"

        state_tour = self.session_data["places_tour"]
        idx = (state_tour.get("current_index", 0) + 1) % len(PLACES_BANK)
        next_p = PLACES_BANK[idx]
        return await self.explore_india_place(place_name=next_p["id"])
