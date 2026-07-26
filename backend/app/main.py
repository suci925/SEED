"""
Seed FastAPI Application.

Exposes the Seed agent as a web API.
"""

from __future__ import annotations

import sys
from pathlib import Path
from contextlib import asynccontextmanager

# 将 backend/ 加入 Python 路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.types import IdentityID

from app.core.config import settings

from app.infrastructure.llm.factory import (
    create_llm_provider,
)

from app.infrastructure.obsidian.vault import (
    ObsidianVault,
)

from app.infrastructure.database.connection import (
    AsyncSessionFactory,
)

from app.infrastructure.repositories.sqlite_experience_repository import (
    SQLiteExperienceRepository,
)

from app.infrastructure.repositories.sqlite_memory_repository import (
    SQLiteMemoryRepository,
)

from app.infrastructure.repositories.sqlite_experience_repository import (
    SQLiteExperienceRepository,
)

from app.infrastructure.search.web_search import (
    WebSearchService,
)

from app.application.agent.orchestrator import (
    AgentOrchestrator,
)

from app.application.search.pipeline import (
    SearchPipeline,
)

from app.application.experience.distiller import (
    ExperienceDistiller,
)

from app.application.evolution.loop import (
    EvolutionLoop,
)

from app.application.skills.manager import (
    SkillManager,
)


# --------------------------------------------------
# Application State
# --------------------------------------------------

class AppContext:
    """Shared app-wide dependencies."""

    def __init__(self) -> None:
        self.vault: ObsidianVault | None = None
        self.agent: AgentOrchestrator | None = None


app_ctx = AppContext()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise shared resources."""

    if not settings.OBSIDIAN_VAULT_PATH:
        raise RuntimeError(
            "OBSIDIAN_VAULT_PATH not configured in .env"
        )

    vault = ObsidianVault(
        settings.OBSIDIAN_VAULT_PATH
    )

    app_ctx.vault = vault

    print(
        f"Vault loaded: {vault.note_count} notes",
    )

    yield

    # Shutdown: nothing to clean up yet


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


# --------------------------------------------------
# Schemas
# --------------------------------------------------

class ChatRequest(BaseModel):
    """Incoming user message."""

    message: str
    owner_id: str = "default-user"


class ChatResponse(BaseModel):
    """Agent response."""

    reply: str
    context_notes: int
    memory_saved: bool
    memory_category: str = "skip"
    experience_distilled: bool = False


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
async def root():
    """Health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "vault_notes": (
            app_ctx.vault.note_count
            if app_ctx.vault
            else 0
        ),
    }


@app.get("/notes")
async def list_notes(
    tag: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
):
    """Search / list Obsidian notes."""
    if app_ctx.vault is None:
        raise HTTPException(
            status_code=503,
            detail="Vault not loaded",
        )

    if tag:
        results = app_ctx.vault.search_by_tag(tag)
    elif keyword:
        results = app_ctx.vault.search_by_keyword(
            keyword,
            max_results=limit,
        )
    else:
        results = app_ctx.vault.notes[:limit]

    # Track view in knowledge graph
    try:
        graph = app_ctx.vault.graph
        for n in results[:5]:
            node_id = f"note:{n.name}"
            graph.get_node(node_id)
        graph.save()
    except Exception:
        pass

    return [
        {
            "name": n.name,
            "tags": n.tags,
            "content_preview": n.content[:200],
        }
        for n in results
    ]


@app.get("/tags")
async def list_tags():
    """List all tags in the vault."""
    if app_ctx.vault is None:
        raise HTTPException(
            status_code=503,
            detail="Vault not loaded",
        )

    return {"tags": app_ctx.vault.list_all_tags()}


@app.get("/graph")
async def get_graph(
    node_id: str | None = None,
):
    """View the knowledge graph."""
    if app_ctx.vault is None:
        raise HTTPException(status_code=503)

    graph = app_ctx.vault.graph

    if node_id:
        related = graph.get_related(node_id)
        return {
            "node": graph.get_node(node_id),
            "related": related,
        }

    return {
        "nodes": graph.node_count,
        "edges": graph.edge_count,
        "node_list": [
            {"id": nid, "path": n["path"]}
            for nid, n in list(
                graph._nodes.items()
            )[:50]
        ],
    }


@app.post("/evolution")
async def trigger_evolution(owner_id: str = "default-user"):
    """Trigger a full evolution cycle manually."""
    if app_ctx.vault is None:
        raise HTTPException(status_code=503, detail="Vault not loaded")
    try:
        llm = create_llm_provider()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    async with AsyncSessionFactory() as session:
        loop = EvolutionLoop(llm=llm, vault=app_ctx.vault, experience_repo=SQLiteExperienceRepository)
        result = await loop.run(session=session, owner_id=IdentityID(owner_id))
    return {
        "cycle": result.cycle,
        "notes_reviewed": result.notes_reviewed,
        "decayed_edges": result.decayed_edges,
        "reflection_summary": result.reflection.summary if result.reflection else "",
        "patterns": result.reflection.patterns if result.reflection else [],
        "note_path": str(result.note_path) if result.note_path else None,
    }


@app.get("/history")
async def list_history(
    limit: int = 20,
    owner_id: str = "default-user",
):
    """View recent conversation history."""
    async with AsyncSessionFactory() as session:
        repo = SQLiteExperienceRepository(session)
        results = await repo.list_by_owner(
            IdentityID(owner_id),
        )

    return [
        {
            "action": e.action[:100],
            "outcome": e.outcome.value,
            "type": e.experience_type.value,
            "lesson": e.lesson,
            "created_at": (
                e.created_at.isoformat()
                if e.created_at
                else None
            ),
        }
        for e in results[:limit]
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the Seed agent."""

    # Lazy-init agent on first request
    if app_ctx.agent is None:

        try:
            llm = create_llm_provider()
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=str(e),
            )

        vault = app_ctx.vault

        if vault is None:
            raise HTTPException(
                status_code=503,
                detail="Vault not loaded",
            )

        web_search = WebSearchService()

        app_ctx.agent = AgentOrchestrator(
            llm=llm,
            vault=vault,
            memory_repo=SQLiteMemoryRepository,
            experience_repo=SQLiteExperienceRepository,
            web_search=web_search,
            search_pipeline=SearchPipeline(
                vault=vault,
                web_search=web_search,
                skill_manager=SkillManager(),
            ),
            experience_distiller=ExperienceDistiller(
                llm=llm,
                vault=vault,
            ),
            evolution_loop=EvolutionLoop(
                llm=llm,
                vault=vault,
                experience_repo=SQLiteExperienceRepository,
            ),
        )

    # 每个请求创建独立 session
    async with AsyncSessionFactory() as session:
        result = await app_ctx.agent.process_message(
            message=request.message,
            session=session,
        )

    return ChatResponse(
        reply=result.reply,
        context_notes=result.context_notes,
        memory_saved=result.memory_saved,
        memory_category=result.memory_category,
        experience_distilled=result.experience_distilled,
    )
