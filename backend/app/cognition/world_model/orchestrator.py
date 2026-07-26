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

from app.cognition.world_model.base import (
    LLMProvider,
)

from app.perception.context.vault import (
    ObsidianVault,
)

from app.memory.coordinator import (
    MemoryCoordinator,
)

from app.perception.context.pipeline import (
    SearchPipeline,
)

from app.experience_engine.distiller import (
    ExperienceDistiller,
)

from app.experience_engine.learner import (
    ExperienceLearner,
)

from app.experience_engine.loop import (
    EvolutionLoop,
    EvolutionResult,
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
        llm: LLMProvider,
        vault: ObsidianVault,
        *,
        memory_repo: type[MemoryRepository] | None = None,
        experience_repo: type[ExperienceRepository] | None = None,
        web_search: WebSearchService | None = None,
        search_pipeline: SearchPipeline | None = None,
        memory_manager: type[MemoryCoordinator] | None = None,
        experience_distiller: ExperienceDistiller | None = None,
        experience_learner: ExperienceLearner | None = None,
        evolution_loop: EvolutionLoop | None = None,
        owner_id: IdentityID | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._llm = llm
        self._vault = vault
        self._memory_repo_cls = memory_repo
        self._experience_repo_cls = experience_repo
        self._web_search = web_search
        self._search_pipeline = search_pipeline
        self._distiller = experience_distiller
        self._learner = experience_learner
        self._evolution_loop = evolution_loop
        self._owner_id = owner_id
        self._system_prompt = (
            system_prompt or self._default_system_prompt()
        )
        self._memory_manager_cls = memory_manager
        self._conversation_history: list[dict] = []

    def _init_repos(self, session: Any) -> None:
        """Per-request initialisation of repositories."""

        from sqlalchemy.ext.asyncio import AsyncSession

        memory_cls = self._memory_repo_cls
        exp_cls = self._experience_repo_cls

        if memory_cls:
            self._memory_repo = memory_cls(session)
        if exp_cls:
            self._experience_repo = exp_cls(session)

        if self._search_pipeline is None:
            self._search_pipeline = SearchPipeline(
                vault=self._vault,
                web_search=self._web_search,
            )

        if memory_cls and hasattr(self, '_memory_repo'):
            self._memory_manager = (
                self._memory_manager_cls or MemoryCoordinator
            )(
                vault=self._vault,
                memory_repo=self._memory_repo,
            )
        else:
            self._memory_manager = None

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    MIN_OBSIDIAN_RESULTS = 2
    """If Obsidian returns fewer than this, trigger web search."""

    async def process_message(
        self,
        message: str,
        *,
        session: Any = None,
        owner_id: IdentityID | None = None,
    ) -> AgentResponse:
        """
        Process a user message end-to-end.

        Args:
            message: User's input text.
            session: SQLAlchemy AsyncSession (per-request).
            owner_id: Optional identity owner.

        Returns:
            AgentResponse with reply and metadata.
        """

        uid = owner_id or self._owner_id

        # Init per-request repositories
        self._init_repos(session)

        import time
        start = time.monotonic()

        # 1. 4-layer search pipeline
        search_result = self._search_pipeline.search(
            message,
            min_obsidian_results=self.MIN_OBSIDIAN_RESULTS,
        )

        context_notes = search_result.obsidian_notes
        combined_context = search_result.combined_context

        # 2. Update graph weights from this search
        try:
            graph = self._vault.graph
            if graph.node_count > 0:
                # Decay old weights
                graph.decay_weights()
                # Update access counts for found notes
                for note in context_notes:
                    node_id = f"note:{note.name}"
                    graph.get_node(node_id)
                graph.save()
        except Exception:
            pass

        # 3. Build conversation-aware prompt
        conv_context = self._build_conversation_context(
            user_message=message,
        )

        # 3. Call LLM with full context
        full_context = ""

        if combined_context:
            full_context += (
                f"## 检索到的知识\n\n"
                f"{combined_context}\n\n"
            )

        if conv_context:
            full_context += (
                f"## 对话历史\n\n"
                f"{conv_context}\n\n"
            )

        reply = ""

        try:
            if full_context:
                reply = await self._llm.chat_with_context(
                    message,
                    context=full_context,
                    system=self._system_prompt,
                )
            else:
                reply = await self._llm.chat_async(
                    message,
                    system=self._system_prompt,
                )
        except Exception as e:
            reply = (
                "抱歉，我暂时无法连接到 AI 服务。"
                f"错误: {type(e).__name__}"
            )

        # 5. Track conversation history (keep last 6 turns)
        self._conversation_history.append({
            "role": "user",
            "content": message,
        })
        self._conversation_history.append({
            "role": "assistant",
            "content": reply,
        })
        if len(self._conversation_history) > 12:
            self._conversation_history = (
                self._conversation_history[-12:]
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

        # 5b. Enhance experience with structured learning
        if self._learner is not None:
            try:
                structured = await self._learner.extract(
                    user_message=message,
                    assistant_reply=reply,
                )
                if structured is not None:
                    exp.context = structured.context
                    exp.actions = structured.actions
                    exp.failures = structured.failures
                    exp.solution = structured.solution
                    exp.confidence = structured.confidence
                    exp.experience_type = (
                        ExperienceType.TASK
                        if structured.actions
                        else ExperienceType.INTERACTION
                    )
            except Exception:
                pass

        await self._experience_repo.save(exp)

        # 6. Memory Manager: decide what to remember
        mem_category = "skip"
        mem_importance = 0.0

        if self._memory_manager is not None:
            mem_result = await self._memory_manager.process_exchange(
                user_message=message,
                assistant_reply=reply,
                owner_id=uid or IdentityID("unknown"),
            )
            mem_category = mem_result.category.value
            mem_importance = mem_result.importance

        # 7. Experience Distiller: extract reusable lessons
        distill_result = None

        if self._distiller is not None:
            distill_result = await self._distiller.distill(
                user_message=message,
                assistant_reply=reply,
            )

        # 8. Evolution tick: lightweight learning cycle
        if self._evolution_loop is not None:
            try:
                await self._evolution_loop.tick(
                    session=session,
                    owner_id=uid,
                )
            except Exception:
                pass

        return AgentResponse(
            reply=reply,
            context_notes=len(context_notes),
            memory_saved=(
                mem_category != "skip"
            ),
            memory_category=mem_category,
            memory_importance=mem_importance,
            experience_id=exp.id,
            experience_distilled=(
                distill_result.distilled
                if distill_result
                else False
            ),
        )

    # --------------------------------------------------
    # Conversation Context
    # --------------------------------------------------

    def _build_conversation_context(
        self,
        user_message: str,
        *,
        max_turns: int = 6,
    ) -> str:
        """
        Build recent conversation history context.

        Helps the LLM remember what was discussed
        in previous turns.
        """

        if not self._conversation_history:
            return ""

        # Get last N exchanges
        recent = self._conversation_history[
            -(max_turns * 2):
        ]

        lines: list[str] = []

        for entry in recent:
            role = "用户" if entry["role"] == "user" else "Seed"
            content = entry["content"][:200]
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

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

请基于检索到的知识回答问题。

## 对话记忆

我会看到最近几轮的对话历史。
请参考历史上下文来保持对话的连贯性。
如果用户提到之前讨论过的话题，请基于历史记录回答。"""


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
