"""
logger.py - Enterprise Structured Tracing & Logging System for AI Voice Agent.
Provides:
1. Rotating central log file: ai-agent/logs/agent.log (10MB x 5 backups).
2. Per-call trace loggers: ai-agent/logs/calls/call_{call_id}.log.
3. Console logging with UTF-8 support for Hindi/Hinglish text on Windows.
4. Structured helper methods for tracing STT, LLM, Tools, VAD, and TTS events.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
CALLS_LOGS_DIR = LOGS_DIR / "calls"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
CALLS_LOGS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 1. Setup root / central agent logger
_central_logger = logging.getLogger("ai_voice_agent")
_central_logger.setLevel(logging.DEBUG)

if not _central_logger.handlers:
    # Console Handler (UTF-8 safe)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(DEFAULT_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    _central_logger.addHandler(console_handler)

    # Rotating Central File Handler (DEBUG level)
    central_file = str(LOGS_DIR / "agent.log")
    file_handler = RotatingFileHandler(
        central_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(DEFAULT_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    _central_logger.addHandler(file_handler)
    # Also attach to root logger so sub-packages (events, pipeline, orchestrator) log to file
    logging.getLogger().addHandler(file_handler)


def get_agent_logger() -> logging.Logger:
    """Returns the central AI Voice Agent logger."""
    return _central_logger


class CallTraceLogger:
    """
    Dedicated per-call trace logger that records every fine-grained event
    (VAD, STT, LLM, Tools, DataChannel, TTS, Disconnect) for a specific call session.
    """

    def __init__(self, call_id: str):
        self.call_id = call_id or "unassigned"
        safe_id = "".join(c for c in self.call_id if c.isalnum() or c in ("-", "_"))
        self.log_file = str(CALLS_LOGS_DIR / f"call_{safe_id}.log")

        self.logger = logging.getLogger(f"call.{safe_id}")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            ch = RotatingFileHandler(
                self.log_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=2,
                encoding="utf-8"
            )
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(logging.Formatter(
                "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S"
            ))
            self.logger.addHandler(ch)

    def log_session_start(self, caller_id: str, persona: str, language: str, gender: str):
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 CALL STARTED: call_id={self.call_id}")
        self.logger.info(f"👤 Caller: {caller_id} | Persona: {persona} | Lang: {language} | Gender: {gender}")
        self.logger.info("=" * 60)

    def log_vad(self, event: str, duration_sec: Optional[float] = None):
        dur = f" (duration={duration_sec:.2f}s)" if duration_sec is not None else ""
        self.logger.debug(f"🎙️ [VAD] {event}{dur}")

    def log_stt(self, text: str, latency_ms: Optional[float] = None, normalized: Optional[str] = None):
        norm_str = f" | Normalized: '{normalized}'" if (normalized and normalized != text) else ""
        lat_str = f" [{latency_ms:.0f}ms]" if latency_ms else ""
        self.logger.info(f"🗣️ [STT Recognized]{lat_str}: '{text}'{norm_str}")

    def log_llm_request(self, model: str, num_messages: int, max_tokens: int):
        self.logger.debug(f"🤖 [LLM Request] Model={model}, Messages={num_messages}, MaxTokens={max_tokens}")

    def log_llm_response(self, text: str, latency_ms: Optional[float] = None, tool_calls: Optional[list] = None):
        lat_str = f" [{latency_ms:.0f}ms]" if latency_ms else ""
        tc_str = f" | ToolCalls: {tool_calls}" if tool_calls else ""
        self.logger.info(f"💡 [LLM Response]{lat_str}: '{text}'{tc_str}")

    def log_tool_invocation(self, tool_name: str, arguments: dict, result: str):
        self.logger.info(f"🛠️ [Tool Executed] {tool_name}({arguments}) -> {result[:120]}...")

    def log_data_packet(self, packet_type: str, component: str, payload_summary: str):
        self.logger.info(f"📱 [DataChannel Sent] type='{packet_type}', comp='{component}': {payload_summary}")

    def log_memory_event(self, action: str, details: str):
        self.logger.info(f"🧠 [Memory] {action}: {details}")

    def log_error(self, component: str, error: Exception):
        self.logger.error(f"❌ [Error in {component}]: {error}", exc_info=True)

    def log_session_end(self, duration_sec: int, reason: str = "normal"):
        self.logger.info("=" * 60)
        self.logger.info(f"🏁 CALL ENDED: duration={duration_sec}s | reason={reason}")
        self.logger.info("=" * 60)


_call_loggers = {}

def get_call_logger(call_id: str) -> CallTraceLogger:
    """Retrieves or creates a dedicated CallTraceLogger for the given call ID."""
    if call_id not in _call_loggers:
        _call_loggers[call_id] = CallTraceLogger(call_id)
    return _call_loggers[call_id]
