"""D&D 5e Content Management Module.

This module encapsulates all D&D 5e content management functionality including:
- Database models and connection management
- Content repositories for accessing game data
- RAG (Retrieval-Augmented Generation) for semantic search
- Migration and maintenance scripts
- Pydantic schemas for data validation

The ContentService acts as the primary facade for this module.
"""

from app.content.connection import DatabaseManager
from app.content.service import ContentService

__all__ = [
    "ContentService",
    "DatabaseManager",
]
