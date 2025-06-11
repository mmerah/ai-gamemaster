"""D&D 5e data models.

This module contains Pydantic models for all D&D 5e data types from the 5e-database.
The models are organized by category to match the structure of the source data.
"""

from app.models.d5e.base import (
    DC,
    APIReference,
    Choice,
    ChoiceOption,
    Cost,
    Damage,
    DamageAtLevel,
    OptionSet,
    Usage,
)
from app.models.d5e.character import (
    D5eBackground,
    D5eClass,
    D5eFeat,
    D5eRace,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    MultiClassing,
    MultiClassingPrereq,
    MultiClassingProficiency,
    Spellcasting,
    SpellcastingInfo,
)
from app.models.d5e.equipment import (
    ArmorClass,
    D5eEquipment,
    D5eEquipmentCategory,
    D5eMagicItem,
    D5eMagicSchool,
    D5eWeaponProperty,
    EquipmentRange,
)
from app.models.d5e.mechanics import (
    D5eAbilityScore,
    D5eAlignment,
    D5eCondition,
    D5eDamageType,
    D5eLanguage,
    D5eProficiency,
    D5eSkill,
)
from app.models.d5e.progression import D5eClassLevel, D5eFeature, D5eLevel
from app.models.d5e.spells_monsters import (
    D5eMonster,
    D5eSpell,
    MonsterAction,
    MonsterArmorClass,
    MonsterProficiency,
    MonsterSpeed,
    SpecialAbility,
)

__all__ = [
    # Base models
    "APIReference",
    "Choice",
    "ChoiceOption",
    "Cost",
    "DC",
    "Damage",
    "DamageAtLevel",
    "OptionSet",
    "Usage",
    # Mechanics models
    "D5eAbilityScore",
    "D5eAlignment",
    "D5eCondition",
    "D5eDamageType",
    "D5eLanguage",
    "D5eProficiency",
    "D5eSkill",
    # Character models
    "D5eBackground",
    "D5eClass",
    "D5eFeat",
    "D5eRace",
    "D5eSubclass",
    "D5eSubrace",
    "D5eTrait",
    "MultiClassing",
    "MultiClassingPrereq",
    "MultiClassingProficiency",
    "Spellcasting",
    "SpellcastingInfo",
    # Equipment models
    "ArmorClass",
    "D5eEquipment",
    "D5eEquipmentCategory",
    "D5eMagicItem",
    "D5eMagicSchool",
    "D5eWeaponProperty",
    "EquipmentRange",
    # Progression models
    "D5eClassLevel",
    "D5eFeature",
    "D5eLevel",
    # Spells & Monsters
    "D5eMonster",
    "D5eSpell",
    "MonsterAction",
    "MonsterArmorClass",
    "MonsterProficiency",
    "MonsterSpeed",
    "SpecialAbility",
]
