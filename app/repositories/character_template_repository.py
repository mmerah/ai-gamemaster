"""
Character template repository implementation for managing character template data persistence.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from app.game.unified_models import CharacterTemplateModel

logger = logging.getLogger(__name__)


@dataclass
class CharacterTemplateMetadata:
    """Lightweight metadata for character templates stored in index file."""
    id: str
    name: str
    race: str
    char_class: str
    level: int
    description: str
    file: str
    portrait_path: Optional[str] = None


class CharacterTemplateRepository:
    """Repository for managing character template JSON files."""
    
    def __init__(self, templates_dir: str = "saves/character_templates"):
        self.templates_dir = templates_dir
        self.templates_index_file = os.path.join(templates_dir, "templates.json")
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the character templates directory exists."""
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def _migrate_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old template data format to new unified model format."""
        # Handle field name changes
        if "subrace_name" in data:
            data["subrace"] = data.pop("subrace_name", None)
        if "subclass_name" in data:
            data["subclass"] = data.pop("subclass_name", None)
        
        # Ensure required list fields are not None
        if data.get("spells_known") is None:
            data["spells_known"] = []
        if data.get("cantrips_known") is None:
            data["cantrips_known"] = []
        
        # Ensure starting_equipment items have required fields
        if "starting_equipment" in data:
            for item in data["starting_equipment"]:
                if isinstance(item, dict):
                    # Ensure item has id and description
                    if "id" not in item and "name" in item:
                        item["id"] = item["name"].lower().replace(" ", "_")
                    if "description" not in item:
                        item["description"] = item.get("name", "Unknown item")
                    if "quantity" not in item:
                        item["quantity"] = 1
        
        return data
    
    def get_all_templates(self) -> List[CharacterTemplateMetadata]:
        """Get metadata for all available character templates."""
        try:
            if not os.path.exists(self.templates_index_file):
                return []
            
            with open(self.templates_index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            templates = []
            for template_data in data.get("templates", []):
                try:
                    templates.append(CharacterTemplateMetadata(**template_data))
                except Exception as e:
                    logger.error(f"Error parsing character template metadata: {e}")
                    continue
            
            return templates
            
        except Exception as e:
            logger.error(f"Error loading character templates index: {e}")
            return []
    
    def get_template(self, template_id: str) -> Optional[CharacterTemplateModel]:
        """Load a specific character template."""
        try:
            templates = self.get_all_templates()
            template_meta = next((t for t in templates if t.id == template_id), None)
            
            if not template_meta:
                logger.warning(f"Character template {template_id} not found in index")
                return None
            
            template_file = os.path.join(self.templates_dir, template_meta.file)
            
            if not os.path.exists(template_file):
                logger.error(f"Character template file not found: {template_file}")
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Migrate old data format
            data = self._migrate_template_data(data)
            
            return CharacterTemplateModel(**data)
            
        except Exception as e:
            logger.error(f"Error loading character template {template_id}: {e}")
            return None
    
    def save_template(self, template: CharacterTemplateModel) -> bool:
        """Save a character template."""
        try:
            # Save character template file
            template_file = os.path.join(self.templates_dir, f"{template.id}.json")
            template_data = template.model_dump(exclude_none=True)
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Update templates index
            self._update_templates_index(template)
            
            logger.info(f"Character template {template.id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving character template {template.id}: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a character template."""
        try:
            templates = self.get_all_templates()
            template_meta = next((t for t in templates if t.id == template_id), None)
            
            if not template_meta:
                logger.warning(f"Character template {template_id} not found")
                return False
            
            # Remove template file
            template_file = os.path.join(self.templates_dir, template_meta.file)
            if os.path.exists(template_file):
                os.remove(template_file)
            
            # Update templates index
            updated_templates = [t for t in templates if t.id != template_id]
            self._save_templates_index(updated_templates)
            
            logger.info(f"Character template {template_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting character template {template_id}: {e}")
            return False
    
    def get_templates_by_class(self, char_class: str) -> List[CharacterTemplateMetadata]:
        """Get all templates for a specific class."""
        templates = self.get_all_templates()
        return [t for t in templates if t.char_class.lower() == char_class.lower()]
    
    def get_templates_by_race(self, race: str) -> List[CharacterTemplateMetadata]:
        """Get all templates for a specific race."""
        templates = self.get_all_templates()
        return [t for t in templates if t.race.lower() == race.lower()]
    
    def _update_templates_index(self, template: CharacterTemplateModel) -> None:
        """Update the templates index with new or updated template."""
        templates = self.get_all_templates()
        
        # Create metadata from template
        race_desc = template.race
        if hasattr(template, 'subrace') and template.subrace:
            race_desc = f"{template.subrace} {template.race}"
        description = f"A {race_desc} {template.char_class}"
        if template.background:
            description += f" with a {template.background} background"
        if hasattr(template, 'subclass') and template.subclass:
            description += f", specializing in {template.subclass}"
        description += "."
        
        metadata = CharacterTemplateMetadata(
            id=template.id,
            name=template.name,
            race=template.race,
            char_class=template.char_class,
            level=template.level,
            description=description,
            file=f"{template.id}.json",
            portrait_path=template.portrait_path
        )
        
        # Replace existing or add new
        updated_templates = [t for t in templates if t.id != template.id]
        updated_templates.append(metadata)
        
        self._save_templates_index(updated_templates)
    
    def _save_templates_index(self, templates: List[CharacterTemplateMetadata]) -> None:
        """Save the templates index file."""
        try:
            index_data = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "templates": []
            }
            
            for template in templates:
                # Convert dataclass to dict
                template_data = {
                    "id": template.id,
                    "name": template.name,
                    "race": template.race,
                    "char_class": template.char_class,
                    "level": template.level,
                    "description": template.description,
                    "file": template.file,
                }
                if template.portrait_path:
                    template_data["portrait_path"] = template.portrait_path
                index_data["templates"].append(template_data)
            
            with open(self.templates_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving character templates index: {e}")
    
    def validate_template_ids(self, template_ids: List[str]) -> Dict[str, bool]:
        """Validate that template IDs exist and return availability status."""
        available_templates = {t.id for t in self.get_all_templates()}
        return {tid: tid in available_templates for tid in template_ids}
