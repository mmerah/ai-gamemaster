"""
Dependency injection container for the application.
"""

import logging
import os
from typing import Optional

from app.content.dual_connection import DualDatabaseManager
from app.content.protocols import DatabaseManagerProtocol
from app.content.repositories.content_pack_repository import ContentPackRepository
from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.service import ContentService
from app.content.services.content_pack_service import ContentPackService
from app.content.services.indexing_service import IndexingService
from app.core.ai_interfaces import IAIResponseProcessor, IRAGService
from app.core.domain_interfaces import (
    ICharacterService,
    IChatService,
    ICombatService,
    IDiceRollingService,
)
from app.core.event_queue import EventQueue
from app.core.external_interfaces import ITTSService
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICampaignTemplateRepository,
    ICharacterInstanceRepository,
    ICharacterTemplateRepository,
    IGameStateRepository,
)
from app.domain.campaigns.campaign_factory import CampaignFactory
from app.domain.campaigns.campaign_service import CampaignService
from app.domain.characters.character_factory import CharacterFactory
from app.domain.characters.character_service import CharacterService
from app.domain.combat.combat_factory import CombatFactory
from app.domain.combat.combat_service import CombatService
from app.domain.npcs.npc_factory import NPCFactory
from app.domain.quests.quest_factory import QuestFactory
from app.domain.validators.content_validator import ContentValidator
from app.providers.ai.base import BaseAIService
from app.repositories.campaign_instance_repository import (
    CampaignInstanceRepository,
)
from app.repositories.campaign_template_repository import (
    CampaignTemplateRepository,
)
from app.repositories.character_instance_repository import (
    CharacterInstanceRepository,
)
from app.repositories.character_template_repository import (
    CharacterTemplateRepository,
)
from app.repositories.game_state_repository import GameStateRepositoryFactory
from app.repositories.in_memory_campaign_instance_repository import (
    InMemoryCampaignInstanceRepository,
)
from app.repositories.in_memory_character_instance_repository import (
    InMemoryCharacterInstanceRepository,
)
from app.services.action_handlers.dice_submission_handler import DiceSubmissionHandler
from app.services.action_handlers.next_step_handler import NextStepHandler
from app.services.action_handlers.player_action_handler import PlayerActionHandler
from app.services.action_handlers.retry_handler import RetryHandler
from app.services.ai_response_processor import (
    AIResponseProcessor,
)
from app.services.ai_response_processors.interfaces import (
    INarrativeProcessor,
    IRagProcessor,
    IStateUpdateProcessor,
)
from app.services.chat_service import ChatService
from app.services.dice_service import DiceRollingService
from app.services.game_orchestrator import GameOrchestrator
from app.services.shared_state_manager import SharedStateManager
from app.services.tts_integration_service import TTSIntegrationService
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Container for managing service dependencies."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
    ):
        """Initialize the service container with settings.

        Args:
            settings: Settings object. If None, uses get_settings().
        """
        self.settings = settings or get_settings()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize all services with proper dependency injection."""
        if self._initialized:
            return

        logger.info("Initializing service container...")

        # Create event queue (needed by many services)
        self._event_queue = EventQueue(
            maxsize=self.settings.system.event_queue_max_size
        )

        # Create shared state manager
        self._shared_state_manager = SharedStateManager()

        # Create AI service early (needed by many services)
        self._ai_service = self._create_ai_service()

        # Create database manager
        self._database_manager = self._create_database_manager()

        # Create repositories
        self._game_state_repo = self._create_game_state_repository()
        # Campaign repository removed - using campaign_template_repo instead
        self._campaign_instance_repo = self._create_campaign_instance_repository()
        self._character_template_repo = self._create_character_template_repository()
        self._character_instance_repo = self._create_character_instance_repository()
        self._campaign_template_repo = self._create_campaign_template_repository()
        # Ruleset and lore repositories removed - using utility functions instead

        # Create TTS Service first (needed by chat service)
        self._tts_service = self._create_tts_service()
        self._tts_integration_service = self._create_tts_integration_service()

        # Create content service (manages all D&D 5e content)
        self._content_service = self._create_content_service()

        # Create content validator
        self._content_validator = self._create_content_validator()

        # Create core services (except combat which needs factories)
        self._character_service = self._create_character_service()
        self._dice_service = self._create_dice_service()
        self._chat_service = self._create_chat_service()

        # Create factories (needed by some services)
        self._character_factory = self._create_character_factory()
        self._combat_factory = self._create_combat_factory()
        self._quest_factory = self._create_quest_factory()
        self._npc_factory = self._create_npc_factory()
        self._campaign_factory = self._create_campaign_factory()

        # Create services that depend on factories
        self._combat_service = self._create_combat_service()

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

        db_url = self.settings.database.url.get_secret_value()

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

    def get_game_state_repository(self) -> IGameStateRepository:
        """Get the game state repository."""
        self._ensure_initialized()
        return self._game_state_repo

    # Campaign repository removed - use get_campaign_template_repository instead

    def get_character_template_repository(self) -> ICharacterTemplateRepository:
        """Get the character template repository."""
        self._ensure_initialized()
        return self._character_template_repo

    def get_campaign_template_repository(self) -> ICampaignTemplateRepository:
        """Get the campaign template repository."""
        self._ensure_initialized()
        return self._campaign_template_repo

    def get_campaign_instance_repository(self) -> ICampaignInstanceRepository:
        """Get the campaign instance repository."""
        self._ensure_initialized()
        return self._campaign_instance_repo

    def get_character_service(self) -> ICharacterService:
        """Get the character service."""
        self._ensure_initialized()
        return self._character_service

    def get_dice_service(self) -> IDiceRollingService:
        """Get the dice rolling service."""
        self._ensure_initialized()
        return self._dice_service

    def get_combat_service(self) -> ICombatService:
        """Get the combat service."""
        self._ensure_initialized()
        return self._combat_service

    def get_chat_service(self) -> IChatService:
        """Get the chat service."""
        self._ensure_initialized()
        return self._chat_service

    def get_campaign_service(self) -> CampaignService:
        """Get the campaign service."""
        self._ensure_initialized()
        return self._campaign_service

    def get_tts_service(self) -> Optional[ITTSService]:
        """Get the TTS service."""
        self._ensure_initialized()
        return self._tts_service

    def get_tts_integration_service(self) -> TTSIntegrationService:
        """Get the TTS integration service."""
        self._ensure_initialized()
        return self._tts_integration_service

    def get_ai_response_processor(self) -> IAIResponseProcessor:
        """Get the AI response processor."""
        self._ensure_initialized()
        return self._ai_response_processor

    def get_game_orchestrator(self) -> GameOrchestrator:
        """Get the game event manager."""
        self._ensure_initialized()
        return self._game_orchestrator

    def get_rag_service(self) -> IRAGService:
        """Get the RAG service."""
        self._ensure_initialized()
        return self._rag_service

    def get_event_queue(self) -> EventQueue:
        """Get the event queue."""
        self._ensure_initialized()
        return self._event_queue

    def get_shared_state_manager(self) -> SharedStateManager:
        """Get the shared state manager."""
        self._ensure_initialized()
        return self._shared_state_manager

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

    def get_ai_service(self) -> Optional[BaseAIService]:
        """Get the AI service.

        Returns:
            The AI service instance or None if not available.
        """
        self._ensure_initialized()
        return self._ai_service

    def _ensure_initialized(self) -> None:
        """Ensure the container is initialized."""
        if not self._initialized:
            self.initialize()

    def _create_database_manager(self) -> DualDatabaseManager:
        """Create the dual database manager."""
        # System database URL (read-only)
        system_db_url = self.settings.database.url.get_secret_value()

        # User database URL
        user_db_url = self.settings.database.user_url.get_secret_value()

        echo = self.settings.database.echo
        enable_sqlite_vec = self.settings.database.enable_sqlite_vec

        # Build pool configuration for databases that support it
        pool_config = {}
        if system_db_url.startswith("postgresql://") or user_db_url.startswith(
            "postgresql://"
        ):
            pool_config = {
                "pool_size": self.settings.database.pool_size,
                "max_overflow": self.settings.database.max_overflow,
                "pool_timeout": self.settings.database.pool_timeout,
                "pool_recycle": self.settings.database.pool_recycle,
            }
        elif system_db_url.startswith("sqlite://") or user_db_url.startswith(
            "sqlite://"
        ):
            # SQLite only supports pool_recycle
            if self.settings.database.pool_recycle > 0:
                pool_config["pool_recycle"] = self.settings.database.pool_recycle

        sqlite_busy_timeout = self.settings.database.sqlite_busy_timeout

        return DualDatabaseManager(
            system_database_url=system_db_url,
            user_database_url=user_db_url,
            echo=echo,
            pool_config=pool_config,
            enable_sqlite_vec=enable_sqlite_vec,
            sqlite_busy_timeout=sqlite_busy_timeout,
        )

    def _create_game_state_repository(self) -> IGameStateRepository:
        """Create the game state repository."""
        repo_type = self.settings.storage.game_state_repo_type
        base_save_dir = self.settings.storage.saves_dir

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

    def _create_character_template_repository(self) -> ICharacterTemplateRepository:
        """Create the character template repository."""
        return CharacterTemplateRepository(self.settings)

    def _create_character_instance_repository(self) -> ICharacterInstanceRepository:
        """Create the character instance repository."""
        # Use in-memory repository when in memory mode
        repo_type = self.settings.storage.game_state_repo_type

        if repo_type == "memory":
            return InMemoryCharacterInstanceRepository(self.settings)
        else:
            return CharacterInstanceRepository(self.settings)

    def _create_campaign_template_repository(self) -> ICampaignTemplateRepository:
        """Create the campaign template repository."""
        # Pass settings directly (will need to update CampaignTemplateRepository)
        return CampaignTemplateRepository(self.settings)

    def _create_campaign_instance_repository(self) -> ICampaignInstanceRepository:
        """Create the campaign instance repository."""
        # Use in-memory repository when in memory mode
        repo_type = self.settings.storage.game_state_repo_type

        if repo_type == "memory":
            return InMemoryCampaignInstanceRepository(self.settings)
        else:
            return CampaignInstanceRepository(self.settings)

    def _create_character_service(self) -> ICharacterService:
        """Create the character service."""
        return CharacterService(self._game_state_repo, self._character_template_repo)

    def _create_dice_service(self) -> IDiceRollingService:
        """Create the dice rolling service."""
        return DiceRollingService(self._character_service, self._game_state_repo)

    def _create_combat_service(self) -> ICombatService:
        """Create the combat service."""
        return CombatService(
            self._game_state_repo,
            self._character_service,
            self._combat_factory,
            self._event_queue,
        )

    def _create_chat_service(self) -> IChatService:
        """Create the chat service."""
        return ChatService(
            self._game_state_repo, self._event_queue, self._tts_integration_service
        )

    def _create_character_factory(self) -> CharacterFactory:
        """Create the character factory."""
        return CharacterFactory(self._content_service)

    def _create_campaign_factory(self) -> CampaignFactory:
        """Create the campaign factory."""
        return CampaignFactory(self._content_service, self._character_factory)

    def _create_combat_factory(self) -> CombatFactory:
        """Create the combat factory."""
        return CombatFactory(self._content_service)

    def _create_quest_factory(self) -> QuestFactory:
        """Create the quest factory."""
        return QuestFactory()

    def _create_npc_factory(self) -> NPCFactory:
        """Create the NPC factory."""
        return NPCFactory(self._content_service)

    def _create_campaign_service(self) -> CampaignService:
        """Create the campaign service."""
        return CampaignService(
            self._campaign_factory,
            self._character_factory,
            self._campaign_template_repo,
            self._character_template_repo,
            self._campaign_instance_repo,
            self._content_service,
        )

    def _create_tts_service(self) -> Optional[ITTSService]:
        """Create the TTS service."""
        # Check if TTS is explicitly disabled in config
        tts_provider = self.settings.tts.provider.lower()
        if tts_provider in ("none", "disabled", "test"):
            logger.info("TTS provider disabled in configuration.")
            return None

        try:
            # Import conditionally to prevent startup crashes
            from app.providers.tts.manager import get_tts_service

            # Pass settings directly (will need to update get_tts_service)
            return get_tts_service(self.settings)
        except ImportError as e:
            logger.warning(f"Could not import TTS manager: {e}. TTS will be disabled.")
            return None
        except Exception as e:
            logger.warning(f"Failed to create TTS service: {e}. TTS will be disabled.")
            return None

    def _create_tts_integration_service(self) -> TTSIntegrationService:
        """Create the TTS integration service."""
        return TTSIntegrationService(self._tts_service, self._game_state_repo)

    def _create_ai_response_processor(self) -> IAIResponseProcessor:
        """Create the AI response processor."""
        # Create processors
        narrative_processor = self._create_narrative_processor()
        state_update_processor = self._create_state_update_processor()
        rag_processor = self._create_rag_processor()

        return AIResponseProcessor(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            narrative_processor,
            state_update_processor,
            rag_processor,
            self._event_queue,
            self._rag_service,
        )

    def _create_narrative_processor(self) -> INarrativeProcessor:
        """Create the narrative processor."""
        from app.services.ai_response_processors import NarrativeProcessor

        return NarrativeProcessor(
            self._game_state_repo,
            self._chat_service,
            self._event_queue,
        )

    def _create_state_update_processor(self) -> IStateUpdateProcessor:
        """Create the state update processor."""
        from app.services.ai_response_processors import StateUpdateProcessor

        return StateUpdateProcessor(
            self._game_state_repo,
            self._character_service,
            self._event_queue,
        )

    def _create_rag_processor(self) -> IRagProcessor:
        """Create the RAG processor."""
        from app.services.ai_response_processors import RagProcessor

        return RagProcessor(
            self._game_state_repo,
            self._rag_service,
        )

    def _create_rag_service(self) -> IRAGService:
        """Create the LangChain-based RAG service."""
        global _global_rag_service_cache

        # Check if RAG is disabled in config (for testing)
        if not self.settings.rag.enabled:
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
            from app.content.rag.chunkers import MarkdownChunker
            from app.content.rag.query_engine import SimpleQueryEngine
            from app.content.rag.rag_service import RAGService
            from app.content.rag.rerankers import EntityMatchReranker

            # Create shared components
            query_engine = SimpleQueryEngine()
            reranker = (
                EntityMatchReranker()
            )  # Using EntityMatchReranker to preserve existing behavior
            chunker = MarkdownChunker()  # Default chunker for lore/markdown content

            if self._content_service:
                # Use D5e-enhanced database-backed RAG service
                from app.content.rag.d5e_db_knowledge_base_manager import (
                    D5eDbKnowledgeBaseManager,
                )

                # Create D5e database-backed knowledge base manager
                d5e_kb_manager = D5eDbKnowledgeBaseManager(
                    self._content_service, self._database_manager, chunker=chunker
                )

                # Create RAG service with D5e knowledge base
                rag_service = RAGService(
                    game_state_repo=self._game_state_repo,
                    kb_manager=d5e_kb_manager,
                    reranker=reranker,
                    query_engine=query_engine,
                )

                logger.info("D5e database-backed RAG service initialized successfully")
            else:
                # Use standard database-backed RAG service
                from app.content.rag.db_knowledge_base_manager import (
                    DbKnowledgeBaseManager,
                )

                db_kb_manager = DbKnowledgeBaseManager(
                    self._database_manager, chunker=chunker
                )
                rag_service = RAGService(
                    game_state_repo=self._game_state_repo,
                    kb_manager=db_kb_manager,
                    reranker=reranker,
                    query_engine=query_engine,
                )
                logger.info(
                    "Standard database-backed RAG service initialized successfully"
                )

            # Configure search parameters
            rag_service.configure_filtering(
                max_results=self.settings.rag.max_total_results,
                score_threshold=self.settings.rag.score_threshold,
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
        # Create action handlers first
        player_action_handler = self._create_player_action_handler()
        dice_submission_handler = self._create_dice_submission_handler()
        next_step_handler = self._create_next_step_handler()
        retry_handler = self._create_retry_handler()

        return GameOrchestrator(
            self._game_state_repo,
            self._character_service,
            self._shared_state_manager,
            player_action_handler,
            dice_submission_handler,
            next_step_handler,
            retry_handler,
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

    def _create_content_validator(self) -> ContentValidator:
        """Create the content validator."""
        return ContentValidator(self._content_service)

    def _create_player_action_handler(self) -> PlayerActionHandler:
        """Create the player action handler."""
        return PlayerActionHandler(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._ai_response_processor,
            self._campaign_service,
            self._event_queue,
            self._rag_service,
        )

    def _create_dice_submission_handler(self) -> DiceSubmissionHandler:
        """Create the dice submission handler."""
        return DiceSubmissionHandler(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._ai_response_processor,
            self._campaign_service,
            self._event_queue,
            self._rag_service,
        )

    def _create_next_step_handler(self) -> NextStepHandler:
        """Create the next step handler."""
        return NextStepHandler(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._ai_response_processor,
            self._campaign_service,
            self._event_queue,
            self._rag_service,
        )

    def _create_retry_handler(self) -> RetryHandler:
        """Create the retry handler."""
        return RetryHandler(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._ai_response_processor,
            self._campaign_service,
            self._event_queue,
            self._rag_service,
        )

    def _create_ai_service(self) -> Optional[BaseAIService]:
        """Create the AI service."""
        from app.providers.ai.manager import get_ai_service

        try:
            ai_service = get_ai_service(self.settings)
            if ai_service:
                logger.info(f"AI Service Initialized: {type(ai_service).__name__}")
            else:
                logger.error("AI Service returned None - check configuration")
            return ai_service
        except Exception as e:
            logger.critical(
                f"FATAL: Failed to initialize AI Service: {e}", exc_info=True
            )
            logger.warning("AI Service could not be initialized. API calls will fail.")
            return None


# Global container instance
_container = None

# Global RAG service cache to prevent torch reimport issues
_global_rag_service_cache: Optional[IRAGService] = None


def get_container(
    settings: Optional[Settings] = None,
) -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer(settings)
    return _container


def initialize_container(settings: Settings) -> None:
    """Initialize the global service container with settings."""
    global _container
    _container = ServiceContainer(settings)
    _container.initialize()


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    if _container is not None:
        _container.cleanup()
    _container = None
    # Note: We intentionally do NOT reset _global_rag_service_cache
    # to avoid torch reimport issues in tests
