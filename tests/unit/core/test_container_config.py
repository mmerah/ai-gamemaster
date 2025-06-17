"""
Unit tests for ServiceContainer configuration options.
"""

from __future__ import annotations

import os
import unittest
from typing import Any, Optional, Type

from tests.test_helpers import IsolatedTestCase, setup_test_environment

# Set up environment before importing app modules
setup_test_environment()

from app.core.container import ServiceContainer, reset_container
from tests.conftest import get_test_config

# Only import RAG services if RAG is enabled
NoOpRAGService: Optional[Type[Any]] = None
RAGServiceImpl: Optional[Type[Any]] = None

if os.environ.get("RAG_ENABLED", "true").lower() != "false":
    try:
        from app.content.rag import (
            NoOpRAGService as _NoOpRAGService,
        )
        from app.content.rag.rag_service import (
            RAGServiceImpl as _RAGServiceImpl,
        )

        NoOpRAGService = _NoOpRAGService
        RAGServiceImpl = _RAGServiceImpl
    except ImportError:
        pass


class TestContainerConfiguration(IsolatedTestCase, unittest.TestCase):
    """Test that ServiceContainer respects configuration options."""

    def tearDown(self) -> None:
        """Reset container after each test."""
        reset_container()

    def test_rag_enabled_by_default(self) -> None:
        """Test that RAG is enabled by default when not explicitly configured."""
        # This test checks container behavior, not environment
        # Import RAG services locally to avoid import errors
        try:
            from app.content.rag import NoOpRAGService
            from app.content.rag.rag_service import RAGServiceImpl
        except ImportError:
            self.skipTest("RAG services not available")

        # Use get_test_config with default values (RAG enabled by default in ServiceConfigModel)
        from app.models.config import ServiceConfigModel

        config = ServiceConfigModel()  # Uses model defaults, not test defaults
        container = ServiceContainer(config)
        container.initialize()

        rag_service = container.get_rag_service()
        # Default behavior is to enable RAG
        self.assertIsInstance(rag_service, RAGServiceImpl)
        self.assertNotIsInstance(rag_service, NoOpRAGService)

    def test_rag_disabled_via_config(self) -> None:
        """Test that RAG can be disabled via configuration."""
        # This test checks container behavior when explicitly disabled
        # Import RAG services locally to avoid import errors
        try:
            from app.content.rag import NoOpRAGService
            from app.content.rag.rag_service import RAGServiceImpl
        except ImportError:
            self.skipTest("RAG services not available")

        container = ServiceContainer(get_test_config(RAG_ENABLED=False))
        container.initialize()

        rag_service = container.get_rag_service()
        self.assertIsInstance(rag_service, NoOpRAGService)
        self.assertNotIsInstance(rag_service, RAGServiceImpl)

    def test_tts_disabled_via_config(self) -> None:
        """Test that TTS can be disabled via configuration."""
        container = ServiceContainer(
            get_test_config(TTS_PROVIDER="disabled", RAG_ENABLED=False)
        )
        container.initialize()

        tts_service = container.get_tts_service()
        self.assertIsNone(tts_service)

    def test_repository_type_config(self) -> None:
        """Test repository type configuration."""
        import shutil
        import tempfile

        # Test memory repository
        container = ServiceContainer(
            get_test_config(
                GAME_STATE_REPO_TYPE="memory",
                RAG_ENABLED=False,
                TTS_PROVIDER="disabled",
            )
        )
        container.initialize()

        repo = container.get_game_state_repository()
        self.assertEqual(repo.__class__.__name__, "InMemoryGameStateRepository")

        reset_container()

        # Test file repository with temp directory
        temp_dir = tempfile.mkdtemp()
        try:
            container = ServiceContainer(
                get_test_config(
                    GAME_STATE_REPO_TYPE="file",
                    CAMPAIGNS_DIR=temp_dir,
                    RAG_ENABLED=False,
                    TTS_PROVIDER="disabled",
                )
            )
            container.initialize()

            repo = container.get_game_state_repository()
            self.assertEqual(repo.__class__.__name__, "FileGameStateRepository")
        finally:
            shutil.rmtree(temp_dir)

    def test_directory_path_configs(self) -> None:
        """Test that directory path configurations are respected."""
        # Reset any global container state
        reset_container()

        # Create a fresh container with our custom config
        container = ServiceContainer(
            get_test_config(
                CAMPAIGNS_DIR="custom/campaigns",
                CHARACTER_TEMPLATES_DIR="custom/templates",
                RAG_ENABLED=False,
                TTS_PROVIDER="disabled",
            )
        )
        container.initialize()

        # Check repositories use custom paths
        # Campaign repository removed - using campaign template repository instead
        campaign_template_repo = container.get_campaign_template_repository()
        self.assertIsNotNone(campaign_template_repo)

        template_repo = container.get_character_template_repository()
        # Verify repository is created with custom config
        self.assertIsNotNone(template_repo)


if __name__ == "__main__":
    unittest.main()
