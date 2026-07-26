"""
Seed Core Exception System.

This module defines the base exception hierarchy
used throughout the Seed application.

All application-specific exceptions should inherit
from SeedException.
"""

from __future__ import annotations


class SeedException(Exception):
    """
    Base exception for all Seed application errors.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
    ) -> None:
        self.message = message

        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class ConfigurationError(SeedException):
    """
    Raised when application configuration is invalid.
    """

    pass


class ValidationError(SeedException):
    """
    Raised when data validation fails.
    """

    pass


class DomainError(SeedException):
    """
    Raised when a domain rule is violated.
    """

    pass


class EntityNotFoundError(SeedException):
    """
    Raised when a requested entity cannot be found.
    """

    pass


class ProviderError(SeedException):
    """
    Raised when an external provider fails.

    Examples:
    - LLM provider failure
    - Database failure
    - External API failure
    """

    pass