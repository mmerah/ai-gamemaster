"""
Dual database connection management for system and user content separation.

This module provides a manager that handles both system (read-only) and user
(read-write) databases to keep user-generated content separate from the
shipped system content.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

from sqlalchemy import MetaData, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import Base
from app.content.protocols import ContentSource
from app.exceptions import ConnectionError, DatabaseError

logger = logging.getLogger(__name__)


class DualDatabaseManager:
    """Manages both system and user content databases."""

    def __init__(
        self,
        system_database_url: str,
        user_database_url: str,
        echo: bool = False,
        pool_config: Optional[Dict[str, Any]] = None,
        enable_sqlite_vec: bool = False,
        sqlite_busy_timeout: Optional[int] = None,
    ) -> None:
        """
        Initialize the DualDatabaseManager.

        Args:
            system_database_url: SQLAlchemy URL for system content DB (read-only)
            user_database_url: SQLAlchemy URL for user content DB
            echo: If True, log all SQL statements
            pool_config: Optional connection pool configuration
            enable_sqlite_vec: If True, attempt to load sqlite-vec extension
            sqlite_busy_timeout: SQLite busy timeout in milliseconds
        """
        # Create system database manager (read-only)
        # Add read-only mode to SQLite URLs
        if (
            system_database_url.startswith("sqlite:///")
            and "mode=" not in system_database_url
        ):
            system_database_url = f"{system_database_url}?mode=ro"

        self.system_db_manager = DatabaseManager(
            database_url=system_database_url,
            echo=echo,
            pool_config=pool_config,
            enable_sqlite_vec=enable_sqlite_vec,
            sqlite_busy_timeout=sqlite_busy_timeout,
        )

        # Create user database manager
        self.user_db_manager = DatabaseManager(
            database_url=user_database_url,
            echo=echo,
            pool_config=pool_config,
            enable_sqlite_vec=enable_sqlite_vec,
            sqlite_busy_timeout=sqlite_busy_timeout,
        )

        self._user_db_initialized = False

    def initialize_user_database(self) -> None:
        """Initialize the user database schema if it doesn't exist."""
        if self._user_db_initialized:
            return

        try:
            # Check if user database exists
            user_db_path = self.user_db_manager.database_url.replace("sqlite:///", "")
            user_db_file = Path(user_db_path)

            # Create directory if it doesn't exist
            user_db_file.parent.mkdir(parents=True, exist_ok=True)

            # Create schema in user database
            logger.info(f"Initializing user database at {user_db_path}")
            Base.metadata.create_all(self.user_db_manager.get_engine())

            # Mark as initialized
            self._user_db_initialized = True
            logger.info("User database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize user database: {e}")
            raise DatabaseError(
                "Failed to initialize user database",
                details={"error": str(e)},
            )

    def get_engine(self, source: ContentSource = "system") -> Engine:
        """
        Get the appropriate database engine.

        Args:
            source: Which database to use ("system", "user", or "both")

        Returns:
            The SQLAlchemy engine instance

        Raises:
            ValueError: If source is "both" (engines can't be combined)
        """
        if source == "both":
            raise ValueError("Cannot get single engine for 'both' sources")

        if source == "user":
            self.initialize_user_database()
            return self.user_db_manager.get_engine()
        else:
            return self.system_db_manager.get_engine()

    @contextmanager
    def get_session(self, source: ContentSource = "system") -> Iterator[Session]:
        """
        Get a database session for the specified source.

        Args:
            source: Which database to use ("system", "user", or "both")

        Yields:
            A SQLAlchemy session

        Raises:
            ValueError: If source is "both" (use get_sessions instead)
        """
        if source == "both":
            raise ValueError("Use get_sessions() for accessing both databases")

        if source == "user":
            self.initialize_user_database()
            with self.user_db_manager.get_session() as session:
                yield session
        else:
            with self.system_db_manager.get_session() as session:
                yield session

    @contextmanager
    def get_sessions(self) -> Iterator[Tuple[Session, Session]]:
        """
        Get sessions for both databases.

        Yields:
            Tuple of (system_session, user_session)

        Note:
            Changes to system_session will be rolled back automatically
            since system DB is read-only.
        """
        self.initialize_user_database()

        with self.system_db_manager.get_session() as system_session:
            with self.user_db_manager.get_session() as user_session:
                yield system_session, user_session

    def dispose(self) -> None:
        """Dispose of both database connections."""
        try:
            self.system_db_manager.dispose()
            self.user_db_manager.dispose()
            logger.info("Dual database manager disposed successfully")
        except Exception as e:
            logger.error(f"Error disposing dual database manager: {e}")
            raise DatabaseError(
                "Failed to dispose dual database manager",
                details={"error": str(e)},
            )
