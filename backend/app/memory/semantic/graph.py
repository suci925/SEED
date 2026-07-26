"""
Knowledge Graph Engine.

Manages nodes (notes), edges (relationships with weights),
and provides graph-aware search and updates.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.memory.semantic.embeddings import (
    EmbeddingEngine,
)

from app.memory.semantic.relationship import (
    RelationType,
    calculate_weight,
    get_initial_weight,
)


# Graph file stored inside the vault
GRAPH_FILENAME = ".seed-graph.json"


class GraphNode:
    """A note node in the knowledge graph."""

    def __init__(
        self,
        node_id: str,
        path: str,
        node_type: str = "note",
        content: str = "",
    ) -> None:
        self.id = node_id
        self.path = path
        self.node_type = node_type
        self.content = content
        self.embedding: list[float] | None = None
        self.created_at = time.time()
        self.accessed_at = time.time()
        self.access_count = 0


class GraphEdge:
    """A weighted relationship between two nodes."""

    def __init__(
        self,
        source: str,
        target: str,
        rel_type: RelationType = RelationType.RELATED,
        weight: float = 0.5,
    ) -> None:
        self.source = source
        self.target = target
        self.rel_type = rel_type
        self.weight = weight
        self.updated_at = time.time()


class KnowledgeGraph:
    """
    The core knowledge graph for Seed's brain.

    Stores nodes (notes) and edges (relationships)
    with real-time weight updates. Serialized to
    a JSON file inside the Obsidian vault.
    """

    def __init__(
        self,
        vault_path: str | Path,
        embedder: EmbeddingEngine | None = None,
    ) -> None:
        self._vault_path = Path(vault_path)
        self._graph_path = (
            self._vault_path / GRAPH_FILENAME
        )
        self._embedder = embedder or EmbeddingEngine()

        # In-memory graph
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._dirty = False

    # --------------------------------------------------
    # Load / Save
    # --------------------------------------------------

    def load(self) -> None:
        """Load graph from .seed-graph.json."""
        if not self._graph_path.exists():
            self._nodes = {}
            self._edges = []
            return

        try:
            data = json.loads(
                self._graph_path.read_text(encoding="utf-8")
            )
            self._nodes = data.get("nodes", {})
            self._edges = data.get("edges", [])
        except (json.JSONDecodeError, Exception):
            self._nodes = {}
            self._edges = []

    def save(self) -> None:
        """Save graph to .seed-graph.json."""
        data = {
            "version": 1,
            "updated_at": time.time(),
            "nodes": self._nodes,
            "edges": self._edges,
        }
        self._graph_path.write_text(
            json.dumps(
                data, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
        self._dirty = False

    def _ensure_saved(self) -> None:
        """Auto-save if dirty."""
        if self._dirty:
            self.save()

    # --------------------------------------------------
    # Node operations
    # --------------------------------------------------

    def add_node(
        self,
        node_id: str,
        path: str,
        *,
        content: str = "",
        node_type: str = "note",
    ) -> str:
        """Add or update a node. Returns node_id."""
        now = time.time()
        now_iso = _time_to_iso(now)

        if node_id in self._nodes:
            # Update existing
            node = self._nodes[node_id]
            node["accessed_at"] = now_iso
            node["access_count"] = (
                node.get("access_count", 0) + 1
            )
            if content:
                node["content_preview"] = content[:200]
        else:
            # Generate embedding
            embedding = self._embedder.embed(
                content or path
            )

            self._nodes[node_id] = {
                "path": path,
                "type": node_type,
                "embedding": embedding,
                "created_at": now_iso,
                "accessed_at": now_iso,
                "access_count": 1,
                "content_preview": content[:200],
            }

        self._dirty = True
        return node_id

    def get_node(
        self,
        node_id: str,
    ) -> dict[str, Any] | None:
        """Get a node by ID."""
        node = self._nodes.get(node_id)
        if node:
            # Update access
            node["accessed_at"] = _time_to_iso(
                time.time()
            )
            node["access_count"] = (
                node.get("access_count", 0) + 1
            )
            self._dirty = True
        return node

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges."""
        self._nodes.pop(node_id, None)
        self._edges = [
            e
            for e in self._edges
            if e["source"] != node_id
            and e["target"] != node_id
        ]
        self._dirty = True

    # --------------------------------------------------
    # Edge operations
    # --------------------------------------------------

    def add_edge(
        self,
        source: str,
        target: str,
        *,
        rel_type: RelationType = RelationType.RELATED,
        weight: float | None = None,
    ) -> None:
        """Add or update an edge between two nodes."""
        if weight is None:
            weight = get_initial_weight(rel_type)

        # Check if edge already exists
        for edge in self._edges:
            if (
                edge["source"] == source
                and edge["target"] == target
                and edge["rel_type"] == rel_type.value
            ):
                # Update existing
                edge["weight"] = weight
                edge["updated_at"] = _time_to_iso(
                    time.time()
                )
                self._dirty = True
                return

        # New edge
        self._edges.append(
            {
                "source": source,
                "target": target,
                "rel_type": rel_type.value,
                "weight": weight,
                "updated_at": _time_to_iso(
                    time.time()
                ),
            }
        )
        self._dirty = True

    def update_weights(
        self,
        node_id: str,
    ) -> None:
        """
        Update all edges connected to a node.
        Called after every interaction.
        """
        node = self._nodes.get(node_id)
        if node is None:
            return

        now = time.time()
        days_since = (
            now - _iso_to_time(node["created_at"])
        ) / 86400

        for edge in self._edges:
            if (
                edge["source"] == node_id
                or edge["target"] == node_id
            ):
                # Determine the other node
                other_id = (
                    edge["target"]
                    if edge["source"] == node_id
                    else edge["source"]
                )
                other = self._nodes.get(other_id)

                if other is None:
                    continue

                # Calculate vector similarity
                vec_sim = self._embedder.cosine_similarity(
                    node["embedding"],
                    other["embedding"],
                )

                # Get recency info for other node
                other_days = (
                    now
                    - _iso_to_time(
                        other.get(
                            "accessed_at",
                            other["created_at"],
                        )
                    )
                ) / 86400

                # Calculate new weight
                edge["weight"] = calculate_weight(
                    vector_similarity=vec_sim,
                    days_since_last_access=other_days,
                    access_count=other.get(
                        "access_count", 1
                    ),
                    current_weight=edge["weight"],
                )
                edge["updated_at"] = _time_to_iso(now)

        self._dirty = True

    # --------------------------------------------------
    # Graph-aware search
    # --------------------------------------------------

    def search_similar(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find notes similar to a query.

        Uses vector similarity + graph boost.
        """
        if not self._nodes:
            return []

        query_emb = self._embedder.embed(query)

        # Score each node
        scored: list[tuple[float, str, dict]] = []

        for nid, node in self._nodes.items():
            # Vector similarity
            vec_score = self._embedder.cosine_similarity(
                query_emb,
                node["embedding"],
            )

            # Graph boost: sum weights of connected edges
            graph_boost = 0.0
            for edge in self._edges:
                if edge["source"] == nid:
                    graph_boost += edge["weight"]
                elif edge["target"] == nid:
                    graph_boost += edge["weight"] * 0.8

            graph_boost = min(graph_boost, 1.0)

            # Recency
            days_since = (
                time.time()
                - _iso_to_time(
                    node.get(
                        "accessed_at",
                        node["created_at"],
                    )
                )
            ) / 86400
            recency = max(
                0.0, 1.0 - days_since / 30.0
            )

            # Final score
            final = (
                0.50 * vec_score
                + 0.30 * graph_boost
                + 0.20 * recency
            )

            scored.append((final, nid, node))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "id": nid,
                "path": node["path"],
                "type": node.get("type", "note"),
                "score": round(score, 4),
                "preview": node.get(
                    "content_preview", ""
                )[:100],
            }
            for score, nid, node in scored[:top_k]
        ]

    def get_related(
        self,
        node_id: str,
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get notes related to a node via graph edges.
        """
        related: list[tuple[float, str]] = []

        for edge in self._edges:
            if edge["source"] == node_id:
                related.append(
                    (edge["weight"], edge["target"])
                )
            elif edge["target"] == node_id:
                related.append(
                    (edge["weight"], edge["source"])
                )

        related.sort(key=lambda x: x[0], reverse=True)

        result = []
        for weight, nid in related[:top_k]:
            node = self._nodes.get(nid)
            if node:
                result.append(
                    {
                        "id": nid,
                        "path": node["path"],
                        "weight": round(weight, 4),
                    }
                )

        return result

    # --------------------------------------------------
    # Decay
    # --------------------------------------------------

    def decay_weights(
        self,
        *,
        max_age_days: float = 30.0,
    ) -> int:
        """
        Decay weights for edges whose nodes haven't
        been accessed recently. Returns count decayed.
        """
        now = time.time()
        count = 0

        for edge in self._edges:
            source = self._nodes.get(edge["source"])
            target = self._nodes.get(edge["target"])

            if source is None or target is None:
                continue

            s_days = (
                now
                - _iso_to_time(
                    source.get(
                        "accessed_at",
                        source["created_at"],
                    )
                )
            ) / 86400
            t_days = (
                now
                - _iso_to_time(
                    target.get(
                        "accessed_at",
                        target["created_at"],
                    )
                )
            ) / 86400

            if s_days > max_age_days or t_days > max_age_days:
                edge["weight"] *= 0.9
                count += 1

        if count:
            self._dirty = True

        return count

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)


def _time_to_iso(t: float) -> str:
    """Convert timestamp to ISO string."""
    from datetime import datetime, timezone

    return datetime.fromtimestamp(
        t, tz=timezone.utc
    ).isoformat()


def _iso_to_time(iso_str: str) -> float:
    """Convert ISO string to timestamp."""
    from datetime import datetime, timezone

    try:
        return datetime.fromisoformat(
            iso_str
        ).timestamp()
    except Exception:
        return time.time()
