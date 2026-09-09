import os
import json
import logging
from typing import Annotated, Dict, Any
from livekit.agents import llm

logger = logging.getLogger("toolchain.interactive.alphabet")

KIDS_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "kids")
ALPHABET_JSON_PATH = os.path.join(KIDS_DATA_DIR, "alphabet_a_to_z_full.json")

def _load_alphabet_bank() -> Dict[str, Dict[str, Any]]:
    if os.path.exists(ALPHABET_JSON_PATH):
        try:
            with open(ALPHABET_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {ALPHABET_JSON_PATH}: {e}")
    return {}

ALPHABET_FLASHCARDS: Dict[str, Dict[str, Any]] = _load_alphabet_bank()
ALL_LETTERS = list(ALPHABET_FLASHCARDS.keys()) if ALPHABET_FLASHCARDS else [chr(c) for c in range(ord('A'), ord('Z')+1)]


class InteractiveAlphabetToolsMixin:
    """Interactive visual alphabet flashcards for kids learning (A to Z complete)."""

    def _ensure_alphabet_state(self):
        if not hasattr(self, "session_data"):
            self.session_data = {}
        if "last_alphabet" not in self.session_data:
            self.session_data["last_alphabet"] = "A"

    @llm.ai_callable(description="Show a visual alphabet learning flashcard for any letter from A to Z (e.g. A for Apple, B for Ball, ..., Z for Zebra, or 'next') with colorful illustrations, phonics, and spellings in the bottom sheet.")
    async def show_alphabet_flashcard(
        self,
        letter: Annotated[str, "The letter to show: 'A' to 'Z', or 'next' for sequential advancement"] = "A",
        word: Annotated[str, "Optional specific word like 'Apple', 'Lion', 'Tiger', 'Zebra'"] = "",
    ) -> str:
        logger.info(f"🔤 [AlphabetTool] show_alphabet_flashcard: letter='{letter}', word='{word}'")
        self.record_tool_invocation("show_alphabet_flashcard", {"letter": letter, "word": word})
        self._ensure_alphabet_state()

        clean_letter = letter.strip().upper()
        if clean_letter == "NEXT":
            current = self.session_data.get("last_alphabet", "A")
            letters = ALL_LETTERS
            next_idx = (letters.index(current) + 1) if current in letters else 0
            if next_idx >= len(letters):
                next_idx = 0
            clean_letter = letters[next_idx]

        # Match by word if letter not directly found
        if clean_letter not in ALPHABET_FLASHCARDS and word:
            w_clean = word.strip().lower()
            for k, val in ALPHABET_FLASHCARDS.items():
                if val.get("word", "").lower().startswith(w_clean):
                    clean_letter = k
                    break

        if clean_letter == "PREV":
            current = self.session_data.get("last_alphabet", "A")
            letters = ALL_LETTERS
            prev_idx = (letters.index(current) - 1) if current in letters else 0
            if prev_idx < 0:
                prev_idx = len(letters) - 1
            clean_letter = letters[prev_idx]

        if clean_letter not in ALPHABET_FLASHCARDS:
            clean_letter = "A"

        self.session_data["last_alphabet"] = clean_letter
        card = ALPHABET_FLASHCARDS[clean_letter]

        sheet_payload = {
            "action": "open",
            "sheet_id": f"alphabet_{clean_letter.lower()}",
            "component": "flashcard",
            "title": f"Letter {card.get('letter', clean_letter)}",
            "subtitle": f"{card.get('word', '')} • {card.get('hindi_meaning', '')}",
            "badge": f"{card.get('emoji', '🔤')} KIDS PHONICS",
            "auto_dismiss_seconds": 25,
            "alphabet_card": {
                "char": card.get("char", clean_letter),
                "letter": card.get("letter", clean_letter),
                "word": card.get("word", ""),
                "hindi_meaning": card.get("hindi_meaning", ""),
                "phonics": card.get("phonics", ""),
                "fun_fact": card.get("fun_fact", ""),
                "image_url": card.get("image_url", ""),
                "emoji": card.get("emoji", "✨"),
                "theme_color": card.get("theme_color", "#8b5cf6"),
                "spelling_letters": card.get("spelling_letters", list(card.get("word", "").upper())),
                "next_letter": card.get("next_letter", "B"),
                "prev_letter": card.get("prev_letter", "Z"),
            },
            "media": {
                "image_url": card.get("image_url", ""),
                "caption": card.get("phonics", ""),
                "aspect_ratio": 1.4
            },
            "quick_facts": [
                f"Phonics: {card.get('phonics', '')}",
                f"Fun Fact: {card.get('fun_fact', '')}"
            ],
            "options": [
                {"id": f"alphabet_prev", "label": "⬅️ Prev", "action": "alphabet_prev"},
                {"id": f"alphabet_next", "label": "Next Letter ➡️", "action": "alphabet_next"},
                {"id": "repeat_letter", "label": "🔊 Phonics", "action": "repeat_letter"}
            ],
            "speech_hint": card.get("speech", "")
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return card.get("speech", f"Ye dekhiye letter {clean_letter} for {card.get('word', '')}!")
