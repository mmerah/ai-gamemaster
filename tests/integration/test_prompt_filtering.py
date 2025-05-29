"""
Integration tests for prompt filtering functionality.
Tests that system error messages are excluded from AI prompts but preserved in chat history.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from app.game.prompt_builder import build_ai_prompt_context
from tests.conftest import get_test_config


class MockHandler:
    """Mock handler for prompt building tests."""
    def __init__(self, rag_service=None):
        self.rag_service = rag_service


class TestPromptFilteringIntegration(unittest.TestCase):
    """Integration tests for system error message filtering."""
    
    def setUp(self):
        """Set up test environment."""
        reset_container()
        self.container = ServiceContainer(get_test_config())
        self.container.initialize()
        
        self.game_state_repo = self.container.get_game_state_repository()
        self.chat_service = self.container.get_chat_service()
        self.game_state = self.game_state_repo.get_game_state()
        
    def test_system_error_messages_excluded_from_ai_prompts(self):
        """Test that system error messages appear in chat history but not in AI prompts."""
        # Add various messages to chat history
        self.chat_service.add_message("user", "I want to cast fireball")
        self.chat_service.add_message("system", 
            "(Error: Failed to get a valid response from the AI. You can try clicking 'Retry Last Request' if this was due to a parsing error.)", 
            is_dice_result=True)
        self.chat_service.add_message("user", "Let me try that again")
        self.chat_service.add_message("assistant", "You cast fireball successfully!")
        self.chat_service.add_message("system",
            "(Error processing AI step: Connection failed. You can try clicking 'Retry Last Request' if this was due to a parsing error.)",
            is_dice_result=True)
        
        # Get chat history for frontend (should include all messages)
        frontend_history = self.chat_service.get_chat_history()
        
        # Build AI prompt context (should exclude error messages)
        mock_handler = MockHandler()
        ai_prompt_messages = build_ai_prompt_context(self.game_state, mock_handler, None)
        
        # Verify frontend history includes error messages
        frontend_errors = [msg for msg in frontend_history 
                          if msg.get('role') == 'system' and 
                          msg.get('content', '').strip().startswith('(Error')]
        self.assertEqual(len(frontend_errors), 2, "Frontend history should contain 2 error messages")
        
        # Verify AI prompt excludes error messages
        ai_prompt_errors = [msg for msg in ai_prompt_messages 
                           if msg.get('content', '').strip().startswith('(Error')]
        self.assertEqual(len(ai_prompt_errors), 0, "AI prompt should contain 0 error messages")
        
        # Verify other messages are included in AI prompt
        user_messages_in_prompt = [msg for msg in ai_prompt_messages 
                                  if msg.get('role') == 'user' and 
                                  'fireball' in msg.get('content', '')]
        self.assertGreater(len(user_messages_in_prompt), 0, "User messages should be in AI prompt")
        
        assistant_messages_in_prompt = [msg for msg in ai_prompt_messages 
                                       if msg.get('role') == 'assistant' and 
                                       'successfully' in msg.get('content', '')]
        self.assertGreater(len(assistant_messages_in_prompt), 0, "Assistant messages should be in AI prompt")
    
    def test_regular_system_messages_not_filtered(self):
        """Test that regular system messages are not filtered out."""
        # Add regular system message
        self.chat_service.add_message("system", "Welcome to the adventure!", is_dice_result=False)
        self.chat_service.add_message("system", "Combat has started!", is_dice_result=True)
        
        # Build AI prompt
        mock_handler = MockHandler()
        ai_prompt_messages = build_ai_prompt_context(self.game_state, mock_handler, None)
        
        # Verify regular system messages are included
        welcome_msg_found = any(msg.get('content') == 'Welcome to the adventure!' 
                               for msg in ai_prompt_messages)
        combat_msg_found = any(msg.get('content') == 'Combat has started!' 
                              for msg in ai_prompt_messages)
        
        self.assertTrue(welcome_msg_found, "Welcome system message should be in AI prompt")
        self.assertTrue(combat_msg_found, "Combat system message should be in AI prompt")
    
    def test_mixed_message_scenario(self):
        """Test a realistic scenario with mixed message types."""
        # Simulate a game session with various message types
        messages = [
            ("user", "I search the room", {}),
            ("assistant", "You find a hidden door!", {}),
            ("system", "(Error: Failed to get a valid response from the AI. You can try clicking 'Retry Last Request' if this was due to a parsing error.)", {"is_dice_result": True}),
            ("user", "I open the hidden door", {}),
            ("assistant", "The door creaks open revealing a dark corridor.", {}),
            ("system", "Roll for perception check", {"is_dice_result": True}),
            ("user", "**Player Rolls Submitted:**\nResult: 15", {}),
            ("system", "(Error processing AI step: Timeout. You can try clicking 'Retry Last Request' if this was due to a parsing error.)", {"is_dice_result": True}),
            ("assistant", "You notice a trap trigger!", {})
        ]
        
        # Add all messages
        for role, content, kwargs in messages:
            self.chat_service.add_message(role, content, **kwargs)
        
        # Get both histories
        frontend_history = self.chat_service.get_chat_history()
        mock_handler = MockHandler()
        ai_prompt_messages = build_ai_prompt_context(self.game_state, mock_handler, None)
        
        # Count message types in each
        frontend_msg_count = len(frontend_history)
        
        # Frontend should have all messages plus any initial messages
        # The game state starts with an initial narrative message
        initial_message_count = len(self.game_state.chat_history) - len(messages)
        self.assertEqual(frontend_msg_count, len(messages) + initial_message_count, 
                        "Frontend should have all messages plus initial messages")
        
        # The actual count might be less due to truncation, but should not include errors
        ai_errors = [msg for msg in ai_prompt_messages 
                    if msg.get('content', '').strip().startswith('(Error')]
        self.assertEqual(len(ai_errors), 0, "No error messages should be in AI prompt")
        
        # Verify specific non-error messages are present
        trap_msg_found = any('trap trigger' in msg.get('content', '') 
                            for msg in ai_prompt_messages)
        self.assertTrue(trap_msg_found, "Trap trigger message should be in AI prompt")


if __name__ == '__main__':
    unittest.main()