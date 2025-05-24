"""
Validators for campaign and character data.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class CampaignValidator:
    """Validator for campaign data."""
    
    REQUIRED_CAMPAIGN_FIELDS = ["id", "name", "description", "party_character_ids"]
    VALID_DIFFICULTIES = ["easy", "normal", "hard"]
    
    @staticmethod
    def validate_campaign_data(campaign_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate campaign data for creation or update.
        
        Args:
            campaign_data: Campaign data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in CampaignValidator.REQUIRED_CAMPAIGN_FIELDS:
            if field not in campaign_data:
                errors.append(f"Missing required field: {field}")
            elif not campaign_data[field]:
                errors.append(f"Required field '{field}' cannot be empty")
        
        # Validate specific fields
        if "id" in campaign_data:
            if not CampaignValidator._is_valid_id(campaign_data["id"]):
                errors.append("Campaign ID must be alphanumeric with underscores/hyphens only")
        
        if "name" in campaign_data:
            if not CampaignValidator._is_valid_name(campaign_data["name"]):
                errors.append("Campaign name must be 1-100 characters")
        
        if "description" in campaign_data:
            if not CampaignValidator._is_valid_description(campaign_data["description"]):
                errors.append("Campaign description must be 1-1000 characters")
        
        if "difficulty" in campaign_data:
            if campaign_data["difficulty"] not in CampaignValidator.VALID_DIFFICULTIES:
                errors.append(f"Difficulty must be one of: {', '.join(CampaignValidator.VALID_DIFFICULTIES)}")
        
        if "party_character_ids" in campaign_data:
            if not CampaignValidator._is_valid_party_list(campaign_data["party_character_ids"]):
                errors.append("Party character IDs must be a non-empty list of strings")
        
        if "starting_level" in campaign_data:
            if not CampaignValidator._is_valid_level(campaign_data["starting_level"]):
                errors.append("Starting level must be between 1 and 20")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_id(campaign_id: str) -> bool:
        """Check if campaign ID is valid."""
        if not isinstance(campaign_id, str):
            return False
        if len(campaign_id) < 1 or len(campaign_id) > 50:
            return False
        # Allow alphanumeric, underscores, and hyphens
        return campaign_id.replace("_", "").replace("-", "").isalnum()
    
    @staticmethod
    def _is_valid_name(name: str) -> bool:
        """Check if campaign name is valid."""
        return isinstance(name, str) and 1 <= len(name.strip()) <= 100
    
    @staticmethod
    def _is_valid_description(description: str) -> bool:
        """Check if campaign description is valid."""
        return isinstance(description, str) and 1 <= len(description.strip()) <= 1000
    
    @staticmethod
    def _is_valid_party_list(party_ids: Any) -> bool:
        """Check if party character IDs list is valid."""
        if not isinstance(party_ids, list):
            return False
        if len(party_ids) == 0:
            return False
        return all(isinstance(pid, str) and len(pid.strip()) > 0 for pid in party_ids)
    
    @staticmethod
    def _is_valid_level(level: Any) -> bool:
        """Check if level is valid."""
        try:
            level_int = int(level)
            return 1 <= level_int <= 20
        except (ValueError, TypeError):
            return False


class CharacterValidator:
    """Validator for character template data."""
    
    REQUIRED_CHARACTER_FIELDS = ["id", "name", "race", "char_class", "base_stats"]
    VALID_ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    
    @staticmethod
    def validate_character_template(template_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate character template data.
        
        Args:
            template_data: Character template data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in CharacterValidator.REQUIRED_CHARACTER_FIELDS:
            if field not in template_data:
                errors.append(f"Missing required field: {field}")
            elif not template_data[field]:
                errors.append(f"Required field '{field}' cannot be empty")
        
        # Validate specific fields
        if "id" in template_data:
            if not CharacterValidator._is_valid_id(template_data["id"]):
                errors.append("Character ID must be alphanumeric with underscores/hyphens only")
        
        if "name" in template_data:
            if not CharacterValidator._is_valid_name(template_data["name"]):
                errors.append("Character name must be 1-50 characters")
        
        if "level" in template_data:
            if not CharacterValidator._is_valid_level(template_data["level"]):
                errors.append("Character level must be between 1 and 20")
        
        if "base_stats" in template_data:
            stats_valid, stats_errors = CharacterValidator._validate_ability_scores(
                template_data["base_stats"]
            )
            if not stats_valid:
                errors.extend(stats_errors)
        
        if "starting_equipment" in template_data:
            if not CharacterValidator._is_valid_equipment_list(template_data["starting_equipment"]):
                errors.append("Starting equipment must be a list of item dictionaries")
        
        if "proficiencies" in template_data:
            if not CharacterValidator._is_valid_proficiencies(template_data["proficiencies"]):
                errors.append("Proficiencies must be a dictionary with string lists")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_id(character_id: str) -> bool:
        """Check if character ID is valid."""
        if not isinstance(character_id, str):
            return False
        if len(character_id) < 1 or len(character_id) > 50:
            return False
        return character_id.replace("_", "").replace("-", "").isalnum()
    
    @staticmethod
    def _is_valid_name(name: str) -> bool:
        """Check if character name is valid."""
        return isinstance(name, str) and 1 <= len(name.strip()) <= 50
    
    @staticmethod
    def _is_valid_level(level: Any) -> bool:
        """Check if character level is valid."""
        try:
            level_int = int(level)
            return 1 <= level_int <= 20
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def _validate_ability_scores(base_stats: Any) -> Tuple[bool, List[str]]:
        """Validate ability scores dictionary."""
        errors = []
        
        if not isinstance(base_stats, dict):
            return False, ["Base stats must be a dictionary"]
        
        # Check for required abilities
        for ability in CharacterValidator.VALID_ABILITIES:
            if ability not in base_stats:
                errors.append(f"Missing ability score: {ability}")
            else:
                try:
                    score = int(base_stats[ability])
                    if not (1 <= score <= 30):  # Allow for magical enhancement
                        errors.append(f"{ability} score must be between 1 and 30")
                except (ValueError, TypeError):
                    errors.append(f"{ability} score must be a number")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_equipment_list(equipment: Any) -> bool:
        """Check if equipment list is valid."""
        if not isinstance(equipment, list):
            return False
        
        for item in equipment:
            if not isinstance(item, dict):
                return False
            if "name" not in item or not isinstance(item["name"], str):
                return False
        
        return True
    
    @staticmethod
    def _is_valid_proficiencies(proficiencies: Any) -> bool:
        """Check if proficiencies dictionary is valid."""
        if not isinstance(proficiencies, dict):
            return False
        
        for key, value in proficiencies.items():
            if not isinstance(key, str):
                return False
            if not isinstance(value, list):
                return False
            if not all(isinstance(item, str) for item in value):
                return False
        
        return True


class GameStateValidator:
    """Validator for game state data."""
    
    @staticmethod
    def validate_dice_roll_data(roll_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate dice roll submission data.
        
        Args:
            roll_data: Dice roll data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required_fields = ["character_id", "roll_type", "dice_formula"]
        
        for field in required_fields:
            if field not in roll_data:
                errors.append(f"Missing required field: {field}")
            elif not roll_data[field]:
                errors.append(f"Required field '{field}' cannot be empty")
        
        # Validate dice formula format
        if "dice_formula" in roll_data:
            if not GameStateValidator._is_valid_dice_formula(roll_data["dice_formula"]):
                errors.append("Invalid dice formula format")
        
        # Validate roll type
        if "roll_type" in roll_data:
            valid_roll_types = ["skill_check", "saving_throw", "initiative", "attack_roll", "damage_roll", "ability_check", "custom"]
            if roll_data["roll_type"] not in valid_roll_types:
                errors.append(f"Invalid roll type. Must be one of: {', '.join(valid_roll_types)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_dice_formula(formula: str) -> bool:
        """Check if dice formula is valid."""
        if not isinstance(formula, str):
            return False
        
        # Remove spaces and convert to lowercase
        formula = formula.replace(" ", "").lower()
        
        # Must have at least one 'd' with numbers before and after it
        import re
        # Pattern: number(s) + 'd' + number(s) + optional modifier
        pattern = r'^\d+d\d+([+-]\d+)?$'
        return bool(re.match(pattern, formula))


def validate_campaign_data(campaign_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Convenience function for campaign validation."""
    return CampaignValidator.validate_campaign_data(campaign_data)


def validate_character_template(template_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Convenience function for character template validation."""
    return CharacterValidator.validate_character_template(template_data)


def validate_dice_roll_data(roll_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Convenience function for dice roll validation."""
    return GameStateValidator.validate_dice_roll_data(roll_data)
