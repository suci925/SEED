"""
Conversation Service.

Handles conversation lifecycle
and interaction history management.
"""

from __future__ import annotations


from app.core.types import (
    ConversationID,
    IdentityID,
)

from app.domain.conversation import Conversation

from app.application.repositories.conversation_repository import (
    ConversationRepository,
)


class ConversationService:
    """
    Application service for Conversation.

    Responsible for managing
    user-agent interaction history.
    """


    def __init__(
        self,
        repository: ConversationRepository,
    ) -> None:
        self._repository = repository


    async def create_conversation(
        self,
        conversation: Conversation,
    ) -> Conversation:
        """
        Create and persist conversation.
        """

        await self._repository.save(
            conversation
        )

        return conversation


    async def get_conversation(
        self,
        conversation_id: ConversationID,
    ) -> Conversation | None:
        """
        Retrieve conversation.
        """

        return await self._repository.get_by_id(
            conversation_id
        )


    async def list_conversations(
        self,
        owner_id: IdentityID,
    ) -> list[Conversation]:
        """
        List conversations owned by identity.
        """

        return await self._repository.list_by_owner(
            owner_id
        )


    async def search_history(
        self,
        owner_id: IdentityID,
        query: str,
    ) -> list[Conversation]:
        """
        Search conversation history.
        """

        return await self._repository.search(
            owner_id,
            query,
        )


    async def delete_conversation(
        self,
        conversation_id: ConversationID,
    ) -> None:
        """
        Delete conversation.
        """

        await self._repository.delete(
            conversation_id
        )


    async def append_message(
        self,
        conversation: Conversation,
    ) -> None:
        """
        Append new message to conversation.

        The domain entity is responsible
        for message validation.
        """

        await self._repository.save(
            conversation
        )