"""
SQLite implementation of the Conversation repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import ConversationID, IdentityID
from app.domain.conversation import Conversation, ConversationStatus
from app.application.repositories.conversation_repository import ConversationRepository
from app.infrastructure.database.models import ConversationModel


class SQLiteConversationRepository(ConversationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: ConversationModel) -> Conversation:
        from app.core.types import ConversationID, IdentityID
        conv = Conversation(
            id=ConversationID(model.id),
            owner_id=IdentityID(model.owner_id),
            title=model.title,
        )
        conv.status = ConversationStatus(model.status)
        conv.created_at = model.created_at
        conv.updated_at = model.updated_at
        return conv

    @staticmethod
    def _to_model(conv: Conversation) -> ConversationModel:
        return ConversationModel(
            id=str(conv.id),
            owner_id=str(conv.owner_id),
            title=conv.title,
            status=conv.status.value,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    async def save(self, conv: Conversation) -> None:
        await self._session.merge(self._to_model(conv))
        await self._session.commit()

    async def get_by_id(self, conv_id: ConversationID) -> Conversation | None:
        model = await self._session.get(ConversationModel, str(conv_id))
        return self._to_domain(model) if model else None

    async def list_by_owner(self, owner_id: IdentityID) -> list[Conversation]:
        stmt = select(ConversationModel).where(ConversationModel.owner_id == str(owner_id)).order_by(ConversationModel.created_at.desc())
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def delete(self, conv_id: ConversationID) -> None:
        model = await self._session.get(ConversationModel, str(conv_id))
        if model:
            await self._session.delete(model)
            await self._session.commit()

    async def search(self, owner_id: IdentityID, query: str) -> list[Conversation]:
        like = f"%{query}%"
        stmt = select(ConversationModel).where(
            ConversationModel.owner_id == str(owner_id),
            ConversationModel.title.ilike(like),
        ).order_by(ConversationModel.created_at.desc())
        return [self._to_domain(m) for m in (await self._session.execute(stmt)).scalars().all()]
