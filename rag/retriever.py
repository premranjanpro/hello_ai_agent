"""
rag/retriever.py - High-Performance RAG Semantic Retrieval Engine.
Serves as the unified retrieval layer for LLM prompts, tool execution, and dynamic context injection.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from rag.embeddings import FastSemanticEmbedder
from rag.vector_store import VectorStore
from rag.knowledge_indexer import KnowledgeIndexer

logger = logging.getLogger("rag.retriever")

class RagRetriever:
    """Singleton RAG Retriever with in-memory semantic search."""

    _instance: Optional["RagRetriever"] = None

    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            agent_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(agent_root, "data")
        self.data_dir = data_dir
        self.embedder = FastSemanticEmbedder()
        self.store = VectorStore(self.embedder)
        self.is_indexed = False
        self._initialize()

    @classmethod
    def get_instance(cls, data_dir: Optional[str] = None) -> "RagRetriever":
        if cls._instance is None:
            cls._instance = cls(data_dir)
        return cls._instance

    def _initialize(self):
        """Indexes structured data directories on startup."""
        if not self.is_indexed:
            try:
                count = KnowledgeIndexer.index_all(self.data_dir, self.store)
                self.is_indexed = True
                logger.info(f"[RagRetriever] Initialized with {count} structured chunks.")
            except Exception as e:
                logger.error(f"[RagRetriever] Indexing failed: {e}")

    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3,
        min_score: float = 0.08
    ) -> List[Dict[str, Any]]:
        """Performs fast semantic cosine similarity search."""
        if not query:
            return []
        return self.store.similarity_search(query, category=category, top_k=top_k, min_score=min_score)

    def retrieve_context_str(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 2
    ) -> str:
        """Returns clean formatted knowledge string ready for injection into prompt."""
        matches = self.retrieve(query, category=category, top_k=top_k)
        if not matches:
            return ""

        chunks = []
        for idx, m in enumerate(matches, 1):
            text = m.get("text", "").strip()
            cat = m.get("category", "")
            chunks.append(f"[{cat.upper()} KNOWLEDGE #{idx}]: {text}")

        return "\n".join(chunks)
