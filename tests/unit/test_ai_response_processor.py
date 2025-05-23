"""
Unit tests for AI response processor service.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse, DiceRequest, GameStateUpdate
from app.game.models import GameState, CombatState, Combatant, CharacterInstance


class TestAIResponseProcessor(unittest.TestCase):
    """Test AI response processor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        
        # Get services
        self.processor = self.container.get_ai_response_processor()
        self.game_state_repo = self.container.get_game_state_repository()
        self.character_service = self.container.get_character_service()
        self.dice_service = self.container.get_dice_service()
        self.combat_service = self.container.get_combat_service()
        self.chat_service = self.container.get_chat_service()
        
        # Get initial game state
        self.game_state = self.game_state_repo.get_game_state()
    
    def test_process_simple_narrative_response(self):
        """Test processing a simple AI response with just narrative."""
        # Get initial chat history length (may include initial narrative)
        initial_chat_len = len(self.chat_service.get_chat_history())
        
        ai_response = AIResponse(
            reasoning="This is a simple narrative response",
            narrative="You enter the tavern and see a bustling crowd.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False
        )
        
        pending_requests, needs_rerun = self.processor.process_response(ai_response)
        
        self.assertEqual(pending_requests, [])
        self.assertFalse(needs_rerun)
        
        # Check that narrative was added to chat
        chat_history = self.chat_service.get_chat_history()
        self.assertEqual(len(chat_history), initial_chat_len + 1)
        self.assertEqual(chat_history[-1]['role'], 'assistant')
        self.assertEqual(chat_history[-1]['content'], "You enter the tavern and see a bustling crowd.")
    
    def test_process_response_with_location_update(self):
        """Test processing AI response with location update."""
        # Location is a dict, not a model
        new_location = {
            "name": "The Prancing Pony",
            "description": "A famous inn in Bree"
        }
        
        ai_response = AIResponse(
            reasoning="Moving to a new location",
            narrative="You arrive at the Prancing Pony.",
            location_update=new_location,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False
        )
        
        self.processor.process_response(ai_response)
        
        # Check location was updated
        updated_state = self.game_state_repo.get_game_state()
        self.assertEqual(updated_state.current_location["name"], "The Prancing Pony")
        self.assertEqual(updated_state.current_location["description"], "A famous inn in Bree")
    
    def test_process_response_with_player_dice_requests(self):
        """Test processing AI response with player dice requests."""
        # Use a character ID that exists in initial party data
        dice_request = DiceRequest(
            request_id="test_roll_1",
            character_ids=["char2"],  # Elara's ID in initial data
            type="ability_check",
            dice_formula="1d20",
            ability="wisdom",
            reason="Perception check"
        )
        
        ai_response = AIResponse(
            reasoning="Requesting perception check",
            narrative="Make a perception check.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[dice_request],
            end_turn=False
        )
        
        pending_requests, needs_rerun = self.processor.process_response(ai_response)
        
        self.assertEqual(len(pending_requests), 1)
        self.assertFalse(needs_rerun)
        self.assertEqual(pending_requests[0]["request_id"], "test_roll_1")
        self.assertEqual(pending_requests[0]["type"], "ability_check")
    
    def test_process_response_with_npc_dice_requests(self):
        """Test processing AI response with NPC dice requests."""
        # Add an NPC combatant (NPCs in combat are tracked as combatants and monster_stats)
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="goblin1", name="Goblin", initiative=10, is_player=False)
        ]
        # Also add to monster_stats for character service to find it
        self.game_state.combat.monster_stats["goblin1"] = {
            "name": "Goblin",
            "hp": 7,
            "ac": 15,
            "conditions": []
        }
        
        dice_request = DiceRequest(
            request_id="npc_roll_1",
            character_ids=["goblin1"],
            type="attack",
            dice_formula="1d20",
            reason="Goblin attacks"
        )
        
        ai_response = AIResponse(
            reasoning="NPC attacking",
            narrative="The goblin attacks!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[dice_request],
            end_turn=False
        )
        
        with patch.object(self.dice_service, 'perform_roll', return_value={
            "character_id": "goblin1",
            "roll_type": "attack",
            "total": 15,
            "result_summary": "Goblin: Attack Roll = 15",
            "result_message": "Goblin rolled 1d20 = 15 for attack"
        }):
            pending_requests, needs_rerun = self.processor.process_response(ai_response)
        
        # NPC rolls should be performed automatically
        self.assertEqual(pending_requests, [])
        self.assertTrue(needs_rerun)  # Should trigger AI rerun after NPC rolls
    
    def test_combat_started_flag_handling(self):
        """Test handling of combat just started flag."""
        # Start combat
        self.game_state.combat.is_active = True
        self.game_state.combat._combat_just_started_flag = True
        self.game_state.combat.combatants = [
            Combatant(id="char2", name="Elara", initiative=-1, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=-1, is_player=False)
        ]
        
        ai_response = AIResponse(
            reasoning="Combat started",
            narrative="Roll for initiative!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],  # AI didn't request initiative
            end_turn=False
        )
        
        with patch.object(self.dice_service, 'perform_roll', return_value={
            "character_id": "goblin1",
            "roll_type": "initiative",
            "total": 15,
            "result_summary": "Goblin: Initiative = 15"
        }):
            pending_requests, needs_rerun = self.processor.process_response(ai_response)
        
        # Should force initiative rolls
        self.assertEqual(len(pending_requests), 1)  # Player initiative
        self.assertEqual(pending_requests[0]["type"], "initiative")
        self.assertFalse(self.game_state.combat._combat_just_started_flag)  # Flag should be reset
    
    def test_turn_advancement_handling(self):
        """Test turn advancement when AI signals end_turn."""
        # Set up active combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=20, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=10, is_player=False)
        ]
        self.game_state.combat.current_turn_index = 0
        
        ai_response = AIResponse(
            reasoning="Player turn complete",
            narrative="Elara's turn ends.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=True  # Signal to end turn
        )
        
        self.processor.process_response(ai_response)
        
        # Turn should advance
        self.assertEqual(self.game_state.combat.current_turn_index, 1)
    
    def test_pre_calculate_next_combatant(self):
        """Test pre-calculation of next combatant when removing current."""
        from app.ai_services.schemas import CombatantRemoveUpdate
        
        # Set up combat with 3 combatants
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="char2", name="Elara", initiative=20, is_player=True),
            Combatant(id="goblin1", name="Goblin 1", initiative=15, is_player=False),
            Combatant(id="goblin2", name="Goblin 2", initiative=10, is_player=False)
        ]
        # Add NPCs to monster_stats for character service to find them
        self.game_state.combat.monster_stats["goblin1"] = {
            "name": "Goblin 1", "hp": 5, "ac": 15, "conditions": []
        }
        self.game_state.combat.monster_stats["goblin2"] = {
            "name": "Goblin 2", "hp": 7, "ac": 15, "conditions": []
        }
        self.game_state.combat.current_turn_index = 1  # Goblin 1's turn
        
        # Remove the current combatant
        remove_update = CombatantRemoveUpdate(
            type="combatant_remove",
            character_id="goblin1"
        )
        
        ai_response = AIResponse(
            reasoning="Goblin 1 defeated",
            narrative="Goblin 1 falls!",
            location_update=None,
            game_state_updates=[remove_update],
            dice_requests=[],
            end_turn=True
        )
        
        # Process the response
        self.processor.process_response(ai_response)
        
        # Should have removed goblin1
        self.assertEqual(len(self.game_state.combat.combatants), 2)
        # Current index should now point to goblin2
        self.assertEqual(self.game_state.combat.combatants[self.game_state.combat.current_turn_index].id, "goblin2")


