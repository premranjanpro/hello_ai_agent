"""
quiz_game_tools.py - Dedicated Age-Adaptive Categorized Quizzes & In-Call Mini Games Toolchain.

Allows callers to ask for quizzes based on age tier (Kids, Teens, Adults) or specific categories
(Bollywood, Cricket, Geography, Science, Riddles). Emits an interactive bottom sheet with a 10s timer
and 4 options (A, B, C, D), allowing dual-mode input (screen tap or voice utterance).
"""

import random
import logging
from typing import Annotated, Dict, Any, List
from livekit.agents import llm

logger = logging.getLogger("toolchain.interactive.quiz_game")

# Age-categorized question bank
QUIZ_BANK: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "kids": {
        "Animals": [
            {
                "id": "k_anim_1",
                "question": "Jungle ka Raja kis janwar ko kaha jata hai?",
                "options": [{"id": "A", "label": "Sher (Lion)"}, {"id": "B", "label": "Haathi (Elephant)"}, {"id": "C", "label": "Bandar (Monkey)"}, {"id": "D", "label": "Kutta (Dog)"}],
                "correct": "A",
                "fun_fact": "Sher ko jungle ka raja kaha jata hai kyunki wo bahut taqatwar aur nidar hota hai!"
            },
            {
                "id": "k_anim_2",
                "question": "Hamara National Bird (Rashtriya Pakshi) kaunsa hai?",
                "options": [{"id": "A", "label": "Tota (Parrot)"}, {"id": "B", "label": "Mor (Peacock)"}, {"id": "C", "label": "Kabootar (Pigeon)"}, {"id": "D", "label": "Chidiya (Sparrow)"}],
                "correct": "B",
                "fun_fact": "Mor ke pankh bahut sundar aur rang-birange hote hain!"
            },
            {
                "id": "k_anim_3",
                "question": "Kis janwar ki lambi naak (trunk) hoti hai?",
                "options": [{"id": "A", "label": "Haathi (Elephant)"}, {"id": "B", "label": "Ghoda (Horse)"}, {"id": "C", "label": "Kharghosh (Rabbit)"}, {"id": "D", "label": "Bhaloo (Bear)"}],
                "correct": "A",
                "fun_fact": "Haathi apni soond se paani peeta hai aur cheezein uthata hai!"
            }
        ],
        "Colors": [
            {
                "id": "k_col_1",
                "question": "Aasman (Sky) ka rang kaisa hota hai?",
                "options": [{"id": "A", "label": "Neela (Blue)"}, {"id": "B", "label": "Laal (Red)"}, {"id": "C", "label": "Peela (Yellow)"}, {"id": "D", "label": "Kaala (Black)"}],
                "correct": "A",
                "fun_fact": "Dhoop me aasman pyara neela dikhta hai!"
            },
            {
                "id": "k_col_2",
                "question": "Apple (Seb) aamtaur par kis rang ka hota hai?",
                "options": [{"id": "A", "label": "Laal (Red)"}, {"id": "B", "label": "Neela (Blue)"}, {"id": "C", "label": "Bainjani (Purple)"}, {"id": "D", "label": "Safed (White)"}],
                "correct": "A",
                "fun_fact": "An apple a day keeps the doctor away!"
            }
        ],
        "Math": [
            {
                "id": "k_math_1",
                "question": "2 + 3 kitna hota hai?",
                "options": [{"id": "A", "label": "4"}, {"id": "B", "label": "5"}, {"id": "C", "label": "6"}, {"id": "D", "label": "7"}],
                "correct": "B",
                "fun_fact": "2 toffee me 3 toffee milayi to ban gayi 5 toffee!"
            }
        ]
    },
    "teens": {
        "Space": [
            {
                "id": "t_space_1",
                "question": "Hamare Solar System me sabse bada planet kaunsa hai?",
                "options": [{"id": "A", "label": "Mangal (Mars)"}, {"id": "B", "label": "Brihaspati (Jupiter)"}, {"id": "C", "label": "Shani (Saturn)"}, {"id": "D", "label": "Prithvi (Earth)"}],
                "correct": "B",
                "fun_fact": "Jupiter itna bada hai ki usme 1,300 Earth sama sakti hain!"
            },
            {
                "id": "t_space_2",
                "question": "Chand par kadam rakhne wale pehle vyakti kaun the?",
                "options": [{"id": "A", "label": "Neil Armstrong"}, {"id": "B", "label": "Yuri Gagarin"}, {"id": "C", "label": "Rakesh Sharma"}, {"id": "D", "label": "Buzz Aldrin"}],
                "correct": "A",
                "fun_fact": "Neil Armstrong ne 1969 me Apollo 11 mission ke dauran pehla kadam rakha tha!"
            }
        ],
        "Cricket": [
            {
                "id": "t_cric_1",
                "question": "Cricket ke ek over me kitni legal gendein (balls) hoti hain?",
                "options": [{"id": "A", "label": "4"}, {"id": "B", "label": "5"}, {"id": "C", "label": "6"}, {"id": "D", "label": "8"}],
                "correct": "C",
                "fun_fact": "Pehle kuch deshon me 8 balls ka over hota tha, par ab international rule me 6 balls hoti hain!"
            },
            {
                "id": "t_cric_2",
                "question": "Captain Cool ke naam se kis mashhoor cricketer ko jana jata hai?",
                "options": [{"id": "A", "label": "Virat Kohli"}, {"id": "B", "label": "MS Dhoni"}, {"id": "C", "label": "Rohit Sharma"}, {"id": "D", "label": "Sachin Tendulkar"}],
                "correct": "B",
                "fun_fact": "MS Dhoni ne 2007 T20 World Cup aur 2011 ODI World Cup dono jeetaye!"
            }
        ],
        "Science": [
            {
                "id": "t_sci_1",
                "question": "Paani (Water) ka chemical formula kya hota hai?",
                "options": [{"id": "A", "label": "CO2"}, {"id": "B", "label": "H2O"}, {"id": "C", "label": "NaCl"}, {"id": "D", "label": "O2"}],
                "correct": "B",
                "fun_fact": "2 Hydrogen ke atoms aur 1 Oxygen ka atom milkar banta hai paani!"
            }
        ]
    },
    "adults": {
        "Bollywood": [
            {
                "id": "a_bolly_1",
                "question": "Film 'Sholay' me Gabbar Singh ka mashhoor dialogue kya tha?",
                "options": [{"id": "A", "label": "Kitne aadmi the?"}, {"id": "B", "label": "Mogambo khush hua"}, {"id": "C", "label": "Rishte me hum tumhare baap lagte hain"}, {"id": "D", "label": "Pushpa, I hate tears"}],
                "correct": "A",
                "fun_fact": "Gabbar Singh ka role Amjad Khan ne nibhaya tha!"
            },
            {
                "id": "a_bolly_2",
                "question": "Oscar jeetne wala gaana 'Naatu Naatu' kis film ka hai?",
                "options": [{"id": "A", "label": "Baahubali"}, {"id": "B", "label": "RRR"}, {"id": "C", "label": "KGF"}, {"id": "D", "label": "Pushpa"}],
                "correct": "B",
                "fun_fact": "RRR ne Best Original Song category me Academy Award jeetkar itihas racha tha!"
            }
        ],
        "History": [
            {
                "id": "a_hist_1",
                "question": "Bharat ka pehla Pradhan Mantri (Prime Minister) kaun tha?",
                "options": [{"id": "A", "label": "Mahatma Gandhi"}, {"id": "B", "label": "Jawaharlal Nehru"}, {"id": "C", "label": "Sardar Patel"}, {"id": "D", "label": "Dr. BR Ambedkar"}],
                "correct": "B",
                "fun_fact": "Pandit Jawaharlal Nehru 1947 se 1964 tak Bharat ke pehle PM rahe."
            },
            {
                "id": "a_hist_2",
                "question": "Taj Mahal kis Mughal Badshah ne banwaya tha?",
                "options": [{"id": "A", "label": "Akbar"}, {"id": "B", "label": "Shah Jahan"}, {"id": "C", "label": "Babur"}, {"id": "D", "label": "Humayun"}],
                "correct": "B",
                "fun_fact": "Shah Jahan ne apni begum Mumtaz Mahal ki yaad me ye azeem-o-shaan imarat banwayi thi!"
            }
        ],
        "Riddles": [
            {
                "id": "a_rid_1",
                "question": "Paheli: Aisi kaunsi cheez hai jo sookhte waqt geeli hoti chali jati hai?",
                "options": [{"id": "A", "label": "Roti"}, {"id": "B", "label": "Tauliya (Towel)"}, {"id": "C", "label": "Chhaya"}, {"id": "D", "label": "Pankha"}],
                "correct": "B",
                "fun_fact": "Tauliya doosro ko sukhate-sukhate khud geela ho jata hai!"
            },
            {
                "id": "a_rid_2",
                "question": "Paheli: Wo kya hai jiske paas gale me gardan hai par sar nahi?",
                "options": [{"id": "A", "label": "Bottal (Bottle)"}, {"id": "B", "label": "Kameez (Shirt)"}, {"id": "C", "label": "Ghada"}, {"id": "D", "label": "Ped"}],
                "correct": "B",
                "fun_fact": "Kameez ya Shirt ka collar (gardan) hota hai par uske paas sar nahi hota!"
            }
        ]
    }
}


