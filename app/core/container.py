"""
Dependency injection container for the application.
"""

import logging
from typing import Any, Dict, Optional, Union

from app.core.event_queue import EventQueue
from app.core.interfaces import (
    AIResponseProcessor,
    BaseTTSService,
    CharacterService,
    ChatService,
    CombatService,
    DiceRollingService,
    GameStateRepository,
)
from app.core.rag_interfaces import RAGService
from app.models import ServiceConfigModel
from app.repositories.campaign_instance_repository import CampaignInstanceRepository
from app.repositories.campaign_template_repository import CampaignTemplateRepository
from app.repositories.character_template_repository import CharacterTemplateRepository

# Import D5e services
from app.repositories.d5e.repository_hub import D5eRepositoryHub
from app.repositories.game_state_repository import GameStateRepositoryFactory
from app.repositories.in_memory_campaign_instance_repository import (
    InMemoryCampaignInstanceRepository,
)
from app.services.campaign_service import CampaignService
from app.services.character_service import CharacterServiceImpl
from app.services.chat_service import ChatServiceImpl
from app.services.combat_service import CombatServiceImpl
from app.services.d5e.data_loader import D5eDataLoader
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import D5eReferenceResolver
from app.services.d5e_data_service import D5eDataService
from app.services.dice_service import DiceRollingServiceImpl
from app.services.game_events import GameEventManager
from app.services.response_processors.ai_response_processor_impl import (
    AIResponseProcessorImpl,
)
from app.services.tts_integration_service import TTSIntegrationService

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Container for managing service dependencies."""

    def __init__(
        self, config: Optional[Union[Dict[str, Any], ServiceConfigModel]] = None
    ):
        self.config: Union[Dict[str, Any], ServiceConfigModel] = (
            config if config is not None else {}
        )
        self._initialized = False

    def _get_config_value(self, key: str, default: Any) -> Any:
        """Get config value handling both dict and object configs."""
        if isinstance(self.config, dict):
            return self.config.get(key, default)
        else:
            return getattr(self.config, key, default)

    def initialize(self) -> None:
        """Initialize all services with proper dependency injection."""
        if self._initialized:
            return

        logger.info("Initializing service container...")

        # Create event queue (needed by many services)
        max_size_value = self._get_config_value("EVENT_QUEUE_MAX_SIZE", 0)
        max_size = int(max_size_value) if isinstance(max_size_value, (int, str)) else 0
        self._event_queue = EventQueue(maxsize=max_size)

        # Create repositories
        self._game_state_repo = self._create_game_state_repository()
        # Campaign repository removed - using campaign_template_repo instead
        self._campaign_instance_repo = self._create_campaign_instance_repository()
        self._character_template_repo = self._create_character_template_repository()
        self._campaign_template_repo = self._create_campaign_template_repository()
        # Ruleset and lore repositories removed - using utility functions instead

        # Create TTS Service first (needed by chat service)
        self._tts_service = self._create_tts_service()
        self._tts_integration_service = self._create_tts_integration_service()

        # Create core services
        self._character_service = self._create_character_service()
        self._dice_service = self._create_dice_service()
        self._combat_service = self._create_combat_service()
        self._chat_service = self._create_chat_service()

        # Create campaign management services
        self._campaign_service = self._create_campaign_service()

        # Create RAG service
        self._rag_service = self._create_rag_service()

        # Create higher-level services
        self._ai_response_processor = self._create_ai_response_processor()
        self._game_event_manager = self._create_game_event_manager()

        # Create D5e services
        self._d5e_data_loader = self._create_d5e_data_loader()
        self._d5e_reference_resolver = self._create_d5e_reference_resolver()
        self._d5e_index_builder = self._create_d5e_index_builder()
        self._d5e_repository_hub = self._create_d5e_repository_hub()
        self._d5e_data_service = self._create_d5e_data_service()

        self._initialized = True
        logger.info("Service container initialized successfully.")

    def get_game_state_repository(self) -> GameStateRepository:
        """Get the game state repository."""
        self._ensure_initialized()
        return self._game_state_repo

    # Campaign repository removed - use get_campaign_template_repository instead

    def get_character_template_repository(self) -> CharacterTemplateRepository:
        """Get the character template repository."""
        self._ensure_initialized()
        return self._character_template_repo

    def get_campaign_template_repository(self) -> CampaignTemplateRepository:
        """Get the campaign template repository."""
        self._ensure_initialized()
        return self._campaign_template_repo

    def get_campaign_instance_repository(
        self,
    ) -> InMemoryCampaignInstanceRepository | CampaignInstanceRepository:
        """Get the campaign instance repository."""
        self._ensure_initialized()
        return self._campaign_instance_repo

    def get_character_service(self) -> CharacterService:
        """Get the character service."""
        self._ensure_initialized()
        return self._character_service

    def get_dice_service(self) -> DiceRollingService:
        """Get the dice rolling service."""
        self._ensure_initialized()
        return self._dice_service

    def get_combat_service(self) -> CombatService:
        """Get the combat service."""
        self._ensure_initialized()
        return self._combat_service

    def get_chat_service(self) -> ChatService:
        """Get the chat service."""
        self._ensure_initialized()
        return self._chat_service

    def get_campaign_service(self) -> CampaignService:
        """Get the campaign service."""
        self._ensure_initialized()
        return self._campaign_service

    def get_tts_service(self) -> Optional[BaseTTSService]:
        """Get the TTS service."""
        self._ensure_initialized()
        return self._tts_service

    def get_tts_integration_service(self) -> TTSIntegrationService:
        """Get the TTS integration service."""
        self._ensure_initialized()
        return self._tts_integration_service

    def get_ai_response_processor(self) -> AIResponseProcessor:
        """Get the AI response processor."""
        self._ensure_initialized()
        return self._ai_response_processor

    def get_game_event_manager(self) -> GameEventManager:
        """Get the game event manager."""
        self._ensure_initialized()
        return self._game_event_manager

    def get_rag_service(self) -> RAGService:
        """Get the RAG service."""
        self._ensure_initialized()
        return self._rag_service

    def get_event_queue(self) -> EventQueue:
        """Get the event queue."""
        self._ensure_initialized()
        return self._event_queue

    def get_d5e_data_loader(self) -> D5eDataLoader:
        """Get the D5e data loader."""
        self._ensure_initialized()
        return self._d5e_data_loader

    def get_d5e_reference_resolver(self) -> D5eReferenceResolver:
        """Get the D5e reference resolver."""
        self._ensure_initialized()
        return self._d5e_reference_resolver

    def get_d5e_index_builder(self) -> D5eIndexBuilder:
        """Get the D5e index builder."""
        self._ensure_initialized()
        return self._d5e_index_builder

    def get_d5e_repository_hub(self) -> D5eRepositoryHub:
        """Get the D5e repository hub."""
        self._ensure_initialized()
        return self._d5e_repository_hub

    def get_d5e_data_service(self) -> D5eDataService:
        """Get the D5e data service."""
        self._ensure_initialized()
        return self._d5e_data_service

    def _ensure_initialized(self) -> None:
        """Ensure the container is initialized."""
        if not self._initialized:
            self.initialize()

    def _create_game_state_repository(self) -> GameStateRepository:
        """Create the game state repository."""
        repo_type = self._get_config_value("GAME_STATE_REPO_TYPE", "memory")
        base_save_dir = str(self._get_config_value("SAVES_DIR", "saves"))

        if repo_type == "file":
            return GameStateRepositoryFactory.create_repository(
                "file", base_save_dir=base_save_dir
            )
        else:
            # For in-memory repo, we'll set campaign_service later to avoid circular dependency
            return GameStateRepositoryFactory.create_repository(
                "memory", base_save_dir=base_save_dir
            )

    # Campaign repository removed - using campaign template repository instead

    def _create_character_template_repository(self) -> CharacterTemplateRepository:
        """Create the character template repository."""
        # Handle both dict and object config
        if isinstance(self.config, dict):
            templates_dir = str(
                self.config.get("CHARACTER_TEMPLATES_DIR", "saves/character_templates")
            )
        else:
            templates_dir = str(
                getattr(
                    self.config, "CHARACTER_TEMPLATES_DIR", "saves/character_templates"
                )
            )
        return CharacterTemplateRepository(templates_dir)

    def _create_campaign_template_repository(self) -> CampaignTemplateRepository:
        """Create the campaign template repository."""
        # Pass config as ServiceConfigModel
        if isinstance(self.config, dict):
            # Create a ServiceConfigModel from dict
            from app.models import ServiceConfigModel

            config_obj = ServiceConfigModel(**self.config)
            return CampaignTemplateRepository(config_obj)
        else:
            return CampaignTemplateRepository(self.config)

    def _create_campaign_instance_repository(
        self,
    ) -> InMemoryCampaignInstanceRepository | CampaignInstanceRepository:
        """Create the campaign instance repository."""
        # Use in-memory repository when in memory mode
        repo_type = self._get_config_value("GAME_STATE_REPO_TYPE", "memory")

        campaigns_dir = str(self._get_config_value("CAMPAIGNS_DIR", "saves/campaigns"))

        if repo_type == "memory":
            return InMemoryCampaignInstanceRepository(campaigns_dir)
        else:
            return CampaignInstanceRepository(campaigns_dir)

    def _create_character_service(self) -> CharacterService:
        """Create the character service."""
        return CharacterServiceImpl(self._game_state_repo)

    def _create_dice_service(self) -> DiceRollingService:
        """Create the dice rolling service."""
        return DiceRollingServiceImpl(self._character_service, self._game_state_repo)

    def _create_combat_service(self) -> CombatService:
        """Create the combat service."""
        return CombatServiceImpl(
            self._game_state_repo, self._character_service, self._event_queue
        )

    def _create_chat_service(self) -> ChatService:
        """Create the chat service."""
        return ChatServiceImpl(
            self._game_state_repo, self._event_queue, self._tts_integration_service
        )

    def _create_campaign_service(self) -> CampaignService:
        """Create the campaign service."""
        return CampaignService(
            self._campaign_template_repo,
            self._character_template_repo,
            self._campaign_instance_repo,
        )

    def _create_tts_service(self) -> Optional[BaseTTSService]:
        """Create the TTS service."""
        # Check if TTS is explicitly disabled in config
        tts_provider = self._get_config_value("TTS_PROVIDER", "kokoro").lower()
        if tts_provider in ("none", "disabled", "test"):
            logger.info("TTS provider disabled in configuration.")
            return None

        try:
            # Import conditionally to prevent startup crashes
            from app.tts_services.manager import get_tts_service

            # Pass config as ServiceConfigModel
            if isinstance(self.config, dict):
                # Create a ServiceConfigModel from dict
                from app.models import ServiceConfigModel

                config_obj = ServiceConfigModel(**self.config)
                return get_tts_service(config_obj)
            else:
                return get_tts_service(self.config)
        except ImportError as e:
            logger.warning(f"Could not import TTS manager: {e}. TTS will be disabled.")
            return None
        except Exception as e:
            logger.warning(f"Failed to create TTS service: {e}. TTS will be disabled.")
            return None

    def _create_tts_integration_service(self) -> TTSIntegrationService:
        """Create the TTS integration service."""
        return TTSIntegrationService(self._tts_service, self._game_state_repo)

    def _create_ai_response_processor(self) -> AIResponseProcessor:
        """Create the AI response processor."""
        return AIResponseProcessorImpl(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._event_queue,
        )

    def _create_rag_service(self) -> RAGService:
        """Create the LangChain-based RAG service."""
        global _global_rag_service_cache

        # Check if RAG is disabled in config (for testing)
        rag_enabled = self._get_config_value("RAG_ENABLED", True)
        if not rag_enabled:
            logger.info("RAG service disabled in configuration")
            # Return a no-op implementation
            from app.services.rag.no_op_rag_service import NoOpRAGService

            return NoOpRAGService()

        # Check global cache first to avoid reimport issues
        if _global_rag_service_cache is not None:
            logger.info("Using globally cached RAG service instance")
            # Update repository references if it has the attribute
            if hasattr(_global_rag_service_cache, "game_state_repo"):
                _global_rag_service_cache.game_state_repo = self._game_state_repo
            return _global_rag_service_cache

        try:
            # Lazy import to avoid loading heavy dependencies when RAG is disabled
            from app.services.rag.rag_service import RAGServiceImpl

            rag_service = RAGServiceImpl(game_state_repo=self._game_state_repo)

            # Configure search parameters
            rag_service.configure_filtering(
                max_results=5,  # Maximum total results
                score_threshold=0.3,  # Minimum similarity score
            )

            # Cache globally to avoid reimport issues
            _global_rag_service_cache = rag_service

            logger.info("LangChain RAG service initialized successfully")
            return rag_service
        except RuntimeError as e:
            if "already has a docstring" in str(e):
                logger.warning(
                    "Torch reimport issue detected, falling back to no-op RAG service"
                )
                from app.services.rag.no_op_rag_service import NoOpRAGService

                return NoOpRAGService()
            raise

    def _create_game_event_manager(self) -> GameEventManager:
        """Create the game event manager."""
        return GameEventManager(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._ai_response_processor,
            self._campaign_service,
            self._rag_service,
        )

    def _create_d5e_data_loader(self) -> D5eDataLoader:
        """Create the D5e data loader."""
        # Use default path to 5e-database submodule
        return D5eDataLoader()

    def _create_d5e_reference_resolver(self) -> D5eReferenceResolver:
        """Create the D5e reference resolver."""
        return D5eReferenceResolver(self._d5e_data_loader)

    def _create_d5e_index_builder(self) -> D5eIndexBuilder:
        """Create the D5e index builder."""
        return D5eIndexBuilder(self._d5e_data_loader)

    def _create_d5e_repository_hub(self) -> D5eRepositoryHub:
        """Create the D5e repository hub."""
        return D5eRepositoryHub(
            data_loader=self._d5e_data_loader,
            reference_resolver=self._d5e_reference_resolver,
            index_builder=self._d5e_index_builder,
        )

    def _create_d5e_data_service(self) -> D5eDataService:
        """Create the D5e data service."""
        return D5eDataService(
            data_loader=self._d5e_data_loader,
            reference_resolver=self._d5e_reference_resolver,
            index_builder=self._d5e_index_builder,
        )


# Global container instance
_container = None

# Global RAG service cache to prevent torch reimport issues
_global_rag_service_cache: Optional[RAGService] = None


def get_container(config: Optional[ServiceConfigModel] = None) -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer(config)
    return _container


def initialize_container(config: ServiceConfigModel) -> None:
    """Initialize the global service container with configuration."""
    global _container
    _container = ServiceContainer(config)
    _container.initialize()


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    _container = None
    # Note: We intentionally do NOT reset _global_rag_service_cache
    # to avoid torch reimport issues in tests
