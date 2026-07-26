"""
Web Search Service.

Wraps the searchpin library to provide
multi-engine web search (Baidu, Bing, Sogou)
for the Seed agent when Obsidian knowledge
is insufficient.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WebSearchResult:
    """A single web search result."""

    title: str
    url: str
    snippet: str
    content: str = ""
    source_engine: str = ""
    rerank_score: float = 0.0


class WebSearchService:
    """
    Multi-engine web search service.

    Uses searchpin to search Baidu, Bing, and Sogou
    with built-in deduplication and semantic reranking.
    Works in Chinese networks without proxy.
    """

    def __init__(self) -> None:
        self._engine: Any = None

    # --------------------------------------------------
    # Lazy initialisation
    # --------------------------------------------------

    @property
    def engine(self) -> Any:
        """Lazy-load the search engine on first use."""

        if self._engine is None:
            from searchpin import SearchEngine

            self._engine = SearchEngine()

        return self._engine

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> list[WebSearchResult]:
        """
        Search the web for a query.

        Args:
            query: Search keywords.
            max_results: Max results to return.

        Returns:
            List of WebSearchResult, already
            deduplicated and reranked by relevance.
        """

        raw = self.engine.search(
            query,
            max_results=max_results,
        )

        if not isinstance(raw, dict):
            return []

        raw_results = raw.get("results", [])

        return [
            WebSearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("snippet", ""),
                content=r.get("content", ""),
                source_engine=r.get(
                    "_source_engine", ""
                ),
                rerank_score=r.get(
                    "_rerank_score", 0.0
                ),
            )
            for r in raw_results
        ]

    # --------------------------------------------------
    # Format for Agent context
    # --------------------------------------------------

    @staticmethod
    def format_for_context(
        results: list[WebSearchResult],
        *,
        max_snippet_len: int = 300,
    ) -> str:
        """
        Format search results as a context string
        for the LLM prompt.
        """

        if not results:
            return ""

        lines: list[str] = [
            "## 网络搜索结果\n"
        ]

        for i, r in enumerate(results, 1):
            lines.append(
                f"### [{i}] {r.title}\n"
                f"来源: {r.url}\n\n"
                f"{r.snippet[:max_snippet_len]}\n"
            )

        return "\n\n".join(lines)

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self) -> None:
        """Release search engine resources."""

        if self._engine is not None:
            try:
                self._engine.close()
            except Exception:
                pass
            self._engine = None
