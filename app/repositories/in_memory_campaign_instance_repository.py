"""
In-memory implementation of campaign instance repository for testing.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.models.models import CampaignInstanceModel

logger = logging.getLogger(__name__)


class InMemoryCampaignInstanceRepository:
    """In-memory repository for managing campaign instance metadata."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        """
        Initialize the in-memory repository.

        Args:
            base_dir: The base directory path. This parameter is accepted for compatibility
                     with the file-based repository but is only used to set the base_dir
                     attribute for CampaignService compatibility. No file I/O is performed.
        """
        self._instances: Dict[str, CampaignInstanceModel] = {}
        # Store base_dir for compatibility with CampaignService which expects it
        self.base_dir = Path(base_dir) if base_dir else Path("saves/campaigns")
        # No file loading - this is a true in-memory repository
        logger.info("Initialized InMemoryCampaignInstanceRepository (no file I/O)")

    def get_all_instances(self) -> List[CampaignInstanceModel]:
        """Get all campaign instances."""
        return list(self._instances.values())

    def get_instance(self, instance_id: str) -> Optional[CampaignInstanceModel]:
        """Get a specific campaign instance by ID."""
        return self._instances.get(instance_id)

    def create_instance(self, instance: CampaignInstanceModel) -> bool:
        """Create a new campaign instance."""
        if instance.id in self._instances:
            logger.error(f"Campaign instance {instance.id} already exists")
            return False

        self._instances[instance.id] = instance
        return True

    def update_instance(self, instance: CampaignInstanceModel) -> bool:
        """Update an existing campaign instance."""
        if instance.id not in self._instances:
            logger.error(f"Campaign instance {instance.id} not found")
            return False

        # Update last_played timestamp
        instance.last_played = datetime.now(timezone.utc)
        self._instances[instance.id] = instance
        return True

    def delete_instance(self, instance_id: str) -> bool:
        """Delete a campaign instance."""
        if instance_id not in self._instances:
            logger.error(f"Campaign instance {instance_id} not found")
            return False

        del self._instances[instance_id]
        return True

    def get_instances_with_character(
        self, character_template_id: str
    ) -> List[CampaignInstanceModel]:
        """Get all instances that include a specific character template."""
        return [
            instance
            for instance in self._instances.values()
            if character_template_id in instance.character_ids
        ]
