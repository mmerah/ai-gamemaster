"""Database-backed specialized repository for D&D 5e classes.

This module provides advanced class-specific queries using SQLAlchemy.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError

from app.content.models import CharacterClass, ContentPack, Feature, Level
from app.content.protocols import DatabaseManagerProtocol
from app.content.repositories.db_base_repository import BaseD5eDbRepository
from app.content.schemas import D5eClass, D5eFeature, D5eLevel
from app.exceptions import DatabaseError, EntityNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class DbClassRepository(BaseD5eDbRepository[D5eClass]):
    """Database-backed repository for accessing class data with specialized queries."""

    def __init__(self, database_manager: DatabaseManagerProtocol) -> None:
        """Initialize the class repository."""
        super().__init__(
            model_class=D5eClass,
            entity_class=CharacterClass,
            database_manager=database_manager,
        )

        # Also create repositories for features and levels
        self._feature_repo = BaseD5eDbRepository[D5eFeature](
            model_class=D5eFeature,
            entity_class=Feature,
            database_manager=database_manager,
        )

        self._level_repo = BaseD5eDbRepository[D5eLevel](
            model_class=D5eLevel,
            entity_class=Level,
            database_manager=database_manager,
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

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            all_features = self._feature_repo.list_all()

            # Filter by class
            class_features = [
                feature
                for feature in all_features
                if feature.class_ and feature.class_.index == class_index
            ]

            # Filter by level if specified
            if level is not None:
                class_features = [f for f in class_features if f.level == level]

            # Sort by level
            return sorted(class_features, key=lambda f: f.level)
        except Exception as e:
            logger.error(
                f"Error getting class features for '{class_index}': {e}",
                extra={"class_index": class_index, "level": level, "error": str(e)},
            )
            raise DatabaseError(
                "Failed to get class features",
                details={"class_index": class_index, "level": level, "error": str(e)},
            )

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
            level
            for level in all_levels
            if level.class_ and level.class_.index == class_index
        ]

        return sorted(class_levels, key=lambda lvl: lvl.level)

    def get_level_data(self, class_index: str, level: int) -> Optional[D5eLevel]:
        """Get level-specific data for a class.

        Args:
            class_index: The class index
            level: The character level (1-20)

        Returns:
            Level data if found

        Raises:
            DatabaseError: If database operation fails
            ValidationError: If level is out of range
        """
        if level < 1 or level > 20:
            raise ValidationError(
                f"Invalid level {level}, must be between 1 and 20",
                field="level",
                value=level,
            )

        try:
            # Level indices are formatted as "{class}-{level}"
            level_index = f"{class_index}-{level}"
            return self._level_repo.get_by_index_with_options(
                level_index, resolve_references=True
            )
        except Exception as e:
            logger.error(
                f"Error getting level data for '{class_index}' level {level}: {e}",
                extra={"class_index": class_index, "level": level, "error": str(e)},
            )
            raise DatabaseError(
                "Failed to get level data",
                details={"class_index": class_index, "level": level, "error": str(e)},
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

    def get_saving_throw_proficiencies(self, class_index: str) -> List[str]:
        """Get the saving throw proficiencies for a class.

        Args:
            class_index: The class index

        Returns:
            List of ability score indices for saving throws

        Raises:
            EntityNotFoundError: If class not found
            DatabaseError: If database operation fails
        """
        try:
            cls = self.get_by_index_with_options(class_index, resolve_references=False)
            if not cls:
                raise EntityNotFoundError("Class", class_index, "index")

            return [save.index for save in cls.saving_throws]
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error getting saving throw proficiencies for '{class_index}': {e}",
                extra={"class_index": class_index, "error": str(e)},
            )
            raise DatabaseError(
                "Failed to get saving throw proficiencies",
                details={"class_index": class_index, "error": str(e)},
            )
