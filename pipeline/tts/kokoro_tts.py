"""
pipeline/tts/kokoro_tts.py - Kokoro-82M Open-Source TTS Provider.
Runs lightweight ONNX/PyTorch model on CPU with natural human cadence.
"""

import logging
import asyncio
import uuid
from typing import Optional

from livekit.agents import tts
from livekit import rtc
from pipeline.tts.edge_tts import EdgeTTS

logger = logging.getLogger("pipeline.tts.kokoro")


class KokoroTTS(tts.TTS):
    """
    LiveKit TTS implementation backed by Kokoro-82M (Apache 2.0).
    """

    def __init__(self, voice: str = "af_heart", speed: float = 1.0):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self.voice = voice
        self.speed = speed
        self._pipeline = None
        self._init_kokoro()

    def _init_kokoro(self):
        try:
            from kokoro import KPipeline
            self._pipeline = KPipeline(lang_code="a")
            logger.info(f"[KokoroTTS] Initialized KPipeline with voice: {self.voice}")
        except Exception as e:
            logger.warning(f"[KokoroTTS] Kokoro not installed/ready: {e}. Will fallback if invoked.")

    def synthesize(self, text: str) -> "tts.ChunkedStream":
        return KokoroChunkedStream(self, text)


class KokoroChunkedStream(tts.ChunkedStream):
    def __init__(self, tts_instance: KokoroTTS, text: str):
        super().__init__(tts=tts_instance, input_text=text)
        self._tts = tts_instance
        self._text = text
        self._request_id = str(uuid.uuid4())

    async def _run(self) -> None:
        if not self._text.strip():
            return

        if self._tts._pipeline is None:
            logger.info("[KokoroTTS] Pipeline unavailable, falling back dynamically to EdgeTTS.")
            fallback = EdgeTTS()
            stream = fallback.synthesize(self._text)
            async for event in stream:
                self._event_ch.send_nowait(event)
            return

        try:
            import numpy as np
            loop = asyncio.get_running_loop()

            def _generate():
                generator = self._tts._pipeline(self._text, voice=self._tts.voice, speed=self._tts.speed)
                all_audio = []
                for _, _, audio in generator:
                    all_audio.append(audio)
                if all_audio:
                    return np.concatenate(all_audio)
                return np.array([], dtype=np.float32)

            audio_data = await loop.run_in_executor(None, _generate)
            if len(audio_data) == 0:
                return

            pcm_data = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16).tobytes()

            chunk_size_samples = 480
            chunk_size_bytes = chunk_size_samples * 2
            offset = 0
            while offset < len(pcm_data):
                chunk_bytes = pcm_data[offset : offset + chunk_size_bytes]
                chunk_samples = len(chunk_bytes) // 2
                frame = rtc.AudioFrame(
                    data=chunk_bytes,
                    sample_rate=24000,
                    num_channels=1,
                    samples_per_channel=chunk_samples,
                )
                self._event_ch.send_nowait(
                    tts.SynthesizedAudio(
                        request_id=self._request_id,
                        frame=frame,
                    )
                )
                offset += chunk_size_bytes
                await asyncio.sleep(0.001)

        except Exception as e:
            logger.error(f"[KokoroTTS] Synthesis error: {e}")
