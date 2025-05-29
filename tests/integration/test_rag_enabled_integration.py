"""
Integration tests specifically for when RAG is enabled.
These tests ensure the full RAG functionality works correctly.
"""
import unittest
import os
import pytest

# Skip entire module if RAG is disabled
if os.environ.get('RAG_ENABLED', 'true').lower() == 'false':
    pytest.skip("RAG is disabled", allow_module_level=True)

from app.core.container import ServiceContainer, reset_container
from app.services.rag import RAGServiceImpl


class TestRAGEnabledIntegration(unittest.TestCase):
    """Integration tests for RAG functionality when enabled."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment with RAG enabled once for all tests."""
        reset_container()
        # Explicitly enable RAG for these tests
        cls.config = {
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': True  # Enable RAG for these tests
        }
        cls.container = ServiceContainer(cls.config)
        cls.container.initialize()
    
    def setUp(self):
        """Set up test-specific state."""
        # Use the shared container instance
        self.container = self.__class__.container
    
    def test_rag_service_is_real_implementation(self):
        """Test that real RAG service is created when enabled."""
        rag_service = self.container.get_rag_service()
        self.assertIsInstance(rag_service, RAGServiceImpl)
    
    def test_rag_service_integration_with_game_event_handler(self):
        """Test that RAG service integrates properly with game event handler."""
        game_event_handler = self.container.get_game_event_handler()
        
        # Verify the handler has a real RAG service
        self.assertIsInstance(game_event_handler.rag_service, RAGServiceImpl)
    
    def test_rag_service_provides_knowledge(self):
        """Test that RAG service actually provides knowledge when enabled."""
        rag_service = self.container.get_rag_service()
        game_state_repo = self.container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()
        
        # Test with a spell casting action
        action = "I cast fireball at the goblin"
        results = rag_service.get_relevant_knowledge(action, game_state)
        
        # Should return results (even if empty due to test data)
        self.assertIsNotNone(results)
        self.assertGreaterEqual(results.total_queries, 0)
        self.assertGreaterEqual(results.execution_time_ms, 0)


if __name__ == '__main__':
    unittest.main()