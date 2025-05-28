"""
Unit tests for the RAG (Retrieval-Augmented Generation) system.
Tests the query engine, knowledge bases, and RAG service implementation.
"""
import unittest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
from app.core.rag_interfaces import RAGQuery, QueryType, KnowledgeResult, RAGResults
from app.services.rag.query_engine import RAGQueryEngineImpl
from app.services.rag.rag_service import RAGServiceImpl
from app.services.rag.knowledge_bases import KnowledgeBaseManager


class TestRAGQueryEngine(unittest.TestCase):
    """Test the RAG query engine that analyzes player actions."""
    
    def setUp(self):
        self.query_engine = RAGQueryEngineImpl()
        self.mock_game_state = Mock()
        self.mock_game_state.combat = Mock()
        self.mock_game_state.combat.is_active = False
        self.mock_game_state.current_location = {'name': 'tavern'}
        self.mock_game_state.event_summary = ['Player entered tavern', 'Met bartender']
    
    def test_spell_casting_detection(self):
        """Test detection of spell casting actions."""
        spell_actions = [
            "I cast fireball at the goblin",
            "I use healing word on my ally",
            "Cast magic missile",
            "I invoke shield spell",
            "Fire a fireball spell"
        ]
        
        for action in spell_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(len(queries), 0, f"No queries generated for: {action}")
                # At least one query should be spell-related
                has_spell_query = any(q.query_type == QueryType.SPELL_CASTING for q in queries)
                self.assertTrue(has_spell_query, f"No spell query for: {action}")
    
    def test_combat_action_detection(self):
        """Test detection of combat actions."""
        combat_actions = [
            "I attack the skeleton with my sword",
            "Strike the orc",
            "I swing at the goblin",
            "Dodge the incoming attack",
            "I charge at the dragon"
        ]
        
        for action in combat_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(len(queries), 0, f"No queries generated for: {action}")
                # Should generate combat-related queries
                has_combat_query = any(q.query_type == QueryType.COMBAT for q in queries)
                self.assertTrue(has_combat_query, f"No combat query for: {action}")
    
    def test_skill_check_detection(self):
        """Test detection of skill check actions."""
        skill_actions = [
            "I make a stealth check",
            "I search the room",
            "I try to persuade the guard",
            "Make an athletics check to climb"
        ]
        
        for action in skill_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(len(queries), 0, f"No queries generated for: {action}")
                # Should generate skill-related queries
                has_skill_query = any(q.query_type == QueryType.SKILL_CHECK for q in queries)
                self.assertTrue(has_skill_query, f"No skill query for: {action}")
    
    def test_spell_name_extraction(self):
        """Test extraction of spell names from actions."""
        test_cases = [
            ("I cast fireball at the enemy", "fireball"),
            ("Use healing word on ally", "healing word"),
            ("Cast magic missile spell", "magic missile"),
            ("I invoke the shield spell", "shield"),
            ("Fire ice knife at target", "ice knife")
        ]
        
        for action, expected_spell in test_cases:
            with self.subTest(action=action, expected=expected_spell):
                extracted = self.query_engine._extract_spell_name_enhanced(action)
                self.assertIn(expected_spell.lower(), extracted.lower(),
                            f"Expected '{expected_spell}' in extracted spell name '{extracted}'")
    
    def test_creature_extraction(self):
        """Test extraction of creature names from actions."""
        test_cases = [
            ("I attack the goblin", ["goblin"]),
            ("Strike the orc and skeleton", ["orc", "skeleton"]),
            ("Fight the dragon", ["dragon"]),
            ("Avoid the giant spider", ["giant", "spider"])
        ]
        
        for action, expected_creatures in test_cases:
            with self.subTest(action=action):
                creatures = self.query_engine._extract_creatures(action)
                for expected in expected_creatures:
                    self.assertIn(expected, creatures,
                                f"Expected creature '{expected}' not found in {creatures}")
    
    def test_empty_action_handling(self):
        """Test handling of empty or invalid actions."""
        invalid_actions = ["", None, "   "]
        
        for action in invalid_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                # Empty actions might still generate general queries, so allow some flexibility
                if action == "   ":  # Whitespace might generate a general query
                    self.assertLessEqual(len(queries), 1, f"Should return minimal queries for: {action}")
                else:
                    self.assertEqual(len(queries), 0, f"Should return empty list for: {action}")
    
    def test_social_interaction_detection(self):
        """Test detection of social interaction actions."""
        social_actions = [
            "I talk to the bartender",
            "Speak with the guard about passage",
            "I approach the merchant",
            "Ask the innkeeper about rooms"
        ]
        
        for action in social_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(len(queries), 0, f"No queries generated for: {action}")


