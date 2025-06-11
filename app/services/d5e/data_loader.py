"""Data loader for 5e-database JSON files."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class D5eDataLoader:
    """Loads and caches D&D 5e data from JSON files.

    This class is responsible for loading the 25 JSON files from the 5e-database
    submodule. It provides caching to avoid repeated file I/O operations.
    """

    # Mapping of category names to their JSON file names
    CATEGORY_FILES = {
        "ability-scores": "5e-SRD-Ability-Scores.json",
        "alignments": "5e-SRD-Alignments.json",
        "backgrounds": "5e-SRD-Backgrounds.json",
        "classes": "5e-SRD-Classes.json",
        "conditions": "5e-SRD-Conditions.json",
        "damage-types": "5e-SRD-Damage-Types.json",
        "equipment": "5e-SRD-Equipment.json",
        "equipment-categories": "5e-SRD-Equipment-Categories.json",
        "feats": "5e-SRD-Feats.json",
        "features": "5e-SRD-Features.json",
        "languages": "5e-SRD-Languages.json",
        "levels": "5e-SRD-Levels.json",
        "magic-items": "5e-SRD-Magic-Items.json",
        "magic-schools": "5e-SRD-Magic-Schools.json",
        "monsters": "5e-SRD-Monsters.json",
        "proficiencies": "5e-SRD-Proficiencies.json",
        "races": "5e-SRD-Races.json",
        "rules": "5e-SRD-Rules.json",
        "rule-sections": "5e-SRD-Rule-Sections.json",
        "skills": "5e-SRD-Skills.json",
        "spells": "5e-SRD-Spells.json",
        "subclasses": "5e-SRD-Subclasses.json",
        "subraces": "5e-SRD-Subraces.json",
        "traits": "5e-SRD-Traits.json",
        "weapon-properties": "5e-SRD-Weapon-Properties.json",
    }

    def __init__(self, base_path: str = "knowledge/5e-database/src/2014") -> None:
        """Initialize the data loader.

        Args:
            base_path: Path to the directory containing the JSON files.
                      Defaults to the 5e-database submodule location.
        """
        self._base_path = base_path
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def load_category(self, category: str) -> List[Dict[str, Any]]:
        """Load data for a specific category.

        This method loads the JSON file for the given category and caches
        the result. Subsequent calls for the same category will return
        the cached data without reading the file again.

        Args:
            category: The category name (e.g., "spells", "classes", "monsters")

        Returns:
            List of dictionaries containing the data for the category.

        Raises:
            ValueError: If the category is not recognized.
            FileNotFoundError: If the JSON file doesn't exist.
            json.JSONDecodeError: If the JSON file is malformed.
        """
        if category not in self.CATEGORY_FILES:
            raise ValueError(f"Unknown category: {category}")

        # Return cached data if available
        if category in self._cache:
            return self._cache[category]

        # Load from file
        file_name = self.CATEGORY_FILES[category]
        file_path = Path(self._base_path) / file_name

        with open(file_path, "r", encoding="utf-8") as f:
            data: List[Dict[str, Any]] = json.load(f)

        # Cache and return
        self._cache[category] = data
        return data

    def get_by_index(self, category: str, index: str) -> Optional[Dict[str, Any]]:
        """Get a specific item from a category by its index.

        Args:
            category: The category name.
            index: The index of the item to retrieve.

        Returns:
            The item dictionary if found, None otherwise.
        """
        data = self.load_category(category)

        for item in data:
            if item.get("index") == index:
                return item

        return None

    def clear_cache(self, category: Optional[str] = None) -> None:
        """Clear the cache.

        Args:
            category: If provided, only clear cache for this category.
                     If None, clear entire cache.
        """
        if category is None:
            self._cache.clear()
        elif category in self._cache:
            del self._cache[category]

    def get_all_categories(self) -> List[str]:
        """Get a list of all available categories.

        Returns:
            List of category names.
        """
        return list(self.CATEGORY_FILES.keys())
