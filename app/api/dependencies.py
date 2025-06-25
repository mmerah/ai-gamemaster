"""
Centralized dependency injection for API routes.

This module provides getter functions for all services and repositories
used across API routes, eliminating duplicate code.
"""

from typing import Optional

from app.core.ai_interfaces import IRAGService
from app.core.container import get_container
from app.core.content_interfaces import (
    IContentPackService,
    IContentService,
    IIndexingService,
)
from app.core.domain_interfaces import (
    ICampaignService,
    ICharacterService,
    IDiceRollingService,
)
from app.core.external_interfaces import ITTSIntegrationService, ITTSService
from app.core.orchestration_interfaces import IGameOrchestrator
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICampaignTemplateRepository,
    ICharacterInstanceRepository,
    ICharacterTemplateRepository,
    IGameStateRepository,
)
from app.core.system_interfaces import IEventQueue
from app.settings import Settings

# --- Service Getters (return interfaces) ---


def get_game_orchestrator() -> IGameOrchestrator:
    """Get game orchestrator instance."""
    return get_container().get_game_orchestrator()


def get_campaign_service() -> ICampaignService:
    """Get campaign service instance."""
    return get_container().get_campaign_service()


def get_content_service() -> IContentService:
    """Get content service instance."""
    return get_container().get_content_service()


def get_character_service() -> ICharacterService:
    """Get character service instance."""
    return get_container().get_character_service()


def get_dice_service() -> IDiceRollingService:
    """Get dice service instance."""
    return get_container().get_dice_service()


def get_tts_service() -> Optional[ITTSService]:
    """Get TTS service instance."""
    return get_container().get_tts_service()


def get_tts_integration_service() -> ITTSIntegrationService:
    """Get TTS integration service instance."""
    return get_container().get_tts_integration_service()


# --- Repository Getters (return interfaces) ---


def get_campaign_template_repository() -> ICampaignTemplateRepository:
    """Get campaign template repository instance."""
    return get_container().get_campaign_template_repository()


def get_campaign_instance_repository() -> ICampaignInstanceRepository:
    """Get campaign instance repository instance."""
    return get_container().get_campaign_instance_repository()


def get_character_template_repository() -> ICharacterTemplateRepository:
    """Get character template repository instance."""
    return get_container().get_character_template_repository()


def get_character_instance_repository() -> ICharacterInstanceRepository:
    """Get character instance repository instance."""
    # Character instances are managed through character service
    return get_container()._create_character_instance_repository()


def get_game_state_repository() -> IGameStateRepository:
    """Get game state repository instance."""
    return get_container().get_game_state_repository()


# --- Other Dependencies ---


def get_event_queue() -> IEventQueue:
    """Get event queue instance."""
    queue = get_container().get_event_queue()
    # EventQueue implements IEventQueue interface
    return queue


def get_content_pack_service() -> IContentPackService:
    """Get content pack service instance."""
    return get_container().get_content_pack_service()


def get_indexing_service() -> IIndexingService:
    """Get indexing service instance."""
    return get_container().get_indexing_service()


def get_settings() -> Settings:
    """Get application settings instance."""
    return get_container().settings


def get_rag_service() -> IRAGService:
    """Get RAG service instance."""
    return get_container().get_rag_service()
