"""
tests/test_modular_architecture.py - Comprehensive Verification for Enterprise AI Calling Architecture.
Tests:
1. toolchain/ package (Common Tools + Persona Mixins + Disconnect Flags)
2. pipeline/ package (VAD calibration, STT setup, Multi-Engine TTS, Builder)
3. orchestrator/ package (LPU routing, MemoryManager, StructuredExtractor)
4. events/ package (CallEventSession, CaptionBroadcaster, EventDispatcher)
5. Root shims compatibility
"""

import os
import sys
import unittest

# Add ai-agent to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestModularArchitecture(unittest.TestCase):
    def setUp(self):
        import asyncio
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
    def test_01_toolchain_imports_and_registry(self):
        from toolchain import ToolRegistry, SessionData
        from toolchain.base import BaseVoiceTool

        session = SessionData(call_id="call_test_123", caller_id="user_456")
        self.assertFalse(session.disconnect_pending)

        # Test Cab Booking
        cab_ctx = ToolRegistry.create_context(persona_id="cab_booking", call_session_id="call_1", user_id="user_1")
        self.assertIsNotNone(cab_ctx)
        self.assertTrue(hasattr(cab_ctx, "book_cab_ride"))
        self.assertTrue(hasattr(cab_ctx, "disconnect_call"))
        self.assertTrue(hasattr(cab_ctx, "check_wallet_balance"))

        # Test HR Job
        hr_ctx = ToolRegistry.create_context(persona_id="hr_job", call_session_id="call_2", user_id="user_2")
        self.assertTrue(hasattr(hr_ctx, "record_screening_answer"))
        self.assertTrue(hasattr(hr_ctx, "disconnect_call"))

        # Test Companion
        comp_ctx = ToolRegistry.create_context(persona_id="companion", call_session_id="call_3", user_id="user_3")
        self.assertTrue(hasattr(comp_ctx, "suggest_relaxation_activity"))
        self.assertTrue(hasattr(comp_ctx, "disconnect_call"))

    def test_02_pipeline_vad_stt_tts_builder(self):
        from pipeline import (
            CallingPipelineConfig,
            SileroVADProvider,
            SttProvider,
            TtsFactory,
            VoicePipelineBuilder,
            AudioRecorder,
        )
        from livekit.agents import llm

        cfg = CallingPipelineConfig()
        self.assertGreater(cfg.vad_threshold, 0.3)
        self.assertGreater(cfg.vad_min_endpointing_delay, 0.2)
        self.assertGreater(cfg.interrupt_speech_duration, 0.1)

        vad = SileroVADProvider.create(config=cfg)
        self.assertIsNotNone(vad)

        stt = SttProvider.create(language="hinglish")
        self.assertIsNotNone(stt)

        tts_engine = TtsFactory.create(provider="edge", voice="hi-IN-SwaraNeural")
        self.assertIsNotNone(tts_engine)

        chat_ctx = llm.ChatContext()
        chat_ctx.append(role="system", text="You are a test assistant.")

        # Test VoicePipelineBuilder assembling with dummy llm
        from livekit.plugins import groq
        dummy_llm = groq.LLM(model="qwen/qwen3.8-27b", api_key="dummy_key_for_init")
        agent = VoicePipelineBuilder.build(
            llm_instance=dummy_llm,
            chat_ctx=chat_ctx,
            tts_provider="edge",
            config=cfg,
        )
        self.assertIsNotNone(agent)

    def test_03_orchestrator(self):
        from orchestrator import (
            LlmOrchestrator,
            LlmRouter,
            RouteConfig,
            MemoryManager,
            StructuredExtractor,
        )

        route = LlmRouter.get_voice_route()
        self.assertIsInstance(route, RouteConfig)
        self.assertEqual(route.provider, "groq")
        self.assertIn(route.model, [LlmRouter.FAST_VOICE_MODEL, LlmRouter.DEFAULT_VOICE_MODEL])

        failover_route = LlmRouter.get_voice_route(failover=True)
        self.assertEqual(failover_route.model, LlmRouter.FALLBACK_VOICE_MODEL)

        orch = LlmOrchestrator(api_key="test_key")
        self.assertEqual(orch.active_provider, "groq")

        filler = LlmOrchestrator.get_thinking_filler(language="hinglish")
        self.assertTrue(len(filler) > 3)

        mem = MemoryManager(backend_api_url="http://localhost:5063")
        self.assertEqual(mem.backend_api_url, "http://localhost:5063")

    def test_04_events_and_session(self):
        from events import CallEventSession, CaptionBroadcaster, EventDispatcher

        session = CallEventSession(
            call_id="call_999",
            caller_id="caller_888",
            clean_caller_id="888",
            persona_id="cab_booking",
            language="hinglish",
            gender="female",
        )
        self.assertEqual(len(session.turns), 0)
        session.append_turn("user", "Hello there")
        session.append_turn("assistant", "Hi, how can I help you today?")
        self.assertEqual(len(session.turns), 2)
        self.assertEqual(session.turns[0]["role"], "user")
        self.assertEqual(session.turns[1]["role"], "assistant")

    def test_05_modular_architecture_integrity(self):
        from pipeline.config import CallingPipelineConfig
        from pipeline.tts import EdgeTTS, create_tts_engine
        from toolchain import ToolRegistry
        from orchestrator import LlmOrchestrator, LlmRouter

        cfg = CallingPipelineConfig()
        self.assertTrue(hasattr(cfg, "vad_threshold"))
        self.assertTrue(callable(create_tts_engine))
        self.assertTrue(hasattr(ToolRegistry, "create_context"))
        self.assertTrue(hasattr(LlmOrchestrator, "get_livekit_llm"))


if __name__ == "__main__":
    unittest.main()
