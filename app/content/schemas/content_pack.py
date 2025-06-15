"""Content Pack schemas for managing collections of D&D content.

This module contains the Pydantic models for content packs, which organize
D&D content into collections (SRD, homebrew, third-party, etc.).
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class D5eContentPack(BaseModel):
    """Represents a collection of D&D content.

    Content packs allow organizing content into separate collections that can be
    activated/deactivated and prioritized for content resolution.
    """

    id: str = Field(..., description="Unique identifier for the content pack")
    name: str = Field(..., description="Display name of the content pack")
    description: Optional[str] = Field(
        None, description="Description of the content pack"
    )
    version: str = Field(..., description="Version of the content pack")
    author: Optional[str] = Field(
        None, description="Author or publisher of the content"
    )
    is_active: bool = Field(
        True, description="Whether the content pack is currently active"
    )
    created_at: datetime = Field(..., description="When the content pack was created")
    updated_at: datetime = Field(
        ..., description="When the content pack was last updated"
    )

    model_config = ConfigDict(from_attributes=True)


class ContentPackCreate(BaseModel):
    """Request model for creating a new content pack."""

    name: str = Field(..., description="Display name of the content pack")
    description: Optional[str] = Field(
        None, description="Description of the content pack"
    )
    version: str = Field("1.0.0", description="Version of the content pack")
    author: Optional[str] = Field(
        None, description="Author or publisher of the content"
    )
    is_active: bool = Field(
        True, description="Whether to activate the pack immediately"
    )


class ContentPackUpdate(BaseModel):
    """Request model for updating an existing content pack."""

    name: Optional[str] = Field(None, description="Updated display name")
    description: Optional[str] = Field(None, description="Updated description")
    version: Optional[str] = Field(None, description="Updated version")
    author: Optional[str] = Field(None, description="Updated author")
    is_active: Optional[bool] = Field(None, description="Updated active status")


class ContentPackWithStats(D5eContentPack):
    """Content pack with statistics about its contents."""

    statistics: Dict[str, int] = Field(
        ..., description="Statistics about the content in this pack"
    )


class ContentUploadResult(BaseModel):
    """Result of a content upload operation."""

    content_type: str = Field(
        ..., description="Type of content uploaded (spells, monsters, etc.)"
    )
    total_items: int = Field(..., description="Total number of items in the upload")
    successful_items: int = Field(
        ..., description="Number of items successfully imported"
    )
    failed_items: int = Field(..., description="Number of items that failed validation")
    validation_errors: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of item index/name to validation error message",
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-critical warnings about the import"
    )