class InteractiveQuizGameToolsMixin:
    """Age-adaptive categorized quizzes and in-call mini games toolchain."""

    def _ensure_quiz_state(self):
        if not hasattr(self, "session_data"):
            self.session_data = {}
        if "quiz_state" not in self.session_data:
            self.session_data["quiz_state"] = {
                "score": 0,
                "current_question": None,
                "answered_ids": [],
            }

    @llm.ai_callable(description="Ask the user an interactive quiz question customized to their age group (kids, teens, or adults) and category. Pops up a 10-second interactive bottom sheet with 4 options (A, B, C, D) on the caller's screen.")
    async def ask_categorized_quiz(
        self,
        age_group: Annotated[str, "Age tier: 'kids' (4-8 yrs), 'teens' (9-15 yrs), or 'adults' (16+ yrs)"] = "adults",
        category: Annotated[str, "Category: 'Animals', 'Colors', 'Math', 'Space', 'Cricket', 'Science', 'Bollywood', 'History', 'Riddles', or 'any'"] = "any",
    ) -> str:
        logger.info(f"🎯 [QuizTool] ask_categorized_quiz: age={age_group}, category={category}")
        self.record_tool_invocation("ask_categorized_quiz", {"age_group": age_group, "category": category})
        self._ensure_quiz_state()

        tier = age_group.lower().strip()
        if "kid" in tier or "bach" in tier or "child" in tier:
            tier_key = "kids"
        elif "teen" in tier or "school" in tier or "student" in tier:
            tier_key = "teens"
        else:
            tier_key = "adults"

        tier_categories = QUIZ_BANK.get(tier_key, QUIZ_BANK["adults"])

        # Pick matching or random category
        selected_cat = None
        for c in tier_categories.keys():
            if c.lower() in category.lower():
                selected_cat = c
                break
        if not selected_cat:
            selected_cat = random.choice(list(tier_categories.keys()))

        questions = tier_categories[selected_cat]
        # Filter unasked
        answered = self.session_data["quiz_state"]["answered_ids"]
        available = [q for q in questions if q["id"] not in answered]
        if not available:
            available = questions

        q = random.choice(available)
        self.session_data["quiz_state"]["current_question"] = q
        self.session_data["quiz_state"]["answered_ids"].append(q["id"])

        # Construct declarative sheet payload
        sheet_payload = {
            "action": "open",
            "sheet_id": f"quiz_{q['id']}",
            "component": "quiz",
            "title": f"Quiz: {selected_cat}",
            "subtitle": f"Target: {tier_key.capitalize()} • 10 Seconds",
            "badge": f"{selected_cat.upper()}",
            "auto_dismiss_seconds": 15,
            "countdown": {
                "total_seconds": 10,
                "current_seconds": 10
            },
            "interactive_input": {
                "type": "options_grid",
                "question": q["question"],
                "options": q["options"],
                "correct_option": q["correct"]
            },
            "speech_hint": q["question"]
        }

        # Emit to app screen
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        # Build options text for natural speech
        opts_str = ", ".join([f"Option {opt['id']}: {opt['label']}" for opt in q["options"]])
        return (
            f"Maine aapke screen par sawal bhej diya hai! "
            f"Sawal hai: '{q['question']}'. "
            f"Options hain: {opts_str}. "
            f"Aap screen par tap karke ya bol kar bata sakte hain!"
        )

    @llm.ai_callable(description="Play an interactive mini-game with the user in the bottom sheet. Supports 'Number Guessing', 'Coin Toss', 'Rapid Fire', and 'Dimaagi Paheli'.")
    async def launch_in_call_game(
        self,
        game_type: Annotated[str, "Type of game: 'number_guess', 'coin_toss', 'rapid_fire', 'riddle'"] = "number_guess",
    ) -> str:
        logger.info(f"🎮 [GameTool] launch_in_call_game: type={game_type}")
        self.record_tool_invocation("launch_in_call_game", {"game_type": game_type})

        g = game_type.lower()
        if "coin" in g or "toss" in g or "sikka" in g:
            outcome = random.choice(["Heads", "Tails"])
            sheet_payload = {
                "action": "open",
                "sheet_id": "game_coin_toss",
                "component": "game",
                "title": "🪙 Coin Toss Challenge",
                "subtitle": "Tap Heads or Tails!",
                "badge": "MINI GAME",
                "auto_dismiss_seconds": 12,
                "interactive_input": {
                    "type": "options_grid",
                    "question": "Aap kya choose karte hain? Heads ya Tails?",
                    "options": [{"id": "H", "label": "🪙 Heads"}, {"id": "T", "label": "🪙 Tails"}],
                    "correct_option": "H" if outcome == "Heads" else "T"
                }
            }
            if hasattr(self, "emit_interactive_sheet"):
                await self.emit_interactive_sheet(sheet_payload)
            return "Chalo sikka uchaalte hain! Maine screen par coin toss open kar diya hai. Aap Heads loge ya Tails?"

        elif "number" in g or "guess" in g or "ginti" in g:
            secret_num = random.randint(1, 10)
            self._ensure_quiz_state()
            self.session_data["quiz_state"]["secret_number"] = secret_num

            sheet_payload = {
                "action": "open",
                "sheet_id": "game_number_guess",
                "component": "game",
                "title": "🔢 Number Guessing Game (1 se 10)",
                "subtitle": "Guess the number in my mind!",
                "badge": "GUESS GAME",
                "auto_dismiss_seconds": 15,
                "interactive_input": {
                    "type": "options_grid",
                    "question": "Maine 1 se 10 ke beech ek number socha hai. Guess kijiye wo kaun sa hai?",
                    "options": [
                        {"id": "A", "label": f"{secret_num}"},
                        {"id": "B", "label": f"{(secret_num % 10) + 1}"},
                        {"id": "C", "label": f"{((secret_num + 2) % 10) + 1}"},
                        {"id": "D", "label": f"{((secret_num + 5) % 10) + 1}"}
                    ],
                    "correct_option": "A"
                }
            }
            # Shuffle options display
            random.shuffle(sheet_payload["interactive_input"]["options"])
            if hasattr(self, "emit_interactive_sheet"):
                await self.emit_interactive_sheet(sheet_payload)
            return "Maine 1 se 10 ke beech ek secret number socha hai! Aap screen par tap karke ya bolkar guess kijiye wo kaunsa number hai!"

        else:
            # Fallback to riddle / dimaagi paheli
            return await self.ask_categorized_quiz(age_group="adults", category="Riddles")

    @llm.ai_callable(description="Check and validate the quiz answer given by user either via voice utterance or button tap. Reveals correct answer and updates score.")
    async def validate_quiz_answer(
        self,
        user_answer: Annotated[str, "The answer given by the caller: e.g. 'Option A', 'Sher', 'Neil Armstrong', 'B'"],
    ) -> str:
        logger.info(f"✅ [QuizTool] validate_quiz_answer: answer='{user_answer}'")
        self.record_tool_invocation("validate_quiz_answer", {"answer": user_answer})
        self._ensure_quiz_state()

        curr = self.session_data["quiz_state"].get("current_question")
        if not curr:
            return "Aapne bilkul theek koshish ki! Chaliye ek naya sawal poochti hoon."

        correct_id = curr.get("correct", "")
        clean_ans = user_answer.strip().lower()

        # Check if matched by option letter or text label
        is_correct = False
        if clean_ans.startswith("option ") and correct_id.lower() in clean_ans:
            is_correct = True
        elif clean_ans == correct_id.lower():
            is_correct = True
        else:
            for opt in curr.get("options", []):
                if opt["id"].lower() == correct_id.lower():
                    if opt["label"].lower() in clean_ans or clean_ans in opt["label"].lower():
                        is_correct = True
                        break

        if is_correct:
            self.session_data["quiz_state"]["score"] = self.session_data["quiz_state"].get("score", 0) + 10
            score = self.session_data["quiz_state"]["score"]
            fun_fact = curr.get("fun_fact", "")
            return f"Waah! Sahi jawab! 🎉 Option {correct_id} bilkul sahi hai! {fun_fact} Aapka score ab {score} points ho gaya hai!"
        else:
            fun_fact = curr.get("fun_fact", "")
            return f"Aree, thoda sa chook gaye! Iska sahi jawab Option {correct_id} tha. {fun_fact} Agle sawal me koshish karte hain!"
