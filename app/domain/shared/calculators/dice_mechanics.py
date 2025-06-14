"""
Dice rolling and modifier calculation mechanics for D&D 5e.
"""

import logging
import random
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Mapping standard D&D 5e skills to their abilities
SKILL_TO_ABILITY = {
    "acrobatics": "DEX",
    "animal handling": "WIS",
    "arcana": "INT",
    "athletics": "STR",
    "deception": "CHA",
    "history": "INT",
    "insight": "WIS",
    "intimidation": "CHA",
    "investigation": "INT",
    "medicine": "WIS",
    "nature": "INT",
    "perception": "WIS",
    "performance": "CHA",
    "persuasion": "CHA",
    "religion": "INT",
    "sleight of hand": "DEX",
    "stealth": "DEX",
    "survival": "WIS",
}


def get_proficiency_bonus(level: int) -> int:
    """Calculate proficiency bonus based on character level."""
    return max(1, (level - 1) // 4 + 2)


def get_ability_modifier(score: Optional[int]) -> int:
    """Calculate the ability modifier for a given ability score."""
    if score is None:
        return 0
    try:
        return (int(score) - 10) // 2
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid score '{score}' for modifier calculation. Returning 0."
        )
        return 0


def roll_single_die(sides: int) -> int:
    """Roll a single die with the specified number of sides."""
    if sides <= 0:
        raise ValueError("Die sides must be positive")
    return random.randint(1, sides)


def roll_multiple_dice(count: int, sides: int) -> List[int]:
    """Roll multiple dice of the same type."""
    if count <= 0 or sides <= 0:
        raise ValueError("Dice count and sides must be positive")
    return [roll_single_die(sides) for _ in range(count)]


def apply_keep_modifier(rolls: List[int], keep_type: str, keep_count: int) -> List[int]:
    """Apply keep highest (kh) or keep lowest (kl) modifier to dice rolls."""
    if not rolls:
        return rolls

    keep_count = min(max(1, keep_count), len(rolls))

    if keep_type == "kh":  # Keep highest
        return sorted(rolls, reverse=True)[:keep_count]
    elif keep_type == "kl":  # Keep lowest
        return sorted(rolls)[:keep_count]
    else:
        logger.warning(f"Unknown keep modifier: {keep_type}")
        return rolls


def parse_dice_component(
    dice_str: str,
) -> Tuple[int, int, Optional[str], Optional[int]]:
    """
    Parse a dice component string like '2d6', 'd20', '1d20kh1'.
    Returns: (num_dice, die_size, keep_type, keep_count)
    """
    dice_pattern = re.compile(r"(\d+)?d(\d+)(kh\d+|kl\d+)?")
    match = dice_pattern.match(dice_str.lower())

    if not match:
        raise ValueError(f"Invalid dice component: {dice_str}")

    num_dice_str, die_size_str, keep_mod_str = match.groups()

    num_dice = int(num_dice_str or "1")
    die_size = int(die_size_str)

    keep_type = None
    keep_count = None

    if keep_mod_str:
        keep_type = keep_mod_str[:2]
        keep_count = int(keep_mod_str[2:] or "1")

    return num_dice, die_size, keep_type, keep_count


def roll_dice_formula(formula: str) -> Tuple[int, List[int], int, str]:
    """
    Roll dice based on a formula string (e.g., "1d20", "2d6+3", "1d20kh1").
    Returns: (total_result, individual_rolls, modifier_from_formula, description)
    """
    if not formula or not isinstance(formula, str):
        return 0, [], 0, "Invalid Formula"

    formula_cleaned = formula.lower().replace(" ", "")
    total_value = 0
    all_rolls: List[int] = []
    modifier_from_formula = 0
    desc_parts: List[str] = []

    # Pattern to match dice (e.g., 2d6kh1) and modifiers (e.g., +3, -1)
    pattern = re.compile(r"(\d+)?d(\d+)(kh\d+|kl\d+)?|([+-]\d+)")

    last_match_end = 0
    for match in pattern.finditer(formula_cleaned):
        # Check for unprocessed parts between matches
        if match.start() > last_match_end:
            unmatched_part = formula_cleaned[last_match_end : match.start()]
            logger.warning(
                f"Unmatched part in dice formula '{formula}': '{unmatched_part}'"
            )
        last_match_end = match.end()

        num_dice_str, die_size_str, keep_mod_str, const_mod_str = match.groups()

        if die_size_str:  # It's a dice component
            try:
                num_dice, die_size, keep_type, keep_count = parse_dice_component(
                    match.group(0)
                )

                current_rolls = roll_multiple_dice(num_dice, die_size)
                all_rolls.extend(current_rolls)
                desc_parts.append(f"{num_dice}d{die_size}{keep_mod_str or ''}")

                rolls_to_sum = current_rolls
                if keep_type and keep_count:
                    rolls_to_sum = apply_keep_modifier(
                        current_rolls, keep_type, keep_count
                    )

                total_value += sum(rolls_to_sum)

            except ValueError as e:
                logger.error(
                    f"Invalid dice component '{match.group(0)}' in '{formula}': {e}"
                )
                return 0, [], 0, f"Invalid Dice ({match.group(0)})"

        elif const_mod_str:  # It's a constant modifier
            try:
                mod_val = int(const_mod_str)
                modifier_from_formula += mod_val
                desc_parts.append(f"{mod_val:+}")
            except ValueError:
                logger.error(
                    f"Invalid modifier component '{const_mod_str}' in '{formula}'."
                )
                return 0, [], 0, f"Invalid Modifier ({const_mod_str})"

    # Check if the entire formula was processed
    if last_match_end < len(formula_cleaned):
        unmatched_end_part = formula_cleaned[last_match_end:]
        logger.warning(
            f"Trailing unmatched part in dice formula '{formula}': '{unmatched_end_part}'"
        )

    total_value += modifier_from_formula
    description = " ".join(desc_parts) if desc_parts else formula

    logger.debug(
        f"Formula '{formula}' -> Rolls: {all_rolls}, FormulaMod: {modifier_from_formula}, Total: {total_value}"
    )
    return total_value, all_rolls, modifier_from_formula, description


def format_roll_type_description(
    roll_type: str, skill: Optional[str] = None, ability: Optional[str] = None
) -> str:
    """Format a user-friendly description of the roll type."""
    if roll_type == "skill_check" and skill:
        return f"{skill.title()} Check"
    if roll_type == "saving_throw" and ability:
        return f"{ability.upper()} Save"
    if roll_type == "initiative":
        return "Initiative"
    # Generic fallback
    return roll_type.replace("_", " ").title()