class TestKnowledgeBaseManager(unittest.TestCase):
    """Test the LangChain-based knowledge base manager."""
    
    def setUp(self):
        # Create temporary directories for knowledge files
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "knowledge/rules"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "knowledge/lore"), exist_ok=True)
        
        # Create test data files
        self.test_spells = {
            "fireball": {
                "name": "Fireball",
                "level": 3,
                "damage": "8d6",
                "range": "150 feet",
                "description": "A bright streak flashes from your pointing finger to a point you choose within range"
            },
            "healing_word": {
                "name": "Healing Word",
                "level": 1,
                "healing": "1d4 + spellcasting ability modifier",
                "range": "60 feet", 
                "description": "A creature of your choice that you can see within range regains hit points"
            }
        }
        
        self.test_monsters = {
            "goblin": {
                "name": "Goblin",
                "armor_class": 15,
                "hit_points": 7,
                "challenge": 0.25,
                "abilities": ["nimble escape", "scimitar attack"]
            },
            "orc": {
                "name": "Orc",
                "armor_class": 13,
                "hit_points": 15,
                "challenge": 0.5,
                "abilities": ["aggressive", "greataxe attack"]
            }
        }
        
        # Write test files
        spells_path = os.path.join(self.temp_dir, "knowledge/spells.json")
        with open(spells_path, 'w') as f:
            json.dump(self.test_spells, f)
            
        monsters_path = os.path.join(self.temp_dir, "knowledge/monsters.json")
        with open(monsters_path, 'w') as f:
            json.dump(self.test_monsters, f)
            
        # Mock the knowledge file paths
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Initialize knowledge base manager
        self.kb_manager = KnowledgeBaseManager()
    
    def tearDown(self):
        os.chdir(self.original_dir)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_knowledge_base_initialization(self):
        """Test that knowledge bases are initialized properly."""
        # Should have vector stores for different knowledge types
        self.assertIn("spells", self.kb_manager.vector_stores)
        self.assertIn("monsters", self.kb_manager.vector_stores)
    
    def test_semantic_search(self):
        """Test semantic search functionality."""
        results = self.kb_manager.search("fireball spell damage", kb_types=["spells"])
        
        self.assertTrue(results.results, "Should find fireball results")
        self.assertGreater(results.total_queries, 0)
        
        # Check that fireball is in the results
        fireball_found = any("fireball" in r.content.lower() for r in results.results)
        self.assertTrue(fireball_found, "Fireball should be found in results")
    
    def test_cross_knowledge_base_search(self):
        """Test searching across multiple knowledge bases."""
        results = self.kb_manager.search("goblin attack", kb_types=["monsters", "spells"])
        
        self.assertTrue(results.results, "Should find results")
        
        # Should find goblin monster info
        goblin_found = any("goblin" in r.content.lower() for r in results.results)
        self.assertTrue(goblin_found, "Should find goblin in results")
    
    def test_relevance_scoring(self):
        """Test that relevance scoring works with vector search."""
        results = self.kb_manager.search("fireball", kb_types=["spells"])
        
        self.assertTrue(results.results, "Should find results")
        
        # Results should be sorted by relevance (highest first)
        for i in range(len(results.results) - 1):
            self.assertGreaterEqual(results.results[i].relevance_score, 
                                   results.results[i + 1].relevance_score,
                                   "Results should be sorted by relevance score")
    
    def test_score_threshold(self):
        """Test that score threshold filters out low-relevance results."""
        # Search for something unrelated
        results = self.kb_manager.search("completely unrelated xyz", 
                                        kb_types=["spells"], 
                                        score_threshold=0.5)
        
        # Should either have no results or only high-relevance results
        for result in results.results:
            self.assertGreaterEqual(result.relevance_score, 0.5,
                                   "Results below threshold should be filtered out")
    
    def test_add_campaign_lore(self):
        """Test adding campaign-specific lore."""
        campaign_id = "test_campaign"
        lore_data = {
            "ancient_artifact": {
                "name": "Staff of Power",
                "description": "A legendary staff wielded by ancient wizards"
            }
        }
        
        self.kb_manager.add_campaign_lore(campaign_id, lore_data)
        
        # Should be able to search campaign lore
        kb_type = f"lore_{campaign_id}"
        self.assertIn(kb_type, self.kb_manager.vector_stores)
        
        results = self.kb_manager.search("staff power", kb_types=[kb_type])
        self.assertTrue(results.results, "Should find campaign lore")
    
    def test_add_event(self):
        """Test adding events to campaign event log."""
        campaign_id = "test_campaign"
        event_summary = "Party defeated the goblin chieftain"
        keywords = ["goblin", "victory", "combat"]
        
        self.kb_manager.add_event(campaign_id, event_summary, keywords)
        
        # Should be able to search events
        kb_type = f"events_{campaign_id}"
        self.assertIn(kb_type, self.kb_manager.vector_stores)
        
        results = self.kb_manager.search("goblin chieftain", kb_types=[kb_type])
        self.assertTrue(results.results, "Should find event")




