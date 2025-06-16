"""
Dependency injection container for the application.
"""

import logging
from typing import Any, Dict, Optional, Union

from app.content.dual_connection import DualDatabaseManager
from app.content.protocols import DatabaseManagerProtocol
from app.content.repositories.content_pack_repository import ContentPackRepository
from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.service import ContentService
from app.content.services.content_pack_service import ContentPackService
from app.content.services.indexing_service import IndexingService
from app.core.event_queue import EventQueue
from app.core.interfaces import (
    AIResponseProcessor,
    BaseTTSService,
    CharacterService,
    ChatService,
    CombatService,
    DiceRollingService,
    GameStateRepository,
    RAGService,
)
from app.domain.campaigns.service import CampaignService
from app.domain.characters.service import CharacterServiceImpl
from app.domain.combat.combat_service import CombatServiceImpl
from app.models.config import ServiceConfigModel
from app.repositories.game.campaign_instance_repository import (
    CampaignInstanceRepository,
)
from app.repositories.game.campaign_template_repository import (
    CampaignTemplateRepository,
)
from app.repositories.game.character_template_repository import (
    CharacterTemplateRepository,
)
from app.repositories.game.game_state import GameStateRepositoryFactory
from app.repositories.game.in_memory_campaign_instance_repository import (
    InMemoryCampaignInstanceRepository,
)
from app.services.chat_service import ChatServiceImpl
from app.services.dice_service import DiceRollingServiceImpl
from app.services.game_orchestrator import GameOrchestrator
from app.services.response_processor import (
    AIResponseProcessorImpl,
)
from app.services.tts_integration_service import TTSIntegrationService
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Container for managing service dependencies."""

    def __init__(
        self,
        config: Optional[Union[Dict[str, Any], ServiceConfigModel, Settings]] = None,
    ):
        # If no config provided, use the global settings instance
        if config is None:
            self.config: Union[Dict[str, Any], ServiceConfigModel, Settings] = (
                get_settings()
            )
        elif isinstance(config, Settings):
            self.config = config
        else:
            self.config = config  # Dict or ServiceConfigModel
        self._initialized = False

    def _get_config_value(self, key: str, default: Any) -> Any:
        """Get config value handling dict, ServiceConfigModel, and Settings configs."""
        if isinstance(self.config, Settings):
            # Import here to avoid circular import
            from pydantic import SecretStr

            # Map old config keys to new settings structure
            settings = self.config
            settings_map: Dict[str, Any] = {
                # AI Settings
                "AI_PROVIDER": lambda: settings.ai.provider,
                "AI_RESPONSE_PARSING_MODE": lambda: settings.ai.response_parsing_mode,
                "AI_TEMPERATURE": lambda: settings.ai.temperature,
                "AI_MAX_TOKENS": lambda: settings.ai.max_tokens,
                "AI_MAX_RETRIES": lambda: settings.ai.max_retries,
                "AI_RETRY_DELAY": lambda: settings.ai.retry_delay,
                "AI_REQUEST_TIMEOUT": lambda: settings.ai.request_timeout,
                "AI_RETRY_CONTEXT_TIMEOUT": lambda: settings.ai.retry_context_timeout,
                "OPENROUTER_API_KEY": lambda: settings.ai.openrouter_api_key,
                "OPENROUTER_MODEL_NAME": lambda: settings.ai.openrouter_model_name,
                "OPENROUTER_BASE_URL": lambda: settings.ai.openrouter_base_url,
                "LLAMA_SERVER_URL": lambda: settings.ai.llama_server_url,
                "MAX_AI_CONTINUATION_DEPTH": lambda: settings.ai.max_continuation_depth,
                # Prompt Settings
                "MAX_PROMPT_TOKENS_BUDGET": lambda: settings.prompt.max_tokens_budget,
                "LAST_X_HISTORY_MESSAGES": lambda: settings.prompt.last_x_history_messages,
                "TOKENS_PER_MESSAGE_OVERHEAD": lambda: settings.prompt.tokens_per_message_overhead,
                # Database Settings
                "DATABASE_URL": lambda: settings.database.url,
                "USER_DATABASE_URL": lambda: settings.database.user_url,
                "DATABASE_ECHO": lambda: settings.database.echo,
                "DATABASE_POOL_SIZE": lambda: settings.database.pool_size,
                "DATABASE_MAX_OVERFLOW": lambda: settings.database.max_overflow,
                "DATABASE_POOL_TIMEOUT": lambda: settings.database.pool_timeout,
                "DATABASE_POOL_RECYCLE": lambda: settings.database.pool_recycle,
                "ENABLE_SQLITE_VEC": lambda: settings.database.enable_sqlite_vec,
                "SQLITE_BUSY_TIMEOUT": lambda: settings.database.sqlite_busy_timeout,
                # RAG Settings
                "RAG_ENABLED": lambda: settings.rag.enabled,
                "RAG_MAX_RESULTS_PER_QUERY": lambda: settings.rag.max_results_per_query,
                "RAG_MAX_TOTAL_RESULTS": lambda: settings.rag.max_total_results,
                "RAG_SCORE_THRESHOLD": lambda: settings.rag.score_threshold,
                "RAG_EMBEDDINGS_MODEL": lambda: settings.rag.embeddings_model,
                "RAG_CHUNK_SIZE": lambda: settings.rag.chunk_size,
                "RAG_CHUNK_OVERLAP": lambda: settings.rag.chunk_overlap,
                "RAG_COLLECTION_NAME_PREFIX": lambda: settings.rag.collection_name_prefix,
                "RAG_METADATA_FILTERING_ENABLED": lambda: settings.rag.metadata_filtering_enabled,
                "RAG_RELEVANCE_FEEDBACK_ENABLED": lambda: settings.rag.relevance_feedback_enabled,
                "RAG_CACHE_TTL": lambda: settings.rag.cache_ttl,
                # TTS Settings
                "TTS_PROVIDER": lambda: settings.tts.provider,
                "TTS_VOICE": lambda: settings.tts.voice,
                "KOKORO_LANG_CODE": lambda: settings.tts.kokoro_lang_code,
                "TTS_CACHE_DIR_NAME": lambda: settings.tts.cache_dir_name,
                # Storage Settings
                "GAME_STATE_REPO_TYPE": lambda: settings.storage.game_state_repo_type,
                "CAMPAIGNS_DIR": lambda: settings.storage.campaigns_dir,
                "CHARACTER_TEMPLATES_DIR": lambda: settings.storage.character_templates_dir,
                "CAMPAIGN_TEMPLATES_DIR": lambda: settings.storage.campaign_templates_dir,
                "SAVES_DIR": lambda: settings.storage.saves_dir,
                # System Settings
                "EVENT_QUEUE_MAX_SIZE": lambda: settings.system.event_queue_max_size,
                "LOG_LEVEL": lambda: settings.system.log_level,
                "LOG_FILE": lambda: settings.system.log_file,
                # Flask Settings
                "SECRET_KEY": lambda: settings.flask.secret_key,
                "FLASK_APP": lambda: settings.flask.flask_app,
                "FLASK_DEBUG": lambda: settings.flask.flask_debug,
                "TESTING": lambda: settings.flask.testing,
                # SSE Settings
                "SSE_HEARTBEAT_INTERVAL": lambda: settings.sse.heartbeat_interval,
                "SSE_EVENT_TIMEOUT": lambda: settings.sse.event_timeout,
            }
            if key in settings_map:
                value = settings_map[key]()
                # Automatically unwrap SecretStr values
                if isinstance(value, SecretStr):
                    return value.get_secret_value()
                return value
            return default
        elif isinstance(self.config, dict):
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

        # Create content service (manages all D&D 5e content)
        self._content_service = self._create_content_service()

        # Create campaign management services
        self._campaign_service = self._create_campaign_service()

        # Create content pack and indexing services
        self._content_pack_service = self._create_content_pack_service()
        self._indexing_service = self._create_indexing_service()

        # Create RAG service (may use D5e services)
        self._rag_service = self._create_rag_service()

        # Create higher-level services
        self._ai_response_processor = self._create_ai_response_processor()
        self._game_orchestrator = self._create_game_orchestrator()

        # Validate database at the end
        self._validate_database()

        self._initialized = True
        logger.info("Service container initialized successfully.")

    def _validate_database(self) -> None:
        """Validate database exists and has required schema."""
        from app.content.validator import validate_database

        db_url = str(
            self._get_config_value("DATABASE_URL", "sqlite:///data/content.db")
        )

        # Use the new validator
        success, error_msg = validate_database(db_url)

        if not success:
            # Provide helpful error messages based on the issue
            if error_msg and "not found" in error_msg:
                raise RuntimeError(
                    f"{error_msg}. "
                    f"Run 'python -m app.content.scripts.migrate_content.py sqlite:///{db_url.split('///')[-1]}' to create it."
                )
            elif error_msg and (
                "schema incomplete" in error_msg
                or "Missing critical tables" in error_msg
            ):
                raise RuntimeError(
                    f"{error_msg}. "
                    f"Run 'python -m app.content.scripts.migrate_content.py sqlite:///{db_url.split('///')[-1]}' to initialize."
                )
            elif error_msg and "empty" in error_msg:
                logger.warning(
                    f"{error_msg}. "
                    f"Run 'python -m app.content.scripts.migrate_content.py sqlite:///{db_url.split('///')[-1]}' to populate it."
                )
            else:
                # Generic error case
                raise RuntimeError(
                    f"Database validation failed: {error_msg or 'Unknown error'}"
                )

    def cleanup(self) -> None:
        """Clean up resources held by the container."""
        if hasattr(self, "_database_manager") and self._database_manager is not None:
            self._database_manager.dispose()
            logger.info("Disposed database connections")

    def get_database_manager(self) -> DatabaseManagerProtocol:
        """Get the dual database manager."""
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

    def get_game_orchestrator(self) -> GameOrchestrator:
        """Get the game event manager."""
        self._ensure_initialized()
        return self._game_orchestrator

    def get_rag_service(self) -> RAGService:
        """Get the RAG service."""
        self._ensure_initialized()
        return self._rag_service

    def get_event_queue(self) -> EventQueue:
        """Get the event queue."""
        self._ensure_initialized()
        return self._event_queue

    def get_content_service(self) -> ContentService:
        """Get the content service for D&D 5e operations.

        Returns:
            ContentService: The primary interface for accessing D&D 5e content,
            including spells, monsters, equipment, and game rules.
        """
        self._ensure_initialized()
        return self._content_service

    def get_content_pack_service(self) -> ContentPackService:
        """Get the content pack service for managing content packs.

        Returns:
            ContentPackService: Service for managing content packs and their lifecycle.
        """
        self._ensure_initialized()
        return self._content_pack_service

    def get_indexing_service(self) -> IndexingService:
        """Get the indexing service for content indexing operations.

        Returns:
            IndexingService: Service for indexing content for search and retrieval.
        """
        self._ensure_initialized()
        return self._indexing_service

    def _ensure_initialized(self) -> None:
        """Ensure the container is initialized."""
        if not self._initialized:
            self.initialize()

    def _create_database_manager(self) -> DualDatabaseManager:
        """Create the dual database manager."""
        # System database URL (read-only)
        system_db_url = str(
            self._get_config_value("DATABASE_URL", "sqlite:///data/content.db")
        )

        # User database URL
        user_db_url = str(
            self._get_config_value(
                "USER_DATABASE_URL", "sqlite:///data/user_content.db"
            )
        )

        echo = bool(self._get_config_value("DATABASE_ECHO", False))
        enable_sqlite_vec = bool(self._get_config_value("ENABLE_SQLITE_VEC", True))

        # Build pool configuration for databases that support it
        pool_config = {}
        if system_db_url.startswith("postgresql://") or user_db_url.startswith(
            "postgresql://"
        ):
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
        elif system_db_url.startswith("sqlite://") or user_db_url.startswith(
            "sqlite://"
        ):
            # SQLite only supports pool_recycle
            pool_recycle = int(self._get_config_value("DATABASE_POOL_RECYCLE", 3600))
            if pool_recycle > 0:
                pool_config["pool_recycle"] = pool_recycle

        sqlite_busy_timeout = int(self._get_config_value("SQLITE_BUSY_TIMEOUT", 5000))

        return DualDatabaseManager(
            system_database_url=system_db_url,
            user_database_url=user_db_url,
            echo=echo,
            pool_config=pool_config,
            enable_sqlite_vec=enable_sqlite_vec,
            sqlite_busy_timeout=sqlite_busy_timeout,
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
        templates_dir = str(
            self._get_config_value(
                "CHARACTER_TEMPLATES_DIR", "saves/character_templates"
            )
        )
        return CharacterTemplateRepository(templates_dir)

    def _create_campaign_template_repository(self) -> CampaignTemplateRepository:
        """Create the campaign template repository."""
        # Pass config as ServiceConfigModel
        if isinstance(self.config, Settings):
            # Convert Settings to ServiceConfigModel
            from app.models.config import ServiceConfigModel

            config_dict = self.config.to_service_config_dict()
            config_obj = ServiceConfigModel(**config_dict)
            return CampaignTemplateRepository(config_obj)
        elif isinstance(self.config, dict):
            # Create a ServiceConfigModel from dict
            from app.models.config import ServiceConfigModel

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
            self._content_service,
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
            from app.providers.tts.manager import get_tts_service

            # Pass config as ServiceConfigModel
            if isinstance(self.config, Settings):
                # Convert Settings to ServiceConfigModel
                from app.models.config import ServiceConfigModel

                config_dict = self.config.to_service_config_dict()
                config_obj = ServiceConfigModel(**config_dict)
                return get_tts_service(config_obj)
            elif isinstance(self.config, dict):
                # Create a ServiceConfigModel from dict
                from app.models.config import ServiceConfigModel

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
            self._rag_service,
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
            from app.content.rag.no_op_rag_service import NoOpRAGService

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
            from app.content.rag.service import RAGServiceImpl

            if self._content_service:
                # Use D5e-enhanced database-backed RAG service
                from app.content.rag.d5e_db_knowledge_base_manager import (
                    D5eDbKnowledgeBaseManager,
                )

                # Create D5e database-backed knowledge base manager
                d5e_kb_manager = D5eDbKnowledgeBaseManager(
                    self._content_service, self._database_manager
                )

                # Create RAG service with D5e knowledge base
                rag_service = RAGServiceImpl(game_state_repo=self._game_state_repo)
                rag_service.kb_manager = d5e_kb_manager

                logger.info("D5e database-backed RAG service initialized successfully")
            else:
                # Use standard database-backed RAG service
                from app.content.rag.db_knowledge_base_manager import (
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
                from app.content.rag.no_op_rag_service import NoOpRAGService

                return NoOpRAGService()
            raise

    def _create_game_orchestrator(self) -> GameOrchestrator:
        """Create the game event manager."""
        return GameOrchestrator(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._ai_response_processor,
            self._campaign_service,
            self._rag_service,
        )

    def _create_content_service(self) -> ContentService:
        """Create the content service with its repository hub."""
        repository_hub = D5eDbRepositoryHub(self._database_manager)
        return ContentService(repository_hub)

    def _create_content_pack_service(self) -> ContentPackService:
        """Create the content pack service."""
        content_pack_repository = ContentPackRepository(self._database_manager)
        repository_hub = D5eDbRepositoryHub(self._database_manager)
        return ContentPackService(content_pack_repository, repository_hub)

    def _create_indexing_service(self) -> IndexingService:
        """Create the indexing service."""
        return IndexingService(self._database_manager)


# Global container instance
_container = None

# Global RAG service cache to prevent torch reimport issues
_global_rag_service_cache: Optional[RAGService] = None


def get_container(
    config: Optional[Union[ServiceConfigModel, Settings]] = None,
) -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer(config)
    return _container


def initialize_container(config: Union[ServiceConfigModel, Settings]) -> None:
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
