"""Tests for RAG service content pack priority functionality."""

from typing import List, Optional
from unittest.mock import Mock, patch

import numpy as np
import pytest

from app.content.rag.db_knowledge_base_manager import DbKnowledgeBaseManager
from app.content.rag.rag_service import RAGService
from app.models.game_state.main import GameStateModel
from app.models.rag import KnowledgeResult, QueryType, RAGQuery, RAGResults


class TestRAGContentPackPriority:
    """Test that RAG service respects content pack priority."""

    @pytest.fixture
    def mock_kb_manager(self) -> Mock:
        """Create a mock knowledge base manager."""
        return Mock(spec=DbKnowledgeBaseManager)

    @pytest.fixture
    def rag_service(self, mock_kb_manager: Mock) -> RAGService:
        """Create RAG service with mocked dependencies."""
        from app.content.rag.query_engine import SimpleQueryEngine

        service = RAGService(
            game_state_repo=Mock(),
            kb_manager=mock_kb_manager,
            query_engine=Mock(spec=SimpleQueryEngine),
        )
        return service

    @pytest.fixture
    def game_state(self) -> GameStateModel:
        """Create a game state with content pack priority."""
        return GameStateModel(
            campaign_id="test-campaign",
            campaign_goal="Test campaign",
            current_location={"name": "Test Town", "description": "A test location"},
            party={},
            chat_history=[],
            event_summary=[],
            world_lore=[],
            active_quests={},
            known_npcs={},
            content_pack_priority=["custom-pack", "homebrew-pack", "dnd_5e_srd"],
        )

    def test_get_relevant_knowledge_passes_content_pack_priority(
        self,
        rag_service: RAGService,
        mock_kb_manager: Mock,
        game_state: GameStateModel,
    ) -> None:
        """Test that get_relevant_knowledge passes content pack priority to kb_manager."""
        # Setup mock query engine to return a query
        mock_query = RAGQuery(
            query_text="fireball spell",
            query_type=QueryType.SPELL_CASTING,
            context={"spell_name": "fireball"},
            knowledge_base_types=["spells"],
        )
        mock_analyze_action = Mock(return_value=[mock_query])
        rag_service.query_engine = Mock(analyze_action=mock_analyze_action)

        # Setup mock response
        mock_results = RAGResults(
            results=[
                KnowledgeResult(
                    content="Fireball: A custom version of the spell",
                    source="spells",
                    relevance_score=0.9,
                )
            ],
            total_queries=1,
            execution_time_ms=10.0,
        )
        mock_kb_manager.search.return_value = mock_results

        # Call the method
        results = rag_service.get_relevant_knowledge(
            "I cast fireball",
            game_state,
            content_pack_priority=["custom-pack", "homebrew-pack", "dnd_5e_srd"],
        )

        # Verify kb_manager.search was called with content pack priority
        assert mock_kb_manager.search.called
        call_args = mock_kb_manager.search.call_args
        assert call_args.kwargs["content_pack_priority"] == [
            "custom-pack",
            "homebrew-pack",
            "dnd_5e_srd",
        ]
        assert results.results[0].content == "Fireball: A custom version of the spell"

    def test_rag_context_builder_integration(self, game_state: GameStateModel) -> None:
        """Test that rag_context_builder gets content pack priority from game state."""
        from app.content.rag.rag_context_builder import rag_context_builder

        # Mock the RAG service
        mock_rag_service = Mock()
        mock_rag_service.get_relevant_knowledge.return_value = RAGResults(
            results=[
                KnowledgeResult(
                    content="Custom Fireball spell from homebrew pack",
                    source="spells",
                    relevance_score=0.95,
                )
            ],
            total_queries=1,
            execution_time_ms=5.0,
        )

        # Call get_rag_context_for_prompt
        context = rag_context_builder.get_rag_context_for_prompt(
            game_state,
            mock_rag_service,
            "I cast fireball at the goblin",
            [],
            force_new_query=True,
        )

        # Verify the RAG service was called with content pack priority
        mock_rag_service.get_relevant_knowledge.assert_called_once()
        call_args = mock_rag_service.get_relevant_knowledge.call_args
        assert call_args[0][1] == game_state  # game_state argument
        assert call_args[0][2] == [
            "custom-pack",
            "homebrew-pack",
            "dnd_5e_srd",
        ]  # content_pack_priority

        # Verify context contains the custom result
        assert "Custom Fireball spell" in context
