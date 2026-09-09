"""
objection_handler.py - Enterprise Voice Objection Handling & Conversational Pivot Engine.
Provides real-time objection detection, empathetic acknowledgment, value reframing, and low-friction next steps.
Calibrated for English, Hindi, and Hinglish B2B Sales and Lead Generation calls.
"""

import re
import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger("orchestrator.objection_handler")


class ObjectionHandler:
    """
    Intelligent objection detection and conversational reframing.
    Follows the 3-step consultative framework:
    1. Acknowledge (Validate the prospect's concern without being defensive)
    2. Reframe (Bridge to the core value or ROI metric)
    3. Low-Friction Ask (Pivot to a zero-risk micro-commitment like a 5-min demo or WhatsApp summary)
    """

    OBJECTION_PATTERNS = {
        "pricing": [
            r"\b(too expensive|bahut mehnga|zyada rate|high price|budget nahi|costs too much|no money|paisa nahi|expensive)\b",
            r"\b(discount milega|rate kam karo|kam karo|reduce price|out of budget)\b",
        ],
        "timing_busy": [
            r"\b(busy right now|driving|driving kar raha|baad me|call later|meeting me|not a good time|busy hoon)\b",
            r"\b(fursat nahi|free nahi hoon|call tomorrow|kal call karo|shaam ko)\b",
        ],
        "existing_vendor": [
            r"\b(already have|already using|pehle se hai|dusra software|mera khud ka|ola|uber|in-house)\b",
            r"\b(existing system|dusra vendor|competitor|contracted)\b",
        ],
        "send_whatsapp_email": [
            r"\b(whatsapp kar do|send on whatsapp|email bhej do|send brochure|send details|pdf bhej do|message kar do)\b",
            r"\b(send me an email|write to me|share on whatsapp)\b",
        ],
        "bot_skepticism": [
            r"\b(are you a robot|are you ai|robot ho kya|ai bol raha hai|computer bol raha hai|machine ho)\b",
            r"\b(asli aadmi se baat karao|human agent|transfer to human)\b",
        ],
        "not_interested": [
            r"\b(not interested|nahi chahiye|interest nahi hai|no need|zarurat nahi|don't call|mat karo)\b",
        ],
    }

    STRATEGIES: Dict[str, Dict[str, str]] = {
        "pricing": {
            "acknowledge": "Bilkul samajh sakta hoon, budget aur ROI kisi bhi business ke liye sabse pehli priority hoti hai.",
            "reframe": "Hamara system actually aapke commission aur manual dispatch costs ko 40% tak reduce karta hai, jisse yeh pehle hi mahine me self-fund ho jata hai.",
            "low_friction_ask": "Kya main aapko 5 minute ka quick breakdown dikha sakta hoon, bina kisi purchase commitment ke?",
        },
        "timing_busy": {
            "acknowledge": "Arey bilkul sir, aapka waqt bohot keemti hai aur main bilkul disturb nahi karna chahta.",
            "reframe": "Main bas 30 seconds me quick overview share kar sakta hoon ya phir aapke convenient time par reschedule kar lein.",
            "low_friction_ask": "Kya aaj shaam ko 5 baje ya kal subah 11 baje aapko 2 minute ke liye call karna theek rahega?",
        },
        "existing_vendor": {
            "acknowledge": "Great! Yeh sunkar accha laga ki aap already digital system use kar rahe hain.",
            "reframe": "Kayi clients jo pehle dusra software use kar rahe the, unhone hume white-label branded apps aur zero server downtime ke liye switch kiya.",
            "low_friction_ask": "Aapko koi vendor change nahi karna, bas ek quick feature comparison report dekh lijiye, theek rahega?",
        },
        "send_whatsapp_email": {
            "acknowledge": "Haan ji bilkul, main abhi brochure aur demo video aapke WhatsApp par bhej raha hoon.",
            "reframe": "Lekin brochure me 50 alag-alag modules hain. Agar aap bas apna primary requirement bata dein—jaise Cab fleet ya Tour CRM—to main exact relevant material bhej paunga.",
            "low_friction_ask": "Aapke paas total kitni cabs ya monthly packages hain?",
        },
        "bot_skepticism": {
            "acknowledge": "Haha, ji haan! Main Pruva Tech ka real-time AI Voice Assistant hoon, jo bilkul natural conversation ke liye designed hai.",
            "reframe": "Main aapke saare sawaalo ke jawab live de sakta hoon aur live demo bhi schedule kar sakta hoon.",
            "low_friction_ask": "Bataiye, aapke business me software se related kya help kar sakta hoon?",
        },
        "not_interested": {
            "acknowledge": "Main bilkul samajh gaya sir, koi issue nahi.",
            "reframe": "Hamara goal aapka waqt kharab karna nahi hai. Agar future me white-label apps ya fleet automation ki zarurat ho to Pruva Tech hamesha available hai.",
            "low_friction_ask": "Kya main ek 1-page WhatsApp summary bhej doon taaki reference ke liye aapke paas rahe?",
        },
    }

    @classmethod
    def detect_objection(cls, user_text: str) -> Optional[Tuple[str, Dict[str, str]]]:
        """
        Analyzes user utterance and returns objection category and reframing strategy if found.
        """
        if not user_text:
            return None

        clean_text = user_text.lower()
        for category, patterns in cls.OBJECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, clean_text, re.IGNORECASE):
                    strategy = cls.STRATEGIES.get(category, {})
                    logger.info(f"[ObjectionHandler] Detected objection: '{category}' in utterance: '{user_text}'")
                    return category, strategy

        return None

    @classmethod
    def get_prompt_guidelines(cls) -> str:
        """
        Generates system prompt injection instructions for enterprise objection handling.
        """
        return (
            "\n\n====================================================================\n"
            "CRITICAL OBJECTION HANDLING & CONVERSATIONAL PIVOT GUIDELINES:\n"
            "Customers often present automatic resistance. Follow this 3-step consultative pivot:\n"
            "1. ACKNOWLEDGE: Never argue, contradict, or sound defensive. Always empathize first ('Bilkul samajh sakta hoon...', 'I understand...').\n"
            "2. REFRAME: Connect their objection to our core value (ROI, white-label branding, zero-commission cab fleet, time saved).\n"
            "3. LOW-FRICTION ASK: Never push for an immediate sale. Always ask for a micro-commitment (e.g. 'Can I send a 2-minute video on WhatsApp?', 'Would 5 PM tomorrow be better?').\n\n"
            "SPECIFIC OBJECTION PLAYBOOKS:\n"
            "- If user says 'Too expensive / Budget nahi': Acknowledge cost importance, reframe that software saves 40% dispatch commissions, offer a free ROI calculator.\n"
            "- If user says 'Busy right now / Driving': Apologize warmly for the interruption, ask for a specific callback time (e.g. 5 PM today or 11 AM tomorrow).\n"
            "- If user says 'Already have software': Compliment their digital mindset, offer a zero-risk feature comparison sheet.\n"
            "- If user says 'WhatsApp pe bhej do': Agree immediately, but ask 1 clarifying question (e.g. 'Cab size' or 'Agency type') so the WhatsApp brochure is customized.\n"
            "- If user asks 'Are you AI / Robot?': Be honest with a cheerful, warm tone: 'Yes! I am Pruva's AI Assistant, trained to help you with software demos.'\n"
            "- If user gives a firm 'Not interested': Be gracious and polite: 'No problem at all, thank you for your time. Have a wonderful day!' and close gracefully.\n"
            "====================================================================\n"
        )
