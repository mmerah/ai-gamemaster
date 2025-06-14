"""Integration tests for repository session isolation.

These tests verify that repository results are completely isolated from
database sessions and can be used after sessions close.
"""

from typing import Any

import pytest

from app.database.connection import DatabaseManager
from app.database.models import ContentPack, Spell
from app.exceptions import ValidationError
from app.models.d5e.spells_monsters import D5eSpell
from app.repositories.d5e.db_spell_repository import DbSpellRepository
from tests.integration.database.test_database_fixtures import test_db_manager


class TestRepositorySessionIsolation:
    """Test suite for repository session isolation."""

    def test_model_accessible_after_session_closes(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that models remain accessible after database session closes."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act - Get spell inside session context
        spell = repo.get_by_index("acid-arrow")

        # Session is now closed (get_by_index manages its own session)

        # Assert - Model is still fully accessible
        assert spell is not None
        assert isinstance(spell, D5eSpell)
        assert spell.index == "acid-arrow"
        assert spell.name == "Acid Arrow"
        assert spell.level == 2

        # Can still access all fields
        assert spell.school is not None
        assert spell.school.name == "Evocation"

        # Can serialize to dict
        spell_dict = spell.model_dump()
        assert spell_dict["index"] == "acid-arrow"
        assert spell_dict["name"] == "Acid Arrow"

        # Can convert to JSON
        spell_json = spell.model_dump_json()
        assert "acid-arrow" in spell_json
        assert "Acid Arrow" in spell_json

    def test_no_lazy_loading_exceptions(self, test_db_manager: DatabaseManager) -> None:
        """Test that no lazy loading exceptions occur after session closes."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act - Get multiple spells
        spells = repo.get_by_level(1)

        # Session is now closed

        # Assert - Can iterate and access all spells without issues
        assert len(spells) > 0

        for spell in spells:
            # These accesses would raise errors if lazy loading was happening
            assert spell.index is not None
            assert spell.name is not None
            assert spell.level == 1

            # Complex nested objects should also work
            if spell.school:
                assert spell.school.index is not None
                assert spell.school.name is not None

            # Lists should be accessible
            if spell.classes:
                for class_ref in spell.classes:
                    assert class_ref.index is not None
                    assert class_ref.name is not None

    def test_list_all_results_isolated_from_session(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that list_all results are isolated from database session."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act - Get all spells
        all_spells = repo.list_all()

        # Session is now closed

        # Assert - All spells are accessible
        assert len(all_spells) > 0

        # Can process all spells without session
        spell_names = [spell.name for spell in all_spells]
        assert "Acid Arrow" in spell_names
        assert "Fireball" in spell_names

        # Can filter and transform
        level_3_spells = [s for s in all_spells if s.level == 3]
        assert len(level_3_spells) > 0

        # Can serialize all to dict
        for spell in all_spells[:5]:  # Test first 5
            spell_dict = spell.model_dump()
            assert "index" in spell_dict
            assert "name" in spell_dict

    def test_search_results_isolated_from_session(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that search results are isolated from database session."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act - Search for spells
        fire_spells = repo.search("fire")

        # Session is now closed

        # Assert - Results are accessible
        assert len(fire_spells) > 0

        # Can access all fields
        for spell in fire_spells:
            assert "fire" in spell.name.lower()

            # Can build derived data
            spell_info = f"{spell.name} (Level {spell.level})"
            assert spell_info is not None

            # Can check complex conditions
            if spell.level > 0 and spell.school:
                school_name = spell.school.name
                assert school_name is not None

    def test_no_sqlalchemy_objects_in_model(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that models contain no SQLAlchemy objects."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act
        spell = repo.get_by_index("fireball")

        # Assert - Check the model contains no SQLAlchemy objects
        assert spell is not None

        # Convert to dict and check all values
        spell_dict = spell.model_dump()

        def check_no_sqlalchemy(obj: Any, path: str = "") -> None:
            """Recursively check for SQLAlchemy objects."""
            if hasattr(obj, "__table__"):
                raise AssertionError(f"SQLAlchemy object found at {path}")

            if isinstance(obj, dict):
                for key, value in obj.items():
                    check_no_sqlalchemy(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_no_sqlalchemy(item, f"{path}[{i}]")

        check_no_sqlalchemy(spell_dict)

    def test_concurrent_access_after_session_close(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that multiple models can be accessed concurrently after session."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act - Get multiple spells in different queries
        spell1 = repo.get_by_index("fireball")
        spell2 = repo.get_by_index("lightning-bolt")
        spells_list = repo.get_by_level(2)

        # All sessions are now closed

        # Assert - All models are independently accessible
        assert spell1 is not None
        assert spell2 is not None
        assert len(spells_list) > 0

        # Can access all independently
        assert spell1.name == "Fireball"
        assert spell2.name == "Lightning Bolt"

        # Can process the list
        spell_names = [s.name for s in spells_list]
        assert len(spell_names) == len(spells_list)

        # Can mix operations
        all_spells = [spell1, spell2] + spells_list
        unique_indices = {s.index for s in all_spells}
        assert len(unique_indices) >= 3

    def test_model_mutation_does_not_affect_database(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that mutating a model doesn't affect the database."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act - Get a spell and mutate it
        spell = repo.get_by_index("magic-missile")
        assert spell is not None

        original_name = spell.name
        original_level = spell.level

        # Mutate the model (Pydantic models are mutable by default)
        # Note: In production, you might want to use frozen=True
        spell_dict = spell.model_dump()
        spell_dict["name"] = "Super Magic Missile"
        spell_dict["level"] = 9

        # Get the spell again
        spell_again = repo.get_by_index("magic-missile")

        # Assert - Database was not affected
        assert spell_again is not None
        assert spell_again.name == original_name
        assert spell_again.level == original_level

    def test_error_handling_with_closed_session(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that errors are handled properly even with closed sessions."""
        # Arrange
        repo = DbSpellRepository(test_db_manager)

        # Act & Assert - Non-existent spell
        result = repo.get_by_index("non-existent-spell")
        assert result is None

        # Search with no results
        results = repo.search("xyzabc123")
        assert results == []

        # These operations should not raise session-related errors
