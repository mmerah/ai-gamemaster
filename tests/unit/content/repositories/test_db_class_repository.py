"""Tests for the database-aware class repository."""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import CharacterClass, ContentPack, Feature, Level
from app.content.repositories.db_class_repository import DbClassRepository
from app.content.schemas import APIReference, D5eClass, D5eFeature, D5eLevel


class TestDbClassRepository:
    """Test the database-backed class repository."""

    @pytest.fixture
    def database_manager(self) -> Mock:
        """Create a mock database manager."""
        return Mock(spec=DatabaseManager)

    @pytest.fixture
    def session(self) -> Mock:
        """Create a mock session."""
        return Mock(spec=Session)

    @pytest.fixture
    def context_manager(self, session: Mock) -> Mock:
        """Create a mock context manager for database sessions."""
        context = Mock()
        context.__enter__ = Mock(return_value=session)
        context.__exit__ = Mock(return_value=None)
        return context

    @pytest.fixture
    def repository(self, database_manager: Mock) -> DbClassRepository:
        """Create a test repository."""
        return DbClassRepository(database_manager)

    def _create_mock_class(
        self,
        index: str = "wizard",
        name: str = "Wizard",
        hit_die: int = 6,
        spellcasting: Optional[Any] = None,
        saving_throws: Optional[List[Dict[str, Any]]] = None,
        multi_classing: Optional[Any] = None,
        starting_equipment: Optional[List[Dict[str, Any]]] = None,
    ) -> Mock:
        """Create a mock class entity."""
        cls = Mock(spec=CharacterClass)
        cls.index = index
        cls.name = name
        cls.url = f"/api/classes/{index}"
        cls.hit_die = hit_die
        cls.spellcasting = spellcasting
        cls.saving_throws = saving_throws or [
            {"index": "int", "name": "INT", "url": "/api/ability-scores/int"},
            {"index": "wis", "name": "WIS", "url": "/api/ability-scores/wis"},
        ]
        cls.multi_classing = multi_classing
        cls.starting_equipment = starting_equipment or []
        cls.starting_equipment_options = []
        cls.proficiencies = []
        cls.proficiency_choices = []
        cls.class_levels = f"/api/classes/{index}/levels"
        cls.subclasses = []
        cls.content_pack_id = "dnd_5e_srd"

        # Mock the table attribute for _entity_to_model
        def create_column_mock(name: str) -> Mock:
            col = Mock()
            col.name = name
            return col

        cls.__table__ = Mock()
        cls.__table__.columns = [
            create_column_mock("index"),
            create_column_mock("name"),
            create_column_mock("url"),
            create_column_mock("hit_die"),
            create_column_mock("spellcasting"),
            create_column_mock("saving_throws"),
            create_column_mock("multi_classing"),
            create_column_mock("starting_equipment"),
            create_column_mock("starting_equipment_options"),
            create_column_mock("proficiencies"),
            create_column_mock("proficiency_choices"),
            create_column_mock("class_levels"),
            create_column_mock("subclasses"),
            create_column_mock("content_pack_id"),
        ]

        return cls

    def _create_mock_feature(
        self,
        index: str = "arcane-recovery",
        name: str = "Arcane Recovery",
        level: int = 1,
        class_index: str = "wizard",
        subclass_index: Optional[str] = None,
    ) -> Mock:
        """Create a mock feature entity."""
        feature = Mock(spec=Feature)
        feature.index = index
        feature.name = name
        feature.url = f"/api/features/{index}"
        feature.level = level
        # Use 'class' not 'class_' for the column name since D5eFeature uses alias
        setattr(
            feature,
            "class",
            {
                "index": class_index,
                "name": class_index.title(),
                "url": f"/api/classes/{class_index}",
            },
        )
        feature.subclass = (
            {
                "index": subclass_index,
                "name": subclass_index,
                "url": f"/api/subclasses/{subclass_index}",
            }
            if subclass_index
            else None
        )
        feature.desc = ["Feature description..."]
        feature.content_pack_id = "dnd_5e_srd"

        # Mock the table attribute
        def create_column_mock(name: str) -> Mock:
            col = Mock()
            col.name = name
            return col

        feature.__table__ = Mock()
        feature.__table__.columns = [
            create_column_mock("index"),
            create_column_mock("name"),
            create_column_mock("url"),
            create_column_mock("level"),
            create_column_mock("class"),
            create_column_mock("subclass"),
            create_column_mock("desc"),
            create_column_mock("content_pack_id"),
        ]

        return feature

    def _create_mock_level(
        self,
        level: int = 1,
        class_index: str = "wizard",
        prof_bonus: int = 2,
        features: Optional[List[Dict[str, Any]]] = None,
        spellcasting: Optional[Dict[str, Any]] = None,
    ) -> Mock:
        """Create a mock level entity."""
        level_entity = Mock(spec=Level)
        level_entity.index = f"{class_index}-{level}"
        level_entity.level = level
        level_entity.url = f"/api/classes/{class_index}/levels/{level}"
        # Use 'class' not 'class_' for the column name since D5eLevel uses alias
        setattr(
            level_entity,
            "class",
            {
                "index": class_index,
                "name": class_index.title(),
                "url": f"/api/classes/{class_index}",
            },
        )
        level_entity.ability_score_bonuses = 0
        level_entity.prof_bonus = prof_bonus
        level_entity.features = features or []
        level_entity.spellcasting = spellcasting
        level_entity.content_pack_id = "dnd_5e_srd"

        # Mock the table attribute
        def create_column_mock(name: str) -> Mock:
            col = Mock()
            col.name = name
            return col

        level_entity.__table__ = Mock()
        level_entity.__table__.columns = [
            create_column_mock("index"),
            create_column_mock("level"),
            create_column_mock("url"),
            create_column_mock("class"),
            create_column_mock("ability_score_bonuses"),
            create_column_mock("prof_bonus"),
            create_column_mock("features"),
            create_column_mock("spellcasting"),
            create_column_mock("content_pack_id"),
        ]

        return level_entity

    def test_get_spellcasting_classes(
        self,
        repository: DbClassRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spellcasting classes."""
        # Create mock classes
        spellcasting_data = {
            "level": 1,
            "spellcasting_ability": {
                "index": "int",
                "name": "INT",
                "url": "/api/ability-scores/int",
            },
        }
        wizard = self._create_mock_class(
            "wizard", "Wizard", hit_die=6, spellcasting=spellcasting_data
        )
        fighter = self._create_mock_class(
            "fighter", "Fighter", hit_die=10, spellcasting=None
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [wizard, fighter]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_spellcasting_classes()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Wizard"

    def test_get_by_hit_die(
        self,
        repository: DbClassRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting classes by hit die."""
        # Create mock classes
        self._create_mock_class("wizard", "Wizard", hit_die=6)
        barbarian = self._create_mock_class("barbarian", "Barbarian", hit_die=12)

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [barbarian]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_hit_die(12)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Barbarian"

    def test_get_class_features(
        self,
        repository: DbClassRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting class features."""
        # Create mock features
        feature1 = self._create_mock_feature(
            "arcane-recovery", "Arcane Recovery", level=1, class_index="wizard"
        )
        feature2 = self._create_mock_feature(
            "spellcasting-wizard", "Spellcasting", level=1, class_index="wizard"
        )
        feature3 = self._create_mock_feature(
            "fighting-style", "Fighting Style", level=1, class_index="fighter"
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [feature1, feature2, feature3]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_class_features("wizard")

        # Verify
        assert len(results) == 2
        assert all(f.class_.index == "wizard" for f in results)

    def test_get_class_features_by_level(
        self,
        repository: DbClassRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting class features filtered by level."""
        # Create mock features
        feature1 = self._create_mock_feature(
            "arcane-recovery", "Arcane Recovery", level=1, class_index="wizard"
        )
        feature2 = self._create_mock_feature(
            "arcane-tradition", "Arcane Tradition", level=2, class_index="wizard"
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [feature1, feature2]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_class_features("wizard", level=2)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Arcane Tradition"

    def test_get_subclass_features(
        self,
        repository: DbClassRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting subclass features."""
        # Create mock features
        feature1 = self._create_mock_feature(
            "bladesong",
            "Bladesong",
            level=2,
            class_index="wizard",
            subclass_index="bladesinger",
        )
        feature2 = self._create_mock_feature(
            "extra-attack",
            "Extra Attack",
            level=6,
            class_index="wizard",
            subclass_index="bladesinger",
        )
        feature3 = self._create_mock_feature(
            "portent",
            "Portent",
            level=2,
            class_index="wizard",
            subclass_index="divination",
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [feature1, feature2, feature3]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_subclass_features("bladesinger")

        # Verify
        assert len(results) == 2
        assert all(f.subclass and f.subclass.index == "bladesinger" for f in results)

    def test_get_level_progression(
        self,
        repository: DbClassRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting level progression for a class."""
        # Create mock levels
        level1 = self._create_mock_level(1, "wizard", prof_bonus=2)
        level2 = self._create_mock_level(2, "wizard", prof_bonus=2)
        level3 = self._create_mock_level(3, "wizard", prof_bonus=2)

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [level1, level2, level3]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_level_progression("wizard")

        # Verify
        assert len(results) == 3
        assert results[0].level == 1
        assert results[1].level == 2
        assert results[2].level == 3

    def test_get_level_data(
        self,
        repository: DbClassRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting specific level data."""
        # Create mock level
        level_data = self._create_mock_level(5, "wizard", prof_bonus=3)

        # Mock the query chain for the level repository
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.first.return_value = level_data

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        result = repository.get_level_data("wizard", 5)

        # Verify
        assert result is not None
        assert result.level == 5
        assert result.prof_bonus == 3

    def test_get_proficiency_bonus(self, repository: DbClassRepository) -> None:
        """Test getting proficiency bonus by level."""
        assert repository.get_proficiency_bonus(1) == 2
        assert repository.get_proficiency_bonus(4) == 2
        assert repository.get_proficiency_bonus(5) == 3
        assert repository.get_proficiency_bonus(8) == 3
        assert repository.get_proficiency_bonus(9) == 4
        assert repository.get_proficiency_bonus(12) == 4
        assert repository.get_proficiency_bonus(13) == 5
        assert repository.get_proficiency_bonus(16) == 5
        assert repository.get_proficiency_bonus(17) == 6
        assert repository.get_proficiency_bonus(20) == 6

    def test_get_multiclass_requirements(self, repository: DbClassRepository) -> None:
        """Test getting multiclass requirements."""
        # Create a mock D5eClass instance directly
        mock_class = Mock(spec=D5eClass)
        mock_class.multi_classing = Mock()
        mock_class.multi_classing.prerequisites = [Mock()]
        mock_class.multi_classing.prerequisites[0].ability_score = Mock()
        mock_class.multi_classing.prerequisites[0].ability_score.index = "int"
        mock_class.multi_classing.prerequisites[0].minimum_score = 13

        mock_class.multi_classing.proficiencies = [Mock()]
        mock_class.multi_classing.proficiencies[0].index = "light-armor"

        # Patch get_by_index_with_options to return our mock
        with patch.object(
            repository, "get_by_index_with_options", return_value=mock_class
        ):
            # Execute
            result = repository.get_multiclass_requirements("wizard")

        # Verify
        assert result is not None
        assert "prerequisites" in result
        assert result["prerequisites"][0]["ability"] == "int"
        assert result["prerequisites"][0]["minimum"] == 13
        assert "proficiencies" in result
        assert "light-armor" in result["proficiencies"]

    def test_get_spell_slots(self, repository: DbClassRepository) -> None:
        """Test getting spell slots for a spellcasting class."""
        # Create mock level with spellcasting data
        mock_level = Mock(spec=D5eLevel)
        mock_level.spellcasting = Mock()
        mock_level.spellcasting.spell_slots_level_1 = 2
        mock_level.spellcasting.spell_slots_level_2 = 0
        mock_level.spellcasting.spell_slots_level_3 = 0
        mock_level.spellcasting.spell_slots_level_4 = 0
        mock_level.spellcasting.spell_slots_level_5 = 0
        mock_level.spellcasting.spell_slots_level_6 = 0
        mock_level.spellcasting.spell_slots_level_7 = 0
        mock_level.spellcasting.spell_slots_level_8 = 0
        mock_level.spellcasting.spell_slots_level_9 = 0

        # Patch get_level_data to return our mock
        with patch.object(repository, "get_level_data", return_value=mock_level):
            # Execute
            result = repository.get_spell_slots("wizard", 1)

        # Verify
        assert result is not None
        assert result[1] == 2

    def test_get_saving_throw_proficiencies(
        self, repository: DbClassRepository
    ) -> None:
        """Test getting saving throw proficiencies."""
        # Create mock class
        mock_class = Mock(spec=D5eClass)
        mock_class.saving_throws = [Mock(index="int"), Mock(index="wis")]

        # Patch get_by_index_with_options to return our mock
        with patch.object(
            repository, "get_by_index_with_options", return_value=mock_class
        ):
            # Execute
            result = repository.get_saving_throw_proficiencies("wizard")

        # Verify
        assert len(result) == 2
        assert "int" in result
        assert "wis" in result
