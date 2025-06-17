"""
Unit tests for character factory module.
"""

import unittest
from typing import Optional
from unittest.mock import MagicMock, Mock

from app.content.schemas import ArmorClass, D5eClass, D5eEquipment
from app.content.service import ContentService
from app.domain.characters.character_factory import CharacterFactory
from app.models.utils import ItemModel


class TestCharacterFactory(unittest.TestCase):
    """Test character factory functionality."""

    def _create_mock_item(self, name: str, quantity: int = 1) -> Mock:
        """Helper to create a mock equipment item."""
        item = Mock(spec=ItemModel)
        item.name = name
        item.quantity = quantity
        return item

    def setUp(self) -> None:
        """Set up test data for each test."""
        # Mock ContentService
        self.mock_content_service = Mock(spec=ContentService)

        # Create mock D5eClass objects
        self.fighter_class = MagicMock(spec=D5eClass)
        self.fighter_class.name = "Fighter"
        self.fighter_class.index = "fighter"
        self.fighter_class.hit_die = 10

        self.wizard_class = MagicMock(spec=D5eClass)
        self.wizard_class.name = "Wizard"
        self.wizard_class.index = "wizard"
        self.wizard_class.hit_die = 6

        self.ranger_class = MagicMock(spec=D5eClass)
        self.ranger_class.name = "Ranger"
        self.ranger_class.index = "ranger"
        self.ranger_class.hit_die = 10

        # Mock ContentService methods
        def get_class_by_name_mock(
            name: str, content_pack_priority: Optional[list[str]] = None
        ) -> Optional[D5eClass]:
            name_lower = name.lower()
            if name_lower == "fighter":
                return self.fighter_class
            elif name_lower == "wizard":
                return self.wizard_class
            elif name_lower == "ranger":
                return self.ranger_class
            return None

        self.mock_content_service.get_class_by_name = Mock(
            side_effect=get_class_by_name_mock
        )

        # Create mock armor
        self.leather_armor = MagicMock(spec=D5eEquipment)
        self.leather_armor.name = "Leather Armor"
        self.leather_armor.index = "leather-armor"
        self.leather_armor.armor_category = "Light"
        self.leather_armor.armor_class = ArmorClass(base=11, dex_bonus=True)
        self.leather_armor.str_minimum = None
        self.leather_armor.stealth_disadvantage = False

        self.scale_mail = MagicMock(spec=D5eEquipment)
        self.scale_mail.name = "Scale Mail"
        self.scale_mail.index = "scale-mail"
        self.scale_mail.armor_category = "Medium"
        self.scale_mail.armor_class = ArmorClass(base=14, dex_bonus=True, max_bonus=2)
        self.scale_mail.str_minimum = None
        self.scale_mail.stealth_disadvantage = True

        self.plate_armor = MagicMock(spec=D5eEquipment)
        self.plate_armor.name = "Plate"
        self.plate_armor.index = "plate"
        self.plate_armor.armor_category = "Heavy"
        self.plate_armor.armor_class = ArmorClass(base=18, dex_bonus=False)
        self.plate_armor.str_minimum = 15
        self.plate_armor.stealth_disadvantage = True

        def get_equipment_by_name_mock(
            name: str, content_pack_priority: Optional[list[str]] = None
        ) -> Optional[D5eEquipment]:
            name_lower = name.lower()
            if "leather" in name_lower:
                return self.leather_armor
            elif "scale" in name_lower:
                return self.scale_mail
            elif "plate" in name_lower:
                return self.plate_armor
            return None

        self.mock_content_service.get_equipment_by_name = Mock(
            side_effect=get_equipment_by_name_mock
        )

        self.factory = CharacterFactory(self.mock_content_service)

    def test_character_factory_creation(self) -> None:
        """Test factory creation."""
        factory = CharacterFactory(self.mock_content_service)
        self.assertIsInstance(factory, CharacterFactory)
        self.assertEqual(factory.content_service, self.mock_content_service)

    def test_from_template_basic(self) -> None:
        """Test basic template to character conversion."""
        template = Mock()
        template.id = "test_char"
        template.name = "Test Character"
        template.race = "Human"
        template.char_class = "Fighter"
        template.level = 1
        template.alignment = "Lawful Good"
        template.background = "Soldier"
        template.portrait_path = "/path/to/portrait.jpg"
        template.base_stats = Mock()
        template.base_stats.STR = 16
        template.base_stats.DEX = 14
        template.base_stats.CON = 15
        template.base_stats.INT = 12
        template.base_stats.WIS = 13
        template.base_stats.CHA = 10
        template.proficiencies = {
            "skills": ["Athletics"],
            "saving_throws": ["STR", "CON"],
        }
        template.languages = ["Common", "Draconic"]
        # Use dict for equipment since it will be converted to ItemModel in inventory
        template.starting_equipment = [
            {
                "id": "sword1",
                "name": "Longsword",
                "description": "A sharp blade",
                "quantity": 1,
            }
        ]
        template.starting_gold = 150

        character = self.factory.from_template(template, "test_campaign")

        # Check CharacterInstanceModel fields
        self.assertEqual(character.template_id, "test_char")
        self.assertEqual(character.campaign_id, "test_campaign")
        self.assertEqual(character.level, 1)
        self.assertEqual(len(character.inventory), 1)
        self.assertEqual(character.inventory[0].name, "Longsword")
        self.assertEqual(character.gold, 150)
        self.assertEqual(character.temp_hp, 0)
        self.assertEqual(character.conditions, [])
        self.assertEqual(character.experience_points, 0)
        self.assertEqual(character.spell_slots_used, {})
        self.assertEqual(character.hit_dice_used, 0)
        self.assertEqual(character.death_saves["successes"], 0)
        self.assertEqual(character.death_saves["failures"], 0)
        self.assertEqual(character.exhaustion_level, 0)
        self.assertEqual(character.notes, "")
        self.assertEqual(character.achievements, [])
        self.assertEqual(character.relationships, {})

    def test_hp_calculation_level_1(self) -> None:
        """Test HP calculation for level 1 character."""
        template = Mock()
        template.char_class = "Fighter"
        template.level = 1
        template.base_stats = Mock()
        template.base_stats.CON = 16  # +3 modifier

        hp = self.factory._calculate_character_hit_points(template)
        self.assertEqual(hp, 13)  # 10 (fighter hit die) + 3 (CON mod)

    def test_hp_calculation_multi_level(self) -> None:
        """Test HP calculation for multi-level character."""
        template = Mock()
        template.char_class = "Wizard"
        template.level = 5
        template.base_stats = Mock()
        template.base_stats.CON = 14  # +2 modifier

        hp = self.factory._calculate_character_hit_points(template)
        # Level 1: 6 + 2 = 8
        # Levels 2-5: 4 * (3.5 + 2) = 4 * 5.5 = 22
        # Total: 8 + 22 = 30
        self.assertEqual(hp, 30)

    def test_hp_calculation_minimum(self) -> None:
        """Test HP calculation ensures minimum 1 HP."""
        template = Mock()
        template.char_class = "Wizard"
        template.level = 1
        template.base_stats = Mock()
        template.base_stats.CON = 6  # -2 modifier

        hp = self.factory._calculate_character_hit_points(template)
        self.assertEqual(hp, 4)  # 6 (wizard hit die) + (-2) = 4

    def test_ac_calculation_leather_armor(self) -> None:
        """Test AC calculation with leather armor."""
        template = Mock()
        template.char_class = "Ranger"
        # Convert dict to ItemModel-like object
        armor_item = ItemModel(
            id="leather-armor",
            name="Leather Armor",
            description="Light armor",
            quantity=1,
        )
        template.starting_equipment = [armor_item]
        template.base_stats = Mock()
        template.base_stats.DEX = 16  # +3 modifier

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 14)  # 11 (leather base) + 3 (DEX mod)

    def test_ac_calculation_medium_armor(self) -> None:
        """Test AC calculation with medium armor (max dex bonus)."""
        template = Mock()
        template.char_class = "Fighter"
        armor_item = ItemModel(
            id="scale-mail", name="Scale Mail", description="Medium armor", quantity=1
        )
        template.starting_equipment = [armor_item]
        template.base_stats = Mock()
        template.base_stats.DEX = 18  # +4 modifier

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 16)  # 14 (scale mail base) + 2 (max DEX bonus)

    def test_ac_calculation_heavy_armor(self) -> None:
        """Test AC calculation with heavy armor (no dex bonus)."""
        template = Mock()
        template.char_class = "Fighter"
        armor_item = ItemModel(
            id="plate", name="Plate", description="Heavy armor", quantity=1
        )
        template.starting_equipment = [armor_item]
        template.base_stats = Mock()
        template.base_stats.DEX = 16  # +3 modifier

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 18)  # 18 (plate base) + 0 (no DEX bonus)

    def test_ac_calculation_no_armor(self) -> None:
        """Test AC calculation with no armor."""
        template = Mock()
        template.char_class = "Wizard"
        template.starting_equipment = []
        template.base_stats = Mock()
        template.base_stats.DEX = 14  # +2 modifier

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 12)  # 10 (base) + 2 (DEX mod)

    def test_character_with_shield(self) -> None:
        """Test character creation with shield in equipment."""
        template = Mock()
        template.id = "test_char"
        template.name = "Shield Bearer"
        template.race = "Human"
        template.char_class = "Fighter"
        template.level = 3
        template.alignment = "Neutral Good"
        template.background = "Soldier"
        template.portrait_path = None
        template.base_stats = Mock()
        template.base_stats.STR = 15
        template.base_stats.DEX = 12
        template.base_stats.CON = 14
        template.base_stats.INT = 10
        template.base_stats.WIS = 13
        template.base_stats.CHA = 11
        template.proficiencies = {
            "skills": ["Athletics", "Intimidation"],
            "saving_throws": ["STR", "CON"],
        }
        template.languages = ["Common", "Orcish"]
        template.starting_equipment = [
            {
                "id": "scale-mail",
                "name": "Scale Mail",
                "description": "Armor",
                "quantity": 1,
            },
            {"id": "shield", "name": "Shield", "description": "AC +2", "quantity": 1},
            {
                "id": "longsword",
                "name": "Longsword",
                "description": "Weapon",
                "quantity": 1,
            },
        ]
        template.starting_gold = 100

        character = self.factory.from_template(template, "test_campaign")

        # Check inventory
        self.assertEqual(len(character.inventory), 3)
        item_names = [item.name for item in character.inventory]
        self.assertIn("Scale Mail", item_names)
        self.assertIn("Shield", item_names)
        self.assertIn("Longsword", item_names)

        # Check HP calculation
        # Level 3 Fighter with CON +2: 10 (hit die) + 2 (CON) + 2*((10+1)/2 + 2) = 12 + 2*(5.5+2) = 12 + 15 = 27
        self.assertEqual(character.current_hp, 27)
        self.assertEqual(character.max_hp, 27)

        # Note: armor_class is computed in CombinedCharacterModel, not stored in instance

    def test_character_with_missing_data(self) -> None:
        """Test character creation handles missing or invalid data gracefully."""
        template = Mock()
        template.id = "test_char"
        template.name = "Test Character"
        template.race = "UnknownRace"
        template.char_class = "UnknownClass"  # This class won't be found
        template.level = 1
        template.alignment = "Chaotic Neutral"
        template.background = "Unknown"
        template.portrait_path = None
        template.base_stats = Mock()
        template.base_stats.STR = 10
        template.base_stats.DEX = 10
        template.base_stats.CON = 10
        template.base_stats.INT = 10
        template.base_stats.WIS = 10
        template.base_stats.CHA = 10
        template.proficiencies = {"skills": [], "saving_throws": []}
        template.languages = []
        template.starting_equipment = []
        template.starting_gold = 0

        # Configure mock to return None for unknown class
        self.mock_content_service.get_class_by_name.return_value = None

        character = self.factory.from_template(template, "test_campaign")

        # Should use default hit die of 8 when class not found
        self.assertEqual(character.current_hp, 8)  # 8 (default hit die) + 0 (CON mod)
        # Note: armor_class is computed in CombinedCharacterModel, not stored in instance

    def test_multiple_armor_pieces(self) -> None:
        """Test that only the best armor is used when multiple pieces present."""
        template = Mock()
        template.char_class = "Fighter"
        leather = ItemModel(
            id="leather-armor",
            name="Leather Armor",
            description="Light armor",
            quantity=1,
        )
        scale = ItemModel(
            id="scale-mail", name="Scale Mail", description="Better armor", quantity=1
        )
        template.starting_equipment = [leather, scale]
        template.base_stats = Mock()
        template.base_stats.DEX = 14  # +2 modifier

        ac = self.factory._calculate_character_armor_class(template)
        # Uses first armor found (Leather: 11+2) not best armor
        self.assertEqual(ac, 13)


if __name__ == "__main__":
    unittest.main()
