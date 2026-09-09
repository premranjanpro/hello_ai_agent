"""
base.py - Base In-Memory FunctionContext for Voice Calls with Session Tracking & Disconnect Hooks.
"""

import json
import logging
import time
from typing import Optional, Dict, Any
from livekit.agents import llm

logger = logging.getLogger("toolchain.base")


class BaseToolContext(llm.FunctionContext):
    """
    Base FunctionContext for LiveKit Voice Agent.
    Manages in-memory session states, LiveKit Room hooks (like graceful disconnect),
    and end-of-call structured payload compilation.
    """

    def __init__(
        self,
        call_session_id: str = "",
        user_id: str = "",
        api_base_url: str = "http://localhost:5063",
        room: Any = None,
        call_id: Optional[str] = None,
        caller_id: Optional[str] = None,
    ):
        super().__init__()
        self.call_session_id = call_id or call_session_id
        self.user_id = caller_id or user_id
        self.api_base_url = api_base_url.rstrip("/")
        self.room = room

        # Graceful disconnect state (waits for assistant goodbye speech playout)
        self.disconnect_pending = False
        self.disconnect_reason = ""

        # Central in-memory session dictionary
        self.session_data: Dict[str, Any] = {
            "fare_estimate": None,
            "cab_booking": None,
            "hr_evaluation": None,
            "emergency_alert": None,
            "medicine_reminders": [],
            "english_feedback": [],
            "quiz_progress": None,
            "personal_milestones": [],
            "wallet_balance_inquiries": [],
            "reported_issues": [],
            "transfer_requests": [],
            "callback_request": None,
            "software_lead": None,
            "game_session": None,
            "tool_history": [],
            "last_assistant_text": "",
        }

    @property
    def disconnect_requested(self) -> bool:
        return self.disconnect_pending

    @disconnect_requested.setter
    def disconnect_requested(self, val: bool):
        self.disconnect_pending = val

    def record_tool_invocation(self, tool_name: str, details: Dict[str, Any]):
        """Tracks every tool invocation in in-memory session history."""
        self.session_data["tool_history"].append({
            "tool": tool_name,
            "timestamp": time.time(),
            **details
        })

    def request_disconnect(self, reason: str = "user_requested"):
        """
        Flags that the call should be disconnected after assistant's goodbye speech completes.
        Prevents abruptly cutting off the audio stream mid-word.
        """
        self.disconnect_pending = True
        self.disconnect_reason = reason
        logger.info(f"📞 [toolchain.base] Graceful disconnect flagged: reason='{reason}'")

    def get_final_structured_payload(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        Compiles in-memory session data into a clean, unified payload ready
        for POST /api/ai/calls/{call_id}/structured-data at call wrap-up.
        """
        # 1. Cab Booking Payload
        if self.session_data.get("cab_booking"):
            b = self.session_data["cab_booking"]
            return {
                "dataType": "cab_booking",
                "structuredJson": json.dumps(b),
                "summary": f"Cab {b['bookingId']} confirmed ({b['cabType']}) from {b['pickup']} to {b['drop']}. Driver: {b['driverName']}, OTP: {b['otp']}, Fare: Rs.{b['fare']}"
            }

        if self.session_data.get("fare_estimate") and "cab_booking" in persona_id:
            fe = self.session_data["fare_estimate"]
            return {
                "dataType": "cab_booking_inquiry",
                "structuredJson": json.dumps(fe),
                "summary": f"Fare inquiry for {fe['cabType']} from {fe['pickup']} to {fe['drop']} (Rs.{fe['estimatedFare']})"
            }

        # 2. HR Candidate Evaluation Payload
        if self.session_data.get("hr_evaluation"):
            ev = self.session_data["hr_evaluation"]
            return {
                "dataType": "hr_evaluation",
                "structuredJson": json.dumps(ev),
                "summary": f"HR Screening: {ev['candidateName']} for {ev['roleApplied']}. Exp: {ev['experienceYears']} yrs, Score: {ev['scoreOutOf10']}/10 ({ev['recommendation']})"
            }

        # 3. Parents Care Emergency Alert Payload
        if self.session_data.get("emergency_alert"):
            emg = self.session_data["emergency_alert"]
            return {
                "dataType": "emergency_alert",
                "structuredJson": json.dumps(emg),
                "summary": f"⚠️ EMERGENCY ALERT: Urgency: {emg['urgency']}. Symptoms: {emg['symptoms']}"
            }

        # 4. English Learning Summary
        if self.session_data.get("english_feedback"):
            feedbacks = self.session_data["english_feedback"]
            return {
                "dataType": "english_coaching",
                "structuredJson": json.dumps({"totalCorrections": len(feedbacks), "feedbacks": feedbacks}),
                "summary": f"Spoken English Session: {len(feedbacks)} constructive feedback corrections provided."
            }

        # 5. Kids Learning Progress
        if self.session_data.get("quiz_progress"):
            qp = self.session_data["quiz_progress"]
            return {
                "dataType": "kids_quiz",
                "structuredJson": json.dumps(qp),
                "summary": f"Kids Learning: {qp.get('topic', 'General')} quiz completed with score {qp.get('score', 0)}."
            }

        # 6. Companion Milestones
        if self.session_data.get("personal_milestones"):
            ms = self.session_data["personal_milestones"]
            return {
                "dataType": "companion_milestones",
                "structuredJson": json.dumps(ms),
                "summary": f"Companion Session: {len(ms)} personal caller affinity milestones recorded."
            }

        # 7. Callback Request Payload
        if self.session_data.get("callback_request"):
            cb = self.session_data["callback_request"]
            return {
                "dataType": "callback_request",
                "structuredJson": json.dumps(cb),
                "summary": f"Callback scheduled: {cb.get('preferredTime', 'later')} (delay: {cb.get('delayMinutes', 15)} mins)."
            }

        # 8. B2B Software Sales Lead Payload
        if self.session_data.get("software_lead"):
            lead = self.session_data["software_lead"]
            sol = lead.get("interested_solution") or "General Mobility SaaS"
            demo = lead.get("demo_scheduled")
            demo_text = f", Demo: {demo['slot']}" if demo else ""
            return {
                "dataType": "software_lead",
                "structuredJson": json.dumps(lead),
                "summary": f"Software Lead: {sol} for '{lead.get('business_name') or lead.get('client_name', 'Prospect')}'{demo_text}"
            }

        # 9. Kids Game Session Payload
        if self.session_data.get("game_session"):
            gs = self.session_data["game_session"]
            return {
                "dataType": "kids_game",
                "structuredJson": json.dumps(gs),
                "summary": f"Kids Quiz Game: Score: {gs.get('score', 0)} pts, Stars: {gs.get('stars', 0)} ⭐ ({gs.get('correct_answers', 0)}/{gs.get('total_questions_asked', 0)} correct)."
            }

        return None


# Alias for backwards compatibility
BaseVoiceTool = BaseToolContext
