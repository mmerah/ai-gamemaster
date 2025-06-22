"""
API request models for type-safe FastAPI endpoints.

This module contains all request models used by FastAPI routes to ensure
type safety and automatic request validation.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel


# Character endpoint requests
class CharacterTemplateCreateRequest(BaseModel):
    """Request for creating character templates.

    Handles frontend-specific field mappings like skill_proficiencies.
    """

    # Identity
    name: str = Field(..., min_length=1, max_length=100)
    race: str = Field(..., description="D&D 5e race ID")
    subrace: Optional[str] = Field(None, description="Subrace ID if applicable")
    char_class: str = Field(..., description="D&D 5e class ID", alias="class")
    subclass: Optional[str] = Field(None, description="Subclass ID if applicable")
    level: int = Field(1, ge=1, le=20)
    background: str = Field(..., description="D&D 5e background ID")
    alignment: str = Field(..., description="Character alignment")

    # Stats and abilities
    ability_scores: Dict[str, int] = Field(
        ..., description="STR, DEX, CON, INT, WIS, CHA scores"
    )
    hit_points: int = Field(..., ge=1)
    armor_class: int = Field(..., ge=1)
    speed: int = Field(30, ge=0)
    experience: int = Field(0, ge=0)

    # Proficiencies - handle frontend's skill_proficiencies field
    skill_proficiencies: Optional[List[str]] = Field(
        None, description="List of proficient skills"
    )
    proficiencies: Optional[Dict[str, Any]] = Field(
        None, description="All proficiencies"
    )

    # Features and equipment
    features: Optional[List[Dict[str, Any]]] = Field(
        None, description="Character features"
    )
    equipment: Optional[List[Dict[str, Any]]] = Field(
        None, description="Starting equipment"
    )
    languages: Optional[List[str]] = Field(None, description="Known languages")

    # Additional info
    physical_description: Optional[str] = None
    personality_traits: Optional[str] = None
    ideals: Optional[str] = None
    bonds: Optional[str] = None
    flaws: Optional[str] = None
    backstory: Optional[str] = None

    @field_validator("proficiencies", mode="before")
    def merge_skill_proficiencies(cls, v: Any, values: Any) -> Optional[Dict[str, Any]]:
        """Merge skill_proficiencies into proficiencies dict."""
        if "skill_proficiencies" in values.data:
            skills = values.data["skill_proficiencies"]
            if skills and isinstance(skills, list):
                if v is None:
                    v = {}
                v["skills"] = skills
        return v  # type: ignore[no-any-return]

    model_config = ConfigDict(populate_by_name=True)  # Allow 'class' alias


class CharacterTemplateUpdateRequest(BaseModel):
    """Request for updating character templates.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    race: Optional[str] = None
    subrace: Optional[str] = None
    char_class: Optional[str] = Field(None, alias="class")
    subclass: Optional[str] = None
    level: Optional[int] = Field(None, ge=1, le=20)
    background: Optional[str] = None
    alignment: Optional[str] = None
    ability_scores: Optional[Dict[str, int]] = None
    hit_points: Optional[int] = Field(None, ge=1)
    armor_class: Optional[int] = Field(None, ge=1)
    speed: Optional[int] = Field(None, ge=0)
    experience: Optional[int] = Field(None, ge=0)
    skill_proficiencies: Optional[List[str]] = None
    proficiencies: Optional[Dict[str, Any]] = None
    features: Optional[List[Dict[str, Any]]] = None
    equipment: Optional[List[Dict[str, Any]]] = None
    languages: Optional[List[str]] = None
    physical_description: Optional[str] = None
    personality_traits: Optional[str] = None
    ideals: Optional[str] = None
    bonds: Optional[str] = None
    flaws: Optional[str] = None
    backstory: Optional[str] = None

    @field_validator("proficiencies", mode="before")
    def merge_skill_proficiencies(cls, v: Any, values: Any) -> Optional[Dict[str, Any]]:
        """Merge skill_proficiencies into proficiencies dict if provided."""
        if "skill_proficiencies" in values.data:
            skills = values.data["skill_proficiencies"]
            if skills is not None:
                if v is None:
                    v = {}
                v["skills"] = skills
        return v  # type: ignore[no-any-return]

    model_config = ConfigDict(populate_by_name=True)


