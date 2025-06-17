"""
Unit tests for NPC factory module.
"""

import unittest
from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import Mock, patch

from app.content.schemas import D5eMonster
from app.content.service import ContentService
from app.domain.npcs.factories import NPCFactory
from app.models.utils import NPCModel


class TestNPCFactory(unittest.TestCase):
    """Test NPC factory functionality."""

    def setUp(self) -> None:
        """Set up test data for each test."""
        # Mock ContentService
        self.mock_content_service = Mock(spec=ContentService)

        # Set up the hub structure for monster repository
        self.mock_content_service._hub = Mock()
        self.mock_content_service._hub.monsters = Mock()

        # Create factory
        self.factory = NPCFactory(self.mock_content_service)

        # Create mock monster data
        self.goblin_monster = Mock(spec=D5eMonster)
        self.goblin_monster.name = "Goblin"
        self.goblin_monster.size = "Small"
        self.goblin_monster.type = "humanoid"
        self.goblin_monster.alignment = "neutral evil"
        self.goblin_monster.languages = "Common, Goblin"

        self.dragon_monster = Mock(spec=D5eMonster)
        self.dragon_monster.name = "Adult Red Dragon"
        self.dragon_monster.size = "Huge"
        self.dragon_monster.type = "dragon"
        self.dragon_monster.alignment = "chaotic evil"
        self.dragon_monster.languages = "Common, Draconic"

    def test_create_npc_basic(self) -> None:
        """Test creating a basic NPC."""
        npc = self.factory.create_npc(
            name="Gandalf the Grey",
            description="A wise wizard with a long grey beard.",
        )

        self.assertIsInstance(npc, NPCModel)
        self.assertEqual(npc.name, "Gandalf the Grey")
        self.assertEqual(npc.description, "A wise wizard with a long grey beard.")
        self.assertEqual(npc.last_location, "Unknown")
        self.assertTrue(npc.id.startswith("npc_"))

    def test_create_npc_with_location(self) -> None:
        """Test creating NPC with specific location."""
        npc = self.factory.create_npc(
            name="Bilbo Baggins",
            description="A hobbit fond of adventures.",
            last_location="The Shire",
        )

        self.assertEqual(npc.last_location, "The Shire")

    def test_create_npc_with_custom_id(self) -> None:
        """Test creating NPC with custom ID."""
        custom_id = "npc_important_001"
        npc = self.factory.create_npc(
            name="Aragorn",
            description="The rightful king of Gondor.",
            npc_id=custom_id,
        )

        self.assertEqual(npc.id, custom_id)

    def test_create_shopkeeper(self) -> None:
        """Test creating a shopkeeper NPC."""
        npc = self.factory.create_shopkeeper(
            name="Barliman Butterbur",
            shop_type="inn",
            location="The Prancing Pony",
        )

        self.assertEqual(npc.name, "Barliman Butterbur")
        self.assertEqual(
            npc.description, "The proprietor of a inn in The Prancing Pony"
        )
        self.assertEqual(npc.last_location, "The Prancing Pony")

    def test_create_quest_giver(self) -> None:
        """Test creating a quest giver NPC."""
        npc = self.factory.create_quest_giver(
            name="Lord Elrond",
            role="elven lord",
            location="Rivendell",
        )

        self.assertEqual(npc.name, "Lord Elrond")
        self.assertEqual(
            npc.description, "A elven lord who might have tasks for adventurers"
        )
        self.assertEqual(npc.last_location, "Rivendell")

    def test_create_from_monster_success(self) -> None:
        """Test creating NPC from monster stat block."""
        # Mock the content service to return goblin
        self.mock_content_service._hub.monsters.get_by_name_with_options.return_value = self.goblin_monster

        npc = self.factory.create_from_monster(
            monster_index="goblin",
            location="Dark Forest",
        )

        self.assertIsNotNone(npc)
        assert npc is not None  # Type narrowing for mypy
        self.assertEqual(npc.name, "Goblin")
        self.assertEqual(
            npc.description, "A Small humanoid, neutral evil. Speaks: Common, Goblin"
        )
        self.assertEqual(npc.last_location, "Dark Forest")

        # Verify content service was called correctly
        self.mock_content_service._hub.monsters.get_by_name_with_options.assert_called_once_with(
            "goblin", content_pack_priority=None
        )

    def test_create_from_monster_with_custom_name(self) -> None:
        """Test creating NPC from monster with custom name."""
        self.mock_content_service._hub.monsters.get_by_name_with_options.return_value = self.goblin_monster

        npc = self.factory.create_from_monster(
            monster_index="goblin",
            custom_name="Grix the Cunning",
            location="Goblin Camp",
        )

        self.assertIsNotNone(npc)
        assert npc is not None  # Type narrowing for mypy
        self.assertEqual(npc.name, "Grix the Cunning")
        self.assertEqual(
            npc.description, "A Small humanoid, neutral evil. Speaks: Common, Goblin"
        )

    def test_create_from_monster_not_found(self) -> None:
        """Test creating NPC from non-existent monster."""
        self.mock_content_service._hub.monsters.get_by_name_with_options.return_value = None

        npc = self.factory.create_from_monster(
            monster_index="invalid-monster",
        )

        self.assertIsNone(npc)

    def test_create_from_monster_with_content_packs(self) -> None:
        """Test creating NPC from monster with content pack priority."""
        self.mock_content_service._hub.monsters.get_by_name_with_options.return_value = self.dragon_monster

        content_packs = ["custom_monsters", "dnd_5e_srd"]
        npc = self.factory.create_from_monster(
            monster_index="adult-red-dragon",
            content_pack_priority=content_packs,
        )

        # Verify content packs were passed through
        self.mock_content_service._hub.monsters.get_by_name_with_options.assert_called_once_with(
            "adult-red-dragon", content_pack_priority=content_packs
        )

        self.assertIsNotNone(npc)
        assert npc is not None  # Type narrowing for mypy
        self.assertEqual(npc.name, "Adult Red Dragon")
        self.assertEqual(
            npc.description, "A Huge dragon, chaotic evil. Speaks: Common, Draconic"
        )

    def test_create_from_monster_no_languages(self) -> None:
        """Test creating NPC from monster without languages."""
        # Create monster without languages
        beast_monster = Mock(spec=D5eMonster)
        beast_monster.name = "Dire Wolf"
        beast_monster.size = "Large"
        beast_monster.type = "beast"
        beast_monster.alignment = "unaligned"
        beast_monster.languages = None

        self.mock_content_service._hub.monsters.get_by_name_with_options.return_value = beast_monster

        npc = self.factory.create_from_monster("dire-wolf")

        self.assertIsNotNone(npc)
        assert npc is not None  # Type narrowing for mypy
        self.assertEqual(npc.description, "A Large beast, unaligned")

    @patch("app.domain.npcs.factories.datetime")
    @patch("app.domain.npcs.factories.uuid4")
    def test_generate_npc_id(
        self, mock_uuid: unittest.mock.Mock, mock_datetime: unittest.mock.Mock
    ) -> None:
        """Test NPC ID generation."""
        # Mock datetime to return a fixed time
        mock_now = datetime(2025, 6, 17, 14, 45, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        # Mock uuid to return a predictable value
        mock_uuid.return_value = Mock(
            __str__=Mock(return_value="abcdef12-3456-7890-abcd-ef1234567890")
        )

        # Generate ID
        npc_id = self.factory._generate_npc_id()

        # Verify format
        self.assertEqual(npc_id, "npc_20250617_144530_abcdef12")

    def test_create_various_shopkeepers(self) -> None:
        """Test creating different types of shopkeepers."""
        shop_types = [
            ("general store", "Milo Goodbarrel"),
            ("blacksmith", "Thorin Ironforge"),
            ("alchemist", "Zara the Wise"),
            ("tavern", "Red-Beard McGillicuddy"),
        ]

        for shop_type, name in shop_types:
            npc = self.factory.create_shopkeeper(
                name=name,
                shop_type=shop_type,
                location="Market Square",
            )

            self.assertEqual(npc.name, name)
            self.assertIn(shop_type, npc.description)
            self.assertEqual(npc.last_location, "Market Square")

    def test_create_various_quest_givers(self) -> None:
        """Test creating different types of quest givers."""
        quest_givers = [
            ("village elder", "Elder Thorne"),
            ("mysterious stranger", "The Hooded Figure"),
            ("guard captain", "Captain Marcus"),
            ("guild master", "Master Elara"),
        ]

        for role, name in quest_givers:
            npc = self.factory.create_quest_giver(
                name=name,
                role=role,
                location="Town Hall",
            )

            self.assertEqual(npc.name, name)
            self.assertIn(role, npc.description)
            self.assertEqual(npc.last_location, "Town Hall")

    def test_error_handling_in_create_from_monster(self) -> None:
        """Test error handling when creating from monster fails."""
        # Make content service raise an exception
        self.mock_content_service._hub.monsters.get_by_name_with_options.side_effect = (
            Exception("Database error")
        )

        npc = self.factory.create_from_monster("goblin")

        # Should return None on error
        self.assertIsNone(npc)


if __name__ == "__main__":
    unittest.main()
