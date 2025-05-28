"""
Integration test for backend trigger preservation when AI is busy.
This test verifies that the backend trigger flag is preserved when the AI is busy.
"""
import unittest
from unittest.mock import Mock, patch
from flask import Flask
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse
from app.game.models import GameState, Combatant
from tests.conftest import get_test_config
import time


class TestBackendTriggerBusyAI(unittest.TestCase):
    """Test backend trigger preservation when AI is busy."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.config = get_test_config()
        
        # Create Flask app for context
        self.app = Flask(__name__)
        self.app.config.update(self.config)
        
        # Create app context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.container = ServiceContainer(self.config)
        self.container.initialize()
        
        # Get services
        self.game_event_handler = self.container.get_game_event_handler()
        self.game_state_repo = self.container.get_game_state_repository()
        self.combat_service = self.container.get_combat_service()
        self.chat_service = self.container.get_chat_service()
        
        # Mock AI service
        self.mock_ai_service = Mock()
        
        # Set the AI service in Flask config
        self.app.config['AI_SERVICE'] = self.mock_ai_service
    
    def tearDown(self):
        """Clean up Flask context."""
        self.app_context.pop()
        
    def test_backend_trigger_preserved_when_ai_busy(self):
        """Test that backend trigger is preserved when AI is busy processing."""
        # Start combat
        self.combat_service.start_combat([
            {"id": "goblin1", "name": "Goblin", "hp": 10, "ac": 12, "stats": {"DEX": 14}}
        ])
        
        # Set up combat state - goblin's turn
        game_state = self.game_state_repo.get_game_state()
        game_state.combat.combatants = [
            Combatant(id="char1", name="Player", initiative=5, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=15, is_player=False)
        ]
        game_state.combat.current_turn_index = 1  # Goblin's turn
        game_state.combat.monster_stats["goblin1"] = {
            "hp": 10,
            "initial_hp": 10,
            "ac": 12,
            "conditions": []
        }
        self.game_state_repo.save_game_state(game_state)
        
        # Mock AI response that requests a dice roll
        attack_response = AIResponse(
            reasoning="The goblin attacks!",
            narrative="The goblin swings its sword!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[{
                "request_id": "goblin_attack",
                "character_ids": ["goblin1"],
                "type": "attack_roll",
                "dice_formula": "1d20",
                "reason": "Goblin attacks"
            }],
            end_turn=False
        )
        
        # Create a slow AI response to simulate processing time
        def slow_ai_response(messages):
            time.sleep(0.1)  # Simulate AI processing time
            return attack_response
        
        self.mock_ai_service.get_response.side_effect = slow_ai_response
        
        # First trigger - should start processing
        result1 = self.game_event_handler.handle_next_step_trigger()
        self.assertEqual(result1['status_code'], 200)
        self.assertTrue(result1['needs_backend_trigger'])
        
        # Immediately trigger again while AI is still processing
        # This simulates the frontend rapidly calling the endpoint
        # We need to do this in a way that catches the AI being busy
        
        # Set the AI processing flag manually to simulate the race condition
        self.game_event_handler._shared_state['ai_processing'] = True
        self.game_event_handler._shared_state['needs_backend_trigger'] = True
        
        # Second trigger while AI is busy
        result2 = self.game_event_handler.handle_next_step_trigger()
        
        # Should get a 429 (busy) response
        self.assertEqual(result2['status_code'], 429)
        self.assertEqual(result2['error'], "AI is busy")
        
        # CRITICAL: Backend trigger should still be True
        self.assertTrue(result2['needs_backend_trigger'], 
                       "Backend trigger should be preserved when AI is busy")
        
        # Verify shared state still has the trigger set
        self.assertTrue(self.game_event_handler._shared_state['needs_backend_trigger'],
                       "Shared state should preserve backend trigger when AI is busy")
        
        # Clear the AI processing flag to simulate completion
        self.game_event_handler._shared_state['ai_processing'] = False
        
        # Third trigger after AI is no longer busy
        result3 = self.game_event_handler.handle_next_step_trigger()
        
        # This time it should process successfully
        self.assertEqual(result3['status_code'], 200)
        # After successful processing, the trigger might be cleared or set based on game state


if __name__ == '__main__':
    unittest.main()