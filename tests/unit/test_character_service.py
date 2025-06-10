"""
Unit tests for character service functionality.
"""

import unittest
from typing import ClassVar

from app.core.container import ServiceContainer, reset_container
from app.models.models import (
    BaseStatsModel,
    CharacterInstanceModel,
    CharacterTemplateModel,
    ProficienciesModel,
)
from app.repositories.game_state_repository import GameStateRepository
from app.services.character_service import (
    CharacterService,
    CharacterStatsCalculator,
    CharacterValidator,
)
from tests.conftest import get_test_config


class TestCharacterService(unittest.TestCase):
    """Test character service functionality."""

    container: ClassVar[ServiceContainer]
    character_service: ClassVar[CharacterService]
    repo: ClassVar[GameStateRepository]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_config())
        cls.container.initialize()
        cls.character_service = cls.container.get_character_service()
        cls.repo = cls.container.get_game_state_repository()

    def setUp(self) -> None:
        """Reset game state before each test."""
        # Reset to fresh game state by creating new game state
        from app.models.models import GameStateModel

        game_state = GameStateModel()
        self.repo.save_game_state(game_state)

        # Add test characters to the game state
        game_state = self.repo.get_game_state()
        game_state.party["char1"] = CharacterInstanceModel(
            template_id="torvin_stonebeard",
            campaign_id="test",
            current_hp=25,
            max_hp=25,
            temp_hp=0,
            experience_points=0,
            level=3,
            spell_slots_used={},
            hit_dice_used=0,
            death_saves={"successes": 0, "failures": 0},
            inventory=[],
            gold=100,
            conditions=[],
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={},
        )
        game_state.party["char2"] = CharacterInstanceModel(
            template_id="elara_meadowlight",
            campaign_id="test",
            current_hp=18,
            max_hp=18,
            temp_hp=0,
            experience_points=0,
            level=3,
            spell_slots_used={},
            hit_dice_used=0,
            death_saves={"successes": 0, "failures": 0},
            inventory=[],
            gold=100,
            conditions=[],
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={},
        )
        game_state.party["char3"] = CharacterInstanceModel(
            template_id="zaltar_mystic",
            campaign_id="test",
            current_hp=15,
            max_hp=15,
            temp_hp=0,
            experience_points=0,
            level=3,
            spell_slots_used={},
            hit_dice_used=0,
            death_saves={"successes": 0, "failures": 0},
            inventory=[],
            gold=100,
            conditions=[],
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={},
        )

    def test_get_character(self) -> None:
        """Test getting character by ID."""
        char_data = self.character_service.get_character("char1")
        self.assertIsNotNone(char_data)
        assert char_data is not None  # Type guard for mypy
        self.assertEqual(char_data.template.name, "Torvin Stonebeard")
        self.assertEqual(char_data.character_id, "char1")

        # Test non-existent character
        char_data = self.character_service.get_character("nonexistent")
        self.assertIsNone(char_data)

    def test_get_character_name(self) -> None:
        """Test getting character display names."""
        name = self.character_service.get_character_name("char1")
        self.assertEqual(name, "Torvin Stonebeard")

        # Test fallback to ID for unknown character
        name = self.character_service.get_character_name("unknown")
        self.assertEqual(name, "unknown")

    def test_find_character_by_name_or_id(self) -> None:
        """Test finding characters by name or ID."""
        # Test all party members can be found by name
        result = self.character_service.find_character_by_name_or_id(
            "Elara Meadowlight"
        )
        self.assertEqual(result, "char2")

        result = self.character_service.find_character_by_name_or_id("Zaltar Mystic")
        self.assertEqual(result, "char3")

        # Test case insensitive search
        result = self.character_service.find_character_by_name_or_id(
            "torvin stonebeard"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result, "char1")

        # Test direct ID lookup
        result = self.character_service.find_character_by_name_or_id("char2")
        self.assertIsNotNone(result)
        self.assertEqual(result, "char2")

        # Test partial name matching doesn't work (should be exact)
        result = self.character_service.find_character_by_name_or_id("Elara")
        self.assertIsNone(result)

        # Test non-existent character
        result = self.character_service.find_character_by_name_or_id("NonExistent")
        self.assertIsNone(result)

    def test_invalid_character_operations(self) -> None:
        """Test operations with invalid character IDs."""
        # Test with None - skip this as it's a type error
        # result = self.character_service.find_character_by_name_or_id(None)
        # self.assertIsNone(result)

        # Test with empty string
        result = self.character_service.find_character_by_name_or_id("")
        self.assertIsNone(result)

        # Test getting non-existent character
        char = self.character_service.get_character("nonexistent")
        self.assertIsNone(char)


