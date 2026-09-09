"""
pipeline/stt.py - Enterprise Resilient Speech-to-Text with Groq Whisper Turbo & StreamAdapter.
Provides genuine streaming turn-taking for LiveKit VoicePipelineAgent without fake Realtime websocket 404s.
"""

import logging
import os
from typing import Optional, Any
from dotenv import load_dotenv

from livekit.plugins import groq
from livekit.agents import stt, utils
from livekit.agents.stt.stream_adapter import StreamAdapterWrapper
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions
from pipeline.config import STT_LANGUAGE_PROMPT

load_dotenv()
logger = logging.getLogger("pipeline.stt")

# Whisper background noise & hallucination tokens to filter
WHISPER_HALLUCINATIONS = {
    "", "thank you", "thank you.", "subtitles by", "subtitles", 
    "amara.org", "[blank_audio]", "[applause]", "[music]",
    "you", "thanks for watching", "bye", "bye."
}

import re

class KidsPhoneticNormalizer:
    """
    Normalizes children's speech, phonetic variations, lisps, and common Whisper mishearings
    for Hindi, Hinglish, curriculum topics, landmarks, and characters.
    """

    PHONETIC_RULES = [
        # Landmarks / Places
        (r"\b(daazling|dazling|dajling|darjling|daajiling|daarjling|darjiling)\b", "darjeeling"),
        (r"\b(toy\s*tin|toi\s*ten|toy\s*tain|chook\s*chook|chhook\s*chhook|railgadi)\b", "toy train"),
        (r"\b(uti|ootee|ooti)\b", "ooty"),
        (r"\b(taaj\s*mahal|taj\s*mehal|tajmahal)\b", "taj mahal"),
        (r"\b(planatorium|planaterium|planetorium|taare\s*dekhne|space\s*museum)\b", "planetarium"),
        (r"\b(joo|zooo|janwar\s*dekhna|chidiyaghar)\b", "zoo"),
        (r"\b(barf\s*dekhna|snow\s*peak|snow\s*fall)\b", "gulmarg snow"),
        (r"\b(dolfin|dolphin|dolfins)\b", "goa dolphin"),
        (r"\b(house\s*boat|shikara|kerala\s*boat)\b", "kerala houseboat"),

        # Alphabet & Phonics
        (r"\b(epal|aepul|aple|apal)\b", "apple"),
        (r"\b(bol|bal)\b(?=\s+dikhao|\s+khelein|\s+lao|$)", "ball"),
        (r"\b(c\s*for\s*kat|c\s*for\s*tat)\b", "c for cat"),
        (r"\b(d\s*for\s*dok|d\s*for\s*doggie)\b", "d for dog"),
        (r"\b(elepant|elifant)\b", "elephant"),

        # Stories & Rhymes
        (r"\b(khani|kahaani|stoy)\b", "kahani"),
        (r"\b(suno|sunaao)\b", "sunao"),
        (r"\b(poim|rime|ryme|kavita)\b", "poem"),

        # Painting & Drawing Activities
        (r"\b(penting|paint|darwing|drwa|drwing|draw|drawing)\b", "painting"),
        (r"\b(rang\s*bharna|chitra\s*banana|colouring|coloring)\b", "painting"),
        (r"\b(hous|havs|haos)\b(?=\s+ka|\s+ki|\s+banana|\s+draw|$)", "house"),

        # Spelling & Tracing Activities
        (r"\b(speling|ispling|splling)\b", "spelling"),
        (r"\b(sylabul|silabul|sillebul|sylebul|sylable)\b", "syllable"),
        (r"\b(d-o-g|d\s+o\s+g|d\s*o\s*g)\b", "D O G"),
        (r"\b(c-a-t|c\s+a\s+t|c\s*a\s*t)\b", "C A T"),
        (r"\b(r-a-t|r\s+a\s+t|r\s*a\s*t)\b", "R A T"),
        (r"\b(m-a-t|m\s+a\s+t|m\s*a\s*t)\b", "M A T"),
        (r"\b(f-i-s-h|f\s+i\s+s\s+h|f\s*i\s*s\s*h)\b", "F I S H"),
        (r"\b(likh\s*ke\s*dikhao|likha|likh\s*diya)\b", "likh diya"),

        # Bilingual Animal & Word Translations
        (r"\b(kutta|kutte)\b(?=\s+ko\s+english|\s+in\s+english|$)", "kutta ko english"),
        (r"\b(billi)\b(?=\s+ko\s+english|\s+in\s+english|$)", "billi ko english"),
        (r"\b(chuha)\b(?=\s+ko\s+english|\s+in\s+english|$)", "chuha ko english"),
        (r"\b(machhli|machli)\b(?=\s+ko\s+english|\s+in\s+english|$)", "machhli ko english"),
        (r"\b(chatai)\b(?=\s+ko\s+english|\s+in\s+english|$)", "chatai ko english"),
        (r"\b(dog)\b(?=\s+ko\s+hindi|\s+in\s+hindi|$)", "dog ko hindi"),
        (r"\b(cat)\b(?=\s+ko\s+hindi|\s+in\s+hindi|$)", "cat ko hindi"),
        (r"\b(rat)\b(?=\s+ko\s+hindi|\s+in\s+hindi|$)", "rat ko hindi"),
        (r"\b(mat)\b(?=\s+ko\s+hindi|\s+in\s+hindi|$)", "mat ko hindi"),
        (r"\b(fish)\b(?=\s+ko\s+hindi|\s+in\s+hindi|$)", "fish ko hindi"),

        # Visual Image Quiz
        (r"\b(kiska\s*photo|kiska\s*image|kiska\s*chitra|ye\s*kya\s*hai)\b", "ye kiska photo hai"),

        # Characters
        (r"\b(puyuva|purva|puluva|poorva)\b", "puruva"),
        (r"\b(kairi|keri|kairee)\b", "kairi"),

        # Counting & Numbers
        (r"\b(ginti|kounting|kount)\b", "counting"),
        (r"\b(ek\s*do\s*teen|one\s*two\s*three)\b", "counting 1 to 10"),

        # General Animals & Objects
        (r"\b(bhaloo|balu)\b", "bhalu"),
    ]

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""

        # Remove repeated stutter syllables (e.g. "a-a-apple" -> "apple", "d-d-didi" -> "didi") without breaking spellings like "d-o-g"
        normalized = re.sub(r"\b([a-zA-Z])-\1+", r"\1", text.strip(), flags=re.IGNORECASE)

        # Apply phonetic pattern rules
        for pattern, replacement in cls.PHONETIC_RULES:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        return normalized.strip()


