"""
Unit tests for game event handler service.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse
from app.game.models import Combatant


class TestGameEventHandler(unittest.TestCase):
    """Test game event handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        
        # Get services
        self.handler = self.container.get_game_event_handler()
        self.game_state_repo = self.container.get_game_state_repository()
        self.character_service = self.container.get_character_service()
        self.dice_service = self.container.get_dice_service()
        self.combat_service = self.container.get_combat_service()
        self.chat_service = self.container.get_chat_service()
        self.ai_response_processor = self.container.get_ai_response_processor()
        
        # Get initial game state
        self.game_state = self.game_state_repo.get_game_state()
        
        # Mock AI service
        self.mock_ai_service = Mock()
        self.mock_app = Mock()
        self.mock_app.config = {'AI_SERVICE': self.mock_ai_service}
        
        # Patch current_app
        self.app_patcher = patch('app.services.game_event_handler.current_app', self.mock_app)
        self.app_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.app_patcher.stop()
    
    def test_handle_player_action_success(self):
        """Test successful player action handling."""
        # Get initial chat history length (may include initial narrative)
        initial_chat_len = len(self.chat_service.get_chat_history())
        
        action_data = {
            'action_type': 'free_text',
            'value': 'I search the room'
        }
        
        # Mock AI response
        ai_response = AIResponse(
            reasoning="Player searches the room",
            narrative="You search the room and find a hidden door.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False
        )
        self.mock_ai_service.get_response.return_value = ai_response
        
        # Patch build_ai_prompt_context
        with patch('app.game.prompts.build_ai_prompt_context', return_value=[]):
            result = self.handler.handle_player_action(action_data)
        
        # Check result
        self.assertEqual(result['status_code'], 200)
        self.assertIn('party', result)
        self.assertIn('chat_history', result)
        self.assertFalse(result['needs_backend_trigger'])
        
        # Check chat history was updated
        chat_history = self.chat_service.get_chat_history()
        self.assertEqual(len(chat_history), initial_chat_len + 2)  # Player message + AI response
        self.assertEqual(chat_history[-2]['content'], '"I search the room"')
        self.assertEqual(chat_history[-1]['content'], "You search the room and find a hidden door.")
    
    def test_handle_player_action_empty_text(self):
        """Test handling empty player action."""
        action_data = {
            'action_type': 'free_text',
            'value': ''
        }
        
        result = self.handler.handle_player_action(action_data)
        
        # Should return error
        self.assertEqual(result['status_code'], 400)
        self.assertIn('error', result)
        
        # Check system message was added
        chat_history = self.chat_service.get_chat_history()
        self.assertTrue(any(msg['content'] == "Please type something before sending." for msg in chat_history))
    
    def test_handle_player_action_ai_busy(self):
        """Test rejection when AI is already processing."""
        # Set AI as busy
        self.handler._ai_processing = True
        
        action_data = {
            'action_type': 'free_text',
            'value': 'Test action'
        }
        
        result = self.handler.handle_player_action(action_data)
        
        # Should return busy error
        self.assertEqual(result['status_code'], 429)
        self.assertEqual(result['error'], "AI is busy")
    
    def test_handle_player_action_not_player_turn(self):
        """Test rejection when it's not the player's turn."""
        # Set up combat with NPC's turn
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=10, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=20, is_player=False)
        ]
        self.game_state.combat.current_turn_index = 1  # Goblin's turn
        
        action_data = {
            'action_type': 'free_text',
            'value': 'I attack!'
        }
        
        result = self.handler.handle_player_action(action_data)
        
        # Should return error
        self.assertEqual(result['status_code'], 400)
        
        # Check system message
        chat_history = self.chat_service.get_chat_history()
        self.assertTrue(any("(It's not your turn!)" in msg['content'] for msg in chat_history))
    
    def test_handle_dice_submission_success(self):
        """Test successful dice submission handling."""
        roll_data = [{
            'character_id': 'elara',
            'roll_type': 'attack',
            'dice_formula': '1d20',
            'reason': 'Attack roll'
        }]
        
        # Mock dice roll result
        with patch.object(self.dice_service, 'perform_roll', return_value={
            'character_id': 'elara',
            'roll_type': 'attack',
            'total': 18,
            'result_summary': 'Elara: Attack Roll = 18'
        }):
            # Mock AI response
            ai_response = AIResponse(
                reasoning="Processing attack roll",
                narrative="Elara's attack hits!",
                location_update=None,
                game_state_updates=[],
                dice_requests=[],
                end_turn=False
            )
            self.mock_ai_service.get_response.return_value = ai_response
            
            # Patch build_ai_prompt_context
            with patch('app.game.prompts.build_ai_prompt_context', return_value=[]):
                result = self.handler.handle_dice_submission(roll_data)
        
        # Check result
        self.assertEqual(result['status_code'], 200)
        self.assertIn('submitted_roll_results', result)
        self.assertEqual(len(result['submitted_roll_results']), 1)
    
    def test_handle_completed_roll_submission(self):
        """Test handling of already-completed roll results."""
        roll_results = [{
            'character_id': 'elara',
            'roll_type': 'saving_throw',
            'total': 15,
            'result_summary': 'Elara: Saving Throw = 15',
            'result_message': 'Elara rolled 1d20 + 3 = 15'
        }]
        
        # Mock AI response
        ai_response = AIResponse(
            reasoning="Processing saving throw",
            narrative="Elara succeeds on the saving throw.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False
        )
        self.mock_ai_service.get_response.return_value = ai_response
        
        # Patch build_ai_prompt_context
        with patch('app.game.prompts.build_ai_prompt_context', return_value=[]):
            result = self.handler.handle_completed_roll_submission(roll_results)
        
        # Check result
        self.assertEqual(result['status_code'], 200)
        self.assertIn('submitted_roll_results', result)
        self.assertEqual(result['submitted_roll_results'], roll_results)
    
    def test_handle_next_step_trigger_npc_turn(self):
        """Test triggering next step for NPC turn."""
        # Set up combat with NPC's turn
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=10, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=20, is_player=False)
        ]
        self.game_state.combat.current_turn_index = 1  # Goblin's turn
        
        # Mock AI response
        ai_response = AIResponse(
            reasoning="Goblin attacks",
            narrative="The goblin swings its rusty sword at Elara!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=True
        )
        self.mock_ai_service.get_response.return_value = ai_response
        
        # Patch build_ai_prompt_context
        with patch('app.game.prompts.build_ai_prompt_context', return_value=[]):
            result = self.handler.handle_next_step_trigger()
        
        # Check result
        self.assertEqual(result['status_code'], 200)
        
        # Check that AI was called with NPC turn instruction
        self.mock_ai_service.get_response.assert_called_once()
    
    def test_handle_retry_last_ai_request(self):
        """Test retrying a failed AI request."""
        # First, make a failed request
        action_data = {
            'action_type': 'free_text',
            'value': 'I cast fireball'
        }
        
        # Mock AI failure
        self.mock_ai_service.get_response.return_value = None
        
        # Patch build_ai_prompt_context
        with patch('app.game.prompts.build_ai_prompt_context', return_value=[{"role": "user", "content": "test"}]):
            result = self.handler.handle_player_action(action_data)
        
        # Verify failure
        self.assertEqual(result['status_code'], 500)
        
        # Verify context was stored
        self.assertIsNotNone(self.handler._last_ai_request_context)
        
        # Now test retry
        # Mock successful AI response for retry
        ai_response = AIResponse(
            reasoning="Retrying fireball cast",
            narrative="You cast fireball successfully!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False
        )
        self.mock_ai_service.get_response.return_value = ai_response
        
        retry_result = self.handler.handle_retry_last_ai_request()
        
        # Check retry was successful
        self.assertEqual(retry_result['status_code'], 200)
        
        # Note: Context is NOT cleared after successful retry (by design - keeps it for potential re-retry)
        self.assertIsNotNone(self.handler._last_ai_request_context)
    
    def test_handle_retry_no_stored_context(self):
        """Test retry when no previous request exists."""
        result = self.handler.handle_retry_last_ai_request()
        
        # Should return error
        self.assertEqual(result['status_code'], 400)
        self.assertEqual(result['error'], "No previous AI request to retry")
    
    def test_determine_backend_trigger_needed(self):
        """Test logic for determining if backend trigger is needed."""
        # Test 1: NPC action requires follow-up
        needs_trigger = self.handler._determine_backend_trigger_needed(True, [])
        self.assertTrue(needs_trigger)
        
        # Test 2: Player requests pending
        needs_trigger = self.handler._determine_backend_trigger_needed(False, [{"request_id": "test"}])
        self.assertFalse(needs_trigger)
        
        # Test 3: No pending requests, NPC turn
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            Combatant(id="elara", name="Elara", initiative=10, is_player=True),
            Combatant(id="goblin1", name="Goblin", initiative=20, is_player=False)
        ]
        self.game_state.combat.current_turn_index = 1  # Goblin's turn
        
        needs_trigger = self.handler._determine_backend_trigger_needed(False, [])
        self.assertTrue(needs_trigger)


