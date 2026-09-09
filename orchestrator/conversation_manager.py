"""
conversation_manager.py - Provider-Independent Conversation & Dialog Manager.
Handles conversational state, action selection, adaptive engagement, silence management,
smart response length bounding, and interruption recovery across LiveKit, Twilio, and Exotel calls.
"""

import time
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("orchestrator.conversation_manager")


class ConversationState(str, Enum):
    INITIATED = "INITIATED"
    GREETING = "GREETING"
    LISTENING = "LISTENING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    WAITING_USER = "WAITING_USER"
    SILENCE_WARNING = "SILENCE_WARNING"
    QUALIFYING = "QUALIFYING"
    CTA_PRESENTED = "CTA_PRESENTED"
    TRANSFERRING = "TRANSFERRING"
    WRAPPING_UP = "WRAPPING_UP"
    ENDED = "ENDED"


class ConversationAction(str, Enum):
    ANSWER = "ANSWER"
    ASK = "ASK"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    WAIT = "WAIT"
    CLARIFY = "CLARIFY"
    TOOL_CALL = "TOOL_CALL"
    TRANSFER = "TRANSFER"
    END_CALL = "END_CALL"
    QUALIFY = "QUALIFY"
    SCHEDULE = "SCHEDULE"
    FOLLOW_UP = "FOLLOW_UP"


class EngagementSignal(str, Enum):
    ENGAGED = "ENGAGED"
    INTERESTED = "INTERESTED"
    CONFUSED = "CONFUSED"
    HESITANT = "HESITANT"
    QUIET = "QUIET"
    FRUSTRATED = "FRUSTRATED"
    READY_TO_CLOSE = "READY_TO_CLOSE"


