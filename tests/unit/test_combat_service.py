"""
Unit tests for combat service functionality.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from tests.conftest import get_test_config


class TestCombatService(unittest.TestCase):
    """Test combat service functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_config())
        cls.container.initialize()
        cls.combat_service = cls.container.get_combat_service()
        cls.character_service = cls.container.get_character_service()
        cls.repo = cls.container.get_game_state_repository()
    
    def setUp(self):
        """Reset game state before each test."""
        # Reset to fresh game state
        self.repo._active_game_state = self.repo._initialize_default_game_state()
    
    def test_start_combat(self):
        """Test starting combat."""
        # Create test monsters
        monsters = [
            {"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}},
            {"id": "orc1", "name": "Orc", "hp": 15, "ac": 13, "stats": {"DEX": 12}}
        ]
        
        # Start combat
        self.combat_service.start_combat(monsters)
        
        # Verify combat state
        game_state = self.repo.get_game_state()
        self.assertTrue(game_state.combat.is_active)
        self.assertEqual(len(game_state.combat.combatants), 2)  # Only the 2 monsters passed
        self.assertGreater(len(game_state.combat.combatants), 0)
    
    def test_end_combat(self):
        """Test ending combat."""
        # Start combat first
        monsters = [{"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}}]
        self.combat_service.start_combat(monsters)
        
        # End combat
        self.combat_service.end_combat()
        
        # Verify combat ended
        game_state = self.repo.get_game_state()
        self.assertFalse(game_state.combat.is_active)
        self.assertEqual(len(game_state.combat.combatants), 0)
    
    def test_determine_initiative_order(self):
        """Test determining initiative order."""
        # Start combat with monsters
        monsters = [
            {"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}},
            {"id": "orc1", "name": "Orc", "hp": 15, "ac": 13, "stats": {"DEX": 12}}
        ]
        
        self.combat_service.start_combat(monsters)
        
        # Check that initiative order was determined
        game_state = self.repo.get_game_state()
        combatants = game_state.combat.combatants
        
        # Should have the monsters we added
        self.assertEqual(len(combatants), 2)
        
        # Verify all entities have initiative values
        for combatant in combatants:
            self.assertIsInstance(combatant.initiative, int)
    
    def test_advance_turn(self):
        """Test advancing turns in combat."""
        # Start combat
        monsters = [{"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}}]
        self.combat_service.start_combat(monsters)
        
        # Get initial turn index
        game_state = self.repo.get_game_state()
        initial_turn = game_state.combat.current_turn_index
        
        # Advance turn
        self.combat_service.advance_turn()
        
        # Verify turn advanced
        updated_state = self.repo.get_game_state()
        new_turn = updated_state.combat.current_turn_index
        
        # Turn should have advanced (or wrapped around)
        expected_turn = (initial_turn + 1) % len(updated_state.combat.combatants)
        self.assertEqual(new_turn, expected_turn)


if __name__ == '__main__':
    unittest.main()
