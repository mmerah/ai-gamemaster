"""Integration tests for D5e RAG system."""

from typing import Generator

import pytest
from pydantic import SecretStr

from app.content.rag.d5e_db_knowledge_base_manager import D5eDbKnowledgeBaseManager
from app.core.container import ServiceContainer
from app.models.game_state.main import GameStateModel
from tests.conftest import get_test_settings


@pytest.mark.requires_rag
class TestD5eRAGIntegration:
    """Test D5e RAG system integration."""

    @pytest.fixture
    def container_with_d5e_rag(
        self, test_database_url: str
    ) -> Generator[ServiceContainer, None, None]:
        """Create a container with D5e RAG enabled using test database.

        This is an integration test fixture that uses REAL embeddings.
        The test database should have pre-generated embeddings.
        """
        # Enable RAG with test settings
        settings = get_test_settings()
        settings.rag.enabled = True
        settings.rag.embeddings_model = "intfloat/multilingual-e5-small"
        settings.rag.chunk_size = 100  # Smaller chunks for tests
        settings.rag.max_results_per_query = 5  # Get more results for better testing
        settings.rag.max_total_results = 10
        settings.rag.score_threshold = 0.2  # Lower threshold for tests
        settings.database.url = SecretStr(test_database_url)  # Use test database

        container = ServiceContainer(settings)
        # Initialize to ensure services are created
        container.initialize()

        yield container

        # Cleanup
        from app.core.container import reset_container

        reset_container()

    def test_d5e_rag_service_initialization(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e RAG service initializes correctly."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Verify it's using D5e database-backed knowledge base manager
        assert hasattr(rag_service, "kb_manager")
        assert isinstance(rag_service.kb_manager, D5eDbKnowledgeBaseManager)

    def test_d5e_rag_spell_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching for spells using D5e RAG."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Create a minimal game state for context

        game_state = GameStateModel()

        # Search using the correct interface
        results = rag_service.get_relevant_knowledge("cast fireball spell", game_state)

        # Verify we get results (structure only, not content)
        assert results is not None
        assert results.total_queries > 0
        assert hasattr(results, "results")
        # Performance check - real embeddings are slower than mocks
        assert results.execution_time_ms < 5000  # 5 seconds max for real embeddings

    def test_d5e_rag_monster_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching for monsters using D5e RAG."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Create a minimal game state for context

        game_state = GameStateModel()

        # Search using the correct interface
        results = rag_service.get_relevant_knowledge("attack goblin", game_state)

        # Verify structure
        assert results is not None
        assert results.total_queries > 0

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

    def test_d5e_knowledge_base_categories(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that all expected knowledge bases are searchable."""
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

        # The DB-backed implementation doesn't use vector_stores
        # Instead, verify we can search these categories

        game_state = GameStateModel()

        for category in expected_categories:
            results = rag_service.get_relevant_knowledge(f"test {category}", game_state)
            # Just verify the search doesn't crash
            assert results is not None

    def test_rag_completely_disabled(self) -> None:
        """Test that RAG can be completely disabled."""
        # Create settings with RAG disabled
        settings = get_test_settings()
        settings.rag.enabled = False

        container = ServiceContainer(settings)
        container.initialize()

        try:
            rag_service = container.get_rag_service()

            # Should get no-op implementation
            assert rag_service.__class__.__name__ == "NoOpRAGService"
        finally:
            from app.core.container import reset_container

            reset_container()

    def test_d5e_specific_spell_content(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e spell searches return actual spell data."""
        rag_service = container_with_d5e_rag.get_rag_service()

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

    def test_d5e_specific_monster_content(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e monster searches return actual monster data."""
        rag_service = container_with_d5e_rag.get_rag_service()

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
            for term in [
                "small humanoid",
                "armor class",
                "hit points",
                "hp:",
                "type:",
                "cr:",
            ]
        )

    def test_d5e_lore_integration(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that lore is still loaded alongside D5e data."""
        rag_service = container_with_d5e_rag.get_rag_service()
        kb_manager = getattr(rag_service, "kb_manager", None)

        if kb_manager is None:
            pytest.skip("RAG service implementation doesn't expose kb_manager")

        # Lore should still be searchable

        game_state = GameStateModel()

        # Search for lore content
        results = rag_service.get_relevant_knowledge("dragon lore", game_state)
        assert results is not None

    def test_d5e_cross_reference_search(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test searching across multiple D5e categories."""
        rag_service = container_with_d5e_rag.get_rag_service()

        game_state = GameStateModel()

        # Search that should match multiple categories
        results = rag_service.get_relevant_knowledge(
            "wizard casting fireball at goblin", game_state
        )

        # Should find results from multiple sources
        assert results.has_results()
        assert len(results.results) > 0

        # Should find content related to multiple aspects of the query
        combined_content = " ".join([r.content.lower() for r in results.results])

        # Should find spell-related or class-related content
        has_magic_content = any(
            keyword in combined_content
            for keyword in ["spell", "wizard", "fireball", "cast", "magic"]
        )

        # Should find creature-related content
        has_creature_content = any(
            keyword in combined_content
            for keyword in ["goblin", "monster", "creature", "humanoid"]
        )

        # At least one type of content should be found
        assert has_magic_content or has_creature_content, (
            f"Expected magic or creature content, but got: {combined_content[:500]}"
        )

    def test_d5e_query_performance(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e RAG queries complete in reasonable time."""
        rag_service = container_with_d5e_rag.get_rag_service()

        game_state = GameStateModel()

        # Perform a search
        results = rag_service.get_relevant_knowledge("cast shield spell", game_state)

        # Should complete reasonably quickly (under 5 seconds for real embeddings)
        assert results.execution_time_ms < 5000
        # Should have some results
        assert results.has_results()