# Campaign endpoint requests
class CampaignTemplateCreateRequest(BaseModel):
    """Request for creating campaign templates."""

    # Basic info
    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    description: str = Field(..., description="Campaign description")
    campaign_goal: str = Field(..., description="Main campaign objective")

    # Starting conditions
    starting_location: Dict[str, Any] = Field(
        ..., description="Starting location details"
    )
    opening_narrative: str = Field(..., description="Opening story text")
    starting_level: int = Field(1, ge=1, le=20, description="Starting character level")
    difficulty: str = Field(
        "normal",
        description="Campaign difficulty",
        pattern="^(easy|normal|hard|deadly)$",
    )

    # Optional fields
    ruleset_id: Optional[str] = Field(
        "dnd5e_standard", description="Ruleset identifier"
    )
    lore_id: Optional[str] = Field("generic_fantasy", description="Lore identifier")
    theme_mood: Optional[str] = Field(None, description="Campaign theme and mood")
    xp_system: Optional[str] = Field(
        "milestone", description="XP system", pattern="^(milestone|xp)$"
    )

    # Rules and restrictions
    house_rules: Optional[Dict[str, Any]] = Field(None, description="House rules")
    allowed_races: Optional[List[str]] = Field(None, description="Allowed race IDs")
    allowed_classes: Optional[List[str]] = Field(None, description="Allowed class IDs")
    starting_gold_range: Optional[Dict[str, int]] = Field(
        None, description="Starting gold range"
    )

    # Content management
    content_pack_ids: Optional[List[str]] = Field(
        None, description="Content pack IDs for this campaign"
    )

    # TTS settings
    narration_enabled: Optional[bool] = Field(
        False, description="Enable narration by default"
    )
    tts_voice: Optional[str] = Field("af_heart", description="Default TTS voice")

    # Additional info
    tags: Optional[List[str]] = Field(None, description="Campaign tags")
    session_zero_notes: Optional[str] = Field(None, description="Session zero notes")
    world_map_path: Optional[str] = Field(None, description="Path to world map image")


class CampaignTemplateUpdateRequest(BaseModel):
    """Request for updating campaign templates.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    campaign_goal: Optional[str] = None
    starting_location: Optional[Dict[str, Any]] = None
    opening_narrative: Optional[str] = None
    starting_level: Optional[int] = Field(None, ge=1, le=20)
    difficulty: Optional[str] = Field(None, pattern="^(easy|normal|hard|deadly)$")
    ruleset_id: Optional[str] = None
    lore_id: Optional[str] = None
    theme_mood: Optional[str] = None
    xp_system: Optional[str] = Field(None, pattern="^(milestone|xp)$")
    house_rules: Optional[Dict[str, Any]] = None
    allowed_races: Optional[List[str]] = None
    allowed_classes: Optional[List[str]] = None
    starting_gold_range: Optional[Dict[str, int]] = None
    content_pack_ids: Optional[List[str]] = None
    narration_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None
    tags: Optional[List[str]] = None
    session_zero_notes: Optional[str] = None
    world_map_path: Optional[str] = None


class CampaignInstanceCreateRequest(BaseModel):
    """Request for creating a campaign instance (active game)."""

    name: str = Field(
        ..., min_length=1, max_length=200, description="Campaign instance name"
    )
    template_id: Optional[str] = Field(
        None, description="Template ID if created from template"
    )
    character_ids: List[str] = Field(
        ..., description="Character template IDs for the party"
    )

    # Optional initial state
    current_location: Optional[str] = Field("Unknown", description="Starting location")
    content_pack_priority: Optional[List[str]] = Field(
        None, description="Content pack priority order"
    )

    # TTS settings override
    narration_enabled: Optional[bool] = Field(
        None, description="Campaign-specific narration override"
    )
    tts_voice: Optional[str] = Field(
        None, description="Campaign-specific TTS voice override"
    )


class CampaignInstanceUpdateRequest(BaseModel):
    """Request for updating a campaign instance.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    character_ids: Optional[List[str]] = Field(
        None, description="Updated character list"
    )
    current_location: Optional[str] = None
    content_pack_priority: Optional[List[str]] = None
    narration_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None


# Game endpoint requests
class PlayerActionRequest(BaseModel):
    """Request for player actions."""

    action_type: str = Field(..., description="Action type (e.g., 'free_text')")
    value: str = Field(..., description="The actual action text")
    character_id: Optional[str] = Field(None, description="Optional character ID")


