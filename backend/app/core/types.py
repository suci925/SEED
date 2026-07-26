"""
Seed Core Type Definitions.

This module contains shared type definitions
used across the entire Seed system.

The purpose of this module is to provide
strongly typed identifiers and common types
for domain entities.
"""

from __future__ import annotations

from typing import NewType
from uuid import UUID


# ==================================================
# Domain Entity Identifiers
# ==================================================

"""
Each domain entity has its own identifier type.

Using NewType helps static type checkers
distinguish different kinds of IDs.

Example:

MemoryID != IdentityID

even though both are UUID internally.
"""


IdentityID = NewType(
    "IdentityID",
    UUID,
)


MemoryID = NewType(
    "MemoryID",
    UUID,
)


KnowledgeID = NewType(
    "KnowledgeID",
    UUID,
)


ExperienceID = NewType(
    "ExperienceID",
    UUID,
)


GoalID = NewType(
    "GoalID",
    UUID,
)


TaskID = NewType(
    "TaskID",
    UUID,
)


ConversationID = NewType(
    "ConversationID",
    UUID,
)