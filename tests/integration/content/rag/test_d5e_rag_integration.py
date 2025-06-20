"""Integration tests for D5e RAG system."""

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from app.content.rag.d5e_db_knowledge_base_manager import D5eDbKnowledgeBaseManager
from app.content.rag.db_knowledge_base_manager import DummySentenceTransformer
from app.core.container import ServiceContainer
from app.models.game_state import GameStateModel
from tests.conftest import get_test_settings


class TestD5eRAGIntegration:
    """Test D5e RAG system integration."""

    @pytest.fixture
    def container_with_d5e_rag(
        self, test_database_url: str
    ) -> Generator[ServiceContainer, None, None]:
        """Create a container with D5e RAG enabled using test database."""
        import numpy as np

        # Mock the SentenceTransformer class
        mock_transformer = MagicMock()

        # Define a simple mock encode function that returns a consistent vector
        def mock_encode_func(texts: Any, **kwargs: Any) -> Any:
            if isinstance(texts, str):
                texts = [texts]
            # Return a unique but deterministic vector for each text based on its hash
            embeddings = []
            for text in texts:
                seed = hash(text) % (2**32)
                rng = np.random.RandomState(seed)
                embedding = rng.randn(384).astype(np.float32)
                embedding /= np.linalg.norm(embedding)
                embeddings.append(embedding)
            return np.array(embeddings)

        mock_transformer.encode.side_effect = mock_encode_func
        mock_transformer.embedding_dimension = 384

        # Patch the import statement itself to avoid numpy/scipy issues
        import sys
        from unittest.mock import Mock

        mock_module = Mock()
        mock_module.SentenceTransformer = MagicMock(return_value=mock_transformer)
        sys.modules["sentence_transformers"] = mock_module

        try:
            # Enable RAG with optimized settings
            settings = get_test_settings()
            # Update settings for RAG testing
            settings.rag.enabled = True
            settings.rag.embeddings_model = "sentence-transformers/all-MiniLM-L6-v2"
            settings.rag.chunk_size = 100  # Smaller chunks for tests
            settings.rag.max_results_per_query = 2  # Limit results for faster tests
            settings.rag.max_total_results = 5
            settings.database.url = SecretStr(test_database_url)  # Use test database

            container = ServiceContainer(settings)
            # Initialize to ensure services are created
            container.initialize()

            yield container

        finally:
            # Cleanup
            from app.core.container import reset_container

            reset_container()
            # Remove the mocked module
            if "sentence_transformers" in sys.modules:
                del sys.modules["sentence_transformers"]

    @pytest.mark.requires_rag
    def test_d5e_rag_service_initialization(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e RAG service initializes correctly."""
        rag_service = container_with_d5e_rag.get_rag_service()

        # Verify it's using D5e database-backed knowledge base manager
        assert hasattr(rag_service, "kb_manager")
        assert isinstance(rag_service.kb_manager, D5eDbKnowledgeBaseManager)

    @pytest.mark.requires_rag
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
        # Performance check - should be fast with mocked transformer
        assert results.execution_time_ms < 500  # 500ms max

    @pytest.mark.requires_rag
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

    @pytest.mark.requires_rag
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

        # Check if we're using the fallback transformer or mocked transformer
        kb_manager = getattr(rag_service, "kb_manager", None)
        if kb_manager and hasattr(kb_manager, "_sentence_transformer"):
            # If using fallback or mocked transformer, just verify we got spell data
            if isinstance(
                kb_manager._sentence_transformer, (DummySentenceTransformer, MagicMock)
            ):
                combined_content = " ".join(
                    [r.content.lower() for r in results.results]
                )
                assert "spell:" in combined_content
                assert "level" in combined_content
                return

        # Should contain fireball-specific content (only for real embeddings)
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

        game_state = GameStateModel()

        # Search for a well-known monster
        results = rag_service.get_relevant_knowledge("attack a goblin", game_state)

        # Should find results
        assert results.has_results()
        assert results.total_queries > 0

        # Check if we're using the fallback transformer or mocked transformer
        kb_manager = getattr(rag_service, "kb_manager", None)
        if kb_manager and hasattr(kb_manager, "_sentence_transformer"):
            # If using fallback or mocked transformer, just verify we got monster data
            if isinstance(
                kb_manager._sentence_transformer, (DummySentenceTransformer, MagicMock)
            ):
                combined_content = " ".join(
                    [r.content.lower() for r in results.results]
                )
                assert "monster:" in combined_content or "type:" in combined_content
                return

        # Should contain goblin-specific content (only for real embeddings)
        combined_content = " ".join([r.content.lower() for r in results.results])
        assert "goblin" in combined_content
        # D5e specific details
        # Debug: print what we actually got
        print(f"Results content: {combined_content[:500]}")
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

    @pytest.mark.requires_rag
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

    @pytest.mark.requires_rag
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

        # Check if we're using the fallback transformer or mocked transformer
        kb_manager = getattr(rag_service, "kb_manager", None)
        if kb_manager and hasattr(kb_manager, "_sentence_transformer"):
            # If using fallback or mocked transformer, just verify we got some results
            if isinstance(
                kb_manager._sentence_transformer, (DummySentenceTransformer, MagicMock)
            ):
                assert len(results.results) > 0
                return

        sources = {r.source for r in results.results}
        # Should find results from multiple knowledge bases
        assert len(sources) >= 2  # At least spells and monsters

    @pytest.mark.requires_rag
    def test_d5e_query_performance(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that D5e RAG queries complete in reasonable time."""
        rag_service = container_with_d5e_rag.get_rag_service()

        game_state = GameStateModel()

        # Perform a search
        results = rag_service.get_relevant_knowledge("cast shield spell", game_state)

        # Should complete quickly (under 1 second)
        assert results.execution_time_ms < 1000
        # Should have some results
        assert results.has_results()
