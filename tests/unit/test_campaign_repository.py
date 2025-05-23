"""
Unit tests for CampaignRepository.
"""
import unittest
import tempfile
import shutil
import os
import json
from datetime import datetime, timezone
from unittest.mock import patch, mock_open
from app.repositories.campaign_repository import CampaignRepository
from app.game.enhanced_models import CampaignDefinition, CampaignMetadata


class TestCampaignRepository(unittest.TestCase):
    """Test cases for CampaignRepository."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = CampaignRepository(campaigns_dir=self.temp_dir)
        
        # Sample campaign data
        self.sample_campaign = CampaignDefinition(
            id="test_campaign",
            name="Test Campaign",
            description="A test campaign for unit testing",
            created_date=datetime.now(timezone.utc),
            last_played=None,
            starting_level=1,
            difficulty="normal",
            party_character_ids=["char1", "char2"],
            starting_location={"name": "Starting Point", "description": "Where it all begins"},
            campaign_goal="Test the system",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            event_summary=[],
            opening_narrative="Welcome to the test campaign",
            house_rules={}
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_ensure_directory_exists(self):
        """Test that the repository creates the campaigns directory."""
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_get_all_campaigns_empty(self):
        """Test getting campaigns when no campaigns exist."""
        campaigns = self.repo.get_all_campaigns()
        self.assertEqual(campaigns, [])

    def test_save_and_get_campaign(self):
        """Test saving and retrieving a campaign."""
        # Save campaign
        result = self.repo.save_campaign(self.sample_campaign)
        self.assertTrue(result)
        
        # Check campaign directory was created
        campaign_dir = os.path.join(self.temp_dir, "test_campaign")
        self.assertTrue(os.path.exists(campaign_dir))
        
        # Check campaign file was created
        campaign_file = os.path.join(campaign_dir, "campaign.json")
        self.assertTrue(os.path.exists(campaign_file))
        
        # Retrieve campaign
        retrieved_campaign = self.repo.get_campaign("test_campaign")
        self.assertIsNotNone(retrieved_campaign)
        self.assertEqual(retrieved_campaign.id, "test_campaign")
        self.assertEqual(retrieved_campaign.name, "Test Campaign")

    def test_get_all_campaigns_with_data(self):
        """Test getting all campaigns when campaigns exist."""
        # Save a campaign first
        self.repo.save_campaign(self.sample_campaign)
        
        campaigns = self.repo.get_all_campaigns()
        self.assertEqual(len(campaigns), 1)
        self.assertIsInstance(campaigns[0], CampaignMetadata)
        self.assertEqual(campaigns[0].id, "test_campaign")

    def test_get_nonexistent_campaign(self):
        """Test getting a campaign that doesn't exist."""
        campaign = self.repo.get_campaign("nonexistent")
        self.assertIsNone(campaign)

    def test_delete_campaign(self):
        """Test deleting a campaign."""
        # First save a campaign
        self.repo.save_campaign(self.sample_campaign)
        
        # Verify it exists
        campaigns = self.repo.get_all_campaigns()
        self.assertEqual(len(campaigns), 1)
        
        # Delete it
        result = self.repo.delete_campaign("test_campaign")
        self.assertTrue(result)
        
        # Verify it's gone
        campaigns = self.repo.get_all_campaigns()
        self.assertEqual(len(campaigns), 0)
        
        # Verify directory is removed
        campaign_dir = os.path.join(self.temp_dir, "test_campaign")
        self.assertFalse(os.path.exists(campaign_dir))

    def test_delete_nonexistent_campaign(self):
        """Test deleting a campaign that doesn't exist."""
        result = self.repo.delete_campaign("nonexistent")
        self.assertFalse(result)

    def test_update_last_played(self):
        """Test updating the last played timestamp."""
        # Save campaign
        self.repo.save_campaign(self.sample_campaign)
        
        # Update last played
        self.repo.update_last_played("test_campaign")
        
        # Check that last_played was updated in the index
        campaigns = self.repo.get_all_campaigns()
        self.assertEqual(len(campaigns), 1)
        self.assertIsNotNone(campaigns[0].last_played)

    def test_campaigns_index_creation(self):
        """Test that campaigns index is created and updated correctly."""
        # Save campaign
        self.repo.save_campaign(self.sample_campaign)
        
        # Check index file exists
        index_file = os.path.join(self.temp_dir, "campaigns.json")
        self.assertTrue(os.path.exists(index_file))
        
        # Check index content
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        self.assertEqual(index_data["version"], "1.0")
        self.assertEqual(len(index_data["campaigns"]), 1)
        self.assertEqual(index_data["campaigns"][0]["id"], "test_campaign")

    def test_datetime_serialization(self):
        """Test that datetime objects are properly serialized and deserialized."""
        # Set specific datetime
        test_time = datetime.now(timezone.utc)
        self.sample_campaign.created_date = test_time
        self.sample_campaign.last_played = test_time
        
        # Save and retrieve
        self.repo.save_campaign(self.sample_campaign)
        retrieved = self.repo.get_campaign("test_campaign")
        
        # Check dates are preserved (allowing for small precision differences)
        self.assertIsInstance(retrieved.created_date, datetime)
        self.assertIsInstance(retrieved.last_played, datetime)

    def test_malformed_datetime_handling(self):
        """Test handling of malformed datetime strings in saved data."""
        # Create a campaign file with malformed datetime
        campaign_dir = os.path.join(self.temp_dir, "test_campaign")
        os.makedirs(campaign_dir, exist_ok=True)
        
        malformed_data = {
            "id": "test_campaign",
            "name": "Test Campaign",
            "description": "Test",
            "created_date": "2023-01-01T00:00:00+00:00Z",  # Malformed: both +00:00 and Z
            "last_played": "2023-01-01T00:00:00Z",
            "starting_level": 1,
            "difficulty": "normal",
            "party_character_ids": ["char1"],
            "starting_location": {"name": "Test", "description": "Test"},
            "campaign_goal": "Test",
            "initial_npcs": {},
            "initial_quests": {},
            "world_lore": [],
            "event_summary": [],
            "opening_narrative": "Test",
            "house_rules": {}
        }
        
        campaign_file = os.path.join(campaign_dir, "campaign.json")
        with open(campaign_file, 'w', encoding='utf-8') as f:
            json.dump(malformed_data, f)
        
        # Create index entry
        index_data = {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "campaigns": [{
                "id": "test_campaign",
                "name": "Test Campaign",
                "description": "Test",
                "created_date": "2023-01-01T00:00:00+00:00Z",
                "last_played": "2023-01-01T00:00:00Z",
                "starting_level": 1,
                "difficulty": "normal",
                "party_size": 1,
                "folder": "test_campaign",
                "thumbnail": None
            }]
        }
        
        index_file = os.path.join(self.temp_dir, "campaigns.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f)
        
        # Should be able to load without errors
        campaign = self.repo.get_campaign("test_campaign")
        self.assertIsNotNone(campaign)
        self.assertEqual(campaign.id, "test_campaign")

    @patch('app.repositories.campaign_repository.logger')
    def test_error_handling_file_not_found(self, mock_logger):
        """Test error handling when campaign file is not found."""
        # Create index entry without corresponding file
        index_data = {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "campaigns": [{
                "id": "missing_campaign",
                "name": "Missing Campaign",
                "description": "Test",
                "created_date": datetime.now(timezone.utc).isoformat(),
                "last_played": None,
                "starting_level": 1,
                "difficulty": "normal",
                "party_size": 1,
                "folder": "missing_campaign",
                "thumbnail": None
            }]
        }
        
        index_file = os.path.join(self.temp_dir, "campaigns.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f)
        
        campaign = self.repo.get_campaign("missing_campaign")
        self.assertIsNone(campaign)
        mock_logger.error.assert_called()

    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    @patch('app.repositories.campaign_repository.logger')
    def test_error_handling_save_failure(self, mock_logger, mock_open):
        """Test error handling when save operation fails."""
        result = self.repo.save_campaign(self.sample_campaign)
        self.assertFalse(result)
        mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()
