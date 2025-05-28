"""
Unit tests for repository functionality.
"""
import unittest
from app.core.container import ServiceContainer, reset_container
from tests.conftest import get_test_config


class TestGameStateRepository(unittest.TestCase):
    """Test game state repository functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer(get_test_config())
        self.container.initialize()
        self.repo = self.container.get_game_state_repository()
    
    def test_game_state_initialization(self):
        """Test that game state initializes with default data."""
        game_state = self.repo.get_game_state()
        
        # Check that party is loaded
        self.assertGreater(len(game_state.party), 0)
        self.assertIn("char1", game_state.party)
        
        # Check character data
        char1 = game_state.party["char1"]
        self.assertEqual(char1.name, "Torvin Stonebeard")
        self.assertEqual(char1.race, "Dwarf")
        self.assertEqual(char1.char_class, "Cleric")
        self.assertEqual(char1.level, 3)
        
        # Check that other game state elements are initialized
        self.assertIsNotNone(game_state.current_location)
        self.assertIsNotNone(game_state.campaign_goal)
        self.assertGreater(len(game_state.known_npcs), 0)
        self.assertGreater(len(game_state.active_quests), 0)
        self.assertGreater(len(game_state.world_lore), 0)
    
    def test_game_state_persistence(self):
        """Test saving and retrieving game state."""
        original_state = self.repo.get_game_state()
        
        # Modify the state
        original_state.current_location["name"] = "Test Location"
        original_state.event_summary.append("Test event occurred")
        
        # Save the state
        self.repo.save_game_state(original_state)
        
        # Retrieve and verify
        retrieved_state = self.repo.get_game_state()
        self.assertEqual(retrieved_state.current_location["name"], "Test Location")
        self.assertIn("Test event occurred", retrieved_state.event_summary)


if __name__ == '__main__':
    unittest.main()