class TestPlayerActionValidator(unittest.TestCase):
    """Test player action validation."""
    
    def test_valid_action(self):
        """Test validation of valid action."""
        from app.services.game_event_handler import PlayerActionValidator
        
        action_data = {
            'action_type': 'free_text',
            'value': 'I open the door'
        }
        
        result = PlayerActionValidator.validate_action(action_data)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.error_message, "")
    
    def test_empty_text_action(self):
        """Test validation of empty text."""
        from app.services.game_event_handler import PlayerActionValidator
        
        action_data = {
            'action_type': 'free_text',
            'value': ''
        }
        
        result = PlayerActionValidator.validate_action(action_data)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.is_empty_text)
    
    def test_invalid_action_format(self):
        """Test validation of invalid action format."""
        from app.services.game_event_handler import PlayerActionValidator
        
        # Missing action_type
        action_data = {'value': 'test'}
        result = PlayerActionValidator.validate_action(action_data)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "Invalid action format")
        
        # None action data
        result = PlayerActionValidator.validate_action(None)
        self.assertFalse(result.is_valid)


class TestDiceSubmissionValidator(unittest.TestCase):
    """Test dice submission validation."""
    
    def test_valid_submission(self):
        """Test validation of valid dice submission."""
        from app.services.game_event_handler import DiceSubmissionValidator
        
        roll_data = [{
            'character_id': 'elara',
            'roll_type': 'attack',
            'dice_formula': '1d20'
        }]
        
        result = DiceSubmissionValidator.validate_submission(roll_data)
        self.assertTrue(result.is_valid)
    
    def test_invalid_submission_format(self):
        """Test validation of invalid submission format."""
        from app.services.game_event_handler import DiceSubmissionValidator
        
        # Not a list
        roll_data = "invalid"
        result = DiceSubmissionValidator.validate_submission(roll_data)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "Invalid data format, expected list of rolls")


if __name__ == '__main__':
    unittest.main()
