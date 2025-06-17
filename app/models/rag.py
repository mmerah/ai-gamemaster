"""
RAG (Retrieval-Augmented Generation) related type definitions.

This module contains all RAG-related model definitions.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ===== Pydantic Models =====


class EventMetadataModel(BaseModel):
    """Metadata for RAG events."""

    timestamp: str = Field(..., description="ISO timestamp of the event")
    location: Optional[str] = Field(None, description="Location where event occurred")
    participants: Optional[List[str]] = Field(
        None, description="List of participants in the event"
    )
    combat_active: Optional[bool] = Field(
        None, description="Whether combat was active during event"
    )

    model_config = ConfigDict(extra="forbid")


class LoreDataModel(BaseModel):
    """Structure for lore entries."""

    id: str = Field(..., description="Lore entry ID")
    name: str = Field(..., description="Lore entry name")
    description: str = Field(..., description="Brief description")
    content: str = Field(..., description="Full lore content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(None, description="Lore category")

    model_config = ConfigDict(extra="forbid")
