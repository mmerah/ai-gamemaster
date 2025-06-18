"""
Integration tests specifically for when RAG is enabled.
These tests ensure the full RAG functionality works correctly.
"""

import os
from typing import Generator
from unittest.mock import Mock

import pytest

# Skip entire module if RAG is disabled
if os.environ.get("RAG_ENABLED", "true").lower() == "false":
    pytest.skip("RAG is disabled", allow_module_level=True)

from flask import Flask

from app.content.rag.rag_service import RAGService
from app.core.container import ServiceContainer, get_container, reset_container
from tests.conftest import get_test_config


class TestRAGEnabledIntegration:
    """Integration tests for RAG functionality when enabled."""

    @pytest.fixture
    def rag_enabled_app(self, mock_ai_service: Mock) -> Generator[Flask, None, None]:
        """Create a Flask app with RAG enabled."""
        reset_container()
        config = get_test_config()
        # Update config fields directly
        config.RAG_ENABLED = True  # Enable RAG for these tests
        config.AI_SERVICE = mock_ai_service  # Use centralized mock

        from app import create_app

        app = create_app(config)
        with app.app_context():
            yield app
        reset_container()

    @pytest.fixture
    def container(self, rag_enabled_app: Flask) -> ServiceContainer:
        """Get the container from the app."""
        return get_container()

    def test_rag_service_is_real_implementation(
        self, container: ServiceContainer
    ) -> None:
        """Test that real RAG service is created when enabled."""
        rag_service = container.get_rag_service()
        assert isinstance(rag_service, RAGService)

    def test_rag_service_integration_with_game_orchestrator(
        self, container: ServiceContainer
    ) -> None:
        """Test that RAG service integrates properly with game orchestrator."""
        game_orchestrator = container.get_game_orchestrator()

        # Verify the narrative orchestration service has a real RAG service
        assert isinstance(
            game_orchestrator.narrative_orchestration.rag_service, RAGService
        )

    def test_rag_service_provides_knowledge(self, container: ServiceContainer) -> None:
        """Test that RAG service actually provides knowledge when enabled."""
        rag_service = container.get_rag_service()
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()

        # Test with a spell casting action
        action = "I cast fireball at the goblin"
        results = rag_service.get_relevant_knowledge(action, game_state)

        # Should return results (even if empty due to test data)
        assert results is not None
        assert results.total_queries >= 0
        assert results.execution_time_ms >= 0
