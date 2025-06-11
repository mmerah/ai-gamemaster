"""
Unit tests for the knowledge base manager.
Tests the LangChain-based knowledge base manager with lore data.
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

from app.models import LoreDataModel
from app.services.rag.knowledge_bases import KnowledgeBaseManager


class TestKnowledgeBaseManager(unittest.TestCase):
    """Test the LangChain-based knowledge base manager."""

    temp_dir: ClassVar[str]
    test_lore: ClassVar[Dict[str, Any]]
    original_dir: ClassVar[str]
    _kb_manager: ClassVar[KnowledgeBaseManager]
    kb_manager: KnowledgeBaseManager  # Instance variable

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level fixtures to avoid reinitializing embeddings."""
        # Create temporary directories for knowledge files
        cls.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(cls.temp_dir, "knowledge/lore"), exist_ok=True)

        # Create test lore data
        cls.test_lore = {
            "world_setting": {
                "name": "Sword Coast",
                "description": "A dangerous frontier along the western coast",
                "notable_locations": ["Waterdeep", "Baldur's Gate", "Neverwinter"],
            },
            "factions": {
                "harpers": {
                    "name": "The Harpers",
                    "description": "A secret organization dedicated to promoting good",
                    "goals": ["Preserve history", "Maintain balance"],
                }
            },
        }

        # Write test lore file
        lore_path = os.path.join(
            cls.temp_dir, "knowledge/lore/generic_fantasy_lore.json"
        )
        with open(lore_path, "w") as f:
            json.dump(cls.test_lore, f)

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
        # Should have vector store for lore
        self.assertIn("lore", self.kb_manager.vector_stores)

    def test_semantic_search(self) -> None:
        """Test semantic search functionality."""
        # Search for faction information
        results = self.kb_manager.search("Sword Coast frontier", ["lore"])

        self.assertIsNotNone(results)

        # The search should find something
        self.assertTrue(len(results.results) > 0, "No search results found")

        # Check if any results contain Sword Coast information
        sword_coast_found = any(
            "sword coast" in result.content.lower() for result in results.results
        )
        self.assertTrue(
            sword_coast_found, "Sword Coast information not found in results"
        )

    def test_campaign_lore_addition(self) -> None:
        """Test adding campaign-specific lore."""
        campaign_id = "test_campaign_001"
        lore_data = LoreDataModel(
            id="campaign_lore_1",
            name="Dragon Cult",
            description="A cult worshipping ancient dragons",
            content="Beliefs: Dragons should rule the world\nLeader: Severin Silrajin\nStrongholds: Well of Dragons, Skyreach Castle",
            tags=["faction", "antagonist"],
            category="faction",
        )

        # Add campaign lore
        self.kb_manager.add_campaign_lore(campaign_id, lore_data)

        # Verify it was added
        kb_type = f"lore_{campaign_id}"
        self.assertIn(kb_type, self.kb_manager.vector_stores)

        # Search for it
        results = self.kb_manager.search("dragon cult leader", [kb_type])
        self.assertTrue(len(results.results) > 0)

    def test_search_filtering(self) -> None:
        """Test that search filtering works correctly."""
        # Search with custom parameters
        results = self.kb_manager.search(
            "fantasy world",
            ["lore"],
            k=2,  # Limit to 2 results
            score_threshold=0.3,
        )
        self.assertLessEqual(len(results.results), 2)

    def test_add_documents_to_knowledge_base(self) -> None:
        """Test adding documents to an existing knowledge base."""
        from langchain_core.documents import Document

        # Create a new document
        new_doc = Document(
            page_content="The Lost Mine of Phandelver is located near Phandalin",
            metadata={"source": "adventure", "type": "location"},
        )

        # Add to lore knowledge base
        kb_type = "lore"
        vector_store = self.kb_manager.vector_stores.get(kb_type)
        self.assertIsNotNone(vector_store)

        # Add the document
        if vector_store is not None:
            vector_store.add_documents([new_doc])

        # Search for it
        results = self.kb_manager.search("Phandelver mine", [kb_type])
        self.assertTrue(len(results.results) > 0)

        # Verify the content was found
        phandelver_found = any(
            "phandelver" in result.content.lower() for result in results.results
        )
        self.assertTrue(phandelver_found)


if __name__ == "__main__":
    unittest.main()
