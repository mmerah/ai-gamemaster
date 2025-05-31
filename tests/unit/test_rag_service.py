"""
Unit tests for the RAG service implementation.
Tests the RAG service with mocked dependencies.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os

# Skip entire module if RAG is disabled
import pytest
if os.environ.get('RAG_ENABLED', 'true').lower() == 'false':
    pytest.skip("RAG is disabled", allow_module_level=True)

from app.core.rag_interfaces import RAGQuery, QueryType, KnowledgeResult, RAGResults
from app.services.rag.rag_service import RAGServiceImpl
import tempfile
import json
import shutil


class TestRAGService(unittest.TestCase):
    """Test the main RAG service implementation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures to avoid reinitializing embeddings."""
        # Create temporary directory for test knowledge files
        cls.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(cls.temp_dir, "knowledge/rules"), exist_ok=True)
        os.makedirs(os.path.join(cls.temp_dir, "knowledge/lore"), exist_ok=True)
        
        # Create minimal test data
        test_spells = {
            "fireball": {
                "name": "Fireball",
                "level": 3,
                "damage": "8d6 fire",
                "range": "150 feet"
            }
        }
        
        test_monsters = {
            "goblin": {
                "name": "Goblin", 
                "armor_class": 15,
                "hit_points": 7,
                "challenge": 0.25
            }
        }
        
        # Write test files
        with open(os.path.join(cls.temp_dir, "knowledge/spells.json"), 'w') as f:
            json.dump(test_spells, f)
        with open(os.path.join(cls.temp_dir, "knowledge/monsters.json"), 'w') as f:
            json.dump(test_monsters, f)
            
        # Change to temp directory and create service
        cls.original_dir = os.getcwd()
        os.chdir(cls.temp_dir)
        
        cls.rag_service = RAGServiceImpl()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up class-level fixtures."""
        os.chdir(cls.original_dir)
        import shutil
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up test-specific state."""
        # Use the shared rag_service instance
        self.rag_service = self.__class__.rag_service
    
    def test_get_relevant_knowledge(self):
        """Test getting relevant knowledge for an action."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = None
        mock_game_state.event_summary = []
        
        results = self.rag_service.get_relevant_knowledge("I cast fireball", mock_game_state)
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, RAGResults)
        self.assertIsInstance(results.execution_time_ms, (int, float))
        # May or may not have results depending on embeddings initialization
    
    def test_analyze_action(self):
        """Test action analysis."""
        mock_game_state = Mock()
        mock_game_state.event_summary = []  # Add this to prevent subscriptable error
        queries = self.rag_service.analyze_action("I cast fireball", mock_game_state)
        
        self.assertIsInstance(queries, list)
        # Should generate at least one query for spell casting
        self.assertGreater(len(queries), 0)
        
        # Should have a spell casting query
        spell_query = next((q for q in queries if q.query_type == QueryType.SPELL_CASTING), None)
        self.assertIsNotNone(spell_query)
    
    def test_configuration(self):
        """Test RAG service configuration."""
        self.assertIsNotNone(self.rag_service.query_engine)
        self.assertIsNotNone(self.rag_service.kb_manager)
    
    
    def test_empty_action_handling(self):
        """Test handling of empty actions."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = None
        mock_game_state.event_summary = []
        
        results = self.rag_service.get_relevant_knowledge("", mock_game_state)
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, RAGResults)
        # Should handle gracefully even with empty input


class TestRAGServiceEndToEnd(unittest.TestCase):
    """Test end-to-end scenarios for RAG service."""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        # Create temporary directory
        cls.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(cls.temp_dir, "knowledge"), exist_ok=True)
        
        # Create more comprehensive test data
        cls.test_spells = {
            "fireball": {
                "name": "Fireball",
                "level": 3,
                "damage": "8d6 fire damage",
                "range": "150 feet",
                "area": "20-foot radius sphere",
                "description": "Explosive fire damage"
            }
        }
        
        cls.test_monsters = {
            "goblin": {
                "name": "Goblin",
                "armor_class": 15,
                "hit_points": 7,
                "challenge": 0.25
            }
        }
        
        # Write knowledge files
        with open(os.path.join(cls.temp_dir, "knowledge/spells.json"), 'w') as f:
            json.dump(cls.test_spells, f)
        with open(os.path.join(cls.temp_dir, "knowledge/monsters.json"), 'w') as f:
            json.dump(cls.test_monsters, f)
        
        # Change to temp directory and create service
        cls.original_dir = os.getcwd()
        os.chdir(cls.temp_dir)
        
        cls.rag_service = RAGServiceImpl()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up class-level fixtures."""
        os.chdir(cls.original_dir)
        import shutil
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up test-specific state."""
        # Use the shared rag_service instance
        self.rag_service = self.__class__.rag_service
    


if __name__ == '__main__':
    unittest.main()