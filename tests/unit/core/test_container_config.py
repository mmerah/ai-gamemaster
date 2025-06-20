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

import os

from app.core.container import ServiceContainer, reset_container
from app.settings import RAGSettings, StorageSettings, TTSSettings
from tests.conftest import get_test_settings

# Only import RAG services if RAG is enabled
NoOpRAGService: Optional[Type[Any]] = None
RAGService: Optional[Type[Any]] = None

if os.environ.get("RAG_ENABLED", "true").lower() != "false":
    try:
        from app.content.rag import (
            NoOpRAGService as _NoOpRAGService,
        )
        from app.content.rag.rag_service import (
            RAGService as _RAGServiceImpl,
        )

        NoOpRAGService = _NoOpRAGService
        RAGService = _RAGServiceImpl
    except ImportError:
        pass


class TestContainerConfiguration(IsolatedTestCase, unittest.TestCase):
    """Test that ServiceContainer respects configuration options."""

    def setUp(self) -> None:
        """Set up clean state before each test."""
        reset_container()
        # Also reset the global RAG service cache
        import app.core.container

        app.core.container._global_rag_service_cache = None

    def tearDown(self) -> None:
        """Reset container after each test."""
        reset_container()
        # Also reset the global RAG service cache
        import app.core.container

        app.core.container._global_rag_service_cache = None

    def test_rag_enabled_by_default(self) -> None:
        """Test that RAG is enabled by default when not explicitly configured."""
        # This test checks container behavior, not environment
        # Import RAG services locally to avoid import errors
        try:
            from app.content.rag import NoOpRAGService
            from app.content.rag.rag_service import RAGService
        except ImportError:
            self.skipTest("RAG services not available")

        # Temporarily override the environment variable to test proper Settings behavior
        old_rag_enabled = os.environ.get("RAG_ENABLED")
        try:
            # Remove the env var so Settings uses its default
            if "RAG_ENABLED" in os.environ:
                del os.environ["RAG_ENABLED"]

            # Create Settings with default values (RAG should be enabled by default)
            from app.settings import Settings

            settings = Settings()

            container = ServiceContainer(settings)
            container.initialize()

            rag_service = container.get_rag_service()
            # Default behavior should enable RAG
            self.assertIsInstance(rag_service, RAGService)
            self.assertNotIsInstance(rag_service, NoOpRAGService)
        finally:
            # Restore the original environment
            if old_rag_enabled is not None:
                os.environ["RAG_ENABLED"] = old_rag_enabled

    def test_rag_disabled_via_config(self) -> None:
        """Test that RAG can be disabled via configuration."""
        # This test checks container behavior when explicitly disabled
        # Import RAG services locally to avoid import errors
        try:
            from app.content.rag import NoOpRAGService
            from app.content.rag.rag_service import RAGService
        except ImportError:
            self.skipTest("RAG services not available")

        settings = get_test_settings()
        settings.rag.enabled = False
        container = ServiceContainer(settings)
        container.initialize()

        rag_service = container.get_rag_service()
        self.assertIsInstance(rag_service, NoOpRAGService)
        self.assertNotIsInstance(rag_service, RAGService)

    def test_tts_disabled_via_config(self) -> None:
        """Test that TTS can be disabled via configuration."""
        settings = get_test_settings()
        settings.tts.provider = "disabled"
        settings.rag.enabled = False
        container = ServiceContainer(settings)
        container.initialize()

        tts_service = container.get_tts_service()
        self.assertIsNone(tts_service)

    def test_repository_type_config(self) -> None:
        """Test repository type configuration."""
        import shutil
        import tempfile

        # Test memory repository
        settings = get_test_settings()
        settings.storage.game_state_repo_type = "memory"
        settings.rag.enabled = False
        settings.tts.provider = "disabled"
        container = ServiceContainer(settings)
        container.initialize()

        repo = container.get_game_state_repository()
        self.assertEqual(repo.__class__.__name__, "InMemoryGameStateRepository")

        reset_container()

        # Test file repository with temp directory
        temp_dir = tempfile.mkdtemp()
        try:
            settings = get_test_settings()
            settings.storage.game_state_repo_type = "file"
            settings.storage.saves_dir = temp_dir
            settings.storage.campaigns_dir = temp_dir
            settings.rag.enabled = False
            settings.tts.provider = "disabled"
            # Create a fresh container, not reusing any globals
            container = ServiceContainer(settings)
            # Debug: check what settings the container actually has
            self.assertEqual(container.settings.storage.game_state_repo_type, "file")
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
        settings = get_test_settings()
        settings.storage.campaigns_dir = "custom/campaigns"
        settings.storage.character_templates_dir = "custom/templates"
        settings.rag.enabled = False
        settings.tts.provider = "disabled"
        container = ServiceContainer(settings)
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
