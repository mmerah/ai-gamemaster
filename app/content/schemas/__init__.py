"""D&D 5e data models.

This module contains Pydantic models for all D&D 5e data types from the 5e-database.
The models are organized by category to match the structure of the source data.
"""

from app.content.schemas.base import (
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
from app.content.schemas.character import (
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
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentPackWithStats,
    ContentUploadResult,
    D5eContentPack,
)
from app.content.schemas.content_types import ContentTypeInfo
from app.content.schemas.equipment import (
    ArmorClass,
    D5eEquipment,
    D5eEquipmentCategory,
    D5eMagicItem,
    D5eMagicSchool,
    D5eWeaponProperty,
    EquipmentRange,
)
from app.content.schemas.mechanics import (
    D5eAbilityScore,
    D5eAlignment,
    D5eCondition,
    D5eDamageType,
    D5eLanguage,
    D5eProficiency,
    D5eRule,
    D5eRuleSection,
    D5eSkill,
)
from app.content.schemas.progression import (
    D5eClassLevel,
    D5eFeature,
    D5eLevel,
    SpellSlotInfo,
)
from app.content.schemas.spells_monsters import (
    D5eMonster,
    D5eSpell,
    MonsterAction,
    MonsterArmorClass,
    MonsterProficiency,
    MonsterSpeed,
    SpecialAbility,
)
from app.content.schemas.types import (
    AbilityModifiers,
    AbilityScores,
    ClassAtLevelInfo,
    D5eEntity,
    D5eIndex,
    D5eName,
    DamageInteractionsInfo,
    HitPointInfo,
    SearchResults,
    StartingEquipmentInfo,
    is_api_reference,
    is_class_reference,
    is_equipment_reference,
    is_magic_item_reference,
    is_monster_reference,
    is_race_reference,
    is_resolved_entity,
    is_spell_reference,
    narrow_entity_type,
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
    # Content Pack models
    "ContentPackCreate",
    "ContentPackUpdate",
    "ContentPackWithStats",
    "ContentUploadResult",
    "D5eContentPack",
    # Content Type models
    "ContentTypeInfo",
    # Mechanics models
    "D5eAbilityScore",
    "D5eAlignment",
    "D5eCondition",
    "D5eDamageType",
    "D5eLanguage",
    "D5eProficiency",
    "D5eRule",
    "D5eRuleSection",
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
    "SpellSlotInfo",
    # Spells & Monsters
    "D5eMonster",
    "D5eSpell",
    "MonsterAction",
    "MonsterArmorClass",
    "MonsterProficiency",
    "MonsterSpeed",
    "SpecialAbility",
    # Type definitions
    "AbilityModifiers",
    "AbilityScores",
    "ClassAtLevelInfo",
    "D5eEntity",
    "D5eIndex",
    "D5eName",
    "DamageInteractionsInfo",
    "HitPointInfo",
    "SearchResults",
    "StartingEquipmentInfo",
    # Type guards
    "is_api_reference",
    "is_class_reference",
    "is_equipment_reference",
    "is_magic_item_reference",
    "is_monster_reference",
    "is_race_reference",
    "is_resolved_entity",
    "is_spell_reference",
    "narrow_entity_type",
]
