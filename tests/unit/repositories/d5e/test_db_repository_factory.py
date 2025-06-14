"""Tests for the database-backed repository factory."""

from unittest.mock import Mock

import pytest

from app.database.connection import DatabaseManager
from app.repositories.d5e.db_base_repository import BaseD5eDbRepository
from app.repositories.d5e.db_class_repository import DbClassRepository
from app.repositories.d5e.db_equipment_repository import DbEquipmentRepository
from app.repositories.d5e.db_monster_repository import DbMonsterRepository
from app.repositories.d5e.db_repository_factory import D5eDbRepositoryFactory
from app.repositories.d5e.db_spell_repository import DbSpellRepository


class TestD5eDbRepositoryFactory:
    """Test the database-backed repository factory."""

    @pytest.fixture
    def database_manager(self) -> Mock:
        """Create a mock database manager."""
        return Mock(spec=DatabaseManager)

    @pytest.fixture
    def factory(self, database_manager: Mock) -> D5eDbRepositoryFactory:
        """Create a test factory."""
        return D5eDbRepositoryFactory(database_manager)

    def test_factory_initializes_all_repositories(
        self, factory: D5eDbRepositoryFactory
    ) -> None:
        """Test that factory creates all 25 repositories on initialization."""
        categories = factory.get_all_categories()

        # Should have exactly 25 categories
        assert len(categories) == 25

        # Check specific categories exist
        expected_categories = [
            "ability-scores",
            "alignments",
            "backgrounds",
            "classes",
            "conditions",
            "damage-types",
            "equipment",
            "equipment-categories",
            "feats",
            "features",
            "languages",
            "levels",
            "magic-items",
            "magic-schools",
            "monsters",
            "proficiencies",
            "races",
            "rules",
            "rule-sections",
            "skills",
            "spells",
            "subclasses",
            "subraces",
            "traits",
            "weapon-properties",
        ]

        for category in expected_categories:
            assert category in categories

    def test_get_repository_by_category(self, factory: D5eDbRepositoryFactory) -> None:
        """Test getting repositories by category name."""
        # Test getting a generic repository
        skills_repo = factory.get("skills")
        assert isinstance(skills_repo, BaseD5eDbRepository)

        # Test getting a specialized repository
        spells_repo = factory.get("spells")
        assert isinstance(spells_repo, DbSpellRepository)

    def test_get_unknown_category_raises_error(
        self, factory: D5eDbRepositoryFactory
    ) -> None:
        """Test that getting unknown category raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            factory.get("unknown-category")

        assert "Unknown category: unknown-category" in str(exc_info.value)
        assert "Valid categories:" in str(exc_info.value)

    def test_specialized_repositories_use_correct_classes(
        self, factory: D5eDbRepositoryFactory
    ) -> None:
        """Test that specialized repositories use their custom classes."""
        # Check spell repository
        spells_repo = factory.get_spells()
        assert isinstance(spells_repo, DbSpellRepository)

        # Check monster repository
        monsters_repo = factory.get_monsters()
        assert isinstance(monsters_repo, DbMonsterRepository)

        # Check equipment repository
        equipment_repo = factory.get_equipment()
        assert isinstance(equipment_repo, DbEquipmentRepository)

        # Check class repository
        classes_repo = factory.get_classes()
        assert isinstance(classes_repo, DbClassRepository)

    def test_generic_repositories_use_base_class(
        self, factory: D5eDbRepositoryFactory
    ) -> None:
        """Test that generic repositories use the base class."""
        # Test various generic repositories
        generic_categories = [
            "ability-scores",
            "alignments",
            "conditions",
            "damage-types",
            "languages",
            "proficiencies",
            "skills",
            "backgrounds",
            "feats",
            "races",
            "subclasses",
            "subraces",
            "traits",
            "features",
            "levels",
            "equipment-categories",
            "magic-items",
            "magic-schools",
            "weapon-properties",
            "rules",
            "rule-sections",
        ]

        for category in generic_categories:
            repo = factory.get(category)
            assert isinstance(repo, BaseD5eDbRepository)
            # Make sure it's not one of the specialized types
            assert not isinstance(
                repo,
                (
                    DbSpellRepository,
                    DbMonsterRepository,
                    DbEquipmentRepository,
                    DbClassRepository,
                ),
            )

    def test_typed_getter_methods(self, factory: D5eDbRepositoryFactory) -> None:
        """Test that typed getter methods return correct repository types."""
        # Test each typed getter
        assert isinstance(factory.get_ability_scores(), BaseD5eDbRepository)
        assert isinstance(factory.get_alignments(), BaseD5eDbRepository)
        assert isinstance(factory.get_backgrounds(), BaseD5eDbRepository)
        assert isinstance(factory.get_classes(), DbClassRepository)
        assert isinstance(factory.get_conditions(), BaseD5eDbRepository)
        assert isinstance(factory.get_damage_types(), BaseD5eDbRepository)
        assert isinstance(factory.get_equipment(), DbEquipmentRepository)
        assert isinstance(factory.get_feats(), BaseD5eDbRepository)
        assert isinstance(factory.get_features(), BaseD5eDbRepository)
        assert isinstance(factory.get_languages(), BaseD5eDbRepository)
        assert isinstance(factory.get_levels(), BaseD5eDbRepository)
        assert isinstance(factory.get_magic_items(), BaseD5eDbRepository)
        assert isinstance(factory.get_magic_schools(), BaseD5eDbRepository)
        assert isinstance(factory.get_monsters(), DbMonsterRepository)
        assert isinstance(factory.get_proficiencies(), BaseD5eDbRepository)
        assert isinstance(factory.get_races(), BaseD5eDbRepository)
        assert isinstance(factory.get_skills(), BaseD5eDbRepository)
        assert isinstance(factory.get_spells(), DbSpellRepository)
        assert isinstance(factory.get_subclasses(), BaseD5eDbRepository)
        assert isinstance(factory.get_subraces(), BaseD5eDbRepository)
        assert isinstance(factory.get_traits(), BaseD5eDbRepository)
        assert isinstance(factory.get_weapon_properties(), BaseD5eDbRepository)
        assert isinstance(factory.get_rules(), BaseD5eDbRepository)
        assert isinstance(factory.get_rule_sections(), BaseD5eDbRepository)

    def test_all_repositories_share_database_manager(
        self, database_manager: Mock
    ) -> None:
        """Test that all repositories are created with the same database manager."""
        factory = D5eDbRepositoryFactory(database_manager)

        # Check a few repositories to ensure they have the database manager
        skills_repo = factory.get_skills()
        assert skills_repo._database_manager is database_manager

        spells_repo = factory.get_spells()
        assert spells_repo._database_manager is database_manager

        classes_repo = factory.get_classes()
        assert classes_repo._database_manager is database_manager
