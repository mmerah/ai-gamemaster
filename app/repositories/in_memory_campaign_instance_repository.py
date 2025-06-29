"""
In-memory implementation of campaign instance repository for testing.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.core.repository_interfaces import ICampaignInstanceRepository
from app.models.campaign.instance import CampaignInstanceModel
from app.settings import Settings

logger = logging.getLogger(__name__)


class InMemoryCampaignInstanceRepository(ICampaignInstanceRepository):
    """In-memory repository for managing campaign instance metadata."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the in-memory repository.

        Args:
            settings: Application settings
        """
        self._instances: Dict[str, CampaignInstanceModel] = {}
        self.settings = settings
        # Store base_dir for compatibility with CampaignService which expects it
        self.base_dir = Path(settings.storage.campaigns_dir)
        # No file loading - this is a true in-memory repository
        logger.info("Initialized InMemoryCampaignInstanceRepository (no file I/O)")

    def get(self, instance_id: str) -> Optional[CampaignInstanceModel]:
        """Get a specific campaign instance by ID."""
        return self._instances.get(instance_id)

    def delete(self, instance_id: str) -> bool:
        """Delete a campaign instance."""
        if instance_id not in self._instances:
            logger.error(f"Campaign instance {instance_id} not found")
            return False

        del self._instances[instance_id]
        return True

    def save(self, instance: CampaignInstanceModel) -> bool:
        """Save a campaign instance (create or update).

        This method implements the ABC requirement and combines create/update logic.

        Args:
            instance: The campaign instance to save

        Returns:
            True if saved successfully, False otherwise
        """
        is_new = instance.id not in self._instances

        # Update last_played timestamp for existing instances
        if not is_new:
            instance.last_played = datetime.now(timezone.utc)

        # Save the instance
        self._instances[instance.id] = instance

        logger.info(
            f"{'Created' if is_new else 'Updated'} campaign instance {instance.id} in memory"
        )
        return True

    def list(self) -> List[CampaignInstanceModel]:
        """List all campaign instances.

        This method implements the ABC requirement.

        Returns:
            List of all campaign instances
        """
        return list(self._instances.values())
