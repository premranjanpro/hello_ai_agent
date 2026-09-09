"""
rag/vector_store.py - High-Performance In-Memory Categorized Vector Database.
Supports cosine similarity search across categories ('common', 'kids', 'romantic', 'younger', 'family').
"""

import json
import logging
from typing import List, Dict, Any, Optional
from rag.embeddings import FastSemanticEmbedder

logger = logging.getLogger("rag.vector_store")

class DocumentChunk:
    def __init__(
        self,
        doc_id: str,
        text: str,
        category: str,
        metadata: Dict[str, Any],
        vector: Optional[List[float]] = None
    ):
        self.doc_id = doc_id
        self.text = text
        self.category = category.lower().strip()
        self.metadata = metadata
        self.vector = vector or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "text": self.text,
            "category": self.category,
            "metadata": self.metadata,
            "vector": self.vector
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        return cls(
            doc_id=data["doc_id"],
            text=data["text"],
            category=data.get("category", "common"),
            metadata=data.get("metadata", {}),
            vector=data.get("vector", [])
        )


class VectorStore:
    """In-memory cosine-similarity vector store with category segregation."""

    def __init__(self, embedder: Optional[FastSemanticEmbedder] = None):
        self.embedder = embedder or FastSemanticEmbedder()
        self.documents: List[DocumentChunk] = []

    def add_document(
        self,
        doc_id: str,
        text: str,
        category: str = "common",
        metadata: Optional[Dict[str, Any]] = None,
        vector: Optional[List[float]] = None
    ):
        """Adds a single document chunk into the vector store."""
        if not vector:
            vector = self.embedder.embed_text(text)
        chunk = DocumentChunk(doc_id, text, category, metadata or {}, vector)
        self.documents.append(chunk)

    def add_documents(self, docs: List[Dict[str, Any]]):
        """Batch add document dictionaries: [{doc_id, text, category, metadata}]."""
        for d in docs:
            self.add_document(
                doc_id=d["doc_id"],
                text=d["text"],
                category=d.get("category", "common"),
                metadata=d.get("metadata", {}),
                vector=d.get("vector")
            )

    def similarity_search(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3,
        min_score: float = 0.05
    ) -> List[Dict[str, Any]]:
        """Finds top-k most similar documents using cosine similarity."""
        if not query or not self.documents:
            return []

        query_vec = self.embedder.embed_text(query)
        scored_results = []
        target_cat = category.lower().strip() if category else None

        for doc in self.documents:
            # Filter by category if specified (or 'all')
            if target_cat and target_cat != "all" and doc.category != target_cat:
                continue

            score = self.embedder.cosine_similarity(query_vec, doc.vector)
            if score >= min_score:
                scored_results.append({
                    "score": round(score, 4),
                    "doc_id": doc.doc_id,
                    "category": doc.category,
                    "text": doc.text,
                    "metadata": doc.metadata
                })

        # Sort descending by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def count(self) -> int:
        return len(self.documents)

    def save_index(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            data = [d.to_dict() for d in self.documents]
            json.dump(data, f, ensure_ascii=False)
        logger.info(f"Vector store index saved ({len(self.documents)} docs) -> {filepath}")

    def load_index(self, filepath: str) -> bool:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents = [DocumentChunk.from_dict(d) for d in data]
            logger.info(f"Vector store index loaded ({len(self.documents)} docs) from {filepath}")
            return True
        except Exception as e:
            logger.warning(f"Could not load vector store index from {filepath}: {e}")
            return False
