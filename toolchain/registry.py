"""
registry.py - Dynamic ToolRegistry assembling Common Tools + Persona Tools per call.
"""

import logging
from typing import Any, Dict, Type

from toolchain.base import BaseToolContext
from toolchain.common.call_control import CallControlToolsMixin
from toolchain.common.account_tools import AccountToolsMixin
from toolchain.common.general_tools import GeneralKnowledgeToolsMixin
from toolchain.common.family_tools import FamilyToolsMixin
from toolchain.personas.cab_tools import CabBookingToolsMixin
from toolchain.personas.hr_tools import HrScreeningToolsMixin
from toolchain.personas.care_tools import ParentsCareToolsMixin
from toolchain.personas.tutor_tools import EnglishTutorToolsMixin
from toolchain.personas.kids_tools import KidsLearningToolsMixin
from toolchain.personas.companion_tools import CompanionToolsMixin
from toolchain.personas.sales_tools import SoftwareSalesToolsMixin
from toolchain.personas.game_tools import KidsGameToolsMixin
from toolchain.user_calling import UserToUserCallToolsMixin
from toolchain.common.interactive_ui_emitter import InteractiveUiEmitterMixin
from toolchain.interactive import (
    InteractiveQuizGameToolsMixin,
    VisualPlacesToolsMixin,
    LiveNewsToolsMixin,
    InteractiveAlphabetToolsMixin,
    EducationalStoryToolsMixin,
    MediaPlayerToolsMixin,
)
from toolchain.interactive.places_tools import InteractivePlacesToolsMixin
from toolchain.interactive.kids_games_tools import KidsGamesToolsMixin

logger = logging.getLogger("toolchain.registry")

# Mapping of persona_id substring to specific persona tool mixin
_PERSONA_TOOL_MIXINS: Dict[str, Type] = {
    "cab_booking": CabBookingToolsMixin,
    "hr_interview": HrScreeningToolsMixin,
    "hr_job": HrScreeningToolsMixin,
    "parents_care": ParentsCareToolsMixin,
    "english_tutor": EnglishTutorToolsMixin,
    "kids_learning": KidsLearningToolsMixin,
    "romantic_chat": CompanionToolsMixin,
    "companion": CompanionToolsMixin,
    "software_sales": SoftwareSalesToolsMixin,
    "sales": SoftwareSalesToolsMixin,
    "kids_game": KidsGameToolsMixin,
    "game": KidsGameToolsMixin,
}


class ToolRegistry:
    """
    Factory that dynamically creates a tailored LiveKit FunctionContext
    combining universal common tools + persona-specific domain tools.
    """

    @classmethod
    def create_context(
        cls,
        persona_id: str,
        call_session_id: str = "",
        user_id: str = "",
        api_base_url: str = "http://localhost:5063",
        room: Any = None,
        language: str = "hinglish"
    ) -> BaseToolContext:
        """
        Builds a composite FunctionContext containing:
        1. BaseToolContext (Session tracking & graceful disconnect)
        2. CallControlToolsMixin (disconnect_call, repeat, language, speed, pause)
        3. AccountToolsMixin (wallet balance, human transfer, sms summary, report issue, verify identity)
        4. GeneralKnowledgeToolsMixin (real-time clock, live weather, daily inquiries)
        5. Matching Persona Tool Mixin (if persona matches cab, hr, care, tutor, kids, companion)
        """
        clean_id = (persona_id or "").lower()

        # Find matching persona mixin
        persona_mixin = None
        for key, mixin_cls in _PERSONA_TOOL_MIXINS.items():
            if key in clean_id:
                persona_mixin = mixin_cls
                break

        # Cleanly segment bases to prevent bloated tool token counts that trigger Groq 413 limits
        if any(k in clean_id for k in ["kids", "learning"]):
            # Focused Kids & Preschool learning suite
            bases = [
                BaseToolContext,
                CallControlToolsMixin,
                FamilyToolsMixin,
                InteractiveUiEmitterMixin,
                InteractivePlacesToolsMixin,
                InteractiveAlphabetToolsMixin,
                EducationalStoryToolsMixin,
                KidsGamesToolsMixin,
            ]
            class_name = f"CompositeContext_{clean_id}"
        elif any(k in clean_id for k in ["match", "bridge", "connect_host", "user_to_user"]):
            bases = [
                BaseToolContext,
                CallControlToolsMixin,
                GeneralKnowledgeToolsMixin,
                InteractiveUiEmitterMixin,
                UserToUserCallToolsMixin,
            ]
            class_name = f"CompositeContext_{clean_id}"
        else:
            bases = [
                BaseToolContext,
                CallControlToolsMixin,
                GeneralKnowledgeToolsMixin,
                InteractiveUiEmitterMixin,
                VisualPlacesToolsMixin,
                LiveNewsToolsMixin,
                AccountToolsMixin,
            ]
            if persona_mixin and persona_mixin not in bases:
                bases.append(persona_mixin)
                class_name = f"CompositeContext_{clean_id}"
            else:
                class_name = "CompositeContext_Common"

        # Deduplicate bases preserving insertion order
        unique_bases = list(dict.fromkeys(bases))

        # Create composite class type
        composite_type = type(class_name, tuple(unique_bases), {})

        # Instantiate with session parameters
        instance = composite_type(
            call_session_id=call_session_id,
            user_id=user_id,
            api_base_url=api_base_url,
            room=room,
        )
        instance.current_language = language
        instance.current_rate = "+0%"

        logger.info(f"🛠️ [ToolRegistry] Built {class_name} for persona '{persona_id}' (Persona Mixin: {getattr(persona_mixin, '__name__', 'None')})")
        return instance


# Backwards compatibility alias for existing code
class AiToolsContext(
    BaseToolContext,
    CallControlToolsMixin,
    AccountToolsMixin,
    GeneralKnowledgeToolsMixin,
    FamilyToolsMixin,
    UserToUserCallToolsMixin,
    InteractiveUiEmitterMixin,
    InteractiveQuizGameToolsMixin,
    VisualPlacesToolsMixin,
    LiveNewsToolsMixin,
    InteractiveAlphabetToolsMixin,
    EducationalStoryToolsMixin,
    MediaPlayerToolsMixin,
    CabBookingToolsMixin,
    HrScreeningToolsMixin,
    ParentsCareToolsMixin,
    EnglishTutorToolsMixin
):
    """Backwards-compatible mega context supporting all tools."""
    pass
