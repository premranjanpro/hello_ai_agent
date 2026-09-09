"""
pipeline/tts/sarvam_tts.py - Sarvam AI Bulbul TTS Provider.
Engineered specifically for Indian Languages (Hindi, Hinglish, Bengali, Tamil, etc.).
"""

import io
import base64
import logging
import asyncio
import uuid
from typing import Optional
import aiohttp
from pydub import AudioSegment

from livekit.agents import tts
from livekit import rtc

logger = logging.getLogger("pipeline.tts.sarvam")


class SarvamTTS(tts.TTS):
    """
    LiveKit TTS implementation for Sarvam AI (Bulbul) API.
    Provides natural Hindi and Hinglish cadence for conversational personas.
    """

    def __init__(
        self,
        api_key: str,
        target_language_code: str = "hi-IN",
        speaker: str = "meera",
        pace: float = 1.0,
        pitch: float = 0.0,
    ):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self.api_key = api_key
        self.target_language_code = target_language_code
        self.speaker = speaker
        self.pace = pace
        self.pitch = pitch

    def synthesize(self, text: str) -> "tts.ChunkedStream":
        return SarvamChunkedStream(self, text)


class SarvamChunkedStream(tts.ChunkedStream):
    def __init__(self, tts_instance: SarvamTTS, text: str):
        super().__init__(tts=tts_instance, input_text=text)
        self._tts = tts_instance
        self._text = text
        self._request_id = str(uuid.uuid4())

    async def _run(self) -> None:
        if not self._text.strip():
            return

        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": self._tts.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": [self._text.strip()],
            "target_language_code": self._tts.target_language_code,
            "speaker": self._tts.speaker,
            "pitch": self._tts.pitch,
            "pace": self._tts.pace,
            "loudness": 1.2,
            "speech_sample_rate": 24000,
            "enable_preprocessing": True,
            "model": "bulbul:v1",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"[SarvamTTS] API Error {resp.status}: {err_text}")
                        return
                    data = await resp.json()
                    audios = data.get("audios", [])
                    if not audios:
                        return
                    wav_bytes = base64.b64decode(audios[0])

            audio_seg = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
            audio_seg = audio_seg.set_frame_rate(24000).set_channels(1).set_sample_width(2)

            raw_pcm = audio_seg.raw_data
            chunk_size_samples = 480  # 20ms @ 24kHz
            chunk_size_bytes = chunk_size_samples * 2

            offset = 0
            while offset < len(raw_pcm):
                chunk_bytes = raw_pcm[offset : offset + chunk_size_bytes]
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
            logger.error(f"[SarvamTTS] Synthesis failed: {e}")
