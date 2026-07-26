"""
SQLAlchemy database models.

Defines persistence models
for SEED entities.
"""

from __future__ import annotations


from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    String,
    Text,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base.
    """

    pass


class MemoryModel(Base):
    """
    Database model for Memory.
    """

    __tablename__ = "memories"


    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )


    owner_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )


    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    memory_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="fact",
    )


    importance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
    )


    source: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="conversation",
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
    )


    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        onupdate=datetime.now(timezone.utc),
    )


class KnowledgeModel(Base):
    """
    Database model for Knowledge.
    """

    __tablename__ = "knowledge"


    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )


    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    knowledge_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="document",
    )


    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
    )


    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        onupdate=datetime.now(timezone.utc),
    )


class ExperienceModel(Base):
    """
    Database model for Experience.
    """

    __tablename__ = "experiences"


    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )


    owner_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )


    action: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    result: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    experience_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="interaction",
    )


    lesson: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # --- 结构化经验字段 ---

    context_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )

    actions_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    failures_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    solution: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
    )


    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        onupdate=datetime.now(timezone.utc),
    )


class ConversationModel(Base):
    """Database model for Conversation."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, onupdate=datetime.now(timezone.utc))


class GoalModel(Base):
    """Database model for Goal."""

    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    priority: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, onupdate=datetime.now(timezone.utc))


class TaskModel(Base):
    """Database model for Task."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    goal_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    priority: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, onupdate=datetime.now(timezone.utc))