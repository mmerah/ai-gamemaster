"""
Factory for creating quest-related objects.

This module provides the QuestFactory class for creating quests.

NOTE: This factory is currently not integrated into the application flow.
Quests are currently created directly by the AI response processing system.
This factory is maintained for future use when quest creation is refactored
to be more structured and separated from AI response handling.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models.utils import QuestModel

logger = logging.getLogger(__name__)


class QuestFactory:
    """Factory for creating quests."""

    def __init__(self) -> None:
        """Initialize the quest factory."""
        pass

    def create_quest(
        self,
        title: str,
        description: str,
        status: str = "active",
        quest_id: Optional[str] = None,
    ) -> QuestModel:
        """
        Create a new quest.

        Args:
            title: The quest title
            description: The quest description
            status: The quest status (active, completed, failed, inactive)
            quest_id: Optional quest ID, will generate if not provided

        Returns:
            QuestModel: The newly created quest
        """
        try:
            # Generate ID if not provided
            if quest_id is None:
                quest_id = self._generate_quest_id()

            # Validate status
            valid_statuses = ["active", "completed", "failed", "inactive"]
            if status not in valid_statuses:
                logger.warning(
                    f"Invalid quest status '{status}', defaulting to 'active'"
                )
                status = "active"

            return QuestModel(
                id=quest_id,
                title=title,
                description=description,
                status=status,
            )

        except Exception as e:
            logger.error(f"Error creating quest '{title}': {e}", exc_info=True)
            raise

    def create_main_quest(
        self, title: str, description: str, quest_id: Optional[str] = None
    ) -> QuestModel:
        """
        Create a main quest (always active).

        Args:
            title: The quest title
            description: The quest description
            quest_id: Optional quest ID

        Returns:
            QuestModel: The newly created main quest
        """
        return self.create_quest(
            title=f"[MAIN] {title}",
            description=description,
            status="active",
            quest_id=quest_id,
        )

    def create_side_quest(
        self, title: str, description: str, quest_id: Optional[str] = None
    ) -> QuestModel:
        """
        Create a side quest.

        Args:
            title: The quest title
            description: The quest description
            quest_id: Optional quest ID

        Returns:
            QuestModel: The newly created side quest
        """
        return self.create_quest(
            title=f"[SIDE] {title}",
            description=description,
            status="active",
            quest_id=quest_id,
        )

    def complete_quest(self, quest: QuestModel) -> QuestModel:
        """
        Mark a quest as completed.

        Args:
            quest: The quest to complete

        Returns:
            QuestModel: The updated quest
        """
        quest.status = "completed"
        logger.info(f"Quest '{quest.title}' marked as completed")
        return quest

    def fail_quest(self, quest: QuestModel) -> QuestModel:
        """
        Mark a quest as failed.

        Args:
            quest: The quest to fail

        Returns:
            QuestModel: The updated quest
        """
        quest.status = "failed"
        logger.info(f"Quest '{quest.title}' marked as failed")
        return quest

    def _generate_quest_id(self) -> str:
        """
        Generate a unique quest ID.

        Returns:
            str: A unique quest ID
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid4())[:8]
        return f"quest_{timestamp}_{unique_id}"
