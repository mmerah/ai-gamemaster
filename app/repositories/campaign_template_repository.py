"""Repository for managing campaign templates."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
from dataclasses import dataclass, asdict, field
from app.game.unified_models import CampaignTemplateModel

logger = logging.getLogger(__name__)

@dataclass
class CampaignTemplateMetadata:
    """Lightweight metadata for campaign templates stored in index file."""
    id: str
    name: str
    description: str
    created_date: datetime
    last_modified: Optional[datetime]
    starting_level: int
    difficulty: str
    folder: str
    thumbnail: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class CampaignTemplateRepository:
    """Handles storage and retrieval of campaign templates using unified models."""
    
    def __init__(self, config):
        self.config = config
        self.templates_dir = Path(config.get('CAMPAIGN_TEMPLATES_DIR', 'saves/campaign_templates'))
        self.templates_file = self.templates_dir / 'templates.json'
        self.templates_index_file = self.templates_dir / 'templates_index.json'
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure the templates directory exists."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        if not self.templates_file.exists():
            # Create empty templates index
            self._save_templates_index({})
    
    def _load_templates_index(self) -> Dict[str, Dict]:
        """Load the templates index file."""
        try:
            with open(self.templates_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_templates_index(self, index: Dict[str, Dict]):
        """Save the templates index file."""
        with open(self.templates_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def _get_template_path(self, template_id: str) -> Path:
        """Get the path for a specific template file."""
        return self.templates_dir / f"{template_id}.json"
    
    def _migrate_template_data(self, data: Dict) -> Dict:
        """Migrate old template data format to new unified model format."""
        # Handle old structure where initial_npcs/quests were dict of dicts
        if "initial_npcs" in data:
            npcs = data["initial_npcs"]
            if npcs and isinstance(list(npcs.values())[0], dict):
                # Convert to NPCModel structure
                migrated_npcs = {}
                for npc_id, npc_data in npcs.items():
                    if "id" not in npc_data:
                        npc_data["id"] = npc_id
                    migrated_npcs[npc_id] = npc_data
                data["initial_npcs"] = migrated_npcs
        
        if "initial_quests" in data:
            quests = data["initial_quests"]
            if quests and isinstance(list(quests.values())[0], dict):
                # Convert to QuestModel structure
                migrated_quests = {}
                for quest_id, quest_data in quests.items():
                    if "id" not in quest_data:
                        quest_data["id"] = quest_id
                    migrated_quests[quest_id] = quest_data
                data["initial_quests"] = migrated_quests
        
        # Handle old starting_location format
        if "starting_location" in data and isinstance(data["starting_location"], dict):
            loc = data["starting_location"]
            if "name" in loc and "description" in loc:
                # Already in correct format
                pass
            else:
                # Convert old format if needed
                data["starting_location"] = {
                    "name": loc.get("name", "Unknown"),
                    "description": loc.get("description", "")
                }
        
        # Handle old house_rules format
        if "house_rules" in data and isinstance(data["house_rules"], dict):
            rules = data["house_rules"]
            # Ensure all required fields are present with defaults
            default_rules = {
                "critical_hit_tables": False,
                "flanking_rules": False,
                "milestone_leveling": True,
                "death_saves_public": False
            }
            default_rules.update(rules)
            data["house_rules"] = default_rules
        
        # Handle old starting_gold_range format
        if "starting_gold_range" in data and isinstance(data["starting_gold_range"], dict):
            gold_range = data["starting_gold_range"]
            if "min" in gold_range and "max" in gold_range:
                # Already in correct format
                pass
            else:
                # Convert old format if needed
                data["starting_gold_range"] = {
                    "min": gold_range.get("min", 0),
                    "max": gold_range.get("max", 0)
                }
        
        return data
    
    def get_all_templates(self) -> List[CampaignTemplateModel]:
        """Get all campaign templates."""
        templates = []
        index = self._load_templates_index()
        
        for template_id, template_info in index.items():
            template_path = self._get_template_path(template_id)
            if template_path.exists():
                try:
                    with open(template_path, 'r') as f:
                        template_data = json.load(f)
                        # Migrate old data format
                        template_data = self._migrate_template_data(template_data)
                        templates.append(CampaignTemplateModel(**template_data))
                except Exception as e:
                    print(f"Error loading template {template_id}: {e}")
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[CampaignTemplateModel]:
        """Get a specific campaign template by ID."""
        template_path = self._get_template_path(template_id)
        
        if not template_path.exists():
            return None
        
        try:
            with open(template_path, 'r') as f:
                template_data = json.load(f)
                # Migrate old data format
                template_data = self._migrate_template_data(template_data)
                return CampaignTemplateModel(**template_data)
        except Exception as e:
            print(f"Error loading template {template_id}: {e}")
            return None
    
    def save_template(self, template: CampaignTemplateModel) -> bool:
        """Save a campaign template."""
        try:
            # Ensure template has an ID
            if not template.id:
                template.id = str(uuid4())
            
            # Save the template file
            template_path = self._get_template_path(template.id)
            template_data = template.model_dump(exclude_none=True)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Update the index
            index = self._load_templates_index()
            index[template.id] = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "created_date": template.created_date.isoformat() if template.created_date else None,
                "last_modified": template.last_modified.isoformat() if template.last_modified else None,
                "tags": template.tags
            }
            self._save_templates_index(index)
            
            # Also update the metadata index
            self._update_templates_index(template)
            
            return True
        except Exception as e:
            logger.error(f"Error saving template {template.id}: {e}")
            return False
    
    def update_template(self, template_id: str, updates: Dict) -> Optional[CampaignTemplateModel]:
        """Update an existing campaign template."""
        existing_template = self.get_template(template_id)
        if not existing_template:
            return None
        
        # Update the template
        template_dict = existing_template.model_dump()
        template_dict.update(updates)
        
        # Update last_modified timestamp
        template_dict['last_modified'] = datetime.now(timezone.utc)
        
        # Create updated template
        updated_template = CampaignTemplateModel(**template_dict)
        
        # Save it
        if self.save_template(updated_template):
            return updated_template
        return None
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a campaign template."""
        template_path = self._get_template_path(template_id)
        
        if not template_path.exists():
            return False
        
        try:
            # Remove the file
            template_path.unlink()
            
            # Update the index
            index = self._load_templates_index()
            if template_id in index:
                del index[template_id]
                self._save_templates_index(index)
            
            return True
        except Exception as e:
            print(f"Error deleting template {template_id}: {e}")
            return False
    
    def create_campaign_from_template(self, template_id: str, campaign_name: Optional[str] = None) -> Optional[Dict]:
        """Create a new campaign definition from a template."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        # Generate new campaign ID
        campaign_id = str(uuid4())
        
        # Create campaign definition from template
        campaign_data = {
            "id": campaign_id,
            "name": campaign_name or f"New {template.name}",
            "description": template.description,
            "campaign_goal": template.campaign_goal,
            "starting_location": template.starting_location,
            "opening_narrative": template.opening_narrative,
            "starting_level": template.starting_level,
            "difficulty": template.difficulty,
            "ruleset_id": template.ruleset_id,
            "lore_id": template.lore_id,
            "narration_enabled": template.narration_enabled,
            "tts_voice": template.tts_voice,
            "initial_npcs": template.initial_npcs,
            "initial_quests": template.initial_quests,
            "world_lore": template.world_lore,
            "house_rules": template.house_rules,
            "created_date": datetime.now(timezone.utc).isoformat(),
            "last_played": None,
            "party_character_ids": [],  # Will be filled when starting campaign
            "event_summary": [],
            "template_id": template_id  # Track which template was used
        }
        
        # Add optional fields if present
        if template.theme_mood:
            campaign_data["theme_mood"] = template.theme_mood
        if template.allowed_races:
            campaign_data["allowed_races"] = template.allowed_races
        if template.allowed_classes:
            campaign_data["allowed_classes"] = template.allowed_classes
        if template.starting_gold_range:
            campaign_data["starting_gold_range"] = template.starting_gold_range
        if template.world_map_path:
            campaign_data["world_map_path"] = template.world_map_path
        if template.session_zero_notes:
            campaign_data["session_zero_notes"] = template.session_zero_notes
        if template.xp_system:
            campaign_data["xp_system"] = template.xp_system
        
        return campaign_data
    
    def get_all_template_metadata(self) -> List[CampaignTemplateMetadata]:
        """Get metadata for all available campaign templates."""
        try:
            if not self.templates_index_file.exists():
                # Fall back to old index format
                return self._get_metadata_from_templates()
            
            with open(self.templates_index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            templates = []
            for template_data in data.get("templates", []):
                try:
                    # Parse datetime strings
                    if "created_date" in template_data:
                        date_str = template_data["created_date"]
                        if '+00:00Z' in date_str:
                            date_str = date_str.replace('+00:00Z', '+00:00')
                        elif 'Z' in date_str and '+' not in date_str:
                            date_str = date_str.replace('Z', '+00:00')
                        template_data["created_date"] = datetime.fromisoformat(date_str)
                    if "last_modified" in template_data and template_data["last_modified"]:
                        date_str = template_data["last_modified"]
                        if '+00:00Z' in date_str:
                            date_str = date_str.replace('+00:00Z', '+00:00')
                        elif 'Z' in date_str and '+' not in date_str:
                            date_str = date_str.replace('Z', '+00:00')
                        template_data["last_modified"] = datetime.fromisoformat(date_str)
                    
                    templates.append(CampaignTemplateMetadata(**template_data))
                except Exception as e:
                    logger.error(f"Error parsing template metadata: {e}")
                    continue
            
            return templates
            
        except Exception as e:
            logger.error(f"Error loading templates index: {e}")
            return self._get_metadata_from_templates()
    
    def _get_metadata_from_templates(self) -> List[CampaignTemplateMetadata]:
        """Get metadata by loading all templates (fallback method)."""
        metadata_list = []
        templates = self.get_all_templates()
        
        for template in templates:
            metadata = CampaignTemplateMetadata(
                id=template.id,
                name=template.name,
                description=template.description,
                created_date=template.created_date,
                last_modified=template.last_modified,
                starting_level=template.starting_level,
                difficulty=template.difficulty,
                folder=template.id,  # Use ID as folder name
                thumbnail=None,
                tags=template.tags if hasattr(template, 'tags') else []
            )
            metadata_list.append(metadata)
        
        return metadata_list
    
    def update_last_modified(self, template_id: str) -> None:
        """Update the last modified timestamp for a campaign template."""
        try:
            template = self.get_template(template_id)
            if template:
                template.last_modified = datetime.now(timezone.utc)
                self.save_template(template)
            
        except Exception as e:
            logger.error(f"Error updating last modified for template {template_id}: {e}")
    
    def _update_templates_index(self, template: CampaignTemplateModel) -> None:
        """Update the templates index with new or updated template metadata."""
        metadata_list = self.get_all_template_metadata()
        
        # Create metadata from template
        metadata = CampaignTemplateMetadata(
            id=template.id,
            name=template.name,
            description=template.description,
            created_date=template.created_date,
            last_modified=template.last_modified,
            starting_level=template.starting_level,
            difficulty=template.difficulty,
            folder=template.id,
            thumbnail=None,
            tags=template.tags if hasattr(template, 'tags') else []
        )
        
        # Replace existing or add new
        updated_list = [m for m in metadata_list if m.id != template.id]
        updated_list.append(metadata)
        
        self._save_templates_index_metadata(updated_list)
    
    def _save_templates_index_metadata(self, metadata_list: List[CampaignTemplateMetadata]) -> None:
        """Save the templates index file with metadata."""
        try:
            index_data = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "templates": []
            }
            
            for metadata in metadata_list:
                metadata_dict = asdict(metadata)
                # Convert datetime objects to ISO strings
                if "created_date" in metadata_dict:
                    metadata_dict["created_date"] = metadata.created_date.isoformat()
                if "last_modified" in metadata_dict and metadata_dict["last_modified"]:
                    metadata_dict["last_modified"] = metadata.last_modified.isoformat()
                
                index_data["templates"].append(metadata_dict)
            
            with open(self.templates_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving templates index: {e}")