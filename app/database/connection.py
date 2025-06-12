"""
Database connection and session management using SQLAlchemy.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions using SQLAlchemy."""

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_config: Optional[Dict[str, Any]] = None,
        enable_sqlite_vec: bool = False,
    ) -> None:
        """
        Initialize the DatabaseManager.

        Args:
            database_url: SQLAlchemy database URL (e.g., "sqlite:///data/content.db")
            echo: If True, log all SQL statements
            pool_config: Optional connection pool configuration
            enable_sqlite_vec: If True, attempt to load sqlite-vec extension
        """
        if not database_url or not database_url.startswith(
            ("sqlite://", "postgresql://")
        ):
            raise ValueError(f"Invalid database URL: {database_url}")

        self.database_url = database_url
        self._echo = echo
        self._pool_config = pool_config or {}
        self._enable_sqlite_vec = enable_sqlite_vec
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

            self._engine = create_engine(self.database_url, **engine_kwargs)

            # If sqlite-vec is enabled and we're using SQLite, load the extension
            if self._enable_sqlite_vec and self.database_url.startswith("sqlite://"):
                self._load_sqlite_vec_extension(self._engine)

            logger.info(f"Created database engine for: {self.database_url}")

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
        """
        if self._engine is not None:
            self._engine.dispose()
            # Reset the engine so it gets recreated on next access
            self._engine = None
            self._session_factory = None
            logger.info("Disposed database engine and closed all connections")
