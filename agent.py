"""
agent.py - Real-Time Multi-Persona AI Voice Agent (Enterprise Modular Architecture).
Orchestrates Silero VAD, Streaming STT, Groq LPU LLM, Neural TTS, Dynamic Toolchains, and WebRTC Events.
"""

import asyncio
import sys

# Ensure UTF-8 output encoding on Windows consoles to prevent charmap errors with Hindi text
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass
    if hasattr(sys.stderr, "buffer"):
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass

# Ensure event loop exists on Python 3.12+ in spawned worker processes
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import json
import logging
import os
import time
import aiohttp
from dotenv import load_dotenv

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)

from personas.registry import get_persona, get_tts_voice, DEFAULT_PERSONA_ID
from pipeline import (
    CallingPipelineConfig,
    SileroVADProvider,
    AudioRecorder,
    VoicePipelineBuilder,
)
from toolchain import ToolRegistry
from orchestrator import LlmOrchestrator, MemoryManager, StructuredExtractor
from events import CallEventSession, CaptionBroadcaster, EventDispatcher

from logger import get_agent_logger, get_call_logger

logger = get_agent_logger()

HELLO_API_URL = os.getenv("HELLO_API_URL", "http://localhost:5063")
RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)


def prewarm(proc: JobProcess):
    """Preload Silero VAD model into memory for zero cold-start delay."""
    logger.info("Prewarming Silero VAD model with tuned voice thresholds...")
    proc.userdata["vad"] = SileroVADProvider.create()
    logger.info("Silero VAD model prewarmed successfully.")


def extract_metadata(room_metadata: str, participant_metadata: str = None) -> dict:
    """Parse JSON metadata from Room or Participant."""
    meta = {}
    for raw in [participant_metadata, room_metadata]:
        if raw and raw.strip():
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    meta.update(parsed)
            except Exception as e:
                logger.warning(f"Failed to parse metadata: {e}")
    return meta


async def fetch_persona_config(persona_id: str) -> dict:
    """Fetch live persona prompt, custom questions and settings from hello_api."""
    if not persona_id:
        return {}
    clean_id = persona_id if persona_id.startswith("persona_role_") else f"persona_role_{persona_id}"
    url = f"{HELLO_API_URL}/api/ai/personas/{clean_id}/config"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2.0)) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.debug(f"Could not fetch dynamic persona config for {persona_id}: {e}")
    return {}


async def fetch_user_memory(user_id: str, persona_id: str) -> dict:
    """Fetch previous conversation memory & context from hello_api."""
    if not user_id or not persona_id:
        return {"hasHistory": False, "memorySummary": "", "recentTurns": []}

    url = f"{HELLO_API_URL}/api/ai/memory?userId={user_id}&personaId={persona_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"[hello_api] Memory loaded: hasHistory={data.get('hasHistory')}")
                    return data
    except Exception as e:
        logger.warning(f"[hello_api] Could not fetch memory: {e}")

    return {"hasHistory": False, "memorySummary": "", "recentTurns": []}


