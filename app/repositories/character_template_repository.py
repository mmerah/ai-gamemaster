"""
Character template repository implementation for managing character template data persistence.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.repository_interfaces import ICharacterTemplateRepository
from app.models.character import CharacterTemplateModel
from app.models.utils import (
    MigrationResultModel,
)
from app.settings import Settings

logger = logging.getLogger(__name__)


class CharacterTemplateRepository(ICharacterTemplateRepository):
    """Repository for managing character template JSON files."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.templates_dir = settings.storage.character_templates_dir
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensure the character templates directory exists."""
        os.makedirs(self.templates_dir, exist_ok=True)

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
                f"Migrated character template {data.get('id', 'unknown')} from legacy format to version 1"
            )

        # Future migrations would go here:
        # if version < 2:
        #     data = self._migrate_v1_to_v2(data)
        #     data['version'] = 2
        #     version = 2
        #     migrated = True

        return MigrationResultModel(data=data, version=version, migrated=migrated)

    def get(self, template_id: str) -> Optional[CharacterTemplateModel]:
        """Load a specific character template."""
        try:
            template_file = os.path.join(self.templates_dir, f"{template_id}.json")

            if not os.path.exists(template_file):
                logger.warning(f"Character template file not found: {template_file}")
                return None

            with open(template_file, encoding="utf-8") as f:
                data = json.load(f)

            # Check version and migrate if needed
            migration_result = self._check_version(data)

            return CharacterTemplateModel(**migration_result.data)

        except Exception as e:
            logger.error(f"Error loading character template {template_id}: {e}")
            return None

    def save(self, template: CharacterTemplateModel) -> bool:
        """Save a character template."""
        try:
            # Check if this is an update (template already exists)
            template_file = os.path.join(self.templates_dir, f"{template.id}.json")
            is_update = os.path.exists(template_file)

            # Update last_modified timestamp for existing templates
            if is_update:
                template.last_modified = datetime.now(timezone.utc)
            # For new templates, ensure created_date is set
            elif template.created_date is None:
                template.created_date = datetime.now(timezone.utc)

            # Save character template file
            template_data = template.model_dump(mode="json", exclude_none=True)

            with open(template_file, "w", encoding="utf-8") as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Character template {template.id} saved successfully")
            return True

        except Exception as e:
            logger.error(f"Error saving character template {template.id}: {e}")
            return False

    def delete(self, template_id: str) -> bool:
        """Delete a character template."""
        try:
            template_file = os.path.join(self.templates_dir, f"{template_id}.json")

            if not os.path.exists(template_file):
                logger.warning(f"Character template {template_id} not found")
                return False

            # Remove template file
            os.remove(template_file)

            logger.info(f"Character template {template_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting character template {template_id}: {e}")
            return False

    def list(self) -> List[CharacterTemplateModel]:
        """List all character templates."""
        templates = []

        try:
            # Simply scan the directory for JSON files
            for filename in os.listdir(self.templates_dir):
                if filename.endswith(".json") and filename != "templates.json":
                    template_id = filename[:-5]  # Remove .json extension
                    template = self.get(template_id)
                    if template:
                        templates.append(template)
        except Exception as e:
            logger.error(f"Error loading character templates: {e}")

        return templates
