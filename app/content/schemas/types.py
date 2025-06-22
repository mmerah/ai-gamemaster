"""Type definitions for D&D 5e service layer.

This module contains TypedDicts, type aliases, type guards, and other type definitions
used by the D5e service layer for better type safety.
"""

from typing import Any, Dict, List, Optional, TypeAlias, TypedDict, TypeGuard, Union

from app.content.schemas import (
    APIReference,
    D5eAbilityScore,
    D5eAlignment,
    D5eBackground,
    D5eClass,
    D5eCondition,
    D5eDamageType,
    D5eEquipment,
    D5eEquipmentCategory,
    D5eFeat,
    D5eFeature,
    D5eLanguage,
    D5eLevel,
    D5eMagicItem,
    D5eMagicSchool,
    D5eMonster,
    D5eProficiency,
    D5eRace,
    D5eRule,
    D5eRuleSection,
    D5eSkill,
    D5eSpell,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    D5eWeaponProperty,
)

# Type aliases for common patterns
D5eEntity: TypeAlias = Union[
    D5eSpell,
    D5eMonster,
    D5eClass,
    D5eRace,
    D5eEquipment,
    D5eMagicItem,
    D5eBackground,
    D5eFeat,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    D5eAbilityScore,
    D5eAlignment,
    D5eCondition,
    D5eDamageType,
    D5eLanguage,
    D5eProficiency,
    D5eSkill,
    D5eWeaponProperty,
    D5eEquipmentCategory,
    D5eFeature,
    D5eLevel,
    D5eMagicSchool,
    D5eRule,
    D5eRuleSection,
]

D5eIndex: TypeAlias = str  # e.g., "fireball", "wizard"
D5eName: TypeAlias = str  # e.g., "Fireball", "Wizard"


# TypedDicts for complex return types
class HitPointInfo(TypedDict):
    """Hit point information for a class at a specific level."""

    hit_die: int
    average_hp: int
    max_hp: int


class ClassAtLevelInfo(TypedDict, total=False):
    """Complete class information at a specific level."""

    class_: Dict[str, Any]  # Class model dump - using 'class_' to avoid keyword
    level: int
    level_data: Dict[str, Any]  # Level data model dump
    features: List[Dict[str, Any]]  # List of feature model dumps
    proficiency_bonus: int
    hit_points: HitPointInfo
    spell_slots: Optional[Dict[int, int]]  # Spell level -> number of slots
    multiclass_requirements: Optional[Dict[str, Any]]


class StartingEquipmentInfo(TypedDict):
    """Starting equipment organized by source."""

    class_: List[D5eEquipment]  # Using 'class_' to avoid keyword
    background: List[D5eEquipment]


class DamageInteractionsInfo(TypedDict):
    """Damage vulnerabilities, resistances, and immunities."""

    vulnerabilities: List[str]
    resistances: List[str]
    immunities: List[str]


# Search result type
SearchResults: TypeAlias = Dict[str, List[D5eEntity]]

# Ability score mappings
AbilityScores: TypeAlias = Dict[str, int]
AbilityModifiers: TypeAlias = Dict[str, int]


# Type Guards
def is_api_reference(obj: Any) -> TypeGuard[Dict[str, Any]]:
    """Check if an object is an API reference.

    A reference has exactly three fields: index, name, and url.
    Objects with additional fields are resolved entities, not references.
    """
    if not isinstance(obj, dict):
        return False

    required_fields = {"index", "name", "url"}
    return all(field in obj for field in required_fields) and len(obj.keys()) == len(
        required_fields
    )


def is_resolved_entity(data: Any) -> TypeGuard[Dict[str, Any]]:
    """Check if data is a fully resolved entity (not just a reference).

    Resolved entities have the reference fields plus additional data.
    """
    if not isinstance(data, dict):
        return False

    required_fields = {"index", "name", "url"}
    has_required = all(field in data for field in required_fields)
    has_extra = len(data.keys()) > len(required_fields)

    return has_required and has_extra


def is_spell_reference(ref: APIReference) -> TypeGuard[APIReference]:
    """Type guard to check if reference is to a spell."""
    return ref.url.startswith("/api/spells/")


def is_monster_reference(ref: APIReference) -> TypeGuard[APIReference]:
    """Type guard to check if reference is to a monster."""
    return ref.url.startswith("/api/monsters/")


def is_class_reference(ref: APIReference) -> TypeGuard[APIReference]:
    """Type guard to check if reference is to a class."""
    return ref.url.startswith("/api/classes/")


def is_race_reference(ref: APIReference) -> TypeGuard[APIReference]:
    """Type guard to check if reference is to a race."""
    return ref.url.startswith("/api/races/")


def is_equipment_reference(ref: APIReference) -> TypeGuard[APIReference]:
    """Type guard to check if reference is to equipment."""
    return ref.url.startswith("/api/equipment/")


def is_magic_item_reference(ref: APIReference) -> TypeGuard[APIReference]:
    """Type guard to check if reference is to a magic item."""
    return ref.url.startswith("/api/magic-items/")


def narrow_entity_type(entity: D5eEntity) -> str:
    """Determine the specific type of a D5e entity.

    Returns the entity type as a string (e.g., "spell", "monster", etc.)
    """
    # Check by unique attributes
    if hasattr(entity, "casting_time") and hasattr(entity, "components"):
        return "spell"
    elif hasattr(entity, "challenge_rating") and hasattr(entity, "hit_dice"):
        return "monster"
    elif hasattr(entity, "hit_die") and hasattr(entity, "saving_throws"):
        return "class"
    elif hasattr(entity, "speed") and hasattr(entity, "ability_bonuses"):
        return "race"
    elif hasattr(entity, "cost") and hasattr(entity, "weight"):
        return "equipment"
    elif hasattr(entity, "rarity") and hasattr(entity, "variant"):
        return "magic_item"
    elif hasattr(entity, "personality_traits"):
        return "background"
    elif hasattr(entity, "prerequisites") and hasattr(entity, "desc"):
        return "feat"
    elif hasattr(entity, "ability_score") and hasattr(entity, "desc"):
        return "skill"
    elif hasattr(entity, "type") and hasattr(entity, "typical_speakers"):
        return "language"
    else:
        return "unknown"
