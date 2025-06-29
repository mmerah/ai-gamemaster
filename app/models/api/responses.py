"""
API response models for type-safe FastAPI endpoints.

This module contains all response models used by FastAPI routes to ensure
type safety and automatic API documentation generation.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field, computed_field, field_serializer

from app.content.schemas.character import D5eBackground, D5eClass, D5eRace
from app.content.schemas.content_pack import D5eContentPack
from app.content.schemas.mechanics import (
    D5eAbilityScore,
    D5eAlignment,
    D5eLanguage,
    D5eSkill,
)
from app.models.campaign.instance import CampaignInstanceModel
from app.models.game_state.main import GameStateModel
from app.models.rag import RAGResults

# Generic type for list responses
T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


# Character endpoint responses
class CharacterCreationOptionsData(BaseModel):
    """Character creation options data.

    Since FastAPI will serialize the models to JSON automatically,
    we can use the actual D5e model types here for better type safety.
    The frontend will receive the same JSON structure.
    """

    races: List[D5eRace] = Field(..., description="Available races")
    classes: List[D5eClass] = Field(..., description="Available classes")
    backgrounds: List[D5eBackground] = Field(..., description="Available backgrounds")
    alignments: List[D5eAlignment] = Field(..., description="Available alignments")
    languages: List[D5eLanguage] = Field(..., description="Available languages")
    skills: List[D5eSkill] = Field(..., description="Available skills")
    ability_scores: List[D5eAbilityScore] = Field(
        ..., description="Ability score options"
    )


class CharacterCreationOptionsMetadata(BaseModel):
    """Metadata for character creation options."""

    content_pack_ids: Optional[List[str]] = Field(
        None, description="Content packs used for filtering"
    )
    total_races: int = Field(..., description="Total number of races")
    total_classes: int = Field(..., description="Total number of classes")
    total_backgrounds: int = Field(..., description="Total number of backgrounds")


class CharacterCreationOptionsResponse(BaseModel):
    """Response for GET /character_templates/options."""

    options: CharacterCreationOptionsData = Field(
        ..., description="Available character creation options"
    )
    metadata: CharacterCreationOptionsMetadata = Field(
        ..., description="Metadata about the options"
    )


class AdventureCharacterData(BaseModel):
    """Character data within an adventure."""

    current_hp: int = Field(..., description="Character's current hit points")
    max_hp: int = Field(..., description="Character's maximum hit points")
    level: int = Field(..., description="Character's level")
    class_name: str = Field(..., alias="class", description="Character's class name")
    experience: int = Field(..., description="Character's experience points")


class AdventureInfo(BaseModel):
    """Information about a character's adventure/campaign."""

    campaign_id: Optional[str] = Field(
        None, description="Unique identifier for the campaign"
    )
    campaign_name: Optional[str] = Field(None, description="Name of the campaign")
    template_id: Optional[str] = Field(None, description="Character template ID used")
    last_played: Optional[str] = Field(
        None, description="ISO timestamp of last play session"
    )
    created_date: Optional[str] = Field(
        None, description="ISO timestamp of campaign creation"
    )
    session_count: int = Field(0, description="Number of play sessions")
    current_location: Optional[str] = Field(
        None, description="Current location in the campaign"
    )
    in_combat: bool = Field(
        False, description="Whether the party is currently in combat"
    )
    character_data: AdventureCharacterData = Field(
        ..., description="Character status data"
    )


class CharacterAdventuresResponse(BaseModel):
    """Response for GET /character_templates/{id}/adventures."""

    character_name: str = Field(..., description="Name of the character template")
    adventures: List[AdventureInfo] = Field(
        ..., description="List of adventures/campaigns"
    )


# Campaign endpoint responses
class StartCampaignResponse(BaseModel):
    """Response for POST /campaigns/start."""

    message: str = Field(..., description="Success message")
    initial_state: GameStateModel = Field(
        ..., description="Initial game state for the campaign"
    )


# Content endpoint responses
class ContentPackStatistics(BaseModel):
    """Statistics for a content pack."""

    total_items: int = Field(..., description="Total number of content items")
    items_by_type: Dict[str, int] = Field(
        ..., description="Item counts by content type"
    )


class ContentPackWithStatisticsResponse(D5eContentPack):
    """Content pack with statistics."""

    statistics: ContentPackStatistics = Field(
        ..., description="Statistics about the content pack"
    )


class ContentPackUsageStatistics(BaseModel):
    """Usage statistics for content packs."""

    pack_id: str = Field(..., description="Content pack ID")
    pack_name: str = Field(..., description="Content pack name")
    character_count: int = Field(
        ..., description="Number of characters using this pack"
    )


# Game endpoint responses (mostly reuse GameEventResponseModel)
class SaveGameResponse(BaseModel):
    """Response for POST /game_state/save."""

    success: bool = Field(..., description="Whether the save was successful")
    save_file: str = Field(..., description="Path to the saved game file")
    message: str = Field(..., description="Success or error message")
    campaign_id: Optional[str] = Field(None, description="ID of the saved campaign")


# SSE endpoint responses
class SSEHealthResponse(BaseModel):
    """Response for SSE health check endpoint."""

    status: str = Field(..., description="Health status")
    queue_size: int = Field(..., description="Current event queue size")
    timestamp: float = Field(..., description="Current timestamp")


# Content pack upload responses
class ContentUploadResult(BaseModel):
    """Result of uploading a single content item."""

    item_id: str = Field(..., description="Item identifier")
    success: bool = Field(..., description="Whether upload succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    warnings: Optional[List[str]] = Field(None, description="Validation warnings")


class ContentUploadResponse(BaseModel):
    """Response for POST /content/packs/{pack_id}/upload/{content_type}."""

    success: bool = Field(..., description="Overall upload success")
    uploaded_count: int = Field(
        ..., description="Number of items successfully uploaded"
    )
    failed_count: int = Field(0, description="Number of items that failed")
    results: List[ContentUploadResult] = Field(
        ..., description="Individual item results"
    )


class ContentPackItemsResponse(BaseModel):
    """Response for GET /content/packs/{pack_id}/content."""

    items: Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]] = Field(
        ..., description="Content items - list for single type, dict for all types"
    )
    total: Optional[int] = Field(
        None, description="Total number of items (single type)"
    )
    totals: Optional[Dict[str, int]] = Field(
        None, description="Item counts by type (all types)"
    )
    page: Optional[int] = Field(None, description="Current page (single type)")
    per_page: Optional[int] = Field(None, description="Items per page (single type)")
    content_type: Optional[str] = Field(
        None, description="Content type - 'all' or specific type"
    )
    offset: int = Field(0, description="Pagination offset")
    limit: int = Field(50, description="Pagination limit")


# Campaign template creation response
class CreateCampaignFromTemplateResponse(BaseModel):
    """Response for POST /campaign_templates/{template_id}/create_campaign."""

    success: bool = Field(True, description="Operation success")
    campaign: CampaignInstanceModel = Field(
        ..., description="Created campaign instance"
    )
    message: str = Field(..., description="Success message")


# RAG endpoint responses
class RAGQueryResponse(BaseModel):
    """Response model for RAG queries."""

    results: RAGResults = Field(..., description="RAG query results")
    query_info: Dict[str, Any] = Field(
        ..., description="Debug information about the query"
    )
    used_content_packs: List[str] = Field(
        ..., description="Content packs that were used"
    )
