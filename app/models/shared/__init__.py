"""
Shared models that are used across multiple modules.

This package contains models that need to be shared between different
parts of the application to avoid circular dependencies.
"""

from app.models.shared.chat import ChatMessageModel

__all__ = ["ChatMessageModel"]
