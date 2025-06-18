"""
Unit tests for CampaignInstanceRepository.
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone

from app.models.campaign import CampaignInstanceModel
from app.repositories.campaign_instance_repository import (
    CampaignInstanceRepository,
)


class TestCampaignInstanceRepository(unittest.TestCase):
    """Test cases for CampaignInstanceRepository."""

    def setUp(self) -> None:
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
            event_log_path=os.path.join(
                self.test_dir, "test_instance_1", "event_log.json"
            ),
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
        )

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_ensure_directory_exists(self) -> None:
        """Test that the repository creates its directory."""
        # Remove the directory
        shutil.rmtree(self.test_dir)

        # Create a new repository - should create the directory
        CampaignInstanceRepository(self.test_dir)

        self.assertTrue(os.path.exists(self.test_dir))

    def test_create_instance_success(self) -> None:
        """Test successfully creating a campaign instance."""
        result = self.repo.save(self.sample_instance)

        self.assertTrue(result)

        # Verify the instance was saved
        instances = self.repo.list()
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].id, self.sample_instance.id)

    def test_create_instance_duplicate_id(self) -> None:
        """Test creating an instance with duplicate ID succeeds (save is upsert)."""
        # Create the first instance
        self.repo.save(self.sample_instance)

        # Try to save again with the same ID (should update, not fail)
        result = self.repo.save(self.sample_instance)

        self.assertTrue(result)  # save should succeed as it's an upsert

    def test_get_instance_exists(self) -> None:
        """Test getting an existing instance."""
        self.repo.save(self.sample_instance)

        instance = self.repo.get(self.sample_instance.id)

        self.assertIsNotNone(instance)
        assert instance is not None  # Type guard
        self.assertEqual(instance.id, self.sample_instance.id)
        self.assertEqual(instance.name, self.sample_instance.name)

    def test_get_instance_not_found(self) -> None:
        """Test getting a non-existent instance."""
        instance = self.repo.get("nonexistent")

        self.assertIsNone(instance)

    def test_update_instance_success(self) -> None:
        """Test updating an existing instance."""
        self.repo.save(self.sample_instance)

        # Update the instance
        self.sample_instance.session_count = 5
        self.sample_instance.in_combat = True

        result = self.repo.save(self.sample_instance)

        self.assertTrue(result)

        # Verify the update
        updated = self.repo.get(self.sample_instance.id)
        self.assertIsNotNone(updated)
        assert updated is not None  # Type guard
        self.assertEqual(updated.session_count, 5)
        self.assertTrue(updated.in_combat)
        # last_played should be updated automatically
        self.assertGreater(updated.last_played, self.sample_instance.created_date)

    def test_save_creates_new_instance(self) -> None:
        """Test save creates a new instance if it doesn't exist."""
        result = self.repo.save(self.sample_instance)

        self.assertTrue(result)  # save should create if not exists

    def test_delete_instance_success(self) -> None:
        """Test deleting an existing instance."""
        self.repo.save(self.sample_instance)

        # Create a fake campaign directory
        campaign_dir = os.path.join(self.test_dir, self.sample_instance.id)
        os.makedirs(campaign_dir, exist_ok=True)
        with open(os.path.join(campaign_dir, "test.txt"), "w") as f:
            f.write("test")

        result = self.repo.delete(self.sample_instance.id)

        self.assertTrue(result)

        # Verify deletion
        self.assertIsNone(self.repo.get(self.sample_instance.id))
        self.assertFalse(os.path.exists(campaign_dir))

    def test_delete_instance_not_found(self) -> None:
        """Test deleting a non-existent instance."""
        result = self.repo.delete("nonexistent")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
