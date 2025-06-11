"""Protocol definitions for D&D 5e data repositories."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class D5eRepositoryProtocol(Protocol[TModel]):
    """Protocol for D&D 5e data repositories.

    This defines the interface that all D5e repositories must implement,
    providing a consistent API for data access across different entity types.
    """

    def get_by_index(self, index: str) -> Optional[TModel]:
        """Get an entity by its index.

        Args:
            index: The unique index of the entity.

        Returns:
            The entity model if found, None otherwise.
        """
        ...

    def get_by_name(self, name: str) -> Optional[TModel]:
        """Get an entity by its name (case-insensitive).

        Args:
            name: The name of the entity.

        Returns:
            The entity model if found, None otherwise.
        """
        ...

    def list_all(self) -> List[TModel]:
        """List all entities in this repository.

        Returns:
            List of all entity models.
        """
        ...

    def search(self, query: str) -> List[TModel]:
        """Search entities by partial name match.

        Args:
            query: The search query (partial name).

        Returns:
            List of matching entity models.
        """
        ...

    def filter_by(self, **criteria: Any) -> List[TModel]:
        """Filter entities by specific criteria.

        Args:
            **criteria: Field-value pairs to filter by.

        Returns:
            List of matching entity models.
        """
        ...


class D5eDataServiceProtocol(Protocol):
    """Protocol for the main D5e data service.

    This defines the high-level interface for accessing all D&D 5e data.
    """

    # Character creation helpers
    def get_class_at_level(
        self, class_name: str, level: int
    ) -> Optional[Dict[str, Any]]:
        """Get complete class information at a specific level.

        Args:
            class_name: Name of the class.
            level: Character level (1-20).

        Returns:
            Dictionary with class features, spell slots, etc.
        """
        ...

    def calculate_ability_modifiers(self, scores: Dict[str, int]) -> Dict[str, int]:
        """Calculate ability modifiers from ability scores.

        Args:
            scores: Dictionary mapping ability names to scores.

        Returns:
            Dictionary mapping ability names to modifiers.
        """
        ...

    def get_proficiency_bonus(self, level: int) -> int:
        """Get proficiency bonus for a character level.

        Args:
            level: Character level (1-20).

        Returns:
            Proficiency bonus.
        """
        ...

    # Spell helpers
    def get_spells_for_class(
        self, class_name: str, level: Optional[int] = None
    ) -> List[BaseModel]:
        """Get all spells available to a class.

        Args:
            class_name: Name of the class.
            level: Optional spell level filter.

        Returns:
            List of spell models.
        """
        ...

    def get_spell_slots(self, class_name: str, level: int) -> Dict[int, int]:
        """Get spell slots by class and level.

        Args:
            class_name: Name of the spellcasting class.
            level: Character level.

        Returns:
            Dictionary mapping spell level to number of slots.
        """
        ...

    # Monster helpers
    def get_monsters_by_cr(self, min_cr: float, max_cr: float) -> List[BaseModel]:
        """Get monsters within a challenge rating range.

        Args:
            min_cr: Minimum challenge rating.
            max_cr: Maximum challenge rating.

        Returns:
            List of monster models.
        """
        ...

    # Equipment helpers
    def get_starting_equipment(
        self, class_name: str, background: str
    ) -> List[BaseModel]:
        """Get all starting equipment options.

        Args:
            class_name: Name of the class.
            background: Name of the background.

        Returns:
            List of equipment models.
        """
        ...

    # Rules helpers
    def get_rule_section(self, section: str) -> List[str]:
        """Get rules text for a specific section.

        Args:
            section: Name of the rule section.

        Returns:
            List of rule text paragraphs.
        """
        ...
