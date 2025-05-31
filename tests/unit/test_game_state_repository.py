"""
Unit tests for game state repository functionality.
Tests both InMemoryGameStateRepository and FileGameStateRepository implementations.
"""
import unittest
import tempfile
import shutil
import os
from app.core.container import ServiceContainer, reset_container
from app.repositories.game_state_repository import InMemoryGameStateRepository, FileGameStateRepository
from app.game.models import GameState
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


class TestInMemoryGameStateRepository(unittest.TestCase):
    """Test InMemoryGameStateRepository specifically."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repo = InMemoryGameStateRepository()
    
    def test_initialization(self):
        """Test that repository initializes with default state."""
        state = self.repo.get_game_state()
        self.assertIsNotNone(state)
        self.assertIsInstance(state, GameState)
        # Should have initialized party
        self.assertGreater(len(state.party), 0)
    
    def test_save_and_retrieve(self):
        """Test in-memory save and retrieve."""
        # Get initial state
        state = self.repo.get_game_state()
        original_location = state.current_location.copy()
        
        # Modify state
        state.current_location["name"] = "Modified Location"
        state.event_summary.append("In-memory test event")
        
        # Save
        self.repo.save_game_state(state)
        
        # Retrieve
        retrieved = self.repo.get_game_state()
        self.assertEqual(retrieved.current_location["name"], "Modified Location")
        self.assertIn("In-memory test event", retrieved.event_summary)
        
        # Verify it's the same object (in-memory)
        self.assertIs(retrieved, state)
    
    def test_state_persistence_across_instances(self):
        """Test that state persists in memory."""
        # Modify state
        state = self.repo.get_game_state()
        state.campaign_id = "test_campaign_memory"
        
        # Should still have the same state
        retrieved = self.repo.get_game_state()
        self.assertEqual(retrieved.campaign_id, "test_campaign_memory")


class TestFileGameStateRepository(unittest.TestCase):
    """Test FileGameStateRepository specifically."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = FileGameStateRepository(base_save_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization_with_no_existing_file(self):
        """Test that repository creates default state when no file exists."""
        state = self.repo.get_game_state()
        self.assertIsNotNone(state)
        self.assertIsInstance(state, GameState)
        # Should have initialized party
        self.assertGreater(len(state.party), 0)
    
    def test_save_creates_file(self):
        """Test that saving creates a file."""
        state = self.repo.get_game_state()
        state.campaign_id = "test_file_campaign"
        
        self.repo.save_game_state(state)
        
        # Check file was created
        expected_path = os.path.join(self.temp_dir, "campaigns", "test_file_campaign", "active_game_state.json")
        self.assertTrue(os.path.exists(expected_path))
    
    def test_load_from_existing_file(self):
        """Test loading state from an existing file."""
        # Save state with specific campaign
        state = self.repo.get_game_state()
        state.campaign_id = "existing_campaign"
        state.current_location["name"] = "Saved Location"
        self.repo.save_game_state(state)
        
        # Create new repository instance and load campaign state
        new_repo = FileGameStateRepository(base_save_dir=self.temp_dir)
        loaded_state = new_repo.load_campaign_state("existing_campaign")
        self.assertEqual(loaded_state.campaign_id, "existing_campaign")
        self.assertEqual(loaded_state.current_location["name"], "Saved Location")
    
    def test_different_campaigns_different_files(self):
        """Test that different campaigns use different files."""
        # Save state for campaign 1
        state1 = self.repo.get_game_state()
        state1.campaign_id = "campaign1"
        state1.current_location["name"] = "Campaign 1 Location"
        self.repo.save_game_state(state1)
        
        # Save state for campaign 2
        state2 = self.repo.get_game_state()
        state2.campaign_id = "campaign2"
        state2.current_location["name"] = "Campaign 2 Location"
        self.repo.save_game_state(state2)
        
        # Verify both files exist
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "campaigns", "campaign1", "active_game_state.json")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "campaigns", "campaign2", "active_game_state.json")))
        
        # Load campaign 1
        loaded1 = self.repo.load_campaign_state("campaign1")
        self.assertEqual(loaded1.current_location["name"], "Campaign 1 Location")
        
        # Load campaign 2
        loaded2 = self.repo.load_campaign_state("campaign2")
        self.assertEqual(loaded2.current_location["name"], "Campaign 2 Location")
    
    def test_corrupted_file_handling(self):
        """Test handling of corrupted save files."""
        # Create corrupted campaign directory
        campaign_dir = os.path.join(self.temp_dir, "campaigns", "corrupted_campaign")
        os.makedirs(campaign_dir, exist_ok=True)
        
        # Create a corrupted file
        corrupted_path = os.path.join(campaign_dir, "active_game_state.json")
        with open(corrupted_path, 'w') as f:
            f.write("{ invalid json }")
        
        # Try to load from corrupted file
        state = self.repo.load_campaign_state("corrupted_campaign")
        
        # Should return None since loading failed
        self.assertIsNone(state)
        
        # Active state should still be valid (reverted to default)
        active_state = self.repo.get_game_state()
        self.assertIsNotNone(active_state)
        self.assertIsInstance(active_state, GameState)


if __name__ == '__main__':
    unittest.main()
