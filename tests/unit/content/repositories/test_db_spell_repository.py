"""Tests for the database-aware spell repository."""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import ContentPack, Spell
from app.content.repositories.db_spell_repository import DbSpellRepository
from app.content.schemas import APIReference, D5eSpell


class TestDbSpellRepository:
    """Test the database-backed spell repository."""

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
    def repository(self, database_manager: Mock) -> DbSpellRepository:
        """Create a test repository."""
        return DbSpellRepository(database_manager)

    def _create_mock_spell(
        self,
        index: str = "fireball",
        name: str = "Fireball",
        level: int = 3,
        school: Optional[Dict[str, Any]] = None,
        classes: Optional[List[Dict[str, Any]]] = None,
        ritual: bool = False,
        concentration: bool = False,
        components: Optional[List[str]] = None,
        casting_time: str = "1 action",
        range: str = "150 feet",
        desc: Optional[List[str]] = None,
        higher_level: Optional[List[str]] = None,
    ) -> Mock:
        """Create a mock spell entity."""
        spell = Mock(spec=Spell)
        spell.index = index
        spell.name = name
        spell.url = f"/api/spells/{index}"
        spell.level = level
        spell.school = school or {
            "index": "evocation",
            "name": "Evocation",
            "url": "/api/magic-schools/evocation",
        }
        spell.classes = classes or [
            {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"},
            {"index": "sorcerer", "name": "Sorcerer", "url": "/api/classes/sorcerer"},
        ]
        spell.subclasses = []  # Required field
        spell.ritual = ritual
        spell.concentration = concentration
        spell.components = components or ["V", "S", "M"]
        spell.material = (
            "A tiny ball of bat guano and sulfur"
            if "M" in (components or ["V", "S", "M"])
            else None
        )
        spell.casting_time = casting_time
        spell.range = range
        spell.duration = "Instantaneous"
        spell.desc = desc or ["A bright streak flashes from your pointing finger..."]
        spell.higher_level = higher_level or [
            "When you cast this spell using a spell slot of 4th level or higher..."
        ]
        spell.damage = None  # Optional field
        spell.dc = None  # Optional field
        spell.area_of_effect = None  # Optional field
        spell.attack_type = None  # Optional field
        spell.content_pack_id = "dnd_5e_srd"

        # Mock the table attribute for _entity_to_model
        def create_column_mock(name: str) -> Mock:
            col = Mock()
            col.name = name
            return col

        spell.__table__ = Mock()
        spell.__table__.columns = [
            create_column_mock("index"),
            create_column_mock("name"),
            create_column_mock("url"),
            create_column_mock("level"),
            create_column_mock("school"),
            create_column_mock("classes"),
            create_column_mock("subclasses"),
            create_column_mock("ritual"),
            create_column_mock("concentration"),
            create_column_mock("components"),
            create_column_mock("material"),
            create_column_mock("casting_time"),
            create_column_mock("range"),
            create_column_mock("duration"),
            create_column_mock("desc"),
            create_column_mock("higher_level"),
            create_column_mock("damage"),
            create_column_mock("dc"),
            create_column_mock("area_of_effect"),
            create_column_mock("attack_type"),
            create_column_mock("content_pack_id"),
        ]

        return spell

    def test_get_by_level(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spells by level."""
        # Create mock spells
        self._create_mock_spell("mage-hand", "Mage Hand", level=0)
        self._create_mock_spell("magic-missile", "Magic Missile", level=1)
        level3 = self._create_mock_spell("fireball", "Fireball", level=3)

        # Mock the query chain for filter_by
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [level3]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_level(3)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"
        assert results[0].level == 3

    def test_get_by_school(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spells by school."""
        # Create mock spells
        evocation = self._create_mock_spell(
            "fireball",
            "Fireball",
            school={
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
        )
        self._create_mock_spell(
            "vampiric-touch",
            "Vampiric Touch",
            school={
                "index": "necromancy",
                "name": "Necromancy",
                "url": "/api/magic-schools/necromancy",
            },
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [evocation]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_school("evocation")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"
        assert results[0].school.index == "evocation"

    def test_get_by_class(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spells by class."""
        # Create mock spells
        wizard_spell = self._create_mock_spell(
            "fireball",
            "Fireball",
            classes=[
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
            ],
        )
        self._create_mock_spell(
            "cure-wounds",
            "Cure Wounds",
            classes=[
                {"index": "cleric", "name": "Cleric", "url": "/api/classes/cleric"}
            ],
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [wizard_spell]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_class("wizard")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"

    def test_get_by_class_and_level(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spells by class and level."""
        # Create mock spell
        spell = self._create_mock_spell(
            "fireball",
            "Fireball",
            level=3,
            classes=[
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
            ],
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [spell]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_class_and_level("wizard", 3)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"
        assert results[0].level == 3

    def test_get_ritual_spells(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting ritual spells."""
        # Create mock spells
        ritual = self._create_mock_spell("identify", "Identify", ritual=True)
        self._create_mock_spell("fireball", "Fireball", ritual=False)

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [ritual]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_ritual_spells()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Identify"
        assert results[0].ritual is True

    def test_get_concentration_spells(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting concentration spells."""
        # Create mock spells
        concentration = self._create_mock_spell("bless", "Bless", concentration=True)
        self._create_mock_spell("fireball", "Fireball", concentration=False)

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [concentration]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_concentration_spells()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Bless"
        assert results[0].concentration is True

    def test_get_by_components(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spells by components."""
        # Create mock spells
        vsm = self._create_mock_spell(
            "fireball", "Fireball", components=["V", "S", "M"]
        )
        self._create_mock_spell("magic-missile", "Magic Missile", components=["V", "S"])
        self._create_mock_spell("vicious-mockery", "Vicious Mockery", components=["V"])

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [vsm]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute - get spells with material components
        results = repository.get_by_components(material=True)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"
        assert "M" in results[0].components

    def test_get_by_casting_time(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spells by casting time."""
        # Create mock spells
        action = self._create_mock_spell(
            "fireball", "Fireball", casting_time="1 action"
        )
        self._create_mock_spell(
            "healing-word", "Healing Word", casting_time="1 bonus action"
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [action]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_casting_time("1 action")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"
        assert results[0].casting_time == "1 action"

    def test_get_by_range(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spells by range."""
        # Create mock spells
        ranged = self._create_mock_spell("fireball", "Fireball", range="150 feet")
        self._create_mock_spell("cure-wounds", "Cure Wounds", range="Touch")

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [ranged]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_range("150 feet")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"
        assert results[0].range == "150 feet"

    def test_get_available_schools(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting available spell schools."""
        # Mock the query result
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [
            ("evocation",),
            ("necromancy",),
            ("abjuration",),
            ("illusion",),
        ]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        schools = repository.get_available_schools()

        # Verify
        assert len(schools) == 4
        assert "evocation" in schools
        assert "necromancy" in schools
        assert "abjuration" in schools
        assert "illusion" in schools

    def test_get_max_level(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting the maximum spell level."""
        # Mock the query result
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.scalar.return_value = 9

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        max_level = repository.get_max_level()

        # Verify
        assert max_level == 9

    def test_search_by_description(
        self,
        repository: DbSpellRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test searching spells by description."""
        # Create mock spells
        fireball = self._create_mock_spell(
            "fireball",
            "Fireball",
            desc=[
                "A bright streak flashes from your pointing finger to a point you choose..."
            ],
            higher_level=[
                "When you cast this spell using a spell slot of 4th level or higher..."
            ],
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [fireball]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.search_by_description("bright streak")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Fireball"
