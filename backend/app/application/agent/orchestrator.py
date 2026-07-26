"""
Seed Agent Orchestrator.

The core loop that ties together user input,
knowledge retrieval (Obsidian), LLM reasoning
(Claude), and memory updates.
"""

from __future__ import annotations

from typing import Any

from app.core.types import IdentityID

from app.domain.experience import (
    Experience,
    ExperienceOutcome,
    ExperienceType,
)

from app.infrastructure.llm.deepseek_client import (
    DeepSeekClient,
)

from app.infrastructure.obsidian.vault import (
    ObsidianVault,
)

from app.application.repositories.memory_repository import (
    MemoryRepository,
)

from app.application.repositories.experience_repository import (
    ExperienceRepository,
)

from app.application.memory.manager import (
    MemoryManager,
    MemoryManagerResult,
)

from app.application.search.pipeline import (
    SearchPipeline,
    SearchResult,
)

from app.application.experience.distiller import (
    ExperienceDistiller,
    DistillationResult,
)


class AgentOrchestrator:
    """
    Orchestrates the Seed agent loop.

    The flow for each user message:
      1. Search Obsidian for relevant context
      2. Build prompt with retrieved context
      3. Call Claude to generate a response
      4. Record the interaction as Experience
      5. Save important information as Memory
      6. Return the response
    """

    def __init__(
        self,
        llm: DeepSeekClient,
        vault: ObsidianVault,
        memory_repo: MemoryRepository,
        experience_repo: ExperienceRepository,
        *,
        web_search: WebSearchService | None = None,
        search_pipeline: SearchPipeline | None = None,
        memory_manager: MemoryManager | None = None,
        experience_distiller: ExperienceDistiller | None = None,
        owner_id: IdentityID | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._llm = llm
        self._vault = vault
        self._memory_repo = memory_repo
        self._experience_repo = experience_repo
        self._web_search = web_search
        self._search_pipeline = search_pipeline or SearchPipeline(
            vault=vault,
            web_search=web_search,
        )
        self._memory_manager = memory_manager or MemoryManager(
            vault=vault,
            memory_repo=memory_repo,
        )
        self._distiller = experience_distiller
        self._owner_id = owner_id
        self._system_prompt = (
            system_prompt or self._default_system_prompt()
        )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    MIN_OBSIDIAN_RESULTS = 2
    """If Obsidian returns fewer than this, trigger web search."""

    async def process_message(
        self,
        message: str,
        *,
        owner_id: IdentityID | None = None,
    ) -> AgentResponse:
        """
        Process a user message end-to-end.

        Returns the agent's response and any
        side effects (saved memories, etc.).
        """

        uid = owner_id or self._owner_id

        import time
        start = time.monotonic()

        # 1. 4-layer search pipeline
        search_result = self._search_pipeline.search(
            message,
            min_obsidian_results=self.MIN_OBSIDIAN_RESULTS,
        )

        context_notes = search_result.obsidian_notes
        combined_context = search_result.combined_context

        # 4. Call DeepSeek
        reply = ""

        try:
            reply = await self._llm.chat_with_context(
                message,
                context=combined_context,
                system=self._system_prompt,
            )
        except Exception as e:
            reply = (
                "抱歉，我暂时无法连接到 AI 服务。"
                f"错误: {type(e).__name__}"
            )

        elapsed = time.monotonic() - start

        # 5. Record the interaction as Experience
        exp = Experience(
            owner_id=uid or IdentityID("unknown"),
            action=message,
            outcome=ExperienceOutcome.SUCCESS,
            experience_type=ExperienceType.INTERACTION,
            lesson=None,
            metadata={
                "context_notes": len(context_notes),
                "web_results": len(
                    search_result.web_results
                ),
                "layers_used": search_result.layers_used,
                "response_length": len(reply),
                "llm_model": self._llm.model,
                "elapsed_seconds": round(elapsed, 2),
            },
        )

        await self._experience_repo.save(exp)

        # 6. Memory Manager: decide what to remember
        mem_result = await self._memory_manager.process_exchange(
            user_message=message,
            assistant_reply=reply,
            owner_id=uid or IdentityID("unknown"),
        )

        # 7. Experience Distiller: extract reusable lessons
        distill_result = None

        if self._distiller is not None:
            distill_result = await self._distiller.distill(
                user_message=message,
                assistant_reply=reply,
            )

        return AgentResponse(
            reply=reply,
            context_notes=len(context_notes),
            memory_saved=(
                mem_result.category.value != "skip"
            ),
            memory_category=mem_result.category.value,
            memory_importance=mem_result.importance,
            experience_id=exp.id,
            experience_distilled=(
                distill_result.distilled
                if distill_result
                else False
            ),
        )

    # --------------------------------------------------
    # Default System Prompt
    # --------------------------------------------------

    @staticmethod
    def _default_system_prompt() -> str:
        return """你是 Seed，一个由 Claude 驱动的个人 AI 助手。

## 核心能力

- **长期记忆**：你有 Obsidian 知识库作为外部大脑，可以检索笔记回答问题
- **经验累积**：每次交互都会被记录为 Experience，帮助你学习
- **目标导向**：你可以帮助用户跟踪目标并拆解为任务

## 行为准则

1. 用中文回答，除非用户用其他语言提问
2. 回答基于检索到的相关知识，如果知识不足可以说明
3. 保持简洁、有价值的回答

## 记忆系统

本系统具备自动记忆能力：

- **偏好记忆**：当你表达喜好（"我喜欢X"）时，我会记住并存为偏好笔记
- **知识记忆**：当学到新知识或解决问题时，会存入知识库
- **经验记忆**：遇到坑或学到教训时，会记录经验笔记
- 所有记忆自动存入你的 Obsidian 知识库

## 知识检索

当用户提问时，系统会自动：
1. 从你的 Obsidian 知识库中检索相关笔记
2. 如果知识库没有足够信息，会自动上网搜索

请基于检索到的知识回答问题。如果同时有
本地知识和网络搜索结果，优先使用本地知识。"""


class AgentResponse:
    """
    Result of processing a user message.
    """

    def __init__(
        self,
        *,
        reply: str,
        context_notes: int,
        memory_saved: bool,
        memory_category: str = "skip",
        memory_importance: float = 0.0,
        experience_id: Any = None,
        experience_distilled: bool = False,
    ) -> None:
        self.reply = reply
        self.context_notes = context_notes
        self.memory_saved = memory_saved
        self.memory_category = memory_category
        self.memory_importance = memory_importance
        self.experience_id = experience_id
        self.experience_distilled = experience_distilled

    def __repr__(self) -> str:
        return (
            f"AgentResponse("
            f"reply_len={len(self.reply)}, "
            f"context_notes={self.context_notes}, "
            f"memory_saved={self.memory_saved})"
        )
