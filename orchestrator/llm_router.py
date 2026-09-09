"""
orchestrator/llm_router.py - Dynamic Model & Engine Routing.
Selects optimal LLM engine & parameters depending on call latency requirements and task complexity.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("orchestrator.router")


@dataclass
class RouteConfig:
    model: str
    provider: str
    temperature: float
    max_tokens: int


class LlmRouter:
    """Routes voice turn requests to the most responsive model."""

    DEFAULT_VOICE_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    FAST_VOICE_MODEL = "qwen/qwen3.8-27b"
    FALLBACK_VOICE_MODEL = "groq/compound-mini"
    EXTRACTION_MODEL = "qwen/qwen3.8-27b"

    @classmethod
    def get_voice_route(cls, failover: bool = False, speed_priority: bool = False) -> RouteConfig:
        model = cls.FALLBACK_VOICE_MODEL if failover else os.getenv("GROQ_MODEL", cls.FAST_VOICE_MODEL)
        return RouteConfig(
            model=model,
            provider="groq",
            temperature=0.35,
            max_tokens=150,
        )

    @classmethod
    def get_extractor_route(cls) -> RouteConfig:
        return RouteConfig(
            model=cls.EXTRACTION_MODEL,
            provider="groq",
            temperature=0.1,
            max_tokens=256,
        )
