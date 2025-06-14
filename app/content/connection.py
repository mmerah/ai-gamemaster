"""
Database connection and session management using SQLAlchemy.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.exceptions import ConnectionError, DatabaseError, SessionError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions using SQLAlchemy."""

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_config: Optional[Dict[str, Any]] = None,
        enable_sqlite_vec: bool = False,
        sqlite_busy_timeout: Optional[int] = None,
    ) -> None:
        """
        Initialize the DatabaseManager.

        Args:
            database_url: SQLAlchemy database URL (e.g., "sqlite:///data/content.db")
            echo: If True, log all SQL statements
            pool_config: Optional connection pool configuration
            enable_sqlite_vec: If True, attempt to load sqlite-vec extension
            sqlite_busy_timeout: SQLite busy timeout in milliseconds (default: 5000)
        """
        if not database_url or not database_url.startswith(
            ("sqlite://", "postgresql://")
        ):
            raise ConnectionError(
                "Invalid database URL format",
                details={"url_prefix": database_url[:20] if database_url else None},
            )

        self.database_url = database_url
        self._echo = echo
        self._pool_config = pool_config or {}
        self._enable_sqlite_vec = enable_sqlite_vec
        self._sqlite_busy_timeout = sqlite_busy_timeout or 5000
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker[Session]] = None

    def get_engine(self) -> Engine:
        """
        Get or create the SQLAlchemy engine.

        Returns:
            The SQLAlchemy engine instance
        """
        if self._engine is None:
            # Create engine with configuration
            engine_kwargs: Dict[str, Any] = {
                "echo": self._echo,
                **self._pool_config,
            }

            # For SQLite, we need special configuration
            if self.database_url.startswith("sqlite://"):
                engine_kwargs.update(
                    {
                        "connect_args": {"check_same_thread": False},
                        "pool_pre_ping": True,
                    }
                )

            try:
                self._engine = create_engine(self.database_url, **engine_kwargs)

                # Configure SQLite-specific settings
                if self.database_url.startswith("sqlite://"):
                    self._configure_sqlite_pragmas(self._engine)

                    # Load sqlite-vec extension if enabled
                    if self._enable_sqlite_vec:
                        self._load_sqlite_vec_extension(self._engine)

                logger.info(
                    "Created database engine",
                    extra={
                        "database_type": "sqlite"
                        if self.database_url.startswith("sqlite://")
                        else "postgresql",
                        "echo": self._echo,
                        "sqlite_vec_enabled": self._enable_sqlite_vec,
                    },
                )
            except SQLAlchemyError as e:
                logger.error(
                    f"Failed to create database engine: {e}",
                    exc_info=True,
                    extra={"database_url": self.database_url, "error": str(e)},
                )
                raise ConnectionError(
                    "Failed to create database engine",
                    details={"error": str(e)},
                )

        return self._engine

    def _load_sqlite_vec_extension(self, engine: Engine) -> None:
        """
        Load the sqlite-vec extension for vector operations.

        Args:
            engine: The SQLAlchemy engine
        """

        try:
            import sqlite_vec
        except ImportError:
            logger.warning(
                "sqlite-vec Python package not installed. "
                "Vector search will use fallback implementation. "
                "Install with: pip install sqlite-vec"
            )
            return

        @event.listens_for(engine, "connect")
        def load_extension(dbapi_conn: Any, connection_record: Any) -> None:
            """Load sqlite-vec extension on each connection."""
            try:
                # Enable extension loading
                dbapi_conn.enable_load_extension(True)

                # Use the sqlite-vec Python package to load the extension
                sqlite_vec.load(dbapi_conn)

                logger.info("Successfully loaded sqlite-vec extension")
            except Exception as e:
                logger.warning(f"Could not load sqlite-vec extension: {e}")
                # Don't fail if extension isn't available
            finally:
                # Disable extension loading for security
                try:
                    dbapi_conn.enable_load_extension(False)
                except Exception:
                    pass

    def _configure_sqlite_pragmas(self, engine: Engine) -> None:
        """
        Configure SQLite pragmas for optimal performance and concurrency.

        Args:
            engine: The SQLAlchemy engine
        """

        @event.listens_for(engine, "connect")
        def configure_sqlite_pragmas(dbapi_conn: Any, connection_record: Any) -> None:
            """Configure SQLite pragmas on each connection."""
            try:
                cursor = dbapi_conn.cursor()

                # Enable Write-Ahead Logging for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")

                # Set busy timeout to wait for locks (in milliseconds)
                cursor.execute(f"PRAGMA busy_timeout={self._sqlite_busy_timeout}")

                # Set synchronous mode to NORMAL for better performance
                # while maintaining durability
                cursor.execute("PRAGMA synchronous=NORMAL")

                cursor.close()

                logger.info(
                    "Configured SQLite pragmas: WAL mode enabled, "
                    f"busy_timeout={self._sqlite_busy_timeout}ms, synchronous=NORMAL"
                )
            except Exception as e:
                logger.warning(
                    f"Could not configure SQLite pragmas: {e}",
                    extra={
                        "busy_timeout": self._sqlite_busy_timeout,
                        "error": str(e),
                    },
                )
                # Don't fail if pragmas can't be set

    def _create_session_factory(self) -> sessionmaker[Session]:
        """
        Create the session factory.

        Returns:
            A sessionmaker instance
        """
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.get_engine(),
                expire_on_commit=False,
            )
        return self._session_factory

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """
        Get a database session as a context manager.

        Yields:
            A SQLAlchemy session that auto-commits on success and rollbacks on exception

        Example:
            with db_manager.get_session() as session:
                session.query(Model).all()
        """
        session_factory = self._create_session_factory()
        session = session_factory()

        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(
                f"Database session error: {e}",
                exc_info=True,
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise SessionError(
                "Database session failed",
                details={"error": str(e)},
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all_tables(self, metadata: MetaData) -> None:
        """
        Create all tables defined in the metadata.

        Args:
            metadata: SQLAlchemy MetaData object containing table definitions
        """
        metadata.create_all(self.get_engine())
        logger.info("Created all database tables")

    def dispose(self) -> None:
        """
        Dispose of the connection pool and close all connections.

        This should be called when shutting down the application.

        Raises:
            DatabaseError: If disposal fails
        """
        if self._engine is not None:
            try:
                self._engine.dispose()
                # Reset the engine so it gets recreated on next access
                self._engine = None
                self._session_factory = None
                logger.info(
                    "Database engine disposed",
                    extra={"database_url": self.database_url},
                )
            except Exception as e:
                logger.error(
                    f"Error disposing database engine: {e}",
                    exc_info=True,
                    extra={"error": str(e)},
                )
                raise DatabaseError(
                    "Failed to dispose database engine",
                    details={"error": str(e)},
                )
