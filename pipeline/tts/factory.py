"""
pipeline/tts/factory.py - Multi-Engine Audio Synthesis Provider Factory.
Supports Edge-TTS (default, neural), Kokoro-82M (local CPU), and Sarvam AI (Indian accents).
"""

import os
import logging
from typing import Optional
from livekit.agents import tts

from pipeline.tts.edge_tts import EdgeTTS
from pipeline.tts.sarvam_tts import SarvamTTS
from pipeline.tts.kokoro_tts import KokoroTTS

logger = logging.getLogger("pipeline.tts.factory")


class TtsFactory:
    """Factory for instantiating livekit-compatible TTS providers."""

    @staticmethod
    def create(
        provider: Optional[str] = None,
        voice: Optional[str] = None,
        pitch: Optional[str] = None,
        rate: Optional[str] = None,
        language: str = "hinglish",
        gender: str = "female",
    ) -> tts.TTS:
        chosen_provider = (provider or os.getenv("DEFAULT_TTS_PROVIDER", "edge")).strip().lower()
        active_pitch = pitch or "+0Hz"
        active_rate = rate or "+0%"

        logger.info(f"[TtsFactory] Creating TTS engine: '{chosen_provider}' (Pitch: {active_pitch}, Rate: {active_rate})")

        # 1. Sarvam AI Bulbul
        if chosen_provider == "sarvam":
            sarvam_key = os.getenv("SARVAM_API_KEY", "").strip()
            if sarvam_key:
                speaker = "meera" if gender == "female" else "dhruv"
                pace_val = 1.25 if ("+18%" in active_rate or "+20%" in active_rate or "+22%" in active_rate) else (0.9 if "-10%" in active_rate else (1.1 if "+8%" in active_rate else 1.0))
                pitch_val = -0.5 if "-5Hz" in active_pitch else (0.8 if "+20Hz" in active_pitch else 0.0)
                logger.info(f"[TtsFactory] Initialized Sarvam AI Bulbul (Speaker: {speaker}, Pace: {pace_val}, Pitch: {pitch_val})")
                return SarvamTTS(
                    api_key=sarvam_key,
                    target_language_code="hi-IN",
                    speaker=speaker,
                    pace=pace_val,
                    pitch=pitch_val,
                )
            else:
                logger.warning("[TtsFactory] SARVAM_API_KEY is missing! Gracefully falling back to EdgeTTS.")

        # 2. Kokoro-82M
        elif chosen_provider == "kokoro":
            try:
                kokoro_voice = "af_heart" if gender == "female" else "am_adam"
                speed_val = 1.25 if ("+18%" in active_rate or "+20%" in active_rate or "+22%" in active_rate) else (0.9 if "-10%" in active_rate else (1.1 if "+8%" in active_rate else 1.0))
                logger.info(f"[TtsFactory] Initialized Kokoro-82M (Voice: {kokoro_voice}, Speed: {speed_val})")
                return KokoroTTS(voice=kokoro_voice, speed=speed_val)
            except Exception as e:
                logger.warning(f"[TtsFactory] Kokoro unavailable: {e}. Gracefully falling back to EdgeTTS.")

        # 3. Microsoft Edge-TTS (Default Free)
        default_voice = voice or ("hi-IN-SwaraNeural" if gender == "female" else "hi-IN-MadhurNeural")
        logger.info(f"[TtsFactory] Initialized EdgeTTS (Voice: {default_voice}, Pitch: {active_pitch}, Rate: {active_rate})")
        return EdgeTTS(
            voice=default_voice,
            pitch=active_pitch,
            rate=active_rate,
        )


def create_tts_engine(
    provider: Optional[str] = None,
    voice: Optional[str] = None,
    pitch: Optional[str] = None,
    rate: Optional[str] = None,
    language: str = "hinglish",
    gender: str = "female",
) -> tts.TTS:
    """Convenience alias function matching legacy tts_factory.py API."""
    return TtsFactory.create(
        provider=provider,
        voice=voice,
        pitch=pitch,
        rate=rate,
        language=language,
        gender=gender,
    )
