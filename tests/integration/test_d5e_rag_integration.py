"""Integration tests for D5e RAG system."""

from typing import Generator
from unittest.mock import patch

import pytest

from app.core.container import ServiceContainer
from app.core.rag_interfaces import QueryType, RAGQuery
from app.services.rag.d5e_knowledge_base_manager import D5eKnowledgeBaseManager


class TestD5eRAGIntegration:
    """Test D5e RAG system integration."""

    @pytest.fixture
    def container_with_d5e_rag(self) -> Generator[ServiceContainer, None, None]:
        """Create a container with D5e RAG enabled."""
        # Enable RAG and D5e integration
        config = {
            "RAG_ENABLED": True,
            "USE_D5E_RAG": True,
            "RAG_LOAD_STATIC_FILES": False,
        }

        container = ServiceContainer(config)
        # Initialize to ensure services are created
        container.initialize()

        yield container

        # Cleanup
        from app.core.container import reset_container

        reset_container()

    @pytest.mark.requires_rag
    def test_d5e_rag_service_initialization(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e RAG service initializes correctly."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Verify it's using D5e knowledge base manager
        assert hasattr(rag_service, "kb_manager")
        assert isinstance(rag_service.kb_manager, D5eKnowledgeBaseManager)

    @pytest.mark.requires_rag
    def test_d5e_rag_spell_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching for spells using D5e RAG."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Create a minimal game state for context
        from app.models import GameStateModel

        game_state = GameStateModel()

        # Search using the correct interface
        results = rag_service.get_relevant_knowledge("cast fireball spell", game_state)

        # Verify we get results
        assert results is not None
        assert results.total_queries > 0
        # Can't guarantee specific results without embeddings, but structure should be valid
        assert hasattr(results, "results")
        assert hasattr(results, "execution_time_ms")

    @pytest.mark.requires_rag
    def test_d5e_rag_monster_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching for monsters using D5e RAG."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Create a minimal game state for context
        from app.models import GameStateModel

        game_state = GameStateModel()

        # Search using the correct interface
        results = rag_service.get_relevant_knowledge("attack goblin", game_state)

        # Verify structure
        assert results is not None
        assert results.total_queries > 0

    @pytest.mark.requires_rag
    def test_d5e_rag_rules_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching for rules using D5e RAG."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Create a minimal game state for context
        from app.models import GameStateModel

        game_state = GameStateModel()

        # Search using the correct interface
        results = rag_service.get_relevant_knowledge(
            "check advantage rules", game_state
        )

        # Verify structure
        assert results is not None
        assert results.total_queries > 0

    @pytest.mark.requires_rag
    def test_d5e_rag_equipment_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching for equipment using D5e RAG."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Create a minimal game state for context
        from app.models import GameStateModel

        game_state = GameStateModel()

        # Search using the correct interface
        results = rag_service.get_relevant_knowledge(
            "check longsword properties", game_state
        )

        # Verify structure
        assert results is not None
        assert results.total_queries > 0

    @pytest.mark.requires_rag
    def test_d5e_knowledge_base_categories(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that all expected knowledge bases are created."""
        rag_service = container_with_d5e_rag.get_rag_service()
        # Access kb_manager if it exists (implementation detail)
        kb_manager = getattr(rag_service, "kb_manager", None)
        if kb_manager is None:
            pytest.skip("RAG service implementation doesn't expose kb_manager")

        # Expected knowledge base categories
        expected_categories = [
            "rules",
            "character_options",
            "spells",
            "monsters",
            "equipment",
            "mechanics",
        ]

        # Verify categories exist in vector stores
        for category in expected_categories:
            assert category in kb_manager.vector_stores, (
                f"Missing knowledge base: {category}"
            )

    def test_d5e_rag_disabled(self) -> None:
        """Test that D5e RAG can be disabled."""
        config = {
            "RAG_ENABLED": True,
            "USE_D5E_RAG": False,  # Disable D5e integration
        }

        container = ServiceContainer(config)
        container.initialize()

        try:
            rag_service = container.get_rag_service()

            # Should use standard knowledge base manager
            assert hasattr(rag_service, "kb_manager")
            assert not isinstance(rag_service.kb_manager, D5eKnowledgeBaseManager)
        finally:
            from app.core.container import reset_container

            reset_container()

    def test_rag_completely_disabled(self) -> None:
        """Test that RAG can be completely disabled."""
        config = {
            "RAG_ENABLED": False,
        }

        container = ServiceContainer(config)
        container.initialize()

        try:
            rag_service = container.get_rag_service()

            # Should get no-op implementation
            assert rag_service.__class__.__name__ == "NoOpRAGService"
        finally:
            from app.core.container import reset_container

            reset_container()