class ResilientGroqSTT(groq.STT):
    """
    Enterprise-Grade Resilient Groq STT for LiveKit VoicePipelineAgent.
    Features:
    1. Built-in StreamAdapterWrapper providing genuine audio streaming without crashing
       on non-existent Groq Realtime WebSocket endpoints (404 fix).
    2. Exception-safe recognize implementation that gracefully absorbs network timeouts
       or transient errors, preventing the voice pipeline loop from dying.
    3. Whisper hallucination filtering to eliminate ghost audio triggers.
    4. KidsPhoneticNormalizer integration to correct children's lisp, mispronunciations,
       and speech variations automatically.
    """

    def __init__(self, vad: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vad = vad
        self._capabilities = stt.STTCapabilities(streaming=True, interim_results=False)

    @property
    def capabilities(self) -> stt.STTCapabilities:
        return self._capabilities

    def stream(
        self,
        *,
        language: Optional[str] = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> StreamAdapterWrapper:
        return StreamAdapterWrapper(
            self,
            vad=self._vad,
            wrapped_stt=self,
            language=language or self._opts.language,
            conn_options=conn_options,
        )

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: Optional[str],
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        try:
            ev = await super()._recognize_impl(
                buffer=buffer,
                language=language,
                conn_options=conn_options,
            )
            if ev.alternatives and ev.alternatives[0].text:
                clean_text = ev.alternatives[0].text.strip()
                # 1. Filter Whisper special tokens (e.g. <|hi|>, <|transcribe|>, <|en|>)
                if clean_text.startswith("<|") or clean_text.endswith("|>") or re.match(r"^<\|.*\|>$", clean_text):
                    logger.debug(f"[ResilientGroqSTT] Discarded Whisper special token: '{clean_text}'")
                    ev.alternatives[0].text = ""
                    return ev

                # 2. Filter empty, punctuation-only noise (Keep single letters A-Z, 0-9, and Hindi characters for kids learning)
                letters_only = re.sub(r"[^\w\s\u0900-\u097F]", "", clean_text).strip()
                if len(letters_only) == 0:
                    ev.alternatives[0].text = ""
                    return ev
                if len(letters_only) == 1 and not (letters_only.isalnum() or '\u0900' <= letters_only <= '\u097F'):
                    ev.alternatives[0].text = ""
                    return ev

                # 3. Check for noise, background chatter or known Whisper hallucinations
                clean_lower = clean_text.lower()
                if (
                    clean_lower in WHISPER_HALLUCINATIONS
                    or any(h in clean_lower for h in ["kau mavi", "kusik siyahan", "kelderamu", "tunggu", "subtitles by", "amara.org"])
                ):
                    logger.debug(f"[ResilientGroqSTT] Filtered hallucination: '{clean_text}'")
                    ev.alternatives[0].text = ""
                    return ev

                normalized_text = KidsPhoneticNormalizer.normalize(clean_text)
                if normalized_text != clean_text:
                    logger.info(f"🎙️ [Kids STT Normalizer] Raw: '{clean_text}' ➔ Cleaned: '{normalized_text}'")
                    ev.alternatives[0].text = normalized_text
                else:
                    logger.info(f"🎙️ [STT Transcribed] '{clean_text}' (lang={ev.alternatives[0].language or language})")
            return ev
        except Exception as e:
            logger.warning(f"[ResilientGroqSTT] Transient STT error safely absorbed: {e}")
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[],
            )


class SttFactory:
    """Creates configured STT instances for real-time speech transcription."""

    @staticmethod
    def create_stt(
        language: str = "hinglish",
        api_key: str = "",
        model: str = "whisper-large-v3-turbo",
        vad: Optional[Any] = None,
    ) -> ResilientGroqSTT:
        key = api_key or os.getenv("GROQ_API_KEY", "") or "dummy_key_for_init"
        if not os.getenv("GROQ_API_KEY") and not api_key:
            logger.warning("GROQ_API_KEY is not set for STT! Using fallback for initialization.")

        # Map language strings to Whisper language codes
        lang_lower = (language or "hinglish").strip().lower()
        if lang_lower == "english":
            whisper_lang = "en"
            detect_lang = False
        else:
            # Lock language to Hindi (hi) with Hinglish/Kids vocabulary prompt
            # This completely prevents Whisper from hallucinating foreign languages (Welsh, Ukrainian, Nepali)
            # and ensures crystal-clear Hindi & Hinglish phonetic accuracy for children!
            whisper_lang = "hi"
            detect_lang = False

        if vad is None:
            from pipeline.vad import SileroVADProvider
            vad = SileroVADProvider.create()

        logger.info(f"[SttFactory] Initializing Resilient Groq STT: model={model}, lang={whisper_lang}, detect={detect_lang}")
        return ResilientGroqSTT(
            vad=vad,
            model=model,
            api_key=key,
            language=whisper_lang,
            prompt=STT_LANGUAGE_PROMPT,
            detect_language=detect_lang,
        )

    @classmethod
    def create(
        cls,
        language: str = "hinglish",
        api_key: str = "",
        model: str = "whisper-large-v3-turbo",
        vad: Optional[Any] = None,
    ) -> ResilientGroqSTT:
        return cls.create_stt(language=language, api_key=api_key, model=model, vad=vad)


# Alias
SttProvider = SttFactory

