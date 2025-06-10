"""
Unit tests for dice service functionality.
"""

import unittest
from typing import ClassVar

from app.core.container import ServiceContainer, reset_container
from app.core.interfaces import (
    CharacterService,
    DiceRollingService,
    GameStateRepository,
)
from app.models import CharacterInstanceModel
from tests.conftest import get_test_config


class TestDiceService(unittest.TestCase):
    """Test dice service functionality."""

    # Class variables with proper type annotations
    container: ClassVar[ServiceContainer]
    dice_service: ClassVar[DiceRollingService]
    character_service: ClassVar[CharacterService]
    repo: ClassVar[GameStateRepository]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_config())
        cls.container.initialize()
        cls.dice_service = cls.container.get_dice_service()
        cls.character_service = cls.container.get_character_service()
        cls.repo = cls.container.get_game_state_repository()

    def setUp(self) -> None:
        """Reset game state before each test."""
        # Reset container to get fresh game state
        reset_container()
        container = ServiceContainer(get_test_config())
        container.initialize()
        # Re-assign class variables with fresh instances
        TestDiceService.container = container
        TestDiceService.dice_service = container.get_dice_service()
        TestDiceService.character_service = container.get_character_service()
        TestDiceService.repo = container.get_game_state_repository()

        # Add test characters to the game state
        game_state = self.repo.get_game_state()
        game_state.party["torvin"] = CharacterInstanceModel(
            template_id="torvin_stonebeard",
            campaign_id="test",
            current_hp=32,
            max_hp=32,
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
        game_state.party["zaltar"] = CharacterInstanceModel(
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
            gold=50,
            conditions=[],
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={},
        )
        self.repo.save_game_state(game_state)

    def test_perform_basic_roll(self) -> None:
        """Test performing a basic dice roll."""
        # Get a character ID from the party
        char_id = self.character_service.find_character_by_name_or_id(
            "Torvin Stonebeard"
        )
        self.assertIsNotNone(char_id)
        assert char_id is not None  # Type guard for mypy

        # Perform a basic roll
        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="custom",
            dice_formula="1d20",
            reason="Test roll",
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.result_summary)
        self.assertIsNotNone(result.total_result)
        self.assertTrue(1 <= result.total_result <= 20)

    def test_skill_check_roll(self) -> None:
        """Test skill check dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id(
            "Torvin Stonebeard"
        )
        self.assertIsNotNone(char_id)
        assert char_id is not None  # Type guard for mypy

        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="skill_check",
            dice_formula="1d20",
            reason="Wisdom (Perception) check",
            skill="Perception",
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result.error)
        self.assertEqual(result.roll_type, "skill_check")
        self.assertIsNotNone(result.result_summary)
        # Total result includes modifiers, so can be higher than 20
        self.assertGreaterEqual(result.total_result, 1)

    def test_saving_throw_roll(self) -> None:
        """Test saving throw dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id("Zaltar Mystic")
        self.assertIsNotNone(char_id)
        assert char_id is not None  # Type guard for mypy

        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="saving_throw",
            dice_formula="1d20",
            reason="Dexterity saving throw",
            ability="DEX",
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result.error)
        self.assertEqual(result.roll_type, "saving_throw")
        self.assertIsNotNone(result.result_summary)
        # Total result includes modifiers, so can be higher than 20
        self.assertGreaterEqual(result.total_result, 1)

    def test_attack_roll(self) -> None:
        """Test attack roll dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id("Zaltar Mystic")
        self.assertIsNotNone(char_id)
        assert char_id is not None  # Type guard for mypy

        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="attack_roll",
            dice_formula="1d20",
            reason="Dagger attack",
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result.error)
        self.assertEqual(result.roll_type, "attack_roll")
        # Total result includes modifiers, so can be higher than 20
        self.assertGreaterEqual(result.total_result, 1)

    def test_damage_roll(self) -> None:
        """Test damage roll dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id(
            "Torvin Stonebeard"
        )
        self.assertIsNotNone(char_id)
        assert char_id is not None  # Type guard for mypy

        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="damage_roll",
            dice_formula="1d8+3",
            reason="Warhammer damage",
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result.error)
        self.assertEqual(result.roll_type, "damage_roll")
        self.assertIsNotNone(result.result_summary)
        # 1d8 + modifier
        self.assertGreaterEqual(result.total_result, 1)

    def test_damage_roll_no_double_modifier(self) -> None:
        """Test that damage rolls don't add character modifier twice."""
        char_id = self.character_service.find_character_by_name_or_id(
            "Torvin Stonebeard"
        )
        self.assertIsNotNone(char_id)
        assert char_id is not None  # Type guard for mypy

        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="damage_roll",
            dice_formula="2d6",
            reason="Two-handed sword damage",
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result.error)
        self.assertEqual(result.roll_type, "damage_roll")
        # For damage rolls, the character modifier should be 0
        self.assertEqual(result.character_modifier, 0)
        # 2d6 result (2-12)
        self.assertTrue(2 <= result.total_result <= 12)

    def test_advantage_disadvantage_rolls(self) -> None:
        """Test rolls with advantage/disadvantage."""
        char_id = self.character_service.find_character_by_name_or_id(
            "Torvin Stonebeard"
        )
        self.assertIsNotNone(char_id)
        assert char_id is not None  # Type guard for mypy

        # Test advantage
        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="attack_roll",
            dice_formula="2d20kh",
            reason="Attack with advantage",
        )

        self.assertIsNotNone(result)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.result_summary)
        # With advantage/disadvantage, result still in normal range
        self.assertGreaterEqual(result.total_result, 1)

    def test_dice_service_error_handling(self) -> None:
        """Test error handling in dice service."""
        # Test unknown character
        result = self.dice_service.perform_roll(
            character_id="unknown_character", roll_type="attack", dice_formula="1d20"
        )
        self.assertIsNotNone(result.error)

        # Test invalid dice formula
        char_id = self.character_service.find_character_by_name_or_id("Zaltar")
        if char_id is not None:  # Type guard for mypy
            result = self.dice_service.perform_roll(
                character_id=char_id,
                roll_type="skill_check",
                dice_formula="invalid_formula",
            )
            self.assertIsNotNone(result.error)
