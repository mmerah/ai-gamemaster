"""
Repository for managing campaign instance metadata.

Campaign instances are active/saved games created from campaign templates.
This repository manages the metadata about these instances, while the actual
game state is managed by GameStateRepository.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models import CampaignInstanceModel, MigrationResultModel

logger = logging.getLogger(__name__)


class CampaignInstanceRepository:
    """Repository for managing campaign instance metadata."""

    def __init__(self, base_dir: str = "saves/campaigns") -> None:
        self.base_dir = Path(base_dir)
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensure the campaigns directory exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_instance_path(self, instance_id: str) -> Path:
        """Get the path for a campaign instance's metadata file."""
        return self.base_dir / instance_id / "instance.json"

    def _check_version(self, data: Dict[str, Any]) -> MigrationResultModel:
        """Check save format version and handle migrations if needed."""
        version = data.get("version", 0)
        migrated = False

        if version < 1:
            # Legacy format without version field - add it
            data["version"] = 1
            version = 1
            migrated = True
            logger.info(
                f"Migrated campaign instance {data.get('id', 'unknown')} from legacy format to version 1"
            )

        # Future migrations would go here:
        # if version < 2:
        #     data = self._migrate_v1_to_v2(data)
        #     data['version'] = 2
        #     version = 2
        #     migrated = True

        return MigrationResultModel(data=data, version=version, migrated=migrated)

    def get_all_instances(self) -> List[CampaignInstanceModel]:
        """Get all campaign instances."""
        instances: List[CampaignInstanceModel] = []

        try:
            # Scan for campaign directories
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    # The name of the directory campaigns/<name_of_dir> is the ID of the campaign instance (see create_instance)
                    instance = self.get_instance(item.name)
                    if instance:
                        instances.append(instance)
        except Exception as e:
            logger.error(f"Error loading campaign instances: {e}")

        return instances

    def get_instance(self, instance_id: str) -> Optional[CampaignInstanceModel]:
        """Get a specific campaign instance by ID."""
        instance_path = self._get_instance_path(instance_id)

        if not instance_path.exists():
            return None

        try:
            with open(instance_path, encoding="utf-8") as f:
                data = json.load(f)

            # Check version and migrate if needed
            migration_result = self._check_version(data)
            return CampaignInstanceModel(**migration_result.data)
        except Exception as e:
            logger.error(f"Error loading campaign instance {instance_id}: {e}")
            return None

    def create_instance(self, instance: CampaignInstanceModel) -> bool:
        """Create a new campaign instance."""
        instance_path = self._get_instance_path(instance.id)

        if instance_path.exists():
            logger.error(f"Campaign instance {instance.id} already exists")
            return False

        try:
            # Create campaign directory
            instance_path.parent.mkdir(parents=True, exist_ok=True)

            # Save instance metadata
            with open(instance_path, "w", encoding="utf-8") as f:
                json.dump(
                    instance.model_dump(mode="json"), f, indent=2, ensure_ascii=False
                )

            return True
        except Exception as e:
            logger.error(f"Error creating campaign instance {instance.id}: {e}")
            return False

    def update_instance(self, instance: CampaignInstanceModel) -> bool:
        """Update an existing campaign instance."""
        instance_path = self._get_instance_path(instance.id)

        if not instance_path.exists():
            logger.error(f"Campaign instance {instance.id} not found")
            return False

        try:
            # Update last_played timestamp
            instance.last_played = datetime.now(timezone.utc)

            # Save updated instance
            with open(instance_path, "w", encoding="utf-8") as f:
                json.dump(
                    instance.model_dump(mode="json"), f, indent=2, ensure_ascii=False
                )

            return True
        except Exception as e:
            logger.error(f"Error updating campaign instance {instance.id}: {e}")
            return False

    def delete_instance(self, instance_id: str) -> bool:
        """Delete a campaign instance."""
        campaign_dir = self.base_dir / instance_id

        if not campaign_dir.exists():
            logger.error(f"Campaign instance {instance_id} not found")
            return False

        try:
            import shutil

            shutil.rmtree(campaign_dir)
            return True
        except Exception as e:
            logger.error(f"Error deleting campaign directory {campaign_dir}: {e}")
            return False
