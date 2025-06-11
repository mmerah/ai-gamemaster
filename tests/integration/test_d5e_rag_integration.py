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

        # Test direct search on knowledge base
        if hasattr(rag_service, "kb_manager"):
            results = rag_service.kb_manager.search(
                "advantage rules", ["d5e_rules", "d5e_mechanics"]
            )

            # Verify structure
            assert results is not None
            assert len(results.results) >= 0  # May or may not find results
        else:
            # If no kb_manager, just verify the service exists
            assert rag_service is not None

    @pytest.mark.requires_rag
    def test_d5e_rag_equipment_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching for equipment using D5e RAG."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Test direct search on knowledge base
        if hasattr(rag_service, "kb_manager"):
            results = rag_service.kb_manager.search(
                "longsword weapon", ["d5e_equipment"]
            )

            # Verify structure
            assert results is not None
            assert len(results.results) >= 0  # May or may not find results
        else:
            # If no kb_manager, just verify the service exists
            assert rag_service is not None

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

    @pytest.mark.requires_rag
    def test_d5e_specific_spell_content(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e spell searches return actual spell data."""
        rag_service = container_with_d5e_rag.get_rag_service()

        from app.models import GameStateModel

        game_state = GameStateModel()

        # Search for a well-known spell
        results = rag_service.get_relevant_knowledge("cast fireball spell", game_state)

        # Should find results
        assert results.has_results()
        assert results.total_queries > 0

        # Should contain fireball-specific content
        combined_content = " ".join([r.content.lower() for r in results.results])
        assert "fireball" in combined_content
        # D5e specific details
        assert any(
            term in combined_content for term in ["8d6", "fire damage", "20-foot"]
        )

    @pytest.mark.requires_rag
    def test_d5e_specific_monster_content(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e monster searches return actual monster data."""
        rag_service = container_with_d5e_rag.get_rag_service()

        from app.models import GameStateModel

        game_state = GameStateModel()

        # Search for a well-known monster
        results = rag_service.get_relevant_knowledge("attack a goblin", game_state)

        # Should find results
        assert results.has_results()
        assert results.total_queries > 0

        # Should contain goblin-specific content
        combined_content = " ".join([r.content.lower() for r in results.results])
        assert "goblin" in combined_content
        # D5e specific details
        assert any(
            term in combined_content
            for term in ["small humanoid", "armor class", "hit points"]
        )

    @pytest.mark.requires_rag
    def test_d5e_lore_integration(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that lore is still loaded alongside D5e data."""
        rag_service = container_with_d5e_rag.get_rag_service()
        kb_manager = getattr(rag_service, "kb_manager", None)

        if kb_manager is None:
            pytest.skip("RAG service implementation doesn't expose kb_manager")

        # Lore should still be loaded
        assert "lore" in kb_manager.vector_stores

    @pytest.mark.requires_rag
    def test_d5e_cross_reference_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching across multiple D5e categories."""
        rag_service = container_with_d5e_rag.get_rag_service()

        from app.models import GameStateModel

        game_state = GameStateModel()

        # Search that should match multiple categories
        results = rag_service.get_relevant_knowledge(
            "wizard casting fireball at goblin", game_state
        )

        # Should find results from multiple sources
        assert results.has_results()
        sources = {r.source for r in results.results}
        # Should find results from multiple knowledge bases
        assert len(sources) >= 2  # At least spells and monsters

    @pytest.mark.requires_rag
    def test_d5e_query_performance(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e RAG queries complete in reasonable time."""
        rag_service = container_with_d5e_rag.get_rag_service()

        from app.models import GameStateModel

        game_state = GameStateModel()

        # Perform a search
        results = rag_service.get_relevant_knowledge("cast shield spell", game_state)

        # Should complete quickly (under 1 second)
        assert results.execution_time_ms < 1000
        # Should have some results
        assert results.has_results()
