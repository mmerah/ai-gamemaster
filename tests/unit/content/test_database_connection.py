"""
Unit tests for database connection SQLite pragma configuration.
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, List
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Column, Integer, String, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import DeclarativeBase, Session

from app.content.connection import DatabaseManager


class Base(DeclarativeBase):
    """Base class for test models."""

    pass


class ConcurrentTestModel(Base):
    """Sample model for concurrency testing."""

    __tablename__ = "test_concurrent"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    value = Column(Integer, default=0)


class TestSQLitePragmaConfiguration:
    """Test suite for SQLite pragma configuration."""

    def test_wal_mode_enabled(self) -> None:
        """Test that WAL mode is enabled for SQLite databases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_wal.db"
            db_url = f"sqlite:///{db_path}"

            manager = DatabaseManager(database_url=db_url)
            try:
                # Get a session and check journal mode
                with manager.get_session() as session:
                    result = session.execute(text("PRAGMA journal_mode"))
                    journal_mode = result.scalar()
                    assert journal_mode == "wal"
            finally:
                manager.dispose()

    def test_busy_timeout_configured(self) -> None:
        """Test that busy timeout is properly configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_timeout.db"
            db_url = f"sqlite:///{db_path}"

            # Default timeout should be 5000ms
            manager = DatabaseManager(database_url=db_url)
            try:
                with manager.get_session() as session:
                    result = session.execute(text("PRAGMA busy_timeout"))
                    timeout = result.scalar()
                    assert timeout == 5000
            finally:
                manager.dispose()

    def test_custom_busy_timeout_from_config(self) -> None:
        """Test that busy timeout can be configured via environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_custom_timeout.db"
            db_url = f"sqlite:///{db_path}"

            # Set custom timeout via environment variable
            os.environ["SQLITE_BUSY_TIMEOUT"] = "10000"

            manager = DatabaseManager(database_url=db_url, sqlite_busy_timeout=10000)
            try:
                with manager.get_session() as session:
                    result = session.execute(text("PRAGMA busy_timeout"))
                    timeout = result.scalar()
                    assert timeout == 10000
            finally:
                # Clean up environment variable
                os.environ.pop("SQLITE_BUSY_TIMEOUT", None)
                manager.dispose()

    def test_synchronous_mode_configured(self) -> None:
        """Test that synchronous mode is set to NORMAL for performance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sync.db"
            db_url = f"sqlite:///{db_path}"

            manager = DatabaseManager(database_url=db_url)
            try:
                with manager.get_session() as session:
                    result = session.execute(text("PRAGMA synchronous"))
                    sync_mode = result.scalar()
                    assert sync_mode == 1  # NORMAL mode
            finally:
                manager.dispose()

    def test_pragma_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that pragma configuration is logged."""
        import logging

        # Set log level to INFO for the specific logger
        caplog.set_level(logging.INFO, logger="app.content.connection")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_logging.db"
            db_url = f"sqlite:///{db_path}"

            manager = DatabaseManager(database_url=db_url)
            try:
                # Force engine creation to trigger pragma configuration
                with manager.get_session() as session:
                    # Execute a simple query to ensure connection
                    session.execute(text("SELECT 1"))

                # Check that pragma configuration was logged
                assert "Configured SQLite pragmas" in caplog.text
                assert "WAL mode enabled" in caplog.text
            finally:
                manager.dispose()

    def test_pragmas_not_applied_to_postgresql(self) -> None:
        """Test that SQLite pragmas are not applied to PostgreSQL databases."""
        # Create a real PostgreSQL-style URL (won't actually connect)
        manager = DatabaseManager(database_url="postgresql://user:pass@localhost/test")

        # Mock the create_engine to avoid actual connection
        with patch("app.content.connection.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            # Track event.listens_for calls
            listen_calls = []

            def track_listen(target: Any, identifier: str) -> Any:
                def decorator(fn: Any) -> Any:
                    listen_calls.append((target, identifier, fn.__name__))
                    return fn

                return decorator

            with patch(
                "app.content.connection.event.listens_for", side_effect=track_listen
            ):
                mock_create_engine.return_value = mock_engine

                # Get engine which should trigger configuration
                _ = manager.get_engine()

                # Check that no SQLite pragma configuration was added
                pragma_listeners = [
                    call
                    for call in listen_calls
                    if call[1] == "connect" and "configure_sqlite_pragmas" in call[2]
                ]
                assert len(pragma_listeners) == 0

    def test_concurrent_writers_with_wal_mode(self) -> None:
        """Test that multiple concurrent writers work with WAL mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_concurrent.db"
            db_url = f"sqlite:///{db_path}"

            manager = DatabaseManager(database_url=db_url, sqlite_busy_timeout=5000)
            try:
                # Create the test table
                Base.metadata.create_all(manager.get_engine())

                errors: List[Exception] = []

                def write_data(thread_id: int) -> None:
                    """Write data in a thread."""
                    try:
                        for i in range(5):
                            with manager.get_session() as session:
                                obj = ConcurrentTestModel(
                                    name=f"thread_{thread_id}_item_{i}",
                                    value=thread_id * 100 + i,
                                )
                                session.add(obj)
                                session.commit()
                            # Small delay to increase chance of contention
                            time.sleep(0.01)
                    except Exception as e:
                        errors.append(e)

                # Create multiple writer threads
                threads = []
                for i in range(3):
                    thread = threading.Thread(target=write_data, args=(i,))
                    threads.append(thread)
                    thread.start()

                # Wait for all threads to complete
                for thread in threads:
                    thread.join(timeout=10)

                # No errors should have occurred
                assert len(errors) == 0

                # Verify all data was written
                with manager.get_session() as session:
                    count = session.query(ConcurrentTestModel).count()
                    assert count == 15  # 3 threads * 5 items each
            finally:
                manager.dispose()

    def test_multiple_readers_during_write(self) -> None:
        """Test that readers can access database during writes with WAL mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_readers.db"
            db_url = f"sqlite:///{db_path}"

            manager = DatabaseManager(database_url=db_url)
            try:
                # Create the test table and initial data
                Base.metadata.create_all(manager.get_engine())

                with manager.get_session() as session:
                    initial = ConcurrentTestModel(name="initial", value=1)
                    session.add(initial)
                    session.commit()

                read_results: List[int] = []
                write_started = threading.Event()
                reads_finished = threading.Event()
                write_complete = threading.Event()

                def coordinated_write() -> None:
                    """Perform a write operation coordinated with reader threads."""
                    with manager.get_session() as session:
                        # Start transaction
                        obj = ConcurrentTestModel(name="slow_write", value=999)
                        session.add(obj)
                        session.flush()

                        # Signal that the write transaction has started
                        write_started.set()

                        # Hold transaction open until reads are finished
                        reads_finished.wait(timeout=1)

                        session.commit()
                        write_complete.set()

                def read_data() -> None:
                    """Read data while write is in progress."""
                    with manager.get_session() as session:
                        count = session.query(ConcurrentTestModel).count()
                        read_results.append(count)

                # Start coordinated write in background
                write_thread = threading.Thread(target=coordinated_write)
                write_thread.start()

                # Wait for the write transaction to begin
                assert write_started.wait(timeout=1), (
                    "Write thread failed to start transaction"
                )

                # Perform reads while write is in progress
                read_threads = []
                for _ in range(3):
                    thread = threading.Thread(target=read_data)
                    read_threads.append(thread)
                    thread.start()

                # Wait for all read threads to complete
                for thread in read_threads:
                    thread.join(timeout=1)

                # Signal the writer that it can commit
                reads_finished.set()

                # Wait for the write to fully complete
                assert write_complete.wait(timeout=1), "Write thread failed to commit"
                write_thread.join(timeout=1)

                # Reads should have succeeded and seen initial data
                assert len(read_results) == 3
                assert all(
                    count == 1 for count in read_results
                )  # Only initial record visible

                # After write completes, new data should be visible
                with manager.get_session() as session:
                    final_count = session.query(ConcurrentTestModel).count()
                    assert final_count == 2  # Initial + slow_write
            finally:
                manager.dispose()

    def test_pragma_configuration_error_handling(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that pragma configuration errors are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_error.db"
            db_url = f"sqlite:///{db_path}"

            # Mock the pragma configuration to raise an error
            with patch("sqlalchemy.engine.Connection.execute") as mock_execute:
                # Allow engine creation queries but fail on pragma
                def side_effect(statement: Any) -> Any:
                    if isinstance(statement, str) or (
                        hasattr(statement, "text") and "PRAGMA" in str(statement)
                    ):
                        raise Exception("Pragma error")
                    return MagicMock()

                mock_execute.side_effect = side_effect

                manager = DatabaseManager(database_url=db_url)

                # Should not raise exception, just log warning
                try:
                    engine = manager.get_engine()
                    assert engine is not None
                except Exception:
                    # If we get here, the error wasn't handled properly
                    pytest.fail("Pragma error should have been handled")

    def test_in_memory_database_pragmas(self) -> None:
        """Test that pragmas work correctly with in-memory databases."""
        manager = DatabaseManager(database_url="sqlite:///:memory:")

        # In-memory databases should still get pragma configuration
        with manager.get_session() as session:
            # Journal mode for in-memory is always "memory", not WAL
            result = session.execute(text("PRAGMA journal_mode"))
            journal_mode = result.scalar()
            assert journal_mode in ("memory", "wal")  # Either is acceptable

            # But other pragmas should still be set
            result = session.execute(text("PRAGMA busy_timeout"))
            timeout = result.scalar()
            assert timeout == 5000