async def save_structured_data(call_id: str, user_id: str, persona_id: str, structured_obj: dict):
    """Sends structured JSON output to hello_api for storage in PostgreSQL."""
    if not call_id or not structured_obj:
        return
    url = f"{HELLO_API_URL}/api/ai/calls/{call_id}/structured-data"

    if "dataType" in structured_obj and "structuredJson" in structured_obj:
        data_type = structured_obj["dataType"]
        safe_json = structured_obj["structuredJson"]
        summary = structured_obj.get("summary", "")
    else:
        data_type = structured_obj.get("type", "general")
        summary = (
            structured_obj.get("screening_notes")
            or structured_obj.get("summary")
            or structured_obj.get("passenger_notes")
            or structured_obj.get("takeaways")
            or ""
        )
        safe_json = json.dumps(structured_obj)

    payload = {
        "callSessionId": call_id,
        "userId": user_id,
        "personaId": persona_id,
        "dataType": data_type,
        "structuredJson": safe_json,
        "summary": summary,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    logger.info(f"[hello_api] Structured data saved for call {call_id} ({data_type})")
    except Exception as e:
        logger.error(f"[hello_api] Failed to save structured data: {e}")


async def save_user_memory(
    call_id: str,
    user_id: str,
    persona_id: str,
    turns: list,
    orchestrator: LlmOrchestrator,
    opening_style: str = "default",
    tools_ctx=None,
    caller_name: str = ""
):
    """Saves final conversation summary, closing intent topic, remembered caller/child name, and structured payloads to hello_api."""
    if not user_id:
        return

    # Extract name from conversation turns if not provided or if placeholder
    if not caller_name or caller_name.lower() in ["contact", "user", "admin", "null", "none", "unknown"]:
        try:
            extracted = await orchestrator.extract_caller_name(turns)
            if extracted:
                caller_name = extracted
                logger.info(f"✨ [Memory] Spoken caller name '{caller_name}' extracted from conversation turns.")
        except Exception as e:
            logger.warning(f"Failed to extract caller name from turns: {e}")

    summary = await orchestrator.extract_compact_memory(turns)
    last_topic, last_user_statement = await orchestrator.extract_closing_intent_and_topic(turns)
    url = f"{HELLO_API_URL}/api/ai/memory/save"
    payload = {
        "callId": call_id,
        "userId": user_id,
        "personaId": persona_id,
        "userName": caller_name,
        "childName": caller_name,
        "turns": turns,
        "memorySummary": summary,
        "lastTopic": last_topic,
        "lastUserStatement": last_user_statement,
        "lastOpeningStyle": opening_style,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    logger.info(f"[hello_api] Conversation memory (Name: '{caller_name}', Topic: '{last_topic}') updated.")
    except Exception as e:
        logger.error(f"[hello_api] Failed to save conversation memory: {e}")

    # Automatically extract & persist any family members mentioned during the call
    try:
        from orchestrator.family_memory_manager import FamilyMemoryManager
        fam_mgr = FamilyMemoryManager(api_base_url=HELLO_API_URL)
        saved_fams = await fam_mgr.extract_and_save_family_members(turns, user_id)
        if saved_fams:
            logger.info(f"👨‍👩‍👧 [Memory] Extracted and persisted {len(saved_fams)} family members for user {user_id}")
    except Exception as e:
        logger.warning(f"[Memory] Failed to extract family members: {e}")

    # Structured data extraction (from in-memory session or LLM extraction)
    structured_payload = None
    if tools_ctx and hasattr(tools_ctx, "get_final_structured_payload"):
        structured_payload = tools_ctx.get_final_structured_payload(persona_id)

    if not structured_payload:
        extractor = StructuredExtractor(api_key=orchestrator.api_key)
        structured_payload = await extractor.extract_call_summary(turns, persona_role=persona_id)

    if structured_payload:
        await save_structured_data(call_id, user_id, persona_id, structured_payload)


async def save_task_call_evaluation(
    response_id: str,
    task_id: str,
    persona_id: str,
    task_code: str,
    task_title: str,
    phone_number: str,
    user_name: str,
    turns: list,
    duration_seconds: int,
    orchestrator: LlmOrchestrator,
    task_info: dict = None
):
    """Evaluates the conversation against task criteria, scores 0-100%, and logs to hello_api."""
    if not task_info:
        task_info = {}

    extractor = StructuredExtractor(api_key=orchestrator.api_key)
    eval_result = await extractor.evaluate_persona_task_match(turns, persona_id, task_info)

    # Format dialogue turns for storage
    formatted_dialogue = [
        {"role": "ai" if t.get("role") in ["assistant", "ai"] else "user", "message": t.get("content", ""), "timestamp": t.get("timestamp", "")}
        for t in turns
    ]

    structured_telemetry = eval_result.get("structured_payload", {})
    if "salary_evaluation" in eval_result:
        structured_telemetry["salary_evaluation"] = eval_result["salary_evaluation"]
    if "experience_evaluation" in eval_result:
        structured_telemetry["experience_evaluation"] = eval_result["experience_evaluation"]
    if "options_matched" in eval_result:
        structured_telemetry["options_matched"] = eval_result["options_matched"]

    payload = {
        "responseId": response_id if response_id else None,
        "taskId": task_id if task_id else None,
        "personaId": persona_id,
        "taskCode": task_code,
        "taskTitle": task_title,
        "phoneNumber": phone_number,
        "userName": user_name,
        "matchScore": eval_result.get("match_score", 75),
        "qualificationStatus": eval_result.get("qualification_status", "Potential Match"),
        "summary": eval_result.get("summary", ""),
        "answers": eval_result.get("answers", []),
        "dialogue": formatted_dialogue,
        "structuredJson": structured_telemetry,
        "durationSeconds": duration_seconds
    }

    url = f"{HELLO_API_URL}/api/admin/persona/task/user"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                if resp.status == 200:
                    logger.info(f"[hello_api] Task call response & match score ({payload['matchScore']}%) saved successfully.")
    except Exception as e:
        logger.error(f"[hello_api] Failed to save task call response: {e}")


async def report_call_end(call_id: str, duration_seconds: int, recording_file: str, orchestrator: LlmOrchestrator):
    """Notifies hello_api that the call has ended with duration and recording file."""
    if not call_id:
        return
    url = f"{HELLO_API_URL}/api/ai/calls/{call_id}/end"
    payload = {
        "durationSeconds": duration_seconds,
        "recordingFile": recording_file,
        "llmProvider": orchestrator.active_provider,
        "llmModel": orchestrator.active_model,
        "latencyTelemetry": json.dumps({
            "stt_engine": "whisper-large-v3-turbo",
            "tts_engine": "neural-cached",
            "sample_rate": 24000,
        }),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    logger.info(f"[hello_api] Call {call_id} duration logged successfully.")
    except Exception as e:
        logger.error(f"[hello_api] Failed to report call end: {e}")


async def entrypoint(ctx: JobContext):
    """LiveKit worker job entry point for handling incoming AI voice call."""
    logger.info(f"Connecting to LiveKit Room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(f"User joined call: {participant.identity}")

    # Extract user metadata
    meta = extract_metadata(ctx.room.metadata, participant.metadata)
    call_id = meta.get("call_id") or ctx.room.name.replace("ai_call_", "")
    caller_id = meta.get("caller_id") or participant.identity
    clean_caller_id = caller_id.replace("admin_", "") if caller_id else ""
    persona_id = meta.get("persona") or meta.get("persona_id", DEFAULT_PERSONA_ID)
    language = meta.get("language", "hinglish")
    gender = meta.get("gender", "female")

    call_trace = get_call_logger(call_id)
    call_trace.log_session_start(clean_caller_id, persona_id, language, gender)

    task_id = meta.get("taskId")
    task_code = meta.get("taskCode")
    task_title = meta.get("taskTitle")
    target_phone = meta.get("phone", "")
    target_user_name = meta.get("userName", "Contact")
    response_id = meta.get("responseId")

    persona = get_persona(persona_id)
    system_prompt = persona.get_system_prompt(language)
    tts_voice = get_tts_voice(language, gender)
    greeting_text = persona.get_greeting(language)

    # Initialize LLM Orchestrator
    orchestrator = LlmOrchestrator()

    # If it's a specific Persona Task call, load task requirements & questions
    task_info = {}
    if task_id:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{HELLO_API_URL}/api/admin/persona/tasks/{task_id}", timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                    if resp.status == 200:
                        task_info = await resp.json()
        except Exception as e:
            logger.warning(f"Could not load task details for {task_id}: {e}")

    if task_info:
        task_prompt = task_info.get("system_prompt") or ""
        raw_questions = task_info.get("questions") or []
        parsed_q = json.loads(raw_questions) if isinstance(raw_questions, str) else raw_questions
        task_info["questions"] = parsed_q
        q_items = []
        for idx, q in enumerate(parsed_q):
            if not q.get("question"):
                continue
            q_type = q.get("type", "text").upper()
            w = q.get("weight", 25)
            q_str = f"- Q{idx+1} [{q_type}]: {q.get('question')} (Weight: {w}%"
            opts = q.get("options")
            if opts:
                q_str += f", Options: {json.dumps(opts)}"
            if q.get("min") is not None:
                q_str += f", Range: {q.get('min')}-{q.get('max')} {q.get('unit', '')}"
            q_str += ")"
            q_items.append(q_str)
        q_lines = "\n".join(q_items)

        attributes = task_info.get("attributes") or []
        if isinstance(attributes, str):
            try:
                attributes = json.loads(attributes)
            except:
                attributes = []

        # Fallback to legacy fields if attributes array is empty
        if not attributes:
            sal = task_info.get("salary_range")
            if sal and (sal.get("min") or sal.get("max")):
                attributes.append({"name": "Budget / Compensation", "type": "range", **sal})
            exp = task_info.get("experience_range")
            if exp and (exp.get("min") or exp.get("max")):
                attributes.append({"name": "Experience / Volume", "type": "range", **exp})
            for opt in (task_info.get("criteria_options") or []):
                attributes.append({"name": opt.get("category", "Option"), "type": "options", "options": opt.get("options", []), "preferred": opt.get("preferred", "")})

        attr_lines = []
        for a in attributes:
            a_name = a.get("name") or a.get("id") or "Attribute"
            a_type = a.get("type", "range")
            if a_type == "range" or ("min" in a and "max" in a):
                attr_lines.append(f"- {a_name}: {a.get('min', 0)} to {a.get('max', 0)} {a.get('unit', '')}")
            elif a_type in ("options", "choice"):
                opts = a.get("options", [])
                pref = f" (Preferred: {a.get('preferred')})" if a.get("preferred") else ""
                attr_lines.append(f"- {a_name}: {json.dumps(opts)}{pref}")
            elif a_type == "number":
                attr_lines.append(f"- {a_name}: Min {a.get('min', 0)} {a.get('unit', '')}")
            elif a_type == "boolean":
                attr_lines.append(f"- {a_name}: Yes/No verification")
            else:
                attr_lines.append(f"- {a_name}: {a.get('value', 'As specified')}")
        attr_str = "\n".join(attr_lines) if attr_lines else "None specified"

        system_prompt += (
            f"\n\nOUTBOUND CALL SUB-TASK: '{task_info.get('title')}'\n"
            f"Guidance: {task_prompt}\n"
            f"TARGET CRITERIA & CUSTOM ATTRIBUTES TO ASSESS:\n{attr_str}\n"
            f"EVALUATION QUESTIONS TO SYSTEMATICALLY ASK & ASSESS:\n{q_lines}\n"
            "INSTRUCTION: Ask questions naturally and conversationally. Verify all target criteria/attributes against what the user states, and capture their exact details."
        )


    # Dynamic TTS Engine & Pitch/Rate
    tts_provider = meta.get("tts_provider") or os.getenv("DEFAULT_TTS_PROVIDER", "edge")
    active_pitch = meta.get("pitch") or getattr(persona, "pitch", "+0Hz")
    active_rate = meta.get("rate") or getattr(persona, "rate", "+18%")

    # Dedicated Animated Female AI Characters for Kids Learning (Puruva, Kairi, Tray)
    # Default first time: ALWAYS Puruva! Normal user-to-user calling remains 100% unaffected.
    active_character = None
    if "kids" in str(persona.id).lower() or "learning" in str(persona.id).lower():
        from personas.kids_characters import get_initial_character
        active_character = get_initial_character()
        active_pitch = active_character.get("pitch", "+16Hz")
        active_rate = active_character.get("rate", "+18%")
        greeting_text = active_character.get("greeting", greeting_text)
        system_prompt += (
            f"\n\n[ACTIVE FEMALE AI CHARACTER: {active_character['name'].upper()} ({active_character['title'].upper()})]\n"
            f"Personality: {active_character['personality']}\n"
            f"GREETING RULE: You introduce yourself ONLY in the very first greeting at the start of the call. In ongoing conversation, DO NOT say 'Namaste' and DO NOT say 'Main hoon {active_character['name']}' over and over again! Answer the child directly and naturally.\n"
            f"STORYTELLING RULE: When narrating a story (`narrate_story`), recite the story scene out loud with warmth and excitement! Never stay silent!\n"
            f"MANDATORY FEMININE GRAMMAR: Strictly speak with feminine Hindi grammar ('main karti hoon', 'main bolti hoon', 'khelungi', 'bataungi')!\n"
        )
        logger.info(f"👧 [KidsCharacter] Activated initial female AI character: '{active_character['name']}' ({active_character['role_badge']})")

    # Dynamic Persona Config from Database (enables live script & question editing)
    dynamic_cfg = await fetch_persona_config(persona_id)
    if dynamic_cfg:
        if dynamic_cfg.get("systemPrompt"):
            system_prompt = dynamic_cfg["systemPrompt"]
        if dynamic_cfg.get("greetingText"):
            greeting_text = dynamic_cfg["greetingText"]
        if dynamic_cfg.get("ttsEngine"):
            tts_provider = dynamic_cfg["ttsEngine"]
        if dynamic_cfg.get("ttsVoice"):
            tts_voice = dynamic_cfg["ttsVoice"]
        
        # Inject custom requirements/questions if configured
        custom_questions_raw = dynamic_cfg.get("customQuestions")
        if custom_questions_raw:
            try:
                questions_list = json.loads(custom_questions_raw) if isinstance(custom_questions_raw, str) else custom_questions_raw
                if questions_list and isinstance(questions_list, list):
                    q_lines = "\n".join([f"- {q.get('label', q.get('id', 'Question'))}: {q.get('question', q.get('label', ''))}" for q in questions_list])
                    system_prompt += (
                        f"\n\nCRITICAL CONVERSATION GOALS & MANDATORY QUESTIONS TO ASK:\n"
                        f"During this call, your role is to systematically collect answers for the following requirements:\n"
                        f"{q_lines}\n"
                        f"Ask these naturally, listen to the user, and acknowledge their responses."
                    )
            except Exception as e:
                logger.warning(f"Error parsing custom questions: {e}")

    # Fetch Caller Long-Term Memory
    memory_data = await fetch_user_memory(clean_caller_id, persona.id)
    if memory_data.get("hasHistory") and memory_data.get("memorySummary"):
        summary = memory_data["memorySummary"]
        total_prev_calls = memory_data.get("totalCalls", 1)
        system_prompt += (
            f"\n\nPAST USER MEMORY & PREVIOUS CALL CONTEXT:\n"
            f"You have spoken with this user {total_prev_calls} time(s) before.\n"
            f"Key things remembered from past conversations: {summary}\n\n"
            "INSTRUCTION FOR CONTINUITY: Greet the user warmly acknowledging your past conversations."
        )

    # Name-Aware Memory Resolution & Identity Prompt Injection
    known_name = (
        meta.get("userName")
        or meta.get("user_name")
        or memory_data.get("userName")
        or memory_data.get("childName")
        or ""
    ).strip()
    if known_name.lower() in ["contact", "user", "admin", "null", "none", "unknown"]:
        known_name = ""

    is_kids = ("kids" in str(persona_id).lower() or "learning" in str(persona_id).lower())

    if known_name:
        if is_kids:
            system_prompt += (
                f"\n\n[USER IDENTITY & CALLER NAME]:\n"
                f"The child's name is '{known_name}'. You already know and remember their name!\n"
                f"- ALWAYS address them warmly and affectionately by their name '{known_name}' (e.g. 'waah {known_name} champ!', 'shabash {known_name}!').\n"
                f"- NEVER ask what their name is, because you already remember them.\n"
            )
    if is_kids and "TIME REALISM" not in system_prompt:
        system_prompt += (
            "\n\n[TIME-AWARE RULES]:\n"
            "- In morning: ask about brush/breakfast. Afternoon: ask about school. Evening: ask about park play. Night: bedtime story.\n"
            "- If child asks for Puruva/Kairi/Tray, call `switch_active_character`."
        )
    logger.info(f"👤 Resolved Known Name: '{known_name}' (Is Kids: {is_kids})")

    logger.info("==================================================")
    logger.info(f"📞 Call ID         : {call_id}")
    logger.info(f"👤 Caller ID       : {caller_id} (Clean: {clean_caller_id})")
    logger.info(f"🤖 Active Persona  : {persona.name} ({persona.id})")
    logger.info(f"🧠 Has Memory      : {memory_data.get('hasHistory', False)}")
    logger.info(f"🌐 Active Language : {language}")
    logger.info(f"🎙️ TTS Provider    : {tts_provider.upper()} ({tts_voice})")
    logger.info(f"🔥 LLM Model       : {orchestrator.active_model}")
    logger.info("==================================================")

    # Setup Audio Recording
    recording_filename = f"{call_id}.wav"
    recording_filepath = os.path.join(RECORDINGS_DIR, recording_filename)
    recorder = AudioRecorder(recording_filepath, sample_rate=24000)
    recorder.start()

    # Enforce Feminine Hindi Grammar Mandate for Female Voice / Persona
    is_female = (
        (str(gender).lower() == "female") or
        any(w in str(tts_voice).lower() for w in ["swara", "zira", "female", "radha", "priya"]) or
        "kids" in str(persona_id).lower()
    )
    if is_female and "karti hoon" not in system_prompt:
        system_prompt += (
            "\n\n[CRITICAL MANDATORY FEMININE GRAMMAR RULE]:\n"
            "Your voice is strictly FEMALE. In Hindi and Hinglish, you MUST speak using exclusively FEMININE first-person verb forms:\n"
            "- ALWAYS say: 'main karti hoon', 'main bolti hoon', 'main sunati hoon', 'main bataungi / batati hoon', 'main khelungi / khelti hoon'.\n"
            "- Refer to yourself as: 'aapki pyari Puruva AI / dost'. NEVER use masculine verbs ('karta', 'bolta', 'raha hoon', 'karunga')!"
        )

    # Build ChatContext
    initial_chat_ctx = llm.ChatContext()
    initial_chat_ctx.append(role="system", text=system_prompt)

    # Format & Inject Persistent Family Knowledge Profile
    from orchestrator.family_memory_manager import FamilyMemoryManager
    family_members = memory_data.get("familyMembers", [])
    family_context = FamilyMemoryManager.format_family_prompt_context(family_members)
    if family_context:
        initial_chat_ctx.append(role="system", text=family_context)

    recent_turns = memory_data.get("recentTurns", [])
    if recent_turns:
        for turn in recent_turns[-2:]:
            r, c = turn.get("role"), turn.get("content")
            if r in ["user", "assistant"] and c:
                initial_chat_ctx.append(role=r, text=c)

    # Create Dynamic Toolchain (10 Common + Persona-Specific Tools)
    tools_ctx = ToolRegistry.create_context(
        persona_id=persona.id,
        call_session_id=call_id,
        user_id=clean_caller_id,
        api_base_url=HELLO_API_URL,
        room=ctx.room,
        language=language,
    )

    # Build VoicePipelineAgent
    llm_instance = orchestrator.get_livekit_llm(temperature=persona.temperature)
    agent = VoicePipelineBuilder.build(
        llm_instance=llm_instance,
        chat_ctx=initial_chat_ctx,
        fnc_ctx=tools_ctx,
        tts_provider=tts_provider,
        voice=tts_voice,
        pitch=active_pitch,
        rate=active_rate,
        language=language,
        gender=gender,
    )

    # Attach active agent instance to tools_ctx for background timers/watchdogs
    if tools_ctx:
        setattr(tools_ctx, "agent", agent)

    # Initialize Call Session State
    session = CallEventSession(
        call_id=call_id,
        caller_id=caller_id,
        clean_caller_id=clean_caller_id,
        persona_id=persona.id,
        language=language,
        gender=gender,
        recording_file=recording_filename,
        active_character=active_character,
        known_name=known_name,
    )

    # Bind Events via EventDispatcher
    lifecycle_handler = EventDispatcher.bind(
        agent=agent,
        room=ctx.room,
        participant=participant,
        session=session,
        recorder=recorder,
        tools_ctx=tools_ctx,
        api_base_url=HELLO_API_URL,
    )

    # Start Voice Agent
    agent.start(ctx.room, participant)
    logger.info("VoicePipelineAgent started.")

    # Broadcast initial character info packet for Kids Learning Persona
    if active_character and ctx.room and ctx.room.local_participant:
        try:
            char_pkt = {
                "type": "character_info",
                "character_id": active_character["id"],
                "name": active_character["name"],
                "display_name": active_character["display_name"],
                "title": active_character["title"],
                "avatar_url": active_character["avatar_url"],
                "avatar_asset": active_character.get("avatar_asset", ""),
                "avatar_data_path": active_character.get("avatar_data_path", ""),
                "character_type": active_character.get("character_type", ""),
                "theme_color": active_character["theme_color"],
                "pitch": active_character["pitch"],
                "rate": active_character["rate"],
                "role_badge": active_character["role_badge"],
            }
            asyncio.create_task(ctx.room.local_participant.publish_data(
                json.dumps(char_pkt).encode("utf-8"),
                reliable=True
            ))
            logger.info(f"👧 [KidsCharacter] Broadcast initial character packet for {active_character['name']}")
        except Exception as e:
            logger.warning(f"Failed to broadcast initial character info: {e}")

    # Give WebRTC audio channel 500ms to establish audio track subscription on the mobile device
    await asyncio.sleep(0.5)

    # Speak Opening Greeting Immediately (Guaranteed delivery without mic transient false-interruptions)
    if is_kids:
        if known_name:
            greeting_text = f"Yaaay! Hello {known_name} superstar! Main hoon aapki pyari Puruva AI! Aaj kya masti karein?"
        else:
            greeting_text = "Yaaay! Hello superstar! Main hoon aapki pyari Puruva AI! Aaj kya masti karein?"
    elif known_name:
        greeting_text = f"Namaste {known_name} ji! {greeting_text}"

    logger.info(f"🔊 [Agent] Speaking opening greeting immediately (Name: '{known_name}'): '{greeting_text}'")
    # CRITICAL: allow_interruptions MUST be False for the opening greeting so mic transient clicks or room noise never cancel the greeting!
    await agent.say(greeting_text, allow_interruptions=False)
    asyncio.create_task(CaptionBroadcaster.broadcast(ctx.room, "assistant", greeting_text))

    # Await Call End
    try:
        await lifecycle_handler.wait_for_disconnect()
    finally:
        recorder.stop_and_save()
        call_trace.log_session_end(session.duration_seconds)
        logger.info(f"Call finished. Duration: {session.duration_seconds}s.")

        # Final Conversation Turns
        final_turns = session.turns if session.turns else [
            {"role": msg.role, "content": msg.content if isinstance(msg.content, str) else str(msg.content)}
            for msg in agent.chat_ctx.messages if msg.role in ["user", "assistant"]
        ]

        # Post-Call Memory & Structured Intelligence Wrap-up (Persist remembered name)
        await save_user_memory(
            call_id,
            clean_caller_id,
            persona.id,
            final_turns,
            orchestrator,
            opening_style=used_opening_style,
            tools_ctx=tools_ctx,
            caller_name=known_name
        )


        # Dispatch Parent Learning & Engagement Report for Kids Calls
        if "kids" in persona.id or (tools_ctx and hasattr(tools_ctx, "session_data") and "kids_gamification" in getattr(tools_ctx, "session_data", {})):
            try:
                from datetime import datetime
                gam = getattr(tools_ctx, "session_data", {}).get("kids_gamification", {})
                words = gam.get("words_learned", [])
                topics = gam.get("topics_explored", [])
                stars = gam.get("stars", 0)
                tier = gam.get("curriculum_tier", "primary")
                dur_sec = session.duration_seconds
                mins = dur_sec // 60
                secs = dur_sec % 60
                dur_fmt = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

                if words:
                    parent_tip = f"Aapka bacha aaj {', '.join(words[:4])} shabd bohot achhe se seekh raha tha! Raat ko sone se pehle unse ye shabd dohrane ko kahein."
                elif any("habit" in t.lower() for t in topics):
                    parent_tip = "Aapka bacha aaj swasth aadaton (Good Habits) ke baare me seekh raha tha! Kal subah unhe brush karne par shabashi dein."
                elif any("story" in t.lower() for t in topics):
                    parent_tip = "Aapke bache ne aaj seekh dene wali kahani bohot dhyan se suni! Unse poochhein ki kahani ka sabse achha hissa kaun sa tha."
                else:
                    parent_tip = "Aapka bacha active aur curious tha! Roz thodi der aisi learning activities karne se bache ka aatmavishwas badhta hai."

                rep_payload = {
                    "call_id": call_id,
                    "caller_id": clean_caller_id,
                    "duration_seconds": dur_sec,
                    "duration_formatted": dur_fmt,
                    "curriculum_tier": tier,
                    "stars_earned": stars,
                    "words_learned": words,
                    "topics_explored": list(dict.fromkeys(topics)),
                    "parent_tip": parent_tip,
                    "created_at": datetime.now().isoformat()
                }
                async with aiohttp.ClientSession() as cl:
                    await cl.post(f"{HELLO_API_URL}/api/ai/calls/{call_id}/learning-report", json=rep_payload, timeout=5)
                logger.info(f"📊 [ParentReport] Dispatched report for call {call_id}: {dur_fmt}, {stars} stars, {len(words)} words")
            except Exception as ex:
                logger.debug(f"[ParentReport] Learning report send error: {ex}")


        if task_id or response_id:
            await save_task_call_evaluation(
                response_id=response_id,
                task_id=task_id,
                persona_id=persona.id,
                task_code=task_code or task_info.get("task_code", ""),
                task_title=task_title or task_info.get("title", ""),
                phone_number=target_phone,
                user_name=target_user_name,
                turns=final_turns,
                duration_seconds=session.duration_seconds,
                orchestrator=orchestrator,
                task_info=task_info
            )

        await report_call_end(call_id, session.duration_seconds, recording_filename, orchestrator)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
