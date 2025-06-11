"""Factory for creating D5e repositories.

This module provides a factory that generates repository instances for all 25
D&D 5e data categories, mapping each to its appropriate Pydantic model.
"""

from typing import Any, Dict, List, Type, Union, cast

from pydantic import BaseModel, ConfigDict

from app.models.d5e import (
    D5eAbilityScore,
    D5eAlignment,
    D5eBackground,
    D5eClass,
    D5eClassLevel,
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
from app.repositories.d5e.base_repository import BaseD5eRepository
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import D5eReferenceResolver


class D5eRuleData(BaseModel):
    """Wrapper model for rule data with flexible structure."""

    model_config = ConfigDict(extra="allow")  # Allow any extra fields


# Type alias for repository types
RepositoryType = Union[
    BaseD5eRepository[D5eAbilityScore],
    BaseD5eRepository[D5eAlignment],
    BaseD5eRepository[D5eBackground],
    BaseD5eRepository[D5eClass],
    BaseD5eRepository[D5eClassLevel],
    BaseD5eRepository[D5eCondition],
    BaseD5eRepository[D5eDamageType],
    BaseD5eRepository[D5eEquipment],
    BaseD5eRepository[D5eEquipmentCategory],
    BaseD5eRepository[D5eFeat],
    BaseD5eRepository[D5eFeature],
    BaseD5eRepository[D5eLanguage],
    BaseD5eRepository[D5eLevel],
    BaseD5eRepository[D5eMagicItem],
    BaseD5eRepository[D5eMagicSchool],
    BaseD5eRepository[D5eMonster],
    BaseD5eRepository[D5eProficiency],
    BaseD5eRepository[D5eRace],
    BaseD5eRepository[D5eSkill],
    BaseD5eRepository[D5eSpell],
    BaseD5eRepository[D5eSubclass],
    BaseD5eRepository[D5eSubrace],
    BaseD5eRepository[D5eTrait],
    BaseD5eRepository[D5eWeaponProperty],
    # Rules repositories
    BaseD5eRepository[D5eRuleData],
]


class D5eRepositoryFactory:
    """Factory for creating D5e repository instances.

    This factory maps each of the 25 D5e data categories to its appropriate
    Pydantic model and creates repository instances with proper type safety.
    """

    # Mapping of categories to their Pydantic model classes
    CATEGORY_MODELS: Dict[str, Type[BaseModel]] = {
        # Core Mechanics (7 files)
        "ability-scores": D5eAbilityScore,
        "alignments": D5eAlignment,
        "conditions": D5eCondition,
        "damage-types": D5eDamageType,
        "languages": D5eLanguage,
        "proficiencies": D5eProficiency,
        "skills": D5eSkill,
        # Character Options (7 files)
        "backgrounds": D5eBackground,
        "classes": D5eClass,
        "feats": D5eFeat,
        "races": D5eRace,
        "subclasses": D5eSubclass,
        "subraces": D5eSubrace,
        "traits": D5eTrait,
        # Character Progression (2 files)
        "features": D5eFeature,
        "levels": D5eLevel,
        # Equipment & Items (5 files)
        "equipment": D5eEquipment,
        "equipment-categories": D5eEquipmentCategory,
        "magic-items": D5eMagicItem,
        "magic-schools": D5eMagicSchool,
        "weapon-properties": D5eWeaponProperty,
        # Spells & Monsters (2 files)
        "monsters": D5eMonster,
        "spells": D5eSpell,
        # Rules (2 files) - using Dict for now as they have variable structure
        # "rules": Dict[str, Any],
        # "rule-sections": Dict[str, Any],
    }

    def __init__(
        self,
        index_builder: D5eIndexBuilder,
        reference_resolver: D5eReferenceResolver,
    ) -> None:
        """Initialize the factory with dependencies.

        Args:
            index_builder: Index builder for fast lookups
            reference_resolver: Resolver for handling references
        """
        self._index_builder = index_builder
        self._reference_resolver = reference_resolver
        self._repositories: Dict[str, RepositoryType] = {}

        # Create all repositories on initialization
        self._initialize_repositories()

    def _initialize_repositories(self) -> None:
        """Create repository instances for all categories."""
        for category, model_class in self.CATEGORY_MODELS.items():
            # Create repository with specific model type
            repo = BaseD5eRepository(
                category=category,
                model_class=model_class,
                index_builder=self._index_builder,
                reference_resolver=self._reference_resolver,
            )
            self._repositories[category] = cast(RepositoryType, repo)

        # Add rules repositories with D5eRuleData type
        # These have variable structure so we use a flexible model
        rules_categories = ["rules", "rule-sections"]
        for category in rules_categories:
            self._repositories[category] = BaseD5eRepository[D5eRuleData](
                category=category,
                model_class=D5eRuleData,
                index_builder=self._index_builder,
                reference_resolver=self._reference_resolver,
            )

    def get(self, category: str) -> RepositoryType:
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

    def get_ability_scores(self) -> BaseD5eRepository[D5eAbilityScore]:
        """Get the ability scores repository."""
        return cast(
            BaseD5eRepository[D5eAbilityScore], self._repositories["ability-scores"]
        )

    def get_alignments(self) -> BaseD5eRepository[D5eAlignment]:
        """Get the alignments repository."""
        return cast(BaseD5eRepository[D5eAlignment], self._repositories["alignments"])

    def get_backgrounds(self) -> BaseD5eRepository[D5eBackground]:
        """Get the backgrounds repository."""
        return cast(BaseD5eRepository[D5eBackground], self._repositories["backgrounds"])

    def get_classes(self) -> BaseD5eRepository[D5eClass]:
        """Get the classes repository."""
        return cast(BaseD5eRepository[D5eClass], self._repositories["classes"])

    def get_conditions(self) -> BaseD5eRepository[D5eCondition]:
        """Get the conditions repository."""
        return cast(BaseD5eRepository[D5eCondition], self._repositories["conditions"])

    def get_damage_types(self) -> BaseD5eRepository[D5eDamageType]:
        """Get the damage types repository."""
        return cast(
            BaseD5eRepository[D5eDamageType], self._repositories["damage-types"]
        )

    def get_equipment(self) -> BaseD5eRepository[D5eEquipment]:
        """Get the equipment repository."""
        return cast(BaseD5eRepository[D5eEquipment], self._repositories["equipment"])

    def get_feats(self) -> BaseD5eRepository[D5eFeat]:
        """Get the feats repository."""
        return cast(BaseD5eRepository[D5eFeat], self._repositories["feats"])

    def get_features(self) -> BaseD5eRepository[D5eFeature]:
        """Get the features repository."""
        return cast(BaseD5eRepository[D5eFeature], self._repositories["features"])

    def get_languages(self) -> BaseD5eRepository[D5eLanguage]:
        """Get the languages repository."""
        return cast(BaseD5eRepository[D5eLanguage], self._repositories["languages"])

    def get_levels(self) -> BaseD5eRepository[D5eLevel]:
        """Get the levels repository."""
        return cast(BaseD5eRepository[D5eLevel], self._repositories["levels"])

    def get_magic_items(self) -> BaseD5eRepository[D5eMagicItem]:
        """Get the magic items repository."""
        return cast(BaseD5eRepository[D5eMagicItem], self._repositories["magic-items"])

    def get_magic_schools(self) -> BaseD5eRepository[D5eMagicSchool]:
        """Get the magic schools repository."""
        return cast(
            BaseD5eRepository[D5eMagicSchool], self._repositories["magic-schools"]
        )

    def get_monsters(self) -> BaseD5eRepository[D5eMonster]:
        """Get the monsters repository."""
        return cast(BaseD5eRepository[D5eMonster], self._repositories["monsters"])

    def get_proficiencies(self) -> BaseD5eRepository[D5eProficiency]:
        """Get the proficiencies repository."""
        return cast(
            BaseD5eRepository[D5eProficiency], self._repositories["proficiencies"]
        )

    def get_races(self) -> BaseD5eRepository[D5eRace]:
        """Get the races repository."""
        return cast(BaseD5eRepository[D5eRace], self._repositories["races"])

    def get_skills(self) -> BaseD5eRepository[D5eSkill]:
        """Get the skills repository."""
        return cast(BaseD5eRepository[D5eSkill], self._repositories["skills"])

    def get_spells(self) -> BaseD5eRepository[D5eSpell]:
        """Get the spells repository."""
        return cast(BaseD5eRepository[D5eSpell], self._repositories["spells"])

    def get_subclasses(self) -> BaseD5eRepository[D5eSubclass]:
        """Get the subclasses repository."""
        return cast(BaseD5eRepository[D5eSubclass], self._repositories["subclasses"])

    def get_subraces(self) -> BaseD5eRepository[D5eSubrace]:
        """Get the subraces repository."""
        return cast(BaseD5eRepository[D5eSubrace], self._repositories["subraces"])

    def get_traits(self) -> BaseD5eRepository[D5eTrait]:
        """Get the traits repository."""
        return cast(BaseD5eRepository[D5eTrait], self._repositories["traits"])

    def get_weapon_properties(self) -> BaseD5eRepository[D5eWeaponProperty]:
        """Get the weapon properties repository."""
        return cast(
            BaseD5eRepository[D5eWeaponProperty],
            self._repositories["weapon-properties"],
        )

    def get_rules(self) -> BaseD5eRepository[D5eRuleData]:
        """Get the rules repository."""
        return cast(BaseD5eRepository[D5eRuleData], self._repositories["rules"])

    def get_rule_sections(self) -> BaseD5eRepository[D5eRuleData]:
        """Get the rule sections repository."""
        return cast(BaseD5eRepository[D5eRuleData], self._repositories["rule-sections"])

    def get_all_categories(self) -> List[str]:
        """Get a list of all available categories.

        Returns:
            List of category names
        """
        return list(self._repositories.keys())
