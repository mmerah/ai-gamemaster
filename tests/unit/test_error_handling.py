"""
Unit tests for error handling and edge cases.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from tests.conftest import get_test_config


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_config())
        cls.container.initialize()
    
    def setUp(self):
        """Reset game state before each test."""
        # Reset to fresh game state
        repo = self.container.get_game_state_repository()
        repo._active_game_state = repo._initialize_default_game_state()
    
    def test_invalid_character_operations(self):
        """Test operations with invalid character IDs."""
        character_service = self.container.get_character_service()
        
        # Test with None
        result = character_service.find_character_by_name_or_id(None)
        self.assertIsNone(result)
        
        # Test with empty string
        result = character_service.find_character_by_name_or_id("")
        self.assertIsNone(result)
        
        # Test getting non-existent character
        char = character_service.get_character("nonexistent")
        self.assertIsNone(char)
    
    def test_dice_service_error_handling(self):
        """Test dice service error handling."""
        dice_service = self.container.get_dice_service()
        
        # Test with invalid character ID - should not crash
        try:
            result = dice_service.perform_roll(
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
    
    def test_combat_service_error_handling(self):
        """Test combat service error handling."""
        combat_service = self.container.get_combat_service()
        
        # Test ending combat when none is active
        try:
            combat_service.end_combat()
            # Should handle gracefully
        except Exception as e:
            # Should not throw unexpected exceptions
            self.fail(f"Unexpected exception: {e}")
    
    def test_character_validator_edge_cases(self):
        """Test character validator with edge cases."""
        from app.services.character_service import CharacterValidator
        repo = self.container.get_game_state_repository()
        
        # Test with non-existent character
        result = CharacterValidator.is_character_defeated("nonexistent", repo)
        # Should return False or handle gracefully
        self.assertFalse(result)
        
        result = CharacterValidator.is_character_incapacitated("nonexistent", repo)
        # Should return False or handle gracefully
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
