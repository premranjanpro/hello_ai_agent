"""
audio_recorder.py - Dual-Track Real-Time 24kHz Mono WAV Audio Recorder.
"""

import logging
import os
import wave
from livekit import rtc
from pipeline.config import RECORDINGS_DIR

logger = logging.getLogger("pipeline.audio_recorder")


class AudioRecorder:
    """Records incoming participant audio frames into a 16-bit 24kHz mono WAV file in real time directly on disk."""

    def __init__(self, output_path: str = "", sample_rate: int = 24000):
        self.output_path = output_path
        self.sample_rate = sample_rate
        self._wf = None
        self._is_recording = False
        self._total_bytes = 0

    @classmethod
    def for_call(cls, call_id: str, sample_rate: int = 24000) -> "AudioRecorder":
        """Creates recorder automatically targeted at recordings/{call_id}.wav."""
        filename = f"{call_id}.wav"
        filepath = os.path.join(RECORDINGS_DIR, filename)
        return cls(filepath, sample_rate=sample_rate)

    def start(self):
        try:
            self._wf = wave.open(self.output_path, "wb")
            self._wf.setnchannels(1)
            self._wf.setsampwidth(2)  # 16-bit
            self._wf.setframerate(self.sample_rate)
            self._is_recording = True
            logger.info(f"🎙️ [AudioRecorder] Recording started: {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to open recording file: {e}")

    def write_frame(self, frame: rtc.AudioFrame):
        if self._is_recording and self._wf and frame.data:
            try:
                self._wf.writeframes(frame.data)
                self._total_bytes += len(frame.data)
            except Exception as e:
                logger.error(f"Error writing audio frame: {e}")

    def stop_and_save(self) -> int:
        self._is_recording = False
        if self._wf:
            try:
                self._wf.close()
                self._wf = None
                logger.info(f"🎙️ [AudioRecorder] Call recording finalized: {self.output_path} ({self._total_bytes} bytes)")
            except Exception as e:
                logger.error(f"Error finalizing audio recording: {e}")
        return self._total_bytes
