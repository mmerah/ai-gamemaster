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
from app.database.connection import DatabaseManager
from app.models import ServiceConfigModel
from app.repositories.campaign_instance_repository import CampaignInstanceRepository
from app.repositories.campaign_template_repository import CampaignTemplateRepository
from app.repositories.character_template_repository import CharacterTemplateRepository

# Import D5e services
from app.repositories.d5e import D5eRepositoryHub
from app.repositories.game_state_repository import GameStateRepositoryFactory
from app.repositories.in_memory_campaign_instance_repository import (
    InMemoryCampaignInstanceRepository,
)
from app.services.campaign_service import CampaignService
from app.services.character_service import CharacterServiceImpl
from app.services.chat_service import ChatServiceImpl
from app.services.combat_service import CombatServiceImpl
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

        # Create database manager
        self._database_manager = self._create_database_manager()

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

        # Create D5e services first (needed by RAG)
        # Note: D5e data loader, reference resolver, and index builder are no longer needed
        # with database-backed repositories
        self._d5e_repository_hub = self._create_d5e_repository_hub()
        self._d5e_data_service = self._create_d5e_data_service()

        # Create RAG service (may use D5e services)
        self._rag_service = self._create_rag_service()

        # Create higher-level services
        self._ai_response_processor = self._create_ai_response_processor()
        self._game_event_manager = self._create_game_event_manager()

        self._initialized = True
        logger.info("Service container initialized successfully.")

    def cleanup(self) -> None:
        """Clean up resources held by the container."""
        if hasattr(self, "_database_manager") and self._database_manager is not None:
            self._database_manager.dispose()
            logger.info("Disposed database connections")

    def get_database_manager(self) -> DatabaseManager:
        """Get the database manager."""
        self._ensure_initialized()
        return self._database_manager

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

    def _create_database_manager(self) -> DatabaseManager:
        """Create the database manager."""
        database_url = str(
            self._get_config_value("DATABASE_URL", "sqlite:///data/content.db")
        )
        echo = bool(self._get_config_value("DATABASE_ECHO", False))
        enable_sqlite_vec = bool(self._get_config_value("ENABLE_SQLITE_VEC", True))

        # Build pool configuration for databases that support it
        pool_config = {}
        if database_url.startswith("postgresql://"):
            pool_config = {
                "pool_size": int(self._get_config_value("DATABASE_POOL_SIZE", 5)),
                "max_overflow": int(
                    self._get_config_value("DATABASE_MAX_OVERFLOW", 10)
                ),
                "pool_timeout": int(
                    self._get_config_value("DATABASE_POOL_TIMEOUT", 30)
                ),
                "pool_recycle": int(
                    self._get_config_value("DATABASE_POOL_RECYCLE", 3600)
                ),
            }
        elif database_url.startswith("sqlite://"):
            # SQLite only supports pool_recycle
            pool_recycle = int(self._get_config_value("DATABASE_POOL_RECYCLE", 3600))
            if pool_recycle > 0:
                pool_config["pool_recycle"] = pool_recycle

        return DatabaseManager(
            database_url=database_url,
            echo=echo,
            pool_config=pool_config,
            enable_sqlite_vec=enable_sqlite_vec,
        )

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

            if self._d5e_data_service:
                # Use D5e-enhanced database-backed RAG service
                from app.services.rag.d5e_db_knowledge_base_manager import (
                    D5eDbKnowledgeBaseManager,
                )

                # Create D5e database-backed knowledge base manager
                d5e_kb_manager = D5eDbKnowledgeBaseManager(
                    self._d5e_data_service, self._database_manager
                )

                # Create RAG service with D5e knowledge base
                rag_service = RAGServiceImpl(game_state_repo=self._game_state_repo)
                rag_service.kb_manager = d5e_kb_manager

                logger.info("D5e database-backed RAG service initialized successfully")
            else:
                # Use standard database-backed RAG service
                from app.services.rag.db_knowledge_base_manager import (
                    DbKnowledgeBaseManager,
                )

                db_kb_manager = DbKnowledgeBaseManager(self._database_manager)
                rag_service = RAGServiceImpl(game_state_repo=self._game_state_repo)
                rag_service.kb_manager = db_kb_manager
                logger.info(
                    "Standard database-backed RAG service initialized successfully"
                )

            # Configure search parameters
            rag_service.configure_filtering(
                max_results=5,  # Maximum total results
                score_threshold=0.3,  # Minimum similarity score
            )

            # Cache globally to avoid reimport issues
            _global_rag_service_cache = rag_service

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

    def _create_d5e_repository_hub(self) -> D5eRepositoryHub:
        """Create the D5e repository hub."""
        return D5eRepositoryHub(self._database_manager)

    def _create_d5e_data_service(self) -> D5eDataService:
        """Create the D5e data service."""
        return D5eDataService(self._d5e_repository_hub)


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
    if _container is not None:
        _container.cleanup()
    _container = None
    # Note: We intentionally do NOT reset _global_rag_service_cache
    # to avoid torch reimport issues in tests
