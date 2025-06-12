"""Tests for the database-aware base repository."""

from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, relationship, sessionmaker

from app.database.connection import DatabaseManager
from app.database.models import Base, BaseContent, ContentPack
from app.repositories.d5e.db_base_repository import BaseD5eDbRepository


# Test Pydantic model
class MockModel(BaseModel):
    """Simple test model for repository tests."""

    index: str
    name: str
    url: str
    description: Optional[str] = None


# Test SQLAlchemy entity
class MockTestEntity(BaseContent):
    """Test SQLAlchemy entity."""

    __tablename__ = "test_entities"

    description = Column(String(500))
    level = Column(Integer)  # Add level column for filter test
    # Add a mock relationship for testing
    content_pack = relationship("ContentPack", back_populates=None)


class MockTestRepository(BaseD5eDbRepository[MockModel]):
    """Test repository implementation."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        super().__init__(
            model_class=MockModel,
            entity_class=MockTestEntity,
            database_manager=database_manager,
        )


class TestBaseD5eDbRepository:
    """Test the base database repository."""

    def _create_column_mock(self, name: str) -> Mock:
        """Create a mock column with a name attribute."""
        col = Mock()
        col.name = name
        return col

    def _add_table_mock(self, entity: Mock) -> None:
        """Add a __table__ mock with columns to an entity."""
        entity.__table__ = Mock()
        entity.__table__.columns = [
            self._create_column_mock("index"),
            self._create_column_mock("name"),
            self._create_column_mock("url"),
            self._create_column_mock("description"),
            self._create_column_mock("level"),
            self._create_column_mock("content_pack_id"),
        ]

    @pytest.fixture
    def database_manager(self) -> Mock:
        """Create a mock database manager."""
        manager = Mock(spec=DatabaseManager)
        return manager

    @pytest.fixture
    def session(self) -> Mock:
        """Create a mock session."""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def context_manager(self, session: Mock) -> Mock:
        """Create a mock context manager for database sessions."""
        context = Mock()
        context.__enter__ = Mock(return_value=session)
        context.__exit__ = Mock(return_value=None)
        return context

    @pytest.fixture
    def repository(self, database_manager: Mock) -> MockTestRepository:
        """Create a test repository."""
        return MockTestRepository(database_manager)

    def test_get_by_index_with_active_content_pack(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting an entity by index from an active content pack."""
        # Setup
        entity = Mock(spec=MockTestEntity)
        entity.index = "test-spell"
        entity.name = "Test Spell"
        entity.url = "/api/spells/test-spell"
        entity.content_pack_id = "dnd_5e_srd"
        entity.description = "Test description"
        self._add_table_mock(entity)

        content_pack = Mock(spec=ContentPack)
        content_pack.id = "dnd_5e_srd"
        content_pack.is_active = True

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = entity

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Mock entity.content_pack relationship
        entity.content_pack = content_pack

        # Execute
        result = repository.get_by_index("test-spell")

        # Verify
        assert result is not None
        assert result.index == "test-spell"
        assert result.name == "Test Spell"

    def test_get_by_index_with_content_pack_priority(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting an entity by index with content pack priority."""
        # Setup
        entity = Mock(spec=MockTestEntity)
        entity.index = "fireball"
        entity.name = "Custom Fireball"
        entity.url = "/api/spells/fireball"
        entity.content_pack_id = "user_homebrew"
        entity.description = "Custom fireball description"
        self._add_table_mock(entity)

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = entity

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute with content pack priority
        result = repository.get_by_index_with_options(
            "fireball", content_pack_priority=["user_homebrew", "dnd_5e_srd"]
        )

        # Verify
        assert result is not None
        assert result.name == "Custom Fireball"

    def test_get_by_name_case_insensitive(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting an entity by name is case-insensitive."""
        # Setup
        entity = Mock(spec=MockTestEntity)
        entity.index = "magic-missile"
        entity.name = "Magic Missile"
        entity.url = "/api/spells/magic-missile"
        entity.content_pack_id = "dnd_5e_srd"
        entity.description = "Magic missile description"
        self._add_table_mock(entity)

        content_pack = Mock(spec=ContentPack)
        content_pack.id = "dnd_5e_srd"
        content_pack.is_active = True

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = entity

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Mock entity.content_pack relationship
        entity.content_pack = content_pack

        # Execute with different case
        result = repository.get_by_name("MAGIC MISSILE")

        # Verify
        assert result is not None
        assert result.name == "Magic Missile"

    def test_list_all_filters_inactive_packs(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test listing all entities filters out inactive content packs."""
        # Setup
        entity1 = Mock(spec=MockTestEntity)
        entity1.index = "spell1"
        entity1.name = "Spell 1"
        entity1.url = "/api/spells/spell1"
        entity1.description = "Description 1"

        self._add_table_mock(entity1)

        entity2 = Mock(spec=MockTestEntity)
        entity2.index = "spell2"
        entity2.name = "Spell 2"
        entity2.url = "/api/spells/spell2"
        entity2.description = "Description 2"

        self._add_table_mock(entity2)

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [entity1, entity2]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.list_all()

        # Verify
        assert len(results) == 2
        assert results[0].name == "Spell 1"
        assert results[1].name == "Spell 2"

    def test_search_case_insensitive(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test searching is case-insensitive."""
        # Setup
        entity = Mock(spec=MockTestEntity)
        entity.index = "fireball"
        entity.name = "Fireball"
        entity.url = "/api/spells/fireball"
        entity.description = "Fireball description"
        self._add_table_mock(entity)

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [entity]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.search("fire")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"

    def test_filter_by_field_values(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test filtering by field values."""
        # Setup
        entity = Mock(spec=MockTestEntity)
        entity.index = "fireball"
        entity.name = "Fireball"
        entity.url = "/api/spells/fireball"
        entity.description = "Fireball description"
        self._add_table_mock(entity)

        # Add level as a mock attribute
        entity.level = 3

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [entity]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.filter_by(level=3)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"

    def test_exists_returns_true_for_existing_entity(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test exists returns True for an existing entity."""
        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        result = repository.exists("fireball")

        # Verify
        assert result is True

    def test_exists_returns_false_for_nonexistent_entity(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test exists returns False for a non-existent entity."""
        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        result = repository.exists("nonexistent")

        # Verify
        assert result is False

    def test_count_returns_entity_count(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test count returns the total number of entities."""
        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 42

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        result = repository.count()

        # Verify
        assert result == 42

    def test_get_indices_returns_all_indices(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test get_indices returns all unique indices."""
        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [("fireball",), ("magic-missile",), ("shield",)]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_indices()

        # Verify
        assert len(results) == 3
        assert "fireball" in results
        assert "magic-missile" in results
        assert "shield" in results

    def test_get_names_returns_all_names(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test get_names returns all entity names."""
        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [("Fireball",), ("Magic Missile",), ("Shield",)]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_names()

        # Verify
        assert len(results) == 3
        assert "Fireball" in results
        assert "Magic Missile" in results
        assert "Shield" in results

    def test_content_pack_priority_fallback(
        self,
        repository: MockTestRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test content pack priority falls back to lower priority packs."""
        # Setup - entity only exists in second priority pack
        entity = Mock(spec=MockTestEntity)
        entity.index = "magic-missile"
        entity.name = "Magic Missile"
        entity.url = "/api/spells/magic-missile"
        entity.content_pack_id = "dnd_5e_srd"
        entity.description = "Magic missile description"
        self._add_table_mock(entity)

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock

        # First query returns None (not in user_homebrew)
        # Second query returns the entity (found in dnd_5e_srd)
        query_mock.first.side_effect = [None, entity]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute with content pack priority
        result = repository.get_by_index_with_options(
            "magic-missile", content_pack_priority=["user_homebrew", "dnd_5e_srd"]
        )

        # Verify
        assert result is not None
        assert result.name == "Magic Missile"
        # Verify it was called twice (once for each pack)
        assert query_mock.first.call_count == 2
