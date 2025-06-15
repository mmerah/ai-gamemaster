"""Central content type mappings for D&D 5e content.

This module provides a single source of truth for mapping content types
to their corresponding Pydantic models and SQLAlchemy entities.
"""

from typing import Dict, Type

from pydantic import BaseModel

from app.content.models import (
    AbilityScore,
    Alignment,
    Background,
    BaseContent,
    CharacterClass,
    Condition,
    DamageType,
    Equipment,
    EquipmentCategory,
    Feat,
    Feature,
    Language,
    Level,
    MagicItem,
    MagicSchool,
    Monster,
    Proficiency,
    Race,
    Rule,
    RuleSection,
    Skill,
    Spell,
    Subclass,
    Subrace,
    Trait,
    WeaponProperty,
)
from app.content.schemas import (
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

# Map content types to their corresponding Pydantic models
CONTENT_TYPE_TO_MODEL: Dict[str, Type[BaseModel]] = {
    "ability-scores": D5eAbilityScore,
    "alignments": D5eAlignment,
    "backgrounds": D5eBackground,
    "classes": D5eClass,
    "conditions": D5eCondition,
    "damage-types": D5eDamageType,
    "equipment": D5eEquipment,
    "equipment-categories": D5eEquipmentCategory,
    "feats": D5eFeat,
    "features": D5eFeature,
    "languages": D5eLanguage,
    "levels": D5eLevel,
    "magic-items": D5eMagicItem,
    "magic-schools": D5eMagicSchool,
    "monsters": D5eMonster,
    "proficiencies": D5eProficiency,
    "races": D5eRace,
    "rules": D5eRule,
    "rule-sections": D5eRuleSection,
    "skills": D5eSkill,
    "spells": D5eSpell,
    "subclasses": D5eSubclass,
    "subraces": D5eSubrace,
    "traits": D5eTrait,
    "weapon-properties": D5eWeaponProperty,
}

# Map content types to their SQLAlchemy entity classes
CONTENT_TYPE_TO_ENTITY: Dict[str, Type[BaseContent]] = {
    "ability-scores": AbilityScore,
    "alignments": Alignment,
    "backgrounds": Background,
    "classes": CharacterClass,
    "conditions": Condition,
    "damage-types": DamageType,
    "equipment": Equipment,
    "equipment-categories": EquipmentCategory,
    "feats": Feat,
    "features": Feature,
    "languages": Language,
    "levels": Level,
    "magic-items": MagicItem,
    "magic-schools": MagicSchool,
    "monsters": Monster,
    "proficiencies": Proficiency,
    "races": Race,
    "rules": Rule,
    "rule-sections": RuleSection,
    "skills": Skill,
    "spells": Spell,
    "subclasses": Subclass,
    "subraces": Subrace,
    "traits": Trait,
    "weapon-properties": WeaponProperty,
}


# Get all supported content types
def get_supported_content_types() -> list[str]:
    """Get a sorted list of all supported content types.

    Returns:
        List of content type identifiers
    """
    return sorted(list(CONTENT_TYPE_TO_MODEL.keys()))


# Validate that mappings are consistent
def _validate_mappings() -> None:
    """Validate that model and entity mappings have the same keys."""
    model_keys = set(CONTENT_TYPE_TO_MODEL.keys())
    entity_keys = set(CONTENT_TYPE_TO_ENTITY.keys())

    if model_keys != entity_keys:
        missing_in_entity = model_keys - entity_keys
        missing_in_model = entity_keys - model_keys

        error_parts = []
        if missing_in_entity:
            error_parts.append(f"Missing in entity mapping: {missing_in_entity}")
        if missing_in_model:
            error_parts.append(f"Missing in model mapping: {missing_in_model}")

        raise ValueError(
            f"Content type mappings are inconsistent. {' '.join(error_parts)}"
        )


# Validate on module import
_validate_mappings()
