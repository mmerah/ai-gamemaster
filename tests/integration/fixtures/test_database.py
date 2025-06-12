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

from app.database.connection import DatabaseManager
from app.database.models import Base


@pytest.fixture(scope="session")
def test_content_db_path() -> Generator[Path, None, None]:
    """Create a temporary test database with content."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_content_db_")
    test_db_path = Path(temp_dir) / "test_content.db"

    # Use pre-indexed test database if available
    test_db_source = Path("data/test_content.db")
    if test_db_source.exists():
        shutil.copy2(test_db_source, test_db_path)
    else:
        # Fall back to production content.db
        prod_db_path = Path("data/content.db")
        if prod_db_path.exists():
            shutil.copy2(prod_db_path, test_db_path)
        else:
            # If no database exists, create empty one
            engine = create_engine(f"sqlite:///{test_db_path}")
            Base.metadata.create_all(engine)
            engine.dispose()

    yield test_db_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


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
