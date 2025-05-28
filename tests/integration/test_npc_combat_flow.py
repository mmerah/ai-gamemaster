"""
Integration test for NPC combat turn handling.
This test verifies that NPCs receive proper turn instructions.
"""
import unittest
from unittest.mock import patch, Mock
from flask import Flask
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse
from app.game.models import GameState, Combatant
from tests.conftest import get_test_config


class TestNPCCombatFlow(unittest.TestCase):
    """Test NPC combat turn flow and prompt generation."""
    
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
        
    def test_npc_turn_receives_explicit_instruction(self):
        """Test that when it's an NPC's turn, the AI receives an explicit instruction."""
        # Start combat with NPCs
        self.combat_service.start_combat([
            {"id": "goblin1", "name": "Goblin Warrior", "hp": 15, "ac": 13, "stats": {"DEX": 14}}
        ])
        
        # Set up combat state - skip initiative and go straight to goblin's turn
        game_state = self.game_state_repo.get_game_state()
        game_state.combat.combatants = [
            Combatant(id="char1", name="Torvin", initiative=10, is_player=True),
            Combatant(id="goblin1", name="Goblin Warrior", initiative=15, is_player=False)
        ]
        game_state.combat.current_turn_index = 1  # Goblin's turn
        # Set up monster stats for the goblin
        game_state.combat.monster_stats["goblin1"] = {
            "hp": 15,
            "initial_hp": 15,
            "ac": 13,
            "stats": {"DEX": 14},
            "conditions": []
        }
        self.game_state_repo.save_game_state(game_state)
        
        # Mock AI response for the NPC turn
        ai_response = AIResponse(
            reasoning="The goblin attacks the nearest player",
            narrative="The goblin snarls and swings its scimitar!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[{
                "request_id": "goblin_attack",
                "character_ids": ["goblin1"],
                "type": "attack_roll",
                "dice_formula": "1d20",
                "reason": "Goblin attacks with scimitar"
            }],
            end_turn=False
        )
        
        # Capture ALL messages sent to AI (since there may be multiple calls due to auto-continuation)
        all_captured_calls = []
        def capture_ai_call(messages):
            all_captured_calls.append(messages)
            return ai_response
        
        self.mock_ai_service.get_response.side_effect = capture_ai_call
        
        # Trigger next step (which should handle the NPC turn)
        result = self.game_event_handler.handle_next_step_trigger()
        
        # Verify the request was successful
        if result['status_code'] != 200:
            print(f"Error response: {result}")
        self.assertEqual(result['status_code'], 200)
        
        # Verify AI was called (might be multiple times due to auto-continuation)
        self.assertTrue(self.mock_ai_service.get_response.called)
        
        # Check that at least one AI call was made
        self.assertTrue(len(all_captured_calls) > 0, "AI should have been called at least once")
        
        # Look through ALL captured calls (due to auto-continuation, the first call has what we need)
        found_npc_instruction = False
        found_combat_status = False
        
        # We specifically want to check the FIRST call, which should have both the combat status and NPC instruction
        if all_captured_calls:
            first_call_messages = all_captured_calls[0]
            
            # Debug: Print all user messages from first call
            print("\n=== FIRST AI CALL MESSAGES ===")
            for i, msg in enumerate(first_call_messages):
                if msg.get("role") == "user":
                    print(f"\nUser Message {i}:")
                    print(msg["content"][:500] + "..." if len(msg["content"]) > 500 else msg["content"])
            print("\n=== END MESSAGES ===\n")
            
            for msg in first_call_messages:
                if msg.get("role") == "user":
                    content = msg["content"]
                    
                    # Check if this is the CURRENT STATUS message that includes combat status
                    if "CURRENT STATUS:" in content and "Current Turn: Goblin Warrior" in content:
                        found_combat_status = True
                        
                    # Look for actual explicit instructions (not just status)
                    content_lower = content.lower()
                    if any(phrase in content_lower for phrase in [
                        "it's goblin warrior's turn",
                        "narrate their action",
                        "narrate goblin warrior's action"
                    ]):
                        found_npc_instruction = True
        
        # Verify we found the combat status AND an explicit instruction
        self.assertTrue(found_combat_status, "Should have found combat status in messages")
        
        # NOW we should find an explicit NPC turn instruction
        self.assertTrue(
            found_npc_instruction, 
            f"Expected to find explicit NPC turn instruction in messages, but found none. "
            f"Messages: {[msg.get('content', '')[:200] + '...' for msg in first_call_messages if msg.get('role') == 'user']}"
        )
    
    def test_player_turn_vs_npc_turn_instructions(self):
        """Test that player turns and NPC turns receive different instructions."""
        # Set up combat with mixed combatants
        self.combat_service.start_combat([
            {"id": "goblin1", "name": "Goblin", "hp": 10, "ac": 12, "stats": {"DEX": 14}}
        ])
        
        game_state = self.game_state_repo.get_game_state()
        game_state.combat.combatants = [
            Combatant(id="char1", name="Torvin", initiative=15, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=10, is_player=False)
        ]
        # Set up monster stats for the goblin
        game_state.combat.monster_stats["goblin1"] = {
            "hp": 10,
            "initial_hp": 10,
            "ac": 12,
            "stats": {"DEX": 14},
            "conditions": []
        }
        
        # Test 1: Player's turn
        game_state.combat.current_turn_index = 0
        self.game_state_repo.save_game_state(game_state)
        
        player_messages = None
        def capture_player_turn(messages):
            nonlocal player_messages
            player_messages = messages
            return AIResponse(
                reasoning="Waiting for player action",
                narrative="It's Torvin's turn.",
                location_update=None,
                game_state_updates=[],
                dice_requests=[],
                end_turn=False
            )
        
        self.mock_ai_service.get_response.side_effect = capture_player_turn
        
        # Handle player action
        result = self.game_event_handler.handle_player_action({
            "action_type": "free_text",
            "value": "I attack the goblin"
        })
        
        self.assertEqual(result['status_code'], 200)
        
        # Test 2: NPC's turn
        game_state.combat.current_turn_index = 1
        self.game_state_repo.save_game_state(game_state)
        
        npc_messages = None
        def capture_npc_turn(messages):
            nonlocal npc_messages
            npc_messages = messages
            return AIResponse(
                reasoning="Goblin attacks",
                narrative="The goblin strikes!",
                location_update=None,
                game_state_updates=[],
                dice_requests=[],
                end_turn=True
            )
        
        self.mock_ai_service.get_response.side_effect = capture_npc_turn
        
        result = self.game_event_handler.handle_next_step_trigger()
        
        self.assertEqual(result['status_code'], 200)
        
        # Compare the messages
        self.assertIsNotNone(player_messages)
        self.assertIsNotNone(npc_messages)
        
        # Player turn should have the player's action
        found_player_action = any(
            msg.get("role") == "user" and "I attack the goblin" in msg.get("content", "")
            for msg in player_messages
        )
        self.assertTrue(found_player_action, "Player action should be in player turn messages")
        
        # NPC turn should have explicit NPC instruction (this will FAIL currently)
        found_npc_instruction = any(
            msg.get("role") == "user" and 
            any(phrase in msg.get("content", "").lower() for phrase in [
                "goblin's turn",
                "what does goblin do",
                "it's goblin's turn"
            ])
            for msg in npc_messages
        )
        self.assertTrue(
            found_npc_instruction,
            "NPC turn should have explicit instruction about it being the NPC's turn"
        )


if __name__ == '__main__':
    unittest.main()