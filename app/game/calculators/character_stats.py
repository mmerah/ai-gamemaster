"""
Character statistics calculation mechanics for D&D 5e.
"""
import logging
from typing import Dict, List, Optional, Any
from .dice_mechanics import get_ability_modifier, get_proficiency_bonus, SKILL_TO_ABILITY

logger = logging.getLogger(__name__)


def calculate_hit_points(
    level: int,
    constitution_modifier: int,
    hit_die: int = 8,
    use_average_rolls: bool = True
) -> int:
    """
    Calculate maximum hit points for a character.
    
    Args:
        level: Character level
        constitution_modifier: CON modifier
        hit_die: Hit die size (default d8)
        use_average_rolls: If True, use average rolls; if False, use max rolls
    
    Returns:
        Maximum hit points
    """
    if level <= 0:
        return 1
    
    if level == 1:
        # First level always gets max hit die + CON mod
        max_hp = hit_die + constitution_modifier
    else:
        if use_average_rolls:
            # Average roll per level after 1st (D&D 5e average: (die_size + 1) / 2)
            avg_roll_per_level = (hit_die + 1) / 2
            max_hp = hit_die + constitution_modifier + (level - 1) * (avg_roll_per_level + constitution_modifier)
        else:
            # Maximum possible HP (max roll every level)
            max_hp = level * hit_die + (level * constitution_modifier)
    
    return max(1, max_hp)


def calculate_armor_class(
    base_dexterity_modifier: int,
    equipped_armor: Optional[Dict[str, Any]] = None,
    has_shield: bool = False,
    natural_armor_bonus: int = 0
) -> int:
    """
    Calculate armor class based on equipped armor and modifiers.
    
    Args:
        base_dexterity_modifier: Character's DEX modifier
        equipped_armor: Armor data with AC and type info
        has_shield: Whether character has a shield equipped
        natural_armor_bonus: Any natural armor bonus
    
    Returns:
        Total armor class
    """
    base_ac = 10  # Unarmored base AC
    dex_modifier = base_dexterity_modifier
    
    if equipped_armor:
        armor_type = equipped_armor.get("type", "light")
        base_ac = equipped_armor.get("base_ac", 10)
        
        if armor_type == "light":
            # Light armor: full DEX modifier
            pass
        elif armor_type == "medium":
            # Medium armor: DEX modifier capped at +2
            dex_modifier = min(dex_modifier, equipped_armor.get("dex_max_bonus", 2))
        elif armor_type == "heavy":
            # Heavy armor: no DEX modifier (unless special feature)
            dex_modifier = 0
    
    ac = base_ac + dex_modifier + natural_armor_bonus
    
    if has_shield:
        ac += 2  # Standard shield bonus
    
    return ac


def calculate_saving_throw_modifier(
    ability_score: int,
    level: int,
    is_proficient: bool = False
) -> int:
    """Calculate saving throw modifier for an ability."""
    ability_mod = get_ability_modifier(ability_score)
    prof_bonus = get_proficiency_bonus(level) if is_proficient else 0
    return ability_mod + prof_bonus


def calculate_skill_modifier(
    ability_scores: Dict[str, int],
    skill_name: str,
    level: int,
    skill_proficiencies: List[str],
    expertise_skills: Optional[List[str]] = None
) -> int:
    """
    Calculate skill modifier for a character.
    
    Args:
        ability_scores: Dict of ability scores (e.g., {"STR": 14, "DEX": 16, ...})
        skill_name: Name of the skill
        level: Character level
        skill_proficiencies: List of proficient skills
        expertise_skills: List of skills with expertise (double proficiency)
    
    Returns:
        Total skill modifier
    """
    if expertise_skills is None:
        expertise_skills = []
    
    # Get the ability for this skill
    ability_key = SKILL_TO_ABILITY.get(skill_name.lower())
    if not ability_key or ability_key not in ability_scores:
        logger.warning(f"Unknown skill '{skill_name}' or missing ability score")
        return 0
    
    # Base ability modifier
    ability_mod = get_ability_modifier(ability_scores[ability_key])
    
    # Check for proficiency
    is_proficient = skill_name.lower() in [s.lower() for s in skill_proficiencies]
    has_expertise = skill_name.lower() in [s.lower() for s in expertise_skills]
    
    prof_bonus = 0
    if is_proficient:
        prof_bonus = get_proficiency_bonus(level)
        if has_expertise:
            prof_bonus *= 2  # Expertise doubles proficiency bonus
    
    return ability_mod + prof_bonus


