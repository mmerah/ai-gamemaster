"""
Test database fixtures for integration tests.
Creates isolated test databases with indexed content.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.content.connection import DatabaseManager
from app.content.models import Base
from tests.integration.content.database.test_database_manager import get_test_db_manager


@pytest.fixture(scope="session")
def test_content_db_path() -> Generator[Path, None, None]:
    """Create a temporary test database with content."""
    # Use the new test database manager
    db_manager = get_test_db_manager()
    db_path, _ = db_manager.get_test_database(
        source="production",
        with_embeddings=True,
        isolated=False,  # Session-scoped, so share it
    )

    yield db_path

    # No cleanup needed for shared databases


@pytest.fixture(scope="function")
def test_db_manager(
    test_content_db_path: Path,
) -> Generator[DatabaseManager, None, None]:
    """Create a test database manager."""
    db_url = f"sqlite:///{test_content_db_path}"
    db_manager = DatabaseManager(
        database_url=db_url, echo=False, enable_sqlite_vec=True
    )

    yield db_manager

    # Cleanup connections
    db_manager.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_manager: DatabaseManager) -> Generator[Session, None, None]:
    """Create a test database session."""
    with test_db_manager.get_session() as session:
        yield session
