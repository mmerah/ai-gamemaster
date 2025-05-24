"""
Unit tests for retry feature UI integration.
"""
import unittest
from unittest.mock import Mock, patch
from app.core.container import ServiceContainer, reset_container
from app.ai_services.schemas import AIResponse


class TestRetryUIIntegration(unittest.TestCase):
    """Test retry feature UI integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        
        # Get services
        self.handler = self.container.get_game_event_handler()
        self.game_state_repo = self.container.get_game_state_repository()
        
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
    
    def test_can_retry_flag_in_successful_response(self):
        """Test that can_retry_last_request flag is included in successful responses."""
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
        self.mock_ai_service.get_response.return_value = ai_response
        
        # Patch build_ai_prompt_context
        with patch('app.game.prompts.build_ai_prompt_context', return_value=[]):
            result = self.handler.handle_player_action(action_data)
        
        # Check that can_retry_last_request flag is present in response
        self.assertIn('can_retry_last_request', result)
        # For successful requests with no stored context, it should be False
        self.assertFalse(result['can_retry_last_request'])
    
    def test_can_retry_flag_after_ai_failure(self):
        """Test that can_retry_last_request flag is True after AI failure."""
        action_data = {
            'action_type': 'free_text',
            'value': 'I cast fireball'
        }
        
        # Mock AI failure
        self.mock_ai_service.get_response.return_value = None
        
        # Patch build_ai_prompt_context
        with patch('app.game.prompts.build_ai_prompt_context', return_value=[{"role": "user", "content": "test"}]):
            result = self.handler.handle_player_action(action_data)
        
        # Verify failure occurred
        self.assertEqual(result['status_code'], 500)
        
        # Check that can_retry_last_request flag is present and True
        self.assertIn('can_retry_last_request', result)
        self.assertTrue(result['can_retry_last_request'])
    
    def test_can_retry_flag_after_successful_retry(self):
        """Test that can_retry_last_request flag persists after successful retry."""
        # First, cause an AI failure to store context
        action_data = {
            'action_type': 'free_text',
            'value': 'I cast fireball'
        }
        
        # Mock AI failure
        self.mock_ai_service.get_response.return_value = None
        
        # Patch build_ai_prompt_context
        with patch('app.game.prompts.build_ai_prompt_context', return_value=[{"role": "user", "content": "test"}]):
            result = self.handler.handle_player_action(action_data)
        
        # Verify failure and context storage
        self.assertEqual(result['status_code'], 500)
        self.assertTrue(result['can_retry_last_request'])
        
        # Now test successful retry
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
        
        # Check that can_retry_last_request flag is still True (context persists)
        self.assertIn('can_retry_last_request', retry_result)
        self.assertTrue(retry_result['can_retry_last_request'])
    
    def test_can_retry_flag_when_no_context(self):
        """Test that can_retry_last_request flag is False when no context exists."""
        # Try to retry without any previous failed request
        result = self.handler.handle_retry_last_ai_request()
        
        # Should return error
        self.assertEqual(result['status_code'], 400)
        self.assertEqual(result['error'], "No previous AI request to retry")
        
        # Check that can_retry_last_request flag is False
        self.assertIn('can_retry_last_request', result)
        self.assertFalse(result['can_retry_last_request'])
    
    def test_can_retry_flag_in_busy_response(self):
        """Test that can_retry_last_request flag is included in busy responses."""
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
        
        # Check that can_retry_last_request flag is present
        self.assertIn('can_retry_last_request', result)
        # Should be False since no context was stored (request was rejected)
        self.assertFalse(result['can_retry_last_request'])


if __name__ == '__main__':
    unittest.main()
