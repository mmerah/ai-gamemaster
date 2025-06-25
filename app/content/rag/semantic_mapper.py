"""
Semantic mapper for translating conceptual knowledge types to concrete data sources.
Implements a clean, configurable mapping layer.
"""

from typing import Dict, List, Set


class SemanticMapper:
    """Maps conceptual knowledge types to concrete data sources."""

    # Default semantic mappings
    DEFAULT_MAPPINGS: Dict[str, List[str]] = {
        # Conceptual types to concrete knowledge base types
        "adventure": ["lore", "monsters", "equipment", "spells"],
        "lore": ["lore"],  # Lore should map directly to lore
        "npcs": [
            "monsters",
            "lore",
        ],  # NPCs might be in lore or use monster stat blocks
        "rules": ["rules", "mechanics"],
        "character": ["character_options"],
        "combat": ["monsters", "spells", "equipment", "mechanics", "rules"],
        "exploration": ["lore", "monsters", "equipment", "mechanics"],
        "social": ["lore", "monsters", "rules"],
        "story": ["lore"],
        # Direct mappings (passthrough)
        "monsters": ["monsters"],
        "spells": ["spells"],
        "equipment": ["equipment"],
        "character_options": ["character_options"],
        "mechanics": ["mechanics"],
    }

    def __init__(self, custom_mappings: Dict[str, List[str]] | None = None):
        """
        Initialize the semantic mapper.

        Args:
            custom_mappings: Optional custom mappings to override defaults
        """
        self.mappings = self.DEFAULT_MAPPINGS.copy()
        if custom_mappings:
            self.mappings.update(custom_mappings)

    def map_to_concrete_types(self, conceptual_types: List[str]) -> Set[str]:
        """
        Map conceptual knowledge types to concrete data source types.

        Args:
            conceptual_types: List of conceptual types (e.g., ["adventure", "lore"])

        Returns:
            Set of concrete knowledge base types to search
        """
        concrete_types = set()

        for conceptual_type in conceptual_types:
            if conceptual_type in self.mappings:
                # It's a conceptual type with mappings
                concrete_types.update(self.mappings[conceptual_type])
            else:
                # Treat as a concrete type (passthrough)
                concrete_types.add(conceptual_type)

        return concrete_types

    def add_mapping(self, conceptual_type: str, concrete_types: List[str]) -> None:
        """Add or update a mapping."""
        self.mappings[conceptual_type] = concrete_types

    def get_all_concrete_types(self) -> Set[str]:
        """Get all unique concrete types from all mappings."""
        all_types = set()
        for concrete_list in self.mappings.values():
            all_types.update(concrete_list)
        return all_types
