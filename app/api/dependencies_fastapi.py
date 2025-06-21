"""
FastAPI dependency injection functions.

These replace the get_* functions used in Flask routes.
"""

from typing import Optional, cast

from fastapi import Depends, Request

from app.content.protocols import DatabaseManagerProtocol
from app.core.ai_interfaces import IRAGService
from app.core.container import ServiceContainer, get_container
from app.core.content_interfaces import IContentService
from app.core.domain_interfaces import (
    ICampaignService,
    ICharacterService,
    IChatService,
    ICombatService,
    IDiceRollingService,
)
from app.core.external_interfaces import ITTSIntegrationService, ITTSService
from app.core.orchestration_interfaces import IGameOrchestrator
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICampaignTemplateRepository,
    ICharacterTemplateRepository,
    IGameStateRepository,
)
from app.core.system_interfaces import IEventQueue
from app.providers.ai.base import BaseAIService
from app.services.shared_state_manager import SharedStateManager
from app.settings import Settings


def get_settings(request: Request) -> Settings:
    """Get settings from app state."""
    return cast(Settings, request.app.state.settings)


def get_container_dep() -> ServiceContainer:
    """Get service container."""
    return get_container()


def get_game_orchestrator(
    container: ServiceContainer = Depends(get_container_dep),
) -> IGameOrchestrator:
    """Get game orchestrator service."""
    return container.get_game_orchestrator()


def get_character_template_repository(
    container: ServiceContainer = Depends(get_container_dep),
) -> ICharacterTemplateRepository:
    """Get character template repository."""
    return container.get_character_template_repository()


def get_game_state_repository(
    container: ServiceContainer = Depends(get_container_dep),
) -> IGameStateRepository:
    """Get game state repository."""
    return container.get_game_state_repository()


def get_campaign_template_repository(
    container: ServiceContainer = Depends(get_container_dep),
) -> ICampaignTemplateRepository:
    """Get campaign template repository."""
    return container.get_campaign_template_repository()


def get_campaign_instance_repository(
    container: ServiceContainer = Depends(get_container_dep),
) -> ICampaignInstanceRepository:
    """Get campaign instance repository."""
    return container.get_campaign_instance_repository()


def get_content_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> IContentService:
    """Get content service."""
    return container.get_content_service()


def get_database_manager(
    container: ServiceContainer = Depends(get_container_dep),
) -> DatabaseManagerProtocol:
    """Get database manager."""
    return container.get_database_manager()


def get_event_queue(
    container: ServiceContainer = Depends(get_container_dep),
) -> IEventQueue:
    """Get event queue."""
    return container.get_event_queue()


def get_tts_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> Optional[ITTSService]:
    """Get TTS service."""
    return container.get_tts_service()


def get_ai_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> Optional[BaseAIService]:
    """Get AI service."""
    return container.get_ai_service()


def get_shared_state_manager(
    container: ServiceContainer = Depends(get_container_dep),
) -> SharedStateManager:
    """Get shared state manager."""
    return container.get_shared_state_manager()


def get_character_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> ICharacterService:
    """Get character service."""
    return container.get_character_service()


def get_dice_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> IDiceRollingService:
    """Get dice rolling service."""
    return container.get_dice_service()


def get_combat_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> ICombatService:
    """Get combat service."""
    return container.get_combat_service()


def get_chat_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> IChatService:
    """Get chat service."""
    return container.get_chat_service()


def get_rag_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> IRAGService:
    """Get RAG service."""
    return container.get_rag_service()


def get_tts_integration_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> ITTSIntegrationService:
    """Get TTS integration service."""
    return container.get_tts_integration_service()


def get_campaign_service(
    container: ServiceContainer = Depends(get_container_dep),
) -> ICampaignService:
    """Get campaign service."""
    return container.get_campaign_service()
