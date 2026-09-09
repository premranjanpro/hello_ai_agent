"""
hr_tools.py - Dedicated In-Memory Tools for HR & Recruitment Screening Personas.
"""

import logging
import time
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.hr")


class HrScreeningToolsMixin:
    """HR screening, evaluation, and interview scheduling tools."""

    @llm.ai_callable(description="Record candidate screening evaluation score, role, experience, notice period, and recommendation in session memory.")
    async def save_hr_candidate_evaluation(
        self,
        candidate_name: Annotated[str, "Candidate full name"],
        role_applied: Annotated[str, "Job position applied for"],
        years_experience: Annotated[float, "Years of relevant professional experience"],
        expected_ctc: Annotated[str, "Expected salary or CTC mentioned by candidate"],
        notice_period_days: Annotated[int, "Notice period in days (e.g. 15, 30, 60)"] = 30,
        score_out_of_10: Annotated[int, "Screening rating between 1 and 10 based on candidate answers"] = 8,
        recommendation: Annotated[str, "Short recommendation note e.g. 'Shortlisted for technical round'"] = "Shortlisted",
    ) -> str:
        logger.info(f"💼 [Tool] save_hr_candidate_evaluation: {candidate_name} ({role_applied}), score={score_out_of_10}/10")

        self.session_data["hr_evaluation"] = {
            "candidateName": candidate_name,
            "roleApplied": role_applied,
            "experienceYears": years_experience,
            "expectedCtc": expected_ctc,
            "noticePeriodDays": notice_period_days,
            "scoreOutOf10": min(10, max(1, int(score_out_of_10))),
            "recommendation": recommendation,
            "evaluatedAt": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.record_tool_invocation("save_hr_candidate_evaluation", {"candidate": candidate_name, "score": score_out_of_10})

        return (
            f"Aapki screening profile record ho gayi hai. Total experience {years_experience} saal aur expected CTC {expected_ctc} note kar liya hai. "
            "Recruitment team agle round ke liye aapse jald hi contact karegi."
        )

    @llm.ai_callable(description="Record candidate response to screening questions.")
    async def record_screening_answer(
        self,
        candidate_name: Annotated[str, "Candidate full name"],
        question_topic: Annotated[str, "Topic or question asked"],
        answer_summary: Annotated[str, "Summary of candidate's answer"],
    ) -> str:
        logger.info(f"💼 [Tool] record_screening_answer: {candidate_name} ({question_topic})")
        self.record_tool_invocation("record_screening_answer", {"candidate": candidate_name, "topic": question_topic, "answer": answer_summary})
        return f"Aapka {question_topic} se related answer note kar liya gaya hai."

    @llm.ai_callable(description="Schedule or propose a technical or hiring manager interview slot for a qualified candidate.")
    async def schedule_interview(
        self,
        candidate_name: Annotated[str, "Candidate full name"],
        preferred_day: Annotated[str, "Preferred day or date (e.g. 'Tomorrow', 'Monday 3 PM')"],
        interview_type: Annotated[str, "Interview format: 'online_video' or 'telephonic'"] = "online_video",
    ) -> str:
        logger.info(f"📅 [Tool] schedule_interview: {candidate_name} on {preferred_day} ({interview_type})")
        self.record_tool_invocation("schedule_interview", {"day": preferred_day, "type": interview_type})

        return (
            f"Perfect! Aapka {interview_type.replace('_', ' ')} interview {preferred_day} ke liye schedule kar diya gaya hai. "
            "Meeting link aur details aapko WhatsApp aur Email par bhej di jayengi."
        )
