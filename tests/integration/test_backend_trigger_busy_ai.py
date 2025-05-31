"""
Integration test for backend trigger preservation when AI is busy.
This test verifies that the backend trigger flag is preserved when the AI is busy.
"""
import unittest
from unittest.mock import Mock, patch
from flask import Flask
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse
from app.game.models import GameState
from app.game.models import Combatant
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
        self.game_event_manager = self.container.get_game_event_manager()
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
        game_state = self.game_state_repo.get_game_state()
        from app.ai_services.schemas import InitialCombatantData
        updated_state = self.combat_service.start_combat(game_state, [
            InitialCombatantData(id="goblin1", name="Goblin", hp=10, ac=12, stats={"DEX": 14}),
            InitialCombatantData(id="goblin2", name="Goblin Archer", hp=8, ac=13, stats={"DEX": 16})
        ])
        self.game_state_repo.save_game_state(updated_state)
        
        # Set up combat state - first goblin's turn
        game_state = self.game_state_repo.get_game_state()
        # Order by initiative (highest first)
        game_state.combat.combatants = [
            Combatant(id="goblin1", name="Goblin", initiative=15, is_player=False, current_hp=10, max_hp=10, armor_class=12),
            Combatant(id="goblin2", name="Goblin Archer", initiative=14, is_player=False, current_hp=8, max_hp=8, armor_class=13),
            Combatant(id="char1", name="Player", initiative=5, is_player=True, current_hp=20, max_hp=20, armor_class=15)
        ]
        game_state.combat.current_turn_index = 0  # First goblin's turn (highest initiative)
        from app.ai_services.schemas import MonsterBaseStats
        game_state.combat.monster_stats["goblin1"] = MonsterBaseStats(
            name="Goblin",
            initial_hp=10,
            ac=12,
            stats={"DEX": 12},
            abilities=[],
            attacks=[]
        )
        game_state.combat.monster_stats["goblin2"] = MonsterBaseStats(
            name="Goblin Archer",
            initial_hp=8,
            ac=13,
            stats={"DEX": 16},
            abilities=[],
            attacks=[]
        )
        self.game_state_repo.save_game_state(game_state)
        
        # Mock AI response that ends first goblin's turn
        # This will advance to the second goblin's turn, requiring a backend trigger
        attack_response = AIResponse(
            reasoning="The goblin attacks and ends its turn!",
            narrative="The goblin swings its sword and steps back!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=True  # End turn, advancing to goblin2
        )
        
        # Create a slow AI response to simulate processing time
        def slow_ai_response(messages):
            time.sleep(0.1)  # Simulate AI processing time
            return attack_response
        
        self.mock_ai_service.get_response.side_effect = slow_ai_response
        
        # First trigger - should start processing
        result1 = self.game_event_manager.handle_next_step_trigger()
        self.assertEqual(result1['status_code'], 200)
        # With auto-continuation, both NPCs will complete their turns and advance to player turn
        # So backend trigger should be False (player's turn)
        self.assertFalse(result1['needs_backend_trigger'])
        
        # Now test the "AI busy" scenario
        # Manually set up a state where backend trigger should be True (NPC turn)
        game_state = self.game_state_repo.get_game_state()
        game_state.combat.current_turn_index = 0  # Reset to first goblin's turn
        self.game_state_repo.save_game_state(game_state)
        
        # Set the AI processing flag manually to simulate the AI being busy
        self.game_event_manager._shared_state['ai_processing'] = True
        self.game_event_manager._shared_state['needs_backend_trigger'] = True
        
        # Second trigger while AI is busy
        result2 = self.game_event_manager.handle_next_step_trigger()
        
        # Should get a 429 (busy) response
        self.assertEqual(result2['status_code'], 429)
        self.assertEqual(result2['error'], "AI is busy")
        
        # CRITICAL: Backend trigger should still be True
        self.assertTrue(result2['needs_backend_trigger'], 
                       "Backend trigger should be preserved when AI is busy")
        
        # Verify shared state still has the trigger set
        self.assertTrue(self.game_event_manager._shared_state['needs_backend_trigger'],
                       "Shared state should preserve backend trigger when AI is busy")
        
        # Clear the AI processing flag to simulate completion
        self.game_event_manager._shared_state['ai_processing'] = False
        
        # Third trigger after AI is no longer busy
        result3 = self.game_event_manager.handle_next_step_trigger()
        
        # This time it should process successfully
        self.assertEqual(result3['status_code'], 200)
        # After processing both NPC turns, should end on player turn
        self.assertFalse(result3['needs_backend_trigger'])


if __name__ == '__main__':
    unittest.main()