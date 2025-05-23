"""
Unit tests for dice service functionality.
"""
import unittest
from app.core.container import ServiceContainer, reset_container


class TestDiceService(unittest.TestCase):
    """Test dice service functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        self.dice_service = self.container.get_dice_service()
        self.character_service = self.container.get_character_service()
    
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
        # Damage rolls might include character modifiers beyond the formula
        self.assertGreaterEqual(result["total_result"], 1)
    
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
