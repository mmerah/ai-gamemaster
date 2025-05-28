"""
Integration test for animation steps collection during auto-continuation.
This test verifies that intermediate states are collected for frontend animation.
"""
import unittest
from unittest.mock import Mock
from flask import Flask
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse
from app.game.models import GameState, Combatant
from tests.conftest import get_test_config


class TestAnimationSteps(unittest.TestCase):
    """Test animation steps collection during auto-continuation."""
    
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
        
    def test_animation_steps_collected_during_auto_continuation(self):
        """Test that animation steps are collected during NPC turn auto-continuation."""
        # Start combat
        self.combat_service.start_combat([
            {"id": "goblin1", "name": "Goblin", "hp": 10, "ac": 12, "stats": {"DEX": 14}}
        ])
        
        # Set up combat state - goblin's turn
        game_state = self.game_state_repo.get_game_state()
        game_state.combat.combatants = [
            Combatant(id="char1", name="Player", initiative=5, is_player=True, hp=21, max_hp=21),
            Combatant(id="goblin1", name="Goblin", initiative=15, is_player=False)
        ]
        game_state.combat.current_turn_index = 1  # Goblin's turn
        game_state.combat.monster_stats["goblin1"] = {
            "hp": 10,
            "initial_hp": 10,
            "ac": 12,
            "conditions": []
        }
        # The character service should handle party initialization
        self.game_state_repo.save_game_state(game_state)
        
        # Mock AI responses
        # First response: attack roll
        attack_response = AIResponse(
            reasoning="The goblin attacks!",
            narrative="The goblin lunges forward with its rusty sword!",
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
        
        # Second response: damage roll
        damage_response = AIResponse(
            reasoning="Attack hit, rolling damage",
            narrative="The goblin's blade finds its mark!",
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
        
        # Third response: apply damage
        final_response = AIResponse(
            reasoning="Damage dealt, ending turn",
            narrative="The player grimaces as the blade cuts deep, drawing blood!",
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
        
        # Trigger the NPC turn
        result = self.game_event_handler.handle_next_step_trigger()
        
        # Verify the result
        self.assertEqual(result['status_code'], 200)
        
        # Check that we have animation steps
        self.assertIn('animation_steps', result)
        animation_steps = result['animation_steps']
        
        # Should have 3 steps (one for each AI response with narrative)
        self.assertEqual(len(animation_steps), 3)
        
        # Verify each step has the expected structure
        for i, step in enumerate(animation_steps):
            self.assertIn('narrative', step)
            self.assertIn('chat_history', step)
            self.assertIn('combat_info', step)
            self.assertIn('party', step)
        
        # Verify the narratives match our responses
        self.assertEqual(animation_steps[0]['narrative'], "The goblin lunges forward with its rusty sword!")
        self.assertEqual(animation_steps[1]['narrative'], "The goblin's blade finds its mark!")
        self.assertEqual(animation_steps[2]['narrative'], "The player grimaces as the blade cuts deep, drawing blood!")
        
        # Verify combat info shows it's the goblin's turn in early steps
        self.assertEqual(animation_steps[0]['combat_info']['current_turn'], 'Goblin')


if __name__ == '__main__':
    unittest.main()