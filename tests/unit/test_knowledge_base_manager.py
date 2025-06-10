"""
Unit tests for the knowledge base manager.
Tests the LangChain-based knowledge base manager.
"""

import json
import os
import tempfile
import unittest
from typing import Any, ClassVar, Dict

# Skip entire module if RAG is disabled
import pytest

if os.environ.get("RAG_ENABLED", "true").lower() == "false":
    pytest.skip("RAG is disabled", allow_module_level=True)

from app.services.rag.knowledge_bases import KnowledgeBaseManager


class TestKnowledgeBaseManager(unittest.TestCase):
    """Test the LangChain-based knowledge base manager."""

    temp_dir: ClassVar[str]
    test_spells: ClassVar[Dict[str, Dict[str, Any]]]
    test_monsters: ClassVar[Dict[str, Dict[str, Any]]]
    original_dir: ClassVar[str]
    _kb_manager: ClassVar[KnowledgeBaseManager]
    kb_manager: KnowledgeBaseManager  # Instance variable

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level fixtures to avoid reinitializing embeddings."""
        # Create temporary directories for knowledge files
        cls.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(cls.temp_dir, "knowledge/rules"), exist_ok=True)
        os.makedirs(os.path.join(cls.temp_dir, "knowledge/lore"), exist_ok=True)

        # Create test data files
        cls.test_spells = {
            "fireball": {
                "name": "Fireball",
                "level": 3,
                "damage": "8d6",
                "range": "150 feet",
                "description": "A bright streak flashes from your pointing finger to a point you choose within range",
            },
            "healing_word": {
                "name": "Healing Word",
                "level": 1,
                "healing": "1d4 + spellcasting ability modifier",
                "range": "60 feet",
                "description": "A creature of your choice that you can see within range regains hit points",
            },
        }

        cls.test_monsters = {
            "goblin": {
                "name": "Goblin",
                "armor_class": 15,
                "hit_points": 7,
                "challenge": 0.25,
                "abilities": ["nimble escape", "scimitar attack"],
            },
            "orc": {
                "name": "Orc",
                "armor_class": 13,
                "hit_points": 15,
                "challenge": 0.5,
                "abilities": ["aggressive", "greataxe attack"],
            },
        }

        # Write test files
        spells_path = os.path.join(cls.temp_dir, "knowledge/spells.json")
        with open(spells_path, "w") as f:
            json.dump(cls.test_spells, f)

        monsters_path = os.path.join(cls.temp_dir, "knowledge/monsters.json")
        with open(monsters_path, "w") as f:
            json.dump(cls.test_monsters, f)

        # Mock the knowledge file paths
        cls.original_dir = os.getcwd()
        os.chdir(cls.temp_dir)

        # Initialize knowledge base manager ONCE for all tests
        cls._kb_manager = KnowledgeBaseManager()

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up class-level fixtures."""
        os.chdir(cls.original_dir)
        import shutil

        shutil.rmtree(cls.temp_dir)

    def setUp(self) -> None:
        """Set up test-specific state."""
        # Use the shared kb_manager instance
        self.kb_manager = self.__class__._kb_manager

    def test_knowledge_base_initialization(self) -> None:
        """Test that knowledge bases are initialized properly."""
        # Should have vector stores for different knowledge types
        self.assertIn("spells", self.kb_manager.vector_stores)
        self.assertIn("monsters", self.kb_manager.vector_stores)

    def test_semantic_search(self) -> None:
        """Test semantic search functionality."""
        results = self.kb_manager.search("fireball spell damage", kb_types=["spells"])

        self.assertTrue(results.results, "Should find fireball results")
        self.assertGreater(results.total_queries, 0)

        # Check that fireball is in the results
        fireball_found = any("fireball" in r.content.lower() for r in results.results)
        self.assertTrue(fireball_found, "Fireball should be found in results")

    def test_cross_knowledge_base_search(self) -> None:
        """Test searching across multiple knowledge bases."""
        results = self.kb_manager.search(
            "goblin attack", kb_types=["monsters", "spells"]
        )

        self.assertTrue(results.results, "Should find results")

        # Should find goblin monster info
        goblin_found = any("goblin" in r.content.lower() for r in results.results)
        self.assertTrue(goblin_found, "Should find goblin in results")

    def test_relevance_scoring(self) -> None:
        """Test that relevance scoring works with vector search."""
        results = self.kb_manager.search("fireball", kb_types=["spells"])

        self.assertTrue(results.results, "Should find results")

        # Results should be sorted by relevance (highest first)
        for i in range(len(results.results) - 1):
            self.assertGreaterEqual(
                results.results[i].relevance_score,
                results.results[i + 1].relevance_score,
                "Results should be sorted by relevance score",
            )

    def test_score_threshold(self) -> None:
        """Test that score threshold filters out low-relevance results."""
        # Search for something unrelated
        results = self.kb_manager.search(
            "completely unrelated xyz", kb_types=["spells"], score_threshold=0.5
        )

        # Should either have no results or only high-relevance results
        for result in results.results:
            self.assertGreaterEqual(
                result.relevance_score,
                0.5,
                "Results below threshold should be filtered out",
            )

    def test_add_campaign_lore(self) -> None:
        """Test adding campaign-specific lore."""
        from app.models.models import LoreDataModel

        campaign_id = "test_campaign"
        lore_data = LoreDataModel(
            id="test_lore",
            name="Test Campaign Lore",
            description="Lore for the test campaign",
            content="ancient_artifact: Staff of Power - A legendary staff wielded by ancient wizards",
            tags=["artifact", "magic"],
            category="campaign",
        )

        self.kb_manager.add_campaign_lore(campaign_id, lore_data)

        # Should be able to search campaign lore
        kb_type = f"lore_{campaign_id}"
        self.assertIn(kb_type, self.kb_manager.vector_stores)

        results = self.kb_manager.search("staff power", kb_types=[kb_type])
        self.assertTrue(results.results, "Should find campaign lore")

    def test_add_event(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
