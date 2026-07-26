"""
4-Layer Search Pipeline.

Progressive search: Think → Obsidian → Skills → Web.
Each layer only activates if the previous one
didn't find enough results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.perception.context.vault import (
    ObsidianVault,
    ObsidianNote,
)

from app.cognition.world_model.graph import (
    KnowledgeGraph,
)

from app.action.tool_system.web_search import (
    WebSearchService,
    WebSearchResult,
)

from app.skill.manager import SkillManager
from app.skill.base import Skill


@dataclass
class SearchResult:
    """Aggregated result from all search layers."""

    obsidian_notes: list[ObsidianNote] = field(
        default_factory=list,
    )
    graph_results: list[dict] = field(
        default_factory=list,
    )
    matched_skills: list[Skill] = field(
        default_factory=list,
    )
    web_results: list[WebSearchResult] = field(
        default_factory=list,
    )
    layers_used: list[str] = field(
        default_factory=list,
    )
    combined_context: str = ""


class SearchPipeline:
    """
    Orchestrates progressive search across layers.

    Layer 1: Think — No-op for now; future versions
              can use LLM to refine the query.

    Layer 2: Obsidian — Search local knowledge base.

    Layer 3: Skills — Check for matching skills.
              (Future: load skill if found.)

    Layer 4: Web — Search the internet as last resort.
    """

    def __init__(
        self,
        vault: ObsidianVault,
        web_search: WebSearchService | None = None,
        skill_manager: SkillManager | None = None,
    ) -> None:
        self._vault = vault
        self._web_search = web_search
        self._skill_manager = skill_manager or SkillManager()
        self._graph: KnowledgeGraph | None = None

    @property
    def graph(self) -> KnowledgeGraph:
        if self._graph is None:
            self._graph = self._vault.graph
        return self._graph

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def search(
        self,
        query: str,
        *,
        min_obsidian_results: int = 2,
        max_web_results: int = 4,
    ) -> SearchResult:
        """
        Execute a progressive 4-layer search.

        Returns aggregated results from all
        layers that were activated.
        """

        layers_used: list[str] = []
        obsidian_notes: list[ObsidianNote] = []
        graph_results: list[dict] = []
        matched_skills: list[Skill] = []
        web_results: list[WebSearchResult] = []

        # Layer 1: Think — future: query refinement
        layers_used.append("think")

        # Layer 2: Obsidian keyword search
        obsidian_notes = self._search_obsidian(query)

        if obsidian_notes:
            layers_used.append("obsidian")

        # Layer 2b: Vector graph search (semantic)
        graph_results = self._search_graph(query)

        if graph_results:
            layers_used.append("graph")

            # Merge graph results into obsidian_notes
            graph_paths = {
                r["path"] for r in graph_results
            }
            obsidian_paths = {
                n.path for n in obsidian_notes
            }

            # Add graph-only results
            if graph_paths - obsidian_paths:
                layers_used.append("graph")

        # Layer 3: Skills
        matched_skills = self._skill_manager.find_matching(
            query,
        )

        if matched_skills:
            layers_used.append("skills")

        # Layer 4: Web (only if not enough Obsidian results)
        if len(obsidian_notes) < min_obsidian_results:

            if self._web_search is not None:

                web_results = self._web_search.search(
                    query,
                    max_results=max_web_results,
                )

                if web_results:
                    layers_used.append("web")

        # Build combined context
        combined = self._build_context(
            obsidian_notes=obsidian_notes,
            matched_skills=matched_skills,
            web_results=web_results,
        )

        return SearchResult(
            obsidian_notes=obsidian_notes,
            graph_results=graph_results,
            matched_skills=matched_skills,
            web_results=web_results,
            layers_used=layers_used,
            combined_context=combined,
        )

    # --------------------------------------------------
    # Layer 2: Obsidian
    # --------------------------------------------------

    def _search_obsidian(
        self,
        query: str,
        *,
        max_notes: int = 5,
    ) -> list[ObsidianNote]:
        """Search the Obsidian vault for relevant notes."""

        keywords = self._extract_keywords(query)

        seen: set[str] = set()
        results: list[ObsidianNote] = []

        for keyword in keywords:
            if len(results) >= max_notes:
                break

            hits = self._vault.search_by_keyword(
                keyword,
                max_results=max_notes,
            )

            for note in hits:
                if note.name not in seen:
                    seen.add(note.name)
                    results.append(note)

        return results[:max_notes]

    # --------------------------------------------------
    # Context building
    # --------------------------------------------------

    # --------------------------------------------------
    # Layer 2b: Graph / Vector Search
    # --------------------------------------------------

    def _search_graph(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Semantic search using the knowledge graph.

        Falls back to keyword search if the graph
        is empty (no notes indexed yet).
        """

        graph = self.graph

        if graph.node_count == 0:
            return []

        return graph.search_similar(
            query,
            top_k=top_k,
        )

    @staticmethod
    def _build_context(
        *,
        obsidian_notes: list[ObsidianNote],
        matched_skills: list[Skill] | None = None,
        web_results: list[WebSearchResult],
    ) -> str:
        """Combine all search results into a single context."""

        parts: list[str] = []

        # Obsidian notes
        if obsidian_notes:
            note_sections: list[str] = []

            for note in obsidian_notes:
                tag_str = (
                    ", ".join(note.tags)
                    if note.tags
                    else "(no tags)"
                )

                note_sections.append(
                    f"### {note.name}\n"
                    f"Tags: {tag_str}\n\n"
                    f"{note.content[:1000]}"
                )

            parts.append(
                "## Obsidian 知识库\n\n"
                + "\n\n---\n\n".join(note_sections)
            )

        # Skills
        if matched_skills:
            skill_sections: list[str] = [
                "## 可用技能\n"
            ]

            for skill in matched_skills:
                desc = skill.metadata.description[:200]
                skill_sections.append(
                    f"### {skill.metadata.name}\n"
                    f"{desc}\n"
                )

            parts.append(
                "\n".join(skill_sections)
            )

        # Web results
        if web_results:
            web_sections: list[str] = [
                "## 网络搜索结果\n"
            ]

            for i, r in enumerate(web_results, 1):
                web_sections.append(
                    f"### [{i}] {r.title}\n"
                    f"来源: {r.url}\n\n"
                    f"{r.snippet[:300]}\n"
                )

            parts.append(
                "\n\n---\n\n".join(web_sections)
            )

        return "\n\n---\n\n".join(parts)

    # --------------------------------------------------
    # Keyword extraction (moved from orchestrator)
    # --------------------------------------------------

    @staticmethod
    def _extract_keywords(message: str) -> list[str]:
        """Extract meaningful keywords from a message."""

        import re

        words = re.split(
            r"[\s,，。.！!？?、/\\()（）\[\]]+",
            message,
        )

        stop_words = {
            "的", "了", "在", "是", "我", "有", "和",
            "就", "不", "人", "都", "一", "一个", "上",
            "也", "很", "到", "说", "要", "去", "你",
            "会", "着", "没有", "看", "好", "自己",
            "the", "a", "an", "is", "are", "was",
            "to", "in", "for", "of", "on", "and",
            "or", "but", "at", "by", "with", "from",
        }

        keywords = [
            w.strip().lower()
            for w in words
            if len(w.strip()) >= 2
            and w.strip().lower() not in stop_words
        ]

        return keywords or [message]