def calculate_spell_slots_by_level(character_class: str, level: int) -> Dict[int, int]:
    """
    Calculate spell slots for a spellcaster by level.
    This is a simplified version - a full implementation would need class-specific tables.
    
    Args:
        character_class: Character's class
        level: Character level
    
    Returns:
        Dict mapping spell level to number of slots
    """
    # Simplified spell slot calculation - in a full implementation,
    # this would use proper spell slot tables for each class
    spell_slots = {}
    
    full_casters = ["wizard", "sorcerer", "cleric", "druid", "bard"]
    half_casters = ["paladin", "ranger", "artificer"]
    third_casters = ["eldritch knight", "arcane trickster"]
    
    class_lower = character_class.lower()
    
    if class_lower in full_casters:
        # Full caster progression
        caster_level = level
    elif class_lower in half_casters:
        # Half caster progression (starts at level 2)
        caster_level = max(0, (level - 1) // 2)
    elif class_lower in third_casters:
        # Third caster progression (starts at level 3)
        caster_level = max(0, (level - 2) // 3)
    else:
        # Non-spellcaster
        return spell_slots
    
    # Simplified slot calculation (this should be replaced with proper tables)
    if caster_level >= 1:
        spell_slots[1] = min(4, max(2, caster_level))
    if caster_level >= 3:
        spell_slots[2] = min(3, max(1, caster_level - 2))
    if caster_level >= 5:
        spell_slots[3] = min(3, max(1, caster_level - 4))
    if caster_level >= 7:
        spell_slots[4] = min(3, max(1, caster_level - 6))
    if caster_level >= 9:
        spell_slots[5] = min(2, max(1, caster_level - 8))
    
    return spell_slots


def calculate_total_modifier_for_roll(
    character_data: Dict[str, Any],
    roll_type: str,
    skill: Optional[str] = None,
    ability: Optional[str] = None
) -> int:
    """
    Calculate the total modifier for a character's roll.
    
    Args:
        character_data: Character data dict with stats, proficiencies, etc.
        roll_type: Type of roll (skill_check, saving_throw, etc.)
        skill: Skill name for skill checks
        ability: Ability name for ability checks and saves
    
    Returns:
        Total modifier to add to the roll
    """
    if not character_data:
        logger.error("calculate_total_modifier_for_roll called with no character data.")
        return 0

    stats = character_data.get("stats", {})
    proficiencies = character_data.get("proficiencies", {})
    level = character_data.get("level", 1)
    prof_bonus = get_proficiency_bonus(level)
    
    base_modifier = 0
    is_proficient = False

    try:
        if roll_type == 'skill_check' and skill:
            return calculate_skill_modifier(
                stats, skill, level, proficiencies.get("skills", [])
            )
        
        elif roll_type == 'saving_throw' and ability:
            ability_key = ability.upper()
            if ability_key in stats:
                is_proficient = ability_key in proficiencies.get("saving_throws", [])
                return calculate_saving_throw_modifier(stats[ability_key], level, is_proficient)
        
        elif roll_type == 'initiative':
            return get_ability_modifier(stats.get("DEX", 10))
        
        elif roll_type == 'attack_roll':
            # Simplified: Assume DEX for attack (needs weapon data for proper calculation)
            base_modifier = get_ability_modifier(stats.get("DEX", 10))
            is_proficient = True  # Assume proficiency for now
        
        elif roll_type == 'damage_roll':
            # Simplified: Assume DEX for damage (needs weapon data)
            return get_ability_modifier(stats.get("DEX", 10))
        
        elif roll_type in ['ability_check', 'custom']:
            if ability and ability.upper() in stats:
                return get_ability_modifier(stats[ability.upper()])
        
        else:
            logger.warning(f"Unknown roll type for modifier: {roll_type}")
            return 0

        return base_modifier + (prof_bonus if is_proficient else 0)
        
    except Exception as e:
        logger.error(f"Error calculating modifier: {e}", exc_info=True)
        return 0
