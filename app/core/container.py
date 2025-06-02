"""
Dependency injection container for the application.
"""
import logging
from typing import Dict, Any, Optional
from app.core.interfaces import (
    GameStateRepository, CharacterService, DiceRollingService, 
    CombatService, ChatService, AIResponseProcessor,
    BaseTTSService
)
from app.repositories.game_state_repository import GameStateRepositoryFactory
from app.services.character_service import CharacterServiceImpl
from app.services.dice_service import DiceRollingServiceImpl
from app.services.combat_service import CombatServiceImpl
from app.services.chat_service import ChatServiceImpl
from app.services.response_processors.ai_response_processor_impl import AIResponseProcessorImpl
from app.services.game_events import GameEventManager
# CampaignRepository removed - using CampaignTemplateRepository instead
from app.repositories.campaign_instance_repository import CampaignInstanceRepository
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.services.campaign_service import CampaignService
from app.services.tts_integration_service import TTSIntegrationService
from app.core.rag_interfaces import RAGService
from app.core.event_queue import EventQueue

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Container for managing service dependencies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._services = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all services with proper dependency injection."""
        if self._initialized:
            return
        
        logger.info("Initializing service container...")
        
        # Create event queue (needed by many services)
        self._event_queue = EventQueue(maxsize=self.config.get('EVENT_QUEUE_MAX_SIZE', 0))
        
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
    
    def get_campaign_template_repository(self):
        """Get the campaign template repository."""
        self._ensure_initialized()
        return self._campaign_template_repo
    
    def get_campaign_instance_repository(self) -> CampaignInstanceRepository:
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
    
    def _ensure_initialized(self) -> None:
        """Ensure the container is initialized."""
        if not self._initialized:
            self.initialize()
    
    def _create_game_state_repository(self) -> GameStateRepository:
        """Create the game state repository."""
        repo_type = self.config.get('GAME_STATE_REPO_TYPE', 'memory')
        
        if repo_type == 'file':
            campaigns_dir = self.config.get('CAMPAIGNS_DIR', 'saves/campaigns')
            return GameStateRepositoryFactory.create_repository('file', base_save_dir=campaigns_dir)
        else:
            return GameStateRepositoryFactory.create_repository('memory')
    
    # Campaign repository removed - using campaign template repository instead
    
    def _create_character_template_repository(self) -> CharacterTemplateRepository:
        """Create the character template repository."""
        templates_dir = self.config.get('CHARACTER_TEMPLATES_DIR', 'saves/character_templates')
        return CharacterTemplateRepository(templates_dir)
    
    def _create_campaign_template_repository(self):
        """Create the campaign template repository."""
        from app.repositories.campaign_template_repository import CampaignTemplateRepository
        return CampaignTemplateRepository(self.config)
    
    def _create_campaign_instance_repository(self):
        """Create the campaign instance repository."""
        # Use in-memory repository when in memory mode
        repo_type = self.config.get('GAME_STATE_REPO_TYPE', 'memory')
        
        campaigns_dir = self.config.get('CAMPAIGNS_DIR', 'saves/campaigns')
        
        if repo_type == 'memory':
            from app.repositories.in_memory_campaign_instance_repository import InMemoryCampaignInstanceRepository
            return InMemoryCampaignInstanceRepository(campaigns_dir)
        else:
            from app.repositories.campaign_instance_repository import CampaignInstanceRepository
            return CampaignInstanceRepository(campaigns_dir)
    
    def _create_character_service(self) -> CharacterService:
        """Create the character service."""
        return CharacterServiceImpl(self._game_state_repo)
    
    def _create_dice_service(self) -> DiceRollingService:
        """Create the dice rolling service."""
        return DiceRollingServiceImpl(self._character_service, self._game_state_repo)
    
    def _create_combat_service(self) -> CombatService:
        """Create the combat service."""
        return CombatServiceImpl(self._game_state_repo, self._character_service, self._event_queue)
    
    def _create_chat_service(self) -> ChatService:
        """Create the chat service."""
        return ChatServiceImpl(self._game_state_repo, self._tts_integration_service, self._event_queue)
    
    def _create_campaign_service(self) -> CampaignService:
        """Create the campaign service."""
        return CampaignService(
            self._campaign_template_repo, 
            self._character_template_repo,
            self._campaign_instance_repo
        )
    
    def _create_tts_service(self) -> Optional[BaseTTSService]:
        """Create the TTS service."""
        # Check if TTS is explicitly disabled in config
        tts_provider = self.config.get('TTS_PROVIDER', 'kokoro').lower()
        if tts_provider in ('none', 'disabled', 'test'):
            logger.info("TTS provider disabled in configuration.")
            return None
            
        try:
            # Import conditionally to prevent startup crashes
            from app.tts_services.manager import get_tts_service
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
            self._event_queue
        )
    
    def _create_rag_service(self) -> RAGService:
        """Create the LangChain-based RAG service."""
        global _global_rag_service_cache
        
        # Check if RAG is disabled in config (for testing)
        rag_enabled = self.config.get('RAG_ENABLED', True)
        if not rag_enabled:
            logger.info("RAG service disabled in configuration")
            # Return a no-op implementation
            from app.services.rag.no_op_rag_service import NoOpRAGService
            return NoOpRAGService()
        
        # Check global cache first to avoid reimport issues
        if _global_rag_service_cache is not None:
            logger.info("Using globally cached RAG service instance")
            # Update repository references
            _global_rag_service_cache.game_state_repo = self._game_state_repo
            return _global_rag_service_cache
        
        try:
            # Lazy import to avoid loading heavy dependencies when RAG is disabled
            from app.services.rag.rag_service import RAGServiceImpl
            
            rag_service = RAGServiceImpl(
                game_state_repo=self._game_state_repo
            )
            
            # Configure search parameters
            rag_service.configure_filtering(
                max_results=5,          # Maximum total results
                score_threshold=0.3     # Minimum similarity score
            )
            
            # Cache globally to avoid reimport issues
            _global_rag_service_cache = rag_service
            
            logger.info("LangChain RAG service initialized successfully")
            return rag_service
        except RuntimeError as e:
            if "already has a docstring" in str(e):
                logger.warning("Torch reimport issue detected, falling back to no-op RAG service")
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
            self._rag_service
        )


# Global container instance
_container = None

# Global RAG service cache to prevent torch reimport issues
_global_rag_service_cache = None


def get_container(config: Dict[str, Any] = None) -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer(config)
    return _container


def initialize_container(config: Dict[str, Any]) -> None:
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