class ConversationManager:
    """
    Provider-Agnostic Conversation Manager.
    Works identically whether audio stream arrives via WebRTC (LiveKit) or PSTN (Twilio/Exotel).
    """

    def __init__(
        self,
        call_id: str,
        purpose: str = "sales",
        agent_id: str = "sales",
        language: str = "hinglish",
        silence_timeout_sec: float = 6.5,
        max_silence_warnings: int = 2,
    ):
        self.call_id = call_id
        self.purpose = purpose.lower()
        self.agent_id = agent_id
        self.language = language.lower()
        self.silence_timeout_sec = silence_timeout_sec
        self.max_silence_warnings = max_silence_warnings

        self.state = ConversationState.INITIATED
        self.current_action = ConversationAction.GREETING if hasattr(ConversationAction, "GREETING") else ConversationAction.ACKNOWLEDGE

        # Metrics & telemetry
        self.turns: List[Dict[str, Any]] = []
        self.interruptions_count = 0
        self.silence_warnings_count = 0
        self.last_user_speech_time = time.time()
        self.last_ai_speech_time = time.time()
        self.detected_signals: List[EngagementSignal] = [EngagementSignal.ENGAGED]

        # Qualification / Extraction State
        self.collected_attributes: Dict[str, Any] = {}
        self.is_qualified: Optional[bool] = None
        self.qualification_score: int = 0
        self.next_action_recommendation: str = ""

    def on_user_speech_started(self):
        """Triggered immediately when VAD detects human speech."""
        self.last_user_speech_time = time.time()
        self.silence_warnings_count = 0  # reset silence warnings

        if self.state == ConversationState.SPEAKING:
            self.state = ConversationState.INTERRUPTED
            self.interruptions_count += 1
            logger.info(f"⚡ [ConversationManager] User interrupted AI. Total interruptions: {self.interruptions_count}")
        else:
            self.state = ConversationState.LISTENING

    def on_user_speech_committed(self, text: str) -> Tuple[ConversationAction, str]:
        """
        Processes transcribed user utterance, updates conversational signals,
        and decides the optimal next action.
        """
        text_clean = text.strip()
        self.last_user_speech_time = time.time()
        self.turns.append({"role": "user", "content": text_clean, "timestamp": time.time()})

        # 1. Analyze engagement signals
        signal = self._detect_engagement_signal(text_clean)
        self.detected_signals.append(signal)

        # 2. Check for explicit exit / hangup intent
        lower = text_clean.lower()
        if any(w in lower for w in ["bye", "alvida", "disconnect", "call cut", "baad me baat", "not interested", "nahi chahiye"]):
            self.state = ConversationState.WRAPPING_UP
            return ConversationAction.END_CALL, "Politely acknowledge and end the call gracefully."

        # 3. Check for transfer request
        if any(w in lower for w in ["manager se baat", "transfer", "senior se baat", "human agent"]):
            self.state = ConversationState.TRANSFERRING
            return ConversationAction.TRANSFER, "Transfer to human agent."

        # 4. Check for clarification requirement
        if any(w in lower for w in ["kya bola", "samajh nahi aaya", "repeat", "pardon", "what did you say", "again"]):
            return ConversationAction.CLARIFY, "Rephrase the last statement simply in shorter words."

        # 5. Default conversational action
        if "?" in text_clean or any(w in lower for w in ["kya", "kyun", "kaise", "how", "what", "price", "cost", "budget"]):
            return ConversationAction.ANSWER, "Answer user question directly and concisely."
        else:
            return ConversationAction.ASK, "Acknowledge response and ask next qualification question."

    def check_silence_status(self) -> Tuple[bool, str]:
        """
        Called periodically to evaluate whether silence threshold has passed.
        Returns (should_prompt, prompt_text_or_instruction).
        """
        if self.state in [ConversationState.SPEAKING, ConversationState.WRAPPING_UP, ConversationState.ENDED]:
            return False, ""

        idle_duration = time.time() - self.last_user_speech_time

        if idle_duration >= self.silence_timeout_sec:
            self.silence_warnings_count += 1
            self.last_user_speech_time = time.time()

            if self.silence_warnings_count >= self.max_silence_warnings:
                self.state = ConversationState.WRAPPING_UP
                if "hindi" in self.language:
                    return True, "Aapki aawaz nahi aa rahi hai. Hum aapse baad mein sampark karte hain. Dhanyawaad!"
                elif "hinglish" in self.language:
                    return True, "Lagta hai audio disconnect ho gaya hai. Hum aapko baad mein callback karte hain. Have a great day!"
                else:
                    return True, "It seems we lost your audio. We will reach back out to you later. Thank you!"
            else:
                self.state = ConversationState.SILENCE_WARNING
                if "hindi" in self.language:
                    return True, "Kya aap sun paa rahe hain? Boliye, main sun raha hoon."
                elif "hinglish" in self.language:
                    return True, "Kya aap sun paa rahe hain? Take your time, boliye."
                else:
                    return True, "Are you still there? Please take your time."

        return False, ""

    def get_response_guidelines(self) -> str:
        """Generates dynamic prompting instructions tailored to conversational state and signal."""
        latest_signal = self.detected_signals[-1] if self.detected_signals else EngagementSignal.ENGAGED

        guidance = [
            "- VOICE CONSTRAINT: Keep response under 1-2 short natural sentences (15-25 words max).",
            "- NO ROBOTIC INTROS: Do not re-introduce yourself every turn.",
            "- ONE THING AT A TIME: Never ask more than 1 question per turn."
        ]

        if latest_signal == EngagementSignal.CONFUSED:
            guidance.append("- USER IS CONFUSED: Clarify in extremely simple terms, avoid technical jargon.")
        elif latest_signal == EngagementSignal.READY_TO_CLOSE:
            guidance.append("- CLOSING OPPORTUNITY: Deliver clear CTA to confirm next meeting or qualification.")
        elif latest_signal == EngagementSignal.HESITANT:
            guidance.append("- HESITANT USER: Reassure warmly, offer flexible callback if they are busy.")

        return "\n".join(guidance)

    def _detect_engagement_signal(self, text: str) -> EngagementSignal:
        lower = text.lower()
        if any(w in lower for w in ["yes", "haan", "sure", "definitely", "theek hai", "bataiye", "interested", "accha", "great"]):
            return EngagementSignal.ENGAGED
        if any(w in lower for w in ["demo", "meeting", "join", "book", "schedule", "kal", "tomorrow"]):
            return EngagementSignal.READY_TO_CLOSE
        if any(w in lower for w in ["confused", "samajh nahi", "nahi samjha", "kya matlab", "meaning"]):
            return EngagementSignal.CONFUSED
        if any(w in lower for w in ["busy", "baad mein", "meeting mein", "driving", "driving hoon", "call later"]):
            return EngagementSignal.HESITANT
        if len(text.split()) <= 2:
            return EngagementSignal.QUIET
        return EngagementSignal.INTERESTED
