"""
care_tools.py - Dedicated In-Memory Tools for Parents & Elderly Care Persona.
"""

import logging
import random
import time
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.care")


class ParentsCareToolsMixin:
    """Parents care, distress response, and health reminder tools."""

    @llm.ai_callable(description="Trigger an immediate emergency alert for parents or elderly care when critical symptoms, pain, fall, or distress are reported.")
    async def trigger_parent_emergency_alert(
        self,
        urgency_level: Annotated[str, "Urgency level: 'HIGH', 'CRITICAL', or 'MODERATE'"] = "HIGH",
        symptoms: Annotated[str, "Reported pain, fall, severe breathlessness, or distress description"] = "Immediate attention needed",
    ) -> str:
        logger.warning(f"🚨 [Tool] trigger_parent_emergency_alert: Urgency={urgency_level}, Symptoms={symptoms}")

        alert_id = f"EMG-{random.randint(10000, 99999)}"
        self.session_data["emergency_alert"] = {
            "alertId": alert_id,
            "urgency": urgency_level,
            "symptoms": symptoms,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.record_tool_invocation("trigger_parent_emergency_alert", {"alertId": alert_id, "urgency": urgency_level})

        return (
            "Aapji bilkul chinta mat kijiye aur aaram se baithiye. Maine parivaar ko turant alert bhej diya hai. "
            "Aap aaram kijiye, madad aa rahi hai."
        )

    @llm.ai_callable(description="Set or verify daily medication reminder schedule for elderly parents (e.g. BP tablet, sugar medicine, tonic).")
    async def set_medicine_reminder(
        self,
        medicine_name: Annotated[str, "Name of the medicine or tablet (e.g. 'BP tablet', 'Metformin')"],
        time_of_day: Annotated[str, "Schedule timing (e.g. 'Morning after breakfast', 'Night before sleep')"],
    ) -> str:
        logger.info(f"💊 [Tool] set_medicine_reminder: '{medicine_name}' at '{time_of_day}'")
        self.session_data["medicine_reminders"].append({
            "medicine": medicine_name,
            "time": time_of_day,
            "loggedAt": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.record_tool_invocation("set_medicine_reminder", {"medicine": medicine_name, "time": time_of_day})

        return f"Maine note kar liya hai ji! {medicine_name} {time_of_day} lene ka reminder set ho gaya hai. Samay par yaad dilaungi."