class TestDiceRequestHandler(unittest.TestCase):
    """Test dice request handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        
        # Get services
        self.game_state_repo = self.container.get_game_state_repository()
        self.character_service = self.container.get_character_service()
        self.dice_service = self.container.get_dice_service()
        self.chat_service = self.container.get_chat_service()
        
        # Create handler
        from app.services.ai_response_processor import DiceRequestHandler
        self.handler = DiceRequestHandler(
            self.game_state_repo, 
            self.character_service,
            self.dice_service,
            self.chat_service
        )
        
        self.game_state = self.game_state_repo.get_game_state()
    
    def test_resolve_character_ids_with_all_keyword(self):
        """Test resolving 'all' keyword in character IDs."""
        # Set up combat with multiple combatants
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=20, is_player=True, current_hp=30),
            Combatant(id="goblin1", name="Goblin 1", initiative=15, is_player=False, current_hp=7),
            Combatant(id="goblin2", name="Goblin 2", initiative=10, is_player=False, current_hp=0)  # Defeated
        ]
        
        # Mock character validator to mark goblin2 as defeated
        with patch('app.services.character_service.CharacterValidator.is_character_defeated') as mock_defeated:
            mock_defeated.side_effect = lambda char_id, repo: char_id == "goblin2"
            
            resolved_ids = self.handler._resolve_character_ids(["all"])
        
        # Should include only non-defeated combatants
        self.assertEqual(set(resolved_ids), {"elara", "goblin1"})
    
    def test_force_initiative_rolls(self):
        """Test forcing initiative rolls when combat starts."""
        player_requests = []
        npc_requests = []
        party_ids = {"elara"}
        
        # Set up combat needing initiative
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=-1, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=-1, is_player=False)
        ]
        
        self.handler._force_initiative_rolls(player_requests, npc_requests, party_ids)
        
        # Should add initiative requests for both
        self.assertEqual(len(player_requests), 1)
        self.assertEqual(len(npc_requests), 1)
        self.assertEqual(player_requests[0]["type"], "initiative")
        self.assertEqual(npc_requests[0]["type"], "initiative")


class TestTurnAdvancementHandler(unittest.TestCase):
    """Test turn advancement handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        
        # Get services
        self.game_state_repo = self.container.get_game_state_repository()
        self.combat_service = self.container.get_combat_service()
        
        # Create handler
        from app.services.ai_response_processor import TurnAdvancementHandler
        self.handler = TurnAdvancementHandler(self.game_state_repo, self.combat_service)
        
        self.game_state = self.game_state_repo.get_game_state()
    
    def test_normal_turn_advancement(self):
        """Test normal turn advancement."""
        from app.ai_services.schemas import AIResponse
        
        # Set up combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=20, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=10, is_player=False)
        ]
        self.game_state.combat.current_turn_index = 0
        
        ai_response = Mock(spec=AIResponse)
        ai_response.end_turn = True
        
        self.handler.handle_turn_advancement(ai_response, False, False)
        
        # Turn should advance
        self.assertEqual(self.game_state.combat.current_turn_index, 1)
    
    def test_turn_advancement_with_pre_calculated_info(self):
        """Test turn advancement with pre-calculated combatant info."""
        from app.ai_services.schemas import AIResponse
        
        # Set up combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=20, is_player=True),
            Combatant(id="goblin1", name="Goblin 1", initiative=15, is_player=False),
            Combatant(id="goblin2", name="Goblin 2", initiative=10, is_player=False)
        ]
        self.game_state.combat.current_turn_index = 0
        
        ai_response = Mock(spec=AIResponse)
        ai_response.end_turn = True
        
        # Pre-calculated info says to go to goblin2 (skipping goblin1)
        next_info = {
            "combatant_id": "goblin2",
            "new_index": 2,
            "should_end_combat": False
        }
        
        self.handler.handle_turn_advancement(ai_response, False, False, next_info)
        
        # Should jump to goblin2
        self.assertEqual(self.game_state.combat.current_turn_index, 2)
    
    def test_turn_advancement_delays_for_player_requests(self):
        """Test that turn advancement is delayed when player requests are pending."""
        from app.ai_services.schemas import AIResponse
        
        # Set up combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=20, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=10, is_player=False)
        ]
        self.game_state.combat.current_turn_index = 0
        
        ai_response = Mock(spec=AIResponse)
        ai_response.end_turn = True
        
        # Player requests are pending
        self.handler.handle_turn_advancement(ai_response, False, True)
        
        # Turn should NOT advance yet
        self.assertEqual(self.game_state.combat.current_turn_index, 0)


if __name__ == '__main__':
    unittest.main()
