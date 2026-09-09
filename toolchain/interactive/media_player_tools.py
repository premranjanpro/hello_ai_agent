"""
toolchain/interactive/media_player_tools.py - Multimodal Video & Song Player Toolchain.
Emits interactive LiveKit DataChannel payloads to launch educational videos,
Hindi songs, audio equalizer visualizers, and RAG knowledge lookups on the caller's device.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from livekit.agents import llm
from rag import RagRetriever

logger = logging.getLogger("tools.media_player")

class MediaPlayerToolsMixin:
    """Toolchain mixin for triggering interactive video and song players in bottom sheet."""

    @classmethod
    def _load_json_bank(cls, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Failed to load media bank {filepath}: {e}")
            return []

    async def _emit_sheet_payload(self, payload: Dict[str, Any]):
        """Publishes interactive sheet event over LiveKit DataChannel."""
        room = getattr(self, "room", None)
        if not room:
            logger.warning("No room available to emit media player interactive sheet.")
            return

        try:
            raw_bytes = json.dumps(payload).encode("utf-8")
            await room.local_participant.publish_data(raw_bytes, reliable=True)
            logger.info(f"📺 [MediaPlayer] Published {payload.get('media_type', 'media')} sheet: {payload.get('title')}")
        except Exception as e:
            logger.error(f"Failed to broadcast media sheet payload: {e}")

    @llm.ai_callable(
        description="Play an educational or fun cartoon video for kids (e.g. ABC phonics, Chanda Mama, Counting train, Solar system, Thirsty crow story) in the interactive bottom sheet."
    )
    async def play_educational_video(self, topic: str = "", video_title: str = "") -> str:
        """Plays kid-friendly video with thumbnail and video container in the bottom sheet."""
        agent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        bank_path = os.path.join(agent_dir, "data", "kids", "kids_videos.json")
        videos = self._load_json_bank(bank_path)

        selected = None
        if video_title:
            q = video_title.lower().strip()
            selected = next((v for v in videos if q in v.get("title", "").lower()), None)
        if not selected and topic:
            q = topic.lower().strip()
            selected = next((v for v in videos if q in v.get("topic", "").lower() or q in v.get("title", "").lower()), None)
        if not selected and videos:
            selected = videos[0]

        if not selected:
            return "Kshama kijiye, abhi ye video uplabdh nahi hai."

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "media_player",
            "media_type": "video",
            "sheet_id": f"vid_{selected.get('id')}",
            "title": selected.get("title"),
            "topic": selected.get("topic"),
            "duration": selected.get("duration", "3:00"),
            "video_url": selected.get("video_url"),
            "youtube_id": selected.get("youtube_id"),
            "thumbnail_url": selected.get("thumbnail_url"),
            "description": selected.get("description", ""),
            "actions": [
                {"id": "next_video", "label": "Next Video ➡️", "action": "next_video"},
                {"id": "close_media", "label": "Close Video ✖️", "action": "close"}
            ]
        }

        await self._emit_sheet_payload(sheet_payload)
        return (
            f"Maine screen par '{selected.get('title')}' video chala di hai! "
            f"Aap ise enjoy kijiye, main yahin aapke saath baat karne ke liye taiyar hoon!"
        )

    @llm.ai_callable(
        description="Play a requested Hindi song, romantic melody, or trending music (e.g. Kesariya, Tum Hi Ho, Raataan Lambiyan, Softly, Cheques) with interactive audio visualizer."
    )
    async def play_song(self, song_name: str = "", genre: str = "romantic") -> str:
        """Plays music stream with animated equalizer visualizer in the bottom sheet."""
        agent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if genre.lower() in ["trending", "pop", "party", "rap"]:
            bank_path = os.path.join(agent_dir, "data", "younger", "trending_songs.json")
        else:
            bank_path = os.path.join(agent_dir, "data", "romantic", "romantic_songs.json")

        songs = self._load_json_bank(bank_path)
        if not songs:
            # Fallback to romantic songs
            bank_path = os.path.join(agent_dir, "data", "romantic", "romantic_songs.json")
            songs = self._load_json_bank(bank_path)

        selected = None
        if song_name:
            q = song_name.lower().strip()
            selected = next((s for s in songs if q in s.get("title", "").lower() or q in s.get("singer", "").lower()), None)
        if not selected and songs:
            selected = songs[0]

        if not selected:
            return "Ye gaana abhi playlist mein nahi mila, koi aur gana sunna chahenge?"

        sheet_payload = {
            "type": "interactive_sheet",
            "action": "open",
            "component": "media_player",
            "media_type": "audio",
            "sheet_id": f"song_{selected.get('id')}",
            "title": selected.get("title"),
            "singer": selected.get("singer", "Unknown"),
            "movie": selected.get("movie", ""),
            "duration": selected.get("duration", "3:30"),
            "stream_url": selected.get("stream_url"),
            "youtube_id": selected.get("youtube_id"),
            "thumbnail_url": selected.get("thumbnail_url"),
            "lyrics_hook": selected.get("lyrics_hook", ""),
            "genre": selected.get("genre", genre),
            "actions": [
                {"id": "next_song", "label": "Dusra Gana 🎵", "action": "next_song"},
                {"id": "close_media", "label": "Stop Music ✖️", "action": "close"}
            ]
        }

        await self._emit_sheet_payload(sheet_payload)
        return (
            f"Aapke liye '{selected.get('title')}' by {selected.get('singer')} play kar diya hai. "
            f"Screen par equalizer chal raha hai. Aap jab chahein bottom sheet band kar sakte hain, main yahin hoon!"
        )

    @llm.ai_callable(
        description="Search the structured RAG knowledge base for places, monuments, science facts, rhymes, stories, or interview topics."
    )
    async def search_knowledge_base(self, query: str, category: str = "common") -> str:
        """Retrieves semantic information from the structured knowledge base."""
        retriever = RagRetriever.get_instance()
        context = retriever.retrieve_context_str(query, category=category, top_k=2)
        if not context:
            return f"No specific facts found for '{query}' in {category}."
        return f"Retrieved knowledge:\n{context}"
