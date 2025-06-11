"""Specialized repository for D&D 5e spells.

This module provides advanced spell-specific queries beyond the basic repository functionality.
"""

from typing import List, Optional, Set, cast

from app.models.d5e import D5eSpell
from app.repositories.d5e.base_repository import BaseD5eRepository
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import D5eReferenceResolver


class SpellRepository(BaseD5eRepository[D5eSpell]):
    """Repository for accessing spell data with specialized queries."""

    def __init__(
        self,
        index_builder: D5eIndexBuilder,
        reference_resolver: D5eReferenceResolver,
    ) -> None:
        """Initialize the spell repository."""
        super().__init__(
            category="spells",
            model_class=D5eSpell,
            index_builder=index_builder,
            reference_resolver=reference_resolver,
        )

    def get_by_level(
        self, level: int, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all spells of a specific level.

        Args:
            level: The spell level (0 for cantrips, 1-9 for leveled spells)
            resolve_references: Whether to resolve references

        Returns:
            List of spells at the specified level
        """
        # Filter returns List[BaseModel], but we know they're D5eSpell instances
        results = self.filter_by(level=level)
        return [cast(D5eSpell, spell) for spell in results]

    def get_by_school(
        self, school_index: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all spells from a specific school of magic.

        Args:
            school_index: The school index (e.g., 'evocation', 'necromancy')
            resolve_references: Whether to resolve references

        Returns:
            List of spells from the specified school
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        return [spell for spell in all_spells if spell.school.index == school_index]

    def get_by_class(
        self, class_index: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all spells available to a specific class.

        Args:
            class_index: The class index (e.g., 'wizard', 'cleric')
            resolve_references: Whether to resolve references

        Returns:
            List of spells available to the class
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        return [
            spell
            for spell in all_spells
            if any(cls.index == class_index for cls in spell.classes)
        ]

    def get_by_class_and_level(
        self, class_index: str, level: int, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get spells available to a class at a specific level.

        Args:
            class_index: The class index
            level: The spell level
            resolve_references: Whether to resolve references

        Returns:
            List of matching spells
        """
        class_spells = self.get_by_class(class_index, resolve_references)
        return [spell for spell in class_spells if spell.level == level]

    def get_ritual_spells(self, resolve_references: bool = False) -> List[D5eSpell]:
        """Get all ritual spells.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of ritual spells
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        return [spell for spell in all_spells if spell.ritual]

    def get_concentration_spells(
        self, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all concentration spells.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of concentration spells
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        return [spell for spell in all_spells if spell.concentration]

    def get_by_components(
        self,
        verbal: Optional[bool] = None,
        somatic: Optional[bool] = None,
        material: Optional[bool] = None,
        resolve_references: bool = False,
    ) -> List[D5eSpell]:
        """Get spells filtered by component requirements.

        Args:
            verbal: If specified, filter by verbal component requirement
            somatic: If specified, filter by somatic component requirement
            material: If specified, filter by material component requirement
            resolve_references: Whether to resolve references

        Returns:
            List of spells matching component criteria
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        results = []

        for spell in all_spells:
            # Check each component requirement if specified
            if verbal is not None and ("V" in spell.components) != verbal:
                continue
            if somatic is not None and ("S" in spell.components) != somatic:
                continue
            if material is not None and ("M" in spell.components) != material:
                continue

            results.append(spell)

        return results

    def get_by_casting_time(
        self, casting_time: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get spells with a specific casting time.

        Args:
            casting_time: The casting time (e.g., '1 action', '1 bonus action')
            resolve_references: Whether to resolve references

        Returns:
            List of spells with the specified casting time
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        return [
            spell
            for spell in all_spells
            if spell.casting_time.lower() == casting_time.lower()
        ]

    def get_by_range(
        self, range_str: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get spells with a specific range.

        Args:
            range_str: The range (e.g., 'Self', 'Touch', '120 feet')
            resolve_references: Whether to resolve references

        Returns:
            List of spells with the specified range
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        return [
            spell for spell in all_spells if spell.range.lower() == range_str.lower()
        ]

    def get_available_schools(self) -> Set[str]:
        """Get all unique spell schools.

        Returns:
            Set of school indices
        """
        all_spells = self.list_all_with_options(resolve_references=False)
        return {spell.school.index for spell in all_spells}

    def get_max_level(self) -> int:
        """Get the highest spell level available.

        Returns:
            The maximum spell level (typically 9)
        """
        all_spells = self.list_all_with_options(resolve_references=False)
        if not all_spells:
            return 0
        return max(spell.level for spell in all_spells)

    def search_by_description(
        self, keyword: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Search for spells containing a keyword in their description.

        Args:
            keyword: The keyword to search for (case-insensitive)
            resolve_references: Whether to resolve references

        Returns:
            List of spells containing the keyword in their description
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        keyword_lower = keyword.lower()

        results = []
        for spell in all_spells:
            # Check main description
            if any(keyword_lower in desc.lower() for desc in spell.desc):
                results.append(spell)
                continue

            # Check higher level description if present
            if spell.higher_level and any(
                keyword_lower in desc.lower() for desc in spell.higher_level
            ):
                results.append(spell)

        return results
