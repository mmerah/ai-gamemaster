"""
Unit tests for CampaignInstanceRepository.
"""
import json
import os
import tempfile
import shutil
from datetime import datetime, timezone
import unittest
from unittest.mock import patch, mock_open, MagicMock

from app.repositories.campaign_instance_repository import CampaignInstanceRepository
from app.game.unified_models import CampaignInstanceModel


class TestCampaignInstanceRepository(unittest.TestCase):
    """Test cases for CampaignInstanceRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.repo = CampaignInstanceRepository(self.test_dir)
        
        # Sample campaign instance
        self.sample_instance = CampaignInstanceModel(
            id="test_instance_1",
            name="Test Adventure",
            template_id="test_template",
            character_ids=["char1", "char2"],
            current_location="Starting Town",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path=os.path.join(self.test_dir, "test_instance_1", "event_log.json"),
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc)
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_ensure_directory_exists(self):
        """Test that the repository creates its directory."""
        # Remove the directory
        shutil.rmtree(self.test_dir)
        
        # Create a new repository - should create the directory
        repo = CampaignInstanceRepository(self.test_dir)
        
        self.assertTrue(os.path.exists(self.test_dir))
    
    def test_create_instance_success(self):
        """Test successfully creating a campaign instance."""
        result = self.repo.create_instance(self.sample_instance)
        
        self.assertTrue(result)
        
        # Verify the instance was saved
        instances = self.repo.get_all_instances()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].id, self.sample_instance.id)
    
    def test_create_instance_duplicate_id(self):
        """Test creating an instance with duplicate ID fails."""
        # Create the first instance
        self.repo.create_instance(self.sample_instance)
        
        # Try to create another with the same ID
        result = self.repo.create_instance(self.sample_instance)
        
        self.assertFalse(result)
    
    def test_get_instance_exists(self):
        """Test getting an existing instance."""
        self.repo.create_instance(self.sample_instance)
        
        instance = self.repo.get_instance(self.sample_instance.id)
        
        self.assertIsNotNone(instance)
        self.assertEqual(instance.id, self.sample_instance.id)
        self.assertEqual(instance.name, self.sample_instance.name)
    
    def test_get_instance_not_found(self):
        """Test getting a non-existent instance."""
        instance = self.repo.get_instance("nonexistent")
        
        self.assertIsNone(instance)
    
    def test_update_instance_success(self):
        """Test updating an existing instance."""
        self.repo.create_instance(self.sample_instance)
        
        # Update the instance
        self.sample_instance.session_count = 5
        self.sample_instance.in_combat = True
        
        result = self.repo.update_instance(self.sample_instance)
        
        self.assertTrue(result)
        
        # Verify the update
        updated = self.repo.get_instance(self.sample_instance.id)
        self.assertEqual(updated.session_count, 5)
        self.assertTrue(updated.in_combat)
        # last_played should be updated automatically
        self.assertGreater(updated.last_played, self.sample_instance.created_date)
    
    def test_update_instance_not_found(self):
        """Test updating a non-existent instance."""
        result = self.repo.update_instance(self.sample_instance)
        
        self.assertFalse(result)
    
    def test_delete_instance_success(self):
        """Test deleting an existing instance."""
        self.repo.create_instance(self.sample_instance)
        
        # Create a fake campaign directory
        campaign_dir = os.path.join(self.test_dir, self.sample_instance.id)
        os.makedirs(campaign_dir, exist_ok=True)
        with open(os.path.join(campaign_dir, "test.txt"), "w") as f:
            f.write("test")
        
        result = self.repo.delete_instance(self.sample_instance.id)
        
        self.assertTrue(result)
        
        # Verify deletion
        self.assertIsNone(self.repo.get_instance(self.sample_instance.id))
        self.assertFalse(os.path.exists(campaign_dir))
    
    def test_delete_instance_not_found(self):
        """Test deleting a non-existent instance."""
        result = self.repo.delete_instance("nonexistent")
        
        self.assertFalse(result)
    
    def test_get_instances_by_template(self):
        """Test getting instances by template ID."""
        # Create multiple instances
        instance1 = self.sample_instance
        instance2 = CampaignInstanceModel(
            id="test_instance_2",
            name="Another Adventure",
            template_id="test_template",
            character_ids=["char3"],
            current_location="Different Town",
            session_count=2,
            in_combat=False,
            event_summary=[],
            event_log_path=os.path.join(self.test_dir, "test_instance_2", "event_log.json"),
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc)
        )
        instance3 = CampaignInstanceModel(
            id="test_instance_3",
            name="Different Template Adventure",
            template_id="other_template",
            character_ids=["char4"],
            current_location="Other Place",
            session_count=1,
            in_combat=False,
            event_summary=[],
            event_log_path=os.path.join(self.test_dir, "test_instance_3", "event_log.json"),
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc)
        )
        
        self.repo.create_instance(instance1)
        self.repo.create_instance(instance2)
        self.repo.create_instance(instance3)
        
        # Get instances for test_template
        instances = self.repo.get_instances_by_template("test_template")
        
        self.assertEqual(len(instances), 2)
        instance_ids = [i.id for i in instances]
        self.assertIn("test_instance_1", instance_ids)
        self.assertIn("test_instance_2", instance_ids)
        self.assertNotIn("test_instance_3", instance_ids)
    
    def test_get_active_instances(self):
        """Test getting recently active instances."""
        from datetime import timedelta
        
        # Create instances with different last_played dates
        old_date = datetime.now(timezone.utc) - timedelta(days=40)
        recent_date = datetime.now(timezone.utc) - timedelta(days=10)
        
        old_instance = CampaignInstanceModel(
            id="old_instance",
            name="Old Adventure",
            template_id="test_template",
            character_ids=["char1"],
            current_location="Old Town",
            session_count=10,
            in_combat=False,
            event_summary=[],
            event_log_path=os.path.join(self.test_dir, "old_instance", "event_log.json"),
            created_date=old_date,
            last_played=old_date
        )
        
        recent_instance = CampaignInstanceModel(
            id="recent_instance",
            name="Recent Adventure",
            template_id="test_template",
            character_ids=["char2"],
            current_location="New Town",
            session_count=3,
            in_combat=False,
            event_summary=[],
            event_log_path=os.path.join(self.test_dir, "recent_instance", "event_log.json"),
            created_date=recent_date,
            last_played=recent_date
        )
        
        self.repo.create_instance(old_instance)
        self.repo.create_instance(recent_instance)
        
        # Get active instances (within 30 days)
        active = self.repo.get_active_instances(days=30)
        
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, "recent_instance")
    
    def test_error_handling_corrupted_file(self):
        """Test handling of corrupted instances file."""
        # Create a corrupted instances file
        with open(self.repo.instances_file, 'w') as f:
            f.write("invalid json{")
        
        # Should return empty list
        instances = self.repo.get_all_instances()
        self.assertEqual(instances, [])
    
    def test_error_handling_invalid_instance_data(self):
        """Test handling of invalid instance data in file."""
        # Create instances file with invalid data
        data = {
            "valid_instance": self.sample_instance.model_dump(mode='json'),
            "invalid_instance": {
                # Missing required fields
                "name": "Invalid"
            }
        }
        
        with open(self.repo.instances_file, 'w') as f:
            json.dump(data, f)
        
        # Should only load valid instances
        instances = self.repo.get_all_instances()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].id, "test_instance_1")


if __name__ == '__main__':
    unittest.main()