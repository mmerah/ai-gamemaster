"""
Unit tests for chat service functionality.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from tests.conftest import get_test_config


class TestChatService(unittest.TestCase):
    """Test chat service functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer(get_test_config())
        self.container.initialize()
        self.chat_service = self.container.get_chat_service()
        self.repo = self.container.get_game_state_repository()
    
    def test_add_message(self):
        """Test adding messages to chat history."""
        original_count = len(self.repo.get_game_state().chat_history)
        
        self.chat_service.add_message("user", "Hello, DM!")
        
        game_state = self.repo.get_game_state()
        self.assertEqual(len(game_state.chat_history), original_count + 1)
        self.assertEqual(game_state.chat_history[-1]["role"], "user")
        self.assertEqual(game_state.chat_history[-1]["content"], "Hello, DM!")
    
    def test_add_assistant_message(self):
        """Test adding assistant messages to chat history."""
        original_count = len(self.repo.get_game_state().chat_history)
        
        self.chat_service.add_message("assistant", "Test narrative", 
                                     gm_thought="Test reasoning")
        
        game_state = self.repo.get_game_state()
        self.assertEqual(len(game_state.chat_history), original_count + 1)
        self.assertEqual(game_state.chat_history[-1]["role"], "assistant")
        self.assertEqual(game_state.chat_history[-1]["content"], "Test narrative")
        self.assertIn("gm_thought", game_state.chat_history[-1])
    
    def test_get_chat_history(self):
        """Test getting chat history."""
        # Add several messages
        for i in range(5):
            self.chat_service.add_message("user", f"Message {i}")
        
        history = self.chat_service.get_chat_history()
        # Should have original messages plus our 5 new ones
        self.assertGreater(len(history), 5)
        self.assertEqual(history[-1]["content"], "Message 4")


if __name__ == '__main__':
    unittest.main()
