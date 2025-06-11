"""Index builder for efficient D&D 5e data lookups."""

from typing import Any, Dict, List, Optional

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
