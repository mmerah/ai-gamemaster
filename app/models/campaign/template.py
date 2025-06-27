"""
Campaign template models.

This module contains models for campaign templates - the static blueprints
used to create campaign instances.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from pydantic import ConfigDict, Field

from app.models.base import BaseModelWithDatetimeSerializer
from app.models.utils import (
    GoldRangeModel,
    HouseRulesModel,
    LocationModel,
    NPCModel,
    QuestModel,
)

if TYPE_CHECKING:
    from app.domain.validators.content_validator import (
        ContentValidationError,
        ContentValidator,
    )


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

    # Content Management
    content_pack_ids: List[str] = Field(
        default_factory=lambda: ["dnd_5e_srd"],
        description="Content pack IDs available for this campaign template",
    )

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

    def validate_content(
        self, validator: "ContentValidator"
    ) -> Tuple[bool, List["ContentValidationError"]]:
        """Validate D&D 5e content references in this campaign template.

        Args:
            validator: The content validator to use

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return validator.validate_campaign_template(self, self.content_pack_ids)


class CampaignOptionItem(BaseModelWithDatetimeSerializer):
    """Single option item for dropdowns."""

    value: str = Field(..., description="Option value")
    label: str = Field(..., description="Display label")


class CampaignOptionsResponse(BaseModelWithDatetimeSerializer):
    """Response containing available options for campaign creation/editing."""

    difficulties: List[CampaignOptionItem] = Field(
        default=[
            CampaignOptionItem(value="easy", label="Easy"),
            CampaignOptionItem(value="normal", label="Normal"),
            CampaignOptionItem(value="hard", label="Hard"),
            CampaignOptionItem(value="deadly", label="Deadly"),
        ],
        description="Available difficulty levels",
    )
    lores: List[CampaignOptionItem] = Field(
        default_factory=list,
        description="Available lore settings loaded from knowledge base",
    )
    rulesets: List[CampaignOptionItem] = Field(
        default=[
            CampaignOptionItem(value="dnd5e_standard", label="D&D 5e Standard"),
            CampaignOptionItem(value="dnd5e_homebrew", label="D&D 5e with Homebrew"),
        ],
        description="Available ruleset options",
    )


class CampaignTemplateUpdateModel(BaseModelWithDatetimeSerializer):
    """Update model for campaign templates with all fields optional.

    This model is used for PATCH endpoints where only specific fields
    need to be updated. All fields are optional except for those that
    shouldn't be changed (like id, created_date).
    """

    # Identity - most can be updated
    name: Optional[str] = None
    description: Optional[str] = None

    # Core Campaign Info
    campaign_goal: Optional[str] = None
    starting_location: Optional[LocationModel] = None
    opening_narrative: Optional[str] = None

    # Mechanics
    starting_level: Optional[int] = Field(None, ge=1, le=20)
    difficulty: Optional[str] = None
    ruleset_id: Optional[str] = None
    lore_id: Optional[str] = None

    # Initial Content
    initial_npcs: Optional[Dict[str, NPCModel]] = None
    initial_quests: Optional[Dict[str, QuestModel]] = None
    world_lore: Optional[List[str]] = None

    # Rules & Restrictions
    house_rules: Optional[HouseRulesModel] = None
    allowed_races: Optional[List[str]] = None
    allowed_classes: Optional[List[str]] = None
    starting_gold_range: Optional[GoldRangeModel] = None

    # Content Management
    content_pack_ids: Optional[List[str]] = None

    # Additional Info
    theme_mood: Optional[str] = None
    world_map_path: Optional[str] = None
    session_zero_notes: Optional[str] = None
    xp_system: Optional[str] = None

    # TTS Settings
    narration_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None

    # Metadata
    tags: Optional[List[str]] = None

    model_config = ConfigDict(extra="forbid")
