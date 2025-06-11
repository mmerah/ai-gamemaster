"""Specialized repository for D&D 5e classes.

This module provides advanced class-specific queries including level progression,
multiclassing requirements, and feature lookups.
"""

from typing import Any, Dict, List, Optional, cast

from app.models.d5e import D5eClass, D5eFeature, D5eLevel
from app.repositories.d5e.base_repository import BaseD5eRepository
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import D5eReferenceResolver


class ClassRepository(BaseD5eRepository[D5eClass]):
    """Repository for accessing class data with specialized queries."""

    def __init__(
        self,
        index_builder: D5eIndexBuilder,
        reference_resolver: D5eReferenceResolver,
    ) -> None:
        """Initialize the class repository."""
        super().__init__(
            category="classes",
            model_class=D5eClass,
            index_builder=index_builder,
            reference_resolver=reference_resolver,
        )

        # Also create repositories for features and levels
        self._feature_repo = BaseD5eRepository(
            category="features",
            model_class=D5eFeature,
            index_builder=index_builder,
            reference_resolver=reference_resolver,
        )

        self._level_repo = BaseD5eRepository(
            category="levels",
            model_class=D5eLevel,
            index_builder=index_builder,
            reference_resolver=reference_resolver,
        )

    def get_spellcasting_classes(
        self, resolve_references: bool = False
    ) -> List[D5eClass]:
        """Get all classes that have spellcasting abilities.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of spellcasting classes
        """
        all_classes = self.list_all_with_options(resolve_references=resolve_references)
        return [cls for cls in all_classes if cls.spellcasting is not None]

    def get_by_hit_die(
        self, hit_die: int, resolve_references: bool = False
    ) -> List[D5eClass]:
        """Get classes with a specific hit die size.

        Args:
            hit_die: The hit die size (e.g., 6, 8, 10, 12)
            resolve_references: Whether to resolve references

        Returns:
            List of classes with that hit die
        """
        return self.filter_by(hit_die=hit_die)

    def get_class_features(
        self, class_index: str, level: Optional[int] = None
    ) -> List[D5eFeature]:
        """Get all features for a class, optionally filtered by level.

        Args:
            class_index: The class index (e.g., 'wizard', 'fighter')
            level: Optional level filter

        Returns:
            List of class features
        """
        all_features = self._feature_repo.list_all()

        # Filter by class
        class_features = [
            feature for feature in all_features if feature.class_.index == class_index
        ]

        # Filter by level if specified
        if level is not None:
            class_features = [f for f in class_features if f.level == level]

        # Sort by level
        return sorted(class_features, key=lambda f: f.level)

    def get_subclass_features(
        self, subclass_index: str, level: Optional[int] = None
    ) -> List[D5eFeature]:
        """Get all features for a subclass.

        Args:
            subclass_index: The subclass index
            level: Optional level filter

        Returns:
            List of subclass features
        """
        all_features = self._feature_repo.list_all()

        # Filter by subclass
        subclass_features = [
            feature
            for feature in all_features
            if feature.subclass and feature.subclass.index == subclass_index
        ]

        # Filter by level if specified
        if level is not None:
            subclass_features = [f for f in subclass_features if f.level == level]

        # Sort by level
        return sorted(subclass_features, key=lambda f: f.level)

    def get_level_progression(self, class_index: str) -> List[D5eLevel]:
        """Get the complete level progression for a class.

        Args:
            class_index: The class index

        Returns:
            List of level data from 1-20
        """
        all_levels = self._level_repo.list_all()

        # Filter by class and sort by level
        class_levels = [
            level for level in all_levels if level.class_.index == class_index
        ]

        return sorted(class_levels, key=lambda lvl: lvl.level)

    def get_level_data(self, class_index: str, level: int) -> Optional[D5eLevel]:
        """Get level-specific data for a class.

        Args:
            class_index: The class index
            level: The character level (1-20)

        Returns:
            Level data if found
        """
        # Level indices are formatted as "{class}-{level}"
        level_index = f"{class_index}-{level}"
        return self._level_repo.get_by_index_with_options(
            level_index, resolve_references=True
        )

    def get_proficiency_bonus(self, level: int) -> int:
        """Get the proficiency bonus for a character level.

        Args:
            level: The character level (1-20)

        Returns:
            The proficiency bonus
        """
        # Proficiency bonus is the same for all classes
        if level < 1:
            return 2
        elif level <= 4:
            return 2
        elif level <= 8:
            return 3
        elif level <= 12:
            return 4
        elif level <= 16:
            return 5
        else:
            return 6

    def get_multiclass_requirements(self, class_index: str) -> Optional[Dict[str, Any]]:
        """Get multiclassing requirements for a class.

        Args:
            class_index: The class index

        Returns:
            Multiclassing requirements if the class supports it
        """
        cls = self.get_by_index_with_options(class_index, resolve_references=False)
        if not cls or not cls.multi_classing:
            return None

        requirements: Dict[str, Any] = {}

        # Prerequisites
        if cls.multi_classing.prerequisites:
            requirements["prerequisites"] = [
                {"ability": prereq.ability_score.index, "minimum": prereq.minimum_score}
                for prereq in cls.multi_classing.prerequisites
            ]

        # Proficiencies gained
        if cls.multi_classing.proficiencies:
            requirements["proficiencies"] = [
                p.index for p in cls.multi_classing.proficiencies
            ]

        return requirements

    def get_spell_slots(self, class_index: str, level: int) -> Optional[Dict[int, int]]:
        """Get spell slots for a spellcasting class at a specific level.

        Args:
            class_index: The class index
            level: The character level

        Returns:
            Dictionary mapping spell level to number of slots
        """
        level_data = self.get_level_data(class_index, level)
        if not level_data or not level_data.spellcasting:
            return None

        spell_slots: Dict[int, int] = {}
        spellcasting = level_data.spellcasting

        # Extract spell slots from the spellcasting data
        for i in range(1, 10):  # Spell levels 1-9
            slot_attr = f"spell_slots_level_{i}"
            if hasattr(spellcasting, slot_attr):
                slots = getattr(spellcasting, slot_attr)
                if slots and slots > 0:
                    spell_slots[i] = slots

        return spell_slots if spell_slots else None

    def get_classes_with_subclass_at_level(self, level: int) -> List[D5eClass]:
        """Get classes that choose their subclass at a specific level.

        Args:
            level: The level to check

        Returns:
            List of classes that choose subclass at that level
        """
        # Most classes choose at level 1-3, but this would need metadata
        # For now, return a hardcoded mapping
        subclass_levels = {
            1: ["cleric", "sorcerer", "warlock"],
            2: ["wizard"],
            3: ["barbarian", "bard", "fighter", "monk", "paladin", "ranger", "rogue"],
        }

        if level not in subclass_levels:
            return []

        class_indices = subclass_levels[level]
        all_classes = self.list_all()
        return [cls for cls in all_classes if cls.index in class_indices]

    def get_saving_throw_proficiencies(self, class_index: str) -> List[str]:
        """Get the saving throw proficiencies for a class.

        Args:
            class_index: The class index

        Returns:
            List of ability score indices for saving throws
        """
        cls = self.get_by_index_with_options(class_index, resolve_references=False)
        if not cls:
            return []

        return [save.index for save in cls.saving_throws]

    def get_starting_equipment_value(self, class_index: str) -> int:
        """Calculate the total value of starting equipment for a class.

        Args:
            class_index: The class index

        Returns:
            Total value in gold pieces
        """
        cls = self.get_by_index_with_options(class_index, resolve_references=True)
        if not cls:
            return 0

        total_value = 0

        # Sum up guaranteed equipment value
        for item in cls.starting_equipment:
            # Would need equipment data to calculate actual value
            # For now, estimate based on quantity
            total_value += item.quantity * 10  # Rough estimate

        return total_value
