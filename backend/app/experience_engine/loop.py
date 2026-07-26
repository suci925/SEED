"""
Evolution Loop.

The core learning cycle that runs periodically:
Observe → Reflect → Consolidate → Adapt.

This is what makes Seed grow over time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.types import IdentityID

from app.cognition.world_model.base import LLMProvider

from app.perception.context.vault import (
    ObsidianVault,
)

from app.memory.semantic.graph import (
    KnowledgeGraph,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.repositories.interfaces.experience_repository import (
    ExperienceRepository,
)

from app.memory.repositories.sqlite_experience_repository import (
    SQLiteExperienceRepository,
)

from app.reflection.reflector import (
    Reflector,
    Reflection,
)


class EvolutionLoop:
    """
    Periodic learning cycle.

    Call `.run()` for a full evolution cycle
    or `.tick()` for a lightweight version
    after each conversation.

    Full cycle:
      1. Observe — gather recent experiences
      2. Reflect — LLM analysis of patterns
      3. Consolidate — merge, decay, clean graph
      4. Adapt — write reflection to Obsidian
    """

    # After this many conversations, auto-trigger
    AUTO_REFLECT_INTERVAL = 10

    def __init__(
        self,
        llm: LLMProvider,
        vault: ObsidianVault,
        experience_repo: type[ExperienceRepository] = SQLiteExperienceRepository,
    ) -> None:
        self._llm = llm
        self._vault = vault
        self._experience_repo_cls = experience_repo
        self._experience_repo: ExperienceRepository | None = None
        self._reflector = Reflector(llm=llm)
        self._conversation_count = 0

    def _ensure_repo(
        self,
        session: AsyncSession | None = None,
    ) -> ExperienceRepository:
        """Get or create the experience repo."""
        if self._experience_repo is not None:
            return self._experience_repo
        if session is not None:
            self._experience_repo = self._experience_repo_cls(session)
            return self._experience_repo
        raise ValueError("No session available for EvolutionLoop")

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    async def tick(
        self,
        *,
        session: AsyncSession | None = None,
        owner_id: IdentityID | None = None,
    ) -> EvolutionResult:
        """
        Lightweight evolution after each conversation.

        Only consolidates the graph (no LLM call).
        Every N ticks, auto-triggers a full cycle.
        """

        self._conversation_count += 1

        # Consolidate graph
        graph = self._vault.graph
        decayed = graph.decay_weights()
        graph.save()

        result = EvolutionResult(
            cycle="tick",
            decayed_edges=decayed,
        )

        # Auto-trigger full cycle
        if (
            self._conversation_count
            % self.AUTO_REFLECT_INTERVAL
            == 0
        ):
            full = await self.run(
                session=session,
                owner_id=owner_id,
            )
            result.reflection = full.reflection
            result.cycle = "tick+full"

        return result

    async def run(
        self,
        *,
        session: AsyncSession | None = None,
        owner_id: IdentityID | None = None,
    ) -> EvolutionResult:
        """
        Full evolution cycle.

        Observe → Reflect → Consolidate → Adapt.
        """

        graph = self._vault.graph

        # Ensure we have a repo for this session
        self._ensure_repo(session)

        # 1. Observe
        recent = await self._gather_recent(
            owner_id=owner_id,
        )

        # 2. Reflect (LLM)
        reflection = await self._reflector.reflect(
            recent,
        )

        # 3. Consolidate
        decayed = graph.decay_weights()

        if graph.node_count > 1:
            graph = self._consolidate_graph(graph)

        graph.save()

        # 4. Adapt — write reflection to Obsidian
        note_path = self._write_reflection_note(
            reflection=reflection,
            experience_count=len(recent),
        )

        return EvolutionResult(
            cycle="full",
            reflection=reflection,
            notes_reviewed=len(recent),
            decayed_edges=decayed,
            note_path=note_path,
        )

    # --------------------------------------------------
    # Observe
    # --------------------------------------------------

    async def _gather_recent(
        self,
        *,
        owner_id: IdentityID | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Gather recent experiences for analysis."""

        if owner_id is None:
            return []

        try:
            experiences = (
                await self._experience_repo.list_by_owner(
                    owner_id,
                )
            )
        except Exception:
            return []

        results = []

        for exp in experiences[:limit]:
            results.append(
                {
                    "action": exp.action,
                    "outcome": exp.outcome.value,
                    "lesson": exp.lesson or "",
                    "created_at": (
                        exp.created_at.isoformat()
                        if exp.created_at
                        else ""
                    ),
                }
            )

        return results

    # --------------------------------------------------
    # Consolidate
    # --------------------------------------------------

    def _consolidate_graph(
        self,
        graph: KnowledgeGraph,
    ) -> KnowledgeGraph:
        """
        Consolidate knowledge graph:

        - Find similar nodes (high vector similarity)
        - Merge near-duplicates
        - Strengthen frequently co-accessed edges
        """

        if graph.node_count < 2:
            return graph

        nodes = list(graph._nodes.items())

        for i in range(len(nodes)):
            nid_a, node_a = nodes[i]

            for j in range(i + 1, len(nodes)):
                nid_b, node_b = nodes[j]

                # Calculate similarity
                sim = graph._embedder.cosine_similarity(
                    node_a.get("embedding", [0]),
                    node_b.get("embedding", [0]),
                )

                # If very similar, merge
                if sim > 0.92:
                    self._merge_nodes(
                        graph, nid_a, nid_b
                    )
                    # Re-fetch nodes after merge
                    nodes = list(
                        graph._nodes.items()
                    )
                    break

            else:
                continue
            break

        return graph

    def _merge_nodes(
        self,
        graph: KnowledgeGraph,
        keep_id: str,
        remove_id: str,
    ) -> None:
        """
        Merge two similar nodes into one.

        The kept node retains all edges from both.
        """

        remove_node = graph._nodes.get(remove_id)
        if remove_node is None:
            return

        # Redirect all edges from remove → keep
        for edge in graph._edges:
            if edge["source"] == remove_id:
                edge["source"] = keep_id
                edge["weight"] = min(
                    edge["weight"] * 1.1, 1.0
                )
            if edge["target"] == remove_id:
                edge["target"] = keep_id
                edge["weight"] = min(
                    edge["weight"] * 1.1, 1.0
                )

        # Remove duplicate edges
        seen_pairs: set[tuple[str, str]] = set()
        unique_edges = []

        for edge in graph._edges:
            pair = (edge["source"], edge["target"])

            if edge["source"] == edge["target"]:
                continue

            if pair in seen_pairs:
                continue

            seen_pairs.add(pair)
            unique_edges.append(edge)

        graph._edges = unique_edges
        graph._nodes.pop(remove_id, None)
        graph._dirty = True

    # --------------------------------------------------
    # Adapt — Write reflection
    # --------------------------------------------------

    def _write_reflection_note(
        self,
        *,
        reflection: Reflection,
        experience_count: int,
    ) -> Path | None:
        """Write reflection results to Obsidian."""

        now = datetime.now(timezone.utc).isoformat()
        date_str = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d")

        lines = [
            "---",
            "title: 进化反思",
            f"created: {now}",
            "type: evolution",
            "tags: [seed, evolution, reflection]",
            "---",
            "",
            f"# 进化反思 — {date_str}",
            "",
            f"**回顾了 {experience_count} 次交互**",
            "",
        ]

        if reflection.summary:
            lines.extend(
                ["> " + reflection.summary, ""]
            )

        if reflection.patterns:
            lines.extend(["## 观察到的模式", ""])
            for p in reflection.patterns:
                lines.extend([f"- {p}", ""])

        if reflection.insights:
            lines.extend(["## 洞察", ""])
            for i_text in reflection.insights:
                lines.extend([f"- {i_text}", ""])

        if reflection.improvements:
            lines.extend(["## 改进方向", ""])
            for imp in reflection.improvements:
                lines.extend([f"- {imp}", ""])

        # Write to Obsidian
        evo_dir = self._vault.path / "Evolution"
        evo_dir.mkdir(parents=True, exist_ok=True)

        note_path = (
            evo_dir / f"反思-{date_str}.md"
        )
        note_path.write_text(
            "\n".join(lines), encoding="utf-8"
        )

        return note_path


from dataclasses import dataclass, field
from pathlib import Path

from app.reflection.reflector import (
    Reflection,
)


@dataclass
class EvolutionResult:
    """Result of an evolution cycle."""

    cycle: str = "tick"
    reflection: Reflection | None = None
    notes_reviewed: int = 0
    decayed_edges: int = 0
    note_path: Path | None = None
