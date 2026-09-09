"""
kids_games_tools.py - Interactive Kids Games & Adaptive Voice Commentary Toolchain.

Features:
1. Tic-Tac-Toe (Zero-Kaata / X & O): 3x3 interactive board, minimax/smart move,
   win/draw detection, and live voice reaction on every child hit.
2. Memory Match Game: Cute animal card pairs (🦁, 🐘, 🐼, 🐵), card flip tracking,
   encouraging voice feedback on every match or mismatch.
3. Maths Tables (Pahade): 2 to 20 interactive visual table cards.
4. Hindi Varnamala: Swar & Vyanjan (अ से अनार, क से कबूतर) visual flashcards.
"""

import os
import json
import logging
import random
import asyncio
import time
from typing import Annotated, Dict, Any, List, Optional
from livekit.agents import llm

logger = logging.getLogger("toolchain.interactive.kids_games")

KIDS_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "kids")

def _load_kids_json(filename: str) -> List[Dict[str, Any]]:
    path = os.path.join(KIDS_DATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading {path}: {e}")
    return []

CURIOSITY_BANK = _load_kids_json("curiosity_bank.json")
RIDDLES_BANK = _load_kids_json("riddles_bank.json")
GOOD_HABITS = _load_kids_json("good_habits.json")
ROLEPLAY_MISSIONS = _load_kids_json("roleplay_missions.json")
KIDS_VIDEOS = _load_kids_json("kids_videos.json")

def _load_kids_dict(filename: str) -> Dict[str, Any]:
    path = os.path.join(KIDS_DATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading {path}: {e}")
    return {}

CURIOSITY_BANK = _load_kids_json("curiosity_bank.json")
RIDDLES_BANK = _load_kids_json("riddles_bank.json")
GOOD_HABITS = _load_kids_json("good_habits.json")
KIDS_VIDEOS: Dict[str, Any] = _load_kids_dict("kids_videos.json")

# Full Comprehensive Datasets (52 Varnamala, 1-100 Counting, Good vs Bad Habits, 365 Daily Quotes, Musical Instruments, Reading Words)
HINDI_VARNAMALA: Dict[str, Any] = _load_kids_dict("hindi_varnamala_full.json")
VARNAMALA_LETTERS = list(HINDI_VARNAMALA.keys())
COUNTING_1_TO_100: List[Dict[str, Any]] = _load_kids_json("counting_1_to_100_full.json")
GOOD_AND_BAD_HABITS: List[Dict[str, Any]] = _load_kids_json("habits_good_and_bad.json")
DAILY_QUOTES_365: List[Dict[str, Any]] = _load_kids_json("daily_quotes_365.json")
MUSICAL_DATASET: Dict[str, Any] = _load_kids_dict("musical_instruments.json")
HINDI_READING_WORDS: List[Dict[str, Any]] = _load_kids_json("hindi_reading_words.json")
ENGLISH_READING_WORDS: List[Dict[str, Any]] = _load_kids_json("english_reading_words.json")
PRIMARY_CLASS2_VOCABULARY: List[Dict[str, Any]] = _load_kids_json("primary_class2_vocabulary.json")


class KidsGamesToolsMixin:
    """Interactive games and child-adaptive educational tools with live commentary."""

    def _ensure_game_state(self):
        if not hasattr(self, "session_data"):
            self.session_data = {}
        if "tic_tac_toe" not in self.session_data:
            self.session_data["tic_tac_toe"] = {
                "board": ["", "", "", "", "", "", "", "", ""],
                "player": "X",
                "ai": "O",
                "status": "idle",
                "round": 0,
                "player_score": 0,
                "ai_score": 0
            }
        if "memory_game" not in self.session_data:
            self.session_data["memory_game"] = {
                "cards": [],
                "flipped_indices": [],
                "matched_pairs": 0,
                "total_pairs": 3,
                "status": "idle",
                "turns": 0
            }
        if "kids_gamification" not in self.session_data:
            self.session_data["kids_gamification"] = {
                "stars": 0,
                "level": 1,
                "level_title": "Junior Explorer 🥈",
                "curriculum_tier": "primary", # nursery, primary, advanced
                "topics_explored": [],
                "words_learned": [],
                "games_won": 0,
                "badges": ["Welcome Star ⭐"]
            }
        if "child_mastery" not in self.session_data:
            self.session_data["child_mastery"] = {
                "current_milestone": "milestone_1_abcd",
                "abcd_mastered": False,
                "varnamala_mastered": False,
                "counting_mastered": False,
                "phonics_mastered": False,
                "cvc_mastered": False,
                "syllables_mastered": False,
                "curriculum_level": 1,
                "correct_streak": 0,
                "completed_milestones": []
            }

    def _add_star_and_check_level(self, bonus: int = 1, reason: str = "activity_complete") -> Dict[str, Any]:
        gam = self.session_data["kids_gamification"]
        gam["stars"] += bonus
        level_up = False
        new_level = 1 + (gam["stars"] // 5)
        if new_level > gam["level"]:
            gam["level"] = new_level
            levels = {
                1: "Novice Cub 🥉",
                2: "Junior Explorer 🥈",
                3: "Master Superstar 🥇",
                4: "Grand Champion 👑"
            }
            gam["level_title"] = levels.get(gam["level"], "Superstar Genius 🌟")
            gam["badges"].append(f"Level {gam['level']}: {gam['level_title']}")
            level_up = True

        # Broadcast live star reward & celebration packet to Flutter
        if bonus > 0 and hasattr(self, "room") and self.room and self.room.local_participant:
            try:
                reward_pkt = {
                    "type": "celebration_reward",
                    "stars_earned": bonus,
                    "total_stars": gam["stars"],
                    "level": gam["level"],
                    "level_title": gam["level_title"],
                    "level_up": level_up,
                    "reason": reason,
                    "emotion": "celebrating",
                    "confetti": True
                }
                asyncio.create_task(self.room.local_participant.publish_data(
                    json.dumps(reward_pkt).encode("utf-8"),
                    reliable=True
                ))
            except Exception as ex:
                logger.debug(f"Failed to publish celebration_reward: {ex}")

        return {
            "stars": gam["stars"],
            "level": gam["level"],
            "level_title": gam["level_title"],
            "level_up": level_up,
            "curriculum_tier": gam["curriculum_tier"]
        }

    @llm.ai_callable(description="Set or change child's learning curriculum tier based on age: 'nursery' (Age 3-5, colors, sounds, rhymes), 'primary' (Age 6-8, 2-10 pahade, varnamala, stories), or 'advanced' (Age 9+, space, solar system, science riddles).")
    async def set_curriculum_tier(
        self,
        tier: Annotated[str, "Curriculum tier: 'nursery', 'primary', or 'advanced'"] = "primary"
    ) -> str:
        """Sets curriculum level and adapts learning complexity."""
        logger.info(f"📚 [KidsGame] set_curriculum_tier: tier='{tier}'")
        self.record_tool_invocation("set_curriculum_tier", {"tier": tier})
        self._ensure_game_state()

        clean = tier.lower().strip()
        if any(k in clean for k in ["nursery", "lkg", "ukg", "toddler", "chhota", "3", "4", "5"]):
            t = "nursery"
            msg = "Yaaay! Nursery & LKG mode activate ho gaya! Ab hum pyari rhymes, rang-birange colors aur animals ke sounds seekhenge! Chalo batao, lion kaise karta hai? Roaaar!"
        elif any(k in clean for k in ["adv", "bada", "science", "space", "9", "10", "11", "12"]):
            t = "advanced"
            msg = "Woohoo! Super Champ mode unlock! Ab hum Solar System, Space ke rahasya, gravity aur tough riddles solve karenge!"
        else:
            t = "primary"
            msg = "Superstar! Primary Explorer mode active hai! Ab hum 2 se 10 ke Pahade, Hindi Varnamala aur seekh bhari kahaniyan explore karenge!"

        self.session_data["kids_gamification"]["curriculum_tier"] = t
        gam_meta = self._add_star_and_check_level(0)

        sheet_payload = {
            "action": "open",
            "sheet_id": "curriculum_tier_update",
            "component": "banner",
            "title": f"Curriculum: {t.capitalize()} Explorer 🚀",
            "subtitle": f"Level: {gam_meta['level_title']} • {gam_meta['stars']} Stars",
            "badge": "CURRICULUM ACTIVE",
            "auto_dismiss_seconds": 15,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": t,
                "sfx": "level_up"
            },
            "quick_facts": [
                f"🌟 Current Tier: {t.capitalize()} Mode",
                f"🏆 Rank: {gam_meta['level_title']}",
                f"💡 Learning Focus: {msg}"
            ],
            "speech_hint": msg
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return msg

    @llm.ai_callable(description="Start or play a move in Tic-Tac-Toe (Zero-Kaata / X & O) with the child in the interactive bottom sheet. Give energetic voice commentary on every hit.")
    async def play_tic_tac_toe(
        self,
        action: Annotated[str, "Action: 'start', 'move', 'reset', or 'status'"] = "start",
        position: Annotated[int, "Position index from 0 to 8 (0=top-left, 4=center, 8=bottom-right)"] = -1,
    ) -> str:
        """Plays interactive Tic-Tac-Toe with voice reaction."""
        logger.info(f"🎮 [KidsGame] play_tic_tac_toe: action='{action}', pos={position}")
        self.record_tool_invocation("play_tic_tac_toe", {"action": action, "position": position})
        self._ensure_game_state()

        ttt = self.session_data["tic_tac_toe"]
        gam = self.session_data["kids_gamification"]

        # Reset or Start new game
        if action in ("start", "reset") or ttt["status"] in ("idle", "player_won", "ai_won", "draw"):
            ttt["board"] = ["", "", "", "", "", "", "", "", ""]
            ttt["status"] = "playing"
            ttt["round"] += 1

            welcome_msg = "Chalo Zero-Kaata (Tic-Tac-Toe) khelte hain! Tum ho 'X' aur main hoon 'O'. Apni pehli chaal chalo screen par tap karke!"
            sheet_payload = {
                "action": "open",
                "sheet_id": "game_tic_tac_toe",
                "component": "tic_tac_toe",
                "title": "Tic-Tac-Toe (Zero-Kaata)",
                "subtitle": f"Round {ttt['round']} • Tum ho X ❌ | AI hai O ⭕",
                "badge": "GAME TIME",
                "auto_dismiss_seconds": 60,
                "gamification": {
                    "stars": gam["stars"],
                    "level": gam["level"],
                    "level_title": gam["level_title"],
                    "curriculum_tier": gam["curriculum_tier"],
                    "sfx": "game_pop"
                },
                "game_data": {
                    "board": ttt["board"],
                    "player": "X",
                    "ai": "O",
                    "status": "playing",
                    "turn": "player",
                    "player_score": ttt["player_score"],
                    "ai_score": ttt["ai_score"],
                    "commentary": welcome_msg
                },
                "speech_hint": welcome_msg
            }
            if hasattr(self, "emit_interactive_sheet"):
                await self.emit_interactive_sheet(sheet_payload)
            return welcome_msg

        # Handle child move
        board = ttt["board"]
        commentary = ""

        if 0 <= position <= 8:
            if board[position] != "":
                commentary = "Arre, wo box pehle se bhara hua hai! Kisi doosre khali box par tap karo!"
            else:
                board[position] = "X"

                # Check if player won
                win_lines = [
                    (0,1,2), (3,4,5), (6,7,8), # rows
                    (0,3,6), (1,4,7), (2,5,8), # cols
                    (0,4,8), (2,4,6)           # diags
                ]
                player_won = any(board[a] == board[b] == board[c] == "X" for a, b, c in win_lines)
                if player_won:
                    ttt["status"] = "player_won"
                    ttt["player_score"] += 1
                    gam_meta = self._add_star_and_check_level(2)
                    gam["games_won"] += 1
                    sfx = "celebration_fanfare"
                    commentary = f"Hooray! Wah bhai wah! Tum jeet gaye! You earned 2 Stars ⭐! Total Stars: {gam_meta['stars']}! {gam_meta['level_title']}"
                elif "" not in board:
                    ttt["status"] = "draw"
                    gam_meta = self._add_star_and_check_level(1)
                    sfx = "match_chime"
                    commentary = "Arre waah! Zabardast muqabla! Match draw ho gaya! Dono barabar ke khiladi hain! +1 Star ⭐"
                else:
                    # AI takes a move
                    ai_pos = self._find_best_move(board)
                    sfx = "game_pop"
                    if ai_pos != -1:
                        board[ai_pos] = "O"
                        ai_won = any(board[a] == board[b] == board[c] == "O" for a, b, c in win_lines)
                        if ai_won:
                            ttt["status"] = "ai_won"
                            ttt["ai_score"] += 1
                            sfx = "game_over"
                            commentary = "Aha! Maine line bana li! Is baar main jeet gayi haha! Chalo ek aur round khelein?"
                        elif "" not in board:
                            ttt["status"] = "draw"
                            gam_meta = self._add_star_and_check_level(1)
                            sfx = "match_chime"
                            commentary = "Kya match tha! Board bhar gaya aur match draw ho gaya! +1 Star ⭐"
                        else:
                            # Dynamic commentary based on position
                            reactions = [
                                "Nice move! Par dekho maine yahan 'O' lagaya hai. Ab tumhari baari!",
                                "Oho! Tum line banane ki koshish kar rahe ho? Maine block kar diya!",
                                "Wah! Center par acchi nazar hai tumhari! Ab dekho meri chaal!",
                                "Bahut badhiya! Chalo ab agla box chun-o!"
                            ]
                            commentary = random.choice(reactions)

        sheet_payload = {
            "action": "open",
            "sheet_id": "game_tic_tac_toe",
            "component": "tic_tac_toe",
            "title": "Tic-Tac-Toe (Zero-Kaata)",
            "subtitle": f"Round {ttt['round']} • Tum ho X ❌ | AI hai O ⭕",
            "badge": "GAME TIME",
            "auto_dismiss_seconds": 60,
            "gamification": {
                "stars": gam["stars"],
                "level": gam["level"],
                "level_title": gam["level_title"],
                "curriculum_tier": gam["curriculum_tier"],
                "sfx": sfx if 'sfx' in locals() else "game_pop"
            },
            "game_data": {
                "board": ttt["board"],
                "player": "X",
                "ai": "O",
                "status": ttt["status"],
                "turn": "player",
                "player_score": ttt["player_score"],
                "ai_score": ttt["ai_score"],
                "commentary": commentary
            },
            "speech_hint": commentary
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return commentary

    def _find_best_move(self, board: List[str]) -> int:
        """Finds smart/adaptive move for AI."""
        win_lines = [
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
        ]
        # 1. Can AI win right now?
        for a, b, c in win_lines:
            vals = [board[a], board[b], board[c]]
            if vals.count("O") == 2 and vals.count("") == 1:
                for idx in (a, b, c):
                    if board[idx] == "":
                        return idx
        # 2. Must AI block player from winning?
        for a, b, c in win_lines:
            vals = [board[a], board[b], board[c]]
            if vals.count("X") == 2 and vals.count("") == 1:
                for idx in (a, b, c):
                    if board[idx] == "":
                        return idx
        # 3. Take center if available
        if board[4] == "":
            return 4
        # 4. Take random available spot
        available = [i for i, v in enumerate(board) if v == ""]
        return random.choice(available) if available else -1

    @llm.ai_callable(description="Start or play Memory Match Card Flip Game with the child in the bottom sheet. React energetically to every card tap.")
    async def play_memory_game(
        self,
        action: Annotated[str, "Action: 'start', 'flip', 'reset'"] = "start",
        card_index: Annotated[int, "Card index tapped by child (0 to 5)"] = -1,
    ) -> str:
        """Plays interactive Memory Card Match with cute animals and live vocal cheer."""
        logger.info(f"🃏 [KidsGame] play_memory_game: action='{action}', card_idx={card_index}")
        self.record_tool_invocation("play_memory_game", {"action": action, "card_index": card_index})
        self._ensure_game_state()

        mem = self.session_data["memory_game"]
        gam = self.session_data["kids_gamification"]
        sfx = "card_flip"

        if action in ("start", "reset") or not mem["cards"]:
            symbols = ["🦁", "🐘", "🐼"]
            deck = symbols * 2
            random.shuffle(deck)
            mem["cards"] = [{"id": i, "symbol": s, "is_matched": False, "is_flipped": False} for i, s in enumerate(deck)]
            mem["flipped_indices"] = []
            mem["matched_pairs"] = 0
            mem["total_pairs"] = len(symbols)
            mem["status"] = "playing"
            mem["turns"] = 0

            msg = "Chalo Memory Match game khelte hain! Parde ke peeche 3 pyare jaanwar chupe hain. Do ek jaise cards dhoondho! Kisi bhi card par tap karo!"
            sheet_payload = {
                "action": "open",
                "sheet_id": "game_memory_match",
                "component": "memory_match",
                "title": "Memory Match Game 🃏",
                "subtitle": f"Matched: 0/{mem['total_pairs']} Pairs",
                "badge": "BRAIN GAME",
                "auto_dismiss_seconds": 60,
                "gamification": {
                    "stars": gam["stars"],
                    "level": gam["level"],
                    "level_title": gam["level_title"],
                    "curriculum_tier": gam["curriculum_tier"],
                    "sfx": "game_pop"
                },
                "game_data": {
                    "cards": mem["cards"],
                    "matched_pairs": 0,
                    "total_pairs": mem["total_pairs"],
                    "status": "playing",
                    "commentary": msg
                },
                "speech_hint": msg
            }
            if hasattr(self, "emit_interactive_sheet"):
                await self.emit_interactive_sheet(sheet_payload)
            return msg

        # Card flip handling
        commentary = ""
        cards = mem["cards"]
        flipped = mem["flipped_indices"]

        if 0 <= card_index < len(cards):
            card = cards[card_index]
            if not card["is_matched"] and not card["is_flipped"]:
                card["is_flipped"] = True
                flipped.append(card_index)

                if len(flipped) == 1:
                    commentary = f"Aha! Tumne khola {card['symbol']}! Ab iska doosra jodi-daar dhoondho!"
                    sfx = "card_flip"
                elif len(flipped) == 2:
                    mem["turns"] += 1
                    c1 = cards[flipped[0]]
                    c2 = cards[flipped[1]]
                    if c1["symbol"] == c2["symbol"]:
                        c1["is_matched"] = True
                        c2["is_matched"] = True
                        mem["matched_pairs"] += 1
                        flipped.clear()

                        if mem["matched_pairs"] == mem["total_pairs"]:
                            mem["status"] = "won"
                            gam_meta = self._add_star_and_check_level(3)
                            gam["games_won"] += 1
                            sfx = "celebration_fanfare"
                            commentary = f"Balle Balle! Kamaal kar diya! Tumne sabhi pairs dhoond liye! You won 3 stars ⭐! Total stars: {gam_meta['stars']}! {gam_meta['level_title']}"
                        else:
                            gam_meta = self._add_star_and_check_level(1)
                            sfx = "match_chime"
                            commentary = f"Wah bhai wah! Dono {c1['symbol']} match ho gaye! +1 Star ⭐! Agla card kholo!"
                    else:
                        commentary = f"Oops! Ek {c1['symbol']} aur ek {c2['symbol']} tha. Dhyan se yaad rakhna kaun kahan tha!"
                        sfx = "game_pop"
                        c1["is_flipped"] = False
                        c2["is_flipped"] = False
                        flipped.clear()

        sheet_payload = {
            "action": "open",
            "sheet_id": "game_memory_match",
            "component": "memory_match",
            "title": "Memory Match Game 🃏",
            "subtitle": f"Matched: {mem['matched_pairs']}/{mem['total_pairs']} Pairs",
            "badge": "BRAIN GAME",
            "auto_dismiss_seconds": 60,
            "gamification": {
                "stars": gam["stars"],
                "level": gam["level"],
                "level_title": gam["level_title"],
                "curriculum_tier": gam["curriculum_tier"],
                "sfx": sfx
            },
            "game_data": {
                "cards": cards,
                "matched_pairs": mem["matched_pairs"],
                "total_pairs": mem["total_pairs"],
                "status": mem["status"],
                "commentary": commentary
            },
            "speech_hint": commentary
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return commentary

    @llm.ai_callable(description="Teach child Maths Tables (Pahade e.g., 2 ka pahada, 3 ka pahada, 5 ka pahada) with a vibrant visual card in the bottom sheet.")
    async def teach_maths_tables(
        self,
        number: Annotated[int, "The multiplication table number to teach (e.g. 2, 3, 4, 5, 10)"] = 2,
    ) -> str:
        """Teaches multiplication tables with colorful step-by-step visual card."""
        logger.info(f"🔢 [KidsGame] teach_maths_tables: num={number}")
        self.record_tool_invocation("teach_maths_tables", {"number": number})
        self._ensure_game_state()

        num = max(1, min(20, number))
        steps = [f"{num} × {i} = {num * i}" for i in range(1, 11)]
        spoken = f"Chalo sikhte hain {num} ka pahada! {num} ekam {num}, {num} dooni {num*2}, {num} tiya {num*3}, {num} chauke {num*4}, {num} panje {num*5}!"

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Maths Table of {num}")
        gam_meta = self._add_star_and_check_level(1)

        sheet_payload = {
            "action": "open",
            "sheet_id": f"maths_table_{num}",
            "component": "maths_table",
            "title": f"Maths Table of {num} • {num} का पहाड़ा",
            "subtitle": f"Learn & Recite Together 🧮 • {gam_meta['level_title']}",
            "badge": "MATHS MAGIC",
            "auto_dismiss_seconds": 30,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "match_chime"
            },
            "table_data": {
                "number": num,
                "steps": steps,
                "title": f"Table of {num}",
                "tip": f"Pro Tip: Har step me {num} jodte jao!"
            },
            "speech_hint": spoken
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return spoken

    @llm.ai_callable(
        description="Teach child Hindi Varnamala letters (all 52 Swar & Vyanjan like अ से अनार, आ से आम, क से कबूतर, ख से खरगोश, ग से गमला, ज्ञ से ज्ञानी, or 'next' for sequential letter) with visual cards, illustrations, and phonetics."
    )
    async def teach_hindi_varnamala(
        self,
        letter: Annotated[str, "The Hindi letter e.g., 'क', 'ख', 'अ', 'आ', 'च', 'ट', 'ज्ञ', or 'next'"] = "क",
    ) -> str:
        """Teaches Hindi Varnamala with picture and phonetics in bottom sheet (all 52 letters)."""
        logger.info(f"🔤 [KidsGame] teach_hindi_varnamala: letter='{letter}'")
        self.record_tool_invocation("teach_hindi_varnamala", {"letter": letter})
        self._ensure_game_state()

        clean_letter = letter.strip()
        if clean_letter.lower() in ["next", "agla", "aur", "next_varnamala"]:
            current = self.session_data.get("last_varnamala", "अ")
            idx = (VARNAMALA_LETTERS.index(current) + 1) if current in VARNAMALA_LETTERS else 0
            if idx >= len(VARNAMALA_LETTERS):
                idx = 0
            clean_letter = VARNAMALA_LETTERS[idx]
        elif clean_letter.lower() in ["prev", "pichla", "peeche", "prev_varnamala"]:
            current = self.session_data.get("last_varnamala", "अ")
            idx = (VARNAMALA_LETTERS.index(current) - 1) if current in VARNAMALA_LETTERS else 0
            if idx < 0:
                idx = len(VARNAMALA_LETTERS) - 1
            clean_letter = VARNAMALA_LETTERS[idx]

        matched = HINDI_VARNAMALA.get(clean_letter)
        if not matched:
            # Match by word if letter not directly found
            for k, v in HINDI_VARNAMALA.items():
                if clean_letter in v.get("word", "") or clean_letter in v.get("english", "").lower():
                    matched = v
                    break
        if not matched and HINDI_VARNAMALA:
            matched = HINDI_VARNAMALA.get("क") or list(HINDI_VARNAMALA.values())[0]

        self.session_data["last_varnamala"] = matched["letter"]

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Hindi Varnamala: {matched['letter']}")
        gam["words_learned"].append(matched["word"])
        gam_meta = self._add_star_and_check_level(1)

        sheet_payload = {
            "action": "open",
            "sheet_id": f"varnamala_{matched['letter']}",
            "component": "hindi_varnamala",
            "title": f"हिन्दी वर्णमाला: {matched['letter']}",
            "subtitle": f"{matched['word']} • {matched['english']}",
            "badge": "HINDI VARNAMALA 🔤",
            "auto_dismiss_seconds": 35,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "match_chime"
            },
            "media": {
                "image_url": matched["image_url"],
                "caption": matched["fun_fact"],
                "aspect_ratio": 1.4
            },
            "varnamala_data": matched,
            "actions": [
                {"id": "prev_varnamala", "label": "⬅️ Prev", "action": "prev_varnamala"},
                {"id": "next_varnamala", "label": "Next ➡️", "action": "next_varnamala"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ],
            "speech_hint": matched["speech"]
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return matched["speech"]

    @llm.ai_callable(
        description="Teach counting from 1 to 100 in Hindi and English (e.g. 1 to 10, 11 to 20, 21 to 30, up to 100, or a specific number) with numbers table, pronunciations, and visual cards."
    )
    async def teach_counting_1_to_100(
        self,
        start_num: Annotated[int, "Starting number (1 to 100), e.g. 1 for 1-10, 11 for 11-20, 91 for 91-100"] = 1,
        count: Annotated[int, "How many numbers to recite/show (e.g. 10)"] = 10,
    ) -> str:
        """Teaches counting 1 to 100 in Hindi & English in the interactive bottom sheet."""
        logger.info(f"🔢 [KidsGame] teach_counting_1_to_100: start={start_num}, count={count}")
        self.record_tool_invocation("teach_counting_1_to_100", {"start_num": start_num, "count": count})
        self._ensure_game_state()

        start = max(1, min(100, start_num))
        end = min(100, start + count - 1)

        selected_slice = [n for n in COUNTING_1_TO_100 if start <= n["number"] <= end]
        if not selected_slice:
            selected_slice = COUNTING_1_TO_100[:10]

        steps = [f"{item['number']}: {item['english_name']} • {item['hindi_name']} ({item['roman_hindi']})" for item in selected_slice]
        spoken_numbers = ", ".join([f"{item['number']} ({item['roman_hindi']})" for item in selected_slice[:5]])
        spoken = f"Chalo ginti sikhte hain {start} se {end} tak! {spoken_numbers}, aur aage tak! Screen par poori list dekhiye!"

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Counting {start}-{end}")
        gam_meta = self._add_star_and_check_level(1)

        sheet_payload = {
            "action": "open",
            "sheet_id": f"counting_{start}_{end}",
            "component": "maths_table",
            "title": f"Numbers Counting: {start} to {end}",
            "subtitle": f"English & Hindi Pronunciation • 1 to 100",
            "badge": "1-100 COUNTING 🔢",
            "auto_dismiss_seconds": 35,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "match_chime"
            },
            "table_data": {
                "number": start,
                "steps": steps,
                "title": f"Counting {start} to {end}",
                "tip": f"Pro Tip: Har number ko Hindi aur English dono me bolo!"
            },
            "actions": [
                {"id": f"prev_counting_{max(1, start-10)}", "label": "⬅️ Prev 10", "action": "prev_counting"},
                {"id": f"next_counting_{min(91, end+1)}", "label": "Next 10 ➡️", "action": "next_counting"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ],
            "speech_hint": spoken
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return spoken

    @llm.ai_callable(
        description="Teach child Good Habits vs Bad Habits (brushing teeth, hand wash, screen time, sleep early, healthy food) with comparison card and golden rules."
    )
    async def teach_good_and_bad_habit(
        self,
        habit_topic: Annotated[str, "The habit topic, e.g. 'brush', 'handwash', 'screen', 'sleep', 'food'"] = "brush",
    ) -> str:
        """Presents Good Habit vs Bad Habit comparison card with marquee golden rules and karaoke rhyme."""
        logger.info(f"🌟 [KidsGame] teach_good_and_bad_habit: topic='{habit_topic}'")
        self.record_tool_invocation("teach_good_and_bad_habit", {"habit_topic": habit_topic})
        self._ensure_game_state()

        clean = habit_topic.lower().strip()
        matched = None
        if clean in ["next", "next_habit", "dusra", "aage", "aur"]:
            curr_idx = self.session_data.get("last_habit_idx", 0)
            curr_idx = (curr_idx + 1) % len(GOOD_AND_BAD_HABITS)
            matched = GOOD_AND_BAD_HABITS[curr_idx]
            self.session_data["last_habit_idx"] = curr_idx
        elif clean in ["prev", "prev_habit", "pichla", "peeche", "back"]:
            curr_idx = self.session_data.get("last_habit_idx", 0)
            curr_idx = (curr_idx - 1) % len(GOOD_AND_BAD_HABITS)
            matched = GOOD_AND_BAD_HABITS[curr_idx]
            self.session_data["last_habit_idx"] = curr_idx
        else:
            for idx, h in enumerate(GOOD_AND_BAD_HABITS):
                if any(k in clean for k in h.get("keywords", [])):
                    matched = h
                    self.session_data["last_habit_idx"] = idx
                    break
            if not matched and GOOD_AND_BAD_HABITS:
                matched = GOOD_AND_BAD_HABITS[0]
                self.session_data["last_habit_idx"] = 0

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Habit: {matched['title']}")
        gam_meta = self._add_star_and_check_level(1)

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "sheet_id": f"habit_{matched.get('id', '1')}",
            "component": "good_bad_habit",
            "title": f"Good vs Bad Habit: {matched.get('title', 'Habit')}",
            "subtitle": f"Superhero Reward: {matched.get('superhero_reward', 'Golden Star ⭐')}",
            "badge": "GOOD VS BAD HABIT 🌟",
            "auto_dismiss_seconds": 45,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "celebration_fanfare"
            },
            "good_habit": {
                "title": "GOOD HABIT (DO)",
                "text": matched.get("good_habit", ""),
                "image_url": matched.get("good_image_url", matched.get("image_url", "")),
                "badge": "🟢 DO THIS"
            },
            "bad_habit": {
                "title": "BAD HABIT (DON'T)",
                "text": matched.get("bad_habit", ""),
                "why_bad": matched.get("why_bad", ""),
                "image_url": matched.get("bad_image_url", "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=600&auto=format&fit=crop&q=80"),
                "badge": "🔴 DON'T DO THIS"
            },
            "marquee_ticker": matched.get("marquee_items", [
                f"🟢 DO: {matched.get('good_habit', '')}",
                f"🔴 DON'T: {matched.get('bad_habit', '')}",
                f"🦸 GOLDEN RULE: {matched.get('kid_rule', '')}",
                f"⭐ REWARD: {matched.get('superhero_reward', '')}"
            ]),
            "karaoke": matched.get("karaoke", {
                "rhyme_title": f"🎶 {matched.get('title', 'Habit')} Rhyme",
                "lyrics": matched.get("speech", ""),
                "words": matched.get("speech", "").split()
            }),
            "kid_rule": matched.get("kid_rule", ""),
            "superhero_reward": matched.get("superhero_reward", "Golden Star ⭐"),
            "quick_facts": [
                f"✅ GOOD HABIT: {matched.get('good_habit', '')}",
                f"❌ BAD HABIT: {matched.get('bad_habit', '')}",
                f"⚠️ KYUN BURA HAI: {matched.get('why_bad', '')}",
                f"🦸 GOLDEN RULE: {matched.get('kid_rule', '')}"
            ],
            "actions": [
                {"id": "prev_habit", "label": "⬅️ Prev", "action": "prev_habit"},
                {"id": "next_habit", "label": "Next ➡️", "action": "next_habit"},
                {"id": "sing_karaoke", "label": "🎤 Karaoke Gaao", "action": "sing_karaoke"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ],
            "speech_hint": matched.get("speech", "")
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return matched.get("speech", "Aao achhi aadatein seekhein!")

    async def connect_friend_from_city(
        self,
        city: Annotated[str, "The city requested by the child, e.g. 'Delhi', 'Mumbai'"] = "Delhi",
    ) -> str:
        """Connects child to a live friend from the requested city via LiveKit room bridge."""
        logger.info(f"📞 [KidsTool] connect_friend_from_city: city='{city}'")
        self.record_tool_invocation("connect_friend_from_city", {"city": city})

        room_name = getattr(getattr(self, "room", None), "name", None) or getattr(self, "call_session_id", "call_room")
        api_url = getattr(self, "api_base_url", "http://localhost:5063")
        caller_id = getattr(self, "user_id", "")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "roomName": room_name,
                    "city": city,
                    "desiredGender": "any",
                    "requirement": "kids friendly chat",
                    "callerUserId": caller_id
                }
                async with session.post(f"{api_url}/api/ai/bridge-call", json=payload, timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            host_name = data.get("hostUsername", "Dost")
                            return f"Bilkul champ! Maine {city} ke online dost @{host_name} ko call ring kar di hai! Bas 2 second line pe rahiye, wo connect ho rahe hain!"
                        return f"Arre champ, abhi {city} se koi dost online nahi hai. Thodi der me call lagayein ya tab tak mast cartoon video dekhein?"
        except Exception as e:
            logger.error(f"Error bridging friend from {city}: {e}", exc_info=True)

        return f"Champ, maine {city} me call connect karne ki koshish ki hai! Line pe bane rahiye!"

    async def get_daily_quote(
        self,
        day_or_topic: Annotated[str, "Day of year ('today', '1' to '365')"] = "today",
    ) -> str:
        """Presents 365-day Daily Kid Quote banner in bottom sheet with moral lesson and 2 stars."""
        from datetime import datetime, timezone, timedelta
        logger.info(f"📜 [KidsGame] get_daily_quote: query='{day_or_topic}'")
        self.record_tool_invocation("get_daily_quote", {"query": day_or_topic})
        self._ensure_game_state()

        # IST timezone
        ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        current_day_of_year = ist_now.timetuple().tm_yday
        today_date_str = ist_now.strftime("%m-%d")

        clean = (day_or_topic or "").lower().strip()
        matched = None

        if clean in ["next", "next_quote", "kal", "agla"]:
            curr_day = self.session_data.get("last_quote_day", current_day_of_year)
            next_day = (curr_day % 365) + 1
            matched = next((q for q in DAILY_QUOTES_365 if q.get("day") == next_day), None)
            self.session_data["last_quote_day"] = next_day
        elif clean in ["prev", "prev_quote", "pichla", "kal_ka"]:
            curr_day = self.session_data.get("last_quote_day", current_day_of_year)
            prev_day = 365 if curr_day <= 1 else curr_day - 1
            matched = next((q for q in DAILY_QUOTES_365 if q.get("day") == prev_day), None)
            self.session_data["last_quote_day"] = prev_day
        elif clean.isdigit():
            day_num = int(clean)
            matched = next((q for q in DAILY_QUOTES_365 if q.get("day") == day_num), None)
            if matched:
                self.session_data["last_quote_day"] = day_num
        elif clean in ["today", "aaj", "daily", "quote", "aaj ka quote", "today quote"]:
            matched = next((q for q in DAILY_QUOTES_365 if q.get("date") == today_date_str), None)
            if not matched:
                matched = next((q for q in DAILY_QUOTES_365 if q.get("day") == current_day_of_year), None)
            if matched:
                self.session_data["last_quote_day"] = matched.get("day", current_day_of_year)
        else:
            # Match by theme
            for q in DAILY_QUOTES_365:
                if clean in q.get("theme", "").lower() or clean in q.get("theme_hindi", "").lower() or clean in q.get("author_or_character", "").lower():
                    matched = q
                    self.session_data["last_quote_day"] = q.get("day", current_day_of_year)
                    break

        if not matched and DAILY_QUOTES_365:
            matched = DAILY_QUOTES_365[(current_day_of_year - 1) % len(DAILY_QUOTES_365)]
            self.session_data["last_quote_day"] = matched.get("day", current_day_of_year)

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Daily Quote: Day {matched['day']}")
        gam_meta = self._add_star_and_check_level(2)

        sheet_payload = {
            "action": "open",
            "sheet_id": f"quote_day_{matched['day']}",
            "component": "media_card",
            "title": f"🌟 Aaj Ka Jadooi Quote (Day {matched['day']} of 365)",
            "subtitle": f"Theme: {matched['theme_hindi']} ({matched['theme']})",
            "badge": f"DAY {matched['day']} QUOTE 📜",
            "auto_dismiss_seconds": 40,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "celebration_fanfare"
            },
            "media": {
                "image_url": matched["image_url"],
                "caption": f"\"{matched['quote_english']}\"\n— {matched['author_or_character']}",
                "aspect_ratio": 1.4
            },
            "quick_facts": [
                f"📜 HINDI: {matched['quote_hindi']}",
                f"🗣️ AUTHOR: {matched['author_or_character']}",
                f"🎯 TODAY'S MISSION: {matched['kid_takeaway']}",
                f"⭐ REWARD: +2 Learning Stars awarded!"
            ],
            "actions": [
                {"id": "prev_quote", "label": "⬅️ Prev", "action": "prev_quote"},
                {"id": "next_quote", "label": "Next ➡️", "action": "next_quote"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ],
            "speech_hint": matched["speech"]
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return matched["speech"]

    @llm.ai_callable(description="Answer child's 'Kyun?' (Why?) curiosity questions (e.g. why sky is blue, why fish live in water, where sun goes at night, why stars twinkle) with a fun physical metaphor and visual card.")
    async def answer_kids_curiosity(
        self,
        question_or_topic: Annotated[str, "The child's question or topic keyword e.g. 'aasman neela', 'sooraj raat', 'machhli', 'taare'"] = "aasman neela",
    ) -> str:
        """Explains kids why questions using relatable metaphors with 0 Groq tokens."""
        logger.info(f"🧠 [KidsGame] answer_kids_curiosity: topic='{question_or_topic}'")
        self.record_tool_invocation("answer_kids_curiosity", {"question_or_topic": question_or_topic})
        self._ensure_game_state()

        clean = question_or_topic.lower().strip()
        matched = None
        for item in CURIOSITY_BANK:
            if any(k in clean for k in item.get("keywords", [])):
                matched = item
                break
        if not matched and CURIOSITY_BANK:
            matched = CURIOSITY_BANK[0]

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Curiosity: {matched['question']}")
        gam_meta = self._add_star_and_check_level(1)

        sheet_payload = {
            "action": "open",
            "sheet_id": f"curiosity_{matched['id']}",
            "component": "media_card",
            "title": matched["question"],
            "subtitle": f"🌟 {matched['simple_explanation']}",
            "badge": "LITTLE SCIENTIST 🔬",
            "auto_dismiss_seconds": 30,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "match_chime"
            },
            "media": {
                "image_url": matched["image_url"],
                "caption": f"💡 Fun Fact: {matched['fun_fact']}",
                "aspect_ratio": 1.4
            },
            "speech_hint": matched["speech"]
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return matched["speech"]

    @llm.ai_callable(description="Ask the child an interactive Hindi Paheli (Riddle) with 4 clickable options on the screen and voice evaluation.")
    async def ask_kids_riddle(
        self,
        topic: Annotated[str, "Optional topic for riddle e.g. 'animals', 'fruits', or 'random'"] = "random",
    ) -> str:
        """Presents an interactive 4-option Hindi riddle on bottom sheet."""
        logger.info(f"🧩 [KidsGame] ask_kids_riddle: topic='{topic}'")
        self.record_tool_invocation("ask_kids_riddle", {"topic": topic})
        self._ensure_game_state()

        if not RIDDLES_BANK:
            return "Chalo ek paheli puchte hain: Hara hoon par tota nahi... Batao kya? Tarbooz!"

        riddle = random.choice(RIDDLES_BANK)
        self.session_data["current_riddle"] = riddle
        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append("Hindi Paheli (Riddle)")

        options = [
            {"id": f"riddle_opt_{i}", "label": opt}
            for i, opt in enumerate(riddle.get("options", []))
        ]

        sheet_payload = {
            "action": "open",
            "sheet_id": f"riddle_{riddle['id']}",
            "component": "quiz",
            "title": "Hindi Paheli 🧩",
            "subtitle": riddle["riddle"],
            "badge": "SOLVE & WIN ⭐",
            "auto_dismiss_seconds": 45,
            "gamification": {
                "stars": gam["stars"],
                "level": gam["level"],
                "level_title": gam["level_title"],
                "curriculum_tier": gam["curriculum_tier"],
                "sfx": "game_pop"
            },
            "question": {
                "id": riddle["id"],
                "text": riddle["riddle"],
                "options": options,
                "hint": riddle.get("hint", "")
            },
            "speech_hint": f"Paheli suno dhyan se: {riddle['riddle']} Options screen par hain, sahi option par tap karo!"
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return f"Paheli suno dhyan se: {riddle['riddle']} Screen par 4 options hain, batao kaun sa sahi hai!"

    @llm.ai_callable(description="Validate child's answer to the active riddle and reward stars.")
    async def solve_kids_riddle(
        self,
        answer: Annotated[str, "The child's answer or tapped option index/text e.g. 'Khargosh', 'Tarbooz', or '0'"] = "",
    ) -> str:
        """Checks riddle answer locally with 0 Groq tokens and awards stars."""
        logger.info(f"🧩 [KidsGame] solve_kids_riddle: answer='{answer}'")
        self.record_tool_invocation("solve_kids_riddle", {"answer": answer})
        self._ensure_game_state()

        riddle = self.session_data.get("current_riddle")
        if not riddle:
            return "Arre wah! Aapne bahut achha try kiya! Agli paheli ke liye bolo: Ek aur paheli pucho!"

        clean_ans = str(answer).lower().strip()
        correct_opt = riddle.get("correct_option", "").lower()
        correct_idx = str(riddle.get("correct_index", 0))

        is_correct = (
            correct_opt in clean_ans
            or clean_ans in correct_opt
            or f"riddle_opt_{correct_idx}" in clean_ans
            or clean_ans == correct_idx
        )

        gam = self.session_data["kids_gamification"]
        if is_correct:
            gam_meta = self._add_star_and_check_level(1)
            gam["games_won"] += 1
            sfx = "celebration_fanfare"
            reply = riddle.get("celebration", f"Arre wah superstar! Sahi jawab! Total Stars: {gam_meta['stars']} ⭐!")
        else:
            sfx = "game_pop"
            reply = riddle.get("wrong_cheer", f"Thoda sa socho champ! Hint: {riddle.get('hint', '')} Ek baar fir try karo!")

        sheet_update = {
            "action": "update",
            "sheet_id": f"riddle_{riddle['id']}",
            "gamification": {
                "stars": gam["stars"],
                "level": gam["level"],
                "level_title": gam["level_title"],
                "curriculum_tier": gam["curriculum_tier"],
                "sfx": sfx
            },
            "feedback": {
                "is_correct": is_correct,
                "message": reply
            }
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_update)

        return reply

    @llm.ai_callable(description="Teach child essential good habits and moral values (e.g. brushing twice, handwash rule, 4 magic words, eating veggies, clean up toys) with fun rules and rhymes.")
    async def teach_good_habit(
        self,
        habit_topic: Annotated[str, "Habit topic: 'brush', 'handwash', 'magic_words', 'veggies', or 'toys'"] = "brush",
    ) -> str:
        """Teaches daily good habits and etiquette with visual card."""
        logger.info(f"🌱 [KidsGame] teach_good_habit: topic='{habit_topic}'")
        self.record_tool_invocation("teach_good_habit", {"habit_topic": habit_topic})
        self._ensure_game_state()

        clean = habit_topic.lower().strip()
        matched = None
        for h in GOOD_HABITS:
            if any(k in clean for k in h.get("keywords", [])):
                matched = h
                break
        if not matched and GOOD_HABITS:
            matched = GOOD_HABITS[0]

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Good Habit: {matched['title']}")
        gam_meta = self._add_star_and_check_level(1)

        sheet_payload = {
            "action": "open",
            "sheet_id": f"habit_{matched['id']}",
            "component": "media_card",
            "title": matched["title"],
            "subtitle": f"🌟 {matched['rule']}",
            "badge": "GOOD HABITS 🌱",
            "auto_dismiss_seconds": 30,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "match_chime"
            },
            "media": {
                "image_url": matched["image_url"],
                "caption": f"🎵 Rhyme: {matched['rhyme']}",
                "aspect_ratio": 1.4
            },
            "speech_hint": matched["speech"]
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return matched["speech"]

    async def start_roleplay_adventure(
        self,
        mission: Annotated[str, "Mission type: 'space', 'jungle', or 'chef'"] = "space",
    ) -> str:
        """Launches interactive roleplay mission with step-by-step guidance."""
        logger.info(f"🚀 [KidsGame] start_roleplay_adventure: mission='{mission}'")
        self.record_tool_invocation("start_roleplay_adventure", {"mission": mission})
        self._ensure_game_state()

        clean = mission.lower().strip()
        matched = None
        for m in ROLEPLAY_MISSIONS:
            if any(k in clean for k in m.get("keywords", [])):
                matched = m
                break
        if not matched and ROLEPLAY_MISSIONS:
            matched = ROLEPLAY_MISSIONS[0]

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Roleplay: {matched['title']}")
        gam_meta = self._add_star_and_check_level(2)

        steps = matched.get("steps", [])
        step1 = steps[0] if steps else {}

        sheet_payload = {
            "action": "open",
            "sheet_id": f"roleplay_{matched['id']}",
            "component": "media_card",
            "title": matched["title"],
            "subtitle": f"You: {matched['role_child']} • AI: {matched['role_ai']}",
            "badge": "ROLEPLAY MISSION 🚀",
            "auto_dismiss_seconds": 45,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": step1.get("sfx", "celebration_fanfare")
            },
            "media": {
                "image_url": matched["image_url"],
                "caption": f"Step 1: {step1.get('instruction', '')}",
                "aspect_ratio": 1.4
            },
            "speech_hint": step1.get("speech", "")
        }
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return step1.get("speech", f"Chalo {matched['title']} shuru karte hain! Kya aap ready ho?")

    async def play_kids_video(
        self,
        topic: Annotated[str, "The video topic, e.g. 'chanda mama', 'rhyme'"] = "rhyme",
    ) -> str:
        """Plays high-definition educational cartoon video in the dynamic bottom sheet."""
        logger.info(f"📺 [KidsGame] play_kids_video: topic='{topic}'")
        self.record_tool_invocation("play_kids_video", {"topic": topic})
        self._ensure_game_state()

        if not KIDS_VIDEOS:
            return "Arre, abhi mere paas videos load nahi ho paayi hain! Kya hum pyara Zero-Kaata game khelein?"

        clean = (topic or "").lower().strip()

        # Handle 'next' or 'prev' action
        current_idx = getattr(self, "_current_video_idx", 0)
        if clean in ["next", "next_video", "dusra", "aur", "change"]:
            current_idx = (current_idx + 1) % len(KIDS_VIDEOS)
            selected = KIDS_VIDEOS[current_idx]
            self._current_video_idx = current_idx
        elif clean in ["prev", "prev_video", "pichla", "back"]:
            current_idx = (current_idx - 1) % len(KIDS_VIDEOS)
            selected = KIDS_VIDEOS[current_idx]
            self._current_video_idx = current_idx
        else:
            selected = None
            # Explicit matching
            for v in KIDS_VIDEOS:
                v_title = v.get("title", "").lower()
                v_topic = v.get("topic", "").lower()
                v_desc = v.get("description", "").lower()

                if clean not in ["video", "dikhao", "video dikhao", "cartoon", "poem", "rhyme"] and (clean in v_topic or clean in v_title or clean in v_desc):
                    selected = v
                    break
                if any(w in clean for w in ["chanda", "mama", "lori", "bedtime"]) and "chanda" in v.get("id", ""):
                    selected = v
                    break
                if any(w in clean for w in ["abc", "abcd", "alphabet", "phonics"]) and "abc" in v.get("id", ""):
                    selected = v
                    break
                if any(w in clean for w in ["number", "counting", "ginti", "train"]) and "number" in v.get("id", ""):
                    selected = v
                    break
                if any(w in clean for w in ["planet", "solar", "suraj", "space", "antariksh"]) and "solar" in v.get("id", ""):
                    selected = v
                    break
                if any(w in clean for w in ["crow", "kauwa", "kahani", "story", "thirsty"]) and "crow" in v.get("id", ""):
                    selected = v
                    break
                if any(w in clean for w in ["color", "rang", "shape"]) and "color" in v.get("id", ""):
                    selected = v
                    break
                if any(w in clean for w in ["varnamala", "hindi", "kabootar"]) and "varnamala" in v.get("id", ""):
                    selected = v
                    break
                if any(w in clean for w in ["animal", "sound", "janwar", "lion", "safari"]) and "animal" in v.get("id", ""):
                    selected = v
                    break

            if not selected:
                # Default to selected index (e.g. Chanda Mama or ABC Phonics)
                selected = KIDS_VIDEOS[current_idx % len(KIDS_VIDEOS)]
                self._current_video_idx = (current_idx + 1) % len(KIDS_VIDEOS)

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Video: {selected.get('title')}")
        gam_meta = self._add_star_and_check_level(2)

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "media_player",
            "media_type": "video",
            "sheet_id": f"vid_{selected.get('id')}",
            "title": selected.get("title"),
            "topic": selected.get("topic", "kids"),
            "duration": selected.get("duration", "3:00"),
            "video_url": selected.get("video_url"),
            "youtube_id": selected.get("youtube_id"),
            "thumbnail_url": selected.get("thumbnail_url"),
            "description": selected.get("description", ""),
            "badge": "CARTOON VIDEO 🎬",
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "celebration_fanfare"
            },
            "actions": [
                {"id": "prev_video", "label": "⬅️ Prev", "action": "prev_video"},
                {"id": "next_video", "label": "Next ➡️", "action": "next_video"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        # Cheerful, 100% FEMININE voice response
        return (
            f"Yaaay! Maine aapke liye '{selected.get('title')}' video screen par chala di hai! "
            f"Dekhiye kitna pyara video hai! Aap ise aaram se enjoy kijiye, main yahin aapke paas baithi hoon!"
        )

    async def play_musical_instrument(
        self,
        instrument_name: Annotated[str, "Name of instrument, e.g. 'Piano', 'Tabla', 'Bansuri', 'Guitar', 'Dholak', 'Xylophone', 'Drums', 'Sitar'"] = "piano",
        note: Annotated[str, "Note to sound, e.g. 'Sa', 'Re', 'Ga', 'Ma', 'Pa', 'Dha', 'Ni' or empty"] = "",
    ) -> str:
        logger.info(f"🎵 [KidsTools] play_musical_instrument: inst='{instrument_name}', note='{note}'")
        self._ensure_game_state()

        inst_list = MUSICAL_DATASET.get("instruments", [])
        rainbow_keys = MUSICAL_DATASET.get("rainbow_keyboard", [])

        clean_name = instrument_name.lower().strip()
        matched = None
        for inst in inst_list:
            if clean_name in inst.get("name", "").lower() or clean_name in inst.get("hindi_name", "").lower() or clean_name in inst.get("id", "").lower():
                matched = inst
                break

        if not matched:
            matched = inst_list[0] if inst_list else {
                "id": "inst_piano", "name": "Piano", "hindi_name": "पियानो", "family": "Keys",
                "image_url": "https://images.unsplash.com/photo-1520523839898-507127053c17?w=700&q=80",
                "sound_desc": "Ting ting ting!", "fun_fact": "Piano me 88 keys hoti hain.",
                "speech": "Ye dekhiye Piano! Aao mere sath Sa Re Ga Ma bajao!"
            }

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Music: {matched.get('name')}")
        gam_meta = self._add_star_and_check_level(1)

        keys_to_show = matched.get("interactive_keys") or rainbow_keys

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "musical_instrument",
            "sheet_id": f"inst_{matched.get('id')}",
            "title": f"🎵 {matched.get('name')} ({matched.get('hindi_name')})",
            "subtitle": f"Family: {matched.get('family', 'Music')} • Interactive Sound Pad",
            "badge": "MUSICAL INSTRUMENT 🎹",
            "bgm_track": "playful_tinkle",
            "auto_dismiss_seconds": 60,
            "media": {
                "image_url": matched.get("image_url"),
                "caption": matched.get("sound_desc"),
                "aspect_ratio": 1.5
            },
            "musical_instrument": {
                "id": matched.get("id"),
                "name": matched.get("name"),
                "hindi_name": matched.get("hindi_name"),
                "family": matched.get("family"),
                "sound_desc": matched.get("sound_desc"),
                "fun_fact": matched.get("fun_fact"),
                "keys": keys_to_show,
                "active_note": note
            },
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "sfx": "celebration_fanfare"
            },
            "actions": [
                {"id": "inst_piano", "label": "Piano 🎹", "action": "inst_piano"},
                {"id": "inst_tabla", "label": "Tabla 🥁", "action": "inst_tabla"},
                {"id": "inst_flute", "label": "Bansuri 🪈", "action": "inst_flute"},
                {"id": "inst_xylophone", "label": "Xylophone 🎶", "action": "inst_xylophone"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return matched.get("speech", f"Ye hai {matched.get('name')}! Screen par colorful keys par tap karke sur bajao!")

    @llm.ai_callable(description="Teach Hindi reading step-by-step with interactive letter blocks: 2-akshar (नल, जल, घर, फल), 3-akshar (कमल, मटर, सड़क), 4-akshar (अजगर, बरगद, कसरत) with phonics audio.")
    async def teach_hindi_reading(
        self,
        word: Annotated[str, "Hindi word to teach, e.g. 'कमल', 'नल', 'जल', 'घर', 'फल', 'मटर', 'सड़क', 'बरगद', or 'next'"] = "कमल",
        tier: Annotated[str, "Tier: 'nursery' (2-letter), 'primary' (3-letter), 'advanced' (4-letter), or 'all'"] = "all",
    ) -> str:
        logger.info(f"📖 [KidsTools] teach_hindi_reading: word='{word}', tier='{tier}'")
        self._ensure_game_state()

        clean_word = word.strip()
        matched = None

        if clean_word and clean_word != "next":
            for item in HINDI_READING_WORDS:
                if clean_word in item.get("word", "") or clean_word.lower() in item.get("english", "").lower() or clean_word.lower() in item.get("id", "").lower():
                    matched = item
                    break

        if not matched:
            pool = [w for w in HINDI_READING_WORDS if tier in ["all", "", "any"] or w.get("curriculum_tier") == tier]
            if not pool:
                pool = HINDI_READING_WORDS
            matched = random.choice(pool)

        gam = self.session_data["kids_gamification"]
        if matched.get("word") not in gam["words_learned"]:
            gam["words_learned"].append(matched.get("word"))
        gam["topics_explored"].append(f"Hindi Reading: {matched.get('word')}")
        gam_meta = self._add_star_and_check_level(2)

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "hindi_reading",
            "sheet_id": f"hread_{matched.get('id')}",
            "title": f"📖 Hindi Padhna: {matched.get('word')} ({matched.get('english')})",
            "subtitle": f"{matched.get('letter_count')}-Akshar Shabd • {matched.get('curriculum_tier', 'Primary').capitalize()}",
            "badge": "HINDI PHONICS 🔤",
            "bgm_track": "playful_tinkle",
            "auto_dismiss_seconds": 60,
            "media": {
                "image_url": matched.get("image_url"),
                "caption": matched.get("meaning"),
                "aspect_ratio": 1.5
            },
            "hindi_reading": {
                "id": matched.get("id"),
                "word": matched.get("word"),
                "english": matched.get("english"),
                "meaning": matched.get("meaning"),
                "letters": matched.get("letters", []),
                "letter_count": matched.get("letter_count", 2),
                "sentence": matched.get("sentence", ""),
                "phonics_speech": matched.get("phonics_speech", "")
            },
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "sfx": "celebration_fanfare"
            },
            "actions": [
                {"id": "hread_next", "label": "Agla Shabd ➡️", "action": "hread_next"},
                {"id": "hread_repeat", "label": "Phir Se Bolo 🔁", "action": "hread_repeat"},
                {"id": "hread_sentence", "label": "Vakya 📝", "action": "hread_sentence"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return matched.get("phonics_speech", f"Aao padhte hain: {matched.get('word')}! {' + '.join(matched.get('letters', []))} = {matched.get('word')}!")

    @llm.ai_callable(description="Teach English Phonics with CVC words (CAT, BAT, HEN, PIN, SUN, DOG, CUP) and phonetic sounds (/k/ /æ/ /t/ = CAT).")
    async def teach_english_phonics(
        self,
        word: Annotated[str, "CVC word, e.g. 'CAT', 'BAT', 'HEN', 'PIN', 'SUN', 'DOG', 'CUP' or 'next'"] = "CAT",
        vowel_group: Annotated[str, "Vowel group: 'short_a', 'short_e', 'short_i', 'short_o', 'short_u', or 'any'"] = "any",
    ) -> str:
        logger.info(f"🔤 [KidsTools] teach_english_phonics: word='{word}', vowel='{vowel_group}'")
        self._ensure_game_state()

        clean_word = word.strip().upper()
        matched = None

        if clean_word and clean_word != "NEXT":
            for item in ENGLISH_READING_WORDS:
                if clean_word in item.get("word", "") or clean_word in item.get("id", "").upper():
                    matched = item
                    break

        if not matched:
            pool = [w for w in ENGLISH_READING_WORDS if vowel_group in ["any", "", "all"] or w.get("vowel_group") == vowel_group]
            if not pool:
                pool = ENGLISH_READING_WORDS
            matched = random.choice(pool)

        gam = self.session_data["kids_gamification"]
        if matched.get("word") not in gam["words_learned"]:
            gam["words_learned"].append(matched.get("word"))
        gam["topics_explored"].append(f"English Phonics: {matched.get('word')}")
        gam_meta = self._add_star_and_check_level(2)

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "english_phonics",
            "sheet_id": f"eread_{matched.get('id')}",
            "title": f"🔤 English Phonics: {matched.get('word')} ({matched.get('hindi_word')})",
            "subtitle": f"CVC Word • Sound Group: {matched.get('vowel_group', 'short_a').replace('_', ' ').capitalize()}",
            "badge": "ENGLISH PHONICS 🅰️",
            "bgm_track": "playful_tinkle",
            "auto_dismiss_seconds": 60,
            "media": {
                "image_url": matched.get("image_url"),
                "caption": matched.get("sentence"),
                "aspect_ratio": 1.5
            },
            "english_phonics": {
                "id": matched.get("id"),
                "word": matched.get("word"),
                "hindi_word": matched.get("hindi_word"),
                "letters": matched.get("letters", []),
                "letter_sounds": matched.get("letter_sounds", []),
                "sentence": matched.get("sentence", ""),
                "phonics_speech": matched.get("phonics_speech", "")
            },
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "sfx": "celebration_fanfare"
            },
            "actions": [
                {"id": "eread_next", "label": "Next Word ➡️", "action": "eread_next"},
                {"id": "eread_repeat", "label": "Sound Again 🔁", "action": "eread_repeat"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return matched.get("phonics_speech", f"Let's read: {matched.get('word')}! {' - '.join(matched.get('letters', []))} = {matched.get('word')}!")

    @llm.ai_callable(
        description="Teach syllable counting, clapping, and phonics for Class 2 syllabus words (e.g. 'dog' -> 1 clap, 'rabbit' -> 2 claps, 'elephant' -> 3 claps) with celebration."
    )
    async def teach_syllables_and_phonics(
        self,
        word: Annotated[str, "Word to teach syllable clapping for, e.g. 'dog', 'cat', 'rat', 'mat', 'fish', 'rabbit', 'monkey', 'elephant'"] = "dog"
    ) -> str:
        """Teaches syllable segmentation, counting, and clapping for children up to Class 2."""
        logger.info(f"👏 [KidsTools] teach_syllables_and_phonics: word='{word}'")
        self._ensure_game_state()

        clean_word = word.strip().upper()
        matched = None
        for item in PRIMARY_CLASS2_VOCABULARY:
            if item.get("word") == clean_word or item.get("id") == f"cvc_{clean_word.lower()}":
                matched = item
                break

        if not matched:
            matched = random.choice(PRIMARY_CLASS2_VOCABULARY)

        gam = self.session_data["kids_gamification"]
        if matched.get("word") not in gam["words_learned"]:
            gam["words_learned"].append(matched.get("word"))
        gam_meta = self._add_star_and_check_level(2)

        syl_count = matched.get("syllable_count", 1)
        claps_str = " 👏" * syl_count
        syllables_display = " - ".join(matched.get("syllables", [matched.get("word")]))

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "english_phonics",
            "sheet_id": f"syl_{matched.get('id')}",
            "title": f"👏 Syllables: {matched.get('word')} ({syl_count} Clap{'s' if syl_count > 1 else ''}{claps_str})",
            "subtitle": f"{syllables_display} • {matched.get('hindi_translit')} ({matched.get('hindi_word')})",
            "badge": f"CLASS 2 SYLLABLES ({syl_count} CLAP{'S' if syl_count > 1 else ''})",
            "bgm_track": "playful_tinkle",
            "auto_dismiss_seconds": 60,
            "media": {
                "image_url": matched.get("image_url"),
                "caption": matched.get("sample_sentence"),
                "aspect_ratio": 1.5
            },
            "english_phonics": {
                "id": matched.get("id"),
                "word": matched.get("word"),
                "hindi_word": f"{matched.get('hindi_translit')} ({matched.get('hindi_word')})",
                "syllables": matched.get("syllables", []),
                "syllable_count": syl_count,
                "letters": matched.get("spelling_letters", list(matched.get("word"))),
                "sentence": matched.get("sample_sentence", ""),
                "phonics_speech": matched.get("syllable_speech", "")
            },
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "sfx": "celebration_fanfare"
            }
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return matched.get("syllable_speech", f"{matched.get('word')} mein {syl_count} syllable hota hai! Taali bajao: {matched.get('word')}!{claps_str}")

    @llm.ai_callable(
        description="Launch the interactive photo capture camera sheet to take or save a photo of child's family member (mummy, papa, brother, sister, etc.)."
    )
    async def capture_family_photo(
        self,
        relation: Annotated[str, "Family relation: 'mummy', 'papa', 'bhai', 'behan', 'dadi', 'dada', 'friend'"] = "mummy",
        name: Annotated[str, "Name of person if mentioned, e.g. 'Pooja', 'Rahul'"] = "",
    ) -> str:
        logger.info(f"📸 [KidsTools] capture_family_photo: relation='{relation}', name='{name}'")
        self._ensure_game_state()

        rel_clean = relation.lower().strip()
        disp_name = name if name else rel_clean.capitalize()

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "capture_photo",
            "sheet_id": f"family_{rel_clean}",
            "title": f"📸 {disp_name} Ki Photo Khinchein",
            "subtitle": f"Namaste {disp_name}! Aaiye ek pyari photo click karte hain!",
            "badge": "FAMILY MEMORY ❤️",
            "auto_dismiss_seconds": 90,
            "family_member": {
                "relation": rel_clean,
                "name": disp_name,
                "prompt": f"Apne {disp_name} ko camera ke samne layein aur 'Click Photo' dabayein!"
            },
            "actions": [
                {"id": f"photo_captured_{rel_clean}", "label": "Photo Click Karein 📸", "action": f"photo_captured_{rel_clean}"},
                {"id": "photo_cancel", "label": "Baad Me ❌", "action": "photo_cancel"}
            ]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return (
            f"Arrey waah! {disp_name} se milwao! "
            f"Camera ke samne aaiye aur ek pyari si smile kijiye! "
            f"Main aapki sundar photo save kar rahi hoon!"
        )

    @llm.ai_callable(
        description="Display a saved or family member photo card on the child's screen (e.g. Mummy, Papa, Brother, Sister)."
    )
    async def show_family_photo(
        self,
        relation: Annotated[str, "Family relation: 'mummy', 'papa', 'bhai', 'behan', 'friend'"] = "mummy",
        name: Annotated[str, "Name of person"] = "",
    ) -> str:
        logger.info(f"🖼️ [KidsTools] show_family_photo: relation='{relation}', name='{name}'")
        self._ensure_game_state()

        rel_clean = relation.lower().strip()
        disp_name = name if name else rel_clean.capitalize()

        # Demo photo fallback or retrieved
        photo_url = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=700&q=80" if rel_clean == "mummy" else "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=700&q=80"

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "family_photo",
            "sheet_id": f"show_fam_{rel_clean}",
            "title": f"❤️ Meri Pyari {disp_name}",
            "subtitle": f"Family Memory • {disp_name}",
            "badge": "FAMILY LOVE ❤️",
            "auto_dismiss_seconds": 60,
            "media": {
                "image_url": photo_url,
                "caption": f"Hamari pyari {disp_name}!",
                "aspect_ratio": 1.2
            },
            "family_member": {
                "relation": rel_clean,
                "name": disp_name,
                "image_url": photo_url
            },
            "actions": [
                {"id": "love_family", "label": "I Love You ❤️", "action": "love_family"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return f"Dekhiye screen par aapki pyari {disp_name} ki sundar photo! {disp_name} kitni achhi lag rahi hain!"

    @llm.ai_callable(
        description="Play an educational cartoon or rhyme video on the child's screen (e.g. Lakdi Ki Kathi, Chanda Mama, Twinkle Star, Jungle Safari Animals, Birds) with video player and playback controls."
    )
    async def play_educational_video(
        self,
        topic_or_title: Annotated[str, "Video title or topic (e.g. 'lakdi ki kathi', 'chanda mama', 'twinkle star', 'animals', 'solar system')"] = "lakdi ki kathi",
        category: Annotated[str, "Category filter: 'rhymes', 'animals'"] = "rhymes"
    ) -> str:
        """Plays an animated video clip with audio, captions, and playback controls in the interactive bottom sheet."""
        self._ensure_game_state()
        topic_clean = topic_or_title.strip().lower()
        cat_clean = category.strip().lower()

        matched_video = None
        cand_list = KIDS_VIDEOS.get(cat_clean, [])
        for vid in cand_list:
            if topic_clean in vid.get("title", "").lower() or topic_clean in vid.get("id", "").lower() or topic_clean in vid.get("description", "").lower():
                matched_video = vid
                break

        if not matched_video:
            for c_name, v_list in KIDS_VIDEOS.items():
                for vid in v_list:
                    if topic_clean in vid.get("title", "").lower() or topic_clean in vid.get("id", "").lower() or topic_clean in vid.get("description", "").lower():
                        matched_video = vid
                        cat_clean = c_name
                        break
                if matched_video:
                    break

        if not matched_video:
            rhymes_list = KIDS_VIDEOS.get("rhymes", [])
            matched_video = rhymes_list[0] if rhymes_list else {
                "id": "vid_lakdi_kathi",
                "title": "Lakdi Ki Kathi",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "poster_url": "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=800&auto=format&fit=crop&q=80",
                "duration": "1:20",
                "description": "Lakdi ki kathi animated video!"
            }

        gam = self.session_data["kids_gamification"]
        gam["topics_explored"].append(f"Video: {matched_video.get('title')}")
        gam_meta = self._add_star_and_check_level(2)

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "sheet_id": f"video_{matched_video.get('id', 'player')}",
            "component": "video_player",
            "title": f"🎬 {matched_video.get('title', 'Kids Video')}",
            "subtitle": f"{matched_video.get('description', '')} ({matched_video.get('duration', '1:30')})",
            "badge": "VIDEO LEARNING 🎬",
            "auto_dismiss_seconds": 180,
            "gamification": {
                "stars": gam_meta["stars"],
                "level": gam_meta["level"],
                "level_title": gam_meta["level_title"],
                "curriculum_tier": gam_meta["curriculum_tier"],
                "sfx": "celebration_fanfare"
            },
            "video": {
                "title": matched_video.get("title", "Kids Video"),
                "video_url": matched_video.get("video_url"),
                "poster_url": matched_video.get("poster_url"),
                "duration": matched_video.get("duration", "1:30"),
                "category": cat_clean,
                "moral": matched_video.get("moral", "Roz naya seekhein aur khush rahein!")
            },
            "actions": [
                {"id": "play_pause", "label": "⏯️ Play/Pause", "action": "toggle_video"},
                {"id": "next_video", "label": "⏭️ Agla Video", "action": "next_video"},
                {"id": "show_topics", "label": "🎒 Topics", "action": "show_topics"}
            ]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)
        elif hasattr(self, "_emit_sheet_payload"):
            await self._emit_sheet_payload(sheet_payload)

        return f"Arrey waah! Screen par dekhiye, '{matched_video.get('title')}' ka animated video shuru ho gaya hai! Chalo milkar enjoy karte hain!"

    @llm.ai_callable(description="Switches the active on-screen AI character when the child asks to talk to Puruva, Kairi, or Tray (e.g. 'Mujhe Puruva se baat karni hai', 'Kairi ko bulao', 'Tray bhaiya se baat karni hai').")
    async def switch_active_character(
        self,
        character_name: Annotated[str, "The name of the character to summon: 'puruva' (Puruva AI - Sweet Teacher & Mentor), 'kairi' (Masti Champ / Gamer), 'tray' (Science Explorer)"] = "puruva"
    ) -> str:
        """Dynamically switches active character, emits character_info packet to Flutter, and returns personalized switch greeting."""
        from personas.kids_characters import get_character, get_switch_greeting
        self._ensure_game_state()

        cname_clean = character_name.strip().lower()
        if "kairi" in cname_clean:
            char_id = "kairi"
        elif "tray" in cname_clean:
            char_id = "tray"
        else:
            char_id = "puruva"

        new_char = get_character(char_id)
        if hasattr(self, "session") and self.session:
            self.session.active_character = new_char

        # Broadcast character update to Flutter LiveKit room
        if hasattr(self, "room") and self.room and self.room.local_participant:
            char_pkt = {
                "type": "character_info",
                "character_id": new_char["id"],
                "name": new_char["name"],
                "display_name": new_char["display_name"],
                "title": new_char["title"],
                "avatar_url": new_char["avatar_url"],
                "avatar_asset": new_char.get("avatar_asset", ""),
                "avatar_data_path": new_char.get("avatar_data_path", ""),
                "character_type": new_char.get("character_type", ""),
                "theme_color": new_char["theme_color"],
                "pitch": new_char["pitch"],
                "rate": new_char["rate"],
                "role_badge": new_char["role_badge"],
            }
            try:
                await self.room.local_participant.publish_data(
                    json.dumps(char_pkt).encode("utf-8"),
                    reliable=True
                )
            except Exception as e:
                logger.warning(f"Error publishing character switch packet: {e}")

        caller_name = ""
        if hasattr(self, "caller_name") and self.caller_name:
            caller_name = self.caller_name
        elif hasattr(self, "session_data") and "user_name" in self.session_data:
            caller_name = self.session_data.get("user_name", "")

        return get_switch_greeting(char_id, caller_name)

    @llm.ai_callable(description="Reward the child with stars and trigger glowing star jar fly animation with colorful confetti on the phone screen.")
    async def award_stars_and_celebrate(
        self,
        star_count: Annotated[int, "Number of stars to award, usually 1 to 3"] = 1,
        reason: Annotated[str, "Reason for reward, e.g. 'sahi jawab', 'good habit', 'story completed'"] = "sahi jawab"
    ) -> str:
        """Explicit tool to reward stars and trigger live celebrations on child's screen."""
        self.record_tool_invocation("award_stars_and_celebrate", {"star_count": star_count, "reason": reason})
        self._ensure_game_state()
        count = max(1, min(5, star_count))
        res = self._add_star_and_check_level(bonus=count, reason=reason)
        return (
            f"Hooray! Congratulations champ! Aapko milte hain {count} chamakte hue Stars ⭐! "
            f"Aapke paas ab total {res['stars']} stars hain! Level: {res['level_title']}!"
        )

    @llm.ai_callable(description="Set the character's emotional face reaction on screen: 'curious' (head tilt when asking question), 'happy' (rosy blush & smile), 'celebrating' (joyous bounce), or 'neutral'.")
    async def set_character_emotion(
        self,
        emotion: Annotated[str, "'curious', 'happy', 'celebrating', 'neutral'"] = "happy"
    ) -> str:
        """Sets character's emotional reaction and broadcasts to Flutter avatar."""
        self.record_tool_invocation("set_character_emotion", {"emotion": emotion})
        clean = (emotion or "happy").lower().strip()
        if hasattr(self, "room") and self.room and self.room.local_participant:
            try:
                pkt = {
                    "type": "character_emotion",
                    "emotion": clean
                }
                await self.room.local_participant.publish_data(
                    json.dumps(pkt).encode("utf-8"),
                    reliable=True
                )
            except Exception as e:
                logger.debug(f"Failed to publish character_emotion: {e}")
        return f"Character emotion set to {clean}."

    @llm.ai_callable(
        description="Open full-screen interactive finger painting and drawing canvas in Flutter bottom sheet. Allows kids to draw houses, trees, animals, or free drawing with colors and brushes."
    )
    async def open_painting_canvas(
        self,
        topic: Annotated[str, "Drawing topic: 'house', 'tree', 'sun', 'cat', 'car', 'flower', 'free_draw'"] = "house",
        outline_guide: Annotated[str, "Whether to show faint background dotted guide: 'house', 'tree', 'cat', 'none'"] = "house"
    ) -> str:
        """Opens the interactive painting canvas on the child's screen."""
        self.record_tool_invocation("open_painting_canvas", {"topic": topic, "outline_guide": outline_guide})
        self._ensure_game_state()
        clean_topic = (topic or "house").strip().lower()

        topic_titles = {
            "house": ("Ghar (House)", "Chalo ek pyara sa ghar draw karein! Chhat aur darwaza banana mat bhulna!"),
            "tree": ("Ped (Tree)", "Chalo ek hara-bhara ped banate hain!"),
            "sun": ("Sooraj (Sun)", "Chalo chamakta hua peela sooraj draw karein!"),
            "cat": ("Billi (Cat)", "Cute si billi draw karein, do kaan aur lambi poochh!"),
            "flower": ("Phool (Flower)", "Sundar rangeen phool draw karein!"),
            "free_draw": ("Free Painting", "Apni pasand ki koi bhi drawing banaiye!"),
        }
        title_str, hint_str = topic_titles.get(clean_topic, (clean_topic.capitalize(), f"Chalo {clean_topic} draw karein!"))

        sheet_payload = {
            "component": "painting_canvas",
            "title": f"🎨 {title_str}",
            "subtitle": hint_str,
            "topic": clean_topic,
            "outline_guide": outline_guide or clean_topic,
            "colors": [
                "#EF4444", "#3B82F6", "#10B981", "#F59E0B",
                "#8B5CF6", "#EC4899", "#111827", "#FFFFFF"
            ],
            "default_color": "#3B82F6",
            "stroke_width": 4.0,
            "auto_dismiss_seconds": 0, # Persistent canvas
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return f"Painting canvas open ho gaya hai! Chalo screen par {title_str} draw karke dikhao!"

    @llm.ai_callable(
        description="Analyze and praise the child's completed drawing on the painting canvas. Gives warm praise on colors, shapes, and awards celebration stars."
    )
    async def analyze_child_drawing(
        self,
        topic: Annotated[str, "Topic drawn, e.g. 'house', 'tree', 'cat'"] = "house",
        quality_feedback: Annotated[str, "Encouraging comment e.g. 'bahut sundar', 'shandar colors'"] = "bahut sundar"
    ) -> str:
        """Analyzes drawing and triggers star celebrations."""
        self.record_tool_invocation("analyze_child_drawing", {"topic": topic, "quality_feedback": quality_feedback})
        self._ensure_game_state()
        res = self._add_star_and_check_level(bonus=2, reason=f"drawing_{topic}")

        praise_templates = {
            "house": "Arey waah champ! Kitna pyara ghar draw kiya hai! Chhat aur darwaza bilkul perfect hai! Ye mile aapko 2 Golden Stars ⭐⭐!",
            "tree": "Superstar! Ped ke patte aur daaliyan kitni sundar lag rahi hain! 2 Golden Stars aapke hue ⭐⭐!",
            "sun": "Wah! Itna chamakta aur pyara sooraj banaya hai aapne! Kamra roshan ho gaya! ⭐⭐",
            "cat": "Meow meow! Billi ke kaan aur poochh kitni cute banayi hai! Kamaal kar diya! ⭐⭐",
        }
        speech = praise_templates.get(topic.lower(), f"Arey waah! {topic.capitalize()} kitna shandar draw kiya hai aapne! Ye mile aapko 2 Golden Stars ⭐⭐!")
        return f"{speech} Aapke total stars: {res['stars']}!"

    @llm.ai_callable(
        description="Start an interactive visual image quiz 'Pehchano Kaun?' on child's screen with animal/object photo, spoken question, and interactive option chips."
    )
    async def start_visual_image_quiz(
        self,
        topic: Annotated[str, "Topic or animal, e.g. 'elephant', 'lion', 'tiger', 'dog', 'cat', 'horse', 'cow', 'monkey', 'rabbit', 'peacock', 'duck', 'apple', 'mango'"] = "elephant",
        question: Annotated[str, "Quiz question in Hinglish, e.g. 'Ye kiska photo hai?'"] = "Ye kiska photo hai?",
        options: Annotated[List[str], "List of 3 options, e.g. ['Haathi (Elephant)', 'Sher (Lion)', 'Bhalu (Bear)']"] = None,
        correct_answer: Annotated[str, "Correct option string"] = "Haathi (Elephant)"
    ) -> str:
        """Displays a visual image quiz card with interactive buttons and starts inactivity prompt timer."""
        self.record_tool_invocation("start_visual_image_quiz", {"topic": topic, "question": question})
        self._ensure_game_state()

        library = {
            "elephant": {
                "image_url": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=600",
                "question": "Ye kiska photo hai? Badi si soond aur bade bade kaan!",
                "options": ["Haathi (Elephant)", "Ghoda (Horse)", "Sher (Lion)"],
                "correct": "Haathi (Elephant)",
                "clue": "Iski lambi si soond hoti hai aur ye sabse bada janwar hai!",
                "fact": "Haathi apni soond se 8 se 9 liter paani ek baar me pee sakta hai!"
            },
            "lion": {
                "image_url": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=600",
                "question": "Ye kiska photo hai? Jungle ka raja jo tez dahaad maarta hai!",
                "options": ["Sher (Lion)", "Billi (Cat)", "Kutta (Dog)"],
                "correct": "Sher (Lion)",
                "clue": "Ye jungle ka raja hai aur iski gardan par lambe baal hote hain!",
                "fact": "Sher ki dahaad 8 kilometer door tak sunai deti hai!"
            },
            "tiger": {
                "image_url": "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?w=600",
                "question": "Ye kaun sa janwar hai? Peeli aur kaali dhaariyon wala hamara rashtriya pashu!",
                "options": ["Baagh (Tiger)", "Cheetah", "Billi (Cat)"],
                "correct": "Baagh (Tiger)",
                "clue": "Iske shareer par kaali stripes hoti hain aur ye bohot tej daudta hai!",
                "fact": "Baagh hamara National Animal hai aur paani me tairna bohot pasand karta hai!"
            },
            "dog": {
                "image_url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600",
                "question": "Ye kaun sa wafadaar janwar hai? Wuff-wuff karta hai aur pooch hilata hai!",
                "options": ["Kutta (Dog)", "Billi (Cat)", "Khargosh (Rabbit)"],
                "correct": "Kutta (Dog)",
                "clue": "Ye hamare ghar ki rakhwali karta hai aur wuff-wuff bhaunkta hai!",
                "fact": "Dogs ki sunne aur soonghne ki shakti insano se 40 guna zyada hoti hai!"
            },
            "cat": {
                "image_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600",
                "question": "Ye kaun sa pyara janwar hai? Meow-meow karti hai aur doodh peeti hai!",
                "options": ["Billi (Cat)", "Kutta (Dog)", "Ch चूहा (Mouse)"],
                "correct": "Billi (Cat)",
                "clue": "Ye chuhe pakadti hai aur meow meow karti hai!",
                "fact": "Billiyan andhere me bhi bilkul saaf dekh sakti hain!"
            },
            "horse": {
                "image_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600",
                "question": "Ye kaun sa janwar hai? Tabdak-tabdak daudta hai aur hinhinata hai!",
                "options": ["Ghoda (Horse)", "Oonth (Camel)", "Haathi (Elephant)"],
                "correct": "Ghoda (Horse)",
                "clue": "Is par baithkar sawari karte hain aur ye khade hokar bhi so sakta hai!",
                "fact": "Ghoda khade-khade so sakta hai aur bohot tez daudta hai!"
            },
            "cow": {
                "image_url": "https://images.unsplash.com/photo-1546445317-29f4545e9d53?w=600",
                "question": "Ye kaun sa janwar hai? Humein meetha doodh deti hai aur Moo-moo karti hai!",
                "options": ["Gaaye (Cow)", "Bakri (Goat)", "Bhains (Buffalo)"],
                "correct": "Gaaye (Cow)",
                "clue": "Gaumata humein swasth doodh deti hai aur ghaas khati hai!",
                "fact": "Gaaye din bhar me lagbhag 40 kilogram ghaas aur chaara kha sakti hai!"
            },
            "monkey": {
                "image_url": "https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?w=600",
                "question": "Ye kaun sa natkhat janwar hai? Pedon par koodta hai aur kela khana pasand karta hai!",
                "options": ["Bandar (Monkey)", "Bhalu (Bear)", "Khargosh (Rabbit)"],
                "correct": "Bandar (Monkey)",
                "clue": "Ye ek ped se doosre ped par chhalang lagata hai aur kela chheel kar khata hai!",
                "fact": "Bandar insano ki tarah kela chheel kar hi khate hain!"
            },
            "rabbit": {
                "image_url": "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?w=600",
                "question": "Ye kaun sa pyara janwar hai? Safed naram gulgula jo laal gajar khata hai!",
                "options": ["Khargosh (Rabbit)", "Billi (Cat)", "Chuha (Rat)"],
                "correct": "Khargosh (Rabbit)",
                "clue": "Iske lambe lambe kaan hote hain aur ye phudak-phudak kar chalta hai!",
                "fact": "Khargosh jab khush hota hai to hawa me koodta hai, jise 'Binky' bolte hain!"
            },
            "peacock": {
                "image_url": "https://images.unsplash.com/photo-1536514498073-50e69d39c6cf?w=600",
                "question": "Ye kaun sa sundar pakshi hai? Baarish mein rang-birange pankh failakar naachta hai!",
                "options": ["Mor (Peacock)", "Totta (Parrot)", "Kabootar (Pigeon)"],
                "correct": "Mor (Peacock)",
                "clue": "Hamara National Bird jiske pankh par sundar chaand jaise nishaan hote hain!",
                "fact": "Mor ke pankh dhoop aur roshni me rang badalte huye dikhayi dete hain!"
            },
            "duck": {
                "image_url": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=600",
                "question": "Ye kaun sa pakshi hai? Paani mein tairta hai aur Quack-quack karta hai!",
                "options": ["Battakh (Duck)", "Hans (Swan)", "Murga (Rooster)"],
                "correct": "Battakh (Duck)",
                "clue": "Iske panje jhillidar hote hain jo paani me tairne me madad karte hain!",
                "fact": "Battakh ke pankh waterproof hote hain, paani me bhi geele nahi hote!"
            },
            "apple": {
                "image_url": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600",
                "question": "Ye kaun sa phal hai? Laal rang ka meetha aur swasthavardhak!",
                "options": ["Seb (Apple)", "Kela (Banana)", "Aam (Mango)"],
                "correct": "Seb (Apple)",
                "clue": "An apple a day keeps the doctor away! Laal rang ka hota hai!",
                "fact": "Seb paani me tair sakta hai kyunki usme 25 percent hawa hoti hai!"
            },
            "mango": {
                "image_url": "https://images.unsplash.com/photo-1553279768-865429fa0078?w=600",
                "question": "Ye kaun sa phal hai? Phalon ka raja, peela aur meetha rasbhara!",
                "options": ["Aam (Mango)", "Santra (Orange)", "Seb (Apple)"],
                "correct": "Aam (Mango)",
                "clue": "Garmiyo me milne wala sabka favorite phalon ka raja!",
                "fact": "Aam Bharat ka Rashtriya Phal (National Fruit) hai!"
            },
        }

        clean_topic = (topic or "elephant").lower().strip()
        data = library.get(clean_topic, library["elephant"])

        final_question = question if question != "Ye kiska photo hai?" else data["question"]
        final_options = options if options else data["options"]
        final_correct = correct_answer if correct_answer != "Haathi (Elephant)" else data["correct"]
        final_img = data["image_url"]
        clue = data.get("clue", "Isko dhyan se dekho!")
        fact = data.get("fact", "Ye bohot hi anokha aur pyara hai!")

        # Save active quiz state
        self.session_data["active_visual_quiz"] = {
            "topic": clean_topic,
            "question": final_question,
            "options": final_options,
            "correct_answer": final_correct,
            "clue": clue,
            "fact": fact,
            "answered": False,
            "created_at": time.time(),
        }

        sheet_payload = {
            "component": "visual_image_quiz",
            "title": "🔍 Pehchano Kaun?",
            "question": final_question,
            "image_url": final_img,
            "options": final_options,
            "correct_answer": final_correct,
            "topic": clean_topic,
            "auto_dismiss_seconds": 0,
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        # Cancel any previous watchdog and launch a new child-inactivity watchdog
        self._start_quiz_inactivity_watchdog(final_options, final_correct, clue)

        return (
            f"Screen par tasveer khul gayi hai! Turant bache se bolo:\n"
            f"'Pehchano kaun? Is tasveer mein kaun sa janwar hai? {final_question} Bolke batao ya screen par touch karo!'"
        )

    def cancel_quiz_timer(self):
        """Cancels the inactivity hint timer when the child speaks or clicks."""
        task = getattr(self, "_quiz_inactivity_task", None)
        if task and not task.done():
            task.cancel()
            setattr(self, "_quiz_inactivity_task", None)

    def _start_quiz_inactivity_watchdog(self, options: List[str], correct_answer: str, clue: str):
        """Monitors child interaction. If child delays 5-6s, reads options aloud for younger kids."""
        self.cancel_quiz_timer()

        async def _watchdog():
            try:
                # First wait: 6 seconds of thinking time
                await asyncio.sleep(6.0)
                quiz = self.session_data.get("active_visual_quiz")
                if not quiz or quiz.get("answered"):
                    return

                # Child took time: Read options aloud like a loving teacher
                logger.info("⏳ [VisualQuiz] Child is thinking/quiet for 6s. Reading options aloud...")
                opt_str = f"Pehla hai {options[0]}, doosra hai {options[1]}, aur teesra hai {options[2]}"
                prompt_speech = f"Arey champ! Lagta hai aap soch rahe ho! Dekho screen par options hain: {opt_str}! Kaun sa sahi lagta hai? Bolke batao ya screen pe touch karo!"

                agent = getattr(self, "agent", None)
                if agent and hasattr(agent, "say"):
                    await agent.say(prompt_speech, allow_interruptions=True)

                # Second wait: Another 7 seconds for clue
                await asyncio.sleep(7.5)
                quiz = self.session_data.get("active_visual_quiz")
                if not quiz or quiz.get("answered"):
                    return

                logger.info("⏳ [VisualQuiz] Still thinking. Providing gentle clue...")
                clue_speech = f"Ek pyara sa clue doon champ? {clue} Jaldi se jo sahi hai us par ungli se tap kardo!"
                if agent and hasattr(agent, "say"):
                    await agent.say(clue_speech, allow_interruptions=True)

            except asyncio.CancelledError:
                pass
            except Exception as ex:
                logger.warning(f"[VisualQuiz] Watchdog error: {ex}")

        task = asyncio.create_task(_watchdog())
        setattr(self, "_quiz_inactivity_task", task)

    @llm.ai_callable(
        description="Reads the current visual quiz options out loud for younger kids who cannot read yet."
    )
    async def read_quiz_options_aloud(self) -> str:
        """Reads out all options from the active visual quiz."""
        quiz = self.session_data.get("active_visual_quiz", {})
        options = quiz.get("options", [])
        if not options:
            return "Screen par jo photo hai usko dhyan se dekho champ aur batao kiska chitra hai!"
        opt_str = f"Pehla hai {options[0]}, doosra hai {options[1]}, aur teesra hai {options[2]}"
        return f"Dekho superstar, screen par 3 options hain: {opt_str}! Aapko kaun sa sahi lagta hai?"

    @llm.ai_callable(
        description="Evaluates whether the child's spoken or tapped answer for the visual quiz is correct or incorrect, awards stars, and returns cheerful voice feedback."
    )
    async def evaluate_visual_quiz_answer(
        self,
        selected_answer: Annotated[str, "The animal or option chosen by child, e.g. 'Haathi', 'Elephant', 'Sher', 'Dog'"]
    ) -> str:
        """Validates quiz answer, awards 10 stars on success, or gives a gentle clue on mistake."""
        self._ensure_game_state()
        self.cancel_quiz_timer()

        quiz = self.session_data.get("active_visual_quiz", {})
        correct_full = quiz.get("correct_answer", "Haathi (Elephant)")
        clue = quiz.get("clue", "Isko dhyan se dekho!")
        fact = quiz.get("fact", "Ye bohot pyara aur anokha janwar hai!")

        user_ans = (selected_answer or "").strip().lower()
        corr_low = correct_full.lower()

        # Fuzzy matching tokens for both English and Hindi
        # e.g. "haathi (elephant)" -> tokens: ["haathi", "hathi", "elephant"]
        tokens = [t.strip("(),.!?") for t in corr_low.replace("(", " ").replace(")", " ").split() if len(t) > 2]
        if "haathi" in corr_low:
            tokens.extend(["hathi", "hati"])
        if "kutta" in corr_low:
            tokens.extend(["dog", "doggy", "puppy"])
        if "billi" in corr_low:
            tokens.extend(["cat", "kitty", "kitten"])
        if "sher" in corr_low:
            tokens.extend(["lion", "singh"])
        if "baagh" in corr_low:
            tokens.extend(["bagh", "tiger"])
        if "ghoda" in corr_low:
            tokens.extend(["horse", "ghode"])
        if "gaaye" in corr_low:
            tokens.extend(["gai", "cow"])
        if "bandar" in corr_low:
            tokens.extend(["monkey", "makad"])
        if "khargosh" in corr_low:
            tokens.extend(["rabbit", "bunny"])
        if "mor" in corr_low:
            tokens.extend(["peacock"])
        if "battakh" in corr_low:
            tokens.extend(["duck", "batakh"])
        if "seb" in corr_low:
            tokens.extend(["apple"])
        if "aam" in corr_low:
            tokens.extend(["mango"])

        is_correct = any(tok in user_ans for tok in tokens) or (user_ans in corr_low) or (corr_low in user_ans)

        if is_correct:
            quiz["answered"] = True
            self._add_star_and_check_level(bonus=10, reason="visual_quiz_correct")

            # Broadcast success update to Flutter bottom sheet
            if hasattr(self, "room") and self.room and self.room.local_participant:
                try:
                    update_pkt = {
                        "type": "interactive_sheet_update",
                        "component": "visual_image_quiz",
                        "status": "correct",
                        "selected_option": selected_answer,
                        "correct_answer": correct_full,
                    }
                    asyncio.create_task(self.room.local_participant.publish_data(
                        json.dumps(update_pkt).encode("utf-8"),
                        reliable=True
                    ))
                except Exception:
                    pass

            if "quiz_tracking" not in self.session_data:
                self.session_data["quiz_tracking"] = {"unanswered_streak": 0, "total_questions": 0, "current_animal_index": 0}
            qt = self.session_data["quiz_tracking"]
            qt["unanswered_streak"] = 0
            qt["total_questions"] += 1

            if qt["total_questions"] >= 10:
                qt["total_questions"] = 0
                return (
                    f"WAAAH SUPERSTAR! 🎉 Bilkul sahi - ye {correct_full} hi hai! 🌟 "
                    f"Aapko milte hain 10 Golden Stars! Humne 10 sawal poore seekh liye! "
                    f"Chalo ab topic change karte hain aur mast drawing banate hain! Banao ek pyara sa flower ya house!"
                )

            return (
                f"Yaaay! Shabash superstar! Bilkul sahi pehchana - ye {correct_full} hi hai! 🌟 "
                f"Aapko milte hain 10 Golden Stars! {fact} Chalo ab agla janwar dekhein ya drawing karein?"
            )
        else:
            # Gentle encouragement: never scold
            clean_wrong = selected_answer.split("(")[0].strip()
            return (
                f"Arey thoda aur socho champ! Ye {clean_wrong} nahi hai. "
                f"Ek clue: {clue} Ek baar aur koshish karo, screen par tap karo ya bolo!"
            )

    async def handle_bottom_sheet_closure(self, component: str = "", is_timeout: bool = False) -> str:
        """Called whenever the interactive bottom sheet closes or times out after 10s.
        Manages question streaks, auto-transitions after 5 unanswered or 10 total questions,
        and keeps the child engaged without silence!
        """
        self.cancel_quiz_timer()
        self._ensure_game_state()

        if "quiz_tracking" not in self.session_data:
            self.session_data["quiz_tracking"] = {
                "unanswered_streak": 0,
                "total_questions": 0,
                "current_animal_index": 0
            }

        qt = self.session_data["quiz_tracking"]

        if is_timeout:
            qt["unanswered_streak"] += 1
            qt["total_questions"] += 1
            logger.info(f"⏱️ [QuizTracking] Timeout detected. Streak: {qt['unanswered_streak']}/5, Total: {qt['total_questions']}/10")

            # RULE 1: If 5 questions have no response -> CHANGE TOPIC!
            if qt["unanswered_streak"] >= 5:
                qt["unanswered_streak"] = 0
                qt["total_questions"] = 0
                logger.info("🔄 [QuizTracking] 5 questions without response! Auto-switching topic to fun story/drawing.")
                if hasattr(self, "open_painting_canvas"):
                    await self.open_painting_canvas(topic="house")
                return (
                    "Arey mere pyare superstar champ! Lagta hai aap sawalo se thoda bore ho gaye ho! "
                    "Koi baat nahi, padhai band! Chalo screen par mast painting canvas khul gaya hai, ek pyara sa ghar draw karte hain!"
                )

            # RULE 2: If 10 questions done in total -> CHANGE TOPIC!
            if qt["total_questions"] >= 10:
                qt["unanswered_streak"] = 0
                qt["total_questions"] = 0
                logger.info("🌟 [QuizTracking] 10 questions completed! Auto-switching topic.")
                if hasattr(self, "open_painting_canvas"):
                    await self.open_painting_canvas(topic="tree")
                return (
                    "WAAAH SUPERSTAR! 🎉 Humne 10 sawal aur janwar seekh liye! You are a genius! "
                    "Chalo ab ek mast break lete hain aur painting canvas par ek pyara sa tree banate hain!"
                )

            # Otherwise (1-4 unanswered): Advance to next animal smoothly
            animals = ["elephant", "lion", "tiger", "dog", "cat", "horse", "cow", "monkey", "rabbit", "peacock", "duck", "apple", "mango"]
            qt["current_animal_index"] = (qt["current_animal_index"] + 1) % len(animals)
            next_animal = animals[qt["current_animal_index"]]

            # Launch next question immediately!
            await self.start_visual_image_quiz(topic=next_animal)
            return f"Koi baat nahi champ! Chalo agla pyara sa janwar dekhte hain! Screen par dekho aur pehchano kaun!"

        # If user manually dismissed or answered:
        if qt.get("total_questions", 0) >= 10:
            qt["unanswered_streak"] = 0
            qt["total_questions"] = 0
            if hasattr(self, "open_painting_canvas"):
                await self.open_painting_canvas(topic="house")
            return (
                "WAAAH CHAMP! 🎉 10 sawal aur janwar poore ho gaye! "
                "Chalo ab topic change karte hain aur mast painting banate hain! Banao ek pyara sa house!"
            )

        return "Theek hai champ! Chalo aage kya masti karein? ABCD sunao, ya ek mazedaar kahani sunein, ya koi painting banayein?"



    @llm.ai_callable(
        description="Start bilingual English-Hindi animal/object vocabulary quiz (e.g. 'Dog ko Hindi mein kya bolte hain?' -> Kutta, 'Billi ko English mein kya bolte hain?' -> Cat)."
    )
    async def start_bilingual_vocab_quiz(
        self,
        word: Annotated[str, "Source word, e.g. 'dog', 'cat', 'kutta', 'billi', 'haathi', 'elephant'"] = "dog",
        direction: Annotated[str, "'eng_to_hindi' or 'hindi_to_eng'"] = "eng_to_hindi"
    ) -> str:
        """Generates a bilingual translation quiz question with on-screen option cards."""
        self.record_tool_invocation("start_bilingual_vocab_quiz", {"word": word, "direction": direction})
        self._ensure_game_state()

        clean = word.lower().strip()

        # Dynamic search from primary_class2_vocabulary.json
        matched_item = None
        for item in PRIMARY_CLASS2_VOCABULARY:
            if item.get("word", "").lower() == clean or item.get("hindi_translit", "").lower() == clean or item.get("hindi_word", "") == clean:
                matched_item = item
                break

        if matched_item:
            eng_w = matched_item["word"].capitalize()
            hin_w = matched_item["hindi_translit"].capitalize()
            hin_dev = matched_item["hindi_word"]

            # Generate smart distractors from vocabulary
            other_hindi = [it["hindi_translit"].capitalize() for it in PRIMARY_CLASS2_VOCABULARY if it["word"].lower() != clean][:6]
            other_eng = [it["word"].capitalize() for it in PRIMARY_CLASS2_VOCABULARY if it["word"].lower() != clean][:6]

            if "hindi" in direction.lower():
                q_text = f"'{eng_w}' ko Hindi mein kya bolte hain?"
                distractors = random.sample(other_hindi, min(2, len(other_hindi)))
                opts = [hin_w] + distractors
                random.shuffle(opts)
                correct = hin_w
            else:
                q_text = f"'{hin_w} ({hin_dev})' ko English mein kya bolte hain?"
                distractors = random.sample(other_eng, min(2, len(other_eng)))
                opts = [eng_w] + distractors
                random.shuffle(opts)
                correct = eng_w
        else:
            # Fallback static dictionary
            pairs = {
                "dog": ("Kutta", ["Kutta", "Billi", "Sher"], "Kutta"),
                "kutta": ("Dog", ["Dog", "Cat", "Horse"], "Dog"),
                "cat": ("Billi", ["Billi", "Chuha", "Bandar"], "Billi"),
                "billi": ("Cat", ["Cat", "Rabbit", "Fox"], "Cat"),
                "rat": ("Chuha", ["Chuha", "Billi", "Kutta"], "Chuha"),
                "chuha": ("Rat", ["Rat", "Cat", "Dog"], "Rat"),
                "mat": ("Chatai", ["Chatai", "Basta", "Topi"], "Chatai"),
                "chatai": ("Mat", ["Mat", "Bed", "Door"], "Mat"),
                "fish": ("Machhli", ["Machhli", "Batakh", "Mendhak"], "Machhli"),
                "machhli": ("Fish", ["Fish", "Frog", "Duck"], "Fish"),
                "duck": ("Batakh", ["Batakh", "Chidiya", "Machhli"], "Batakh"),
                "batakh": ("Duck", ["Duck", "Bird", "Hen"], "Duck"),
                "milk": ("Doodh", ["Doodh", "Paani", "Kheer"], "Doodh"),
                "doodh": ("Milk", ["Milk", "Water", "Tea"], "Milk"),
                "tree": ("Ped", ["Ped", "Phool", "Patta"], "Ped"),
                "ped": ("Tree", ["Tree", "Flower", "Leaf"], "Tree"),
                "star": ("Taara", ["Taara", "Chanda", "Sooraj"], "Taara"),
                "taara": ("Star", ["Star", "Moon", "Sun"], "Star"),
            }
            pair_info = pairs.get(clean, ("Kutta", ["Kutta", "Billi", "Sher"], "Kutta"))
            if "hindi" in direction.lower():
                q_text = f"'{clean.capitalize()}' ko Hindi mein kya bolte hain?"
            else:
                q_text = f"'{clean.capitalize()}' ko English mein kya bolte hain?"
            opts = pair_info[1]
            correct = pair_info[2]

        sheet_payload = {
            "component": "visual_image_quiz",
            "title": "🗣️ English-Hindi Word Quiz",
            "question": q_text,
            "options": opts,
            "correct_answer": correct,
            "topic": clean,
            "auto_dismiss_seconds": 0,
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return f"{q_text} Options hain: {', '.join(opts)}. Batao kaun sa sahi hai?"

    @llm.ai_callable(
        description="Challenge the child to trace or write a letter or spelling on screen (e.g. 'A', 'K', 'DOG', 'CAT', 'क'). Shows tracing outline canvas."
    )
    async def show_spelling_tracing_challenge(
        self,
        target_text: Annotated[str, "Letter or word to write, e.g. 'A', 'K', 'क', 'DOG', 'CAT'"] = "A",
        hint: Annotated[str, "Hint or guide text"] = "Ungli se screen par likho!"
    ) -> str:
        """Presents a guided letter/spelling tracing challenge."""
        self.record_tool_invocation("show_spelling_tracing_challenge", {"target_text": target_text})
        self._ensure_game_state()

        clean_text = target_text.upper().strip()
        sheet_payload = {
            "component": "letter_tracing",
            "title": f"✍️ Chalo Likhna Seekhein: '{clean_text}'",
            "subtitle": hint,
            "target_text": clean_text,
            "auto_dismiss_seconds": 0,
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return f"Chalo '{clean_text}' screen par likh ke dikhao! Ungli se trace karo!"

    @llm.ai_callable(
        description="Display an illustrated story scene on child's screen with colorful picture, Hindi narration, English subtitle, and moral."
    )
    async def show_illustrated_story_scene(
        self,
        title: Annotated[str, "Story title, e.g. 'Sher aur Chuha', 'Pyasa Kauwa'"] = "Sher aur Chuha",
        scene_number: Annotated[int, "Current scene number (1 to 4)"] = 1,
        image_url: Annotated[str, "High-resolution story illustration URL"] = "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=600",
        narrative_hindi: Annotated[str, "Hindi storytelling text for this scene"] = "Ek jungle mein ek bada sher so raha tha...",
        moral: Annotated[str, "Moral of story if final scene"] = ""
    ) -> str:
        """Displays an illustrated scene of a story on the child's screen."""
        self.record_tool_invocation("show_illustrated_story_scene", {"title": title, "scene_number": scene_number})
        self._ensure_game_state()

        sheet_payload = {
            "component": "story_scene",
            "title": f"📖 {title} (Scene {scene_number})",
            "image_url": image_url,
            "text": narrative_hindi,
            "moral": moral,
            "auto_dismiss_seconds": 0,
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return f"Scene {scene_number}: {narrative_hindi}"

    @llm.ai_callable(
        description="Evaluate child's recitation or answer for current educational milestone. When the child masters a topic (e.g. ABCD complete, Varnamala, Counting, Phonics, CVC words, or Syllables), level them up to the next milestone and celebrate!"
    )
    async def evaluate_and_advance_mastery(
        self,
        milestone_tested: Annotated[str, "Skill or milestone tested: 'abcd', 'varnamala', 'counting', 'phonics', 'cvc_words', 'syllables'"] = "abcd",
        is_passed: Annotated[bool, "True if the child demonstrated fluency or correct recitation"] = True,
        child_response: Annotated[str, "What the child recited or said"] = ""
    ) -> str:
        """Dynamically evaluates child learning mastery and promotes to next level."""
        self.record_tool_invocation("evaluate_and_advance_mastery", {"milestone": milestone_tested, "passed": is_passed})
        self._ensure_game_state()

        mastery = self.session_data["child_mastery"]
        gam_meta = self._add_star_and_check_level(3 if is_passed else 1)

        milestones_order = [
            ("abcd", "🔤 Alphabet A-to-Z", "varnamala", "🇮🇳 Hindi Varnamala (क, ख, ग, घ)"),
            ("varnamala", "🇮🇳 Hindi Varnamala (क, ख, ग, घ)", "counting", "🔢 Counting (1, 2, 3, 4, 5)"),
            ("counting", "🔢 Counting (1, 2, 3, 4, 5)", "phonics", "🍎 Phonics (A for Apple, B for Bat)"),
            ("phonics", "🍎 Phonics (A for Apple, B for Bat)", "cvc_words", "🐶 CVC Words & Spellings (Dog, Cat, Rat, Fish)"),
            ("cvc_words", "🐶 CVC Words (Dog, Cat, Rat, Fish)", "syllables", "👏 Syllable Clapping & Class 2 Words (Elephant, Butterfly)"),
            ("syllables", "👏 Syllables (Elephant, Butterfly)", "master_champion", "👑 Class 2 Master Genius!")
        ]

        clean_milestone = milestone_tested.lower().strip()
        current_info = None
        for curr_m, curr_title, next_m, next_title in milestones_order:
            if curr_m in clean_milestone:
                current_info = (curr_m, curr_title, next_m, next_title)
                break

        if not current_info:
            current_info = milestones_order[0]

        curr_m, curr_title, next_m, next_title = current_info

        if is_passed:
            mastery[f"{curr_m}_mastered"] = True
            if curr_title not in mastery["completed_milestones"]:
                mastery["completed_milestones"].append(curr_title)
            mastery["current_milestone"] = f"milestone_{next_m}"
            mastery["curriculum_level"] = min(5, mastery["curriculum_level"] + 1)
            mastery["correct_streak"] += 1

            sheet_payload = {
                "type": "interactive_sheet",
                "action": "open",
                "component": "milestone_level_up",
                "title": f"🎉 LEVEL UP! {next_title}",
                "subtitle": f"Shabash! Aapne '{curr_title}' pura seekh liya! Agla level shuru!",
                "badge": f"LEVEL {mastery['curriculum_level']} UNLOCKED 🌟",
                "auto_dismiss_seconds": 6,
                "gamification": {
                    "stars": gam_meta["stars"],
                    "level": mastery["curriculum_level"],
                    "sfx": "celebration_fanfare"
                }
            }

            if hasattr(self, "emit_interactive_sheet"):
                await self.emit_interactive_sheet(sheet_payload)

            return (
                f"LEVEL UP! Champ ne '{curr_title}' pura successfully bol liya! "
                f"Ab agla level '{next_title}' padhaiye! Boliye: 'Superstar! Ab hum aage badhenge aur {next_title} seekhenge!'"
            )
        else:
            return f"Bahut achha prayas! Boliye: 'Aapne bahut achhi koshish ki champ! Chalo mere sath ek baar aur repeat karte hain!'"






