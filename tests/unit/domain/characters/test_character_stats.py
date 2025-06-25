"""
Unit tests for character stats calculator module.
"""

import unittest

from app.domain.shared.calculators.character_stats import (
    calculate_armor_class,
    calculate_hit_points,
    calculate_saving_throw_modifier,
    calculate_skill_modifier,
    calculate_spell_slots_by_level,
    calculate_total_modifier_for_roll,
)
from app.models.character.utils import CharacterModifierDataModel


class TestHitPointCalculation(unittest.TestCase):
    """Test hit point calculation."""

    def test_level_1_character(self) -> None:
        """Test HP calculation for level 1 character."""
        # Level 1 fighter (d10) with +2 CON modifier
        hp = calculate_hit_points(1, 2, 10, True)
        self.assertEqual(hp, 12)  # 10 (max hit die) + 2 (CON mod)

    def test_level_1_minimum_hp(self) -> None:
        """Test minimum HP at level 1."""
        # With d6 hit die and -3 CON modifier: 6 + (-3) = 3
        hp = calculate_hit_points(1, -3, 6, True)
        self.assertEqual(hp, 3)

        # Test actual minimum case - when calculation would be 0 or negative
        hp = calculate_hit_points(1, -10, 6, True)
        self.assertEqual(hp, 1)  # 6 + (-10) = -4, but minimum is 1

    def test_multi_level_average(self) -> None:
        """Test HP calculation for multi-level character using averages."""
        # Level 5 ranger (d10) with +3 CON modifier
        # Level 1: 10 + 3 = 13
        # Levels 2-5: 4 levels * (5.5 + 3) = 4 * 8.5 = 34
        # Total: 13 + 34 = 47
        hp = calculate_hit_points(5, 3, 10, True)
        self.assertEqual(hp, 47)

    def test_multi_level_maximum(self) -> None:
        """Test HP calculation using maximum rolls."""
        # Level 3 wizard (d6) with +1 CON modifier
        # Max HP: 3 * 6 + 3 * 1 = 21
        hp = calculate_hit_points(3, 1, 6, False)
        self.assertEqual(hp, 21)

    def test_invalid_level(self) -> None:
        """Test HP calculation with invalid level."""
        hp = calculate_hit_points(0, 2, 8, True)
        self.assertEqual(hp, 1)  # Should return minimum 1


class TestArmorClassCalculation(unittest.TestCase):
    """Test armor class calculation."""

    def test_unarmored_ac(self) -> None:
        """Test AC calculation without armor."""
        # Base AC 10 + 3 DEX modifier = 13
        ac = calculate_armor_class(3)
        self.assertEqual(ac, 13)

    def test_light_armor(self) -> None:
        """Test AC calculation with light armor."""
        light_armor = {"base_ac": 11, "type": "light"}
        # Studded leather (11) + 4 DEX modifier = 15
        ac = calculate_armor_class(4, light_armor)
        self.assertEqual(ac, 15)

    def test_medium_armor(self) -> None:
        """Test AC calculation with medium armor."""
        medium_armor = {"base_ac": 14, "type": "medium", "dex_max_bonus": 2}
        # Scale mail (14) + min(4, 2) DEX modifier = 16
        ac = calculate_armor_class(4, medium_armor)
        self.assertEqual(ac, 16)

    def test_heavy_armor(self) -> None:
        """Test AC calculation with heavy armor."""
        heavy_armor = {"base_ac": 16, "type": "heavy"}
        # Chain mail (16) + 0 DEX modifier = 16
        ac = calculate_armor_class(3, heavy_armor)
        self.assertEqual(ac, 16)

    def test_armor_with_shield(self) -> None:
        """Test AC calculation with shield."""
        light_armor = {"base_ac": 12, "type": "light"}
        # Studded leather (12) + 2 DEX + 2 shield = 16
        ac = calculate_armor_class(2, light_armor, has_shield=True)
        self.assertEqual(ac, 16)

    def test_natural_armor_bonus(self) -> None:
        """Test AC calculation with natural armor bonus."""
        # Base AC 10 + 1 DEX + 2 natural armor = 13
        ac = calculate_armor_class(1, natural_armor_bonus=2)
        self.assertEqual(ac, 13)


class TestSavingThrowModifier(unittest.TestCase):
    """Test saving throw modifier calculation."""

    def test_proficient_save(self) -> None:
        """Test proficient saving throw."""
        # 16 WIS (+3) + proficient at level 5 (+3) = +6
        modifier = calculate_saving_throw_modifier(16, 5, True)
        self.assertEqual(modifier, 6)

    def test_non_proficient_save(self) -> None:
        """Test non-proficient saving throw."""
        # 14 DEX (+2) + not proficient = +2
        modifier = calculate_saving_throw_modifier(14, 3, False)
        self.assertEqual(modifier, 2)

    def test_negative_ability_score(self) -> None:
        """Test saving throw with low ability score."""
        # 8 STR (-1) + proficient at level 1 (+2) = +1
        modifier = calculate_saving_throw_modifier(8, 1, True)
        self.assertEqual(modifier, 1)


