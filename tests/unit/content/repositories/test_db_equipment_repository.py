"""Tests for the database-aware equipment repository."""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import ContentPack, Equipment, MagicItem, WeaponProperty
from app.content.repositories.db_equipment_repository import DbEquipmentRepository
from app.content.schemas import (
    APIReference,
    Cost,
    D5eEquipment,
    D5eMagicItem,
    D5eWeaponProperty,
)


class TestDbEquipmentRepository:
    """Test the database-backed equipment repository."""

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
    def repository(self, database_manager: Mock) -> DbEquipmentRepository:
        """Create a test repository."""
        return DbEquipmentRepository(database_manager)

    def _create_mock_equipment(
        self,
        index: str = "longsword",
        name: str = "Longsword",
        equipment_category: str = "weapon",
        weapon_category: Optional[str] = "Martial",
        armor_category: Optional[str] = None,
        weapon_range: Optional[str] = "Melee",
        cost: Optional[Dict[str, Any]] = None,
        weight: Optional[float] = 3.0,
        properties: Optional[List[Dict[str, Any]]] = None,
        armor_class: Optional[Dict[str, Any]] = None,
    ) -> Mock:
        """Create a mock equipment entity."""
        equipment = Mock(spec=Equipment)
        equipment.index = index
        equipment.name = name
        equipment.url = f"/api/equipment/{index}"
        equipment.equipment_category = {
            "index": equipment_category,
            "name": equipment_category.title(),
            "url": f"/api/equipment-categories/{equipment_category}",
        }
        equipment.weapon_category = weapon_category
        equipment.armor_category = armor_category
        equipment.weapon_range = weapon_range
        equipment.cost = cost or {"quantity": 15, "unit": "gp"}
        equipment.weight = weight
        equipment.properties = properties or []
        equipment.armor_class = armor_class

        # Set other fields to defaults
        equipment.damage = None
        equipment.two_handed_damage = None
        equipment.range = None
        equipment.throw_range = None
        equipment.str_minimum = None
        equipment.stealth_disadvantage = None
        equipment.desc = []
        equipment.special = []
        equipment.quantity = 1
        equipment.contents = []
        equipment.tool_category = None
        equipment.gear_category = None
        equipment.vehicle_category = None

        equipment.content_pack_id = "dnd_5e_srd"

        # Mock the table attribute for _entity_to_model
        def create_column_mock(name: str) -> Mock:
            col = Mock()
            col.name = name
            return col

        equipment.__table__ = Mock()
        equipment.__table__.columns = [
            create_column_mock("index"),
            create_column_mock("name"),
            create_column_mock("url"),
            create_column_mock("equipment_category"),
            create_column_mock("weapon_category"),
            create_column_mock("armor_category"),
            create_column_mock("weapon_range"),
            create_column_mock("cost"),
            create_column_mock("weight"),
            create_column_mock("properties"),
            create_column_mock("armor_class"),
            create_column_mock("damage"),
            create_column_mock("two_handed_damage"),
            create_column_mock("range"),
            create_column_mock("throw_range"),
            create_column_mock("str_minimum"),
            create_column_mock("stealth_disadvantage"),
            create_column_mock("desc"),
            create_column_mock("special"),
            create_column_mock("quantity"),
            create_column_mock("contents"),
            create_column_mock("tool_category"),
            create_column_mock("gear_category"),
            create_column_mock("vehicle_category"),
            create_column_mock("content_pack_id"),
        ]

        return equipment

    def test_get_weapons(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting all weapons."""
        # Create mock equipment
        sword = self._create_mock_equipment(
            "longsword", "Longsword", weapon_category="Martial"
        )
        armor = self._create_mock_equipment(
            "plate",
            "Plate",
            equipment_category="armor",
            weapon_category=None,
            armor_category="Heavy",
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [sword, armor]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_weapons()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Longsword"

    def test_get_armor(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting all armor."""
        # Create mock equipment
        sword = self._create_mock_equipment(
            "longsword", "Longsword", weapon_category="Martial"
        )
        plate = self._create_mock_equipment(
            "plate",
            "Plate",
            equipment_category="armor",
            weapon_category=None,
            armor_category="Heavy",
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [sword, plate]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_armor()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Plate"

    def test_get_by_category(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting equipment by category."""
        # Create mock equipment
        sword = self._create_mock_equipment(
            "longsword", "Longsword", equipment_category="weapon"
        )
        torch = self._create_mock_equipment(
            "torch",
            "Torch",
            equipment_category="adventuring-gear",
            weapon_category=None,
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [sword, torch]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_by_category("weapon")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Longsword"

    def test_get_weapons_by_category(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting weapons by weapon category."""
        # Create mock weapons
        longsword = self._create_mock_equipment(
            "longsword", "Longsword", weapon_category="Martial"
        )
        shortsword = self._create_mock_equipment(
            "shortsword", "Shortsword", weapon_category="Martial"
        )
        club = self._create_mock_equipment("club", "Club", weapon_category="Simple")

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [longsword, shortsword, club]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_weapons_by_category("Martial")

        # Verify
        assert len(results) == 2
        assert all(w.weapon_category == "Martial" for w in results)

    def test_get_armor_by_category(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting armor by armor category."""
        # Create mock armor
        leather = self._create_mock_equipment(
            "leather-armor",
            "Leather Armor",
            equipment_category="armor",
            weapon_category=None,
            armor_category="Light",
        )
        chain_mail = self._create_mock_equipment(
            "chain-mail",
            "Chain Mail",
            equipment_category="armor",
            weapon_category=None,
            armor_category="Heavy",
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [leather, chain_mail]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_armor_by_category("Light")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Leather Armor"

    def test_get_by_cost_range(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting equipment by cost range."""
        # Create mock equipment
        cheap = self._create_mock_equipment(
            "club", "Club", cost={"quantity": 1, "unit": "sp"}
        )
        medium = self._create_mock_equipment(
            "longsword", "Longsword", cost={"quantity": 15, "unit": "gp"}
        )
        expensive = self._create_mock_equipment(
            "plate", "Plate", cost={"quantity": 1500, "unit": "gp"}
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [cheap, medium, expensive]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute - get items between 10gp and 100gp
        results = repository.get_by_cost_range(10, 100)

        # Verify
        assert len(results) == 1
        assert results[0].name == "Longsword"

    def test_get_weapons_with_property(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting weapons with a specific property."""
        # Create mock weapons
        rapier = self._create_mock_equipment(
            "rapier",
            "Rapier",
            properties=[
                {
                    "index": "finesse",
                    "name": "Finesse",
                    "url": "/api/weapon-properties/finesse",
                }
            ],
        )
        longsword = self._create_mock_equipment(
            "longsword",
            "Longsword",
            properties=[
                {
                    "index": "versatile",
                    "name": "Versatile",
                    "url": "/api/weapon-properties/versatile",
                }
            ],
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [rapier, longsword]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_weapons_with_property("finesse")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Rapier"

    def test_get_ranged_weapons(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting ranged weapons."""
        # Create mock weapons
        longbow = self._create_mock_equipment(
            "longbow", "Longbow", weapon_range="Ranged"
        )
        longsword = self._create_mock_equipment(
            "longsword", "Longsword", weapon_range="Melee"
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [longbow, longsword]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_ranged_weapons()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Longbow"

    def test_get_melee_weapons(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting melee weapons."""
        # Create mock weapons
        longsword = self._create_mock_equipment(
            "longsword", "Longsword", weapon_range="Melee"
        )
        longbow = self._create_mock_equipment(
            "longbow", "Longbow", weapon_range="Ranged"
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [longsword, longbow]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_melee_weapons()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Longsword"

    def test_get_tools(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting tools."""
        # Create mock equipment
        thieves_tools = self._create_mock_equipment(
            "thieves-tools",
            "Thieves' Tools",
            equipment_category="tools",
            weapon_category=None,
        )
        longsword = self._create_mock_equipment("longsword", "Longsword")

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [thieves_tools, longsword]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.get_tools()

        # Verify
        assert len(results) == 1
        assert results[0].name == "Thieves' Tools"

    def test_get_lightest_armor_by_ac(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test getting the lightest armor by AC."""
        # Create mock armor
        leather = self._create_mock_equipment(
            "leather-armor",
            "Leather Armor",
            equipment_category="armor",
            weapon_category=None,
            armor_category="Light",
            weight=10.0,
            armor_class={"base": 11, "dex_bonus": True},
        )
        studded = self._create_mock_equipment(
            "studded-leather",
            "Studded Leather",
            equipment_category="armor",
            weapon_category=None,
            armor_category="Light",
            weight=13.0,
            armor_class={"base": 12, "dex_bonus": True},
        )

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [leather, studded]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute - find lightest armor with at least 12 AC
        result = repository.get_lightest_armor_by_ac(12)

        # Verify
        assert result is not None
        assert result.name == "Studded Leather"

    def test_search_by_description(
        self,
        repository: DbEquipmentRepository,
        database_manager: Mock,
        session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test searching equipment by description."""
        # Create mock equipment
        sword = self._create_mock_equipment("longsword", "Longsword")
        torch = self._create_mock_equipment(
            "torch",
            "Torch",
            equipment_category="adventuring-gear",
            weapon_category=None,
        )

        # Add desc to torch
        torch.desc = ["A torch burns for 1 hour, providing bright light..."]

        # Mock the query chain
        query_mock = Mock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [sword, torch]

        session.query.return_value = query_mock
        database_manager.get_session.return_value = context_manager

        # Execute
        results = repository.search_by_description("sword")

        # Verify
        assert len(results) == 1
        assert results[0].name == "Longsword"
