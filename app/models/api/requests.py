"""
API request models for type-safe FastAPI endpoints.

This module contains all request models used by FastAPI routes to ensure
type safety and automatic request validation.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.game_state.main import GameStateModel


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
    character_levels: Optional[Dict[str, int]] = Field(
        None, description="Starting levels for each character (character_id -> level)"
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


# RAG endpoints
class RAGQueryRequest(BaseModel):
    """Request model for RAG queries."""

    query: str = Field(..., description="The query text (player action)")
    campaign_id: Optional[str] = Field(
        None,
        description="Campaign ID to get game state and content packs (optional for testing)",
    )
    kb_types: Optional[List[str]] = Field(
        None, description="Filter by knowledge base types"
    )
    max_results: Optional[int] = Field(
        5, description="Maximum number of results to return"
    )

    # Override options for testing
    override_content_packs: Optional[List[str]] = Field(
        None, description="Override content pack priority for testing"
    )
    override_game_state: Optional[GameStateModel] = Field(
        None, description="Override game state for testing"
    )
