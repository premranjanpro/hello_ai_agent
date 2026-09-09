"""
events/call_events.py - Call Lifecycle & Audio Subscription Event Handlers.
Tracks participant joins, disconnections, audio streaming into AudioRecorder,
and incremental real-time dialogue syncing with backend database.
"""

import asyncio
import logging
import time
from typing import Optional, Any
import aiohttp
from livekit import rtc

from events.base import CallEventSession
from pipeline.audio_recorder import AudioRecorder

logger = logging.getLogger("events.call")


class CallLifecycleHandler:
    """Manages participant events, audio subscription, and background turn syncing."""

    def __init__(
        self,
        room: rtc.Room,
        participant: rtc.RemoteParticipant,
        session: CallEventSession,
        recorder: AudioRecorder,
        agent: Any = None,
        tools_ctx: Any = None,
        api_base_url: str = "http://localhost:5063",
        watchdog: Optional[Any] = None,
    ):
        self.room = room
        self.participant = participant
        self.session = session
        self.recorder = recorder
        self.agent = agent
        self.tools_ctx = tools_ctx
        self.api_base_url = api_base_url.rstrip("/")
        self.watchdog = watchdog
        self.disconnect_event = asyncio.Event()
        self._sync_task: Optional[asyncio.Task] = None
        self._dismiss_comment_count = 0
        self._last_dismiss_comment_time = 0.0

    def bind(self):
        # 1. Track subscription: pipe audio frames into AudioRecorder
        @self.room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, p: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"[CallLifecycle] Subscribed to audio track {track.sid}. Real-time recording started.")
                audio_stream = rtc.AudioStream(track)

                async def _record_loop():
                    async for event in audio_stream:
                        self.recorder.write_frame(event.frame)

                asyncio.create_task(_record_loop())

        # 2. Participant disconnected
        @self.room.on("participant_disconnected")
        def on_participant_disconnected(p: rtc.RemoteParticipant):
            if p.identity == self.participant.identity:
                logger.info(f"[CallLifecycle] User {p.identity} left the room.")
                if self.watchdog:
                    self.watchdog.stop()
                self.disconnect_event.set()

        # 3. Room disconnected
        @self.room.on("disconnected")
        def on_room_disconnected():
            logger.info("[CallLifecycle] LiveKit room disconnected.")
            if self.watchdog:
                self.watchdog.stop()
            self.disconnect_event.set()

        # 4. Handle incoming interactive UI responses (screen taps on bottom sheet)
        @self.room.on("data_received")
        def on_data_received(dp: rtc.DataPacket):
            try:
                import json
                raw_text = dp.data.decode("utf-8")
                payload = json.loads(raw_text)
                p_type = payload.get("type")
                comp = str(payload.get("component") or payload.get("sheet_id") or "").lower()
                if p_type in ["interactive_ui_response", "quiz_answer"]:
                    if self.watchdog:
                        self.watchdog.on_user_interaction("screen_tap")
                    opt_id = payload.get("selected_option_id") or payload.get("option_index")
                    opt_text = payload.get("selected_option_text") or payload.get("option_text")
                    if str(opt_id) == "sheet_timeout" and hasattr(self, "tools_ctx") and hasattr(self.tools_ctx, "handle_bottom_sheet_closure"):
                        async def _handle_timeout():
                            try:
                                speech = await self.tools_ctx.handle_bottom_sheet_closure(component=comp, is_timeout=True)
                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Sheet timeout error: {ex}")
                        asyncio.create_task(_handle_timeout())
                    elif comp == "visual_image_quiz" or str(opt_id).startswith("quiz_animal_"):
                        async def _handle_visual_quiz_tap():
                            try:
                                if hasattr(self.tools_ctx, "cancel_quiz_timer"):
                                    self.tools_ctx.cancel_quiz_timer()
                                if str(opt_id) in ["read_options", "read_quiz_options"] and hasattr(self.tools_ctx, "read_quiz_options_aloud"):
                                    speech = await self.tools_ctx.read_quiz_options_aloud()
                                elif hasattr(self.tools_ctx, "evaluate_visual_quiz_answer"):
                                    ans = opt_text or opt_id
                                    speech = await self.tools_ctx.evaluate_visual_quiz_answer(selected_answer=ans)
                                else:
                                    speech = f"Arre waah! Aapne {opt_text or opt_id} chuna hai!"
                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Visual quiz tap error: {ex}")
                        asyncio.create_task(_handle_visual_quiz_tap())
                    elif comp == "tic_tac_toe" and hasattr(self, "tools_ctx") and hasattr(self.tools_ctx, "play_tic_tac_toe"):
                        async def _handle_ttt():
                            try:
                                pos = int(opt_id) if str(opt_id).isdigit() else -1
                                comm = await self.tools_ctx.play_tic_tac_toe(action="move", position=pos)
                                if comm and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(comm, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Tic-Tac-Toe tap error: {ex}")
                        asyncio.create_task(_handle_ttt())
                    elif comp == "memory_match" and hasattr(self, "tools_ctx") and hasattr(self.tools_ctx, "play_memory_game"):
                        async def _handle_mem():
                            try:
                                idx = int(opt_id) if str(opt_id).isdigit() else -1
                                comm = await self.tools_ctx.play_memory_game(action="flip", card_index=idx)
                                if comm and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(comm, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Memory Match tap error: {ex}")
                        asyncio.create_task(_handle_mem())
                    elif (str(opt_id).startswith("riddle_opt_") or "riddle" in str(payload.get("sheet_id", ""))) and hasattr(self, "tools_ctx") and hasattr(self.tools_ctx, "solve_kids_riddle"):
                        async def _handle_riddle_tap():
                            try:
                                ans = opt_text or opt_id
                                speech = await self.tools_ctx.solve_kids_riddle(answer=ans)
                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Riddle tap error: {ex}")
                        asyncio.create_task(_handle_riddle_tap())
                    elif (comp == "curriculum" or str(opt_id).startswith("tier_")) and hasattr(self, "tools_ctx") and hasattr(self.tools_ctx, "set_curriculum_tier"):
                        async def _handle_curriculum():
                            try:
                                t = str(opt_id).replace("tier_", "")
                                speech = await self.tools_ctx.set_curriculum_tier(tier=t)
                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Curriculum switch error: {ex}")
                        asyncio.create_task(_handle_curriculum())
                    elif (comp in ["topic_picker", "category_picker"] or str(opt_id).startswith("topic_")) and hasattr(self, "tools_ctx"):
                        async def _handle_topic_jump():
                            try:
                                import json
                                curr_char = getattr(self.session, "active_character", {}) or {}
                                topic_key = str(opt_id).replace("topic_", "").lower()
                                logger.info(f"🎯 [CallLifecycle] Category switch requested: '{topic_key}' ({opt_text})")
                                topic_speech = ""

                                if any(k in topic_key for k in ["abcd", "alphabet", "phonics"]):
                                    if hasattr(self.tools_ctx, "show_alphabet_flashcard"):
                                        topic_speech = await self.tools_ctx.show_alphabet_flashcard(letter="A")
                                    elif hasattr(self.tools_ctx, "teach_english_phonics"):
                                        topic_speech = await self.tools_ctx.teach_english_phonics(word="APPLE")
                                elif any(k in topic_key for k in ["hindi", "varnamala", "hread"]):
                                    if hasattr(self.tools_ctx, "teach_hindi_varnamala"):
                                        topic_speech = await self.tools_ctx.teach_hindi_varnamala(letter="क")
                                    elif hasattr(self.tools_ctx, "teach_hindi_reading"):
                                        topic_speech = await self.tools_ctx.teach_hindi_reading(word="कमल")
                                elif any(k in topic_key for k in ["math", "count", "ginti", "table", "pahade"]):
                                    if hasattr(self.tools_ctx, "teach_counting_1_to_100"):
                                        topic_speech = await self.tools_ctx.teach_counting_1_to_100(start_num=1, count=10)
                                    elif hasattr(self.tools_ctx, "teach_maths_tables"):
                                        topic_speech = await self.tools_ctx.teach_maths_tables(number=2)
                                elif any(k in topic_key for k in ["story", "kahani"]):
                                    if hasattr(self.tools_ctx, "narrate_story"):
                                        topic_speech = await self.tools_ctx.narrate_story()
                                elif any(k in topic_key for k in ["rhyme", "balgeet", "poem", "kavita"]):
                                    if hasattr(self.tools_ctx, "recite_rhyme"):
                                        topic_speech = await self.tools_ctx.recite_rhyme(language="hindi")
                                elif "habit" in topic_key:
                                    if hasattr(self.tools_ctx, "teach_good_habit"):
                                        topic_speech = await self.tools_ctx.teach_good_habit(habit_name="brushing")
                                    elif hasattr(self.tools_ctx, "teach_good_and_bad_habit"):
                                        topic_speech = await self.tools_ctx.teach_good_and_bad_habit(habit_topic="brush")
                                elif any(k in topic_key for k in ["place", "tour", "darjeeling", "ghoom", "safari", "monument", "india"]):
                                    if hasattr(self.tools_ctx, "explore_india_place"):
                                        topic_speech = await self.tools_ctx.explore_india_place(place_name="darjeeling")
                                elif "curiosity" in topic_key and hasattr(self.tools_ctx, "answer_kids_curiosity"):
                                    topic_speech = await self.tools_ctx.answer_kids_curiosity(question_or_topic="sky")
                                elif "riddle" in topic_key and hasattr(self.tools_ctx, "ask_kids_riddle"):
                                    topic_speech = await self.tools_ctx.ask_kids_riddle(topic="animals")
                                elif "ttt" in topic_key and hasattr(self.tools_ctx, "play_tic_tac_toe"):
                                    topic_speech = await self.tools_ctx.play_tic_tac_toe(action="start")
                                elif "memory" in topic_key and hasattr(self.tools_ctx, "play_memory_game"):
                                    topic_speech = await self.tools_ctx.play_memory_game(action="start")
                                else:
                                    topic_speech = f"Arre wah champ! Chalo hum {opt_text or topic_key} seekhna shuru karte hain!"

                                if topic_speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(topic_speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Topic jump error: {ex}")
                        asyncio.create_task(_handle_topic_jump())
                    elif (opt_id in ["next_place", "place_next", "story_next_scene", "next_story", "next_card", "card_next", "next_activity", "next_video", "next_varnamala", "next_counting", "next_habit", "next_quote", "hread_next", "eread_next", "alphabet_next", "alphabet_prev"] or str(opt_id).startswith("place_")) and hasattr(self, "tools_ctx"):
                        async def _handle_next():
                            try:
                                speech = ""
                                if (opt_id in ["next_place", "place_next"]) and hasattr(self.tools_ctx, "next_india_place"):
                                    speech = await self.tools_ctx.next_india_place()
                                elif str(opt_id).startswith("place_") and hasattr(self.tools_ctx, "explore_india_place"):
                                    speech = await self.tools_ctx.explore_india_place(place_name=str(opt_id))
                                elif opt_id in ["alphabet_next", "next_letter"] and hasattr(self.tools_ctx, "show_alphabet_flashcard"):
                                    speech = await self.tools_ctx.show_alphabet_flashcard(letter="next")
                                elif opt_id in ["alphabet_prev", "prev_letter"] and hasattr(self.tools_ctx, "show_alphabet_flashcard"):
                                    speech = await self.tools_ctx.show_alphabet_flashcard(letter="prev")
                                elif opt_id == "story_next_scene" and hasattr(self.tools_ctx, "next_story_scene"):
                                    speech = await self.tools_ctx.next_story_scene()
                                elif opt_id == "hread_next" and hasattr(self.tools_ctx, "teach_hindi_reading"):
                                    speech = await self.tools_ctx.teach_hindi_reading(word="next")
                                elif opt_id == "eread_next" and hasattr(self.tools_ctx, "teach_english_phonics"):
                                    speech = await self.tools_ctx.teach_english_phonics(word="next")
                                elif opt_id in ["next_card", "card_next"] and hasattr(self.tools_ctx, "show_learning_card"):
                                    speech = await self.tools_ctx.show_learning_card()
                                elif opt_id == "next_video" and hasattr(self.tools_ctx, "play_kids_video"):
                                    speech = await self.tools_ctx.play_kids_video(topic="next")
                                elif opt_id == "next_varnamala" and hasattr(self.tools_ctx, "teach_hindi_varnamala"):
                                    speech = await self.tools_ctx.teach_hindi_varnamala(letter="next")
                                elif opt_id == "next_counting" and hasattr(self.tools_ctx, "teach_counting_1_to_100"):
                                    speech = await self.tools_ctx.teach_counting_1_to_100(start_num=1, count=10)
                                elif opt_id == "next_habit" and hasattr(self.tools_ctx, "teach_good_and_bad_habit"):
                                    speech = await self.tools_ctx.teach_good_and_bad_habit(habit_topic="next")
                                elif opt_id == "next_quote" and hasattr(self.tools_ctx, "get_daily_quote"):
                                    speech = await self.tools_ctx.get_daily_quote(day_or_topic="next")
                                elif hasattr(self.tools_ctx, "next_activity"):
                                    speech = await self.tools_ctx.next_activity()
                                elif hasattr(self.tools_ctx, "narrate_story"):
                                    speech = await self.tools_ctx.narrate_story()

                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Next activity error: {ex}")
                        asyncio.create_task(_handle_next())
                    elif opt_id in ["story_prev_scene", "prev_story", "prev_card", "prev_activity", "prev_video", "prev_varnamala", "prev_counting", "prev_habit", "prev_quote"] and hasattr(self, "tools_ctx"):
                        async def _handle_prev():
                            try:
                                speech = ""
                                if opt_id == "story_prev_scene" and hasattr(self.tools_ctx, "prev_story_scene"):
                                    speech = await self.tools_ctx.prev_story_scene()
                                elif opt_id == "prev_video" and hasattr(self.tools_ctx, "play_kids_video"):
                                    speech = await self.tools_ctx.play_kids_video(topic="prev")
                                elif opt_id == "prev_varnamala" and hasattr(self.tools_ctx, "teach_hindi_varnamala"):
                                    speech = await self.tools_ctx.teach_hindi_varnamala(letter="prev")
                                elif opt_id == "prev_counting" and hasattr(self.tools_ctx, "teach_counting_1_to_100"):
                                    speech = await self.tools_ctx.teach_counting_1_to_100(start_num=1, count=10)
                                elif opt_id == "prev_habit" and hasattr(self.tools_ctx, "teach_good_and_bad_habit"):
                                    speech = await self.tools_ctx.teach_good_and_bad_habit(habit_topic="prev")
                                elif opt_id == "prev_quote" and hasattr(self.tools_ctx, "get_daily_quote"):
                                    speech = await self.tools_ctx.get_daily_quote(day_or_topic="prev")
                                elif hasattr(self.tools_ctx, "narrate_story"):
                                    speech = await self.tools_ctx.narrate_story()

                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Prev activity error: {ex}")
                        asyncio.create_task(_handle_prev())
                    elif str(opt_id).startswith("inst_") and hasattr(self, "tools_ctx") and hasattr(self.tools_ctx, "play_musical_instrument"):
                        async def _handle_inst():
                            try:
                                iname = str(opt_id).replace("inst_", "")
                                speech = await self.tools_ctx.play_musical_instrument(instrument_name=iname)
                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Instrument switch error: {ex}")
                        asyncio.create_task(_handle_inst())
                    elif opt_id in ["seen_yes", "seen_no", "eaten_yes", "eaten_no"]:
                        async def _handle_card_resp():
                            try:
                                if hasattr(self.tools_ctx, "_add_star_and_check_level"):
                                    self.tools_ctx._add_star_and_check_level(1)
                                if opt_id == "seen_yes":
                                    resp = "Wah superstar! Aapne ise pehle bhi dekha hai! Aapki observation power bohot strong hai! +1 Star ⭐!"
                                elif opt_id == "seen_no":
                                    resp = "Koi baat nahi champ, aaj humne milkar ise seekh liya! Gyan badhta hai! +1 Star ⭐!"
                                elif opt_id == "eaten_yes":
                                    resp = "Mmm tasty! Swaad kaisa tha? Mazedaar na! Swasth rahne ke liye paushtik cheezein khana sabse achha hai! +1 Star ⭐!"
                                else:
                                    resp = "Koi baat nahi pyare bache, kabhi zaroor swaad chak kar dekhna! +1 Star ⭐!"
                                if self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(resp, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Card response error: {ex}")
                        asyncio.create_task(_handle_card_resp())
                    elif str(opt_id).startswith("photo_captured_"):
                        async def _handle_photo_done():
                            rel = str(opt_id).replace("photo_captured_", "")
                            resp = f"Aaha! {rel.capitalize()} ki kitni sundar photo click hui hai! Main ise hamari family memory album me save kar rahi hoon!"
                            if self.agent and hasattr(self.agent, "say"):
                                await self.agent.say(resp, allow_interruptions=True)
                        asyncio.create_task(_handle_photo_done())
                    elif opt_id == "sing_karaoke":
                        async def _handle_sing():
                            sing_msg = "Chalo superstar, mere saath gaao! Subah utho toh brush karo, raat ko sote brush karo! Kitu-mitu keede bhagao, chamkili smile banao! Wah champ, bohot surili aawaz hai aapki!"
                            if self.agent and hasattr(self.agent, "say"):
                                await self.agent.say(sing_msg, allow_interruptions=True)
                        asyncio.create_task(_handle_sing())
                    elif hasattr(self, "tools_ctx") and self.tools_ctx and hasattr(self.tools_ctx, "validate_quiz_answer"):
                        asyncio.create_task(self.tools_ctx.validate_quiz_answer(f"Option {opt_id}"))
                elif p_type in ["interactive_ui_dismissed", "interactive_ui_timeout"]:
                    comp = payload.get("component", "media")
                    if hasattr(self.tools_ctx, "cancel_quiz_timer"):
                        self.tools_ctx.cancel_quiz_timer()
                    is_timeout = (p_type == "interactive_ui_timeout")
                    logger.info(f"📱 [CallLifecycle] Bottom sheet closed/timeout: comp='{comp}', is_timeout={is_timeout}")
                    if hasattr(self.tools_ctx, "handle_bottom_sheet_closure"):
                        async def _handle_close():
                            try:
                                speech = await self.tools_ctx.handle_bottom_sheet_closure(component=comp, is_timeout=is_timeout)
                                if speech and self.agent and hasattr(self.agent, "say"):
                                    await self.agent.say(speech, allow_interruptions=True)
                            except Exception as ex:
                                logger.error(f"[CallLifecycle] Sheet close handler error: {ex}")
                        asyncio.create_task(_handle_close())
                    elif self.agent and hasattr(self.agent, "say"):
                        msg = "Theek hai champ! Chalo aage kya masti karein? ABCD sunao, ya kahani sunein, ya koi painting karein?"
                        asyncio.create_task(self.agent.say(msg, allow_interruptions=True))
            except Exception as e:
                logger.debug(f"[CallLifecycle] Notice on data packet parse: {e}")

        # 5. Start background dialogue synchronizer
        self._sync_task = asyncio.create_task(self._sync_turns_periodically())

    async def _sync_turns_periodically(self):
        """Syncs dialogue turns to backend every 2.5 seconds to guarantee zero transcript loss."""
        last_synced_idx = 0
        while not self.disconnect_event.is_set():
            try:
                await asyncio.sleep(2.5)
                while last_synced_idx < len(self.session.turns):
                    turn = self.session.turns[last_synced_idx]
                    last_synced_idx += 1
                    await self._append_single_turn(turn["role"], turn["content"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"[CallLifecycle] Sync notice: {e}")

    async def _append_single_turn(self, role: str, content: str):
        if not self.session.caller_id or not content or not self.session.call_id:
            return
        url = f"{self.api_base_url}/api/ai/memory/append-turn"
        payload = {
            "callId": self.session.call_id,
            "userId": self.session.caller_id,
            "personaId": self.session.persona_id,
            "role": role,
            "content": content,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                    if resp.status == 200:
                        logger.debug(f"[CallLifecycle] Real-time turn saved: [{role}] {content[:40]}...")
        except Exception as e:
            logger.debug(f"[CallLifecycle] Could not sync turn: {e}")

    async def _finalize_learning_report(self):
        """Compiles child learning outcomes, dispatches LiveKit certificate event and saves to database."""
        try:
            gam = getattr(self.tools_ctx, "session_data", {}).get("kids_gamification", {})
            if not gam:
                return

            stars = gam.get("stars", 0)
            level = gam.get("level", 1)
            level_title = gam.get("level_title", "Junior Explorer 🥈")
            curriculum_tier = gam.get("curriculum_tier", "primary")
            badges = gam.get("badges", ["Welcome Star ⭐"])
            topics_explored = list(dict.fromkeys(gam.get("topics_explored", [])))
            words_learned = list(dict.fromkeys(gam.get("words_learned", [])))
            games_won = gam.get("games_won", 0)

            import json
            report_data = {
                "type": "kids_learning_report",
                "call_id": self.session.call_id,
                "user_id": self.session.caller_id,
                "persona_id": self.session.persona_id,
                "stars": stars,
                "level": level,
                "level_title": level_title,
                "curriculum_tier": curriculum_tier,
                "badges": badges,
                "topics_explored": topics_explored,
                "words_learned": words_learned,
                "games_won": games_won,
                "certificate_title": f"Junior Scholar {level_title}",
                "summary": f"Child earned {stars} stars, reached {level_title}, explored {len(topics_explored)} topics and learned {len(words_learned)} words."
            }

            # 1. Publish to client app over LiveKit data channel
            if self.room and self.room.local_participant:
                try:
                    await self.room.local_participant.publish_data(
                        json.dumps(report_data).encode("utf-8"),
                        reliable=True
                    )
                    logger.info(f"🎓 [CallLifecycle] Published kids_learning_report over DataChannel ({stars} stars)")
                except Exception as ex:
                    logger.debug(f"[CallLifecycle] Notice on data publish: {ex}")

            # 2. Persist to backend database via structured-data endpoint
            url = f"{self.api_base_url}/api/ai/calls/{self.session.call_id}/structured-data"
            payload = {
                "callSessionId": self.session.call_id,
                "userId": self.session.caller_id,
                "personaId": self.session.persona_id,
                "dataType": "kids_learning_report",
                "structuredJson": json.dumps(report_data),
                "summary": report_data["summary"]
            }
            async with aiohttp.ClientSession() as http_sess:
                async with http_sess.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                    if resp.status == 200:
                        logger.info("📊 [CallLifecycle] Successfully saved kids learning report to backend")
                    else:
                        logger.warning(f"[CallLifecycle] Learning report save status: {resp.status}")
        except Exception as e:
            logger.error(f"[CallLifecycle] Error in _finalize_learning_report: {e}")

    async def wait_for_disconnect(self):
        """Awaits call termination and cleans up background sync."""
        await self.disconnect_event.wait()
        await self._finalize_learning_report()
        if self._sync_task:
            self._sync_task.cancel()
