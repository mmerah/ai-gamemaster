"""
Unit tests for game state repository functionality.
Tests both InMemoryGameStateRepository and FileGameStateRepository implementations.
"""

import os
import shutil
import tempfile
import unittest

from app.core.container import ServiceContainer, reset_container
from app.models.game_state import GameStateModel
from app.models.utils import LocationModel
from app.repositories.game.game_state_repository import FileGameStateRepository
from tests.conftest import get_test_config


class TestGameStateRepository(unittest.TestCase):
    """Test game state repository functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer(get_test_config())
        self.container.initialize()
        self.repo = self.container.get_game_state_repository()

    def test_game_state_initialization(self) -> None:
        """Test that game state initializes with default data."""
        game_state = self.repo.get_game_state()

        # Default minimal state has no party members
        self.assertEqual(len(game_state.party), 0)

        # Check that basic game state elements are initialized
        self.assertIsNotNone(game_state.current_location)
        self.assertIsNotNone(game_state.campaign_goal)

        # Default state starts empty for these collections
        self.assertEqual(len(game_state.known_npcs), 0)
        self.assertEqual(len(game_state.active_quests), 0)
        self.assertEqual(len(game_state.world_lore), 0)

        # Should have welcome message
        self.assertEqual(len(game_state.chat_history), 1)
        self.assertEqual(game_state.chat_history[0].role, "assistant")

    def test_game_state_persistence(self) -> None:
        """Test saving and retrieving game state."""
        original_state = self.repo.get_game_state()

        # Modify the state
        original_state.current_location = LocationModel(
            name="Test Location", description="A test location"
        )
        original_state.event_summary.append("Test event occurred")

        # Save the state
        self.repo.save_game_state(original_state)

        # Retrieve and verify
        retrieved_state = self.repo.get_game_state()
        self.assertEqual(retrieved_state.current_location.name, "Test Location")
        self.assertIn("Test event occurred", retrieved_state.event_summary)


class TestFileGameStateRepository(unittest.TestCase):
    """Test FileGameStateRepository specifically."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = FileGameStateRepository(base_save_dir=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_no_existing_file(self) -> None:
        """Test that repository creates default state when no file exists."""
        state = self.repo.get_game_state()
        self.assertIsNotNone(state)
        self.assertIsInstance(state, GameStateModel)
        # Default minimal state has no party members
        self.assertEqual(len(state.party), 0)
        # But should have basic fields
        self.assertIsNotNone(state.current_location)
        self.assertIsNotNone(state.campaign_goal)
        self.assertEqual(len(state.chat_history), 1)  # Welcome message

    def test_save_creates_file(self) -> None:
        """Test that saving creates a file."""
        state = self.repo.get_game_state()
        state.campaign_id = "test_file_campaign"

        self.repo.save_game_state(state)

        # Check file was created
        expected_path = os.path.join(
            self.temp_dir, "campaigns", "test_file_campaign", "active_game_state.json"
        )
        self.assertTrue(os.path.exists(expected_path))

    def test_load_from_existing_file(self) -> None:
        """Test loading state from an existing file."""
        # Save state with specific campaign
        state = self.repo.get_game_state()
        state.campaign_id = "existing_campaign"
        state.current_location = LocationModel(
            name="Saved Location", description="A saved location"
        )
        self.repo.save_game_state(state)

        # Create new repository instance and load campaign state
        new_repo = FileGameStateRepository(base_save_dir=self.temp_dir)
        loaded_state = new_repo.load_campaign_state("existing_campaign")
        self.assertIsNotNone(loaded_state)
        assert loaded_state is not None  # Type guard for mypy
        self.assertEqual(loaded_state.campaign_id, "existing_campaign")
        self.assertEqual(loaded_state.current_location.name, "Saved Location")

    def test_different_campaigns_different_files(self) -> None:
        """Test that different campaigns use different files."""
        # Save state for campaign 1
        state1 = self.repo.get_game_state()
        state1.campaign_id = "campaign1"
        state1.current_location = LocationModel(
            name="Campaign 1 Location", description="Location for campaign 1"
        )
        self.repo.save_game_state(state1)

        # Save state for campaign 2
        state2 = self.repo.get_game_state()
        state2.campaign_id = "campaign2"
        state2.current_location = LocationModel(
            name="Campaign 2 Location", description="Location for campaign 2"
        )
        self.repo.save_game_state(state2)

        # Verify both files exist
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    self.temp_dir, "campaigns", "campaign1", "active_game_state.json"
                )
            )
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    self.temp_dir, "campaigns", "campaign2", "active_game_state.json"
                )
            )
        )

        # Load campaign 1
        loaded1 = self.repo.load_campaign_state("campaign1")
        self.assertIsNotNone(loaded1)
        assert loaded1 is not None  # Type guard for mypy
        self.assertEqual(loaded1.current_location.name, "Campaign 1 Location")

        # Load campaign 2
        loaded2 = self.repo.load_campaign_state("campaign2")
        self.assertIsNotNone(loaded2)
        assert loaded2 is not None  # Type guard for mypy
        self.assertEqual(loaded2.current_location.name, "Campaign 2 Location")

    def test_corrupted_file_handling(self) -> None:
        """Test handling of corrupted save files."""
        # Create corrupted campaign directory
        campaign_dir = os.path.join(self.temp_dir, "campaigns", "corrupted_campaign")
        os.makedirs(campaign_dir, exist_ok=True)

        # Create a corrupted file
        corrupted_path = os.path.join(campaign_dir, "active_game_state.json")
        with open(corrupted_path, "w") as f:
            f.write("{ invalid json }")

        # Try to load from corrupted file
        state = self.repo.load_campaign_state("corrupted_campaign")

        # Should return None since loading failed
        self.assertIsNone(state)

        # Active state should still be valid (reverted to default)
        active_state = self.repo.get_game_state()
        self.assertIsNotNone(active_state)
        self.assertIsInstance(active_state, GameStateModel)


if __name__ == "__main__":
    unittest.main()
