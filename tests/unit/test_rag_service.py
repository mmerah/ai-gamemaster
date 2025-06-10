"""
Unit tests for the RAG service implementation.
Tests the RAG service with mocked dependencies.
"""

import os
import unittest
from typing import Any, ClassVar, Dict
from unittest.mock import Mock

# Skip entire module if RAG is disabled
import pytest

if os.environ.get("RAG_ENABLED", "true").lower() == "false":
    pytest.skip("RAG is disabled", allow_module_level=True)

import json
import shutil
import tempfile

from app.core.rag_interfaces import KnowledgeResult, QueryType, RAGResults
from app.services.rag.rag_service import RAGServiceImpl


class TestRAGResults(unittest.TestCase):
    """Test RAGResults formatting methods."""

    def test_format_for_prompt_with_results(self) -> None:
        """Test formatting results for prompt inclusion."""
        results = RAGResults(
            results=[
                KnowledgeResult(
                    content="Fireball: 8d6 fire damage in 20ft radius",
                    source="spells",
                    relevance_score=0.9,
                ),
                KnowledgeResult(
                    content="Fire damage ignites flammable objects",
                    source="rules",
                    relevance_score=0.7,
                ),
                KnowledgeResult(
                    content="Goblin: Small humanoid, 7 HP",
                    source="monsters",
                    relevance_score=0.8,
                ),
            ]
        )

        formatted = results.format_for_prompt()

        # Should have RELEVANT KNOWLEDGE prefix
        self.assertTrue(formatted.startswith("RELEVANT KNOWLEDGE:"))

        # Should group by source
        self.assertIn("spells:", formatted)
        self.assertIn("rules:", formatted)
        self.assertIn("monsters:", formatted)

        # Should include content
        self.assertIn("Fireball: 8d6 fire damage", formatted)
        self.assertIn("Fire damage ignites", formatted)
        self.assertIn("Goblin: Small humanoid", formatted)

    def test_format_for_prompt_empty(self) -> None:
        """Test formatting with no results."""
        results = RAGResults()
        formatted = results.format_for_prompt()
        self.assertEqual(formatted, "")

    def test_debug_format(self) -> None:
        """Test debug formatting."""
        results = RAGResults(
            results=[
                KnowledgeResult(
                    content="Fireball: 8d6 fire damage in 20ft radius",
                    source="spells",
                    relevance_score=0.9,
                ),
            ],
            execution_time_ms=150.5,
        )

        debug = results.debug_format()
        self.assertIn("RAG Retrieved 1 results in 150.5ms", debug)
        self.assertIn("[spells] Fireball", debug)


class TestRAGService(unittest.TestCase):
    """Test the main RAG service implementation."""

    # Class variables with proper type annotations
    temp_dir: ClassVar[str]
    original_dir: ClassVar[str]
    rag_service: ClassVar[RAGServiceImpl]

    @classmethod
    def setUpClass(cls) -> None:
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
                "range": "150 feet",
            }
        }

        test_monsters = {
            "goblin": {
                "name": "Goblin",
                "armor_class": 15,
                "hit_points": 7,
                "challenge": 0.25,
            }
        }

        # Write test files
        with open(os.path.join(cls.temp_dir, "knowledge/spells.json"), "w") as f:
            json.dump(test_spells, f)
        with open(os.path.join(cls.temp_dir, "knowledge/monsters.json"), "w") as f:
            json.dump(test_monsters, f)

        # Change to temp directory and create service
        cls.original_dir = os.getcwd()
        os.chdir(cls.temp_dir)

        cls.rag_service = RAGServiceImpl()

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up class-level fixtures."""
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir)

    def setUp(self) -> None:
        """Set up test-specific state."""
        # rag_service is accessed directly from the class
        pass

    def test_get_relevant_knowledge(self) -> None:
        """Test getting relevant knowledge for an action."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = None
        mock_game_state.event_summary = []

        results = self.__class__.rag_service.get_relevant_knowledge(
            "I cast fireball", mock_game_state
        )

        self.assertIsNotNone(results)
        self.assertIsInstance(results, RAGResults)
        self.assertIsInstance(results.execution_time_ms, (int, float))
        # May or may not have results depending on embeddings initialization

    def test_analyze_action(self) -> None:
        """Test action analysis."""
        mock_game_state = Mock()
        mock_game_state.event_summary = []  # Add this to prevent subscriptable error
        queries = self.__class__.rag_service.analyze_action(
            "I cast fireball", mock_game_state
        )

        self.assertIsInstance(queries, list)
        # Should generate at least one query for spell casting
        self.assertGreater(len(queries), 0)

        # Should have a spell casting query
        spell_query = next(
            (q for q in queries if q.query_type == QueryType.SPELL_CASTING), None
        )
        self.assertIsNotNone(spell_query)

    def test_configuration(self) -> None:
        """Test RAG service configuration."""
        self.assertIsNotNone(self.__class__.rag_service.query_engine)
        self.assertIsNotNone(self.__class__.rag_service.kb_manager)

    def test_empty_action_handling(self) -> None:
        """Test handling of empty actions."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = None
        mock_game_state.event_summary = []

        results = self.__class__.rag_service.get_relevant_knowledge("", mock_game_state)

        self.assertIsNotNone(results)
        self.assertIsInstance(results, RAGResults)
        # Should handle gracefully even with empty input


class TestRAGServiceEndToEnd(unittest.TestCase):
    """Test end-to-end scenarios for RAG service."""

    # Class variables with proper type annotations
    temp_dir: ClassVar[str]
    original_dir: ClassVar[str]
    rag_service: ClassVar[RAGServiceImpl]
    test_spells: ClassVar[Dict[str, Dict[str, Any]]]
    test_monsters: ClassVar[Dict[str, Dict[str, Any]]]

    @classmethod
    def setUpClass(cls) -> None:
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
                "description": "Explosive fire damage",
            }
        }

        cls.test_monsters = {
            "goblin": {
                "name": "Goblin",
                "armor_class": 15,
                "hit_points": 7,
                "challenge": 0.25,
            }
        }

        # Write knowledge files
        with open(os.path.join(cls.temp_dir, "knowledge/spells.json"), "w") as f:
            json.dump(cls.test_spells, f)
        with open(os.path.join(cls.temp_dir, "knowledge/monsters.json"), "w") as f:
            json.dump(cls.test_monsters, f)

        # Change to temp directory and create service
        cls.original_dir = os.getcwd()
        os.chdir(cls.temp_dir)

        cls.rag_service = RAGServiceImpl()

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up class-level fixtures."""
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir)

    def setUp(self) -> None:
        """Set up test-specific state."""
        # rag_service is accessed directly from the class
        pass


if __name__ == "__main__":
    unittest.main()
