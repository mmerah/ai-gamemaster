"""
Integration test for automatic AI flow continuation.
This test verifies that the backend automatically continues AI processing
when needed without requiring frontend triggers.
"""
import unittest
from unittest.mock import Mock
from flask import Flask
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse
from app.game.models import GameState, Combatant
from tests.conftest import get_test_config


class TestAutoContinuation(unittest.TestCase):
    """Test automatic AI flow continuation."""
    
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
        
    def test_auto_continuation_npc_attack_to_damage(self):
        """Test that NPC attack roll automatically continues to damage roll."""
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
        
        # Mock AI responses
        # First response: attack roll
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
        
        # Second response: damage roll (after seeing attack hit)
        damage_response = AIResponse(
            reasoning="Attack hit, rolling damage",
            narrative="The goblin's blade strikes true!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[{
                "request_id": "goblin_damage",
                "character_ids": ["goblin1"],
                "type": "damage_roll",
                "dice_formula": "1d6",
                "reason": "Goblin sword damage"
            }],
            end_turn=False
        )
        
        # Third response: apply damage and end turn
        final_response = AIResponse(
            reasoning="Damage dealt, ending turn",
            narrative="The player takes 4 damage!",
            location_update=None,
            game_state_updates=[{
                "type": "hp_change",
                "character_id": "char1",
                "value": -4
            }],
            dice_requests=[],
            end_turn=True
        )
        
        # Set up mock to return different responses in sequence
        self.mock_ai_service.get_response.side_effect = [attack_response, damage_response, final_response]
        
        # Trigger the NPC turn - should auto-continue through all steps
        result = self.game_event_handler.handle_next_step_trigger()
        
        # Verify the result
        self.assertEqual(result['status_code'], 200)
        
        # The AI should have been called 3 times automatically
        self.assertEqual(self.mock_ai_service.get_response.call_count, 3)
        
        # Check chat history to verify all steps happened
        chat_history = self.chat_service.get_chat_history()
        chat_contents = [msg.get("content", "") for msg in chat_history]
        
        # Should have the turn instruction
        self.assertTrue(any("It's Goblin's turn" in content for content in chat_contents))
        
        # Should have attack roll result
        self.assertTrue(any("Attack Roll" in content and "**NPC Rolls:**" in content 
                           for content in chat_contents))
        
        # Should have damage roll result
        self.assertTrue(any("Damage Roll" in content and "**NPC Rolls:**" in content 
                           for content in chat_contents))
        
        # Should have final narrative
        self.assertTrue(any("takes 4 damage" in content for content in chat_contents))
        
        # Since turn ended and it's now a player turn, no backend trigger needed
        self.assertFalse(result['needs_backend_trigger'])
        
    def test_auto_continuation_depth_limit(self):
        """Test that auto-continuation has a depth limit to prevent infinite loops."""
        # Set up combat state
        self.combat_service.start_combat([
            {"id": "goblin1", "name": "Goblin", "hp": 10, "ac": 12, "stats": {"DEX": 14}}
        ])
        
        game_state = self.game_state_repo.get_game_state()
        game_state.combat.combatants = [
            Combatant(id="goblin1", name="Goblin", initiative=15, is_player=False)
        ]
        game_state.combat.current_turn_index = 0
        self.game_state_repo.save_game_state(game_state)
        
        # Mock AI to always request another roll (simulating a complex multi-roll sequence)
        infinite_response = AIResponse(
            reasoning="Need another roll",
            narrative="Rolling again...",
            location_update=None,
            game_state_updates=[],
            dice_requests=[{
                "request_id": f"roll_inf",
                "character_ids": ["goblin1"],
                "type": "custom",
                "dice_formula": "1d20",
                "reason": "Another roll"
            }],
            end_turn=False
        )
        
        # Return the same response every time
        self.mock_ai_service.get_response.return_value = infinite_response
        
        # Trigger - should stop at depth limit
        result = self.game_event_handler.handle_next_step_trigger()
        
        # Should have called AI 6 times (initial + 5 continuations)
        self.assertEqual(self.mock_ai_service.get_response.call_count, 6)
        
        # Should still indicate backend trigger needed (since we hit the limit)
        self.assertTrue(result['needs_backend_trigger'])


if __name__ == '__main__':
    unittest.main()