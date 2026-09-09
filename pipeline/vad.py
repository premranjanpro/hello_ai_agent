"""
pipeline/vad.py - Silero VAD Prewarming & Loading Manager.
Calibrated for mobile voice calls without clipping initial consonants or short acknowledgements.
"""

import logging
from typing import Optional
from livekit.agents import JobProcess
from livekit.plugins import silero
from pipeline.config import (
    CallingPipelineConfig,
    VAD_ACTIVATION_THRESHOLD,
    VAD_MIN_SPEECH_DURATION,
    VAD_PREFIX_PADDING,
)

logger = logging.getLogger("pipeline.vad")


class VadManager:
    """Manages prewarming and loading of the Silero Voice Activity Detector."""

    @staticmethod
    def prewarm(proc: JobProcess):
        """Preloads Silero VAD model in the worker process for zero cold-start latency."""
        logger.info("[VadManager] Prewarming Silero VAD with tuned speech thresholds...")
        proc.userdata["vad"] = silero.VAD.load(
            activation_threshold=VAD_ACTIVATION_THRESHOLD,
            min_speech_duration=VAD_MIN_SPEECH_DURATION,
            prefix_padding_duration=VAD_PREFIX_PADDING,
        )
        logger.info("[VadManager] Silero VAD prewarmed successfully.")

    @staticmethod
    def load(proc: Optional[JobProcess] = None):
        """Retrieves prewarmed VAD instance or loads fresh if not prewarmed."""
        if proc and proc.userdata.get("vad"):
            return proc.userdata["vad"]

        return silero.VAD.load(
            activation_threshold=VAD_ACTIVATION_THRESHOLD,
            min_speech_duration=VAD_MIN_SPEECH_DURATION,
            prefix_padding_duration=VAD_PREFIX_PADDING,
        )

    @classmethod
    def create(cls, config: Optional[CallingPipelineConfig] = None, proc: Optional[JobProcess] = None):
        """Alias create method returning calibrated VAD instance."""
        threshold = config.vad_threshold if config else VAD_ACTIVATION_THRESHOLD
        min_speech = config.vad_min_speech_duration if config else VAD_MIN_SPEECH_DURATION
        prefix_pad = config.vad_prefix_padding if config else VAD_PREFIX_PADDING

        if proc and proc.userdata.get("vad"):
            return proc.userdata["vad"]

        return silero.VAD.load(
            activation_threshold=threshold,
            min_speech_duration=min_speech,
            prefix_padding_duration=prefix_pad,
        )


# Alias
SileroVADProvider = VadManager
