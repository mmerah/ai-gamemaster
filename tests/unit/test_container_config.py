"""
Unit tests for ServiceContainer configuration options.
"""
import unittest
import os
from tests.test_helpers import IsolatedTestCase, setup_test_environment

# Set up environment before importing app modules
setup_test_environment()

from app.core.container import ServiceContainer, reset_container

# Only import RAG services if RAG is enabled
if os.environ.get('RAG_ENABLED', 'true').lower() != 'false':
    from app.services.rag import NoOpRAGService, RAGServiceImpl
else:
    NoOpRAGService = None
    RAGServiceImpl = None


class TestContainerConfiguration(IsolatedTestCase, unittest.TestCase):
    """Test that ServiceContainer respects configuration options."""
    
    def tearDown(self):
        """Reset container after each test."""
        reset_container()
    
    def test_rag_enabled_by_default(self):
        """Test that RAG is enabled by default."""
        if os.environ.get('RAG_ENABLED', 'true').lower() == 'false':
            self.skipTest("RAG is disabled")
            
        container = ServiceContainer({})
        container.initialize()
        
        rag_service = container.get_rag_service()
        self.assertIsInstance(rag_service, RAGServiceImpl)
        self.assertNotIsInstance(rag_service, NoOpRAGService)
    
    def test_rag_disabled_via_config(self):
        """Test that RAG can be disabled via configuration."""
        if os.environ.get('RAG_ENABLED', 'true').lower() == 'false':
            self.skipTest("RAG is disabled")
            
        container = ServiceContainer({'RAG_ENABLED': False})
        container.initialize()
        
        rag_service = container.get_rag_service()
        self.assertIsInstance(rag_service, NoOpRAGService)
        self.assertNotIsInstance(rag_service, RAGServiceImpl)
    
    def test_tts_disabled_via_config(self):
        """Test that TTS can be disabled via configuration."""
        container = ServiceContainer({
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False
        })
        container.initialize()
        
        tts_service = container.get_tts_service()
        self.assertIsNone(tts_service)
    
    def test_repository_type_config(self):
        """Test repository type configuration."""
        # Test memory repository
        container = ServiceContainer({
            'GAME_STATE_REPO_TYPE': 'memory',
            'RAG_ENABLED': False,
            'TTS_PROVIDER': 'disabled'
        })
        container.initialize()
        
        repo = container.get_game_state_repository()
        self.assertEqual(repo.__class__.__name__, 'InMemoryGameStateRepository')
        
        reset_container()
        
        # Test file repository
        container = ServiceContainer({
            'GAME_STATE_REPO_TYPE': 'file',
            'CAMPAIGNS_DIR': 'test_campaigns',
            'RAG_ENABLED': False,
            'TTS_PROVIDER': 'disabled'
        })
        container.initialize()
        
        repo = container.get_game_state_repository()
        self.assertEqual(repo.__class__.__name__, 'FileGameStateRepository')
    
    def test_directory_path_configs(self):
        """Test that directory path configurations are respected."""
        config = {
            'CAMPAIGNS_DIR': 'custom/campaigns',
            'CHARACTER_TEMPLATES_DIR': 'custom/templates',
            'RAG_ENABLED': False,
            'TTS_PROVIDER': 'disabled'
        }
        
        container = ServiceContainer(config)
        container.initialize()
        
        # Check repositories use custom paths
        # Campaign repository removed - using campaign template repository instead
        campaign_template_repo = container.get_campaign_template_repository()
        self.assertIsNotNone(campaign_template_repo)
        
        template_repo = container.get_character_template_repository()
        self.assertEqual(template_repo.templates_dir, 'custom/templates')


if __name__ == '__main__':
    unittest.main()