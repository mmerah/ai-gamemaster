"""In-memory character instance repository implementation.

This module provides an in-memory implementation of character instance persistence,
useful for testing and development scenarios.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.core.repository_interfaces import (
    CharacterInstanceRepository as CharacterInstanceRepositoryABC,
)
from app.models.character import CharacterInstanceModel

logger = logging.getLogger(__name__)


class InMemoryCharacterInstanceRepository(CharacterInstanceRepositoryABC):
    """In-memory repository for character instances.

    This implementation stores character instances in memory and optionally
    persists to a file-based fallback for development scenarios.
    """

    def __init__(self, fallback_dir: Optional[str] = None):
        """Initialize the repository.

        Args:
            fallback_dir: Optional directory for file-based fallback storage
        """
        self._instances: Dict[str, CharacterInstanceModel] = {}
        self._fallback_dir = fallback_dir

        # If fallback directory is provided, initialize file-based repo
        self._file_repo: Optional["CharacterInstanceRepository"]
        if fallback_dir:
            from app.repositories.game.character_instance_repository import (
                CharacterInstanceRepository,
            )

            self._file_repo = CharacterInstanceRepository(fallback_dir)
            # Load existing instances into memory
            self._load_from_files()
        else:
            self._file_repo = None

        logger.info("In-memory character instance repository initialized")

    def _load_from_files(self) -> None:
        """Load instances from file repository into memory."""
        if self._file_repo:
            try:
                instances = self._file_repo.list()
                for instance in instances:
                    self._instances[instance.id] = instance
                logger.info(f"Loaded {len(instances)} character instances from files")
            except Exception as e:
                logger.error(f"Error loading instances from files: {e}")

    def get(self, instance_id: str) -> Optional[CharacterInstanceModel]:
        """Get a character instance by ID.

        Args:
            instance_id: The unique identifier of the instance

        Returns:
            The character instance if found, None otherwise
        """
        instance = self._instances.get(instance_id)

        if instance:
            # Return a copy to prevent external modifications
            return CharacterInstanceModel.model_validate(instance.model_dump())

        logger.debug(f"Character instance {instance_id} not found")
        return None

    def save(self, instance: CharacterInstanceModel) -> bool:
        """Save a character instance.

        Args:
            instance: The character instance to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Update last_played timestamp
            instance.last_played = datetime.now()

            # Store a copy to prevent external modifications
            self._instances[instance.id] = CharacterInstanceModel.model_validate(
                instance.model_dump()
            )

            # Also save to file repository if available
            if self._file_repo:
                self._file_repo.save(instance)

            logger.info(f"Saved character instance {instance.id} to memory")
            return True

        except Exception as e:
            logger.error(f"Error saving character instance {instance.id}: {e}")
            return False

    def list_by_template(self, template_id: str) -> List[CharacterInstanceModel]:
        """List all character instances for a given template.

        Args:
            template_id: The template ID to filter by

        Returns:
            List of character instances for the template
        """
        instances = [
            CharacterInstanceModel.model_validate(instance.model_dump())
            for instance in self._instances.values()
            if instance.template_id == template_id
        ]

        # Sort by last played date, most recent first
        instances.sort(key=lambda x: x.last_played, reverse=True)
        return instances

    def list(self) -> List[CharacterInstanceModel]:
        """List all character instances.

        Returns:
            List of all character instances
        """
        instances = [
            CharacterInstanceModel.model_validate(instance.model_dump())
            for instance in self._instances.values()
        ]

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
            if instance_id not in self._instances:
                logger.warning(
                    f"Character instance {instance_id} not found for deletion"
                )
                return False

            # Remove from memory
            del self._instances[instance_id]

            # Also delete from file repository if available
            if self._file_repo:
                self._file_repo.delete(instance_id)

            logger.info(f"Deleted character instance {instance_id} from memory")
            return True

        except Exception as e:
            logger.error(f"Error deleting character instance {instance_id}: {e}")
            return False

    def clear(self) -> None:
        """Clear all instances from memory (useful for testing)."""
        self._instances.clear()
        logger.info("Cleared all character instances from memory")
