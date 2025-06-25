"""Repository for managing campaign templates."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.repository_interfaces import ICampaignTemplateRepository
from app.models.campaign.template import CampaignTemplateModel
from app.models.utils import MigrationResultModel
from app.settings import Settings

logger = logging.getLogger(__name__)


class CampaignTemplateRepository(ICampaignTemplateRepository):
    """Handles storage and retrieval of campaign templates using unified models."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # Get templates directory from settings
        self.templates_dir = Path(settings.storage.campaign_templates_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure the templates directory exists."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def _get_template_path(self, template_id: str) -> Path:
        """Get the path for a specific template file."""
        return self.templates_dir / f"{template_id}.json"

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
                f"Migrated template {data.get('id', 'unknown')} from legacy format to version 1"
            )

        # Future migrations would go here:
        # if version < 2:
        #     data = self._migrate_v1_to_v2(data)
        #     data['version'] = 2
        #     version = 2
        #     migrated = True

        return MigrationResultModel(data=data, version=version, migrated=migrated)

    def list(self) -> List[CampaignTemplateModel]:
        """List all campaign templates."""
        templates: List[CampaignTemplateModel] = []

        try:
            # Simply scan the directory for JSON files
            for filename in self.templates_dir.iterdir():
                if (
                    filename.suffix == ".json"
                    and filename.name != "templates.json"
                    and filename.name != "templates_index.json"
                ):
                    template_id = filename.stem  # Remove .json extension
                    template = self.get(template_id)
                    if template:
                        templates.append(template)
        except Exception as e:
            logger.error(f"Error loading campaign templates: {e}")

        return templates

    def get(self, template_id: str) -> Optional[CampaignTemplateModel]:
        """Get a specific campaign template by ID."""
        template_path = self._get_template_path(template_id)

        if not template_path.exists():
            return None

        try:
            with open(template_path) as f:
                template_data = json.load(f)
                # Check version and migrate if needed
                migration_result = self._check_version(template_data)
                return CampaignTemplateModel(**migration_result.data)
        except Exception as e:
            logger.error(f"Error loading template {template_id}: {e}")
            return None

    def save(self, template: CampaignTemplateModel) -> bool:
        """Save a campaign template."""
        try:
            # Ensure template has an ID
            if not template.id:
                template.id = str(uuid4())

            # Check if this is an update (template already exists)
            template_path = self._get_template_path(template.id)
            is_update = template_path.exists()

            # Update last_modified timestamp for existing templates
            if is_update:
                template.last_modified = datetime.now(timezone.utc)

            # Save the template file
            template_data = template.model_dump(mode="json", exclude_none=True)

            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False, default=str)

            return True
        except Exception as e:
            logger.error(f"Error saving template {template.id}: {e}")
            return False

    def delete(self, template_id: str) -> bool:
        """Delete a campaign template."""
        template_path = self._get_template_path(template_id)

        if not template_path.exists():
            return False

        try:
            # Remove the file
            template_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            return False
