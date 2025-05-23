"""
Unit tests for game utility functions.
"""
import unittest
from app.game import utils


class TestGameUtils(unittest.TestCase):
    """Test game utility functions."""
    
    def test_ability_modifier(self):
        """Test ability modifier calculation."""
        self.assertEqual(utils.get_ability_modifier(10), 0)
        self.assertEqual(utils.get_ability_modifier(16), 3)
        self.assertEqual(utils.get_ability_modifier(8), -1)
        self.assertEqual(utils.get_ability_modifier(20), 5)
        self.assertEqual(utils.get_ability_modifier(3), -4)
    
    def test_proficiency_bonus(self):
        """Test proficiency bonus calculation."""
        self.assertEqual(utils.get_proficiency_bonus(1), 2)
        self.assertEqual(utils.get_proficiency_bonus(4), 2)
        self.assertEqual(utils.get_proficiency_bonus(5), 3)
        self.assertEqual(utils.get_proficiency_bonus(8), 3)
        self.assertEqual(utils.get_proficiency_bonus(9), 4)
        self.assertEqual(utils.get_proficiency_bonus(20), 6)
    
    def test_dice_parsing(self):
        """Test dice notation parsing."""
        # Test basic parsing if function exists
        if hasattr(utils, 'parse_dice'):
            result = utils.parse_dice("2d6+3")
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
