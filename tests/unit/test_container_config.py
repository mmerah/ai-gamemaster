"""
Unit tests for ServiceContainer configuration options.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from app.services.rag import NoOpRAGService, RAGServiceImpl


class TestContainerConfiguration(unittest.TestCase):
    """Test that ServiceContainer respects configuration options."""
    
    def tearDown(self):
        """Reset container after each test."""
        reset_container()
    
    def test_rag_enabled_by_default(self):
        """Test that RAG is enabled by default."""
        container = ServiceContainer({})
        container.initialize()
        
        rag_service = container.get_rag_service()
        self.assertIsInstance(rag_service, RAGServiceImpl)
        self.assertNotIsInstance(rag_service, NoOpRAGService)
    
    def test_rag_disabled_via_config(self):
        """Test that RAG can be disabled via configuration."""
        container = ServiceContainer({'RAG_ENABLED': False})
        container.initialize()
        
        rag_service = container.get_rag_service()
        self.assertIsInstance(rag_service, NoOpRAGService)
        self.assertNotIsInstance(rag_service, RAGServiceImpl)
    
    def test_tts_disabled_via_config(self):
        """Test that TTS can be disabled via configuration."""
        container = ServiceContainer({'TTS_PROVIDER': 'disabled'})
        container.initialize()
        
        tts_service = container.get_tts_service()
        self.assertIsNone(tts_service)
    
    def test_repository_type_config(self):
        """Test repository type configuration."""
        # Test memory repository
        container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        container.initialize()
        
        repo = container.get_game_state_repository()
        self.assertEqual(repo.__class__.__name__, 'InMemoryGameStateRepository')
        
        reset_container()
        
        # Test file repository
        container = ServiceContainer({
            'GAME_STATE_REPO_TYPE': 'file',
            'GAME_STATE_FILE_PATH': 'test_game_state.json'
        })
        container.initialize()
        
        repo = container.get_game_state_repository()
        self.assertEqual(repo.__class__.__name__, 'FileGameStateRepository')
    
    def test_directory_path_configs(self):
        """Test that directory path configurations are respected."""
        config = {
            'CAMPAIGNS_DIR': 'custom/campaigns',
            'CHARACTER_TEMPLATES_DIR': 'custom/templates'
        }
        
        container = ServiceContainer(config)
        container.initialize()
        
        # Check repositories use custom paths
        campaign_repo = container.get_campaign_repository()
        self.assertEqual(campaign_repo.campaigns_dir, 'custom/campaigns')
        
        template_repo = container.get_character_template_repository()
        self.assertEqual(template_repo.templates_dir, 'custom/templates')


if __name__ == '__main__':
    unittest.main()