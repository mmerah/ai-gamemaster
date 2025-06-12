"""Database-backed factory for creating D5e repositories.

This module provides a factory that generates database-backed repository instances
for all 25 D&D 5e data categories, mapping each to its appropriate database model.
"""

from typing import Any, Dict, List, Type, Union, cast

from pydantic import BaseModel, ConfigDict

from app.database.connection import DatabaseManager
from app.database.models import (
    AbilityScore,
    Alignment,
    Background,
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
from app.models.d5e import (
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
    D5eSkill,
    D5eSpell,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    D5eWeaponProperty,
)
from app.repositories.d5e.db_base_repository import BaseD5eDbRepository
from app.repositories.d5e.db_class_repository import DbClassRepository
from app.repositories.d5e.db_equipment_repository import DbEquipmentRepository
from app.repositories.d5e.db_monster_repository import DbMonsterRepository
from app.repositories.d5e.db_spell_repository import DbSpellRepository


class D5eRuleData(BaseModel):
    """Wrapper model for rule data with flexible structure."""

    model_config = ConfigDict(extra="allow")  # Allow any extra fields


# Type alias for repository types
DbRepositoryType = Union[
    BaseD5eDbRepository[D5eAbilityScore],
    BaseD5eDbRepository[D5eAlignment],
    BaseD5eDbRepository[D5eBackground],
    DbClassRepository,
    BaseD5eDbRepository[D5eCondition],
    BaseD5eDbRepository[D5eDamageType],
    DbEquipmentRepository,
    BaseD5eDbRepository[D5eEquipmentCategory],
    BaseD5eDbRepository[D5eFeat],
    BaseD5eDbRepository[D5eFeature],
    BaseD5eDbRepository[D5eLanguage],
    BaseD5eDbRepository[D5eLevel],
    BaseD5eDbRepository[D5eMagicItem],
    BaseD5eDbRepository[D5eMagicSchool],
    DbMonsterRepository,
    BaseD5eDbRepository[D5eProficiency],
    BaseD5eDbRepository[D5eRace],
    BaseD5eDbRepository[D5eSkill],
    DbSpellRepository,
    BaseD5eDbRepository[D5eSubclass],
    BaseD5eDbRepository[D5eSubrace],
    BaseD5eDbRepository[D5eTrait],
    BaseD5eDbRepository[D5eWeaponProperty],
    BaseD5eDbRepository[D5eRuleData],
]


class D5eDbRepositoryFactory:
    """Factory for creating database-backed D5e repository instances.

    This factory maps each of the 25 D5e data categories to its appropriate
    database model and creates repository instances with proper type safety.
    """

    # Mapping of categories to their Pydantic model and SQLAlchemy entity classes
    CATEGORY_MODELS: Dict[str, tuple[Type[BaseModel], Type[Any]]] = {
        # Core Mechanics (7 files)
        "ability-scores": (D5eAbilityScore, AbilityScore),
        "alignments": (D5eAlignment, Alignment),
        "conditions": (D5eCondition, Condition),
        "damage-types": (D5eDamageType, DamageType),
        "languages": (D5eLanguage, Language),
        "proficiencies": (D5eProficiency, Proficiency),
        "skills": (D5eSkill, Skill),
        # Character Options (7 files)
        "backgrounds": (D5eBackground, Background),
        "classes": (D5eClass, CharacterClass),
        "feats": (D5eFeat, Feat),
        "races": (D5eRace, Race),
        "subclasses": (D5eSubclass, Subclass),
        "subraces": (D5eSubrace, Subrace),
        "traits": (D5eTrait, Trait),
        # Character Progression (2 files)
        "features": (D5eFeature, Feature),
        "levels": (D5eLevel, Level),
        # Equipment & Items (5 files)
        "equipment": (D5eEquipment, Equipment),
        "equipment-categories": (D5eEquipmentCategory, EquipmentCategory),
        "magic-items": (D5eMagicItem, MagicItem),
        "magic-schools": (D5eMagicSchool, MagicSchool),
        "weapon-properties": (D5eWeaponProperty, WeaponProperty),
        # Spells & Monsters (2 files)
        "monsters": (D5eMonster, Monster),
        "spells": (D5eSpell, Spell),
        # Rules (2 files)
        "rules": (D5eRuleData, Rule),
        "rule-sections": (D5eRuleData, RuleSection),
    }

    # Categories that have specialized repository implementations
    SPECIALIZED_CATEGORIES = {"spells", "monsters", "equipment", "classes"}

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the factory with database manager.

        Args:
            database_manager: Database manager for creating connections
        """
        self._database_manager = database_manager
        self._repositories: Dict[str, DbRepositoryType] = {}

        # Create all repositories on initialization
        self._initialize_repositories()

    def _initialize_repositories(self) -> None:
        """Create repository instances for all categories."""
        for category, (model_class, entity_class) in self.CATEGORY_MODELS.items():
            if category in self.SPECIALIZED_CATEGORIES:
                # Create specialized repositories
                if category == "spells":
                    self._repositories[category] = DbSpellRepository(
                        self._database_manager
                    )
                elif category == "monsters":
                    self._repositories[category] = DbMonsterRepository(
                        self._database_manager
                    )
                elif category == "equipment":
                    self._repositories[category] = DbEquipmentRepository(
                        self._database_manager
                    )
                elif category == "classes":
                    self._repositories[category] = DbClassRepository(
                        self._database_manager
                    )
                else:
                    # Should never happen, but handle it
                    self._repositories[category] = cast(
                        DbRepositoryType,
                        BaseD5eDbRepository(
                            model_class=model_class,
                            entity_class=entity_class,
                            database_manager=self._database_manager,
                        ),
                    )
            else:
                # Create generic repository with specific model type
                self._repositories[category] = cast(
                    DbRepositoryType,
                    BaseD5eDbRepository(
                        model_class=model_class,
                        entity_class=entity_class,
                        database_manager=self._database_manager,
                    ),
                )

    def get(self, category: str) -> DbRepositoryType:
        """Get a repository by category name.

        Args:
            category: The data category (e.g., 'spells', 'classes')

        Returns:
            The repository instance

        Raises:
            KeyError: If the category is not recognized
        """
        if category not in self._repositories:
            raise KeyError(
                f"Unknown category: {category}. Valid categories: {list(self._repositories.keys())}"
            )

        return self._repositories[category]

    def get_ability_scores(self) -> BaseD5eDbRepository[D5eAbilityScore]:
        """Get the ability scores repository."""
        return cast(
            BaseD5eDbRepository[D5eAbilityScore], self._repositories["ability-scores"]
        )

    def get_alignments(self) -> BaseD5eDbRepository[D5eAlignment]:
        """Get the alignments repository."""
        return cast(BaseD5eDbRepository[D5eAlignment], self._repositories["alignments"])

    def get_backgrounds(self) -> BaseD5eDbRepository[D5eBackground]:
        """Get the backgrounds repository."""
        return cast(
            BaseD5eDbRepository[D5eBackground], self._repositories["backgrounds"]
        )

    def get_classes(self) -> DbClassRepository:
        """Get the classes repository (specialized)."""
        return cast(DbClassRepository, self._repositories["classes"])

    def get_conditions(self) -> BaseD5eDbRepository[D5eCondition]:
        """Get the conditions repository."""
        return cast(BaseD5eDbRepository[D5eCondition], self._repositories["conditions"])

    def get_damage_types(self) -> BaseD5eDbRepository[D5eDamageType]:
        """Get the damage types repository."""
        return cast(
            BaseD5eDbRepository[D5eDamageType], self._repositories["damage-types"]
        )

    def get_equipment(self) -> DbEquipmentRepository:
        """Get the equipment repository (specialized)."""
        return cast(DbEquipmentRepository, self._repositories["equipment"])

    def get_feats(self) -> BaseD5eDbRepository[D5eFeat]:
        """Get the feats repository."""
        return cast(BaseD5eDbRepository[D5eFeat], self._repositories["feats"])

    def get_features(self) -> BaseD5eDbRepository[D5eFeature]:
        """Get the features repository."""
        return cast(BaseD5eDbRepository[D5eFeature], self._repositories["features"])

    def get_languages(self) -> BaseD5eDbRepository[D5eLanguage]:
        """Get the languages repository."""
        return cast(BaseD5eDbRepository[D5eLanguage], self._repositories["languages"])

    def get_levels(self) -> BaseD5eDbRepository[D5eLevel]:
        """Get the levels repository."""
        return cast(BaseD5eDbRepository[D5eLevel], self._repositories["levels"])

    def get_magic_items(self) -> BaseD5eDbRepository[D5eMagicItem]:
        """Get the magic items repository."""
        return cast(
            BaseD5eDbRepository[D5eMagicItem], self._repositories["magic-items"]
        )

    def get_magic_schools(self) -> BaseD5eDbRepository[D5eMagicSchool]:
        """Get the magic schools repository."""
        return cast(
            BaseD5eDbRepository[D5eMagicSchool], self._repositories["magic-schools"]
        )

    def get_monsters(self) -> DbMonsterRepository:
        """Get the monsters repository (specialized)."""
        return cast(DbMonsterRepository, self._repositories["monsters"])

    def get_proficiencies(self) -> BaseD5eDbRepository[D5eProficiency]:
        """Get the proficiencies repository."""
        return cast(
            BaseD5eDbRepository[D5eProficiency], self._repositories["proficiencies"]
        )

    def get_races(self) -> BaseD5eDbRepository[D5eRace]:
        """Get the races repository."""
        return cast(BaseD5eDbRepository[D5eRace], self._repositories["races"])

    def get_skills(self) -> BaseD5eDbRepository[D5eSkill]:
        """Get the skills repository."""
        return cast(BaseD5eDbRepository[D5eSkill], self._repositories["skills"])

    def get_spells(self) -> DbSpellRepository:
        """Get the spells repository (specialized)."""
        return cast(DbSpellRepository, self._repositories["spells"])

    def get_subclasses(self) -> BaseD5eDbRepository[D5eSubclass]:
        """Get the subclasses repository."""
        return cast(BaseD5eDbRepository[D5eSubclass], self._repositories["subclasses"])

    def get_subraces(self) -> BaseD5eDbRepository[D5eSubrace]:
        """Get the subraces repository."""
        return cast(BaseD5eDbRepository[D5eSubrace], self._repositories["subraces"])

    def get_traits(self) -> BaseD5eDbRepository[D5eTrait]:
        """Get the traits repository."""
        return cast(BaseD5eDbRepository[D5eTrait], self._repositories["traits"])

    def get_weapon_properties(self) -> BaseD5eDbRepository[D5eWeaponProperty]:
        """Get the weapon properties repository."""
        return cast(
            BaseD5eDbRepository[D5eWeaponProperty],
            self._repositories["weapon-properties"],
        )

    def get_rules(self) -> BaseD5eDbRepository[D5eRuleData]:
        """Get the rules repository."""
        return cast(BaseD5eDbRepository[D5eRuleData], self._repositories["rules"])

    def get_rule_sections(self) -> BaseD5eDbRepository[D5eRuleData]:
        """Get the rule sections repository."""
        return cast(
            BaseD5eDbRepository[D5eRuleData], self._repositories["rule-sections"]
        )

    def get_all_categories(self) -> List[str]:
        """Get a list of all available categories.

        Returns:
            List of category names
        """
        return list(self._repositories.keys())
