"""
Factory for creating character instances from templates and other data sources.
"""
import logging
from typing import Dict, Any, Optional
from app.game.calculators.character_stats import calculate_hit_points, calculate_armor_class
from app.game.calculators.dice_mechanics import get_ability_modifier

logger = logging.getLogger(__name__)


class CharacterFactory:
    """Factory for creating character instances from various sources."""
    
    def __init__(self, d5e_classes_data: Dict = None, armor_data: Dict = None):
        """
        Initialize the character factory with D&D 5e data.
        
        Args:
            d5e_classes_data: Dictionary of class data from D&D 5e
            armor_data: Dictionary of armor data
        """
        self.d5e_classes_data = d5e_classes_data or {}
        self.armor_data = armor_data or self._get_default_armor_data()
    
    def _get_default_armor_data(self) -> Dict[str, Dict[str, Any]]:
        """Get default armor data if none provided."""
        return {
            "leather armor": {"base_ac": 11, "type": "light", "strength_requirement": 0, "stealth_disadvantage": False},
            "studded leather": {"base_ac": 12, "type": "light", "strength_requirement": 0, "stealth_disadvantage": False},
            "scale mail": {"base_ac": 14, "type": "medium", "dex_max_bonus": 2, "strength_requirement": 0, "stealth_disadvantage": True},
            "chain mail": {"base_ac": 16, "type": "heavy", "dex_max_bonus": 0, "strength_requirement": 13, "stealth_disadvantage": True},
            "plate": {"base_ac": 18, "type": "heavy", "dex_max_bonus": 0, "strength_requirement": 15, "stealth_disadvantage": True},
            "shield": {"ac_bonus": 2, "type": "shield"}
        }
    
    def _find_equipped_armor(self, equipment: list) -> Optional[Dict[str, Any]]:
        """Find equipped armor from equipment list."""
        for item in equipment:
            # Handle both dict and ItemModel objects
            if hasattr(item, 'name'):
                item_name = item.name.lower()
            elif isinstance(item, dict):
                item_name = item.get("name", "").lower()
            else:
                continue
            
            if item_name in self.armor_data and self.armor_data[item_name].get("type") != "shield":
                return self.armor_data[item_name]
        return None
    
    def _has_shield_equipped(self, equipment: list) -> bool:
        """Check if character has a shield equipped."""
        for item in equipment:
            # Handle both dict and ItemModel objects
            if hasattr(item, 'name'):
                item_name = item.name.lower()
            elif isinstance(item, dict):
                item_name = item.get("name", "").lower()
            else:
                continue
                
            if item_name == "shield" or (item_name in self.armor_data and 
                                       self.armor_data[item_name].get("type") == "shield"):
                return True
        return False
    
    def _calculate_character_hit_points(self, template) -> int:
        """Calculate hit points for a character from template."""
        # Handle both dict and BaseStatsModel
        if hasattr(template.base_stats, 'CON'):
            con_stat = template.base_stats.CON
        else:
            con_stat = template.base_stats.get("CON", 10)
        
        con_mod = get_ability_modifier(con_stat)
        
        # Get hit die from class data
        char_class_data = self.d5e_classes_data.get("classes", {}).get(template.char_class.lower())
        hit_die = char_class_data.get("hit_die", 8) if char_class_data else 8
        
        return calculate_hit_points(template.level, con_mod, hit_die)
    
    def _calculate_character_armor_class(self, template) -> int:
        """Calculate armor class for a character from template."""
        # Handle both dict and BaseStatsModel
        if hasattr(template.base_stats, 'DEX'):
            dex_stat = template.base_stats.DEX
        else:
            dex_stat = template.base_stats.get("DEX", 10)
            
        dex_mod = get_ability_modifier(dex_stat)
        
        equipped_armor = self._find_equipped_armor(template.starting_equipment)
        has_shield = self._has_shield_equipped(template.starting_equipment)
        
        return calculate_armor_class(dex_mod, equipped_armor, has_shield)
    
    def from_template(self, template, campaign_id: str = "default") -> Dict[str, Any]:
        """
        Convert a character template to a character instance for the game.
        
        Args:
            template: CharacterTemplateModel object
            campaign_id: ID of the campaign this instance belongs to
            
        Returns:
            Dictionary representing a CharacterInstanceModel
        """
        try:
            max_hp = self._calculate_character_hit_points(template)
            
            # Create instance data matching CharacterInstanceModel
            instance_data = {
                "template_id": template.id,
                "campaign_id": campaign_id,
                "current_hp": max_hp,
                "max_hp": max_hp,
                "temp_hp": 0,
                "experience_points": 0,
                "level": template.level,
                "spell_slots_used": {},
                "hit_dice_used": 0,
                "death_saves": {"successes": 0, "failures": 0},
                "inventory": [item.model_dump() if hasattr(item, 'model_dump') else item for item in template.starting_equipment],
                "gold": template.starting_gold,
                "conditions": [],
                "exhaustion_level": 0,
                "notes": "",
                "achievements": [],
                "relationships": {}
            }
            
            return instance_data
            
        except Exception as e:
            logger.error(f"Error converting template {template.id} to character instance: {e}")
            raise
    
    def from_basic_data(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a character instance from basic character data.
        
        Args:
            character_data: Basic character information
            
        Returns:
            Dictionary representing a character instance
        """
        # Set defaults for required fields
        instance_data = {
            "id": character_data.get("id", "unknown"),
            "name": character_data.get("name", "Unknown"),
            "race": character_data.get("race", "Human"),
            "char_class": character_data.get("char_class", "Fighter"),
            "level": character_data.get("level", 1),
            "alignment": character_data.get("alignment", "Neutral"),
            "background": character_data.get("background", "Folk Hero"),
            "icon": character_data.get("icon", None),
            "base_stats": character_data.get("base_stats", {
                "STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10
            }),
            "proficiencies": character_data.get("proficiencies", {}),
            "languages": character_data.get("languages", ["Common"]),
            "current_hp": character_data.get("current_hp", 10),
            "max_hp": character_data.get("max_hp", 10),
            "temporary_hp": character_data.get("temporary_hp", 0),
            "armor_class": character_data.get("armor_class", 10),
            "conditions": character_data.get("conditions", []),
            "inventory": character_data.get("inventory", []),
            "gold": character_data.get("gold", 0),
            "spell_slots": character_data.get("spell_slots", None),
            "initiative": character_data.get("initiative", None)
        }
        
        return instance_data


def create_character_factory(d5e_classes_data: Dict = None, armor_data: Dict = None) -> CharacterFactory:
    """
    Create a character factory instance.
    
    Args:
        d5e_classes_data: D&D 5e class data
        armor_data: Armor data
        
    Returns:
        CharacterFactory instance
    """
    return CharacterFactory(d5e_classes_data, armor_data)
