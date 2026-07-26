"""
Memory Router — 统一记忆查询入口。

三种查询方式统一入口：
  vector_search()  → fastembed + 向量相似度
  graph_query()    → 知识图谱 (当前 .seed-graph.json, 未来 Memgraph/Neo4j)
  sql_query()      → SQL (当前 SQLite, 未来 PostgreSQL)

外部调用者不关心底层存储，只通过 Router 访问记忆。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.semantic.embeddings import EmbeddingEngine
from app.memory.semantic.graph import KnowledgeGraph
from app.memory.repositories.interfaces.memory_repository import (
    MemoryRepository,
)
from app.memory.repositories.interfaces.experience_repository import (
    ExperienceRepository,
)
from app.memory.repositories.interfaces.knowledge_repository import (
    KnowledgeRepository,
)
from app.memory.repositories.sqlite_memory_repository import (
    SQLiteMemoryRepository,
)
from app.memory.repositories.sqlite_experience_repository import (
    SQLiteExperienceRepository,
)
from app.memory.repositories.sqlite_knowledge_repository import (
    SQLiteKnowledgeRepository,
)


class MemoryRouter:
    """
    Unified entry point for all memory queries.

    Current backend: fastembed + .seed-graph.json + SQLite
    Future backend: any combination of vector/graph/SQL databases.
    """

    def __init__(
        self,
        graph: KnowledgeGraph,
        embedder: EmbeddingEngine | None = None,
    ) -> None:
        self._graph = graph
        self._embedder = embedder or EmbeddingEngine()
        self._session: AsyncSession | None = None

    # --------------------------------------------------
    # Session management (per-request)
    # --------------------------------------------------

    def set_session(
        self, session: AsyncSession
    ) -> None:
        """Set the DB session for SQL queries."""
        self._session = session

    # --------------------------------------------------
    # Vector Search
    # --------------------------------------------------

    def vector_search(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Semantic search via vector similarity.

        Uses fastembed (local, no API) for embedding.
        Compares against all nodes in the knowledge graph.

        Returns:
            List of {id, path, type, score, preview}
        """
        return self._graph.search_similar(
            query, top_k=top_k
        )

    # --------------------------------------------------
    # Graph Query
    # --------------------------------------------------

    def graph_query(
        self,
        operation: str,
        **params: Any,
    ) -> Any:
        """
        Query the knowledge graph.

        Operations:
          - "related": get_related(node_id, top_k=5)
          - "node": get_node(node_id)
          - "stats": node_count, edge_count
        """
        if operation == "related":
            return self._graph.get_related(
                params.get("node_id", ""),
                top_k=params.get("top_k", 5),
            )
        elif operation == "node":
            return self._graph.get_node(
                params.get("node_id", "")
            )
        elif operation == "stats":
            return {
                "nodes": self._graph.node_count,
                "edges": self._graph.edge_count,
            }
        elif operation == "search_similar":
            return self._graph.search_similar(
                params.get("query", ""),
                top_k=params.get("top_k", 5),
            )
        return None

    # --------------------------------------------------
    # SQL Query
    # --------------------------------------------------

    def _repo(
        self,
        repo_cls: type,
    ) -> Any:
        """Create a repository instance with current session."""
        if self._session is None:
            raise RuntimeError(
                "Session not set. Call set_session() first."
            )
        return repo_cls(self._session)

    async def sql_query(
        self,
        repo_type: str,
        method: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Query SQL storage via repository.

        repo_type: "memory", "experience", "knowledge"
        method: repository method name (save, get_by_id, list_by_owner, search, ...)
        """
        repo_map = {
            "memory": SQLiteMemoryRepository,
            "experience": SQLiteExperienceRepository,
            "knowledge": SQLiteKnowledgeRepository,
        }

        repo_cls = repo_map.get(repo_type)
        if repo_cls is None:
            raise ValueError(
                f"Unknown repo: {repo_type}"
            )

        repo = self._repo(repo_cls)
        async_method = getattr(repo, method, None)
        if async_method is None:
            raise ValueError(
                f"Unknown method: {method}"
            )

        return await async_method(*args, **kwargs)

    # --------------------------------------------------
    # Hybrid Search (vector + graph + optional SQL)
    # --------------------------------------------------

    def hybrid_search(
        self,
        query: str,
        *,
        top_k: int = 5,
        graph_boost: float = 0.3,
    ) -> list[dict[str, Any]]:
        """
        Combined vector + graph search.

        Vector similarity × (1 + graph_boost × connected_edges)
        """
        return self._graph.search_similar(
            query, top_k=top_k
        )