class TestSkillModifier(unittest.TestCase):
    """Test skill modifier calculation."""

    def test_proficient_skill(self) -> None:
        """Test proficient skill modifier."""
        ability_scores = {"DEX": 16, "WIS": 14, "INT": 12}
        # Stealth (DEX): +3 ability + +3 proficiency = +6
        modifier = calculate_skill_modifier(
            ability_scores, "stealth", 5, ["stealth", "perception"]
        )
        self.assertEqual(modifier, 6)

    def test_non_proficient_skill(self) -> None:
        """Test non-proficient skill modifier."""
        ability_scores = {"STR": 14, "DEX": 12, "INT": 10}
        # Athletics (STR): +2 ability + 0 proficiency = +2
        modifier = calculate_skill_modifier(
            ability_scores, "athletics", 3, ["perception"]
        )
        self.assertEqual(modifier, 2)

    def test_expertise_skill(self) -> None:
        """Test skill with expertise (double proficiency)."""
        ability_scores = {"WIS": 16, "CHA": 14}
        # Perception (WIS): +3 ability + +6 expertise (2*3) = +9
        modifier = calculate_skill_modifier(
            ability_scores, "perception", 5, ["perception"], ["perception"]
        )
        self.assertEqual(modifier, 9)

    def test_unknown_skill(self) -> None:
        """Test unknown skill returns 0."""
        ability_scores = {"STR": 14}
        modifier = calculate_skill_modifier(ability_scores, "unknown_skill", 1, [])
        self.assertEqual(modifier, 0)

    def test_missing_ability_score(self) -> None:
        """Test skill with missing ability score."""
        ability_scores = {"STR": 14}  # Missing DEX for acrobatics
        modifier = calculate_skill_modifier(
            ability_scores, "acrobatics", 1, ["acrobatics"]
        )
        self.assertEqual(modifier, 0)


class TestSpellSlotCalculation(unittest.TestCase):
    """Test spell slot calculation by character level."""

    def test_full_caster(self) -> None:
        """Test spell slots for full caster."""
        slots = calculate_spell_slots_by_level("wizard", 5)
        self.assertIn(1, slots)
        self.assertIn(2, slots)
        self.assertIn(3, slots)
        self.assertGreaterEqual(slots[1], 2)  # Should have at least 2 first level slots

    def test_half_caster(self) -> None:
        """Test spell slots for half caster."""
        slots = calculate_spell_slots_by_level("paladin", 5)
        self.assertIn(1, slots)  # Should have some spell slots by level 5
        self.assertLess(len(slots), 4)  # Should have fewer slot levels than full caster

    def test_non_caster(self) -> None:
        """Test spell slots for non-caster."""
        slots = calculate_spell_slots_by_level("fighter", 10)
        self.assertEqual(len(slots), 0)  # No spell slots

    def test_low_level_half_caster(self) -> None:
        """Test that half casters don't get slots too early."""
        slots = calculate_spell_slots_by_level("ranger", 1)
        self.assertEqual(len(slots), 0)  # No slots at level 1


class TestTotalModifierForRoll(unittest.TestCase):
    """Test total modifier calculation for various roll types."""

    def test_skill_check_modifier(self) -> None:
        """Test skill check modifier calculation."""
        character_data = CharacterModifierDataModel(
            stats={"DEX": 16, "WIS": 14},
            proficiencies={"skills": ["stealth", "perception"]},
            level=5,
        )
        # Stealth: +3 (DEX) + +3 (proficiency) = +6
        modifier = calculate_total_modifier_for_roll(
            character_data, "skill_check", "stealth"
        )
        self.assertEqual(modifier, 6)

    def test_saving_throw_modifier(self) -> None:
        """Test saving throw modifier calculation."""
        character_data = CharacterModifierDataModel(
            stats={"DEX": 14, "WIS": 16},
            proficiencies={"saving_throws": ["WIS"]},
            level=3,
        )
        # WIS save: +3 (WIS) + +2 (proficiency) = +5
        modifier = calculate_total_modifier_for_roll(
            character_data, "saving_throw", ability="WIS"
        )
        self.assertEqual(modifier, 5)

    def test_initiative_modifier(self) -> None:
        """Test initiative modifier calculation."""
        character_data = CharacterModifierDataModel(
            stats={"DEX": 16}, proficiencies={}, level=1
        )
        # Initiative: +3 (DEX)
        modifier = calculate_total_modifier_for_roll(character_data, "initiative")
        self.assertEqual(modifier, 3)

    def test_ability_check_modifier(self) -> None:
        """Test ability check modifier calculation."""
        character_data = CharacterModifierDataModel(
            stats={"STR": 18}, proficiencies={}, level=1
        )
        # STR check: +4 (STR)
        modifier = calculate_total_modifier_for_roll(
            character_data, "ability_check", ability="STR"
        )
        self.assertEqual(modifier, 4)

    def test_empty_character_data(self) -> None:
        """Test with empty character data."""
        character_data = CharacterModifierDataModel(stats={}, proficiencies={}, level=1)
        modifier = calculate_total_modifier_for_roll(
            character_data, "skill_check", "perception"
        )
        self.assertEqual(modifier, 0)

    def test_invalid_roll_type(self) -> None:
        """Test with invalid roll type."""
        character_data = CharacterModifierDataModel(
            stats={"DEX": 14}, proficiencies={}, level=1
        )
        modifier = calculate_total_modifier_for_roll(
            character_data, "invalid_roll_type"
        )
        self.assertEqual(modifier, 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_hit_points_edge_cases(self) -> None:
        """Test hit point calculation edge cases."""
        # Negative level should return 1
        self.assertEqual(calculate_hit_points(-1, 2, 8), 1)

        # Very high constitution modifier
        hp = calculate_hit_points(1, 10, 6)
        self.assertEqual(hp, 16)  # 6 + 10

    def test_armor_class_edge_cases(self) -> None:
        """Test armor class calculation edge cases."""
        # Very negative DEX modifier
        ac = calculate_armor_class(-5)
        self.assertEqual(ac, 5)  # 10 + (-5)

        # Very high DEX with medium armor
        medium_armor = {"base_ac": 14, "type": "medium", "dex_max_bonus": 2}
        ac = calculate_armor_class(10, medium_armor)  # +5 DEX, capped at +2
        self.assertEqual(ac, 16)  # 14 + 2


if __name__ == "__main__":
    unittest.main()
