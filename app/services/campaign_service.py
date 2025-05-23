"""
Campaign service for managing campaigns and their lifecycle.
"""
import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.game.enhanced_models import CampaignDefinition, CampaignMetadata
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.character_template_repository import CharacterTemplateRepository

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing campaign operations."""
    
    def __init__(self, campaign_repo: CampaignRepository, character_template_repo: CharacterTemplateRepository):
        self.campaign_repo = campaign_repo
        self.character_template_repo = character_template_repo
        # Consider loading D&D 5e data here if needed frequently
        self.d5e_classes = self._load_d5e_data("classes.json")
        self.d5e_armor = self._load_basic_armor_data()  # Use basic hardcoded data for now
    
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
    
    def get_all_campaigns(self) -> List[CampaignMetadata]:
        """Get all available campaigns."""
        return self.campaign_repo.get_all_campaigns()
    
    def get_campaign(self, campaign_id: str) -> Optional[CampaignDefinition]:
        """Get a specific campaign by ID."""
        return self.campaign_repo.get_campaign(campaign_id)
    
    def create_campaign(self, campaign_data: Dict) -> Optional[CampaignDefinition]:
        """Create a new campaign."""
        try:
            # Validate required fields
            required_fields = ["id", "name", "description", "party_character_ids"]
            for field in required_fields:
                if field not in campaign_data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            # Validate character templates exist
            template_validation = self.character_template_repo.validate_template_ids(
                campaign_data["party_character_ids"]
            )
            
            invalid_templates = [tid for tid, valid in template_validation.items() if not valid]
            if invalid_templates:
                logger.error(f"Invalid character template IDs: {invalid_templates}")
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
            campaign_data.setdefault("last_played", None)
            campaign_data.setdefault("starting_level", 1)
            campaign_data.setdefault("difficulty", "normal")
            campaign_data.setdefault("house_rules", {})
            
            # Set default campaign structure if not provided
            campaign_data.setdefault("initial_npcs", {})
            campaign_data.setdefault("initial_quests", {})
            campaign_data.setdefault("world_lore", [])
            campaign_data.setdefault("event_summary", [])
            campaign_data.setdefault("opening_narrative", "Your adventure begins...")
            
            campaign = CampaignDefinition(**campaign_data)
            
            if self.campaign_repo.save_campaign(campaign):
                logger.info(f"Campaign {campaign.id} created successfully")
                return campaign
            else:
                logger.error(f"Failed to save campaign {campaign.id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return None
    
    def update_campaign(self, campaign: CampaignDefinition) -> bool:
        """Update an existing campaign."""
        try:
            # Validate character templates still exist
            template_validation = self.character_template_repo.validate_template_ids(
                campaign.party_character_ids
            )
            
            invalid_templates = [tid for tid, valid in template_validation.items() if not valid]
            if invalid_templates:
                logger.warning(f"Campaign references invalid character templates: {invalid_templates}")
            
            return self.campaign_repo.save_campaign(campaign)
            
        except Exception as e:
            logger.error(f"Error updating campaign {campaign.id}: {e}")
            return False
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign."""
        return self.campaign_repo.delete_campaign(campaign_id)
    
    def start_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Start/load a campaign and return initial game state."""
        try:
            campaign = self.campaign_repo.get_campaign(campaign_id)
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return None
            
            # Update last played timestamp
            self.campaign_repo.update_last_played(campaign_id)
            
            # Load character templates for the party
            party_characters = {}
            for char_id in campaign.party_character_ids:
                template = self.character_template_repo.get_template(char_id)
                if template:
                    # Convert template to character instance
                    char_instance = self._template_to_character_instance(template)
                    party_characters[char_id] = char_instance
                else:
                    logger.warning(f"Character template {char_id} not found")
            
            # Create initial game state
            initial_state = {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "party": party_characters,
                "current_location": campaign.starting_location,
                "campaign_goal": campaign.campaign_goal,
                "known_npcs": campaign.initial_npcs,
                "active_quests": campaign.initial_quests,
                "world_lore": campaign.world_lore,
                "event_summary": campaign.event_summary,
                "chat_history": [
                    {
                        "role": "assistant",
                        "content": campaign.opening_narrative,
                        "gm_thought": "Campaign start. Setting initial scene."
                    }
                ] if campaign.opening_narrative else [],
                "pending_player_dice_requests": [],
                "combat": {
                    "is_active": False,
                    "combatants": [],
                    "current_turn_index": 0,
                    "round_number": 1,
                    "monster_stats": {},
                    "_combat_just_started_flag": False
                },
                "_pending_npc_roll_results": []
            }
            
            return initial_state
            
        except Exception as e:
            logger.error(f"Error starting campaign {campaign_id}: {e}")
            return None
    
    def get_campaign_summary(self, campaign_id: str) -> Optional[Dict]:
        """Get a summary of campaign progress."""
        try:
            campaign = self.campaign_repo.get_campaign(campaign_id)
            if not campaign:
                return None
            
            # TODO: Load actual game state to get current progress
            # For now, return basic campaign info
            return {
                "id": campaign.id,
                "name": campaign.name,
                "description": campaign.description,
                "party_size": len(campaign.party_character_ids),
                "starting_level": campaign.starting_level,
                "difficulty": campaign.difficulty,
                "created_date": campaign.created_date,
                "last_played": campaign.last_played
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign summary for {campaign_id}: {e}")
            return None
    
    def _template_to_character_instance(self, template) -> Dict:
        """Convert a character template to a character instance for the game."""
        from app.game import utils
        
        # Calculate derived stats
        con_mod = utils.get_ability_modifier(template.base_stats.get("CON", 10))
        dex_mod = utils.get_ability_modifier(template.base_stats.get("DEX", 10))
        
        # Enhanced HP Calculation using D&D 5e class data
        char_class_data = self.d5e_classes.get("classes", {}).get(template.char_class.lower())
        hit_die = char_class_data.get("hit_die", 8) if char_class_data else 8  # Default d8
        
        if template.level == 1:
            max_hp = hit_die + con_mod
        else:
            avg_roll_per_level = (hit_die // 2) + 1
            max_hp = hit_die + con_mod + (template.level - 1) * (avg_roll_per_level + con_mod)
        max_hp = max(1, max_hp)
        
        # Enhanced AC Calculation
        ac = 10 + dex_mod  # Unarmored base
        has_shield_equipped = False
        equipped_armor_info = None

        for item_dict in template.starting_equipment:
            item_name = item_dict.get("name", "").lower()
            if item_name == "shield":  # Assuming "shield" is a distinct item name
                has_shield_equipped = True
            elif item_name in self.d5e_armor and self.d5e_armor[item_name].get("type") != "shield":
                # Simple: assume first armor found is equipped
                if equipped_armor_info is None:
                    equipped_armor_info = self.d5e_armor[item_name]
        
        if equipped_armor_info:
            current_armor_ac = equipped_armor_info["base_ac"]
            if equipped_armor_info["type"] == "light":
                current_armor_ac += dex_mod
            elif equipped_armor_info["type"] == "medium":
                current_armor_ac += min(dex_mod, equipped_armor_info.get("dex_max_bonus", 2))
            # Heavy armor typically doesn't add Dex mod unless a feature allows it
            ac = current_armor_ac
        
        if has_shield_equipped:
            ac += self.d5e_armor.get("shield", {}).get("ac_bonus", 0)  # Add shield bonus
        
        # Convert template to character instance format
        instance_data = {
            "id": template.id,
            "name": template.name,
            "race": template.race,
            "char_class": template.char_class,
            "level": template.level,
            "alignment": template.alignment,
            "background": template.background,
            "icon": template.portrait_path,
            "base_stats": template.base_stats,
            "proficiencies": template.proficiencies,
            "languages": template.languages,
            "current_hp": max_hp,
            "max_hp": max_hp,
            "temporary_hp": 0,
            "armor_class": ac,
            "conditions": [],
            "inventory": [item for item in template.starting_equipment],
            "gold": template.starting_gold,
            "spell_slots": None,  # TODO: Calculate based on class and level
            "initiative": None
        }
        
        return instance_data
