"""
Unit tests for character service functionality.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from app.services.character_service import CharacterValidator, CharacterStatsCalculator
from app.game.models import CharacterSheet, CharacterInstance, AbilityScores, Proficiencies


class TestCharacterService(unittest.TestCase):
    """Test character service functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        self.character_service = self.container.get_character_service()
        self.repo = self.container.get_game_state_repository()
    
    def test_get_character(self):
        """Test getting character by ID."""
        char = self.character_service.get_character("char1")
        self.assertIsNotNone(char)
        self.assertEqual(char.name, "Torvin Stonebeard")
        
        # Test non-existent character
        char = self.character_service.get_character("nonexistent")
        self.assertIsNone(char)
    
    def test_get_character_name(self):
        """Test getting character display names."""
        name = self.character_service.get_character_name("char1")
        self.assertEqual(name, "Torvin Stonebeard")
        
        # Test fallback to ID for unknown character
        name = self.character_service.get_character_name("unknown")
        self.assertEqual(name, "unknown")
    
    def test_find_character_by_name_or_id(self):
        """Test finding characters by name or ID."""
        # Test all party members can be found by name
        result = self.character_service.find_character_by_name_or_id("Elara Meadowlight")
        self.assertEqual(result, "char2")
        
        result = self.character_service.find_character_by_name_or_id("Zaltar Mystic")
        self.assertEqual(result, "char3")
        
        # Test case insensitive search
        result = self.character_service.find_character_by_name_or_id("torvin stonebeard")
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


class TestCharacterValidator(unittest.TestCase):
    """Test character validation utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        self.repo = self.container.get_game_state_repository()
    
    def test_character_defeated_check(self):
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
    
    def test_character_incapacitated_check(self):
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


class TestCharacterStatsCalculator(unittest.TestCase):
    """Test character statistics calculation utilities."""
    
    def test_ability_modifier_calculation(self):
        """Test ability modifier calculations."""
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(10), 0)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(8), -1)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(16), 3)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(20), 5)
        self.assertEqual(CharacterStatsCalculator.calculate_ability_modifier(3), -4)
    
    def test_proficiency_bonus_calculation(self):
        """Test proficiency bonus calculations."""
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(1), 2)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(4), 2)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(5), 3)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(8), 3)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(9), 4)
        self.assertEqual(CharacterStatsCalculator.calculate_proficiency_bonus(20), 6)
    
    def test_max_hp_calculation(self):
        """Test maximum HP calculations."""
        # Create a test character
        char_sheet = CharacterSheet(
            id="test", name="Test", race="Human", char_class="Fighter", level=3,
            base_stats=AbilityScores(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8),
            proficiencies=Proficiencies()
        )
        char = CharacterInstance(**char_sheet.model_dump(),
                                current_hp=1, max_hp=1, armor_class=10,
                                temporary_hp=0, conditions=[], inventory=[], gold=0)
        
        max_hp = CharacterStatsCalculator.calculate_max_hp(char)
        # CON 15 = +2 modifier, level 3, hit die avg 5
        # (5 + 2) * 3 = 21
        self.assertEqual(max_hp, 21)
    
    def test_armor_class_calculation(self):
        """Test armor class calculations."""
        char_sheet = CharacterSheet(
            id="test", name="Test", race="Human", char_class="Rogue", level=1,
            base_stats=AbilityScores(STR=10, DEX=16, CON=12, INT=14, WIS=10, CHA=12),
            proficiencies=Proficiencies()
        )
        char = CharacterInstance(**char_sheet.model_dump(),
                                current_hp=1, max_hp=1, armor_class=10,
                                temporary_hp=0, conditions=[], inventory=[], gold=0)
        
        ac = CharacterStatsCalculator.calculate_armor_class(char)
        # Base 10 + DEX modifier (+3) = 13
        self.assertEqual(ac, 13)


if __name__ == '__main__':
    unittest.main()
