"""Tests for exception handling in repositories."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.content.connection import DatabaseManager
from app.content.models import Spell
from app.content.repositories.db_base_repository import BaseD5eDbRepository
from app.content.repositories.db_spell_repository import DbSpellRepository
from app.content.schemas import D5eSpell
from app.exceptions import DatabaseError, SessionError, ValidationError


class TestBaseRepositoryExceptions:
    """Test exception handling in base repository."""

    def test_get_session_no_active_session(self) -> None:
        """Test _get_session raises SessionError when no session is active."""
        db_manager = Mock(spec=DatabaseManager)
        repo = BaseD5eDbRepository(D5eSpell, Spell, db_manager)

        with pytest.raises(SessionError) as exc_info:
            repo._get_session()

        assert "No active database session" in str(exc_info.value)

    def test_entity_to_model_validation_error(self) -> None:
        """Test _entity_to_model raises ValidationError on invalid data."""
        db_manager = Mock(spec=DatabaseManager)
        repo = BaseD5eDbRepository(D5eSpell, Spell, db_manager)

        # Create a mock entity with invalid data
        entity = Mock()
        entity.__table__ = Mock()
        entity.__table__.columns = []
        entity.index = "test-spell"
        entity.name = "Test Spell"

        # Mock the model class to raise an exception
        with patch.object(repo, "_model_class") as mock_model:
            mock_model.side_effect = ValueError("Invalid spell data")
            mock_model.__name__ = "D5eSpell"

            with pytest.raises(ValidationError) as exc_info:
                repo._entity_to_model(entity)

            assert "Failed to validate D5eSpell 'Test Spell'" in str(exc_info.value)
            assert exc_info.value.details["field"] == "entity"
            assert exc_info.value.details["value"] == "test-spell"

    def test_get_by_index_database_error(self) -> None:
        """Test get_by_index raises DatabaseError on SQLAlchemy error."""
        db_manager = Mock(spec=DatabaseManager)
        repo = BaseD5eDbRepository(D5eSpell, Spell, db_manager)

        # Mock the database session to raise an error
        mock_session = MagicMock()
        mock_session.query.side_effect = SQLAlchemyError("Connection lost")

        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        db_manager.get_session.return_value = mock_context

        with pytest.raises(DatabaseError) as exc_info:
            repo.get_by_index("fireball")

        assert "Failed to retrieve D5eSpell by index" in str(exc_info.value)
        assert exc_info.value.details["index"] == "fireball"
        assert "Connection lost" in exc_info.value.details["error"]

    def test_list_all_partial_validation_errors(self) -> None:
        """Test list_all continues processing when some entities fail validation."""
        db_manager = Mock(spec=DatabaseManager)
        repo = BaseD5eDbRepository(D5eSpell, Spell, db_manager)

        # Create mock entities, one valid and one invalid
        valid_entity = Mock()
        valid_entity.index = "valid-spell"

        invalid_entity = Mock()
        invalid_entity.index = "invalid-spell"

        # Mock the session
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.all.return_value = [valid_entity, invalid_entity]

        # Mock content pack filter
        with patch.object(repo, "_apply_content_pack_filter") as mock_filter:
            mock_filter.return_value = mock_query

            # Mock entity conversion
            def mock_entity_to_model(entity: Mock) -> D5eSpell:
                if entity.index == "invalid-spell":
                    raise ValidationError("Invalid spell data")
                return Mock(spec=D5eSpell)

            repo._entity_to_model = mock_entity_to_model  # type: ignore[assignment]

            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_session
            db_manager.get_session.return_value = mock_context

            # Should return only the valid entity
            results = repo.list_all()
            assert len(results) == 1

    def test_filter_by_invalid_field(self) -> None:
        """Test filter_by raises ValidationError for invalid field."""
        db_manager = Mock(spec=DatabaseManager)
        repo = BaseD5eDbRepository(D5eSpell, Spell, db_manager)

        # Mock the session
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        db_manager.get_session.return_value = mock_context

        # Mock the entity class to not have the field
        # hasattr will return False for 'invalid_field'
        mock_entity_class = Mock(spec=["index", "name"])  # Specify only valid fields
        repo._entity_class = mock_entity_class

        with pytest.raises(ValidationError) as exc_info:
            repo.filter_by(invalid_field="value")

        assert "Invalid filter field 'invalid_field'" in str(exc_info.value)
        assert exc_info.value.details["field"] == "invalid_field"

    def test_count_database_error(self) -> None:
        """Test count raises DatabaseError on SQLAlchemy error."""
        db_manager = Mock(spec=DatabaseManager)
        repo = BaseD5eDbRepository(D5eSpell, Spell, db_manager)

        # Mock the database session to raise an error
        mock_session = MagicMock()
        mock_session.query.side_effect = SQLAlchemyError("Operational error occurred")

        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        db_manager.get_session.return_value = mock_context

        with pytest.raises(DatabaseError) as exc_info:
            repo.count()

        assert "Failed to count D5eSpell entities" in str(exc_info.value)


class TestSpellRepositoryExceptions:
    """Test exception handling in spell repository."""

    def test_get_by_school_database_error(self) -> None:
        """Test get_by_school raises DatabaseError on SQLAlchemy error."""
        db_manager = Mock(spec=DatabaseManager)
        repo = DbSpellRepository(db_manager)

        # Mock the database session to raise an error
        mock_session = MagicMock()
        mock_session.query.side_effect = SQLAlchemyError("Query failed")

        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        db_manager.get_session.return_value = mock_context

        with pytest.raises(DatabaseError) as exc_info:
            repo.get_by_school("evocation")

        assert "Failed to get spells by school" in str(exc_info.value)
        assert exc_info.value.details["school_index"] == "evocation"

    def test_get_by_class_list_all_error(self) -> None:
        """Test get_by_class handles errors from list_all_with_options."""
        db_manager = Mock(spec=DatabaseManager)
        repo = DbSpellRepository(db_manager)

        # Mock list_all_with_options to raise an error
        with patch.object(repo, "list_all_with_options") as mock_list:
            mock_list.side_effect = DatabaseError("Failed to list spells")

            with pytest.raises(DatabaseError) as exc_info:
                repo.get_by_class("wizard")

            assert "Failed to get spells by class" in str(exc_info.value)
            assert exc_info.value.details["class_index"] == "wizard"


class TestDatabaseConnectionExceptions:
    """Test exception handling in database connection."""

    def test_invalid_database_url(self) -> None:
        """Test ConnectionError raised for invalid database URL."""
        from app.exceptions import ConnectionError

        with pytest.raises(ConnectionError) as exc_info:
            DatabaseManager("invalid://url", echo=False)

        assert "Invalid database URL format" in str(exc_info.value)

    def test_create_engine_failure(self) -> None:
        """Test ConnectionError raised when engine creation fails."""
        from app.exceptions import ConnectionError

        with patch("app.content.connection.create_engine") as mock_create:
            mock_create.side_effect = SQLAlchemyError("Failed to create engine")

            db_manager = DatabaseManager("sqlite:///test.db")

            with pytest.raises(ConnectionError) as exc_info:
                db_manager.get_engine()

            assert "Failed to create database engine" in str(exc_info.value)

    def test_session_sqlalchemy_error(self) -> None:
        """Test SessionError raised on SQLAlchemy errors in session."""
        db_manager = DatabaseManager("sqlite:///test.db")

        # Mock the session factory
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")

        mock_factory = Mock(return_value=mock_session)

        with patch.object(
            db_manager, "_create_session_factory", return_value=mock_factory
        ):
            with pytest.raises(SessionError) as exc_info:
                with db_manager.get_session():
                    pass  # Session should fail on commit

            assert "Database session failed" in str(exc_info.value)
            assert mock_session.rollback.called

    def test_dispose_error(self) -> None:
        """Test DatabaseError raised when disposal fails."""
        db_manager = DatabaseManager("sqlite:///test.db")

        # Create a mock engine
        mock_engine = Mock()
        mock_engine.dispose.side_effect = Exception("Disposal failed")
        db_manager._engine = mock_engine

        with pytest.raises(DatabaseError) as exc_info:
            db_manager.dispose()

        assert "Failed to dispose database engine" in str(exc_info.value)
