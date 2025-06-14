"""
Enhanced test database management for better isolation and performance.
"""

import hashlib
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Generator, Optional, Tuple

import pytest
from sqlalchemy import create_engine, text

from app.database.models import Base
from app.database.validator import DatabaseValidator

logger = logging.getLogger(__name__)


class DatabaseTestManager:
    """Manages test databases with caching and proper isolation."""

    # Class-level cache for test databases
    _cache_dir = Path(tempfile.gettempdir()) / "ai_gamemaster_test_db_cache"
    _db_cache: Dict[str, Path] = {}

    def __init__(self) -> None:
        """Initialize the test database manager."""
        self._cache_dir.mkdir(exist_ok=True)
        self._cleanup_old_cache()

    def _cleanup_old_cache(self) -> None:
        """Clean up cache files older than 1 day."""
        import time

        current_time = time.time()
        one_day_ago = current_time - (24 * 60 * 60)

        for db_file in self._cache_dir.glob("*.db"):
            if db_file.stat().st_mtime < one_day_ago:
                try:
                    db_file.unlink()
                    logger.info(f"Cleaned up old cache: {db_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {db_file}: {e}")

    def get_test_database(
        self,
        source: str = "production",
        with_embeddings: bool = True,
        isolated: bool = True,
    ) -> Tuple[Path, str]:
        """
        Get a test database with specified characteristics.

        Args:
            source: "production", "empty", or path to source database
            with_embeddings: Whether to include vector embeddings
            isolated: Whether to create an isolated copy

        Returns:
            Tuple of (database_path, database_url)
        """
        # Generate cache key
        cache_key = self._generate_cache_key(source, with_embeddings)

        # Check cache
        if not isolated and cache_key in self._db_cache:
            cached_path = self._db_cache[cache_key]
            if cached_path.exists():
                logger.info(f"Using cached test database: {cached_path}")
                return cached_path, f"sqlite:///{cached_path}"

        # Create new test database
        if isolated:
            # Always create a new temporary database for isolation
            temp_dir = tempfile.mkdtemp(prefix="test_db_isolated_")
            db_path = Path(temp_dir) / "test_content.db"
        else:
            # Use cache directory
            db_path = self._cache_dir / f"{cache_key}.db"

        # Create or copy database
        if source == "empty":
            self._create_empty_database(db_path)
        elif source == "production":
            self._copy_production_database(db_path, with_embeddings)
        else:
            # Copy from specified source
            source_path = Path(source)
            if source_path.exists():
                shutil.copy2(source_path, db_path)
            else:
                raise ValueError(f"Source database not found: {source}")

        # Validate the database
        db_url = f"sqlite:///{db_path}"
        validator = DatabaseValidator(db_url)
        success, error = validator.validate_and_setup()

        if not success:
            logger.warning(f"Test database validation warning: {error}")

        # Cache if not isolated
        if not isolated:
            self._db_cache[cache_key] = db_path

        return db_path, db_url

    def _generate_cache_key(self, source: str, with_embeddings: bool) -> str:
        """Generate a unique cache key for the database configuration."""
        key_data = f"{source}:{with_embeddings}"
        return hashlib.md5(key_data.encode()).hexdigest()[:8]

    def _create_empty_database(self, db_path: Path) -> None:
        """Create an empty database with schema only."""
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        # Add default content pack
        with engine.connect() as conn:
            conn.execute(
                text("""
                INSERT INTO content_packs (id, name, is_active) 
                VALUES ('test_pack', 'Test Content Pack', 1)
                """)
            )
            conn.commit()

        engine.dispose()
        logger.info(f"Created empty test database at {db_path}")

    def _copy_production_database(self, db_path: Path, with_embeddings: bool) -> None:
        """Copy production database for testing."""
        # Try indexed test database first
        test_db_source = Path("data/test_content.db")
        prod_db_source = Path("data/content.db")

        if with_embeddings and test_db_source.exists():
            shutil.copy2(test_db_source, db_path)
            logger.info(f"Copied indexed test database to {db_path}")
        elif prod_db_source.exists():
            shutil.copy2(prod_db_source, db_path)
            logger.info(f"Copied production database to {db_path}")

            if not with_embeddings:
                # Remove embeddings to save space/time
                self._remove_embeddings(db_path)
        else:
            # Fallback: create empty database
            logger.warning("No source database found, creating empty database")
            self._create_empty_database(db_path)

    def _remove_embeddings(self, db_path: Path) -> None:
        """Remove vector embeddings from database to save space."""
        engine = create_engine(f"sqlite:///{db_path}")

        with engine.connect() as conn:
            # Tables with embedding columns
            tables_with_embeddings = [
                "spells",
                "monsters",
                "equipment",
                "classes",
                "races",
                "backgrounds",
                "feats",
                "magic_items",
            ]

            for table in tables_with_embeddings:
                try:
                    conn.execute(text(f"UPDATE {table} SET embedding = NULL"))
                except Exception:
                    # Table might not have embedding column
                    pass

            conn.commit()

        engine.dispose()
        logger.info("Removed embeddings from test database")

    def cleanup_isolated_database(self, db_path: Path) -> None:
        """Clean up an isolated test database."""
        if db_path.exists():
            # Remove the entire temp directory
            temp_dir = db_path.parent
            if temp_dir.name.startswith("test_db_isolated_"):
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up isolated test database: {db_path}")


# Global instance
_test_db_manager: Optional[DatabaseTestManager] = None


def get_test_db_manager() -> DatabaseTestManager:
    """Get the global test database manager instance."""
    global _test_db_manager
    if _test_db_manager is None:
        _test_db_manager = DatabaseTestManager()
    return _test_db_manager


# Pytest fixtures
@pytest.fixture(scope="session")
def test_db_manager() -> DatabaseTestManager:
    """Provide test database manager for the test session."""
    return get_test_db_manager()


@pytest.fixture(scope="session")
def shared_test_database(test_db_manager: DatabaseTestManager) -> Tuple[Path, str]:
    """
    Provide a shared test database for the entire test session.
    Use this for read-only tests that don't modify the database.
    """
    db_path, db_url = test_db_manager.get_test_database(
        source="production", with_embeddings=True, isolated=False
    )
    return db_path, db_url


@pytest.fixture(scope="function")
def isolated_test_database(
    test_db_manager: DatabaseTestManager,
) -> Generator[Tuple[Path, str], None, None]:
    """
    Provide an isolated test database for a single test.
    Use this for tests that modify the database.
    """
    db_path, db_url = test_db_manager.get_test_database(
        source="production", with_embeddings=True, isolated=True
    )

    yield db_path, db_url

    # Cleanup
    test_db_manager.cleanup_isolated_database(db_path)


@pytest.fixture(scope="function")
def empty_test_database(
    test_db_manager: DatabaseTestManager,
) -> Generator[Tuple[Path, str], None, None]:
    """
    Provide an empty test database with schema only.
    Use this for tests that need to populate their own data.
    """
    db_path, db_url = test_db_manager.get_test_database(
        source="empty", with_embeddings=False, isolated=True
    )

    yield db_path, db_url

    # Cleanup
    test_db_manager.cleanup_isolated_database(db_path)
