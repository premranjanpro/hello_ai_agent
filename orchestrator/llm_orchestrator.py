"""
orchestrator/llm_orchestrator.py - Resilient Multi-Engine LLM Orchestrator for Voice.
Provides ultra-fast response times (<400ms TTFT via Groq LPU), automatic failover,
dynamic personalized memory greetings, and filler support.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
import aiohttp
import openai
from livekit.plugins.openai.llm import LLMStream
from livekit.agents import llm
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions
from typing import Union, Literal
from livekit.agents.llm import ToolChoice
from livekit.plugins import groq

from orchestrator.llm_router import LlmRouter

logger = logging.getLogger("orchestrator.llm")


class ResilientGroqLLMStream(LLMStream):
    """Wraps LiveKit LLMStream with pure AI tool-calling workflow and instant quota failover."""

    # Models that fully support function calling on Groq (strictly avoiding non-tool models like compound-mini)
    BACKUP_MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

    async def _run(self) -> None:
        if hasattr(self, "_llm") and hasattr(self._llm, "_opts"):
            if not getattr(self._llm._opts, "max_tokens", None) or self._llm._opts.max_tokens < 250:
                self._llm._opts.max_tokens = 250

        try:
            await super()._run()
        except Exception as e:
            status = getattr(e, "status_code", None)
            logger.warning(f"⚠️ [ResilientGroqLLM] Stream exception: status={status}, msg={e}")

            # Universal resilient recovery: iterate over backup models that support tools
            backup_candidates = [m for m in self.BACKUP_MODELS if m != self._model]
            original_fnc_ctx = getattr(self, "_fnc_ctx", None)

            for target_backup in backup_candidates:
                logger.info(f"🔄 [ResilientGroqLLM] Switching to failover model '{target_backup}' with tools intact...")
                self._model = target_backup
                self._fnc_ctx = original_fnc_ctx
                if hasattr(self, "_llm") and hasattr(self._llm, "_opts"):
                    self._llm._opts.max_tokens = 250

                if hasattr(self, "_chat_ctx") and self._chat_ctx and len(self._chat_ctx.messages) > 2:
                    sys_msgs = [m for m in self._chat_ctx.messages if getattr(m, "role", "") == "system"]
                    user_or_ai = [m for m in self._chat_ctx.messages if getattr(m, "role", "") in ("user", "assistant")]
                    clean_history = []
                    for msg in user_or_ai[-4:]:
                        c = getattr(msg, "content", "")
                        clean_history.append(llm.ChatMessage(role=msg.role, content=c if isinstance(c, str) else str(c or "")))
                    self._chat_ctx.messages.clear()
                    self._chat_ctx.messages.extend(sys_msgs)
                    self._chat_ctx.messages.extend(clean_history)

                try:
                    await super()._run()
                    return
                except Exception as retry_err:
                    logger.warning(f"⚠️ [ResilientGroqLLM] Backup model '{target_backup}' error: {retry_err}")
                    continue

            # Ultimate fallback only if all models failed: text-only recovery
            logger.warning("⚠️ [ResilientGroqLLM] All tool-enabled backup models exhausted; trying text-only fallback...")
            self._fnc_ctx = None
            for target_backup in self.BACKUP_MODELS:
                self._model = target_backup
                try:
                    await super()._run()
                    return
                except Exception as final_err:
                    logger.error(f"❌ [ResilientGroqLLM] Final model '{target_backup}' text fallback failed: {final_err}")
                    continue


class ResilientGroqLLM(groq.LLM):
    """Groq LLM for LiveKit VoicePipelineAgent with strict pre-flight token guard and automatic failover."""

    def __init__(self, *, model: str = "qwen/qwen3.8-27b", max_tokens: int = 250, **kwargs):
        m = model or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        super().__init__(model=m, max_tokens=max_tokens or 250, **kwargs)
        self._opts.max_tokens = max_tokens or 250

    # Whitelist of top voice tools to keep token footprint strictly under token budget
    VOICE_CORE_TOOLS = {
        "switch_active_character",
        "show_alphabet_flashcard",
        "narrate_story",
        "recite_rhyme",
        "teach_hindi_varnamala",
        "teach_maths_table",
        "award_stars_and_celebrate",
        "play_tic_tac_toe",
        "play_memory_game",
        "start_visual_image_quiz",
        "evaluate_visual_quiz_answer",
        "read_quiz_options_aloud",
        "explore_india_place",
        "teach_good_habit",
        "disconnect_call",
    }

    @staticmethod
    def _enforce_strict_token_budget(
        chat_ctx: llm.ChatContext,
        fnc_ctx: Optional[llm.FunctionContext] = None,
        max_recent_turns: int = 12,
    ) -> None:
        """
        Bounds the LLM chat context and tool definitions before sending to Groq
        while strictly preserving tool instructions, persona rules, and tool call pairs:
        - Allows full System Prompt up to 6,000 chars (~1,400 tokens)
        - Retains up to 12 recent conversation messages
        - Never orphans tool calls or tool responses (prevents HTTP 400 errors)
        - Prunes function tools to high-impact voice subset to keep prompt < 1,500 tokens
        """
        if not chat_ctx or not hasattr(chat_ctx, "messages") or not chat_ctx.messages:
            return

        sys_messages = [m for m in chat_ctx.messages if getattr(m, "role", "") == "system"]
        conversation = [m for m in chat_ctx.messages if getattr(m, "role", "") != "system"]

        # 1. System Prompt Guard: Allow full persona up to 6,000 chars
        for sm in sys_messages:
            c = getattr(sm, "content", "")
            if isinstance(c, str) and len(c) > 6000:
                logger.info(f"🛡️ [StrictTokenGuard] Clamping oversized system prompt: {len(c)} chars -> 6000 chars")
                sm.content = c[:6000]

        # 2. History Guard: Keep recent turns while safeguarding tool message integrity
        if len(conversation) > max_recent_turns:
            conversation = conversation[-max_recent_turns:]
            # Ensure the first message in conversation isn't an orphaned tool result
            while conversation and getattr(conversation[0], "role", "") == "tool":
                conversation.pop(0)

        chat_ctx.messages.clear()
        chat_ctx.messages.extend(sys_messages)
        chat_ctx.messages.extend(conversation)

        # 3. Toolchain Schema Guard: Prune non-voice tools to keep request within Groq 7,000 ITPM limit
        if fnc_ctx and hasattr(fnc_ctx, "_fncs") and isinstance(fnc_ctx._fncs, dict):
            if len(fnc_ctx._fncs) > len(ResilientGroqLLM.VOICE_CORE_TOOLS):
                filtered = {
                    k: v for k, v in fnc_ctx._fncs.items()
                    if k in ResilientGroqLLM.VOICE_CORE_TOOLS
                }
                if filtered:
                    fnc_ctx._fncs = filtered
                    logger.debug(f"🛡️ [StrictTokenGuard] Pruned toolchain: to {len(filtered)} tools")

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        fnc_ctx: llm.FunctionContext | None = None,
        temperature: float | None = None,
        n: int | None = 1,
        parallel_tool_calls: bool | None = None,
        tool_choice: Union[ToolChoice, Literal["auto", "required", "none"]] | None = None,
    ) -> ResilientGroqLLMStream:
        # Pre-Flight Token Guard: Hard-bounds chat context & tools so Groq quota is NEVER breached
        self._enforce_strict_token_budget(chat_ctx, fnc_ctx=fnc_ctx)

        return ResilientGroqLLMStream(
            self,
            client=self._client,
            model=self._opts.model,
            user=self._opts.user,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
            conn_options=conn_options or DEFAULT_API_CONNECT_OPTIONS,
            n=n,
            temperature=temperature if temperature is not None else self._opts.temperature,
            parallel_tool_calls=parallel_tool_calls if parallel_tool_calls is not None else self._opts.parallel_tool_calls,
            tool_choice=tool_choice if tool_choice is not None else self._opts.tool_choice,
        )


class LlmOrchestrator:
    """Orchestrates real-time conversational LLM calls across providers with failover protection."""

    def __init__(self, default_model: Optional[str] = None, api_key: str = ""):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.default_model = default_model or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self.active_provider = "groq"
        self.active_model = self.default_model
        self.fallback_model = "openai/gpt-oss-120b"

    def get_livekit_llm(self, temperature: float = 0.40):
        """Creates the optimal LiveKit LLM instance with configured speed settings and bounded tokens."""
        route = LlmRouter.get_voice_route(failover=(self.active_model == self.fallback_model and self.default_model != self.fallback_model))
        logger.info(f"[LlmOrchestrator] Initializing Voice LLM: {route.model} (temp={temperature}, max_tokens={route.max_tokens})")
        return ResilientGroqLLM(
            model=route.model,
            temperature=temperature,
            api_key=self.api_key,
            max_tokens=route.max_tokens,
        )

    async def extract_caller_name(self, turns: list) -> str:
        """Fast regex and semantic extraction of caller/child name if mentioned in conversation."""
        if not turns:
            return ""

        import re
        user_texts = [t.get("content", "") for t in turns if t.get("role") in ["user", "caller"] and t.get("content")]
        combined = " ".join(user_texts)

        patterns = [
            r"(?:mera\s+naam|naam\s+hai|mujhe\s+kehte\s+hain|main\s+hoon)\s+([a-zA-Z\u0900-\u097F]{2,20})",
            r"(?:my\s+name\s+is|i\s+am|call\s+me)\s+([a-zA-Z]{2,20})",
            r"(?:bache\s+ka\s+naam|bacha\s+hai|gudiya\s+ka\s+naam|bete\s+ka\s+naam)\s+([a-zA-Z\u0900-\u097F]{2,20})",
        ]
        for pat in patterns:
            m = re.search(pat, combined, re.IGNORECASE)
            if m:
                found = m.group(1).strip().capitalize()
                if found.lower() not in ["nahi", "kya", "batao", "sunao", "hello", "theek", "achha", "yes", "no", "contact", "user"]:
                    logger.info(f"👤 [LlmOrchestrator] Extracted caller/child name: '{found}'")
                    return found

        return ""

    async def generate_personalized_greeting(
        self,
        persona_name: str,
        language: str = "hinglish",
        memory_data: dict = None,
        default_greeting: str = "",
        persona_role: str = "",
        user_name: str = "",
        is_kids_persona: bool = False,
    ) -> tuple[str, str]:
        """
        Generates an ultra-intelligent, name-aware opening greeting:
        - When caller/child name is known, greets them warmly and personally by name!
        - Mode 1: First-Time User -> Warm introduction with name ('Arrey waah Kabir! Hello champ!').
        - Mode 2: Returning after >= 3 Days -> Welcome back acknowledging name and gap.
        - Mode 3: Recent Call (< 48h) -> Topic follow-up with name.
        - Mode 4: Casual Variety -> Friendly varied greeting with name.
        Returns: (spoken_greeting, opening_style)
        """
        import random

        clean_name = (
            user_name
            or (memory_data.get("userName") if memory_data else "")
            or (memory_data.get("childName") if memory_data else "")
            or ""
        ).strip()
        if clean_name.lower() in ["contact", "user", "admin", "null", "none", "unknown", ""]:
            clean_name = ""

        import datetime
        now = datetime.datetime.now()
        cur_hour = now.hour
        is_morning = 6 <= cur_hour < 12
        is_afternoon = 12 <= cur_hour < 16
        is_evening = 16 <= cur_hour < 19
        is_night = cur_hour >= 19 or cur_hour < 6

        if not memory_data or not isinstance(memory_data, dict):
            if clean_name:
                if is_kids_persona:
                    if is_morning:
                        return f"Good morning {clean_name}! Main hoon {persona_name}! Kya subah brush kar liya champ?", "morning_welcome"
                    elif is_afternoon:
                        return f"Hello {clean_name}! Main hoon {persona_name}! Aaj school me kya naya seekha?", "afternoon_welcome"
                    elif is_evening:
                        return f"Arrey waah {clean_name}! Shaam ko dosto ke sath khelne gaye the?", "evening_welcome"
                    else:
                        return f"Good evening {clean_name}! Homework ho gaya champ? Aao koi pyari kahani sunein!", "night_welcome"
                else:
                    return f"Namaste {clean_name} ji! Main {persona_name} bol rahi hoon. Kahiye, aaj main aapki kya madad kar sakti hoon?", "name_welcome"
            if is_kids_persona:
                return "Yaaay! Hello superstar! Main hoon aapki pyari Puruva AI! Aaj kya mazedaar seekhein ya khelein?", "kids_welcome"
            return default_greeting, "default"

        total_calls = memory_data.get("totalCalls", 0)
        has_history = memory_data.get("hasHistory", False)
        days_since = memory_data.get("daysSinceLastCall")
        last_topic = (memory_data.get("lastTopic") or "").strip()
        last_statement = (memory_data.get("lastUserStatement") or "").strip()
        memory_summary = (memory_data.get("memorySummary") or "").strip()
        last_style = memory_data.get("lastOpeningStyle", "default")

        # 1. New user or first call
        if total_calls == 0 or not has_history:
            if clean_name:
                if is_kids_persona:
                    if is_morning:
                        return f"Good morning {clean_name}! Main hoon {persona_name}! Kya brush kar liya champ?", "new_user_morning"
                    elif is_afternoon:
                        return f"Hello {clean_name}! Main hoon {persona_name}! Aaj school me kya naya seekha?", "new_user_afternoon"
                    elif is_evening:
                        return f"Arrey waah {clean_name}! Shaam ko khelne gaye the? Main hoon {persona_name}!", "new_user_evening"
                    else:
                        return f"Hello {clean_name}! Main hoon {persona_name}! Aao ek mazedaar bedtime story sunein!", "new_user_night"
                else:
                    return f"Namaste {clean_name} ji! Main {persona_name} bol rahi hoon. Kahiye, aaj main aapki kya madad kar sakti hoon?", "name_welcome"
            return default_greeting, "new_user"

        # 2. Returning after >= 3 days gap
        if days_since is not None and days_since >= 3:
            if clean_name:
                if is_kids_persona:
                    gap_options = [
                        (f"Arrey waah {clean_name}! Welcome back champ! Kaafi din baad baat ho rahi hai, kaise ho aap?", "gap_reconnect_1"),
                        (f"Hello {clean_name}! Main to aapka hi intezaar kar rahi thi! Kaise ho champ?", "gap_reconnect_2"),
                    ]
                    return random.choice(gap_options)
                else:
                    return f"Namaste {clean_name} ji! Kaafi din baad baat ho rahi hai, sab kaisa chal raha hai?", "gap_reconnect"
            target_style = "gap_reconnect"
            scenario_guidance = (
                f"The user is calling back after {int(days_since)} days gap. "
                "Greet them warmly acknowledging it has been a few days since you last spoke. "
                "Keep it under 10-14 words."
            )
        # 3. Recent caller (< 48 hours) with an exit statement or topic
        elif (last_topic or last_statement) and (last_style != "topic_followup"):
            if clean_name:
                if is_kids_persona:
                    return f"Hello {clean_name}! Padhai ho gayi aapki? Aao aaj kuch naya seekhein!", "topic_followup"
                else:
                    return f"Hello {clean_name} ji! Kahiye, pichla kaam kaisa raha?", "topic_followup"
            target_style = "topic_followup"
            scenario_guidance = (
                f"The user spoke with you recently. At the end of the last call, user discussed: '{last_statement or last_topic}'. "
                "Generate a natural, super concise opening follow-up asking how that went. "
                "Keep it friendly, natural, and under 8-12 words."
            )
        # 4. Casual & Time-Aware variety to prevent repetitive irritation
        else:
            if clean_name:
                if is_kids_persona:
                    # Dynamic time-of-day contextual options (Anti-Irritation)
                    if is_morning:
                        casual_kids = [
                            (f"Good morning {clean_name}! Kya subah brush kar liya champ?", "time_brush"),
                            (f"Hello {clean_name}! Good morning! Aaj breakfast me kya khaya?", "time_breakfast"),
                            (f"Hi {clean_name}! Main hoon {persona_name}! Chalo subah ki mast padhai shuru karein!", "time_morn_short"),
                            (f"Waah {clean_name}! Aaj hum kya khelein - Piano ya ABC phonics?", "time_morn_game"),
                        ]
                    elif is_afternoon:
                        casual_kids = [
                            (f"Hello {clean_name}! Aaj school gaye the? School me kya maza aaya?", "time_school"),
                            (f"Hi champ {clean_name}! Lunch kar liya? Aao ab thodi der masti karein!", "time_lunch"),
                            (f"Arrey {clean_name}! Chalo Piano ya koi pyari kahani sunein!", "time_afternoon_play"),
                        ]
                    elif is_evening:
                        casual_kids = [
                            (f"Arrey waah {clean_name}! Shaam ko dosto ke sath park me khelne gaye the?", "time_evening_play"),
                            (f"Hello {clean_name}! Shaam ho gayi champ! Chalo mast cartoon video dekhein!", "time_evening_video"),
                            (f"Haan ji {clean_name}, boliye! Aaj kya naya seekhna hai?", "time_evening_chat"),
                        ]
                    else: # Night
                        casual_kids = [
                            (f"Good evening {clean_name}! Homework kar liya champ? Ya koi pyari kahani sunein?", "time_homework"),
                            (f"Hello {clean_name}! Dinner ho gaya? Chalo sone se pehle ek mast bedtime story sunte hain!", "time_dinner"),
                            (f"Haan ji {clean_name}, boliye! Main to aapki pyari {persona_name} hoon!", "time_night_chat"),
                        ]

                    filtered = [opt for opt in casual_kids if opt[1] != last_style]
                    choice = random.choice(filtered if filtered else casual_kids)
                    return choice[0], choice[1]
                else:
                    casual_adults = [
                        (f"Namaste {clean_name} ji! Kahiye, aaj kya help karoon?", "casual_a1"),
                        (f"Haan ji {clean_name} ji, boliye! Kaise hain aap?", "casual_a2"),
                        (f"Hello {clean_name} ji! Bataiye, kya chal raha hai?", "casual_a3"),
                        (f"Namaste {clean_name} ji! Sun rahi hoon, boliye!", "casual_a4"),
                    ]
                    filtered = [opt for opt in casual_adults if opt[1] != last_style]
                    choice = random.choice(filtered if filtered else casual_adults)
                    return choice[0], choice[1]

            casual_options = [
                ("Haan ji, boliye! Kaise hain aap?", "casual_1"),
                ("Hello! Kahiye, aaj kya help karoon?", "casual_2"),
                ("Hey! Bataiye, kya chal raha hai?", "casual_3"),
                ("Haan ji, sun rahi hoon, boliye!", "casual_4"),
            ]
            filtered = [opt for opt in casual_options if opt[1] != last_style]
            choice = random.choice(filtered if filtered else casual_options)
            return choice[0], choice[1]

        if not self.api_key:
            return default_greeting, "default"

        prompt = (
            f"You are {persona_name} ({persona_role}), a friendly AI companion on a voice call.\n"
            f"SCENARIO: {scenario_guidance}\n"
            f"Past memory: {memory_summary[:120]}\n"
            f"Caller Name: '{clean_name}' (If provided, you MUST greet them by their name).\n"
            f"Language: {language} (natural Hindi/Hinglish).\n"
            "TASK: Generate ONLY the 1-sentence opening spoken line (under 12 words). "
            "No quotation marks, no emojis, no asterisks:"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.active_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 35,
            "temperature": 0.5,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=1.2),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        greeting = data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
                        if greeting and len(greeting) > 5:
                            logger.info(f"[LlmOrchestrator] Intelligent ({target_style}) greeting generated: '{greeting}'")
                            return greeting, target_style
        except Exception as e:
            logger.warning(f"[LlmOrchestrator] Dynamic greeting error: {e}")

        return default_greeting, "fallback"

    async def extract_closing_intent_and_topic(self, turns: list) -> tuple[str, str]:
        """
        Analyzes the last few user turns to extract:
        1. What the user stated they were about to do right before hanging up (e.g. 'Going to study physics', 'Going to airport').
        2. The exact final user utterance.
        Returns: (last_topic, last_user_statement)
        """
        user_turns = [t.get("content", "") for t in turns if t.get("role") in ["user", "caller"] and t.get("content")]
        if not user_turns:
            return "", ""

        last_statement = user_turns[-1].strip()
        if len(user_turns) < 2 or not self.api_key:
            return f"Discussed: {last_statement[:60]}", last_statement

        recent_dialogue = "\n".join([f"{t.get('role', 'speaker')}: {t.get('content', '')}" for t in turns[-6:]])
        prompt = (
            "Analyze the end of this voice conversation transcript. Identify what activity the user mentioned they are doing, "
            "planning to do, or where they are going (e.g., 'going to study', 'eating food', 'booking a cab', 'office meeting').\n"
            f"{recent_dialogue}\n\n"
            "Output ONLY a 3 to 6 word summary of what the user is doing next (e.g. 'Going to study physics' or 'Heading to airport'). "
            "If no specific future activity is mentioned, summarize their main topic:"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.active_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 25,
            "temperature": 0.2,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=2.0),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        topic = data["choices"][0]["message"]["content"].strip().strip('"')
                        return topic, last_statement
        except Exception as e:
            logger.warning(f"[LlmOrchestrator] Failed to extract closing topic: {e}")

        return f"Discussed: {last_statement[:50]}", last_statement

    async def extract_compact_memory(self, turns: list) -> str:
        """Extracts a precise, 1-sentence memory statement focusing on names, preferences, and key goals."""
        if not turns or len(turns) < 2 or not self.api_key:
            user_turns = [t["content"] for t in turns if t.get("role") == "user"]
            return f"User discussed: {'; '.join(user_turns[-2:])}" if user_turns else ""

        dialogue = "\n".join([f"{t.get('role', 'speaker')}: {t.get('content', '')}" for t in turns[-8:]])
        prompt = (
            "Analyze this voice conversation transcript. Extract a precise 1-sentence memory summary of what the user wants, "
            "their personal detail (like name, destination, job, preference), or current progress.\n\n"
            f"{dialogue}\n\n"
            "Output ONLY the 1-sentence memory statement, nothing else:"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.active_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 65,
            "temperature": 0.2,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=3.0),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip().strip('"')
        except Exception as e:
            logger.warning(f"[LlmOrchestrator] Memory extraction error: {e}")

        user_turns = [t["content"] for t in turns if t.get("role") == "user"]
        return f"User discussed: {'; '.join(user_turns[-2:])}" if user_turns else ""

    @staticmethod
    def extract_caller_name_from_text(text: str) -> str:
        """Fast regex extraction of caller or child name from user spoken text."""
        import re
        if not text:
            return ""
        
        stopwords = {
            "nahi", "nahin", "theek", "acha", "achha", "bol", "yahan", "sun", "kuch", "hai", 
            "batao", "karo", "call", "agent", "user", "kid", "bacha", "bachhe", "sir", "madam", 
            "didi", "bhaiya", "hello", "hi", "ok", "okay", "yes", "no", "main", "mera", "meri", 
            "kya", "kaise", "kab", "kahan", "kaun", "hum", "aap", "tum", "busy", "free"
        }

        patterns = [
            r"(?:mera\s+naam|my\s+name\s+is)\s+([A-Za-z\u0900-\u097F]{2,20})",
            r"(?:mujhe|call\s+me)\s+([A-Za-z\u0900-\u097F]{2,20})\s+(?:bulao|kehte|bulate)",
            r"(?:main\s+hoon|i\s+am|this\s+is)\s+([A-Za-z\u0900-\u097F]{2,20})",
            r"([A-Za-z\u0900-\u097F]{2,20})\s+(?:naam\s+hai\s+mera|bol\s+raha\s+hoon|bol\s+rahi\s+hoon)",
        ]

        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if cand.lower() not in stopwords and len(cand) >= 2:
                    return cand.capitalize()

        return ""

    async def extract_caller_name(self, turns: list) -> str:
        """Extracts user/child name from conversation turns using regex + LLM fallback."""
        if not turns:
            return ""

        # 1. Fast regex scan across user turns
        for t in turns:
            if t.get("role") in ["user", "caller"]:
                text = t.get("content", "")
                found = self.extract_caller_name_from_text(text)
                if found:
                    return found

        # 2. LLM fallback if user stated name ambiguously
        if self.api_key and len(turns) >= 2:
            dialogue = "\n".join([f"{t.get('role', 'speaker')}: {t.get('content', '')}" for t in turns[:8]])
            prompt = (
                "From this conversation opening, did the caller/child state their name? "
                "If yes, return ONLY the single first name (e.g. 'Kabir', 'Aarav', 'Priya'). "
                "If no name was mentioned, return 'NONE'.\n\n"
                f"{dialogue}"
            )
            try:
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                body = {
                    "model": self.active_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0.0,
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=2.0),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            ans = data["choices"][0]["message"]["content"].strip().strip(".'\"")
                            if ans and ans.upper() != "NONE" and len(ans.split()) == 1 and len(ans) < 20:
                                return ans.capitalize()
            except Exception:
                pass

        return ""

    @staticmethod
    def get_thinking_filler(language: str = "hinglish") -> str:
        """Returns a natural, low-latency conversational filler for speech buffering."""
        import random
        fillers = {
            "hindi": [
                "Haan ji, ek second...",
                "Bilkul, main abhi dekhti hoon...",
                "Acha, ek pal rukiye...",
            ],
            "hinglish": [
                "Haan ji, just a second...",
                "Bilkul, let me check...",
                "Haan, ek second dekhti hoon...",
            ],
            "english": [
                "Sure, just a second...",
                "Right, let me check that...",
                "Got it, one moment please...",
            ],
        }
        options = fillers.get(language.lower(), fillers["hinglish"])
        return random.choice(options)

