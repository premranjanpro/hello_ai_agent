"""
pipeline/builder.py - High-Performance VoicePipelineAgent Builder.
Configures calibrated Silero VAD, Streaming STT, Orchestrated LLM, and Neural TTS
with ultra-responsive turn-taking, fast barge-in, and zero choppy lag.
"""

import logging
from typing import Optional, Any
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents import llm

from pipeline.config import CallingPipelineConfig
from pipeline.vad import SileroVADProvider
from pipeline.stt import SttProvider
from pipeline.tts.factory import TtsFactory

logger = logging.getLogger("pipeline.builder")


class VoicePipelineBuilder:
    """Builder for instantiating an enterprise-grade LiveKit VoicePipelineAgent."""

    @staticmethod
    def build(
        llm_instance: llm.LLM,
        chat_ctx: llm.ChatContext,
        fnc_ctx: Optional[llm.FunctionContext] = None,
        tts_provider: Optional[str] = None,
        voice: Optional[str] = None,
        pitch: Optional[str] = None,
        rate: Optional[str] = None,
        language: str = "hinglish",
        gender: str = "female",
        config: Optional[CallingPipelineConfig] = None,
    ) -> VoicePipelineAgent:
        cfg = config or CallingPipelineConfig()

        vad = SileroVADProvider.create(config=cfg)
        stt = SttProvider.create(language=language, vad=vad)
        tts = TtsFactory.create(
            provider=tts_provider,
            voice=voice,
            pitch=pitch,
            rate=rate,
            language=language,
            gender=gender,
        )

        logger.info(
            f"[VoicePipelineBuilder] Building pipeline: "
            f"VAD(thresh={cfg.vad_threshold}, endpt={cfg.vad_min_endpointing_delay}s), "
            f"BargeIn(interr_dur={cfg.interrupt_speech_duration}s), "
            f"TTS(voice={voice or 'default'})"
        )

        agent = VoicePipelineAgent(
            vad=vad,
            stt=stt,
            llm=llm_instance,
            tts=tts,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
            min_endpointing_delay=cfg.vad_min_endpointing_delay,
            max_endpointing_delay=cfg.vad_max_endpointing_delay,
            interrupt_speech_duration=cfg.interrupt_speech_duration,
            interrupt_min_words=cfg.interrupt_min_words,
            preemptive_synthesis=cfg.preemptive_synthesis,
            max_nested_fnc_calls=cfg.max_nested_fnc_calls,
        )

        return agent
