"""
game_tools.py - Dedicated In-Memory Tools for Interactive Kids Voice Game & Quiz.
Loads questions from local JSON bank, triggers 10-second real-time bottom sheet on the mobile app,
and tracks real-time scores, streaks, and stars.
"""

import json
import logging
import os
import random
import time
from typing import Annotated, Optional, Dict, Any, List
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.game")

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "kids", "quiz_bank.json")


def load_quiz_questions() -> List[Dict[str, Any]]:
    """Loads quiz bank questions from local JSON file."""
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[KidsGame] Error loading quiz bank: {e}")
    return []


class KidsGameToolsMixin:
    """Interactive quiz, trivia game, and real-time app bottom sheet tools."""

    async def _broadcast_game_event(self, event_data: Dict[str, Any]):
        """Broadcasts structured game event to mobile/web app via WebRTC DataChannel."""
        if hasattr(self, "room") and self.room and self.room.local_participant:
            try:
                payload = json.dumps(event_data).encode("utf-8")
                await self.room.local_participant.publish_data(payload, reliable=True)
                logger.info(f"🎮 [KidsGame] Broadcast event to app: {event_data.get('type')}")
            except Exception as e:
                logger.debug(f"[KidsGame] Notice on game event broadcast: {e}")

    def _ensure_game_session(self):
        """Initializes game session state inside session_data."""
        if not self.session_data.get("game_session"):
            self.session_data["game_session"] = {
                "score": 0,
                "stars": 0,
                "total_questions_asked": 0,
                "correct_answers": 0,
                "asked_question_ids": [],
                "current_question": None,
                "streak": 0,
            }

    @llm.ai_callable(description="Ask the next interactive quiz question to the child. Automatically pops up the 10-second countdown bottom sheet in the mobile app.")
    async def ask_next_quiz_question(
        self,
        category: Annotated[str, "Question category: 'Animals', 'Space', 'Math Puzzles', 'Riddles', 'General Knowledge', 'Science', or 'any'"] = "any",
    ) -> str:
        self._ensure_game_session()
        gs = self.session_data["game_session"]
        questions = load_quiz_questions()

        if not questions:
            return "Chalo ek fun paheli poochta hoon! Aisi kaun si cheez hai jiske paas haath hain par taali nahi baja sakti? Batayiye!"

        # Filter unasked questions
        unasked = [q for q in questions if q["id"] not in gs["asked_question_ids"]]
        if not unasked:
            # If all asked, reset unasked pool
            gs["asked_question_ids"] = []
            unasked = questions

        # Filter by category if specified
        if category and category.lower() != "any":
            cat_filtered = [q for q in unasked if category.lower() in q.get("category", "").lower()]
            if cat_filtered:
                unasked = cat_filtered

        chosen = random.choice(unasked)
        gs["asked_question_ids"].append(chosen["id"])
        gs["current_question"] = chosen
        gs["total_questions_asked"] += 1

        # Broadcast event to mobile app so it immediately displays the 10s countdown bottom sheet!
        await self._broadcast_game_event({
            "type": "quiz_question",
            "id": chosen["id"],
            "category": chosen["category"],
            "question": chosen["question"],
            "options": chosen["options"],
            "time_limit_sec": chosen.get("time_limit_sec", 10),
            "points": chosen.get("points", 10),
            "total_score": gs["score"],
            "stars": gs["stars"],
        })

        self.record_tool_invocation("ask_next_quiz_question", {"question_id": chosen["id"], "category": chosen["category"]})

        options_text = " ... ".join([f"Option {i+1}: {opt}" for i, opt in enumerate(chosen["options"])])
        return (
            f"Super! Sawal {chosen['category']} se hai: '{chosen['question']}'! "
            f"Aapke paas mobile screen par 10 second ka timer shuru ho gaya hai. {options_text}. "
            "Aap bol kar ya screen par tap karke answer de sakte hain!"
        )

    @llm.ai_callable(description="Validate child's answer (spoken or option selected) for the current active quiz question.")
    async def submit_quiz_answer(
        self,
        selected_option: Annotated[str, "The option number (1, 2, 3, 4) or answer text spoken by the child"],
    ) -> str:
        self._ensure_game_session()
        gs = self.session_data["game_session"]
        curr = gs.get("current_question")

        if not curr:
            return "Abhi koi active question nahi hai. Kya aap ready hain agla sawal shuru karne ke liye?"

        clean_ans = str(selected_option).strip().lower()
        correct_idx = curr["correct_index"]
        correct_text = curr["options"][correct_idx].lower()

        # Check if matched by option number or text content
        is_correct = False
        target_numbers = [str(correct_idx + 1), f"option {correct_idx + 1}", f"number {correct_idx + 1}"]

        if any(t in clean_ans for t in target_numbers):
            is_correct = True
        elif any(word in clean_ans for word in correct_text.split() if len(word) > 2):
            is_correct = True

        points_earned = curr.get("points", 10) if is_correct else 0
        if is_correct:
            gs["score"] += points_earned
            gs["stars"] += 1
            gs["correct_answers"] += 1
            gs["streak"] += 1
        else:
            gs["streak"] = 0

        # Broadcast result event to update mobile app UI animations
        await self._broadcast_game_event({
            "type": "quiz_result",
            "question_id": curr["id"],
            "is_correct": is_correct,
            "correct_index": correct_idx,
            "correct_answer": curr["options"][correct_idx],
            "explanation": curr.get("explanation", ""),
            "score": gs["score"],
            "stars": gs["stars"],
            "streak": gs["streak"],
        })

        self.record_tool_invocation("submit_quiz_answer", {
            "question_id": curr["id"],
            "is_correct": is_correct,
            "selected": selected_option,
        })

        # Clear active question so next question can be asked
        gs["current_question"] = None

        if is_correct:
            cheers = [
                f"Arre wah! Shabash champ! 🎉 Bilkul sahi jawab! {curr['options'][correct_idx]}! Aapko milte hain {points_earned} points aur ek shiny star ⭐! Total score ho gaya hai {gs['score']}!",
                f"Balle balle! Kamaal kar diya! 🌟 Sahi jawab! {curr.get('explanation', '')} Agle sawal ke liye ready ho?",
                f"Super duper! Ekdum correct! 🎯 You got it right! Total stars: {gs['stars']} ⭐. Next question karein?"
            ]
            return random.choice(cheers)
        else:
            return (
                f"Arey, koi baat nahi! Yeh thoda tricky tha! Sahi jawab tha Option {correct_idx + 1}: '{curr['options'][correct_idx]}'. "
                f"{curr.get('explanation', '')} Koi baat nahi, champ! Agle sawal me zaroor jeetenge. Kya aap ready hain?"
            )

    @llm.ai_callable(description="Give a helpful and fun clue/hint for the current quiz question without directly revealing the answer.")
    async def give_quiz_hint(self) -> str:
        self._ensure_game_session()
        curr = self.session_data["game_session"].get("current_question")
        if not curr:
            return "Pehle agla sawal poochun, tab hint dunga!"

        hint = curr.get("voice_hint", "Socho socho, dhyan se socho!")
        return f"Aapke liye ek mazedaar hint: {hint} Ab batayiye kaun sa option sahi hai?"

    @llm.ai_callable(description="Get current quiz score, stars, streak, and performance summary.")
    async def get_game_score(self) -> str:
        self._ensure_game_session()
        gs = self.session_data["game_session"]
        score = gs["score"]
        stars = gs["stars"]
        correct = gs["correct_answers"]
        total = gs["total_questions_asked"]

        return (
            f"Aapka current score hai {score} points, aur aapne jeete hain {stars} chamakte hue stars ⭐! "
            f"Aapne total {total} me se {correct} sawalon ke ekdum sahi jawab diye hain! Bahut badhiya khel rahe ho champ!"
        )
