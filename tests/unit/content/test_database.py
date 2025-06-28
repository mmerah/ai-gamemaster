"""
Unit tests for database connection and management.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Column, Integer, String, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session

from app.content.connection import DatabaseManager


class Base(DeclarativeBase):
    """Base class for test models."""

    pass


class SampleModel(Base):
    """Sample model for database operations."""

    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    value = Column(String(100))


class TestDatabaseManager:
    """Test suite for DatabaseManager."""

    def test_create_with_memory_database(self) -> None:
        """Test creating a DatabaseManager with in-memory SQLite database."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")

        assert manager is not None
        assert manager.database_url == "sqlite:///:memory:"
        assert manager._engine is None  # Engine should be lazy-loaded
        assert manager._session_factory is None  # Session factory should be lazy-loaded

    def test_create_with_file_database(self) -> None:
        """Test creating a DatabaseManager with file-based SQLite database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db_url = f"sqlite:///{db_path}"

            manager = DatabaseManager(database_url=db_url)

            assert manager is not None
            assert manager.database_url == db_url

    def test_get_engine_creates_engine_once(self) -> None:
        """Test that get_engine creates the engine only once (lazy loading)."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")

        # First call should create the engine
        engine1 = manager.get_engine()
        assert engine1 is not None
        assert isinstance(engine1, Engine)
        assert manager._engine is engine1

        # Second call should return the same engine
        engine2 = manager.get_engine()
        assert engine2 is engine1

    def test_get_session_returns_working_session(self) -> None:
        """Test that get_session returns a working database session."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")

        # Create tables for testing
        Base.metadata.create_all(manager.get_engine())

        # Get a session and test it works
        with manager.get_session() as session:
            assert isinstance(session, Session)

            # Test basic CRUD operations
            test_obj = SampleModel(name="test", value="value123")
            session.add(test_obj)
            session.commit()

            # Query the object back
            result = session.query(SampleModel).filter_by(name="test").first()
            assert result is not None
            assert result.name == "test"
            assert result.value == "value123"

    def test_session_context_manager_commits_on_success(self) -> None:
        """Test that session context manager commits on successful exit."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        Base.metadata.create_all(manager.get_engine())

        # Add an object in one session
        with manager.get_session() as session:
            test_obj = SampleModel(name="commit_test", value="should_persist")
            session.add(test_obj)

        # Verify it persisted in a new session
        with manager.get_session() as session:
            result = session.query(SampleModel).filter_by(name="commit_test").first()
            assert result is not None
            assert result.value == "should_persist"

    def test_session_context_manager_rollbacks_on_exception(self) -> None:
        """Test that session context manager rollbacks on exception."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        Base.metadata.create_all(manager.get_engine())

        # Try to add an object but raise an exception
        with pytest.raises(ValueError):
            with manager.get_session() as session:
                test_obj = SampleModel(name="rollback_test", value="should_not_persist")
                session.add(test_obj)
                raise ValueError("Test exception")

        # Verify it didn't persist
        with manager.get_session() as session:
            result = session.query(SampleModel).filter_by(name="rollback_test").first()
            assert result is None

    def test_create_all_tables(self) -> None:
        """Test creating all tables from metadata."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")

        # Create tables
        manager.create_all_tables(Base.metadata)

        # Verify tables were created
        inspector = inspect(manager.get_engine())
        table_names = inspector.get_table_names()
        assert "test_table" in table_names

    def test_dispose_closes_connections(self) -> None:
        """Test that dispose closes all database connections."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")

        # Get engine to initialize it
        engine = manager.get_engine()
        initial_pool_id = id(engine.pool)

        # Dispose should close connections
        manager.dispose()

        # After dispose, the pool should be recreated if accessed again
        # For SQLite's SingletonThreadPool, we check that it's been disposed
        # by verifying the pool is recreated on next access
        new_engine = manager.get_engine()
        assert id(new_engine.pool) != initial_pool_id

    def test_sqlite_vec_extension_loading(self) -> None:
        """Test that sqlite-vec extension can be loaded for vector operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_vec.db"
            db_url = f"sqlite:///{db_path}"

            manager = DatabaseManager(database_url=db_url, enable_sqlite_vec=True)

            try:
                # Get a session and verify sqlite-vec functions are available
                with manager.get_session() as session:
                    # Try to use a sqlite-vec function
                    # vec_version() should return the version if extension is loaded
                    try:
                        result = session.execute(text("SELECT vec_version()"))
                        version = result.scalar()
                        assert version is not None
                        assert isinstance(version, str)
                    except OperationalError:
                        pytest.skip(
                            "sqlite-vec extension not available in test environment"
                        )
            finally:
                manager.dispose()

    def test_database_url_validation(self) -> None:
        """Test that database URL is validated."""
        from app.exceptions import ConnectionError

        # Invalid URL should raise ConnectionError
        with pytest.raises(ConnectionError, match="Invalid database URL"):
            DatabaseManager(database_url="")

        with pytest.raises(ConnectionError, match="Invalid database URL"):
            DatabaseManager(database_url="not-a-url")

    def test_thread_safety_different_sessions(self) -> None:
        """Test that different threads get different sessions."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")
        Base.metadata.create_all(manager.get_engine())

        sessions: list[Session] = []

        def get_session_in_thread() -> None:
            with manager.get_session() as session:
                sessions.append(session)

        import threading

        # Create multiple threads that get sessions
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=get_session_in_thread)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify we got different session objects
        assert len(sessions) == 3
        assert len(set(id(s) for s in sessions)) == 3  # All different objects

    def test_echo_mode_configuration(self) -> None:
        """Test that echo mode can be configured for SQL logging."""
        # With echo enabled
        manager = DatabaseManager(database_url="sqlite:///:memory:", echo=True)
        engine = manager.get_engine()
        assert engine.echo is True

        # With echo disabled (default)
        manager2 = DatabaseManager(database_url="sqlite:///:memory:")
        engine2 = manager2.get_engine()
        assert engine2.echo is False

    def test_custom_pool_configuration(self) -> None:
        """Test that custom pool configuration can be applied."""
        # For PostgreSQL-style configuration
        pool_config = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 3600,
        }

        # Test with PostgreSQL URL (won't actually connect)
        manager = DatabaseManager(
            database_url="postgresql://user:pass@localhost/test",
            pool_config=pool_config,
        )

        # Verify configuration was stored
        assert manager._pool_config == pool_config

        # For SQLite, only certain pool options are valid
        sqlite_pool_config = {
            "pool_recycle": 3600,  # This is valid for SQLite
        }

        manager2 = DatabaseManager(
            database_url="sqlite:///:memory:", pool_config=sqlite_pool_config
        )

        # Should create engine without errors
        engine = manager2.get_engine()
        assert engine is not None
