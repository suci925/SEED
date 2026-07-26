"""
Local Vector Embeddings.

Uses fastembed for on-device embedding generation.
No API calls, no GPU required, ~90MB model.
"""

from __future__ import annotations

from functools import lru_cache
from math import sqrt

from fastembed import TextEmbedding


# Chinese-optimized small model (512 dim, ~90MB)
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"


class EmbeddingEngine:
    """
    Generates and compares vector embeddings locally.

    Uses fastembed with a Chinese-optimized model
    for multilingual content.
    """

    def __init__(
        self,
        model_name: str = EMBED_MODEL,
    ) -> None:
        self._model_name = model_name
        self._model: TextEmbedding | None = None

    # --------------------------------------------------
    # Lazy load
    # --------------------------------------------------

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(
                model_name=self._model_name,
            )
        return self._model

    # --------------------------------------------------
    # Embed
    # --------------------------------------------------

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding vector for a text.
        """
        results = list(self.model.embed(text))
        return results[0].tolist()

    @property
    def dimension(self) -> int:
        """Embedding vector dimension."""
        sample = self.embed("")
        return len(sample)

    # --------------------------------------------------
    # Similarity
    # --------------------------------------------------

    @staticmethod
    def cosine_similarity(
        a: list[float],
        b: list[float],
    ) -> float:
        """
        Cosine similarity between two vectors.
        Returns 0.0 - 1.0.
        """
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    # --------------------------------------------------
    # Batch
    # --------------------------------------------------

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Embed multiple texts efficiently.
        """
        results = list(self.model.embed(texts))
        return [r.tolist() for r in results]
