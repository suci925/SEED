"""
Relationship Types and Weight Calculation.

Defines the types of relationships between notes
and how their weights are calculated and updated.
"""

from __future__ import annotations

from enum import Enum
from math import exp


class RelationType(str, Enum):
    """Types of relationships between knowledge nodes."""

    RELATED = "related"
    """Content is semantically similar."""

    CO_OCCURRENCE = "co_occurrence"
    """Notes are frequently referenced together."""

    CITES = "cites"
    """Note A links to Note B via [[wikilink]]."""

    SAME_TAG = "same_tag"
    """Notes share one or more tags."""

    TEMPORAL = "temporal"
    """Notes created close in time."""


# Default initial weights per relationship type
DEFAULT_WEIGHTS = {
    RelationType.RELATED: 0.5,
    RelationType.CO_OCCURRENCE: 0.3,
    RelationType.CITES: 0.6,
    RelationType.SAME_TAG: 0.4,
    RelationType.TEMPORAL: 0.2,
}


# --------------------------------------------------
# Weight formula constants
# --------------------------------------------------

# Weight: how much each signal contributes
VECTOR_SIM_WEIGHT = 0.40
RECENCY_WEIGHT = 0.25
ACCESS_FREQ_WEIGHT = 0.20
REL_STRENGTH_WEIGHT = 0.15

# Decay: days until weight halves
RECENCY_HALF_LIFE = 14  # days


def calculate_weight(
    *,
    vector_similarity: float = 0.0,
    days_since_last_access: float = 0.0,
    access_count: int = 0,
    current_weight: float = 0.0,
) -> float:
    """
    Calculate relationship weight using multi-signal fusion.

    weight = 0.40 × vector_similarity
           + 0.25 × recency_factor
           + 0.20 × access_frequency
           + 0.15 × relationship_strength
    """

    # 1. Vector similarity (0.0 - 1.0)
    vec = max(0.0, min(1.0, vector_similarity))

    # 2. Recency factor: exponential decay
    recency = exp(
        -0.05 * days_since_last_access
    )

    # 3. Access frequency: normalized
    freq = min(access_count / 10.0, 1.0)

    # 4. Relationship strength: historical weight
    strength = max(0.0, min(1.0, current_weight))

    return (
        VECTOR_SIM_WEIGHT * vec
        + RECENCY_WEIGHT * recency
        + ACCESS_FREQ_WEIGHT * freq
        + REL_STRENGTH_WEIGHT * strength
    )


def get_initial_weight(
    rel_type: RelationType,
) -> float:
    """Get the initial weight for a relationship type."""
    return DEFAULT_WEIGHTS.get(rel_type, 0.3)