class TestCharacterValidator(unittest.TestCase):
    """Test character validation utilities."""

    container: ServiceContainer
    repo: GameStateRepository

    def setUp(self) -> None:
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer(get_test_config())
        self.container.initialize()
        self.repo = self.container.get_game_state_repository()

        # Add test characters to the game state
        game_state = self.repo.get_game_state()
        game_state.party["char1"] = CharacterInstanceModel(
            template_id="torvin_stonebeard",
            campaign_id="test",
            current_hp=25,
            max_hp=25,
            temp_hp=0,
            experience_points=0,
            level=3,
            spell_slots_used={},
            hit_dice_used=0,
            death_saves={"successes": 0, "failures": 0},
            inventory=[],
            gold=100,
            conditions=[],
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={},
        )

    def test_character_defeated_check(self) -> None:
        """Test checking if character is defeated."""
        # Test healthy character
        is_defeated = CharacterValidator.is_character_defeated("char1", self.repo)
        self.assertFalse(is_defeated)

        # Modify character to be defeated
        game_state = self.repo.get_game_state()
        game_state.party["char1"].current_hp = 0
        self.repo.save_game_state(game_state)

        is_defeated = CharacterValidator.is_character_defeated("char1", self.repo)
        self.assertTrue(is_defeated)

    def test_character_incapacitated_check(self) -> None:
        """Test checking if character is incapacitated."""
        # Test healthy character
        is_incap = CharacterValidator.is_character_incapacitated("char1", self.repo)
        self.assertFalse(is_incap)

        # Add incapacitating condition
        game_state = self.repo.get_game_state()
        game_state.party["char1"].conditions.append("Unconscious")
        self.repo.save_game_state(game_state)

        is_incap = CharacterValidator.is_character_incapacitated("char1", self.repo)
        self.assertTrue(is_incap)

    def test_character_validator_edge_cases(self) -> None:
        """Test character validator with edge cases."""
        # Test with non-existent character
        result = CharacterValidator.is_character_defeated("nonexistent", self.repo)
        # Should return False or handle gracefully
        self.assertFalse(result)

        result = CharacterValidator.is_character_incapacitated("nonexistent", self.repo)
        # Should return False or handle gracefully
        self.assertFalse(result)


class TestCharacterStatsCalculator(unittest.TestCase):
    """Test character statistics calculation utilities."""

    def test_ability_modifier_calculation(self) -> None:
        """Test ability modifier calculations."""
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(10), 0)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(8), -1)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(16), 3)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(20), 5)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(3), -4)

    def test_proficiency_bonus_calculation(self) -> None:
        """Test proficiency bonus calculations."""
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(1), 2)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(4), 2)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(5), 3)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(8), 3)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(9), 4)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(20), 6)

    def test_max_hp_calculation(self) -> None:
        """Test maximum HP calculations."""
        # Create a test character template
        template = CharacterTemplateModel(
            id="test",
            name="Test",
            race="Human",
            char_class="Fighter",
            level=3,
            background="Soldier",
            alignment="Neutral",
            base_stats=BaseStatsModel(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8),
            proficiencies=ProficienciesModel(),
        )

        max_hp = CharacterStatsCalculator.calculate_max_hp(template, level=3)
        # CON 15 = +2 modifier, level 3, hit die avg 5
        # (5 + 2) * 3 = 21
        self.assertEqual(max_hp, 21)

    def test_armor_class_calculation(self) -> None:
        """Test armor class calculations."""
        template = CharacterTemplateModel(
            id="test",
            name="Test",
            race="Human",
            char_class="Rogue",
            level=1,
            background="Criminal",
            alignment="Chaotic Neutral",
            base_stats=BaseStatsModel(STR=10, DEX=16, CON=12, INT=14, WIS=10, CHA=12),
            proficiencies=ProficienciesModel(),
        )

        ac = CharacterStatsCalculator.calculate_armor_class(template)
        # Base 10 + DEX modifier (+3) = 13
        self.assertEqual(ac, 13)


if __name__ == "__main__":
    unittest.main()
