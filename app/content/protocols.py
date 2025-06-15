"""Protocol definitions for content module interfaces."""

from contextlib import contextmanager
from typing import Iterator, Literal, Protocol, Tuple, runtime_checkable

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

ContentSource = Literal["system", "user", "both"]


@runtime_checkable
class DatabaseManagerProtocol(Protocol):
    """Protocol for database manager implementations.

    This protocol defines the interface that both DatabaseManager and
    DualDatabaseManager must implement, allowing them to be used
    interchangeably in the codebase.
    """

    @contextmanager
    def get_session(self, source: ContentSource = "system") -> Iterator[Session]:
        """Get a database session.

        Args:
            source: The content source to get a session for.
                   For single database, this parameter is ignored.
                   For dual database, specifies which database to use.

        Yields:
            Session: A SQLAlchemy session for the requested source.
        """
        ...

    @contextmanager
    def get_sessions(self) -> Iterator[Tuple[Session, Session]]:
        """Get sessions for both system and user databases.

        For single database, returns the same session twice.
        For dual database, returns (system_session, user_session).

        Yields:
            Tuple of (system_session, user_session).
        """
        ...

    def get_engine(self, source: ContentSource = "system") -> Engine:
        """Get the SQLAlchemy engine.

        Args:
            source: The content source to get an engine for.
                   For single database, this parameter is ignored.
                   For dual database, specifies which engine to return.

        Returns:
            Engine: The SQLAlchemy engine for the requested source.
        """
        ...

    def dispose(self) -> None:
        """Dispose of all database connections."""
        ...
