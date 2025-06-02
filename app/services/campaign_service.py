"""
Campaign service for managing campaigns and their lifecycle.
"""
import logging
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.game.unified_models import CampaignTemplateModel, CampaignInstanceModel, CharacterTemplateModel
from app.repositories.campaign_template_repository import CampaignTemplateMetadata, CampaignTemplateRepository
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.repositories.campaign_instance_repository import CampaignInstanceRepository
from app.game.factories.character_factory import create_character_factory

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing campaign operations."""
    
    def __init__(self, campaign_template_repo: CampaignTemplateRepository, character_template_repo: CharacterTemplateRepository, 
                 campaign_instance_repo: CampaignInstanceRepository):
        self.campaign_template_repo = campaign_template_repo
        self.character_template_repo = character_template_repo
        self.instance_repo = campaign_instance_repo
        # Load D&D 5e data for character creation
        self.d5e_classes = self._load_d5e_data("classes.json")
        self.d5e_armor = self._load_basic_armor_data()
        # Create character factory with loaded data
        self.character_factory = create_character_factory(self.d5e_classes, self.d5e_armor)
    
    def _load_d5e_data(self, filename: str):
        """Load D&D 5e data from JSON files."""
        try:
            data_file = os.path.join("saves", "d5e_data", filename)
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
        return {}
    
    def _load_basic_armor_data(self):
        """Load basic armor data (hardcoded for now)."""
        return {
            "leather armor": {"base_ac": 11, "type": "light", "strength_requirement": 0, "stealth_disadvantage": False},
            "studded leather": {"base_ac": 12, "type": "light", "strength_requirement": 0, "stealth_disadvantage": False},
            "scale mail": {"base_ac": 14, "type": "medium", "dex_max_bonus": 2, "strength_requirement": 0, "stealth_disadvantage": True},
            "chain mail": {"base_ac": 16, "type": "heavy", "dex_max_bonus": 0, "strength_requirement": 13, "stealth_disadvantage": True},
            "plate": {"base_ac": 18, "type": "heavy", "dex_max_bonus": 0, "strength_requirement": 15, "stealth_disadvantage": True},
            "shield": {"ac_bonus": 2, "type": "shield"}
        }
    
    def get_all_campaigns(self) -> List[CampaignTemplateMetadata]:
        """Get all available campaign templates."""
        return self.campaign_template_repo.get_all_template_metadata()
    
    def get_campaign_overview(self) -> Dict[str, List]:
        """Get a unified view of campaign templates and instances.
        
        Returns:
            Dict with 'templates' and 'instances' keys
        """
        try:
            # Get all templates
            templates = self.campaign_template_repo.get_all_template_metadata()
            
            # Get all instances
            instances = self.instance_repo.get_all_instances()
            
            # Convert to serializable format
            return {
                "templates": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "description": t.description,
                        "created_date": t.created_date.isoformat() if t.created_date else None,
                        "last_modified": t.last_modified.isoformat() if t.last_modified else None,
                        "starting_level": t.starting_level,
                        "difficulty": t.difficulty,
                        "thumbnail": t.thumbnail,
                        "tags": t.tags
                    }
                    for t in templates
                ],
                "instances": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "template_id": i.template_id,
                        "character_ids": i.character_ids,
                        "party_size": len(i.character_ids),
                        "current_location": i.current_location,
                        "session_count": i.session_count,
                        "in_combat": i.in_combat,
                        "created_date": i.created_date.isoformat() if i.created_date else None,
                        "last_played": i.last_played.isoformat() if i.last_played else None
                    }
                    for i in instances
                ]
            }
        except Exception as e:
            logger.error(f"Error getting campaign overview: {e}")
            return {"templates": [], "instances": []}
    
    def get_campaign(self, campaign_id: str) -> Optional[CampaignTemplateModel]:
        """Get a specific campaign by ID."""
        return self.campaign_template_repo.get_template(campaign_id)
    
    def create_campaign(self, campaign_data: Dict) -> Optional[CampaignTemplateModel]:
        """Create a new campaign template."""
        try:
            # Validate required fields for template
            required_fields = ["id", "name", "description"]
            for field in required_fields:
                if field not in campaign_data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            # Fix for starting_location:
            raw_starting_location = campaign_data.get('starting_location')
            if isinstance(raw_starting_location, str) and raw_starting_location.strip():
                campaign_data['starting_location'] = {
                    "name": raw_starting_location,
                    "description": "The adventure begins here." 
                }
            elif not raw_starting_location or (isinstance(raw_starting_location, dict) and not raw_starting_location.get("name")):
                campaign_data['starting_location'] = {
                    "name": "Unknown Starting Point",
                    "description": "The adventure's origin is yet to be defined."
                }
            
            # Set defaults and create campaign with timezone-aware datetime
            campaign_data.setdefault("created_date", datetime.now(timezone.utc))
            campaign_data.setdefault("starting_level", 1)
            campaign_data.setdefault("difficulty", "normal")
            campaign_data.setdefault("house_rules", {})
            campaign_data.setdefault("narration_enabled", False)
            campaign_data.setdefault("tts_voice", "af_heart")
            
            # Set default campaign structure if not provided
            campaign_data.setdefault("initial_npcs", {})
            campaign_data.setdefault("initial_quests", {})
            campaign_data.setdefault("world_lore", [])
            campaign_data.setdefault("opening_narrative", "Your adventure begins...")
            campaign_data.setdefault("campaign_goal", "Begin your adventure")
            
            campaign = CampaignTemplateModel(**campaign_data)
            
            if self.campaign_template_repo.save_template(campaign):
                logger.info(f"Campaign {campaign.id} created successfully")
                return campaign
            else:
                logger.error(f"Failed to save campaign {campaign.id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return None
    
    def update_campaign(self, campaign: CampaignTemplateModel) -> bool:
        """Update an existing campaign template."""
        try:
            return self.campaign_template_repo.save_template(campaign)
            
        except Exception as e:
            logger.error(f"Error updating campaign {campaign.id}: {e}")
            return False
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign."""
        return self.campaign_template_repo.delete_template(campaign_id)
    
    def create_campaign_instance(self, template_id: str, instance_name: str, character_ids: List[str]) -> Optional[CampaignInstanceModel]:
        """Create a new campaign instance from a template."""
        try:
            # Load the template
            template = self.campaign_template_repo.get_template(template_id)
            if not template:
                logger.error(f"Campaign template {template_id} not found")
                return None
            
            # Validate character templates exist
            template_validation = self.character_template_repo.validate_template_ids(character_ids)
            invalid_templates = [tid for tid, valid in template_validation.items() if not valid]
            if invalid_templates:
                logger.error(f"Invalid character template IDs: {invalid_templates}")
                return None
            
            # Create campaign instance
            instance_id = f"{template_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            event_log_path = os.path.join("saves", "campaigns", instance_id, "event_log.json")
            
            campaign_instance = CampaignInstanceModel(
                id=instance_id,
                name=instance_name,
                template_id=template_id,
                character_ids=character_ids,
                current_location=template.starting_location.name,
                session_count=0,
                in_combat=False,
                event_summary=[],
                event_log_path=event_log_path,
                created_date=datetime.now(timezone.utc),
                last_played=datetime.now(timezone.utc)
            )
            
            # Save campaign instance to repository
            if self.instance_repo.create_instance(campaign_instance):
                logger.info(f"Campaign instance {instance_id} created successfully")
                return campaign_instance
            else:
                logger.error(f"Failed to save campaign instance {instance_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating campaign instance: {e}")
            return None
    
    def start_campaign_from_template(self, template_id: str, instance_name: str, party_character_ids: List[str]) -> Optional[Dict]:
        """Create and start a new campaign instance from a template."""
        try:
            # Create campaign instance
            campaign_instance = self.create_campaign_instance(template_id, instance_name, party_character_ids)
            if not campaign_instance:
                return None
            
            # Load the template for additional data
            template = self.campaign_template_repo.get_template(template_id)
            if not template:
                logger.error(f"Campaign template {template_id} not found")
                return None
            
            # Load character templates for the party
            party_characters = {}
            for char_id in party_character_ids:
                char_template = self.character_template_repo.get_template(char_id)
                if char_template:
                    # Convert template to character instance
                    char_instance = self._template_to_character_instance(char_template, campaign_instance.id)
                    party_characters[char_id] = char_instance
                else:
                    logger.warning(f"Character template {char_id} not found")
            
            # Ensure event log directory and file exist
            event_log_dir = os.path.dirname(campaign_instance.event_log_path)
            os.makedirs(event_log_dir, exist_ok=True)
            if not os.path.exists(campaign_instance.event_log_path):
                try:
                    with open(campaign_instance.event_log_path, "w", encoding="utf-8") as f:
                        json.dump({"events": []}, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.error(f"Failed to initialize event log for campaign {campaign_instance.id}: {e}")

            initial_state = {
                "campaign_id": campaign_instance.id,
                "campaign_name": campaign_instance.name,
                "party": party_characters,
                "current_location": template.starting_location,
                "campaign_goal": template.campaign_goal,
                "known_npcs": template.initial_npcs,
                "active_quests": template.initial_quests,
                "world_lore": template.world_lore,
                "event_summary": campaign_instance.event_summary,
                # TTS settings hierarchy: instance override > template default
                "narration_enabled": (
                    campaign_instance.narration_enabled 
                    if campaign_instance.narration_enabled is not None 
                    else template.narration_enabled
                ),
                "tts_voice": campaign_instance.tts_voice or template.tts_voice,
                "active_ruleset_id": getattr(template, "ruleset_id", None),
                "active_lore_id": getattr(template, "lore_id", None),
                "event_log_path": campaign_instance.event_log_path,
                "chat_history": [
                    {
                        "role": "assistant",
                        "content": template.opening_narrative,
                        "gm_thought": "Campaign start. Setting initial scene."
                    }
                ] if template.opening_narrative else [],
                "pending_player_dice_requests": [],
                "combat": {
                    "is_active": False,
                    "combatants": [],
                    "current_turn_index": 0,
                    "round_number": 1,
                    "monster_stats": {}
                }
            }
            
            return initial_state
            
        except Exception as e:
            logger.error(f"Error starting campaign from template {template_id}: {e}")
            return None
    
    def _create_game_state_dict(self, template: CampaignTemplateModel, instance: Optional[CampaignInstanceModel] = None, party_characters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper method to create game state dictionary from template and optional instance."""
        return {
            "campaign_id": instance.id if instance else template.id,
            "campaign_name": instance.name if instance else template.name,
            "party": party_characters or {},
            "current_location": template.starting_location,
            "campaign_goal": template.campaign_goal,
            "known_npcs": template.initial_npcs,
            "active_quests": template.initial_quests,
            "world_lore": template.world_lore,
            "event_summary": instance.event_summary if instance else [],
            "narration_enabled": template.narration_enabled,
            "tts_voice": template.tts_voice,
            "active_ruleset_id": getattr(template, "ruleset_id", None),
            "active_lore_id": getattr(template, "lore_id", None),
            "event_log_path": instance.event_log_path if instance else None,
            "chat_history": [
                {
                    "role": "assistant",
                    "content": template.opening_narrative,
                    "gm_thought": "Campaign start. Setting initial scene."
                }
            ] if template.opening_narrative else [],
            "pending_player_dice_requests": [],
            "combat": {
                "is_active": False,
                "combatants": [],
                "current_turn_index": 0,
                "round_number": 1,
                "monster_stats": {}
            }
        }
    
    def start_campaign(self, campaign_id: str, party_character_ids: Optional[List[str]] = None) -> Optional[Dict]:
        """Start a campaign (backward compatibility method).
        
        This method handles both campaign instances and templates:
        - If campaign_id is an instance ID, loads that instance
        - If campaign_id is a template ID and party_character_ids provided, creates new instance
        - Otherwise treats as template view
        """
        # First check if this is a campaign instance
        instance = self.instance_repo.get_instance(campaign_id)
        if instance:
            # This is an instance - load its template and use its character IDs
            template = self.campaign_template_repo.get_template(instance.template_id)
            if not template:
                logger.error(f"Campaign template {instance.template_id} not found for instance {campaign_id}")
                return None
            
            # Build the party characters
            party_characters = {}
            for char_id in instance.character_ids:
                char_template = self.character_template_repo.get_template(char_id)
                if char_template:
                    party_characters[char_id] = self._template_to_character_instance(char_template, campaign_id)
                else:
                    logger.warning(f"Character template {char_id} not found for campaign instance {campaign_id}")
            
            return self._create_game_state_dict(template, instance, party_characters)
            
        elif party_character_ids:
            # Create a new instance from template
            instance_name = f"Adventure - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
            return self.start_campaign_from_template(campaign_id, instance_name, party_character_ids)
        else:
            # Try to load as a template and return minimal state
            try:
                template = self.campaign_template_repo.get_template(campaign_id)
                if not template:
                    logger.error(f"Campaign template {campaign_id} not found")
                    return None
                
                # Return minimal state for template viewing
                return self._create_game_state_dict(template)
            except Exception as e:
                logger.error(f"Error starting campaign {campaign_id}: {e}")
                return None
    
    def get_campaign_summary(self, campaign_id: str) -> Optional[Dict]:
        """Get a summary of campaign progress."""
        try:
            campaign = self.campaign_template_repo.get_template(campaign_id)
            if not campaign:
                return None
            
            # TODO: Load actual game state to get current progress
            # For now, return basic campaign info
            return {
                "id": campaign.id,
                "name": campaign.name,
                "description": campaign.description,
                "starting_level": campaign.starting_level,
                "difficulty": campaign.difficulty,
                "created_date": campaign.created_date,
                "last_modified": campaign.last_modified
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign summary for {campaign_id}: {e}")
            return None
    
    def _template_to_character_instance(self, template: CharacterTemplateModel, campaign_id: str = "default") -> Dict[str, Any]:
        """Convert a character template to a character instance for the game."""
        # Use the character factory for conversion
        return self.character_factory.from_template(template, campaign_id)
