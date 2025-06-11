"""Central hub for accessing all D5e repositories.

This module provides a unified interface to access all D&D 5e data repositories,
including both generic and specialized repositories for different data types.
"""

from typing import Any, Dict, List, Optional

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
from app.repositories.d5e.base_repository import BaseD5eRepository
from app.repositories.d5e.class_repository import ClassRepository
from app.repositories.d5e.equipment_repository import EquipmentRepository
from app.repositories.d5e.monster_repository import MonsterRepository
from app.repositories.d5e.repository_factory import D5eRepositoryFactory, D5eRuleData
from app.repositories.d5e.spell_repository import SpellRepository
from app.services.d5e.data_loader import D5eDataLoader
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import D5eReferenceResolver


class D5eRepositoryHub:
    """Central access point for all D5e repositories.

    This hub provides convenient access to all D&D 5e data through typed
    repository properties. It manages the creation and lifecycle of all
    repositories and their dependencies.
    """

    def __init__(
        self,
        data_loader: Optional[D5eDataLoader] = None,
        reference_resolver: Optional[D5eReferenceResolver] = None,
        index_builder: Optional[D5eIndexBuilder] = None,
    ) -> None:
        """Initialize the repository hub.

        Args:
            data_loader: Optional data loader instance
            reference_resolver: Optional reference resolver instance
            index_builder: Optional index builder instance
        """
        # Create dependencies if not provided
        self._data_loader = data_loader or D5eDataLoader()
        self._reference_resolver = reference_resolver or D5eReferenceResolver(
            self._data_loader
        )
        self._index_builder = index_builder or D5eIndexBuilder(self._data_loader)

        # Create repository factory
        self._factory = D5eRepositoryFactory(
            index_builder=self._index_builder,
            reference_resolver=self._reference_resolver,
        )

        # Create specialized repositories
        self._spell_repository = SpellRepository(
            index_builder=self._index_builder,
            reference_resolver=self._reference_resolver,
        )

        self._monster_repository = MonsterRepository(
            index_builder=self._index_builder,
            reference_resolver=self._reference_resolver,
        )

        self._class_repository = ClassRepository(
            index_builder=self._index_builder,
            reference_resolver=self._reference_resolver,
        )

        self._equipment_repository = EquipmentRepository(
            index_builder=self._index_builder,
            reference_resolver=self._reference_resolver,
        )

    # Core Mechanics Repositories

    @property
    def ability_scores(self) -> BaseD5eRepository[D5eAbilityScore]:
        """Get the ability scores repository."""
        return self._factory.get_ability_scores()

    @property
    def alignments(self) -> BaseD5eRepository[D5eAlignment]:
        """Get the alignments repository."""
        return self._factory.get_alignments()

    @property
    def conditions(self) -> BaseD5eRepository[D5eCondition]:
        """Get the conditions repository."""
        return self._factory.get_conditions()

    @property
    def damage_types(self) -> BaseD5eRepository[D5eDamageType]:
        """Get the damage types repository."""
        return self._factory.get_damage_types()

    @property
    def languages(self) -> BaseD5eRepository[D5eLanguage]:
        """Get the languages repository."""
        return self._factory.get_languages()

    @property
    def proficiencies(self) -> BaseD5eRepository[D5eProficiency]:
        """Get the proficiencies repository."""
        return self._factory.get_proficiencies()

    @property
    def skills(self) -> BaseD5eRepository[D5eSkill]:
        """Get the skills repository."""
        return self._factory.get_skills()

    # Character Options Repositories

    @property
    def backgrounds(self) -> BaseD5eRepository[D5eBackground]:
        """Get the backgrounds repository."""
        return self._factory.get_backgrounds()

    @property
    def classes(self) -> ClassRepository:
        """Get the classes repository (specialized)."""
        return self._class_repository

    @property
    def feats(self) -> BaseD5eRepository[D5eFeat]:
        """Get the feats repository."""
        return self._factory.get_feats()

    @property
    def races(self) -> BaseD5eRepository[D5eRace]:
        """Get the races repository."""
        return self._factory.get_races()

    @property
    def subclasses(self) -> BaseD5eRepository[D5eSubclass]:
        """Get the subclasses repository."""
        return self._factory.get_subclasses()

    @property
    def subraces(self) -> BaseD5eRepository[D5eSubrace]:
        """Get the subraces repository."""
        return self._factory.get_subraces()

    @property
    def traits(self) -> BaseD5eRepository[D5eTrait]:
        """Get the traits repository."""
        return self._factory.get_traits()

    # Character Progression Repositories

    @property
    def features(self) -> BaseD5eRepository[D5eFeature]:
        """Get the features repository."""
        return self._factory.get_features()

    @property
    def levels(self) -> BaseD5eRepository[D5eLevel]:
        """Get the levels repository."""
        return self._factory.get_levels()

    # Equipment & Items Repositories

    @property
    def equipment(self) -> EquipmentRepository:
        """Get the equipment repository (specialized)."""
        return self._equipment_repository

    @property
    def equipment_categories(self) -> BaseD5eRepository[D5eEquipmentCategory]:
        """Get the equipment categories repository."""
        return self._factory.get("equipment-categories")  # type: ignore

    @property
    def magic_items(self) -> BaseD5eRepository[D5eMagicItem]:
        """Get the magic items repository."""
        return self._factory.get_magic_items()

    @property
    def magic_schools(self) -> BaseD5eRepository[D5eMagicSchool]:
        """Get the magic schools repository."""
        return self._factory.get_magic_schools()

    @property
    def weapon_properties(self) -> BaseD5eRepository[D5eWeaponProperty]:
        """Get the weapon properties repository."""
        return self._factory.get_weapon_properties()

    # Spells & Monsters Repositories

    @property
    def spells(self) -> SpellRepository:
        """Get the spells repository (specialized)."""
        return self._spell_repository

    @property
    def monsters(self) -> MonsterRepository:
        """Get the monsters repository (specialized)."""
        return self._monster_repository

    # Rules Repositories (untyped for now)

    @property
    def rules(self) -> BaseD5eRepository[D5eRuleData]:
        """Get the rules repository."""
        return self._factory.get_rules()

    @property
    def rule_sections(self) -> BaseD5eRepository[D5eRuleData]:
        """Get the rule sections repository."""
        return self._factory.get_rule_sections()

    # Utility Methods

    def get_repository(self, category: str) -> BaseD5eRepository[Any]:
        """Get a repository by category name.

        Args:
            category: The data category

        Returns:
            The repository for that category

        Raises:
            KeyError: If the category is not recognized
        """
        # Check for specialized repositories first
        specialized_map: Dict[str, BaseD5eRepository[Any]] = {
            "spells": self._spell_repository,
            "monsters": self._monster_repository,
            "classes": self._class_repository,
            "equipment": self._equipment_repository,
        }

        if category in specialized_map:
            return specialized_map[category]

        # Fall back to factory
        return self._factory.get(category)

    def search_all(self, query: str) -> Dict[str, List[Any]]:
        """Search across all repositories.

        Args:
            query: The search query

        Returns:
            Dictionary mapping category names to matching results
        """
        results: Dict[str, List[Any]] = {}

        # Search all categories
        categories = [
            "ability-scores",
            "alignments",
            "backgrounds",
            "classes",
            "conditions",
            "damage-types",
            "equipment",
            "equipment-categories",
            "feats",
            "features",
            "languages",
            "levels",
            "magic-items",
            "magic-schools",
            "monsters",
            "proficiencies",
            "races",
            "skills",
            "spells",
            "subclasses",
            "subraces",
            "traits",
            "weapon-properties",
        ]

        for category in categories:
            try:
                repo = self.get_repository(category)
                matches = repo.search(query)
                if matches:
                    results[category] = matches
            except Exception:
                # Skip categories that fail
                continue

        return results

    def get_statistics(self) -> Dict[str, int]:
        """Get count statistics for all data categories.

        Returns:
            Dictionary mapping category names to entity counts
        """
        stats: Dict[str, int] = {}

        # All repositories
        repos: Dict[str, BaseD5eRepository[Any]] = {
            "ability-scores": self.ability_scores,
            "alignments": self.alignments,
            "backgrounds": self.backgrounds,
            "classes": self.classes,
            "conditions": self.conditions,
            "damage-types": self.damage_types,
            "equipment": self.equipment,
            "feats": self.feats,
            "features": self.features,
            "languages": self.languages,
            "levels": self.levels,
            "magic-items": self.magic_items,
            "magic-schools": self.magic_schools,
            "monsters": self.monsters,
            "proficiencies": self.proficiencies,
            "races": self.races,
            "skills": self.skills,
            "spells": self.spells,
            "subclasses": self.subclasses,
            "subraces": self.subraces,
            "traits": self.traits,
            "weapon-properties": self.weapon_properties,
        }

        for name, repo in repos.items():
            try:
                stats[name] = repo.count()
            except Exception:
                stats[name] = 0

        return stats

    def clear_caches(self) -> None:
        """Clear all caches in the data access layer."""
        self._data_loader.clear_cache()
        self._reference_resolver.clear_cache()
        # Index builder doesn't have a cache to clear
