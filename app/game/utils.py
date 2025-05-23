import random
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Mapping standard D&D 5e skills to their abilities
SKILL_TO_ABILITY = {
    "acrobatics": "DEX", "animal handling": "WIS", "arcana": "INT", "athletics": "STR",
    "deception": "CHA", "history": "INT", "insight": "WIS", "intimidation": "CHA",
    "investigation": "INT", "medicine": "WIS", "nature": "INT", "perception": "WIS",
    "performance": "CHA", "persuasion": "CHA", "religion": "INT", "sleight of hand": "DEX",
    "stealth": "DEX", "survival": "WIS"
}

def get_proficiency_bonus(level: int) -> int:
    """Calculates proficiency bonus based on level."""
    # Ensure level is at least 1
    return max(1, (level - 1) // 4 + 2)

def get_ability_modifier(score):
    """Calculates the ability modifier for a given score."""
    if score is None: return 0
    try:
        return (int(score) - 10) // 2
    except (ValueError, TypeError):
        logger.warning(f"Invalid score '{score}' for modifier calculation. Returning 0.")
        return 0

def calculate_modifier(character_data: Dict, roll_type: str, skill: Optional[str] = None, ability: Optional[str] = None) -> int:
    """
    Calculates the total modifier for a character's roll based on provided data dict.
    Expects character_data to have 'stats', 'proficiencies', 'proficiency_bonus'.
    Handles player and basic NPC data.
    """
    if not character_data:
        logger.error("calculate_modifier called with no character data.")
        return 0

    # Expects dict like {"STR": 10, ...}
    stats = character_data.get("stats", {})
    # Expects dict like {"skills": ["Perception"], "saving_throws": ["DEX"]}
    proficiencies = character_data.get("proficiencies", {})
    prof_bonus = character_data.get("proficiency_bonus", 0)
    base_modifier = 0
    is_proficient = False

    try:
        ability_key_for_roll = None
        if roll_type == 'skill_check' and skill:
            skill_lower = skill.lower()
            ability_key_for_roll = SKILL_TO_ABILITY.get(skill_lower)
            if ability_key_for_roll and ability_key_for_roll in stats:
                base_modifier = get_ability_modifier(stats[ability_key_for_roll])
                if skill_lower in [s.lower() for s in proficiencies.get("skills", [])]:
                    is_proficient = True
            elif ability and ability.upper() in stats:
                # Fallback to directly provided ability
                ability_key_for_roll = ability.upper()
                base_modifier = get_ability_modifier(stats[ability_key_for_roll])
            else:
                logger.warning(f"Cannot determine ability for skill '{skill}' or ability '{ability_key_for_roll}' missing in stats.")
        elif roll_type == 'saving_throw' and ability:
            ability_key_for_roll = ability.upper()
            if ability_key_for_roll in stats:
                base_modifier = get_ability_modifier(stats[ability_key_for_roll])
                if ability_key_for_roll in proficiencies.get("saving_throws", []):
                    is_proficient = True
            else:
                logger.warning(f"Ability score missing for saving throw '{ability_key_for_roll}'.")
        elif roll_type == 'initiative':
            base_modifier = get_ability_modifier(stats.get("DEX", 10))
            # Proficiency bonus is NOT added to initiative
        elif roll_type == 'attack_roll':
            # Simplified: Assume DEX for attack. Needs weapon data for proper STR/DEX.
            base_modifier = get_ability_modifier(stats.get("DEX", 10))
            # Assume proficiency with generic attacks for PoC. Needs weapon proficiency check.
            is_proficient = True # Placeholder
        elif roll_type == 'damage_roll':
            # Simplified: Assume DEX for damage bonus. Needs weapon data.
            base_modifier = get_ability_modifier(stats.get("DEX", 10))
            # Proficiency bonus not added to damage
        elif roll_type in ['ability_check', 'custom']:
            # Handle ability checks and custom rolls
            if ability and ability.upper() in stats:
                base_modifier = get_ability_modifier(stats[ability.upper()])
            else:
                logger.debug(f"No specific ability provided for {roll_type}, using 0 modifier.")
        else:
            logger.warning(f"Unknown roll type for modifier: {roll_type}")

        return base_modifier + (prof_bonus if is_proficient else 0)
    except Exception as e:
        logger.error(f"Error calculating modifier: {e}", exc_info=True)
        return 0


def roll_dice_formula(formula):
    """
    Rolls dice based on a formula string (e.g., "1d20", "2d6+3", "1d20kh1", "1d20kl1").
    Returns a tuple: (total_result, list_of_individual_rolls, base_modifier_from_formula, descriptive_string)
    Returns (0, [], 0, "Invalid Formula") on error.
    """
    if not formula or not isinstance(formula, str):
        return 0, [], 0, "Invalid Formula"

    formula_cleaned = formula.lower().replace(" ", "")
    total_value = 0
    all_rolls: list[int] = []
    modifier_from_formula = 0
    desc_parts: list[str] = []
    pattern = re.compile(r"(\d+)?d(\d+)(kh\d+|kl\d+)?|([+-]\d+)")
    
    last_match_end = 0
    for match in pattern.finditer(formula_cleaned):
        # Check for unprocessed parts between matches (should not happen with this regex but good for robustness)
        if match.start() > last_match_end:
            unmatched_part = formula_cleaned[last_match_end:match.start()]
            logger.warning(f"Unmatched part in dice formula '{formula}': '{unmatched_part}'")
            # Depending on strictness, could return error or ignore
        last_match_end = match.end()

        num_dice_str, die_size_str, keep_mod_str, const_mod_str = match.groups()

        if die_size_str:
            # It's a dice part (e.g., 2d6, d20kh1)
            try:
                num_dice = int(num_dice_str or "1")
                die_size = int(die_size_str)
                if num_dice <= 0 or die_size <= 0: raise ValueError("Dice count/size must be positive.")

                current_rolls = [random.randint(1, die_size) for _ in range(num_dice)]
                all_rolls.extend(current_rolls)
                desc_parts.append(f"{num_dice}d{die_size}{keep_mod_str or ''}")

                rolls_to_sum = list(current_rolls)
                if keep_mod_str:
                    keep_type = keep_mod_str[:2]
                    keep_count = int(keep_mod_str[2:] or "1")
                    keep_count = min(max(1, keep_count), num_dice) # Clamp keep_count

                    if keep_type == "kh": rolls_to_sum.sort(reverse=True)
                    elif keep_type == "kl": rolls_to_sum.sort()
                    else: logger.warning(f"Unknown keep modifier: {keep_type}") # Should not happen with regex
                    rolls_to_sum = rolls_to_sum[:keep_count]
                
                total_value += sum(rolls_to_sum)
            except ValueError as e:
                logger.error(f"Invalid dice component '{match.group(0)}' in '{formula}': {e}")
                return 0, [], 0, f"Invalid Dice ({match.group(0)})"
        elif const_mod_str:
             # It's a constant modifier (e.g., +3, -1)
            try:
                mod_val = int(const_mod_str)
                modifier_from_formula += mod_val
                desc_parts.append(f"{mod_val:+}")
            except ValueError:
                logger.error(f"Invalid modifier component '{const_mod_str}' in '{formula}'.")
                return 0, [], 0, f"Invalid Modifier ({const_mod_str})"
    
    # Check if the entire formula was processed
    if last_match_end < len(formula_cleaned):
        unmatched_end_part = formula_cleaned[last_match_end:]
        logger.warning(f"Trailing unmatched part in dice formula '{formula}': '{unmatched_end_part}'")
        # Decide if this is an error or ignorable

    # Conceptually add formula modifier at the end
    total_value += modifier_from_formula
    # Fallback to original if no parts
    description = " ".join(desc_parts) if desc_parts else formula
    
    logger.debug(f"Formula '{formula}' -> Rolls: {all_rolls}, FormulaMod: {modifier_from_formula}, Total: {total_value}")
    return total_value, all_rolls, modifier_from_formula, description

def format_roll_type_description(roll_type: str, skill: Optional[str], ability: Optional[str]) -> str:
    """Formats a user-friendly description of the roll type."""
    if roll_type == 'skill_check' and skill: return f"{skill.title()} Check"
    if roll_type == 'saving_throw' and ability: return f"{ability.upper()} Save"
    if roll_type == 'initiative': return "Initiative"
    # Generic fallback
    return roll_type.replace('_', ' ').title()
