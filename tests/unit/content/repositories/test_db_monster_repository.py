"""Tests for the database-aware monster repository."""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import ContentPack, Monster
from app.content.repositories.db_monster_repository import DbMonsterRepository
from app.content.schemas import D5eMonster, MonsterAction, MonsterSpeed, SpecialAbility


class TestDbMonsterRepository:
    """Test the database-backed monster repository."""

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
    def repository(self, database_manager: Mock) -> DbMonsterRepository:
        """Create a test repository."""
        return DbMonsterRepository(database_manager)

    def _create_mock_monster(
        self,
        index: str = "adult-red-dragon",
        name: str = "Adult Red Dragon",
        challenge_rating: float = 17.0,
        type: str = "dragon",
        size: str = "Huge",
        alignment: str = "chaotic evil",
        legendary_actions: Optional[List[Dict[str, Any]]] = None,
        special_abilities: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        damage_immunities: Optional[List[str]] = None,
        damage_resistances: Optional[List[str]] = None,
        speed: Optional[Dict[str, Any]] = None,
    ) -> Mock:
        """Create a mock monster entity."""
        monster = Mock(spec=Monster)
        monster.index = index
        monster.name = name
        monster.url = f"/api/monsters/{index}"
        monster.challenge_rating = challenge_rating
        monster.type = type
        monster.size = size
        monster.alignment = alignment

        # Set lists with defaults
        monster.legendary_actions = legendary_actions or []
        monster.special_abilities = special_abilities or []
        monster.actions = actions or []
        monster.damage_immunities = damage_immunities or ["fire"]
        monster.damage_resistances = damage_resistances or []
        monster.condition_immunities = []
        monster.damage_vulnerabilities = []
        monster.senses = {"blindsight": "60 ft.", "darkvision": "120 ft."}
        monster.languages = "Common, Draconic"

        # Set other required fields
        monster.hit_points = 256
        monster.hit_dice = "17d12"
        monster.hit_points_roll = "17d12+136"
        monster.armor_class = [{"type": "natural", "value": 19}]
        monster.proficiency_bonus = 6
        monster.xp = 18000

        # Set ability scores
        monster.strength = 27
        monster.dexterity = 10
        monster.constitution = 25
        monster.intelligence = 16
        monster.wisdom = 13
        monster.charisma = 21

        # Set speed
        monster.speed = speed or {"walk": "40 ft.", "climb": "40 ft.", "fly": "80 ft."}

        # Set proficiencies
        monster.proficiencies = []

        # Set desc - even though it's not on the database model
        monster.desc = None

        monster.content_pack_id = "dnd_5e_srd"

        # Mock the table attribute for _entity_to_model
        def create_column_mock(name: str) -> Mock:
            col = Mock()
            col.name = name
            return col

        monster.__table__ = Mock()
        monster.__table__.columns = [
            create_column_mock("index"),
            create_column_mock("name"),
            create_column_mock("url"),
            create_column_mock("challenge_rating"),
            create_column_mock("type"),
            create_column_mock("size"),
            create_column_mock("alignment"),
            create_column_mock("legendary_actions"),
            create_column_mock("special_abilities"),
            create_column_mock("actions"),
            create_column_mock("damage_immunities"),
            create_column_mock("damage_resistances"),
            create_column_mock("condition_immunities"),
            create_column_mock("damage_vulnerabilities"),
            create_column_mock("senses"),
            create_column_mock("languages"),
            create_column_mock("hit_points"),
            create_column_mock("hit_dice"),
            create_column_mock("hit_points_roll"),
            create_column_mock("armor_class"),
            create_column_mock("proficiency_bonus"),
            create_column_mock("xp"),
            create_column_mock("strength"),
            create_column_mock("dexterity"),
            create_column_mock("constitution"),
            create_column_mock("intelligence"),
            create_column_mock("wisdom"),
            create_column_mock("charisma"),
            create_column_mock("speed"),
            create_column_mock("proficiencies"),
            create_column_mock("content_pack_id"),
        ]

        return monster

    def test_get_by_challenge_rating(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters by challenge rating."""
        # Create mock monsters
        dragon = self._create_mock_monster(
            "adult-red-dragon", "Adult Red Dragon", challenge_rating=17.0
        )
        self._create_mock_monster("goblin", "Goblin", challenge_rating=0.25)

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [dragon]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_challenge_rating(17.0)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Adult Red Dragon"
        assert results[0].challenge_rating == 17.0

    def test_get_by_cr_range(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters within a CR range."""
        # Create mock monsters
        goblin = self._create_mock_monster("goblin", "Goblin", challenge_rating=0.25)
        orc = self._create_mock_monster("orc", "Orc", challenge_rating=0.5)
        troll = self._create_mock_monster("troll", "Troll", challenge_rating=5.0)
        dragon = self._create_mock_monster(
            "adult-red-dragon", "Adult Red Dragon", challenge_rating=17.0
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [goblin, orc, troll, dragon]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_cr_range(0.25, 5.0)

        # Verify
        assert len(results) == 3
        assert all(0.25 <= m.challenge_rating <= 5.0 for m in results)

    def test_get_by_type(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters by type."""
        # Create mock monsters
        dragon = self._create_mock_monster(
            "adult-red-dragon", "Adult Red Dragon", type="dragon"
        )
        young_dragon = self._create_mock_monster(
            "young-red-dragon", "Young Red Dragon", type="dragon"
        )
        self._create_mock_monster("goblin", "Goblin", type="humanoid (goblinoid)")

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [dragon, young_dragon]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_type("dragon")

        # Verify
        assert len(results) == 2
        assert all("dragon" in m.type.lower() for m in results)

    def test_get_by_size(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters by size."""
        # Create mock monsters
        huge_dragon = self._create_mock_monster(
            "adult-red-dragon", "Adult Red Dragon", size="Huge"
        )
        self._create_mock_monster("troll", "Troll", size="Large")
        self._create_mock_monster("goblin", "Goblin", size="Small")

        # Mock the query chain
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [huge_dragon]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_size("Huge")

        # Verify
        assert len(results) == 1
        assert results[0].size == "Huge"

    def test_get_by_alignment(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters by alignment."""
        # Create mock monsters
        evil_dragon = self._create_mock_monster(
            "adult-red-dragon", "Adult Red Dragon", alignment="chaotic evil"
        )
        evil_lich = self._create_mock_monster("lich", "Lich", alignment="lawful evil")
        neutral_bear = self._create_mock_monster("bear", "Bear", alignment="unaligned")

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [evil_dragon, evil_lich, neutral_bear]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_alignment("evil")

        # Verify
        assert len(results) == 2
        assert all("evil" in m.alignment.lower() for m in results)

    def test_get_legendary_monsters(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting legendary monsters."""
        # Create mock monsters
        legendary_dragon = self._create_mock_monster(
            "adult-red-dragon",
            "Adult Red Dragon",
            legendary_actions=[
                {
                    "name": "Detect",
                    "desc": "The dragon makes a Wisdom (Perception) check.",
                },
                {"name": "Tail Attack", "desc": "The dragon makes a tail attack."},
            ],
        )
        normal_goblin = self._create_mock_monster(
            "goblin", "Goblin", legendary_actions=[]
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [legendary_dragon, normal_goblin]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_legendary_monsters()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Adult Red Dragon"
        assert results[0].legendary_actions is not None
        assert len(results[0].legendary_actions) > 0

    def test_get_by_damage_immunity(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters by damage immunity."""
        # Create mock monsters
        fire_immune = self._create_mock_monster(
            "adult-red-dragon", "Adult Red Dragon", damage_immunities=["fire"]
        )
        poison_immune = self._create_mock_monster(
            "iron-golem", "Iron Golem", damage_immunities=["fire", "poison", "psychic"]
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [fire_immune, poison_immune]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_damage_immunity("fire")

        # Verify
        assert len(results) == 2
        assert all(
            any("fire" in imm.lower() for imm in m.damage_immunities) for m in results
        )

    def test_get_by_damage_resistance(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters by damage resistance."""
        # Create mock monsters
        resistant = self._create_mock_monster(
            "werewolf",
            "Werewolf",
            damage_resistances=[
                "bludgeoning, piercing, and slashing from nonmagical attacks"
            ],
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [resistant]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_damage_resistance("bludgeoning")

        # Verify
        assert len(results) == 1
        assert any(
            "bludgeoning" in res.lower() for res in results[0].damage_resistances
        )

    def test_get_by_speed_type(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting monsters by speed type."""
        # Create mock monsters
        flying = self._create_mock_monster(
            "adult-red-dragon",
            "Adult Red Dragon",
            speed={"walk": "40 ft.", "climb": "40 ft.", "fly": "80 ft."},
        )
        swimming = self._create_mock_monster(
            "aboleth", "Aboleth", speed={"walk": "10 ft.", "swim": "40 ft."}
        )
        walking_only = self._create_mock_monster(
            "goblin", "Goblin", speed={"walk": "30 ft."}
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [flying, swimming, walking_only]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_speed_type("fly")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Adult Red Dragon"
        assert results[0].speed.fly is not None

    def test_get_spellcasters(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting spellcasting monsters."""
        # Create mock monsters
        spellcaster = self._create_mock_monster(
            "archmage",
            "Archmage",
            special_abilities=[
                {
                    "name": "Spellcasting",
                    "desc": "The archmage is an 18th-level spellcaster...",
                }
            ],
        )
        non_spellcaster = self._create_mock_monster(
            "goblin", "Goblin", special_abilities=[]
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [spellcaster, non_spellcaster]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_spellcasters()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Archmage"

    def test_get_cr_distribution(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting CR distribution."""
        # Mock the query result
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = [
            (0.25, 5),  # 5 monsters with CR 0.25
            (0.5, 3),  # 3 monsters with CR 0.5
            (1.0, 10),  # 10 monsters with CR 1
            (2.0, 8),  # 8 monsters with CR 2
        ]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        distribution = repository.get_cr_distribution()

        # Verify
        assert distribution == {0.25: 5, 0.5: 3, 1.0: 10, 2.0: 8}

    def test_search_abilities(
        self,
        repository: DbMonsterRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test searching monsters by ability keyword."""
        # Create mock monsters
        breath_weapon = self._create_mock_monster(
            "adult-red-dragon",
            "Adult Red Dragon",
            actions=[
                {
                    "name": "Fire Breath",
                    "desc": "The dragon exhales fire in a 60-foot cone...",
                }
            ],
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [breath_weapon]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.search_abilities("breath")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Adult Red Dragon"
