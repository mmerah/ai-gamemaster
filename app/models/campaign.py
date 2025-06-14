"""
Campaign models.

This module contains all campaign-related models including templates and instances.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import BaseModelWithDatetimeSerializer
from app.models.utils import (
    GoldRangeModel,
    HouseRulesModel,
    LocationModel,
    NPCModel,
    QuestModel,
)


class CampaignSummaryModel(BaseModel):
    """Summary information about a campaign."""

    id: str = Field(..., description="Campaign ID")
    name: str = Field(..., description="Campaign name")
    description: str = Field(..., description="Campaign description")
    starting_level: int = Field(..., description="Starting character level")
    difficulty: str = Field(..., description="Campaign difficulty setting")
    created_date: datetime = Field(..., description="When the campaign was created")
    last_modified: Optional[datetime] = Field(
        None, description="When the campaign was last modified"
    )

    model_config = ConfigDict(extra="forbid")


class CampaignTemplateModel(BaseModelWithDatetimeSerializer):
    """Complete campaign template matching JSON structure"""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Identity
    id: str
    name: str
    description: str

    # Core Campaign Info
    campaign_goal: str
    starting_location: LocationModel
    opening_narrative: str

    # Mechanics
    starting_level: int = Field(ge=1, le=20, default=1)
    difficulty: str = "normal"  # easy, normal, hard, deadly
    ruleset_id: str = "dnd5e_standard"
    lore_id: str = "generic_fantasy"

    # Initial Content
    initial_npcs: Dict[str, NPCModel] = Field(default_factory=dict)
    initial_quests: Dict[str, QuestModel] = Field(default_factory=dict)
    world_lore: List[str] = Field(default_factory=list)

    # Rules & Restrictions
    house_rules: HouseRulesModel = Field(default_factory=HouseRulesModel)
    allowed_races: Optional[List[str]] = None
    allowed_classes: Optional[List[str]] = None
    starting_gold_range: Optional[GoldRangeModel] = None

    # Additional Info
    theme_mood: Optional[str] = None
    world_map_path: Optional[str] = None
    session_zero_notes: Optional[str] = None
    xp_system: str = "milestone"  # milestone, xp

    # TTS Settings (default for campaigns created from this template)
    narration_enabled: bool = Field(
        default=False, description="Default narration setting for campaigns"
    )
    tts_voice: str = Field(
        default="af_heart", description="Default TTS voice for campaigns"
    )

    # Metadata
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


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

    # Current state
    current_location: str
    session_count: int = 0
    in_combat: bool = False
    event_summary: List[str] = Field(default_factory=list)  # Accumulated during play

    # Event tracking
    event_log_path: str  # Path to event log file
    last_event_id: Optional[str] = None

    # TTS Settings (campaign-level override, optional)
    narration_enabled: Optional[bool] = Field(
        default=None, description="Campaign-specific narration override"
    )
    tts_voice: Optional[str] = Field(
        default=None, description="Campaign-specific TTS voice override"
    )

    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_played: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(extra="forbid")