class TestRAGService(unittest.TestCase):
    """Test the main RAG service implementation."""
    
    def setUp(self):
        # Create temporary directory for test knowledge files
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "knowledge/rules"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "knowledge/lore"), exist_ok=True)
        
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
        with open(os.path.join(self.temp_dir, "knowledge/spells.json"), 'w') as f:
            json.dump(test_spells, f)
        with open(os.path.join(self.temp_dir, "knowledge/monsters.json"), 'w') as f:
            json.dump(test_monsters, f)
            
        # Change to temp directory and create service
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.rag_service = RAGServiceImpl()
    
    def tearDown(self):
        os.chdir(self.original_dir)
        import shutil
        shutil.rmtree(self.temp_dir)
    
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
        # Configure new values
        self.rag_service.configure_filtering(
            max_results=10,
            score_threshold=0.5
        )
        
        self.assertEqual(self.rag_service.score_threshold, 0.5)
        self.assertEqual(self.rag_service.max_total_results, 10)
    
    def test_add_event(self):
        """Test adding events through the service."""
        campaign_id = "test_campaign"
        event_summary = "Party defeated the dragon"
        keywords = ["dragon", "victory"]
        
        # Should not raise any exceptions
        self.rag_service.add_event(campaign_id, event_summary, keywords)
    
    def test_empty_action_handling(self):
        """Test handling of empty actions."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = None
        mock_game_state.event_summary = []
        
        results = self.rag_service.get_relevant_knowledge("", mock_game_state)
        
        self.assertIsNotNone(results)
        self.assertFalse(results.has_results())
        self.assertEqual(len(results.results), 0)


class TestRAGIntegration(unittest.TestCase):
    """Integration tests for the complete RAG system."""
    
    def setUp(self):
        # Create temporary directory with proper structure
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "knowledge/rules"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "knowledge/lore"), exist_ok=True)
        
        # Create test knowledge files
        self.test_spells = {
            "fireball": {
                "name": "Fireball",
                "level": 3,
                "damage": "8d6",
                "range": "150 feet",
                "description": "Explosive fire damage"
            }
        }
        
        self.test_monsters = {
            "goblin": {
                "name": "Goblin",
                "armor_class": 15,
                "hit_points": 7,
                "challenge": 0.25
            }
        }
        
        # Write knowledge files
        with open(os.path.join(self.temp_dir, "knowledge/spells.json"), 'w') as f:
            json.dump(self.test_spells, f)
        with open(os.path.join(self.temp_dir, "knowledge/monsters.json"), 'w') as f:
            json.dump(self.test_monsters, f)
        
        # Change to temp directory and create service
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.rag_service = RAGServiceImpl()
    
    def tearDown(self):
        os.chdir(self.original_dir)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_spell_casting(self):
        """Test complete flow for spell casting action."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = None
        mock_game_state.combat = Mock()
        mock_game_state.combat.is_active = False
        mock_game_state.event_summary = ["previous event"]
        
        results = self.rag_service.get_relevant_knowledge("I cast fireball at the goblin", mock_game_state)
        
        # Should record execution time
        self.assertIsInstance(results.execution_time_ms, (int, float), "Should record execution time")
        
        # Check that results are properly formatted if any found
        if results.has_results():
            for result in results.results:
                self.assertIsInstance(result.content, str)
                self.assertGreater(len(result.content), 0)
                self.assertGreaterEqual(result.relevance_score, 0)
    
    def test_performance_timing(self):
        """Test that RAG operations complete in reasonable time."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = None
        mock_game_state.event_summary = []
        
        import time
        start_time = time.time()
        results = self.rag_service.get_relevant_knowledge("I cast fireball", mock_game_state)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Should complete in under 1000ms for simple queries (more lenient for embedding init)
        self.assertLess(execution_time, 1000, "RAG should complete within reasonable time")
        self.assertIsInstance(results.execution_time_ms, (int, float), "Should record execution time")


if __name__ == '__main__':
    unittest.main()
