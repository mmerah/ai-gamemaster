"""
Test the integration of DualDatabaseManager with the ServiceContainer.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from app.content.dual_connection import DualDatabaseManager
from app.content.protocols import DatabaseManagerProtocol
from app.core.container import ServiceContainer, reset_container
from app.models.config import ServiceConfigModel


class TestContainerDatabaseIntegration:
    """Test suite for ServiceContainer database integration."""

    def setup_method(self) -> None:
        """Reset container before each test."""
        reset_container()

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_container()

    def test_container_creates_database_manager(self) -> None:
        """Test that container creates and provides DualDatabaseManager."""
        config = ServiceConfigModel(
            DATABASE_URL="sqlite:///:memory:",
            USER_DATABASE_URL="sqlite:///:memory:_user",
            DATABASE_ECHO=False,
            ENABLE_SQLITE_VEC=False,
        )

        container = ServiceContainer(config)
        container.initialize()

        # Get the database manager
        db_manager = container.get_database_manager()

        assert isinstance(db_manager, DatabaseManagerProtocol)
        assert isinstance(db_manager, DualDatabaseManager)
        # DualDatabaseManager has both system and user databases
        assert db_manager.system_db_manager.database_url == "sqlite:///:memory:?mode=ro"
        assert db_manager.user_db_manager.database_url == "sqlite:///:memory:_user"

    def test_container_uses_config_for_database(self) -> None:
        """Test that container uses configuration for database settings."""
        config = ServiceConfigModel(
            DATABASE_URL="sqlite:///:memory:",  # Use in-memory database for tests
            USER_DATABASE_URL="sqlite:///:memory:_user",
            DATABASE_ECHO=True,
            DATABASE_POOL_SIZE=10,
            DATABASE_MAX_OVERFLOW=20,
            DATABASE_POOL_TIMEOUT=30,
            DATABASE_POOL_RECYCLE=3600,
            ENABLE_SQLITE_VEC=True,
        )

        container = ServiceContainer(config)
        container.initialize()

        db_manager = container.get_database_manager()

        assert isinstance(db_manager, DualDatabaseManager)
        # Check both system and user DB configs
        assert db_manager.system_db_manager._echo is True
        assert db_manager.user_db_manager._echo is True
        assert db_manager.system_db_manager._enable_sqlite_vec is True
        assert db_manager.user_db_manager._enable_sqlite_vec is True

    def test_container_creates_database_manager_once(self) -> None:
        """Test that container creates DualDatabaseManager only once (singleton)."""
        config = ServiceConfigModel(
            DATABASE_URL="sqlite:///:memory:",
            USER_DATABASE_URL="sqlite:///:memory:_user",
        )

        container = ServiceContainer(config)
        container.initialize()

        # Get database manager twice
        db_manager1 = container.get_database_manager()
        db_manager2 = container.get_database_manager()

        # Should be the same instance
        assert db_manager1 is db_manager2

    def test_container_with_dict_config(self) -> None:
        """Test that container works with dictionary configuration."""
        config: Dict[str, Any] = {
            "DATABASE_URL": "sqlite:///:memory:",
            "USER_DATABASE_URL": "sqlite:///:memory:_user",
            "DATABASE_ECHO": False,
            "ENABLE_SQLITE_VEC": False,
        }

        container = ServiceContainer(config)
        container.initialize()

        db_manager = container.get_database_manager()

        assert isinstance(db_manager, DatabaseManagerProtocol)
        assert isinstance(db_manager, DualDatabaseManager)

    def test_get_database_manager_initializes_container(self) -> None:
        """Test that getting database manager initializes container if needed."""
        config = ServiceConfigModel(
            DATABASE_URL="sqlite:///:memory:",
            USER_DATABASE_URL="sqlite:///:memory:_user",
        )

        container = ServiceContainer(config)
        # Don't call initialize() explicitly

        # Getting database manager should trigger initialization
        db_manager = container.get_database_manager()

        assert db_manager is not None
        assert container._initialized is True

    def test_container_disposes_database_on_cleanup(self) -> None:
        """Test that container disposes database connections on cleanup."""
        config = ServiceConfigModel(
            DATABASE_URL="sqlite:///:memory:",
            USER_DATABASE_URL="sqlite:///:memory:_user",
        )

        container = ServiceContainer(config)
        container.initialize()

        # Get database manager to create it
        db_manager = container.get_database_manager()

        # Mock the dispose method
        with patch.object(db_manager, "dispose") as mock_dispose:
            # Cleanup should dispose the database
            container.cleanup()
            mock_dispose.assert_called_once()
