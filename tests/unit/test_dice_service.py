"""
Unit tests for dice service functionality.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from tests.conftest import get_test_config


class TestDiceService(unittest.TestCase):
    """Test dice service functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_config())
        cls.container.initialize()
        cls.dice_service = cls.container.get_dice_service()
        cls.character_service = cls.container.get_character_service()
        cls.repo = cls.container.get_game_state_repository()
    
    def setUp(self):
        """Reset game state before each test."""
        # Reset to fresh game state
        self.repo._active_game_state = self.repo._initialize_default_game_state()
    
    def test_perform_basic_roll(self):
        """Test performing a basic dice roll."""
        # Get a character ID from the default party
        char_id = self.character_service.find_character_by_name_or_id("Torvin Stonebeard")
        self.assertIsNotNone(char_id)
        
        # Perform a basic roll
        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="custom",
            dice_formula="1d20",
            reason="Test roll"
        )
        
        self.assertIsNotNone(result)
        self.assertIn("result_summary", result)
        self.assertIn("total_result", result)
        self.assertTrue(1 <= result["total_result"] <= 20)
    
    def test_skill_check_roll(self):
        """Test skill check dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id("Torvin Stonebeard")
        
        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="skill_check",
            dice_formula="1d20",
            reason="Wisdom (Perception) check",
            skill="Perception"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["roll_type"], "skill_check")
        self.assertIn("result_summary", result)
        # Total result includes modifiers, so can be higher than 20
        self.assertGreaterEqual(result["total_result"], 1)
    
    def test_saving_throw_roll(self):
        """Test saving throw dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id("Elara Meadowlight")
        
        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="saving_throw",
            dice_formula="1d20",
            reason="Dexterity saving throw",
            ability="DEX"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["roll_type"], "saving_throw")
        self.assertIn("result_summary", result)
        # Total result includes modifiers, so can be higher than 20
        self.assertGreaterEqual(result["total_result"], 1)
    
    def test_attack_roll(self):
        """Test attack roll dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id("Zaltar Mystic")
        
        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="attack_roll",
            dice_formula="1d20",
            reason="Dagger attack"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["roll_type"], "attack_roll")
        # Total result includes modifiers, so can be higher than 20
        self.assertGreaterEqual(result["total_result"], 1)
    
    def test_damage_roll(self):
        """Test damage roll dice rolls."""
        char_id = self.character_service.find_character_by_name_or_id("Torvin Stonebeard")
        
        result = self.dice_service.perform_roll(
            character_id=char_id,
            roll_type="damage_roll",
            dice_formula="1d8+3",
            reason="Warhammer damage"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["roll_type"], "damage_roll")
        # Damage rolls should NOT add character modifiers
        # The formula already includes the +3, so result should be between 4 and 11
        self.assertGreaterEqual(result["total_result"], 4)  # 1 (min roll) + 3
        self.assertLessEqual(result["total_result"], 11)    # 8 (max roll) + 3
        
    def test_damage_roll_no_double_modifier(self):
        """Test that damage rolls don't double-apply modifiers."""
        from unittest.mock import patch
        
        char_id = self.character_service.find_character_by_name_or_id("Elara Meadowlight")
        
        # Mock the dice roll to always return 7
        with patch('app.game.calculators.dice_mechanics.random.randint', return_value=7):
            result = self.dice_service.perform_roll(
                character_id=char_id,
                roll_type="damage_roll", 
                dice_formula="1d8+3",
                reason="Shortbow damage"
            )
            
            # With a roll of 7 and +3 modifier in formula, total should be exactly 10
            # NOT 13 (which would be 7 + 3 + character's DEX modifier)
            self.assertEqual(result["total_result"], 10)
            self.assertEqual(result["character_modifier"], 0)  # No character modifier for damage rolls
    
    def test_advantage_disadvantage_rolls(self):
        """Test that the dice system supports advantage and disadvantage."""
        from unittest.mock import patch
        
        char_id = self.character_service.find_character_by_name_or_id("Elara Meadowlight")
        
        # Test advantage (2d20kh1 - keep highest)
        with patch('app.game.calculators.dice_mechanics.random.randint') as mock_rand:
            # First two calls are for the 2d20, third is for request ID
            mock_rand.side_effect = [5, 15, 1234]
            result = self.dice_service.perform_roll(
                character_id=char_id,
                roll_type="skill_check",
                dice_formula="2d20kh1",  # Advantage: roll 2d20, keep highest
                skill="stealth",
                reason="Stealth check with advantage"
            )
            # Should use the 15, not the 5
            # Plus Elara's stealth modifier (DEX +3 + proficiency)
            self.assertGreater(result["total_result"], 15)
            
        # Test disadvantage (2d20kl1 - keep lowest)
        with patch('app.game.calculators.dice_mechanics.random.randint') as mock_rand:
            # First two calls are for the 2d20, third is for request ID
            mock_rand.side_effect = [5, 15, 1234]
            result = self.dice_service.perform_roll(
                character_id=char_id,
                roll_type="skill_check",
                dice_formula="2d20kl1",  # Disadvantage: roll 2d20, keep lowest
                skill="stealth",
                reason="Stealth check with disadvantage"
            )
            # Should use the 5, not the 15
            # Plus Elara's stealth modifier
            self.assertLess(result["total_result"], 15)
    
    def test_dice_service_edge_cases(self):
        """Test dice service with edge cases."""
        # Test with invalid character ID - should not crash
        try:
            result = self.dice_service.perform_roll(
                character_id="nonexistent",
                roll_type="custom",
                dice_formula="1d20",
                reason="Test roll"
            )
            # Should either return a result or handle gracefully
            self.assertIsNotNone(result)
        except Exception as e:
            # If it throws an exception, it should be a reasonable one
            self.assertIsInstance(e, (ValueError, KeyError))


if __name__ == '__main__':
    unittest.main()
