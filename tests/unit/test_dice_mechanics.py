"""
Unit tests for dice mechanics module.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.game.calculators.dice_mechanics import (
    SKILL_TO_ABILITY,
    apply_keep_modifier,
    format_roll_type_description,
    get_ability_modifier,
    get_proficiency_bonus,
    parse_dice_component,
    roll_dice_formula,
    roll_multiple_dice,
    roll_single_die,
)


class TestProficiencyBonus:
    """Test proficiency bonus calculations."""

    def test_level_1_to_4(self) -> None:
        """Test proficiency bonus for levels 1-4."""
        assert get_proficiency_bonus(1) == 2
        assert get_proficiency_bonus(2) == 2
        assert get_proficiency_bonus(3) == 2
        assert get_proficiency_bonus(4) == 2

    def test_level_5_to_8(self) -> None:
        """Test proficiency bonus for levels 5-8."""
        assert get_proficiency_bonus(5) == 3
        assert get_proficiency_bonus(6) == 3
        assert get_proficiency_bonus(7) == 3
        assert get_proficiency_bonus(8) == 3

    def test_level_9_to_12(self) -> None:
        """Test proficiency bonus for levels 9-12."""
        assert get_proficiency_bonus(9) == 4
        assert get_proficiency_bonus(10) == 4
        assert get_proficiency_bonus(11) == 4
        assert get_proficiency_bonus(12) == 4

    def test_high_levels(self) -> None:
        """Test proficiency bonus for higher levels."""
        assert get_proficiency_bonus(13) == 5
        assert get_proficiency_bonus(17) == 6
        assert get_proficiency_bonus(20) == 6


class TestAbilityModifier:
    """Test ability modifier calculations."""

    def test_standard_scores(self) -> None:
        """Test ability modifiers for standard ability scores."""
        assert get_ability_modifier(10) == 0
        assert get_ability_modifier(11) == 0
        assert get_ability_modifier(12) == 1
        assert get_ability_modifier(13) == 1
        assert get_ability_modifier(14) == 2
        assert get_ability_modifier(15) == 2
        assert get_ability_modifier(16) == 3
        assert get_ability_modifier(17) == 3
        assert get_ability_modifier(18) == 4
        assert get_ability_modifier(20) == 5

    def test_low_scores(self) -> None:
        """Test ability modifiers for low ability scores."""
        assert get_ability_modifier(8) == -1
        assert get_ability_modifier(6) == -2
        assert get_ability_modifier(3) == -4
        assert get_ability_modifier(1) == -5

    def test_edge_cases(self) -> None:
        """Test edge cases for ability modifiers."""
        assert get_ability_modifier(None) == 0
        assert get_ability_modifier("invalid") == 0  # type: ignore[arg-type]
        assert get_ability_modifier(0) == -5


class TestDiceRolling:
    """Test dice rolling functions."""

    @patch("app.game.calculators.dice_mechanics.random.randint")
    def test_roll_single_die(self, mock_randint: MagicMock) -> None:
        """Test rolling a single die."""
        mock_randint.return_value = 15
        assert roll_single_die(20) == 15
        mock_randint.assert_called_once_with(1, 20)

    def test_roll_single_die_invalid(self) -> None:
        """Test rolling with invalid parameters."""
        with pytest.raises(ValueError):
            roll_single_die(0)
        with pytest.raises(ValueError):
            roll_single_die(-5)

    @patch("app.game.calculators.dice_mechanics.random.randint")
    def test_roll_multiple_dice(self, mock_randint: MagicMock) -> None:
        """Test rolling multiple dice."""
        mock_randint.side_effect = [4, 2, 6]
        result = roll_multiple_dice(3, 6)
        assert result == [4, 2, 6]
        assert mock_randint.call_count == 3

    def test_roll_multiple_dice_invalid(self) -> None:
        """Test rolling multiple dice with invalid parameters."""
        with pytest.raises(ValueError):
            roll_multiple_dice(0, 6)
        with pytest.raises(ValueError):
            roll_multiple_dice(3, 0)


class TestKeepModifiers:
    """Test keep highest/lowest modifiers."""

    def test_keep_highest(self) -> None:
        """Test keep highest modifier."""
        rolls = [1, 4, 2, 6, 3]
        result = apply_keep_modifier(rolls, "kh", 3)
        assert result == [6, 4, 3]

    def test_keep_lowest(self) -> None:
        """Test keep lowest modifier."""
        rolls = [1, 4, 2, 6, 3]
        result = apply_keep_modifier(rolls, "kl", 2)
        assert result == [1, 2]

    def test_keep_all(self) -> None:
        """Test keeping more dice than available."""
        rolls = [1, 4]
        result = apply_keep_modifier(rolls, "kh", 5)
        assert result == [4, 1]

    def test_empty_rolls(self) -> None:
        """Test keep modifier with empty rolls."""
        result = apply_keep_modifier([], "kh", 3)
        assert result == []

    def test_unknown_modifier(self) -> None:
        """Test unknown keep modifier."""
        rolls = [1, 4, 2]
        result = apply_keep_modifier(rolls, "unknown", 2)
        assert result == [1, 4, 2]  # Should return original rolls


class TestDiceComponentParsing:
    """Test dice component parsing."""

    def test_simple_dice(self) -> None:
        """Test parsing simple dice notation."""
        num_dice, die_size, keep_type, keep_count = parse_dice_component("2d6")
        assert num_dice == 2
        assert die_size == 6
        assert keep_type is None
        assert keep_count is None

    def test_single_die(self) -> None:
        """Test parsing single die notation."""
        num_dice, die_size, keep_type, keep_count = parse_dice_component("d20")
        assert num_dice == 1
        assert die_size == 20
        assert keep_type is None
        assert keep_count is None

    def test_keep_highest(self) -> None:
        """Test parsing keep highest notation."""
        num_dice, die_size, keep_type, keep_count = parse_dice_component("4d6kh3")
        assert num_dice == 4
        assert die_size == 6
        assert keep_type == "kh"
        assert keep_count == 3

    def test_keep_lowest(self) -> None:
        """Test parsing keep lowest notation."""
        num_dice, die_size, keep_type, keep_count = parse_dice_component("3d20kl1")
        assert num_dice == 3
        assert die_size == 20
        assert keep_type == "kl"
        assert keep_count == 1

    def test_invalid_dice(self) -> None:
        """Test parsing invalid dice notation."""
        with pytest.raises(ValueError):
            parse_dice_component("invalid")
        with pytest.raises(ValueError):
            parse_dice_component("2x6")


class TestDiceFormula:
    """Test complete dice formula parsing and rolling."""

    @patch("app.game.calculators.dice_mechanics.random.randint")
    def test_simple_formula(self, mock_randint: MagicMock) -> None:
        """Test simple dice formula."""
        mock_randint.return_value = 10
        total, rolls, modifier, desc = roll_dice_formula("1d20")
        assert total == 10
        assert rolls == [10]
        assert modifier == 0
        assert "1d20" in desc

    @patch("app.game.calculators.dice_mechanics.random.randint")
    def test_formula_with_modifier(self, mock_randint: MagicMock) -> None:
        """Test dice formula with modifier."""
        mock_randint.side_effect = [3, 4]
        total, rolls, modifier, desc = roll_dice_formula("2d6+5")
        assert total == 12  # 3+4+5
        assert rolls == [3, 4]
        assert modifier == 5

    @patch("app.game.calculators.dice_mechanics.random.randint")
    def test_formula_with_negative_modifier(self, mock_randint: MagicMock) -> None:
        """Test dice formula with negative modifier."""
        mock_randint.return_value = 15
        total, rolls, modifier, desc = roll_dice_formula("1d20-2")
        assert total == 13  # 15-2
        assert rolls == [15]
        assert modifier == -2

    def test_invalid_formula(self) -> None:
        """Test invalid dice formula."""
        total, rolls, modifier, desc = roll_dice_formula("")
        assert total == 0
        assert rolls == []
        assert modifier == 0
        assert "Invalid" in desc

    def test_non_string_formula(self) -> None:
        """Test non-string dice formula."""
        total, rolls, modifier, desc = roll_dice_formula(None)  # type: ignore[arg-type]
        assert total == 0
        assert rolls == []
        assert modifier == 0
        assert "Invalid" in desc

    def test_simple_formula_with_d4(self) -> None:
        """Test simple d4 formula (from test_game_utils.py)."""
        total, rolls, modifier, description = roll_dice_formula("1d4+3")
        assert isinstance(total, int)
        assert isinstance(rolls, list)
        assert isinstance(modifier, int)
        assert isinstance(description, str)
        assert modifier == 3
        assert len(rolls) == 1  # Should have one d4 roll
        assert 1 <= rolls[0] <= 4  # d4 should be between 1-4


class TestRollTypeDescription:
    """Test roll type description formatting."""

    def test_skill_check(self) -> None:
        """Test skill check description."""
        result = format_roll_type_description("skill_check", "perception", None)
        assert result == "Perception Check"

    def test_saving_throw(self) -> None:
        """Test saving throw description."""
        result = format_roll_type_description("saving_throw", None, "dex")
        assert result == "DEX Save"

    def test_initiative(self) -> None:
        """Test initiative description."""
        result = format_roll_type_description("initiative", None, None)
        assert result == "Initiative"

    def test_generic_roll(self) -> None:
        """Test generic roll description."""
        result = format_roll_type_description("attack_roll", None, None)
        assert result == "Attack Roll"


class TestSkillToAbilityMapping:
    """Test skill to ability mapping."""

    def test_standard_skills(self) -> None:
        """Test standard D&D 5e skills map correctly."""
        assert SKILL_TO_ABILITY["acrobatics"] == "DEX"
        assert SKILL_TO_ABILITY["athletics"] == "STR"
        assert SKILL_TO_ABILITY["perception"] == "WIS"
        assert SKILL_TO_ABILITY["persuasion"] == "CHA"
        assert SKILL_TO_ABILITY["investigation"] == "INT"
        assert SKILL_TO_ABILITY["medicine"] == "WIS"

    def test_all_skills_present(self) -> None:
        """Test that all standard skills are present."""
        expected_skills = [
            "acrobatics",
            "animal handling",
            "arcana",
            "athletics",
            "deception",
            "history",
            "insight",
            "intimidation",
            "investigation",
            "medicine",
            "nature",
            "perception",
            "performance",
            "persuasion",
            "religion",
            "sleight of hand",
            "stealth",
            "survival",
        ]

        for skill in expected_skills:
            assert skill in SKILL_TO_ABILITY
            assert SKILL_TO_ABILITY[skill] in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
