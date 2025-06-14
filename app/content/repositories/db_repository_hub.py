"""Database-backed central hub for accessing all D5e repositories.

This module provides a unified interface to access all D&D 5e data repositories
using database-backed implementations.
"""

from typing import Any, Dict, List

from app.content.connection import DatabaseManager
from app.content.repositories.db_base_repository import BaseD5eDbRepository
from app.content.repositories.db_class_repository import DbClassRepository
from app.content.repositories.db_equipment_repository import DbEquipmentRepository
from app.content.repositories.db_monster_repository import DbMonsterRepository
from app.content.repositories.db_repository_factory import (
    D5eDbRepositoryFactory,
    D5eRuleData,
)
from app.content.repositories.db_spell_repository import DbSpellRepository
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
    D5eSkill,
    D5eSpell,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    D5eWeaponProperty,
)


class D5eDbRepositoryHub:
    """Database-backed central access point for all D5e repositories.

    This hub provides convenient access to all D&D 5e data through typed
    repository properties. It manages the creation and lifecycle of all
    database-backed repositories.
    """

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the repository hub.

        Args:
            database_manager: Database manager for creating connections
        """
        self._database_manager = database_manager

        # Create repository factory
        self._factory = D5eDbRepositoryFactory(database_manager)

    # Core Mechanics Repositories

    @property
    def ability_scores(self) -> BaseD5eDbRepository[D5eAbilityScore]:
        """Get the ability scores repository."""
        return self._factory.get_ability_scores()

    @property
    def alignments(self) -> BaseD5eDbRepository[D5eAlignment]:
        """Get the alignments repository."""
        return self._factory.get_alignments()

    @property
    def conditions(self) -> BaseD5eDbRepository[D5eCondition]:
        """Get the conditions repository."""
        return self._factory.get_conditions()

    @property
    def damage_types(self) -> BaseD5eDbRepository[D5eDamageType]:
        """Get the damage types repository."""
        return self._factory.get_damage_types()

    @property
    def languages(self) -> BaseD5eDbRepository[D5eLanguage]:
        """Get the languages repository."""
        return self._factory.get_languages()

    @property
    def proficiencies(self) -> BaseD5eDbRepository[D5eProficiency]:
        """Get the proficiencies repository."""
        return self._factory.get_proficiencies()

    @property
    def skills(self) -> BaseD5eDbRepository[D5eSkill]:
        """Get the skills repository."""
        return self._factory.get_skills()

    # Character Options Repositories

    @property
    def backgrounds(self) -> BaseD5eDbRepository[D5eBackground]:
        """Get the backgrounds repository."""
        return self._factory.get_backgrounds()

    @property
    def classes(self) -> DbClassRepository:
        """Get the classes repository (specialized)."""
        return self._factory.get_classes()

    @property
    def feats(self) -> BaseD5eDbRepository[D5eFeat]:
        """Get the feats repository."""
        return self._factory.get_feats()

    @property
    def races(self) -> BaseD5eDbRepository[D5eRace]:
        """Get the races repository."""
        return self._factory.get_races()

    @property
    def subclasses(self) -> BaseD5eDbRepository[D5eSubclass]:
        """Get the subclasses repository."""
        return self._factory.get_subclasses()

    @property
    def subraces(self) -> BaseD5eDbRepository[D5eSubrace]:
        """Get the subraces repository."""
        return self._factory.get_subraces()

    @property
    def traits(self) -> BaseD5eDbRepository[D5eTrait]:
        """Get the traits repository."""
        return self._factory.get_traits()

    # Character Progression Repositories

    @property
    def features(self) -> BaseD5eDbRepository[D5eFeature]:
        """Get the features repository."""
        return self._factory.get_features()

    @property
    def levels(self) -> BaseD5eDbRepository[D5eLevel]:
        """Get the levels repository."""
        return self._factory.get_levels()

    # Equipment & Items Repositories

    @property
    def equipment(self) -> DbEquipmentRepository:
        """Get the equipment repository (specialized)."""
        return self._factory.get_equipment()

    @property
    def equipment_categories(self) -> BaseD5eDbRepository[D5eEquipmentCategory]:
        """Get the equipment categories repository."""
        return self._factory.get("equipment-categories")  # type: ignore

    @property
    def magic_items(self) -> BaseD5eDbRepository[D5eMagicItem]:
        """Get the magic items repository."""
        return self._factory.get_magic_items()

    @property
    def magic_schools(self) -> BaseD5eDbRepository[D5eMagicSchool]:
        """Get the magic schools repository."""
        return self._factory.get_magic_schools()

    @property
    def weapon_properties(self) -> BaseD5eDbRepository[D5eWeaponProperty]:
        """Get the weapon properties repository."""
        return self._factory.get_weapon_properties()

    # Spells & Monsters Repositories

    @property
    def spells(self) -> DbSpellRepository:
        """Get the spells repository (specialized)."""
        return self._factory.get_spells()

    @property
    def monsters(self) -> DbMonsterRepository:
        """Get the monsters repository (specialized)."""
        return self._factory.get_monsters()

    # Rules Repositories (untyped for now)

    @property
    def rules(self) -> BaseD5eDbRepository[D5eRuleData]:
        """Get the rules repository."""
        return self._factory.get_rules()

    @property
    def rule_sections(self) -> BaseD5eDbRepository[D5eRuleData]:
        """Get the rule sections repository."""
        return self._factory.get_rule_sections()

    # Utility Methods

    def get_repository(self, category: str) -> BaseD5eDbRepository[Any]:
        """Get a repository by category name.

        Args:
            category: The data category

        Returns:
            The repository for that category

        Raises:
            KeyError: If the category is not recognized
        """
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
        repos: Dict[str, BaseD5eDbRepository[Any]] = {
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
