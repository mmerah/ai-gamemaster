"""
Campaign instance models.

This module contains models for active campaign instances - the dynamic
game state representing ongoing campaigns.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import ConfigDict, Field

from app.models.base import BaseModelWithDatetimeSerializer


class CampaignInstanceModel(BaseModelWithDatetimeSerializer):
    """Active campaign with current state"""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Identity
    id: str
    name: str
    template_id: Optional[str] = None  # Link to template if created from one

    # Party
    character_ids: List[str] = Field(default_factory=list)  # Character template IDs
    character_levels: Optional[Dict[str, int]] = Field(
        default=None,
        description="Optional starting levels for characters (character_id -> level)",
    )

    # Current state
    current_location: str
    session_count: int = 0
    in_combat: bool = False
    event_summary: List[str] = Field(default_factory=list)  # Accumulated during play

    # Event tracking
    event_log_path: str  # Path to event log file
    last_event_id: Optional[str] = None

    # Content packs
    content_pack_priority: List[str] = Field(
        default_factory=lambda: ["dnd_5e_srd"],
        description="Content pack IDs in priority order (first = highest priority)",
    )

    # TTS Settings (campaign-level override, optional)
    narration_enabled: Optional[bool] = Field(
        default=None, description="Campaign-specific narration override"
    )
    tts_voice: Optional[str] = Field(
        default=None, description="Campaign-specific TTS voice override"
    )

    # Metadata
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_played: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")
