"""
pipeline/config.py - Ultra-Low Latency & Natural Turn-Taking Voice Pipeline Configuration.
Calibrated specifically for mobile phone microphones, Indian English, Hindi, and Hinglish.
"""

import os
from pathlib import Path
from dataclasses import dataclass

# Base agent directory: d:\CabBooking\Antigravity\WorkSpaceCallPlan\ai-agent
AI_AGENT_DIR = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = str(AI_AGENT_DIR / "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# =============================================================================
# 1. Silero VAD (Voice Activity Detection) Calibration for Kids & Soft Voices
# =============================================================================
# =============================================================================
# 1. Silero VAD (Voice Activity Detection) Calibration for Kids & Soft Voices
# =============================================================================
# 0.36 threshold sensitive to children's soft, high-pitched vocal cords
VAD_ACTIVATION_THRESHOLD = float(os.getenv("VAD_ACTIVATION_THRESHOLD", "0.36"))
# 0.12s (120ms) captures quick single phonemes & letters ('A', 'B', 'क')
VAD_MIN_SPEECH_DURATION = float(os.getenv("VAD_MIN_SPEECH_DURATION", "0.12"))
# 350ms prefix padding preserves initial soft consonants (p, b, t, k)
VAD_PREFIX_PADDING = float(os.getenv("VAD_PREFIX_PADDING", "0.35"))
# Kids pause while thinking or spelling; 0.90s prevents cutting off children mid-thought
VAD_MIN_SILENCE_DURATION = float(os.getenv("VAD_MIN_SILENCE_DURATION", "0.90"))

# =============================================================================
# 2. Turn-Taking & Endpointing Delays (Natural Turn Transition for Children)
# =============================================================================
ENDPOINTING_MIN_DELAY = float(os.getenv("ENDPOINTING_MIN_DELAY", "0.85"))
ENDPOINTING_MAX_DELAY = float(os.getenv("ENDPOINTING_MAX_DELAY", "1.60"))

# =============================================================================
# 3. Barge-In / Interruption Handling
# =============================================================================
# 0.50s minimum speech duration prevents random ambient noise from killing AI speech
BARGE_IN_SPEECH_DURATION = float(os.getenv("BARGE_IN_SPEECH_DURATION", "0.50"))
# Require at least 1 recognized word before interrupting AI speech playout
BARGE_IN_MIN_WORDS = int(os.getenv("BARGE_IN_MIN_WORDS", "1"))
ALLOW_INTERRUPTIONS = True

# =============================================================================
# 4. LLM & Token Budget Constraints (Hierarchical Long-Call Window)
# =============================================================================
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "150"))
PREEMPTIVE_SYNTHESIS = True
MAX_NESTED_FNC_CALLS = 2
MAX_TURNS_BEFORE_PRUNING = 20  # Trigger rolling summary when turns exceed 20
RETAIN_RECENT_TURNS = 16       # Keep latest 16 messages verbatim with zero text clipping

# =============================================================================
# 5. Whisper STT Kids Language Guidance Prompt (Primes Indian Kids Vocabulary)
# =============================================================================
STT_LANGUAGE_PROMPT = (
    "Namaste Didi! Chalo padhte hain, ABCD, A for Apple, B for Ball, C for Cat, D for Dog, "
    "cat, mat, rat, bat, hat, fan, van, bag, bed, red, hen, pen, ten, pig, big, pin, lip, "
    "dog, fox, box, pot, hot, sun, run, fun, cup, mug, hut, bus, fish, frog, bird, duck, milk, "
    "ball, star, tree, moon, book, door, boat, cake, lion, cow, painting, drawing house ghar, "
    "kutta, billi, chuha, chatai, machhli, spelling D-O-G, C-A-T, R-A-T, M-A-T, F-I-S-H, "
    "A likho, K likho, Hindi padho, अ se anaar, क se kamal, star reward, Hindi Hinglish for kids."
)


@dataclass
class CallingPipelineConfig:
    """Enterprise calling pipeline configuration parameters."""

    vad_threshold: float = VAD_ACTIVATION_THRESHOLD
    vad_min_speech_duration: float = VAD_MIN_SPEECH_DURATION
    vad_prefix_padding: float = VAD_PREFIX_PADDING
    vad_min_silence_duration: float = VAD_MIN_SILENCE_DURATION

    vad_min_endpointing_delay: float = ENDPOINTING_MIN_DELAY
    vad_max_endpointing_delay: float = ENDPOINTING_MAX_DELAY

    interrupt_speech_duration: float = BARGE_IN_SPEECH_DURATION
    interrupt_min_words: int = BARGE_IN_MIN_WORDS
    allow_interruptions: bool = ALLOW_INTERRUPTIONS

    llm_max_tokens: int = LLM_MAX_TOKENS
    preemptive_synthesis: bool = PREEMPTIVE_SYNTHESIS
    max_nested_fnc_calls: int = MAX_NESTED_FNC_CALLS

    stt_prompt: str = STT_LANGUAGE_PROMPT
    recordings_dir: str = RECORDINGS_DIR


pipeline_config = CallingPipelineConfig()
