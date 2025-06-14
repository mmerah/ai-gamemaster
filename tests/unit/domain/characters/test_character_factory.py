"""
Unit tests for character factory module.
"""

import unittest
from unittest.mock import Mock

from app.domain.characters.factories import (
    CharacterFactory,
    create_character_factory,
)
from app.models.utils import ArmorModel, D5EClassModel, ItemModel


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
        self.d5e_classes = {
            "fighter": D5EClassModel(
                name="fighter",
                hit_die=10,
                primary_ability="STR",
                saving_throw_proficiencies=["STR", "CON"],
                skill_proficiencies=[
                    "Acrobatics",
                    "Athletics",
                    "History",
                    "Insight",
                    "Intimidation",
                    "Perception",
                    "Survival",
                ],
                num_skill_proficiencies=2,
            ),
            "wizard": D5EClassModel(
                name="wizard",
                hit_die=6,
                primary_ability="INT",
                saving_throw_proficiencies=["INT", "WIS"],
                skill_proficiencies=[
                    "Arcana",
                    "History",
                    "Insight",
                    "Investigation",
                    "Medicine",
                    "Religion",
                ],
                num_skill_proficiencies=2,
            ),
            "ranger": D5EClassModel(
                name="ranger",
                hit_die=10,
                primary_ability="DEX",
                saving_throw_proficiencies=["STR", "DEX"],
                skill_proficiencies=[
                    "Animal Handling",
                    "Athletics",
                    "Insight",
                    "Investigation",
                    "Nature",
                    "Perception",
                    "Stealth",
                    "Survival",
                ],
                num_skill_proficiencies=3,
            ),
        }

        self.d5e_armor = {
            "leather armor": ArmorModel(name="leather armor", base_ac=11, type="light"),
            "scale mail": ArmorModel(
                name="scale mail", base_ac=14, type="medium", max_dex_bonus=2
            ),
            "plate": ArmorModel(
                name="plate", base_ac=18, type="heavy", max_dex_bonus=0
            ),
            "shield": ArmorModel(name="shield", base_ac=0, ac_bonus=2, type="shield"),
        }

        self.factory = CharacterFactory(self.d5e_classes, self.d5e_armor)

    def test_create_character_factory(self) -> None:
        """Test factory creation function."""
        factory = create_character_factory(self.d5e_classes, self.d5e_armor)
        self.assertIsInstance(factory, CharacterFactory)
        self.assertEqual(factory.d5e_classes_data, self.d5e_classes)
        self.assertEqual(factory.armor_data, self.d5e_armor)

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

        # Test actual minimum case (when calculation would be 0 or negative)
        template.base_stats = Mock()
        template.base_stats.CON = 1  # -5 modifier
        hp = self.factory._calculate_character_hit_points(template)
        self.assertEqual(hp, 1)  # 6 + (-5) = 1, already at minimum

    def test_ac_calculation_unarmored(self) -> None:
        """Test AC calculation without armor."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 16  # +3 modifier
        template.starting_equipment = []

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 13)  # 10 + 3 (DEX)

    def test_ac_calculation_light_armor(self) -> None:
        """Test AC calculation with light armor."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 18  # +4 modifier
        template.starting_equipment = [self._create_mock_item("Leather Armor", 1)]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 15)  # 11 (leather) + 4 (DEX)

    def test_ac_calculation_medium_armor(self) -> None:
        """Test AC calculation with medium armor (DEX cap)."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 18  # +4 modifier, but capped at +2
        template.starting_equipment = [self._create_mock_item("Scale Mail", 1)]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 16)  # 14 (scale mail) + 2 (capped DEX)

    def test_ac_calculation_heavy_armor(self) -> None:
        """Test AC calculation with heavy armor (no DEX)."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 18  # +4 modifier, but ignored
        template.starting_equipment = [self._create_mock_item("Plate", 1)]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 18)  # 18 (plate), no DEX bonus

    def test_ac_calculation_with_shield(self) -> None:
        """Test AC calculation with shield."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 14  # +2 modifier
        template.starting_equipment = [
            self._create_mock_item("Leather Armor", 1),
            self._create_mock_item("Shield", 1),
        ]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 15)  # 11 (leather) + 2 (DEX) + 2 (shield)

    def test_unknown_class_defaults(self) -> None:
        """Test handling of unknown character class."""
        template = Mock()
        template.char_class = "Unknown Class"
        template.level = 1
        template.base_stats = Mock()
        template.base_stats.CON = 14

        hp = self.factory._calculate_character_hit_points(template)
        self.assertEqual(hp, 10)  # 8 (default) + 2 (CON mod)

    def test_unknown_armor_defaults(self) -> None:
        """Test handling of unknown armor."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 16
        template.starting_equipment = [self._create_mock_item("Unknown Armor", 1)]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 13)  # 10 + 3 (DEX), armor not found

    def test_case_insensitive_equipment(self) -> None:
        """Test that equipment matching is case insensitive."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 14
        template.starting_equipment = [
            self._create_mock_item("LEATHER ARMOR", 1)  # Different case
        ]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 13)  # 11 (leather) + 2 (DEX)

    def test_multiple_armor_pieces(self) -> None:
        """Test that only first armor piece is used."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 14
        template.starting_equipment = [
            self._create_mock_item("Leather Armor", 1),
            self._create_mock_item("Plate", 1),  # Should be ignored
        ]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 13)  # Uses leather armor (first found)

    def test_empty_equipment(self) -> None:
        """Test handling of empty equipment list."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 14
        template.starting_equipment = []

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 12)  # 10 + 2 (DEX), no armor

    def test_malformed_equipment(self) -> None:
        """Test handling of malformed equipment entries."""
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 14
        template.starting_equipment = [
            {"quantity": 1},  # Missing name
            "not a dict",  # Wrong type
            self._create_mock_item("Leather Armor", 1),  # Valid entry
        ]

        ac = self.factory._calculate_character_armor_class(template)
        self.assertEqual(ac, 13)  # Should still find valid armor


class TestCharacterFactoryEdgeCases(unittest.TestCase):
    """Test edge cases for character factory."""

    def _create_mock_item(self, name: str, quantity: int = 1) -> Mock:
        """Helper to create a mock equipment item."""
        item = Mock(spec=ItemModel)
        item.name = name
        item.quantity = quantity
        return item

    def test_missing_stats(self) -> None:
        """Test handling of missing ability scores."""
        factory = CharacterFactory({}, {})
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.STR = 14  # Missing other stats
        template.base_stats.CON = None  # Missing CON
        template.base_stats.DEX = None  # Missing DEX
        template.level = 1
        template.char_class = "Fighter"
        template.starting_equipment = []

        # Should handle missing stats gracefully
        hp = factory._calculate_character_hit_points(template)
        ac = factory._calculate_character_armor_class(template)

        self.assertGreaterEqual(hp, 1)  # Should have at least 1 HP
        self.assertGreaterEqual(ac, 10)  # Should have at least base AC

    def test_invalid_stat_values(self) -> None:
        """Test handling of invalid ability score values."""
        factory = CharacterFactory({}, {})
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.CON = "invalid"
        template.base_stats.DEX = None
        template.level = 1
        template.char_class = "Fighter"
        template.starting_equipment = []

        # Should handle invalid values gracefully
        hp = factory._calculate_character_hit_points(template)
        ac = factory._calculate_character_armor_class(template)

        self.assertGreaterEqual(hp, 1)
        self.assertGreaterEqual(ac, 10)

    def test_empty_class_data(self) -> None:
        """Test factory with empty class data."""
        factory = CharacterFactory({}, {})
        template = Mock()
        template.char_class = "Fighter"
        template.level = 1
        template.base_stats = Mock()
        template.base_stats.CON = 14
        template.starting_equipment = []

        hp = factory._calculate_character_hit_points(template)
        self.assertGreaterEqual(hp, 1)  # Should use defaults

    def test_empty_armor_data(self) -> None:
        """Test factory with empty armor data."""
        factory = CharacterFactory({}, {})
        template = Mock()
        template.base_stats = Mock()
        template.base_stats.DEX = 16
        template.starting_equipment = [self._create_mock_item("Leather Armor", 1)]
        template.level = 1
        template.char_class = "Fighter"

        ac = factory._calculate_character_armor_class(template)
        self.assertGreaterEqual(ac, 10)  # Should have at least base AC


if __name__ == "__main__":
    unittest.main()
