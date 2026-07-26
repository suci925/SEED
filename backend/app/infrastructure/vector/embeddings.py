"""
Embedding Generation.

Interface for converting text
into vector embeddings.
"""

from __future__ import annotations


class EmbeddingModel:
    """Generates vector embeddings from text."""

    def embed(self, text: str) -> list[float]:
        """Convert text to an embedding vector."""
        raise NotImplementedError
