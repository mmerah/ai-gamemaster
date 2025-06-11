"""Index builder for efficient D&D 5e data lookups."""

from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional

from app.services.d5e.data_loader import D5eDataLoader


class D5eIndexBuilder:
    """Builds and maintains indices for fast D&D 5e data lookups.

    This class creates index maps for all data categories, allowing O(1)
    lookups by index and fast searches by name.
    """

    def __init__(self, data_loader: D5eDataLoader) -> None:
        """Initialize the index builder.

        Args:
            data_loader: The data loader to use for fetching data.
        """
        self._data_loader = data_loader
        self._indices: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._name_indices: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Specialized indices for common searches
        self._spell_indices: Dict[str, DefaultDict[str, List[Dict[str, Any]]]] = {
            "by_school": defaultdict(list),
            "by_class": defaultdict(list),
            "by_level": defaultdict(list),
            "by_component": defaultdict(list),
        }
        self._monster_indices: Dict[str, DefaultDict[str, List[Dict[str, Any]]]] = {
            "by_cr": defaultdict(list),
            "by_type": defaultdict(list),
            "by_size": defaultdict(list),
        }
        self._equipment_indices: Dict[str, DefaultDict[str, List[Dict[str, Any]]]] = {
            "by_category": defaultdict(list),
            "by_weapon_category": defaultdict(list),
            "by_armor_category": defaultdict(list),
        }
        self._class_indices: Dict[str, DefaultDict[str, List[Dict[str, Any]]]] = {
            "by_hit_die": defaultdict(list),
            "by_spellcasting": defaultdict(list),
        }

        self._specialized_indices_built = False

    def build_indices(
        self, force_rebuild: bool = False
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Build indices for all data categories.

        This method creates index maps for each category, mapping from the
        entity's index to its full data. The indices are cached for subsequent
        calls unless force_rebuild is True.

        Args:
            force_rebuild: If True, rebuild indices even if already cached.

        Returns:
            Dictionary mapping category names to their index maps.
        """
        if self._indices and not force_rebuild:
            return self._indices

        # Clear existing indices
        self._indices.clear()
        self._name_indices.clear()

        # Build indices for each category
        categories = self._data_loader.get_all_categories()

        for category in categories:
            data = self._data_loader.load_category(category)

            # Build index map
            index_map: Dict[str, Dict[str, Any]] = {}
            name_map: Dict[str, Dict[str, Any]] = {}

            for item in data:
                if "index" in item:
                    index_map[item["index"]] = item

                if "name" in item:
                    # Store by lowercase name for case-insensitive lookup
                    name_key = item["name"].lower().strip()
                    name_map[name_key] = item

            self._indices[category] = index_map
            self._name_indices[category] = name_map

        # Build specialized indices
        self._build_specialized_indices()

        return self._indices

    def get_by_index(self, category: str, index: str) -> Optional[Dict[str, Any]]:
        """Get an item by its index.

        This provides O(1) lookup by index within a category.

        Args:
            category: The category to search in.
            index: The index of the item to retrieve.

        Returns:
            The item data if found, None otherwise.
        """
        # Ensure indices are built
        if not self._indices:
            self.build_indices()

        if category not in self._indices:
            return None

        return self._indices[category].get(index)

    def get_by_name(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """Get an item by its name (case-insensitive).

        This provides fast lookup by name within a category.

        Args:
            category: The category to search in.
            name: The name of the item to retrieve.

        Returns:
            The item data if found, None otherwise.
        """
        # Ensure indices are built
        if not self._name_indices:
            self.build_indices()

        if category not in self._name_indices:
            return None

        # Normalize the name for lookup
        name_key = name.lower().strip()
        return self._name_indices[category].get(name_key)

    def search(self, category: str, query: str) -> List[Dict[str, Any]]:
        """Search for items by partial name match.

        This performs a case-insensitive substring search on item names.

        Args:
            category: The category to search in.
            query: The search query (partial name).

        Returns:
            List of matching items.
        """
        # Ensure indices are built
        if not self._indices:
            self.build_indices()

        if category not in self._indices:
            return []

        # Normalize query for case-insensitive search
        query_lower = query.lower().strip()

        results = []
        for item in self._indices[category].values():
            if "name" in item and query_lower in item["name"].lower():
                results.append(item)

        return results

    def get_all_in_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all items in a category.

        Args:
            category: The category to retrieve.

        Returns:
            List of all items in the category.
        """
        # Ensure indices are built
        if not self._indices:
            self.build_indices()

        if category not in self._indices:
            return []

        return list(self._indices[category].values())

    def clear_cache(self) -> None:
        """Clear all cached indices.

        This forces a rebuild on the next access.
        """
        self._indices.clear()
        self._name_indices.clear()

        # Clear specialized indices
        for category_indices in self._spell_indices.values():
            category_indices.clear()
        for category_indices in self._monster_indices.values():
            category_indices.clear()
        for category_indices in self._equipment_indices.values():
            category_indices.clear()
        for category_indices in self._class_indices.values():
            category_indices.clear()

        self._specialized_indices_built = False

    def _build_specialized_indices(self) -> None:
        """Build specialized indices for common search patterns."""
        if self._specialized_indices_built:
            return

        # Build spell indices
        if "spells" in self._indices:
            for spell in self._indices["spells"].values():
                # Index by school
                if "school" in spell and "index" in spell["school"]:
                    school_index = spell["school"]["index"]
                    self._spell_indices["by_school"][school_index].append(spell)

                # Index by level
                if "level" in spell:
                    level = str(spell["level"])
                    self._spell_indices["by_level"][level].append(spell)

                # Index by class
                if "classes" in spell:
                    for class_ref in spell["classes"]:
                        if "index" in class_ref:
                            self._spell_indices["by_class"][class_ref["index"]].append(
                                spell
                            )

                # Index by components
                if "components" in spell:
                    for component in spell["components"]:
                        self._spell_indices["by_component"][component.lower()].append(
                            spell
                        )

        # Build monster indices
        if "monsters" in self._indices:
            for monster in self._indices["monsters"].values():
                # Index by CR
                if "challenge_rating" in monster:
                    cr = str(monster["challenge_rating"])
                    self._monster_indices["by_cr"][cr].append(monster)

                # Index by type
                if "type" in monster:
                    monster_type = monster["type"].lower()
                    self._monster_indices["by_type"][monster_type].append(monster)

                # Index by size
                if "size" in monster:
                    size = monster["size"].lower()
                    self._monster_indices["by_size"][size].append(monster)

        # Build equipment indices
        if "equipment" in self._indices:
            for item in self._indices["equipment"].values():
                # Index by equipment category
                if (
                    "equipment_category" in item
                    and "index" in item["equipment_category"]
                ):
                    category = item["equipment_category"]["index"]
                    self._equipment_indices["by_category"][category].append(item)

                # Index by weapon category
                if "weapon_category" in item:
                    weapon_cat = item["weapon_category"].lower()
                    self._equipment_indices["by_weapon_category"][weapon_cat].append(
                        item
                    )

                # Index by armor category
                if "armor_category" in item:
                    armor_cat = item["armor_category"].lower()
                    self._equipment_indices["by_armor_category"][armor_cat].append(item)

        # Build class indices
        if "classes" in self._indices:
            for class_data in self._indices["classes"].values():
                # Index by hit die
                if "hit_die" in class_data:
                    hit_die = str(class_data["hit_die"])
                    self._class_indices["by_hit_die"][hit_die].append(class_data)

                # Index by spellcasting
                has_spellcasting = (
                    "spellcasting" in class_data and class_data["spellcasting"]
                )
                spellcasting_key = "yes" if has_spellcasting else "no"
                self._class_indices["by_spellcasting"][spellcasting_key].append(
                    class_data
                )

        self._specialized_indices_built = True

    def get_spells_by_school(self, school_index: str) -> List[Dict[str, Any]]:
        """Get all spells of a specific school."""
        self._ensure_specialized_indices()
        return list(self._spell_indices["by_school"][school_index])

    def get_spells_by_class(self, class_index: str) -> List[Dict[str, Any]]:
        """Get all spells available to a specific class."""
        self._ensure_specialized_indices()
        return list(self._spell_indices["by_class"][class_index])

    def get_spells_by_level(self, level: int) -> List[Dict[str, Any]]:
        """Get all spells of a specific level."""
        self._ensure_specialized_indices()
        return list(self._spell_indices["by_level"][str(level)])

    def get_spells_by_component(self, component: str) -> List[Dict[str, Any]]:
        """Get all spells that require a specific component."""
        self._ensure_specialized_indices()
        return list(self._spell_indices["by_component"][component.lower()])

    def get_monsters_by_cr(self, cr: float) -> List[Dict[str, Any]]:
        """Get all monsters of a specific challenge rating."""
        self._ensure_specialized_indices()
        return list(self._monster_indices["by_cr"][str(cr)])

    def get_monsters_by_type(self, monster_type: str) -> List[Dict[str, Any]]:
        """Get all monsters of a specific type."""
        self._ensure_specialized_indices()
        return list(self._monster_indices["by_type"][monster_type.lower()])

    def get_monsters_by_size(self, size: str) -> List[Dict[str, Any]]:
        """Get all monsters of a specific size."""
        self._ensure_specialized_indices()
        return list(self._monster_indices["by_size"][size.lower()])

    def get_equipment_by_category(self, category_index: str) -> List[Dict[str, Any]]:
        """Get all equipment items of a specific category."""
        self._ensure_specialized_indices()
        return list(self._equipment_indices["by_category"][category_index])

    def get_equipment_by_weapon_category(
        self, weapon_category: str
    ) -> List[Dict[str, Any]]:
        """Get all equipment items of a specific weapon category."""
        self._ensure_specialized_indices()
        return list(
            self._equipment_indices["by_weapon_category"][weapon_category.lower()]
        )

    def get_equipment_by_armor_category(
        self, armor_category: str
    ) -> List[Dict[str, Any]]:
        """Get all equipment items of a specific armor category."""
        self._ensure_specialized_indices()
        return list(
            self._equipment_indices["by_armor_category"][armor_category.lower()]
        )

    def get_classes_by_hit_die(self, hit_die: int) -> List[Dict[str, Any]]:
        """Get all classes with a specific hit die."""
        self._ensure_specialized_indices()
        return list(self._class_indices["by_hit_die"][str(hit_die)])

    def get_spellcasting_classes(self) -> List[Dict[str, Any]]:
        """Get all classes that have spellcasting."""
        self._ensure_specialized_indices()
        return list(self._class_indices["by_spellcasting"]["yes"])

    def get_non_spellcasting_classes(self) -> List[Dict[str, Any]]:
        """Get all classes that do not have spellcasting."""
        self._ensure_specialized_indices()
        return list(self._class_indices["by_spellcasting"]["no"])

    def _ensure_specialized_indices(self) -> None:
        """Ensure specialized indices are built."""
        if not self._specialized_indices_built:
            if not self._indices:
                self.build_indices()
            else:
                self._build_specialized_indices()
