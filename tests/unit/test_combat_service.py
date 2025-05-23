"""
Unit tests for combat service functionality.
"""
import unittest
from app.core.container import ServiceContainer, reset_container


class TestCombatService(unittest.TestCase):
    """Test combat service functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({'GAME_STATE_REPO_TYPE': 'memory'})
        self.container.initialize()
        self.combat_service = self.container.get_combat_service()
        self.repo = self.container.get_game_state_repository()
    
    def test_start_combat(self):
        """Test starting combat."""
        monsters = [
            {"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}},
            {"id": "goblin2", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 12}}
        ]
        
        self.combat_service.start_combat(monsters)
        
        game_state = self.repo.get_game_state()
        self.assertTrue(game_state.combat.is_active)
        self.assertEqual(len(game_state.combat.monster_stats), 2)
        self.assertIn("goblin1", game_state.combat.monster_stats)
        self.assertIn("goblin2", game_state.combat.monster_stats)
    
    def test_end_combat(self):
        """Test ending combat."""
        # Start combat first
        monsters = [{"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}}]
        self.combat_service.start_combat(monsters)
        
        # End combat
        self.combat_service.end_combat()
        
        game_state = self.repo.get_game_state()
        self.assertFalse(game_state.combat.is_active)
        self.assertEqual(len(game_state.combat.monster_stats), 0)
        self.assertEqual(len(game_state.combat.combatants), 0)
    
    def test_advance_turn(self):
        """Test advancing turns in combat."""
        # Start combat first
        monsters = [{"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}}]
        self.combat_service.start_combat(monsters)
        
        # Test that we can advance turn
        self.combat_service.advance_turn()
        
        # Combat should still be active
        game_state = self.repo.get_game_state()
        self.assertTrue(game_state.combat.is_active)
    
    def test_determine_initiative_order(self):
        """Test determining initiative order."""
        # Start combat first
        monsters = [{"id": "goblin1", "name": "Goblin", "hp": 7, "ac": 15, "stats": {"DEX": 14}}]
        self.combat_service.start_combat(monsters)
        
        # Mock roll results
        roll_results = [
            {"character_id": "char1", "roll_type": "initiative", "total_result": 15},
            {"character_id": "goblin1", "roll_type": "initiative", "total_result": 10}
        ]
        
        self.combat_service.determine_initiative_order(roll_results)
        
        game_state = self.repo.get_game_state()
        # Should have initiative values set
        self.assertGreater(len(game_state.combat.combatants), 0)


if __name__ == '__main__':
    unittest.main()
