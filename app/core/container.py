"""
Dependency injection container for the application.
"""
import logging
from typing import Dict, Any, Optional
from app.core.interfaces import (
    GameStateRepository, CharacterService, DiceRollingService, 
    CombatService, ChatService, AIResponseProcessor, GameEventHandler,
    BaseTTSService
)
from app.repositories.game_state_repository import GameStateRepositoryFactory
from app.services.character_service import CharacterServiceImpl
from app.services.dice_service import DiceRollingServiceImpl
from app.services.combat_service import CombatServiceImpl
from app.services.chat_service import ChatServiceImpl
from app.services.ai_response_processor import AIResponseProcessorImpl
from app.services.game_events import GameEventManager
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.repositories.ruleset_repository import RulesetRepository
from app.repositories.lore_repository import LoreRepository
from app.services.campaign_service import CampaignService
from app.services.tts_integration_service import TTSIntegrationService
from app.core.rag_interfaces import RAGService

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
        
        # Create repositories
        self._game_state_repo = self._create_game_state_repository()
        self._campaign_repo = self._create_campaign_repository()
        self._character_template_repo = self._create_character_template_repository()
        self._ruleset_repo = self._create_ruleset_repository()
        self._lore_repo = self._create_lore_repository()
        
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
        self._game_event_handler = self._create_game_event_handler()
        
        self._initialized = True
        logger.info("Service container initialized successfully.")
    
    def get_game_state_repository(self) -> GameStateRepository:
        """Get the game state repository."""
        self._ensure_initialized()
        return self._game_state_repo
    
    def get_campaign_repository(self) -> CampaignRepository:
        """Get the campaign repository."""
        self._ensure_initialized()
        return self._campaign_repo
    
    def get_character_template_repository(self) -> CharacterTemplateRepository:
        """Get the character template repository."""
        self._ensure_initialized()
        return self._character_template_repo
    
    def get_ruleset_repository(self) -> RulesetRepository:
        """Get the ruleset repository."""
        self._ensure_initialized()
        return self._ruleset_repo

    def get_lore_repository(self) -> LoreRepository:
        """Get the lore repository."""
        self._ensure_initialized()
        return self._lore_repo

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
    
    def get_game_event_handler(self) -> GameEventManager:
        """Get the game event manager."""
        self._ensure_initialized()
        return self._game_event_handler
    
    def get_rag_service(self) -> RAGService:
        """Get the RAG service."""
        self._ensure_initialized()
        return self._rag_service
    
    def _ensure_initialized(self) -> None:
        """Ensure the container is initialized."""
        if not self._initialized:
            self.initialize()
    
    def _create_game_state_repository(self) -> GameStateRepository:
        """Create the game state repository."""
        repo_type = self.config.get('GAME_STATE_REPO_TYPE', 'memory')
        
        if repo_type == 'file':
            file_path = self.config.get('GAME_STATE_FILE_PATH', 'saves/game_state.json')
            return GameStateRepositoryFactory.create_repository('file', file_path=file_path)
        else:
            return GameStateRepositoryFactory.create_repository('memory')
    
    def _create_campaign_repository(self) -> CampaignRepository:
        """Create the campaign repository."""
        campaigns_dir = self.config.get('CAMPAIGNS_DIR', 'saves/campaigns')
        return CampaignRepository(campaigns_dir)
    
    def _create_character_template_repository(self) -> CharacterTemplateRepository:
        """Create the character template repository."""
        templates_dir = self.config.get('CHARACTER_TEMPLATES_DIR', 'saves/character_templates')
        return CharacterTemplateRepository(templates_dir)
    
    def _create_ruleset_repository(self) -> RulesetRepository:
        """Create the ruleset repository."""
        return RulesetRepository()

    def _create_lore_repository(self) -> LoreRepository:
        """Create the lore repository."""
        return LoreRepository()

    def _create_character_service(self) -> CharacterService:
        """Create the character service."""
        return CharacterServiceImpl(self._game_state_repo)
    
    def _create_dice_service(self) -> DiceRollingService:
        """Create the dice rolling service."""
        return DiceRollingServiceImpl(self._character_service, self._game_state_repo)
    
    def _create_combat_service(self) -> CombatService:
        """Create the combat service."""
        return CombatServiceImpl(self._game_state_repo, self._character_service)
    
    def _create_chat_service(self) -> ChatService:
        """Create the chat service."""
        return ChatServiceImpl(self._game_state_repo, self._tts_integration_service)
    
    def _create_campaign_service(self) -> CampaignService:
        """Create the campaign service."""
        return CampaignService(self._campaign_repo, self._character_template_repo)
    
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
            self._chat_service
        )
    
    def _create_rag_service(self) -> RAGService:
        """Create the LangChain-based RAG service."""
        # Check if RAG is disabled in config (for testing)
        rag_enabled = self.config.get('RAG_ENABLED', True)
        if not rag_enabled:
            logger.info("RAG service disabled in configuration")
            # Return a no-op implementation
            from app.services.rag.no_op_rag_service import NoOpRAGService
            return NoOpRAGService()
        
        # Lazy import to avoid loading heavy dependencies when RAG is disabled
        from app.services.rag.rag_service import RAGServiceImpl
        
        rag_service = RAGServiceImpl(
            game_state_repo=self._game_state_repo,
            ruleset_repo=self._ruleset_repo,
            lore_repo=self._lore_repo
        )
        
        # Configure search parameters
        rag_service.configure_filtering(
            max_results=5,          # Maximum total results
            score_threshold=0.3     # Minimum similarity score
        )
        
        logger.info("LangChain RAG service initialized successfully")
        return rag_service
    
    def _create_game_event_handler(self) -> GameEventManager:
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
