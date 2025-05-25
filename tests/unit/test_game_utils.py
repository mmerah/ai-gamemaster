"""
Unit tests for game utility functions.
"""
import unittest
from app.game.calculators.dice_mechanics import (
    get_ability_modifier,
    get_proficiency_bonus,
    roll_dice_formula
)


class TestGameUtils(unittest.TestCase):
    """Test game utility functions from the new modular structure."""
    
    def test_ability_modifier(self):
        """Test ability modifier calculation."""
        self.assertEqual(get_ability_modifier(10), 0)
        self.assertEqual(get_ability_modifier(16), 3)
        self.assertEqual(get_ability_modifier(8), -1)
        self.assertEqual(get_ability_modifier(20), 5)
        self.assertEqual(get_ability_modifier(3), -4)
    
    def test_proficiency_bonus(self):
        """Test proficiency bonus calculation."""
        self.assertEqual(get_proficiency_bonus(1), 2)
        self.assertEqual(get_proficiency_bonus(4), 2)
        self.assertEqual(get_proficiency_bonus(5), 3)
        self.assertEqual(get_proficiency_bonus(8), 3)
        self.assertEqual(get_proficiency_bonus(9), 4)
        self.assertEqual(get_proficiency_bonus(20), 6)
    
    def test_dice_formula_parsing(self):
        """Test dice formula rolling functionality."""
        # Test that the roll_dice_formula function works
        # Returns (total_result, individual_rolls, modifier_from_formula, description)
        total, rolls, modifier, description = roll_dice_formula("1d20+5")
        self.assertIsInstance(total, int)
        self.assertIsInstance(rolls, list)
        self.assertIsInstance(modifier, int)
        self.assertIsInstance(description, str)
        self.assertEqual(modifier, 5)
        self.assertEqual(len(rolls), 1)  # Should have one d20 roll
        self.assertTrue(1 <= rolls[0] <= 20)  # d20 should be between 1-20
        
        # Test simple modifier
        total, rolls, modifier, description = roll_dice_formula("1d4+3")
        self.assertEqual(modifier, 3)
        self.assertEqual(len(rolls), 1)  # Should have one d4 roll
        self.assertTrue(1 <= rolls[0] <= 4)  # d4 should be between 1-4


if __name__ == '__main__':
    unittest.main()
