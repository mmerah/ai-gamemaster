"""
Integration test for damage roll backend trigger.
This test verifies that after submitting damage rolls, the backend trigger is properly set.
"""
import unittest
from unittest.mock import Mock
from flask import Flask
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse
from app.game.models import GameState, Combatant
from tests.conftest import get_test_config


class TestDamageRollBackendTrigger(unittest.TestCase):
    """Test damage roll backend trigger functionality."""
    
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
        self.dice_service = self.container.get_dice_service()
        
        # Mock AI service
        self.mock_ai_service = Mock()
        
        # Set the AI service in Flask config
        self.app.config['AI_SERVICE'] = self.mock_ai_service
    
    def tearDown(self):
        """Clean up Flask context."""
        self.app_context.pop()
        
    def test_damage_roll_triggers_backend(self):
        """Test that damage roll submission triggers backend call."""
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
        # Add pending dice request for damage roll
        game_state.pending_player_dice_requests = []
        self.game_state_repo.save_game_state(game_state)
        
        # Simulate that attack already happened
        self.chat_service.add_message("assistant", "The goblin swings its sword at the player!")
        self.chat_service.add_message("user", "**NPC Rolls:**\ngoblin1 rolls Attack Roll: Result **18**.", is_dice_result=True)
        self.chat_service.add_message("assistant", "The attack hits! Rolling for damage...")
        
        # Mock AI response after damage roll
        damage_applied_response = AIResponse(
            reasoning="Applying damage and continuing combat",
            narrative="The player grimaces as the goblin's blade cuts deep, dealing 5 damage!",
            location_update=None,
            game_state_updates=[{
                "type": "hp_change",
                "character_id": "char1",
                "value": -5
            }],
            dice_requests=[],
            end_turn=True  # End goblin's turn
        )
        
        self.mock_ai_service.get_response.return_value = damage_applied_response
        
        # Submit damage roll result
        roll_results = [{
            "character_id": "goblin1",
            "character_name": "Goblin",
            "roll_type": "damage_roll",
            "dice_formula": "1d6+2",
            "total": 5,
            "reason": "Goblin sword damage",
            "individual_rolls": [3],
            "modifier": 2,
            "success": None,
            "dc": None,
            "result_message": "Goblin rolls Damage Roll: 1d6+2 -> [3] +2 = **5**.",
            "result_summary": "Goblin rolls Damage Roll: Result **5**.",
            "is_player_controlled": False
        }]
        
        # Handle the completed roll submission
        result = self.game_event_handler.handle_completed_roll_submission(roll_results)
        
        # Verify response
        self.assertEqual(result['status_code'], 200, "Should succeed")
        
        # Check that backend trigger is set appropriately
        # Since the goblin's turn ended, if it's now a player's turn, backend trigger should be False
        # But if it's still an NPC turn or there are more NPC actions, it should be True
        game_state = self.game_state_repo.get_game_state()
        current_combatant_id = game_state.combat.combatants[game_state.combat.current_turn_index].id
        current_combatant = next(c for c in game_state.combat.combatants if c.id == current_combatant_id)
        
        if current_combatant.is_player:
            self.assertFalse(result['needs_backend_trigger'], "Should not trigger backend for player turn")
        else:
            self.assertTrue(result['needs_backend_trigger'], "Should trigger backend for NPC turn")
            
        # Verify the damage was processed
        self.assertTrue(self.mock_ai_service.get_response.called, "AI should have been called")
        
        # Check that the roll result was added to chat
        chat_history = self.chat_service.get_chat_history()
        
        # Debug print chat history
        print("\n=== CHAT HISTORY ===")
        for msg in chat_history[-10:]:
            print(f"{msg.get('type', 'unknown')}: {msg.get('content', '')[:100]}...")
        print("=== END ===\n")
        
        found_damage_roll = any("Damage Roll" in msg.get("content", "") and "**5**" in msg.get("content", "")
                               for msg in chat_history)
        self.assertTrue(found_damage_roll, "Damage roll result should be in chat history")


if __name__ == '__main__':
    unittest.main()