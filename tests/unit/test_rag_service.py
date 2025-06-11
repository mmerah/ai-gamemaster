"""
Unit tests for the RAG service implementation.
Tests the RAG service interface and result formatting.
"""

import os
import unittest
from typing import ClassVar
from unittest.mock import Mock, patch

# Skip entire module if RAG is disabled
import pytest

if os.environ.get("RAG_ENABLED", "true").lower() == "false":
    pytest.skip("RAG is disabled", allow_module_level=True)

from app.core.rag_interfaces import KnowledgeResult, QueryType, RAGResults
from app.models import GameStateModel
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
        self.assertIn("Fireball", formatted)
        self.assertIn("Fire damage", formatted)
        self.assertIn("Goblin", formatted)

    def test_format_for_prompt_empty(self) -> None:
        """Test formatting with no results."""
        results = RAGResults(results=[])
        formatted = results.format_for_prompt()
        self.assertEqual(formatted, "")

    def test_has_results(self) -> None:
        """Test has_results property."""
        # With results
        results = RAGResults(
            results=[
                KnowledgeResult(content="test", source="test", relevance_score=0.5)
            ]
        )
        self.assertTrue(results.has_results())

        # Without results
        empty_results = RAGResults(results=[])
        self.assertFalse(empty_results.has_results())

    def test_debug_format(self) -> None:
        """Test debug formatting."""
        results = RAGResults(
            results=[
                KnowledgeResult(
                    content="Fireball spell description",
                    source="spells",
                    relevance_score=0.9,
                )
            ],
            total_queries=1,
            execution_time_ms=150.5,
        )

        debug = results.debug_format()
        self.assertIn("RAG Retrieved 1 results in 150.5ms", debug)
        self.assertIn("[spells] Fireball", debug)


class TestRAGService(unittest.TestCase):
    """Test the main RAG service interface."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a RAG service with mocked dependencies
        self.mock_kb_manager = Mock()
        self.mock_query_engine = Mock()

        # Create RAG service
        self.rag_service = RAGServiceImpl()
        self.rag_service.kb_manager = self.mock_kb_manager
        self.rag_service.query_engine = self.mock_query_engine

    def test_get_relevant_knowledge_no_queries(self) -> None:
        """Test when no queries are generated."""
        # Mock query engine to return no queries
        self.mock_query_engine.analyze_action.return_value = []

        game_state = GameStateModel()
        results = self.rag_service.get_relevant_knowledge("test action", game_state)

        self.assertIsNotNone(results)
        self.assertEqual(len(results.results), 0)
        self.assertEqual(results.total_queries, 0)

    def test_get_relevant_knowledge_with_results(self) -> None:
        """Test when queries return results."""
        from app.core.rag_interfaces import RAGQuery

        # Mock query generation
        mock_queries = [
            RAGQuery(
                query_text="fireball spell",
                query_type=QueryType.SPELL_CASTING,
                knowledge_base_types=["spells"],
            )
        ]
        self.mock_query_engine.analyze_action.return_value = mock_queries

        # Mock knowledge base search
        mock_kb_results = RAGResults(
            results=[
                KnowledgeResult(
                    content="Fireball: 8d6 fire damage",
                    source="spells",
                    relevance_score=0.9,
                )
            ],
            total_queries=1,
        )
        self.mock_kb_manager.search.return_value = mock_kb_results

        game_state = GameStateModel()
        results = self.rag_service.get_relevant_knowledge("cast fireball", game_state)

        self.assertEqual(len(results.results), 1)
        self.assertEqual(results.total_queries, 1)
        self.assertIn("Fireball", results.results[0].content)

    def test_configure_filtering(self) -> None:
        """Test configuration of filtering parameters."""
        self.rag_service.configure_filtering(
            max_results=10,
            score_threshold=0.5,
        )

        # Verify the RAG service parameters were updated
        self.assertEqual(self.rag_service.max_total_results, 10)
        self.assertEqual(self.rag_service.score_threshold, 0.5)

    def test_ensure_campaign_knowledge(self) -> None:
        """Test campaign knowledge loading."""
        game_state = GameStateModel(
            campaign_id="test_campaign",
            active_lore_id="test_lore",
        )

        # Mock lore loading
        with patch("app.services.rag.rag_service.load_lore_info") as mock_load_lore:
            from app.models import LoreDataModel

            mock_lore = LoreDataModel(
                id="test_lore",
                name="Test Lore",
                description="Test description",
                content="Test lore content data",
                tags=["test"],
                category="test",
            )
            mock_load_lore.return_value = mock_lore

            # Call the method indirectly through get_relevant_knowledge
            self.mock_query_engine.analyze_action.return_value = []
            self.rag_service.get_relevant_knowledge("test", game_state)

            # Verify campaign lore was added
            self.mock_kb_manager.add_campaign_lore.assert_called_once_with(
                "test_campaign", mock_lore
            )

    def test_add_event(self) -> None:
        """Test adding an event to campaign history."""
        from app.models import EventMetadataModel

        campaign_id = "test_campaign"
        event_summary = "The party defeated a dragon"
        keywords = ["dragon", "victory"]
        from datetime import datetime, timezone

        metadata = EventMetadataModel(
            timestamp=datetime.now(timezone.utc).isoformat(),
            location="Dragon's Lair",
            participants=["party"],
            combat_active=True,
        )

        self.rag_service.add_event(campaign_id, event_summary, keywords, metadata)

        # Verify event was added to knowledge base
        self.mock_kb_manager.add_event.assert_called_once()
        call_args = self.mock_kb_manager.add_event.call_args
        self.assertEqual(call_args[0][0], campaign_id)
        self.assertIn("defeated a dragon", call_args[0][1])


if __name__ == "__main__":
    unittest.main()
