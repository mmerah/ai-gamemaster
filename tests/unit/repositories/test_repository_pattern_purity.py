"""Tests to ensure repository pattern purity and no SQLAlchemy leaks.

These tests verify that:
1. Repositories only return Pydantic models, never SQLAlchemy entities
2. Models can be used outside of database session context
3. No lazy loading exceptions occur after session closes
4. Field mapping cache improves performance
"""

import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pydantic import BaseModel
from sqlalchemy import Column, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base

from app.database.connection import DatabaseManager
from app.database.models import Spell
from app.exceptions import ValidationError
from app.models.d5e.spells_monsters import D5eSpell
from app.repositories.d5e.db_base_repository import BaseD5eDbRepository
from app.repositories.d5e.db_spell_repository import DbSpellRepository

# Create a test base for mock entities
Base = declarative_base()


class MockEntity(Base):  # type: ignore[misc, valid-type]
    """Mock SQLAlchemy entity for testing."""

    __tablename__ = "mock_entities"

    index = Column(String, primary_key=True)
    name = Column(String)
    content_pack_id = Column(String)

    # Simulate a relationship that would cause lazy loading
    related_items = None  # This would normally be a relationship()


class MockModel(BaseModel):
    """Mock Pydantic model for testing."""

    index: str
    name: str


def create_mock_entity(
    index: str, name: str, content_pack_id: str = "srd"
) -> MagicMock:
    """Helper to create a properly mocked SQLAlchemy entity."""
    mock_entity = MagicMock()
    mock_table = MagicMock()
    mock_columns = []

    # Create proper column mocks
    for col_name in ["index", "name", "content_pack_id"]:
        col = MagicMock()
        col.name = col_name
        mock_columns.append(col)

    mock_table.columns = mock_columns
    mock_entity.__table__ = mock_table

    # Set column values
    mock_entity.index = index
    mock_entity.name = name
    mock_entity.content_pack_id = content_pack_id

    return mock_entity


