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
    level = max(1, level)
    return (level - 1) // 4 + 2

def get_ability_modifier(score):
    """Calculates the ability modifier for a given score."""
    if score is None: return 0 # Handle None score
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

    stats = character_data.get("stats", {}) # Expects dict like {"STR": 10, ...}
    proficiencies = character_data.get("proficiencies", {}) # Expects dict like {"skills": ["Perception"], "saving_throws": ["DEX"]}
    prof_bonus = character_data.get("proficiency_bonus", 0)
    base_modifier = 0
    is_proficient = False
    ability_short = None

    try:
        if roll_type == 'skill_check' and skill:
            skill_lower = skill.lower()
            ability_short = SKILL_TO_ABILITY.get(skill_lower)
            if ability_short and ability_short in stats:
                base_modifier = get_ability_modifier(stats[ability_short])
                # Check against lowercase list of skills
                if skill_lower in [s.lower() for s in proficiencies.get("skills", [])]:
                    is_proficient = True
            else:
                logger.warning(f"Could not determine ability for skill '{skill}' or ability score '{ability_short}' missing in stats: {stats.keys()}")
                # Fallback: maybe the AI provided the ability directly?
                if ability and ability.upper() in stats:
                    ability_short = ability.upper()
                    base_modifier = get_ability_modifier(stats[ability_short])
                    logger.debug(f"Using provided ability '{ability_short}' for skill check fallback.")
                else:
                    base_modifier = 0

        elif roll_type == 'saving_throw' and ability:
            ability_short = ability.upper() # Ensure uppercase for matching keys like STR, DEX
            if ability_short in stats:
                base_modifier = get_ability_modifier(stats[ability_short])
                # Check against list of saving throw profs (usually uppercase)
                if ability_short in proficiencies.get("saving_throws", []):
                    is_proficient = True
            else:
                logger.warning(f"Ability score missing for saving throw '{ability_short}'.")
                base_modifier = 0

        elif roll_type == 'initiative':
            ability_short = "DEX"
            if ability_short in stats:
                base_modifier = get_ability_modifier(stats[ability_short])
            else:
                logger.warning(f"DEX score missing for initiative in stats: {stats.keys()}")
                base_modifier = 0
            # Proficiency bonus is NOT added to initiative
            is_proficient = False

        elif roll_type == 'attack_roll':
            # Basic melee/ranged logic - NEEDS IMPROVEMENT WITH WEAPON DATA
            # Defaulting to DEX for now as a common case.
            ability_short = "DEX" # Assume finesse/ranged default
            str_mod = get_ability_modifier(stats.get("STR", 10))
            dex_mod = get_ability_modifier(stats.get("DEX", 10))
            # Simple Finesse check: use higher of STR/DEX if DEX is primary stat? No, use DEX.
            # TODO: Need weapon info to determine STR vs DEX. Defaulting to DEX.
            base_modifier = dex_mod
            # Assume proficiency with generic attacks for now
            # TODO: Check weapon proficiencies list if available
            is_proficient = True # Placeholder assumption

        elif roll_type == 'damage_roll':
            # Damage usually adds ability mod but not proficiency
            # Needs weapon data to know which ability (STR/DEX)
            # Simplified: Add DEX mod for PoC
            ability_short = "DEX"
            if ability_short in stats:
                base_modifier = get_ability_modifier(stats[ability_short])
            else:
                base_modifier = 0
            is_proficient = False # Proficiency bonus not added to damage

        else:
            logger.warning(f"Unknown roll type for modifier calculation: {roll_type}")
            base_modifier = 0
            is_proficient = False

        total_modifier = base_modifier + (prof_bonus if is_proficient else 0)
        return total_modifier

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

    formula = formula.lower().replace(" ", "")
    original_formula = formula # Keep original for description if needed
    logger.debug(f"Rolling dice formula: {formula}")

    total = 0
    rolls = []
    base_modifier = 0
    description_parts = []

    # Regex to find dice parts (XdY[kh/klZ]?) and constant modifiers (+/-N)
    pattern = re.compile(r"(\d+)?d(\d+)(kh\d+|kl\d+)?|([+-]\d+)")
    matches = pattern.finditer(formula)

    processed_indices = set()

    for match in matches:
        start, end = match.span()
        # Skip if this part overlaps with a previously processed part (e.g., modifier inside kh/kl)
        if any(i in processed_indices for i in range(start, end)):
            continue

        part = match.group(0)
        processed_indices.update(range(start, end))

        dice_part = match.group(1) or match.group(2) or match.group(3) # Check if it's a dice part
        mod_part = match.group(4) # Check if it's a modifier part

        if dice_part: # It's a dice roll XdY[kh/klZ]?
            num_dice_str = match.group(1) or "1" # Default to 1 die if number omitted (e.g., d20)
            die_size_str = match.group(2)
            keep_mod = match.group(3) # e.g., kh1, kl1

            try:
                num_dice = int(num_dice_str)
                die_size = int(die_size_str)
                if num_dice <= 0 or die_size <= 0:
                    raise ValueError("Number of dice and size must be positive")

                current_rolls = [random.randint(1, die_size) for _ in range(num_dice)]
                rolls.extend(current_rolls)
                description_parts.append(f"{num_dice}d{die_size}")

                rolls_to_sum = list(current_rolls) # Copy list

                if keep_mod:
                    keep_type = keep_mod[:2] # kh or kl
                    keep_num_str = keep_mod[2:]
                    keep_num = int(keep_num_str) if keep_num_str else 1 # Default keep 1

                    if keep_num > num_dice: keep_num = num_dice # Can't keep more than rolled
                    if keep_num < 1: keep_num = 1 # Must keep at least 1

                    description_parts[-1] += keep_mod # Add kh/kl to description

                    if keep_type == "kh":
                        rolls_to_sum.sort(reverse=True) # Descending for highest
                    elif keep_type == "kl":
                        rolls_to_sum.sort() # Ascending for lowest
                    else:
                        logger.warning(f"Unknown keep modifier: {keep_type}")

                    rolls_to_sum = rolls_to_sum[:keep_num] # Take the top/bottom N

                total += sum(rolls_to_sum)

            except ValueError as e:
                logger.error(f"Invalid dice format in '{part}': {e}")
                return 0, [], 0, f"Invalid Dice ({part})"

        elif mod_part: # It's a constant modifier +/-N
            try:
                mod_value = int(mod_part)
                base_modifier += mod_value
                description_parts.append(f"{mod_value:+}") # Format with sign
            except ValueError:
                logger.error(f"Invalid modifier format: {mod_part}")
                return 0, [], 0, f"Invalid Modifier ({mod_part})"

    total += base_modifier # Add modifier from formula only at the end conceptually
    description = " ".join(description_parts) if description_parts else original_formula

    logger.debug(f"Formula '{formula}' -> Rolls: {rolls}, BaseMod: {base_modifier}, Total: {total}")
    return total, rolls, base_modifier, description