"""Content type models for D&D 5e content.

This module defines models for content type information.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ContentTypeInfo(BaseModel):
    """Information about a content type."""

    type_id: str = Field(
        ..., description="Content type identifier (e.g., 'spells', 'monsters')"
    )
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(
        None, description="Description of this content type"
    )
