"""
Main game event manager that coordinates all event handlers.
"""

import logging
from typing import Dict, Any, List
from app.core.interfaces import (
    GameStateRepository, CharacterService, DiceRollingService,
    CombatService, ChatService, AIResponseProcessor
)
from app.services.campaign_service import CampaignService
from .handlers import (
    PlayerActionHandler, DiceSubmissionHandler, 
    NextStepHandler, RetryHandler
)

logger = logging.getLogger(__name__)


class GameEventManager:
    """
    Manages all game events and delegates to appropriate handlers.
    This replaces the monolithic GameEventHandler.
    """
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService,
                 dice_service: DiceRollingService, combat_service: CombatService,
                 chat_service: ChatService, ai_response_processor: AIResponseProcessor,
                 campaign_service: CampaignService):
        
        # Store dependencies
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor
        self.campaign_service = campaign_service
        
        # Shared retry context storage across all handlers
        self._shared_ai_request_context = None
        self._shared_ai_request_timestamp = None
        
        # Initialize handlers
        self.player_action_handler = PlayerActionHandler(
            game_state_repo, character_service, dice_service, combat_service,
            chat_service, ai_response_processor, campaign_service
        )
        
        self.dice_submission_handler = DiceSubmissionHandler(
            game_state_repo, character_service, dice_service, combat_service,
            chat_service, ai_response_processor, campaign_service
        )
        
        self.next_step_handler = NextStepHandler(
            game_state_repo, character_service, dice_service, combat_service,
            chat_service, ai_response_processor, campaign_service
        )
        
        self.retry_handler = RetryHandler(
            game_state_repo, character_service, dice_service, combat_service,
            chat_service, ai_response_processor, campaign_service
        )
        
        # Share context storage across all handlers
        self._setup_shared_context()
    
    def handle_player_action(self, action_data: Dict) -> Dict[str, Any]:
        """Handle a player action."""
        return self.player_action_handler.handle(action_data)
    
    def handle_dice_submission(self, roll_data: List[Dict]) -> Dict[str, Any]:
        """Handle submitted dice rolls."""
        return self.dice_submission_handler.handle(roll_data)
    
    def handle_completed_roll_submission(self, roll_results: List[Dict]) -> Dict[str, Any]:
        """Handle submission of already-completed roll results."""
        return self.dice_submission_handler.handle_completed_rolls(roll_results)
    
    def handle_next_step_trigger(self) -> Dict[str, Any]:
        """Handle triggering the next step."""
        return self.next_step_handler.handle()
    
    def handle_retry(self) -> Dict[str, Any]:
        """Handle retry request."""
        return self.retry_handler.handle()
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state for frontend."""
        return self._get_state_for_frontend()
    
    def _get_state_for_frontend(self) -> Dict[str, Any]:
        """Get current game state formatted for frontend."""
        from app.services.combat_service import CombatFormatter
        from app.services.chat_service import ChatFormatter
        
        game_state = self.game_state_repo.get_game_state()
        
        return {
            "party": self._format_party_for_frontend(game_state.party),
            "location": game_state.current_location.get("name", "Unknown"),
            "location_description": game_state.current_location.get("description", ""),
            "chat_history": ChatFormatter.format_for_frontend(game_state.chat_history),
            "dice_requests": game_state.pending_player_dice_requests,
            "combat_info": CombatFormatter.format_combat_status(self.game_state_repo),
            "can_retry_last_request": self.retry_handler._can_retry_last_request()
        }
    
    def _format_party_for_frontend(self, party_instances: Dict) -> list:
        """Format party data for frontend."""
        from app.game.calculators.dice_mechanics import get_proficiency_bonus
        
        return [
            {
                "id": pc.id,
                "name": pc.name,
                "race": pc.race,
                "char_class": pc.char_class,
                "level": pc.level,
                "hp": pc.current_hp,
                "max_hp": pc.max_hp,
                "ac": pc.armor_class,
                "conditions": pc.conditions,
                "icon": pc.icon,
                "stats": pc.base_stats.model_dump(),
                "proficiencies": pc.proficiencies.model_dump(),
                "proficiency_bonus": get_proficiency_bonus(pc.level)
            } for pc in party_instances.values()
        ]
    
    def _setup_shared_context(self):
        """Set up shared retry context for all handlers."""
        # Replace individual handler context with shared references
        for handler in [self.player_action_handler, self.dice_submission_handler, 
                       self.next_step_handler, self.retry_handler]:
            # Override their individual context storage with shared references
            handler._last_ai_request_context = self._shared_ai_request_context
            handler._last_ai_request_timestamp = self._shared_ai_request_timestamp
            
            # Override their storage methods to update shared context
            original_store = handler._store_ai_request_context
            def make_shared_store(h):
                def shared_store(messages, initial_instruction=None):
                    self._shared_ai_request_context = {
                        "messages": messages.copy(),
                        "initial_instruction": initial_instruction
                    }
                    import time
                    self._shared_ai_request_timestamp = time.time()
                    # Update all handlers to point to new shared context
                    for other_handler in [self.player_action_handler, self.dice_submission_handler,
                                        self.next_step_handler, self.retry_handler]:
                        other_handler._last_ai_request_context = self._shared_ai_request_context
                        other_handler._last_ai_request_timestamp = self._shared_ai_request_timestamp
                return shared_store
            handler._store_ai_request_context = make_shared_store(handler)
            
            # Override the can_retry method to use shared context
            def make_shared_can_retry(h):
                def shared_can_retry():
                    if not self._shared_ai_request_context or not self._shared_ai_request_timestamp:
                        return False
                    import time
                    return (time.time() - self._shared_ai_request_timestamp) <= 300
                return shared_can_retry
            handler._can_retry_last_request = make_shared_can_retry(handler)
