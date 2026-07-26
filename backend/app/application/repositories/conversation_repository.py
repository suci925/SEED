"""
Conversation Repository Interface.

Defines abstraction for conversation persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.types import (
    ConversationID,
    IdentityID,
)

from app.domain.conversation import Conversation


class ConversationRepository(ABC):
    """
    Abstract repository for Conversation.

    Handles persistence of interaction history
    between Identity and Seed.
    """


    @abstractmethod
    async def save(
        self,
        conversation: Conversation,
    ) -> None:
        """
        Save conversation entity.
        """

        raise NotImplementedError


    @abstractmethod
    async def get_by_id(
        self,
        conversation_id: ConversationID,
    ) -> Conversation | None:
        """
        Retrieve conversation by id.
        """

        raise NotImplementedError


    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: IdentityID,
    ) -> list[Conversation]:
        """
        List conversations belonging
        to an identity.
        """

        raise NotImplementedError


    @abstractmethod
    async def delete(
        self,
        conversation_id: ConversationID,
    ) -> None:
        """
        Delete conversation.
        """

        raise NotImplementedError


    @abstractmethod
    async def search(
        self,
        owner_id: IdentityID,
        query: str,
    ) -> list[Conversation]:
        """
        Search conversation history.

        Future implementations may use
        semantic retrieval.
        """

        raise NotImplementedError