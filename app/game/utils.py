"""
Legacy utility functions for backward compatibility.
Most functionality has been moved to specialized modules.
"""
import logging
from typing import Dict, Optional

# Import from new modular structure
from .calculators.dice_mechanics import (
    get_proficiency_bonus,
    get_ability_modifier, 
    roll_dice_formula,
    format_roll_type_description,
    SKILL_TO_ABILITY
)
from .calculators.character_stats import calculate_total_modifier_for_roll

logger = logging.getLogger(__name__)

# Backward compatibility function
def calculate_modifier(character_data: Dict, roll_type: str, skill: Optional[str] = None, ability: Optional[str] = None) -> int:
    """
    Legacy function for calculating modifiers. 
    Redirects to the new modular implementation.
    
    DEPRECATED: Use calculate_total_modifier_for_roll from calculators.character_stats instead.
    """
    logger.warning("calculate_modifier is deprecated. Use calculate_total_modifier_for_roll instead.")
    return calculate_total_modifier_for_roll(character_data, roll_type, skill, ability)
