"""Tests for the ContentPackRepository."""

from datetime import datetime, timezone
from typing import Any, List
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.content.models import Base, ContentPack
from app.content.protocols import DatabaseManagerProtocol
from app.content.repositories.content_pack_repository import (
    SYSTEM_PACK_IDS,
    ContentPackRepository,
)
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    D5eContentPack,
)
from app.exceptions import (
    ContentPackNotFoundError,
    DatabaseError,
    DuplicateEntityError,
    ValidationError,
)


class TestContentPackRepository:
    """Test the ContentPackRepository class."""

    @pytest.fixture
    def database_manager(self) -> Mock:
        """Create a mock database manager."""
        manager = Mock(spec=DatabaseManagerProtocol)
        return manager

    @pytest.fixture
    def system_session(self) -> Mock:
        """Create a mock system database session."""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def user_session(self) -> Mock:
        """Create a mock user database session."""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def get_session_context(self, user_session: Mock) -> Mock:
        """Create a mock context manager for get_session()."""
        context = Mock()
        context.__enter__ = Mock(return_value=user_session)
        context.__exit__ = Mock(return_value=None)
        return context

    @pytest.fixture
    def get_sessions_context(self, system_session: Mock, user_session: Mock) -> Mock:
        """Create a mock context manager for get_sessions()."""
        context = Mock()
        context.__enter__ = Mock(return_value=(system_session, user_session))
        context.__exit__ = Mock(return_value=None)
        return context

    @pytest.fixture
    def repository(self, database_manager: Mock) -> ContentPackRepository:
        """Create a ContentPackRepository instance."""
        return ContentPackRepository(database_manager)

    @pytest.fixture
    def sample_content_pack(self) -> Mock:
        """Create a mock ContentPack entity."""
        pack = Mock(spec=ContentPack)
        pack.id = "test-pack"
        pack.name = "Test Pack"
        pack.description = "A test content pack"
        pack.version = "1.0.0"
        pack.author = "Test Author"
        pack.is_active = True
        pack.created_at = datetime.now(timezone.utc)
        pack.updated_at = datetime.now(timezone.utc)
        return pack

    @pytest.fixture
    def sample_d5e_content_pack(self) -> D5eContentPack:
        """Create a sample D5eContentPack model."""
        return D5eContentPack(
            id="test-pack",
            name="Test Pack",
            description="A test content pack",
            version="1.0.0",
            author="Test Author",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def test_get_all(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
        sample_d5e_content_pack: D5eContentPack,
    ) -> None:
        """Test getting all content packs."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context

        # Create a properly mocked entity that will work with model_validate
        entity = Mock()
        entity.id = "test-pack"
        entity.name = "Test Pack"
        entity.description = "A test content pack"
        entity.version = "1.0.0"
        entity.author = "Test Author"
        entity.is_active = True
        entity.created_at = datetime.now(timezone.utc)
        entity.updated_at = datetime.now(timezone.utc)

        # Mock the query chain for both sessions
        system_session.query.return_value.all.return_value = []
        user_session.query.return_value.all.return_value = [entity]

        # Execute
        result = repository.get_all()

        # Verify
        assert len(result) == 1
        assert result[0].id == "test-pack"
        assert result[0].name == "Test Pack"
        system_session.query.assert_called_once()
        user_session.query.assert_called_once()

    def test_get_all_active_only(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
        sample_d5e_content_pack: D5eContentPack,
    ) -> None:
        """Test getting only active content packs."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context

        # Create a properly mocked entity
        entity = Mock()
        entity.id = "test-pack"
        entity.name = "Test Pack"
        entity.description = "A test content pack"
        entity.version = "1.0.0"
        entity.author = "Test Author"
        entity.is_active = True
        entity.created_at = datetime.now(timezone.utc)
        entity.updated_at = datetime.now(timezone.utc)

        # Mock the query chain for both sessions
        system_mock_query = Mock()
        system_mock_filtered = Mock()
        system_mock_filtered.all.return_value = []
        system_mock_query.filter_by.return_value = system_mock_filtered
        system_session.query.return_value = system_mock_query

        user_mock_query = Mock()
        user_mock_filtered = Mock()
        user_mock_filtered.all.return_value = [entity]
        user_mock_query.filter_by.return_value = user_mock_filtered
        user_session.query.return_value = user_mock_query

        # Execute
        result = repository.get_all(active_only=True)

        # Verify
        assert len(result) == 1
        assert result[0].is_active is True
        system_mock_query.filter_by.assert_called_once_with(is_active=True)
        user_mock_query.filter_by.assert_called_once_with(is_active=True)

    def test_get_by_id_found(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
        sample_content_pack: ContentPack,
    ) -> None:
        """Test getting a content pack by ID when found."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context

        # Found in user DB
        user_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_content_pack
        )
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        # Execute
        result = repository.get_by_id("test-pack")

        # Verify
        assert result is not None
        assert result.id == "test-pack"

    def test_get_by_id_not_found(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
    ) -> None:
        """Test getting a content pack by ID when not found."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context

        # Not found in either DB
        user_session.query.return_value.filter_by.return_value.first.return_value = None
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        # Execute
        result = repository.get_by_id("non-existent")

        # Verify
        assert result is None

    def test_create_success(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
        get_session_context: Mock,
    ) -> None:
        """Test creating a new content pack."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context
        database_manager.get_session.return_value = get_session_context

        create_data = ContentPackCreate(
            id="new-pack",
            name="New Pack",
            description="A new content pack",
            version="1.0.0",
            author="Test Author",
        )

        # Not found in either DB during existence check
        user_session.query.return_value.filter_by.return_value.first.return_value = None
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        # Execute
        result = repository.create(create_data)

        # Verify
        assert result.id == "new_pack"  # ID is transformed to use underscores
        user_session.add.assert_called_once()
        user_session.commit.assert_called_once()

    def test_create_duplicate_id(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
        sample_content_pack: ContentPack,
    ) -> None:
        """Test creating a content pack with duplicate ID."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context

        create_data = ContentPackCreate(
            id="test-pack",
            name="Duplicate Pack",
            description="A duplicate content pack",
            version="1.0.0",
        )

        # Found in user DB
        user_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_content_pack
        )

        # Execute & Verify
        with pytest.raises(DuplicateEntityError):
            repository.create(create_data)

    def test_update_success(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
        sample_content_pack: ContentPack,
    ) -> None:
        """Test updating a content pack."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context

        # Found in user DB
        user_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_content_pack
        )
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        update_data = ContentPackUpdate(
            name="Updated Pack",
            description="Updated description",
        )

        # Execute
        result = repository.update("test-pack", update_data)

        # Verify
        assert result.name == "Updated Pack"
        assert result.description == "Updated description"
        user_session.commit.assert_called_once()

    def test_update_not_found(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
    ) -> None:
        """Test updating a non-existent content pack."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context

        # Not found in either DB
        user_session.query.return_value.filter_by.return_value.first.return_value = None
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        update_data = ContentPackUpdate(name="Updated Pack")

        # Execute & Verify
        with pytest.raises(ContentPackNotFoundError):
            repository.update("non-existent", update_data)

    def test_update_system_pack(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
    ) -> None:
        """Test that system packs cannot be deactivated."""
        # Setup
        system_pack = ContentPack(
            id="dnd_5e_srd",
            name="D&D 5e SRD",
            description="System pack",
            version="1.0.0",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        database_manager.get_sessions.return_value = get_sessions_context

        # Found in system DB (because it's a system pack)
        user_session.query.return_value.filter_by.return_value.first.return_value = None
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            system_pack
        )

        update_data = ContentPackUpdate(is_active=False)

        # Execute & Verify
        with pytest.raises(ValidationError) as exc_info:
            repository.update("dnd_5e_srd", update_data)
        assert "Cannot deactivate system pack" in str(exc_info.value)

    def test_delete_success(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_session_context: Mock,
        sample_content_pack: ContentPack,
    ) -> None:
        """Test deleting a content pack."""
        # Setup
        database_manager.get_session.return_value = get_session_context

        # Found in user DB
        user_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_content_pack
        )

        # Execute
        result = repository.delete("test-pack")

        # Verify
        assert result is True
        user_session.delete.assert_called_once_with(sample_content_pack)
        user_session.commit.assert_called_once()

    def test_delete_system_pack(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
    ) -> None:
        """Test that system packs cannot be deleted."""
        # Execute & Verify
        with pytest.raises(ValidationError) as exc_info:
            repository.delete("dnd_5e_srd")
        assert "Cannot delete system pack" in str(exc_info.value)

    def test_delete_not_found(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_session_context: Mock,
    ) -> None:
        """Test deleting a non-existent content pack."""
        # Setup
        database_manager.get_session.return_value = get_session_context

        # Not found in user DB
        user_session.query.return_value.filter_by.return_value.first.return_value = None

        # Also not found in system DB
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        # Execute & Verify
        with pytest.raises(ContentPackNotFoundError):
            repository.delete("non-existent")

    def test_get_content_statistics(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
        get_session_context: Mock,
        sample_d5e_content_pack: D5eContentPack,
    ) -> None:
        """Test getting content statistics for a pack."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context
        database_manager.get_session.return_value = get_session_context

        # Mock the get_by_id call - create properly mocked entity
        entity = Mock()
        entity.id = "test-pack"
        entity.name = "Test Pack"
        entity.description = "A test content pack"
        entity.version = "1.0.0"
        entity.author = "Test Author"
        entity.is_active = True
        entity.created_at = datetime.now(timezone.utc)
        entity.updated_at = datetime.now(timezone.utc)

        # Set up get_by_id to find in user DB
        user_session.query.return_value.filter_by.return_value.first.return_value = (
            entity
        )
        system_session.query.return_value.filter_by.return_value.first.return_value = (
            None
        )

        # Mock count queries - use side_effect to handle different model types
        count_query = Mock()
        count_query.filter_by.return_value.count.return_value = 5

        # Use side_effect to return appropriate mock for counting
        def query_side_effect(model: Any) -> Mock:
            # For get_by_id calls
            if model == ContentPack:
                mock_query = Mock()
                mock_query.filter_by.return_value.first.return_value = entity
                return mock_query
            # For all other entity count calls
            else:
                return count_query

        user_session.query.side_effect = query_side_effect

        # Execute
        result = repository.get_statistics("test-pack")

        # Verify
        assert result.id == "test-pack"
        assert result.statistics["spells"] == 5
        assert result.statistics["monsters"] == 5  # All counts return 5 in this mock

    def test_database_error_handling(
        self,
        repository: ContentPackRepository,
        database_manager: Mock,
        system_session: Mock,
        user_session: Mock,
        get_sessions_context: Mock,
    ) -> None:
        """Test that database errors are properly handled."""
        # Setup
        database_manager.get_sessions.return_value = get_sessions_context
        system_session.query.side_effect = SQLAlchemyError("Database connection failed")

        # Execute & Verify
        with pytest.raises(DatabaseError):
            repository.get_all()
