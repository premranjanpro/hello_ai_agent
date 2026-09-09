"""
pipeline package - End-to-end Voice Pipeline Engine.
Provides calibrated VAD, real-time STT, multi-engine TTS, audio recording, and unified builder.
"""

from pipeline.config import CallingPipelineConfig, pipeline_config
from pipeline.vad import SileroVADProvider
from pipeline.stt import SttProvider
from pipeline.audio_recorder import AudioRecorder
from pipeline.tts import EdgeTTS, SarvamTTS, KokoroTTS, TtsFactory, create_tts_engine
from pipeline.builder import VoicePipelineBuilder

__all__ = [
    "CallingPipelineConfig",
    "pipeline_config",
    "SileroVADProvider",
    "SttProvider",
    "AudioRecorder",
    "EdgeTTS",
    "SarvamTTS",
    "KokoroTTS",
    "TtsFactory",
    "create_tts_engine",
    "VoicePipelineBuilder",
]
