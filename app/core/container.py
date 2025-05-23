"""
Dependency injection container for the application.
"""
import logging
from typing import Dict, Any
from app.core.interfaces import (
    GameStateRepository, CharacterService, DiceRollingService, 
    CombatService, ChatService, AIResponseProcessor, GameEventHandler
)
from app.repositories.game_state_repository import GameStateRepositoryFactory
from app.services.character_service import CharacterServiceImpl
from app.services.dice_service import DiceRollingServiceImpl
from app.services.combat_service import CombatServiceImpl
from app.services.chat_service import ChatServiceImpl
from app.services.ai_response_processor import AIResponseProcessorImpl
from app.services.game_event_handler import GameEventHandlerImpl
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.services.campaign_service import CampaignService

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
        
        # Create core services
        self._character_service = self._create_character_service()
        self._dice_service = self._create_dice_service()
        self._combat_service = self._create_combat_service()
        self._chat_service = self._create_chat_service()
        
        # Create campaign management services
        self._campaign_service = self._create_campaign_service()
        
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
    
    def get_ai_response_processor(self) -> AIResponseProcessor:
        """Get the AI response processor."""
        self._ensure_initialized()
        return self._ai_response_processor
    
    def get_game_event_handler(self) -> GameEventHandler:
        """Get the game event handler."""
        self._ensure_initialized()
        return self._game_event_handler
    
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
        return ChatServiceImpl(self._game_state_repo)
    
    def _create_campaign_service(self) -> CampaignService:
        """Create the campaign service."""
        return CampaignService(self._campaign_repo, self._character_template_repo)
    
    def _create_ai_response_processor(self) -> AIResponseProcessor:
        """Create the AI response processor."""
        return AIResponseProcessorImpl(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service
        )
    
    def _create_game_event_handler(self) -> GameEventHandler:
        """Create the game event handler."""
        return GameEventHandlerImpl(
            self._game_state_repo,
            self._character_service,
            self._dice_service,
            self._combat_service,
            self._chat_service,
            self._ai_response_processor
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
