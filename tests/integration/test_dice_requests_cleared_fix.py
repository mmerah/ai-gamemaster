"""
Test for PlayerDiceRequestsClearedEvent fix to ensure only specific submitted requests are cleared.
"""
import pytest
from unittest.mock import Mock, patch
from typing import List

from app import create_app
from app.core.container import get_container, reset_container
from app.events.game_update_events import (
    PlayerDiceRequestAddedEvent,
    PlayerDiceRequestsClearedEvent
)
from app.ai_services.schemas import AIResponse
from app.game.unified_models import DiceRequest, GameStateModel, CharacterInstanceModel, CombatStateModel, CombatantModel


class TestPlayerDiceRequestsClearedFix:
    """Test the fix for PlayerDiceRequestsClearedEvent to only clear specific requests."""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app with proper configuration."""
        reset_container()
        
        from run import create_app
        app = create_app({
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False,
            'TESTING': True
        })
        
        return app
    
    @pytest.fixture
    def container(self, app):
        """Get the service container."""
        with app.app_context():
            return get_container()
    
    def collect_events(self, container) -> List:
        """Collect all events from the event queue."""
        events = []
        event_queue = container.get_event_queue()
        
        while not event_queue.is_empty():
            event = event_queue.get_event(block=False)
            if event:
                events.append(event)
        return events
    
    def setup_combat_state(self, container):
        """Setup a basic combat state for testing."""
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()
        
        # Setup basic party
        game_state.party = {
            "hero1": CharacterInstanceModel(
                template_id="test_hero1_template",
                campaign_id="test_campaign",
                level=5,
                current_hp=50, max_hp=50,
                conditions=[],
                inventory=[]
            ),
            "hero2": CharacterInstanceModel(
                template_id="test_hero2_template",
                campaign_id="test_campaign",
                level=5,
                current_hp=35, max_hp=35,
                conditions=[],
                inventory=[]
            )
        }
        
        # Setup combat
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=[
                CombatantModel(id="hero1", name="Hero 1", initiative=15, current_hp=50, max_hp=50, armor_class=18, is_player=True),
                CombatantModel(id="hero2", name="Hero 2", initiative=12, current_hp=35, max_hp=35, armor_class=13, is_player=True),
                CombatantModel(id="goblin1", name="Goblin", initiative=10, current_hp=7, max_hp=7, armor_class=13, is_player=False)
            ],
            current_turn_index=0,
            round_number=1
        )
        
        return game_state
    
    def test_partial_dice_request_clearing(self, container, app):
        """Test that only specific submitted request IDs are cleared, not all pending requests."""
        with app.app_context():
            # Setup game state
            game_state = self.setup_combat_state(container)
            
            # Add multiple pending dice requests directly to game state
            from app.ai_services.schemas import DiceRequest
            game_state.pending_player_dice_requests = [
                DiceRequest(
                    request_id="req_001",
                    character_ids=["hero1"],
                    type="attack",
                    dice_formula="1d20+5",
                    reason="First attack"
                ),
                DiceRequest(
                    request_id="req_002", 
                    character_ids=["hero1"],
                    type="damage",
                    dice_formula="1d8+3",
                    reason="First damage"
                ),
                DiceRequest(
                    request_id="req_003",
                    character_ids=["hero2"],
                    type="attack",
                    dice_formula="1d20+2",
                    reason="Second attack"
                )
            ]
            
            # Get the dice submission handler
            game_event_manager = container.get_game_event_manager()
            dice_handler = game_event_manager.dice_submission_handler
            
            # Mock AI service to return empty response
            ai_service = app.config.get('AI_SERVICE')
            ai_service.get_response = Mock(return_value=AIResponse(
                narrative="Rolls processed.",
                reasoning="Processing roll submission"
            ))
            
            # Submit only req_001 and req_003 (skip req_002)
            roll_data = [
                {
                    "request_id": "req_001",
                    "character_id": "hero1",
                    "roll_type": "attack",
                    "dice_formula": "1d20+5"
                },
                {
                    "request_id": "req_003",
                    "character_id": "hero2", 
                    "roll_type": "attack",
                    "dice_formula": "1d20+2"
                }
            ]
            
            # Process the dice submission
            with patch.object(container.get_dice_service(), 'perform_roll') as mock_dice:
                mock_dice.return_value = {
                    "character_id": "hero1",
                    "total_result": 15,
                    "result_summary": "Attack roll: 15",
                    "success": True
                }
                
                dice_handler.handle(roll_data)
            
            # Collect events
            events = self.collect_events(container)
            
            # Find PlayerDiceRequestsClearedEvent
            cleared_events = [e for e in events if e.event_type == "player_dice_requests_cleared"]
            assert len(cleared_events) == 1
            
            cleared_event = cleared_events[0]
            assert isinstance(cleared_event, PlayerDiceRequestsClearedEvent)
            
            # Should only have cleared req_001 and req_003
            assert set(cleared_event.cleared_request_ids) == {"req_001", "req_003"}
            
            # req_002 should still be pending
            remaining_requests = game_state.pending_player_dice_requests
            assert len(remaining_requests) == 1
            assert remaining_requests[0].request_id == "req_002"
    
    def test_clear_all_when_no_request_ids_provided(self, container, app):
        """Test that all requests are cleared when no specific request IDs are provided."""
        with app.app_context():
            # Setup game state
            game_state = self.setup_combat_state(container)
            
            # Add pending requests without request_id in submission
            from app.ai_services.schemas import DiceRequest
            game_state.pending_player_dice_requests = [
                DiceRequest(
                    request_id="req_001",
                    character_ids=["hero1"],
                    type="attack",
                    dice_formula="1d20+5",
                    reason="Attack roll"
                ),
                DiceRequest(
                    request_id="req_002",
                    character_ids=["hero2"], 
                    type="attack",
                    dice_formula="1d20+2",
                    reason="Attack roll"
                )
            ]
            
            # Get the dice submission handler
            game_event_manager = container.get_game_event_manager()
            dice_handler = game_event_manager.dice_submission_handler
            
            # Mock AI service
            ai_service = app.config.get('AI_SERVICE')
            ai_service.get_response = Mock(return_value=AIResponse(
                narrative="Rolls processed.",
                reasoning="Processing roll submission"
            ))
            
            # Submit rolls without request_id (legacy behavior)
            roll_data = [
                {
                    "character_id": "hero1",
                    "roll_type": "attack",
                    "dice_formula": "1d20+5"
                    # No request_id
                }
            ]
            
            # Process the dice submission
            with patch.object(container.get_dice_service(), 'perform_roll') as mock_dice:
                mock_dice.return_value = {
                    "character_id": "hero1",
                    "total_result": 15,
                    "result_summary": "Attack roll: 15",
                    "success": True
                }
                
                dice_handler.handle(roll_data)
            
            # Collect events
            events = self.collect_events(container)
            
            # Find PlayerDiceRequestsClearedEvent
            cleared_events = [e for e in events if e.event_type == "player_dice_requests_cleared"]
            assert len(cleared_events) == 1
            
            cleared_event = cleared_events[0]
            assert isinstance(cleared_event, PlayerDiceRequestsClearedEvent)
            
            # Should have cleared all pending requests (legacy behavior)
            assert set(cleared_event.cleared_request_ids) == {"req_001", "req_002"}
            
            # No requests should remain
            assert len(game_state.pending_player_dice_requests) == 0
    
    def test_no_event_when_no_requests_cleared(self, container, app):
        """Test that no PlayerDiceRequestsClearedEvent is emitted when no requests are cleared."""
        with app.app_context():
            # Setup game state
            game_state = self.setup_combat_state(container)
            
            # Add pending request with different ID
            from app.ai_services.schemas import DiceRequest
            game_state.pending_player_dice_requests = [
                DiceRequest(
                    request_id="req_different",
                    character_ids=["hero1"],
                    type="attack",
                    dice_formula="1d20+5",
                    reason="Attack roll"
                )
            ]
            
            # Get the dice submission handler
            game_event_manager = container.get_game_event_manager()
            dice_handler = game_event_manager.dice_submission_handler
            
            # Mock AI service
            ai_service = app.config.get('AI_SERVICE')
            ai_service.get_response = Mock(return_value=AIResponse(
                narrative="Rolls processed.",
                reasoning="Processing roll submission"
            ))
            
            # Submit roll with non-matching request_id
            roll_data = [
                {
                    "request_id": "req_not_found",
                    "character_id": "hero1",
                    "roll_type": "attack",
                    "dice_formula": "1d20+5"
                }
            ]
            
            # Process the dice submission
            with patch.object(container.get_dice_service(), 'perform_roll') as mock_dice:
                mock_dice.return_value = {
                    "character_id": "hero1",
                    "total_result": 15,
                    "result_summary": "Attack roll: 15", 
                    "success": True
                }
                
                dice_handler.handle(roll_data)
            
            # Collect events
            events = self.collect_events(container)
            
            # Should NOT have PlayerDiceRequestsClearedEvent
            cleared_events = [e for e in events if e.event_type == "player_dice_requests_cleared"]
            assert len(cleared_events) == 0
            
            # Original request should still be pending
            assert len(game_state.pending_player_dice_requests) == 1
            assert game_state.pending_player_dice_requests[0].request_id == "req_different"