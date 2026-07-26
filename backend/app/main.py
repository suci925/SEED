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

from app.core.config import settings

from app.infrastructure.llm.deepseek_client import (
    DeepSeekClient,
)

from app.infrastructure.obsidian.vault import (
    ObsidianVault,
)

from app.infrastructure.database.connection import (
    AsyncSessionFactory,
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

    vault_path = (
        settings.OBSIDIAN_VAULT_PATH
        or "c:/Users/30425/OneDrive/Desktop/vault"
    )

    vault = ObsidianVault(vault_path)

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


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the Seed agent."""

    # Lazy-init agent on first request
    if app_ctx.agent is None:

        if not settings.DEEPSEEK_API_KEY:
            raise HTTPException(
                status_code=500,
                detail=(
                    "DEEPSEEK_API_KEY not configured. "
                    "Set it in .env file."
                ),
            )

        llm = DeepSeekClient(
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.DEEPSEEK_MODEL,
        )

        vault = app_ctx.vault

        if vault is None:
            raise HTTPException(
                status_code=503,
                detail="Vault not loaded",
            )

        # 每个请求创建独立 session
        session = AsyncSessionFactory()

        web_search = WebSearchService()

        app_ctx.agent = AgentOrchestrator(
            llm=llm,
            vault=vault,
            memory_repo=SQLiteMemoryRepository(
                session,
            ),
            experience_repo=SQLiteExperienceRepository(
                session,
            ),
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
        )

    result = await app_ctx.agent.process_message(
        message=request.message,
    )

    return ChatResponse(
        reply=result.reply,
        context_notes=result.context_notes,
        memory_saved=result.memory_saved,
        memory_category=result.memory_category,
        experience_distilled=result.experience_distilled,
    )