class TestRepositoryPatternPurity:
    """Test suite for repository pattern purity."""

    def test_repository_returns_pydantic_model_not_sqlalchemy(self) -> None:
        """Test that repositories return Pydantic models, not SQLAlchemy entities."""
        # Arrange
        mock_db = MagicMock(spec=DatabaseManager)
        mock_session = MagicMock(spec=Session)
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        # Create a mock SQLAlchemy entity
        mock_entity = create_mock_entity("test-123", "Test Entity")

        # Mock the query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_entity

        # Create repository
        repo = BaseD5eDbRepository(
            model_class=MockModel,
            entity_class=MockEntity,
            database_manager=mock_db,
        )

        # Act
        result = repo.get_by_index("test-123")

        # Assert
        assert result is not None
        assert isinstance(result, MockModel)
        assert not isinstance(result, MockEntity)
        assert result.index == "test-123"
        assert result.name == "Test Entity"
        # Verify content_pack_id was filtered out
        assert not hasattr(result, "content_pack_id")

    def test_sqlalchemy_objects_in_columns_are_detected(self) -> None:
        """Test that SQLAlchemy objects in columns are detected and skipped."""
        # Arrange
        mock_db = MagicMock(spec=DatabaseManager)
        mock_session = MagicMock(spec=Session)
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        # Create a mock entity with a SQLAlchemy object in a column
        mock_entity = MagicMock()
        mock_table = MagicMock()
        mock_columns = []

        # Create proper column mocks
        for col_name in ["index", "name", "related_entity", "content_pack_id"]:
            col = MagicMock()
            col.name = col_name
            mock_columns.append(col)

        mock_table.columns = mock_columns
        mock_entity.__table__ = mock_table

        # Create a mock related entity (SQLAlchemy object)
        mock_related = MagicMock()
        mock_related.__table__ = MagicMock()  # This marks it as a SQLAlchemy object

        # Set column values
        mock_entity.index = "test-123"
        mock_entity.name = "Test Entity"
        mock_entity.related_entity = mock_related  # SQLAlchemy object!
        mock_entity.content_pack_id = "srd"

        # Mock the query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_entity

        # Create repository
        repo = BaseD5eDbRepository(
            model_class=MockModel,
            entity_class=MockEntity,
            database_manager=mock_db,
        )

        # Act & Assert
        # The repository should handle this gracefully
        result = repo.get_by_index("test-123")
        assert result is not None
        assert not hasattr(result, "related_entity")

    def test_model_usable_outside_session_context(self) -> None:
        """Test that returned models are usable after session closes."""
        # Arrange
        mock_db = MagicMock(spec=DatabaseManager)
        mock_session = MagicMock(spec=Session)
        session_closed = False

        def close_session() -> None:
            nonlocal session_closed
            session_closed = True

        mock_session.close = close_session
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db.get_session.return_value.__exit__ = lambda *args: close_session()

        # Create a mock entity
        mock_entity = create_mock_entity("test-123", "Test Entity")

        # Mock the query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_entity

        # Create repository
        repo = BaseD5eDbRepository(
            model_class=MockModel,
            entity_class=MockEntity,
            database_manager=mock_db,
        )

        # Act
        result = repo.get_by_index("test-123")

        # Assert session was closed
        assert session_closed

        # Assert model is still usable
        assert result is not None
        assert result.index == "test-123"
        assert result.name == "Test Entity"

        # Can serialize to dict without issues
        model_dict = result.model_dump()
        assert model_dict["index"] == "test-123"
        assert model_dict["name"] == "Test Entity"

    def test_field_mapping_cache_performance(self) -> None:
        """Test that field mapping cache improves performance."""
        # Arrange
        mock_db = MagicMock(spec=DatabaseManager)

        # Clear any existing cache
        BaseD5eDbRepository._field_mapping_cache.clear()
        BaseD5eDbRepository._json_fields_cache.clear()

        # Create multiple repositories of the same type
        _ = BaseD5eDbRepository(
            model_class=MockModel,
            entity_class=MockEntity,
            database_manager=mock_db,
        )

        # Measure time for second initialization (should use cache)
        start_time = time.time()
        _ = BaseD5eDbRepository(
            model_class=MockModel,
            entity_class=MockEntity,
            database_manager=mock_db,
        )
        cached_time = time.time() - start_time

        # Assert cache was populated
        assert MockModel in BaseD5eDbRepository._field_mapping_cache
        assert MockModel in BaseD5eDbRepository._json_fields_cache

        # Cache initialization should be very fast
        assert cached_time < 0.001  # Less than 1ms

    def test_validate_model_purity_method(self) -> None:
        """Test the _validate_model_purity safety check method."""
        # Arrange
        mock_db = MagicMock(spec=DatabaseManager)
        repo = BaseD5eDbRepository(
            model_class=MockModel,
            entity_class=MockEntity,
            database_manager=mock_db,
        )

        # Test with clean model
        clean_model = MockModel(index="test-123", name="Test")
        result = repo._validate_model_purity(clean_model)
        assert result == clean_model

        # Test with model containing SQLAlchemy object (simulated)
        # Create a mock that simulates model_dump returning a SQLAlchemy object
        mock_model = MagicMock()
        mock_sqlalchemy_obj = MagicMock()
        mock_sqlalchemy_obj.__table__ = MagicMock()

        # Make model_dump return a dict with a SQLAlchemy object
        mock_model.model_dump.return_value = {
            "index": "test-123",
            "name": "Test",
            "leaked_field": mock_sqlalchemy_obj,
        }

        with pytest.raises(ValidationError) as exc_info:
            repo._validate_model_purity(mock_model)

        assert "SQLAlchemy object leaked" in str(exc_info.value)
        assert "leaked_field" in str(exc_info.value)

    def test_spell_repository_pattern_purity(self) -> None:
        """Test that specialized repositories like SpellRepository maintain purity."""
        # Arrange
        mock_db = MagicMock(spec=DatabaseManager)
        mock_session = MagicMock(spec=Session)
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        # Create a mock spell entity
        mock_spell = MagicMock()
        mock_table = MagicMock()
        mock_columns = []

        # Define all spell columns
        spell_columns = [
            "index",
            "name",
            "level",
            "school",
            "content_pack_id",
            "desc",
            "higher_level",
            "range",
            "components",
            "material",
            "ritual",
            "duration",
            "concentration",
            "casting_time",
            "attack_type",
            "damage",
            "dc",
            "area_of_effect",
            "heal_at_slot_level",
            "classes",
            "subclasses",
            "url",
        ]

        # Create proper column mocks
        for col_name in spell_columns:
            col = MagicMock()
            col.name = col_name
            mock_columns.append(col)

        mock_table.columns = mock_columns
        mock_spell.__table__ = mock_table

        # Set values
        mock_spell.index = "fireball"
        mock_spell.name = "Fireball"
        mock_spell.level = 3
        mock_spell.school = {
            "index": "evocation",
            "name": "Evocation",
            "url": "/api/magic-schools/evocation",
        }
        mock_spell.content_pack_id = "srd"

        # Set required fields with appropriate values
        # Set as actual Python objects since _parse_json_fields will handle them
        mock_spell.desc = ["A bright streak flashes from your pointing finger..."]
        mock_spell.higher_level = None
        mock_spell.range = "150 feet"
        mock_spell.components = ["V", "S", "M"]
        mock_spell.material = "A tiny ball of bat guano and sulfur"
        mock_spell.ritual = False
        mock_spell.duration = "Instantaneous"
        mock_spell.concentration = False
        mock_spell.casting_time = "1 action"
        mock_spell.attack_type = None
        mock_spell.damage = None
        mock_spell.dc = None
        mock_spell.area_of_effect = None
        mock_spell.heal_at_slot_level = None
        mock_spell.classes = []
        mock_spell.subclasses = []
        mock_spell.url = "/api/spells/fireball"

        # Mock the query chain for get_by_level
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_spell]

        # Create spell repository
        repo = DbSpellRepository(mock_db)

        # Act
        results = repo.get_by_level(3)

        # Assert
        assert len(results) == 1
        spell = results[0]
        assert isinstance(spell, D5eSpell)
        assert not hasattr(spell, "__table__")
        assert spell.index == "fireball"
        assert spell.name == "Fireball"
        assert spell.level == 3

    def test_list_all_with_validation_errors(self) -> None:
        """Test that list_all continues processing even with validation errors."""
        # Arrange
        mock_db = MagicMock(spec=DatabaseManager)
        mock_session = MagicMock(spec=Session)
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        # Create mock entities, one valid and one invalid
        valid_entity = create_mock_entity("valid-123", "Valid Entity")

        invalid_entity = MagicMock()
        mock_table = MagicMock()
        mock_columns = []

        # Create proper column mocks
        for col_name in ["index", "name", "content_pack_id"]:
            col = MagicMock()
            col.name = col_name
            mock_columns.append(col)

        mock_table.columns = mock_columns
        invalid_entity.__table__ = mock_table

        invalid_entity.index = None  # This will cause validation error
        invalid_entity.name = "Invalid Entity"
        invalid_entity.content_pack_id = "srd"

        # Mock query to return both entities
        mock_query = MagicMock()
        mock_query.all.return_value = [invalid_entity, valid_entity]
        mock_session.query.return_value = mock_query

        # Mock join for content pack filtering
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Create repository
        repo = BaseD5eDbRepository(
            model_class=MockModel,
            entity_class=MockEntity,
            database_manager=mock_db,
        )

        # Act
        results = repo.list_all()

        # Assert - should have processed the valid entity
        assert len(results) == 1
        assert results[0].index == "valid-123"
        assert results[0].name == "Valid Entity"
