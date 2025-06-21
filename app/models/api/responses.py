"""
API response models for type-safe FastAPI endpoints.

This module contains all response models used by FastAPI routes to ensure
type safety and automatic API documentation generation.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, computed_field, field_serializer

from app.content.schemas.character import D5eBackground, D5eClass, D5eRace
from app.content.schemas.content_pack import D5eContentPack
from app.content.schemas.mechanics import (
    D5eAbilityScore,
    D5eAlignment,
    D5eLanguage,
    D5eSkill,
)
from app.models.campaign import CampaignInstanceModel
from app.models.events.game_events import GameEventResponseModel
from app.models.game_state import GameStateModel

# Re-export GameEventResponseModel for convenience
__all__ = ["GameEventResponseModel"]

# Generic type for list responses
T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    """Generic list response wrapper."""

    items: List[T]
    total: Optional[int] = Field(None, description="Total number of items")


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

    options: CharacterCreationOptionsData
    metadata: CharacterCreationOptionsMetadata


class AdventureCharacterData(BaseModel):
    """Character data within an adventure."""

    current_hp: int
    max_hp: int
    level: int
    class_name: str = Field(..., alias="class")
    experience: int


class AdventureInfo(BaseModel):
    """Information about a character's adventure/campaign."""

    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    template_id: Optional[str] = None
    last_played: Optional[str] = None
    created_date: Optional[str] = None
    session_count: int = 0
    current_location: Optional[str] = None
    in_combat: bool = False
    character_data: AdventureCharacterData


class CharacterAdventuresResponse(BaseModel):
    """Response for GET /character_templates/{id}/adventures."""

    character_name: str
    adventures: List[AdventureInfo]


# Campaign endpoint responses
class CampaignInstanceResponse(CampaignInstanceModel):
    """Campaign instance response model with computed fields."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def party_size(self) -> int:
        """Compute party size from character_ids."""
        return len(self.character_ids)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def created_at(self) -> Optional[str]:
        """Alias for created_date for frontend compatibility."""
        return self.created_date.isoformat() if self.created_date else None

    @field_serializer("created_date", "last_played")
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return dt.isoformat() if dt else None


class StartCampaignResponse(BaseModel):
    """Response for POST /campaigns/start."""

    message: str
    initial_state: GameStateModel


# Content endpoint responses
class ContentPackStatistics(BaseModel):
    """Statistics for a content pack."""

    total_items: int = Field(..., description="Total number of content items")
    items_by_type: Dict[str, int] = Field(
        ..., description="Item counts by content type"
    )


class ContentPackWithStatisticsResponse(D5eContentPack):
    """Content pack with statistics."""

    statistics: ContentPackStatistics


# Config endpoint response
class ConfigData(BaseModel):
    """Configuration data."""

    # AI Settings
    AI_PROVIDER: str
    AI_RESPONSE_PARSING_MODE: str
    AI_MAX_RETRIES: int
    AI_RETRY_DELAY: float
    AI_REQUEST_TIMEOUT: int
    AI_RETRY_CONTEXT_TIMEOUT: int
    AI_TEMPERATURE: float
    AI_MAX_TOKENS: int
    LLAMA_SERVER_URL: Optional[str] = None
    OPENROUTER_MODEL_NAME: Optional[str] = None
    OPENROUTER_BASE_URL: Optional[str] = None

    # Token Budget
    MAX_PROMPT_TOKENS_BUDGET: int
    LAST_X_HISTORY_MESSAGES: int
    MAX_AI_CONTINUATION_DEPTH: int
    TOKENS_PER_MESSAGE_OVERHEAD: int

    # Storage Settings
    GAME_STATE_REPO_TYPE: str
    CHARACTER_TEMPLATES_DIR: str
    CAMPAIGN_TEMPLATES_DIR: str
    CAMPAIGNS_DIR: str

    # Feature Flags
    RAG_ENABLED: bool
    TTS_PROVIDER: str
    TTS_CACHE_DIR_NAME: str
    KOKORO_LANG_CODE: str
    FLASK_DEBUG: bool

    # RAG Settings
    RAG_MAX_RESULTS_PER_QUERY: int
    RAG_EMBEDDINGS_MODEL: str
    RAG_SCORE_THRESHOLD: float
    RAG_MAX_TOTAL_RESULTS: int
    RAG_CHUNK_SIZE: int
    RAG_CHUNK_OVERLAP: int
    RAG_COLLECTION_NAME_PREFIX: str
    RAG_METADATA_FILTERING_ENABLED: bool
    RAG_RELEVANCE_FEEDBACK_ENABLED: bool
    RAG_CACHE_TTL: int

    # SSE Settings
    SSE_HEARTBEAT_INTERVAL: int
    SSE_EVENT_TIMEOUT: int
    EVENT_QUEUE_MAX_SIZE: int

    # Logging
    LOG_LEVEL: str
    LOG_FILE: Optional[str] = None

    # Computed values
    VERSION: str
    ENVIRONMENT: str


class ConfigResponse(BaseModel):
    """Response for GET /config."""

    success: bool
    config: ConfigData


# Game endpoint responses (mostly reuse GameEventResponseModel)
class SaveGameResponse(BaseModel):
    """Response for POST /game_state/save."""

    success: bool
    save_file: str
    message: str


class LoadGameResponse(BaseModel):
    """Response for POST /game_state/load."""

    success: bool
    message: str
    game_state: Optional[Dict[str, Any]] = Field(
        None, description="Loaded game state data"
    )


# D5E endpoint responses
class ContentItem(BaseModel):
    """Generic D&D 5e content item."""

    id: str
    name: str
    content_type: str
    description: Optional[str] = None
    source: Optional[str] = None


class ContentListResponse(BaseModel):
    """Response for GET /d5e/content."""

    items: List[
        Dict[str, Any]
    ]  # Keep as dict for flexibility with different content types
    total: int
    content_type: str


# SSE endpoint responses
class SSEConnectionResponse(BaseModel):
    """Response for SSE connection establishment."""

    client_id: str = Field(..., description="Unique client identifier")
    connection_status: str = Field("connected", description="Connection status")
    message: str = Field(..., description="Connection message")


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

    items: List[Dict[str, Any]] = Field(..., description="Content items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    content_type: Optional[str] = Field(None, description="Filtered content type")


class SupportedContentTypesResponse(BaseModel):
    """Response for GET /content/supported-types."""

    content_types: List[str] = Field(..., description="List of supported content types")
    descriptions: Dict[str, str] = Field(..., description="Human-readable descriptions")


# Campaign template creation response
class CreateCampaignFromTemplateResponse(BaseModel):
    """Response for POST /campaign_templates/{template_id}/create_campaign."""

    success: bool = Field(True, description="Operation success")
    campaign: CampaignInstanceModel = Field(
        ..., description="Created campaign instance"
    )
    message: str = Field(..., description="Success message")


# Dice roll responses
class DiceRollResponse(BaseModel):
    """Response for POST /perform_roll."""

    success: bool
    error: Optional[str] = None
