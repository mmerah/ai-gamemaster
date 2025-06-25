"""Character instance repository implementation.

This module provides file-based persistence for character instances,
implementing the CharacterInstanceRepositoryProtocol.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.core.repository_interfaces import ICharacterInstanceRepository
from app.models.character.instance import CharacterInstanceModel
from app.settings import Settings

logger = logging.getLogger(__name__)


class CharacterInstanceRepository(ICharacterInstanceRepository):
    """File-based repository for character instances."""

    def __init__(self, settings: Settings):
        """Initialize the repository.

        Args:
            settings: Application settings
        """
        self.settings = settings
        # Character instances are stored under saves directory
        # This is intentionally hardcoded as it's not user-configurable
        self.base_dir = Path(
            os.path.join(settings.storage.saves_dir, "character_instances")
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Character instance repository initialized at {self.base_dir}")

    def _get_file_path(self, instance_id: str) -> Path:
        """Get the file path for a character instance.

        Args:
            instance_id: The character instance ID

        Returns:
            Path to the instance file
        """
        # Sanitize the ID for use as a filename
        safe_id = "".join(c for c in instance_id if c.isalnum() or c in "-_")
        return self.base_dir / f"{safe_id}.json"

    def get(self, instance_id: str) -> Optional[CharacterInstanceModel]:
        """Get a character instance by ID.

        Args:
            instance_id: The unique identifier of the instance

        Returns:
            The character instance if found, None otherwise
        """
        file_path = self._get_file_path(instance_id)

        if not file_path.exists():
            logger.debug(f"Character instance {instance_id} not found")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return CharacterInstanceModel(**data)
        except Exception as e:
            logger.error(f"Error loading character instance {instance_id}: {e}")
            return None

    def save(self, instance: CharacterInstanceModel) -> bool:
        """Save a character instance.

        Args:
            instance: The character instance to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            file_path = self._get_file_path(instance.id)

            # Update last_played timestamp
            instance.last_played = datetime.now(timezone.utc)

            # Convert to dict for JSON serialization
            data = instance.model_dump(mode="json")

            # Write to temporary file first for atomicity
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(file_path)

            logger.info(f"Saved character instance {instance.id}")
            return True

        except Exception as e:
            logger.error(f"Error saving character instance {instance.id}: {e}")
            return False

    def list(self) -> List[CharacterInstanceModel]:
        """List all character instances.

        Returns:
            List of all character instances
        """
        instances = []

        for file_path in self.base_dir.glob("*.json"):
            if file_path.suffix != ".json" or file_path.stem.endswith(".tmp"):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    instance = CharacterInstanceModel(**data)
                    instances.append(instance)

            except Exception as e:
                logger.error(f"Error loading instance from {file_path}: {e}")
                continue

        # Sort by last played date, most recent first
        instances.sort(key=lambda x: x.last_played, reverse=True)
        return instances

    def delete(self, instance_id: str) -> bool:
        """Delete a character instance by ID.

        Args:
            instance_id: The unique identifier of the instance

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self._get_file_path(instance_id)

            if not file_path.exists():
                logger.warning(
                    f"Character instance {instance_id} not found for deletion"
                )
                return False

            # Create backup before deletion
            backup_dir = self.base_dir / "deleted"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{file_path.stem}_{timestamp}.json"

            # Move to backup directory instead of permanent deletion
            file_path.rename(backup_path)

            logger.info(
                f"Deleted character instance {instance_id} (backed up to {backup_path})"
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting character instance {instance_id}: {e}")
            return False