class SubmitRollsRequest(BaseModel):
    """Unified request model for dice roll submissions.

    Handles both legacy format (roll requests) and new format (computed results).
    """

    # New format with pre-computed results
    roll_results: Optional[List[DiceRollResultResponseModel]] = Field(
        None, description="Pre-computed roll results"
    )

    # Legacy format with roll requests
    rolls: Optional[Union[List[DiceRollSubmissionModel], DiceRollSubmissionModel]] = (
        Field(None, description="Roll requests to be processed")
    )

    @field_validator("rolls", "roll_results")
    def validate_one_format(
        cls, v: Any, values: Any
    ) -> Optional[
        Union[
            List[DiceRollResultResponseModel],
            List[DiceRollSubmissionModel],
            DiceRollSubmissionModel,
        ]
    ]:
        """Ensure only one format is provided."""
        if v is not None:
            other_field = "roll_results" if "rolls" in str(v) else "rolls"
            if other_field in values.data and values.data[other_field] is not None:
                raise ValueError("Cannot provide both roll_results and rolls")
        return v  # type: ignore[no-any-return]


class PerformRollRequest(BaseModel):
    """Request for performing a dice roll."""

    character_id: str = Field(..., description="Character performing roll")
    roll_type: str = Field(..., description="Type of roll")
    dice_formula: str = Field(..., description="Dice formula (e.g., '1d20+5')")
    skill: Optional[str] = Field(None, description="Skill for skill checks")
    ability: Optional[str] = Field(None, description="Ability for ability checks")
    dc: Optional[int] = Field(None, description="Difficulty class")
    reason: str = Field("", description="Reason for the roll")
    request_id: Optional[str] = Field(None, description="Original request ID")


class LoadGameRequest(BaseModel):
    """Request for loading a saved game state."""

    save_file: str = Field(..., description="Path to the save file to load")


# Config endpoint doesn't need request models (GET only)


# Campaign endpoints
class CreateCampaignFromTemplateRequest(BaseModel):
    """Request for creating a campaign instance from a template."""

    campaign_name: str = Field(
        ..., min_length=1, max_length=200, description="Campaign instance name"
    )

    # Optional overrides from template
    character_ids: Optional[List[str]] = Field(
        None, description="Character IDs for the party"
    )
    narration_enabled: Optional[bool] = Field(
        None, description="Override template narration setting"
    )
    tts_voice: Optional[str] = Field(None, description="Override template TTS voice")


# Content endpoints
class ContentUploadItem(BaseModel):
    """Individual content item for upload."""

    id: str = Field(..., description="Unique item ID")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    # Additional fields depend on content type but we'll keep it flexible
    data: Dict[str, Any] = Field(..., description="Content-specific data")


class ContentUploadRequest(BaseModel):
    """Request for uploading content to a pack."""

    items: Union[List[ContentUploadItem], ContentUploadItem] = Field(
        ..., description="Single item or list of items to upload"
    )

    @field_validator("items", mode="before")
    def ensure_list(cls, v: Any) -> List[ContentUploadItem]:
        """Ensure items is always a list."""
        if isinstance(v, dict):
            # Single item provided
            return [ContentUploadItem(**v)]
        return v  # type: ignore[no-any-return]


class ContentPackCreateRequest(BaseModel):
    """Request for creating a content pack."""

    id: str = Field(
        ..., min_length=1, max_length=100, description="Unique content pack ID"
    )
    name: str = Field(..., min_length=1, max_length=200, description="Display name")
    description: str = Field(..., description="Content pack description")
    source: str = Field(
        ..., description="Source of the content (e.g., 'WotC', 'Homebrew')"
    )
    version: str = Field("1.0.0", description="Content pack version")
    author: Optional[str] = Field(None, description="Content pack author")
    url: Optional[str] = Field(None, description="URL for more information")
    enabled: bool = Field(True, description="Whether the pack is enabled by default")
    priority: int = Field(0, ge=0, description="Priority for content resolution")
    tags: Optional[List[str]] = Field(None, description="Content pack tags")


class ContentPackUpdateRequest(BaseModel):
    """Request for updating a content pack.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    source: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None


# D5E endpoints use query parameters, no request bodies needed
