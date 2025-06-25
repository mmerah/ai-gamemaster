"""
API models package.

This package contains request and response models for FastAPI endpoints.
"""

# Import all request models
from app.models.api.requests import (
    ContentUploadItem,
    ContentUploadRequest,
    CreateCampaignFromTemplateRequest,
    PerformRollRequest,
    PlayerActionRequest,
    RAGQueryRequest,
    SubmitRollsRequest,
)

# Import all response models
from app.models.api.responses import (
    AdventureCharacterData,
    AdventureInfo,
    CharacterAdventuresResponse,
    CharacterCreationOptionsData,
    CharacterCreationOptionsMetadata,
    CharacterCreationOptionsResponse,
    ContentPackItemsResponse,
    ContentPackStatistics,
    ContentPackWithStatisticsResponse,
    ContentUploadResponse,
    ContentUploadResult,
    CreateCampaignFromTemplateResponse,
    RAGQueryResponse,
    SaveGameResponse,
    SSEHealthResponse,
    StartCampaignResponse,
    SuccessResponse,
)

__all__ = [
    # Request models
    "ContentUploadItem",
    "ContentUploadRequest",
    "CreateCampaignFromTemplateRequest",
    "PerformRollRequest",
    "PlayerActionRequest",
    "RAGQueryRequest",
    "SubmitRollsRequest",
    # Response models
    "AdventureCharacterData",
    "AdventureInfo",
    "CharacterAdventuresResponse",
    "CharacterCreationOptionsData",
    "CharacterCreationOptionsMetadata",
    "CharacterCreationOptionsResponse",
    "ContentPackItemsResponse",
    "ContentPackStatistics",
    "ContentPackWithStatisticsResponse",
    "ContentUploadResponse",
    "ContentUploadResult",
    "CreateCampaignFromTemplateResponse",
    "RAGQueryResponse",
    "SaveGameResponse",
    "SSEHealthResponse",
    "StartCampaignResponse",
    "SuccessResponse",
]
