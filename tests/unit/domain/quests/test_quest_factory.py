"""
Unit tests for quest factory module.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.domain.quests.quest_factory import QuestFactory
from app.models.utils import QuestModel


class TestQuestFactory(unittest.TestCase):
    """Test quest factory functionality."""

    def setUp(self) -> None:
        """Set up test data for each test."""
        self.factory = QuestFactory()

    def test_create_quest_basic(self) -> None:
        """Test creating a basic quest."""
        quest = self.factory.create_quest(
            title="Find the Lost Artifact",
            description="An ancient artifact has been stolen from the village temple.",
        )

        self.assertIsInstance(quest, QuestModel)
        self.assertEqual(quest.title, "Find the Lost Artifact")
        self.assertEqual(
            quest.description,
            "An ancient artifact has been stolen from the village temple.",
        )
        self.assertEqual(quest.status, "active")
        self.assertTrue(quest.id.startswith("quest_"))

    def test_create_quest_with_custom_status(self) -> None:
        """Test creating quest with custom status."""
        quest = self.factory.create_quest(
            title="Defeat the Dragon",
            description="A dragon terrorizes the countryside.",
            status="completed",
        )

        self.assertEqual(quest.status, "completed")

    def test_create_quest_with_custom_id(self) -> None:
        """Test creating quest with custom ID."""
        custom_id = "quest_main_001"
        quest = self.factory.create_quest(
            title="Save the Kingdom",
            description="The kingdom is in peril.",
            quest_id=custom_id,
        )

        self.assertEqual(quest.id, custom_id)

    def test_create_quest_invalid_status(self) -> None:
        """Test creating quest with invalid status defaults to active."""
        quest = self.factory.create_quest(
            title="Test Quest",
            description="Test description",
            status="invalid_status",
        )

        self.assertEqual(quest.status, "active")

    def test_create_main_quest(self) -> None:
        """Test creating a main quest."""
        quest = self.factory.create_main_quest(
            title="Destroy the Ring",
            description="Cast the One Ring into Mount Doom.",
        )

        self.assertEqual(quest.title, "[MAIN] Destroy the Ring")
        self.assertEqual(quest.description, "Cast the One Ring into Mount Doom.")
        self.assertEqual(quest.status, "active")

    def test_create_side_quest(self) -> None:
        """Test creating a side quest."""
        quest = self.factory.create_side_quest(
            title="Help the Farmer",
            description="The farmer's crops are being eaten by giant rats.",
        )

        self.assertEqual(quest.title, "[SIDE] Help the Farmer")
        self.assertEqual(
            quest.description, "The farmer's crops are being eaten by giant rats."
        )
        self.assertEqual(quest.status, "active")

    def test_complete_quest(self) -> None:
        """Test marking a quest as completed."""
        quest = self.factory.create_quest(
            title="Test Quest",
            description="Test description",
        )

        # Complete the quest
        completed_quest = self.factory.complete_quest(quest)

        self.assertEqual(completed_quest.status, "completed")
        self.assertIs(completed_quest, quest)  # Should modify in place

    def test_fail_quest(self) -> None:
        """Test marking a quest as failed."""
        quest = self.factory.create_quest(
            title="Protect the Village",
            description="Defend the village from bandits.",
        )

        # Fail the quest
        failed_quest = self.factory.fail_quest(quest)

        self.assertEqual(failed_quest.status, "failed")
        self.assertIs(failed_quest, quest)  # Should modify in place

    @patch("app.domain.quests.quest_factory.datetime")
    @patch("app.domain.quests.quest_factory.uuid4")
    def test_generate_quest_id(
        self, mock_uuid: unittest.mock.Mock, mock_datetime: unittest.mock.Mock
    ) -> None:
        """Test quest ID generation."""
        # Mock datetime to return a fixed time
        mock_now = datetime(2025, 6, 17, 12, 30, 45, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        # Mock uuid to return a predictable value
        mock_uuid.return_value = Mock(
            __str__=Mock(return_value="12345678-abcd-ef12-3456-7890abcdef12")
        )

        # Generate ID
        quest_id = self.factory._generate_quest_id()

        # Verify format
        self.assertEqual(quest_id, "quest_20250617_123045_12345678")

    def test_quest_status_transitions(self) -> None:
        """Test that quest status can transition properly."""
        # Create active quest
        quest = self.factory.create_quest(
            title="Dynamic Quest",
            description="A quest that changes status.",
        )
        self.assertEqual(quest.status, "active")

        # Complete it
        self.factory.complete_quest(quest)
        self.assertEqual(quest.status, "completed")

        # Try to fail a completed quest (should still work)
        self.factory.fail_quest(quest)
        self.assertEqual(quest.status, "failed")

    def test_all_valid_statuses(self) -> None:
        """Test creating quests with all valid statuses."""
        valid_statuses = ["active", "completed", "failed", "inactive"]

        for status in valid_statuses:
            quest = self.factory.create_quest(
                title=f"Quest with {status} status",
                description=f"Testing {status} status",
                status=status,
            )
            self.assertEqual(quest.status, status)

    def test_quest_creation_valid_with_empty_title(self) -> None:
        """Test that quest can be created with empty title (model doesn't validate)."""
        # Note: The QuestModel doesn't have field validation for non-empty strings
        # This test documents the current behavior
        quest = self.factory.create_quest(
            title="",  # Empty title is allowed by the model
            description="Valid description",
        )

        self.assertEqual(quest.title, "")
        self.assertEqual(quest.description, "Valid description")


if __name__ == "__main__":
    unittest.main()
