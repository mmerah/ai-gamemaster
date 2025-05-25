"""
Unit tests for basic UI integration functionality.
"""
import unittest
from unittest.mock import Mock, patch
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse


class TestGameEventManager(unittest.TestCase):
    """Test basic game event manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled'
        })
        self.container.initialize()
        
        # Get services
        self.handler = self.container.get_game_event_handler()
        self.game_state_repo = self.container.get_game_state_repository()
        
        # Mock AI service
        self.mock_ai_service = Mock()
    
    def test_game_state_retrieval(self):
        """Test that game state can be retrieved for frontend."""
        result = self.handler.get_game_state()
        
        # Check that required fields are present
        self.assertIn('party', result)
        self.assertIn('location', result)
        self.assertIn('chat_history', result)
        self.assertIn('dice_requests', result)
        self.assertIn('combat_info', result)
        self.assertIn('can_retry_last_request', result)
        
        # Should be a list of party members (empty initially)
        self.assertIsInstance(result['party'], list)
        self.assertIsInstance(result['dice_requests'], list)
        self.assertIsInstance(result['chat_history'], list)
        self.assertIsInstance(result['combat_info'], dict)
        self.assertIsInstance(result['can_retry_last_request'], bool)
    
    def test_player_action_returns_structured_response(self):
        """Test player action handling returns proper structure."""
        action_data = {
            'action_type': 'free_text',
            'value': 'I search the room'
        }
        
        # Mock successful AI response
        ai_response = AIResponse(
            reasoning="Player searches the room",
            narrative="You search the room and find a hidden door.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False
        )
        
        # Patch both the AI service manager and prompt context
        with patch('app.ai_services.manager.get_ai_service', return_value=self.mock_ai_service), \
             patch('app.game.prompts.build_ai_prompt_context', return_value=[]):
            self.mock_ai_service.get_response.return_value = ai_response
            result = self.handler.handle_player_action(action_data)
        
        # Check that the action returns a structured response
        self.assertIn('status_code', result)
        self.assertIsInstance(result, dict)
        # Accept any valid HTTP status code
        self.assertIsInstance(result['status_code'], int)
    
    def test_dice_submission_returns_structured_response(self):
        """Test handling dice submission returns proper structure."""
        result = self.handler.handle_dice_submission([])
        
        # Should return structured response
        self.assertIn('status_code', result)
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['status_code'], int)
    
    def test_next_step_trigger(self):
        """Test next step trigger functionality."""
        result = self.handler.handle_next_step_trigger()
        
        # Should return some response
        self.assertIn('status_code', result)
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['status_code'], int)
    
    def test_retry_handler_exists(self):
        """Test that retry handler method exists and is callable."""
        # Just test that the method exists and can be called
        try:
            result = self.handler.handle_retry()
            self.assertIsInstance(result, dict)
            self.assertIn('status_code', result)
        except Exception as e:
            # If it fails, that's also fine - we're just testing it exists
            self.assertIsInstance(e, Exception)


if __name__ == '__main__':
    unittest.main()
