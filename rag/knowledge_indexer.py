"""
rag/knowledge_indexer.py - Automated Structured Knowledge Indexer.
Extracts, formats, and indexes knowledge chunks across:
- common (monuments, landmarks, science facts, weather)
- kids (rhymes, moral stories, learning cards, educational videos, quiz)
- romantic (shayari, love quotes, romantic songs)
- younger (career tech prep, trending music, youth culture)
"""

import os
import json
import logging
from typing import List, Dict, Any
from rag.vector_store import VectorStore

logger = logging.getLogger("rag.indexer")

class KnowledgeIndexer:
    """Builds searchable vector chunks from structured JSON knowledge banks."""

    @classmethod
    def index_all(cls, data_dir: str, vector_store: VectorStore) -> int:
        initial_count = vector_store.count()
        logger.info(f"Starting structured knowledge indexing from {data_dir}...")

        # 1. Common: Places & Landmarks
        cls._index_places(os.path.join(data_dir, "common", "places_landmarks.json"), vector_store)
        # 2. Common: Everyday Knowledge & Curiosity
        cls._index_everyday_knowledge(os.path.join(data_dir, "common", "everyday_knowledge.json"), vector_store)

        # 3. Kids: Learning Cards
        cls._index_learning_cards(os.path.join(data_dir, "kids", "learning_cards.json"), vector_store)
        # 4. Kids: Rhymes
        cls._index_rhymes(os.path.join(data_dir, "kids", "rhymes.json"), vector_store)
        # 5. Kids: Stories
        cls._index_stories(os.path.join(data_dir, "kids", "stories.json"), vector_store)
        # 6. Kids: Educational Videos
        cls._index_kids_videos(os.path.join(data_dir, "kids", "kids_videos.json"), vector_store)
        # 7. Kids: Quiz Questions
        cls._index_quiz_bank(os.path.join(data_dir, "kids", "quiz_bank.json"), vector_store)
        # 7b. Kids: Curiosity & Why Questions Bank
        cls._index_curiosity_bank(os.path.join(data_dir, "kids", "curiosity_bank.json"), vector_store)
        # 7c. Kids: Riddles & Paheliyan Bank
        cls._index_riddles_bank(os.path.join(data_dir, "kids", "riddles_bank.json"), vector_store)
        # 7d. Kids: Good Habits & Etiquette Bank
        cls._index_good_habits(os.path.join(data_dir, "kids", "good_habits.json"), vector_store)
        # 7e. Kids: Roleplay Missions Bank
        cls._index_roleplay_missions(os.path.join(data_dir, "kids", "roleplay_missions.json"), vector_store)
        # 7f. Kids: Full Hindi Varnamala (52 letters)
        cls._index_varnamala(os.path.join(data_dir, "kids", "hindi_varnamala_full.json"), vector_store)
        # 7g. Kids: Full Alphabets (A to Z)
        cls._index_alphabets(os.path.join(data_dir, "kids", "alphabet_a_to_z_full.json"), vector_store)
        # 7h. Kids: 1 to 100 Counting
        cls._index_counting(os.path.join(data_dir, "kids", "counting_1_to_100_full.json"), vector_store)
        # 7i. Kids: Good Habits vs Bad Habits
        cls._index_good_and_bad_habits(os.path.join(data_dir, "kids", "habits_good_and_bad.json"), vector_store)
        # 7j. Kids: 365 Daily Quotes
        cls._index_daily_quotes(os.path.join(data_dir, "kids", "daily_quotes_365.json"), vector_store)

        # 8. Romantic: Shayari & Poetry
        cls._index_shayari(os.path.join(data_dir, "romantic", "shayari_and_poetry.json"), vector_store)
        # 9. Romantic: Romantic Songs
        cls._index_romantic_songs(os.path.join(data_dir, "romantic", "romantic_songs.json"), vector_store)

        # 10. Younger: Career & Tech Prep
        cls._index_career_tech(os.path.join(data_dir, "younger", "career_tech_prep.json"), vector_store)
        # 11. Younger: Trending Songs
        cls._index_trending_songs(os.path.join(data_dir, "younger", "trending_songs.json"), vector_store)

        total_indexed = vector_store.count() - initial_count
        logger.info(f"Indexing complete. {total_indexed} total vector chunks indexed across all domains.")
        return total_indexed

    @staticmethod
    def _safe_load(filepath: str) -> Any:
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            return None

    @classmethod
    def _index_places(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for item in data:
            name = item.get("name", "")
            city = item.get("city", "")
            desc = item.get("description", "")
            h_desc = item.get("hindi_description", "")
            text = f"Landmark monument: {name} in {city}, {item.get('state', '')}. Built by {item.get('built_by', '')}. {desc} {h_desc}"
            store.add_document(
                doc_id=item.get("id", f"place_{name}"),
                text=text,
                category="common",
                metadata={"type": "place", "name": name, "city": city, "photo_url": item.get("photo_url")}
            )

    @classmethod
    def _index_everyday_knowledge(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for item in data:
            q = item.get("question", "")
            ans = item.get("answer", "")
            store.add_document(
                doc_id=item.get("id", f"fact_{q[:15]}"),
                text=f"Question: {q} Answer: {ans}",
                category="common",
                metadata={"type": "knowledge", "topic": item.get("topic", "general")}
            )

    @classmethod
    def _index_learning_cards(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for card in data:
            text = f"{card.get('name_en')} ({card.get('name_hi')}) - Category: {card.get('category')}. Fact: {card.get('fact_hi')} {card.get('fact_en')}"
            store.add_document(
                doc_id=card.get("id", f"card_{card.get('name_en')}"),
                text=text,
                category="kids",
                metadata={"type": "learning_card", "category": card.get("category"), "name": card.get("name_en")}
            )

    @classmethod
    def _index_rhymes(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for rhyme in data:
            lines = " ".join(rhyme.get("lines", []))
            text = f"Rhyme: {rhyme.get('title')} ({rhyme.get('language')}). Lyrics: {lines}"
            store.add_document(
                doc_id=rhyme.get("id", f"rhyme_{rhyme.get('title')}"),
                text=text,
                category="kids",
                metadata={"type": "rhyme", "title": rhyme.get("title"), "language": rhyme.get("language")}
            )

    @classmethod
    def _index_stories(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for s in data:
            paras = " ".join(s.get("paragraphs", []))
            moral = s.get("moral_hi") or s.get("moral_en") or ""
            text = f"Story: {s.get('title')} - Moral: {moral}. {paras}"
            store.add_document(
                doc_id=s.get("id", f"story_{s.get('title')}"),
                text=text,
                category="kids",
                metadata={"type": "story", "title": s.get("title"), "moral": moral}
            )

    @classmethod
    def _index_kids_videos(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for v in data:
            text = f"Kids educational video: {v.get('title')} - Topic: {v.get('topic')}. {v.get('description')}"
            store.add_document(
                doc_id=v.get("id", f"vid_{v.get('title')}"),
                text=text,
                category="kids",
                metadata={"type": "video", "title": v.get("title"), "topic": v.get("topic"), "video_url": v.get("video_url"), "thumbnail_url": v.get("thumbnail_url")}
            )

    @classmethod
    def _index_quiz_bank(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for q in data:
            opts = " ".join(q.get("options", []))
            text = f"Quiz Question: {q.get('question')} Options: {opts}"
            store.add_document(
                doc_id=f"quiz_{q.get('id', '')}",
                text=text,
                category="kids",
                metadata={"type": "quiz", "question": q.get("question")}
            )

    @classmethod
    def _index_shayari(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for s in data:
            lines = " ".join(s.get("lines", []))
            text = f"Romantic Shayari / Poetry: {lines} {s.get('transliteration', '')} Theme: {s.get('theme', '')}"
            store.add_document(
                doc_id=s.get("id", f"shayari_{s.get('theme')}"),
                text=text,
                category="romantic",
                metadata={"type": "shayari", "theme": s.get("theme"), "mood": s.get("mood")}
            )

    @classmethod
    def _index_romantic_songs(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for song in data:
            text = f"Romantic Hindi Song: {song.get('title')} by {song.get('singer')} from movie {song.get('movie')}. Lyrics hook: {song.get('lyrics_hook')}"
            store.add_document(
                doc_id=song.get("id", f"song_{song.get('title')}"),
                text=text,
                category="romantic",
                metadata={"type": "song", "title": song.get("title"), "singer": song.get("singer"), "stream_url": song.get("stream_url"), "thumbnail_url": song.get("thumbnail_url")}
            )

    @classmethod
    def _index_career_tech(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for c in data:
            text = f"Career & Tech topic: {c.get('topic')} for {c.get('category')}. Summary: {c.get('summary')} Interview tip: {c.get('interview_tip')}"
            store.add_document(
                doc_id=c.get("id", f"tech_{c.get('topic')}"),
                text=text,
                category="younger",
                metadata={"type": "career_tech", "topic": c.get("topic")}
            )

    @classmethod
    def _index_trending_songs(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for song in data:
            text = f"Trending Music Song: {song.get('title')} by {song.get('singer')}. Genre: {song.get('genre')}"
            store.add_document(
                doc_id=song.get("id", f"song_{song.get('title')}"),
                text=text,
                category="younger",
                metadata={"type": "song", "title": song.get("title"), "singer": song.get("singer"), "stream_url": song.get("stream_url"), "thumbnail_url": song.get("thumbnail_url")}
            )

    @classmethod
    def _index_curiosity_bank(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for c in data:
            kw = " ".join(c.get("keywords", []))
            text = f"Kids Curiosity Question: {c.get('question')} English: {c.get('english_question')} Answer: {c.get('simple_explanation')} Metaphor: {c.get('metaphor_story')} Fun Fact: {c.get('fun_fact')} Keywords: {kw}"
            store.add_document(
                doc_id=f"curiosity_{c.get('id', '')}",
                text=text,
                category="kids",
                metadata={"type": "curiosity", "question": c.get("question"), "image_url": c.get("image_url"), "speech": c.get("speech")}
            )

    @classmethod
    def _index_riddles_bank(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for r in data:
            opts = " ".join(r.get("options", []))
            text = f"Kids Hindi Paheli Riddle: {r.get('riddle')} English: {r.get('english')} Answer: {r.get('correct_option')} Options: {opts} Hint: {r.get('hint')}"
            store.add_document(
                doc_id=f"riddle_{r.get('id', '')}",
                text=text,
                category="kids",
                metadata={"type": "riddle", "riddle": r.get("riddle"), "correct_option": r.get("correct_option"), "options": r.get("options"), "image_url": r.get("image_url")}
            )

    @classmethod
    def _index_good_habits(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for h in data:
            kw = " ".join(h.get("keywords", []))
            text = f"Kids Good Habit / Etiquette: {h.get('title')} Rule: {h.get('rule')} Rhyme: {h.get('rhyme')} Fun Fact: {h.get('fun_fact')} Keywords: {kw}"
            store.add_document(
                doc_id=f"habit_{h.get('id', '')}",
                text=text,
                category="kids",
                metadata={"type": "good_habit", "title": h.get("title"), "speech": h.get("speech"), "image_url": h.get("image_url")}
            )

    @classmethod
    def _index_roleplay_missions(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for m in data:
            kw = " ".join(m.get("keywords", []))
            step_texts = " ".join([s.get("instruction", "") for s in m.get("steps", [])])
            text = f"Kids Interactive Roleplay Adventure: {m.get('title')} Role AI: {m.get('role_ai')} Role Child: {m.get('role_child')} Steps: {step_texts} Keywords: {kw}"
            store.add_document(
                doc_id=f"roleplay_{m.get('id', '')}",
                text=text,
                category="kids",
                metadata={"type": "roleplay", "title": m.get("title"), "image_url": m.get("image_url")}
            )

    @classmethod
    def _index_varnamala(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, dict): return
        for letter, v in data.items():
            text = f"Hindi Varnamala Letter: {v.get('letter')} Word: {v.get('word')} English: {v.get('english')} Fun fact: {v.get('fun_fact')}"
            store.add_document(
                doc_id=f"varnamala_{letter}",
                text=text,
                category="kids",
                metadata={"type": "varnamala", "letter": letter, "word": v.get("word"), "speech": v.get("speech")}
            )

    @classmethod
    def _index_alphabets(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, dict): return
        for char, a in data.items():
            text = f"English Alphabet Phonics: {a.get('letter')} Word: {a.get('word')} Hindi meaning: {a.get('hindi_meaning')} Phonics: {a.get('phonics')} Fun fact: {a.get('fun_fact')}"
            store.add_document(
                doc_id=f"alphabet_{char.lower()}",
                text=text,
                category="kids",
                metadata={"type": "alphabet", "letter": char, "word": a.get("word"), "speech": a.get("speech")}
            )

    @classmethod
    def _index_counting(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for n in data:
            text = f"Number Counting: {n.get('number')} English: {n.get('english_name')} Hindi: {n.get('hindi_name')} ({n.get('roman_hindi')}) Group: {n.get('tens_group')}"
            store.add_document(
                doc_id=f"counting_{n.get('number')}",
                text=text,
                category="kids",
                metadata={"type": "counting", "number": n.get("number"), "speech": n.get("speech")}
            )

    @classmethod
    def _index_good_and_bad_habits(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for h in data:
            kw = " ".join(h.get("keywords", []))
            text = f"Good Habit vs Bad Habit: {h.get('title')} Good Habit: {h.get('good_habit')} Bad Habit: {h.get('bad_habit')} Why bad: {h.get('why_bad')} Rule: {h.get('kid_rule')} Keywords: {kw}"
            store.add_document(
                doc_id=f"habit_pair_{h.get('id')}",
                text=text,
                category="kids",
                metadata={"type": "habit_comparison", "title": h.get("title"), "good": h.get("good_habit"), "bad": h.get("bad_habit")}
            )

    @classmethod
    def _index_daily_quotes(cls, filepath: str, store: VectorStore):
        data = cls._safe_load(filepath)
        if not isinstance(data, list): return
        for q in data:
            text = f"Kids Daily Quote Day {q.get('day')} ({q.get('date')}): {q.get('quote_english')} Hindi: {q.get('quote_hindi')} Author: {q.get('author_or_character')} Theme: {q.get('theme')} Mission: {q.get('kid_takeaway')}"
            store.add_document(
                doc_id=f"quote_day_{q.get('day')}",
                text=text,
                category="kids",
                metadata={"type": "daily_quote", "day": q.get("day"), "date": q.get("date"), "author": q.get("author_or_character")}
            )
