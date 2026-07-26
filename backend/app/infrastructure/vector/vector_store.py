"""
Vector Store Operations.

Storage and retrieval of vector
embeddings for similarity search.
"""

from __future__ import annotations


class VectorStore:
    """Stores and queries vector embeddings."""

    def insert(self, vector: list[float], metadata: dict) -> None:
        """Insert a vector with metadata."""
        raise NotImplementedError

    def search(self, query: list[float], top_k: int = 10) -> list[dict]:
        """Search for similar vectors."""
        raise NotImplementedError
