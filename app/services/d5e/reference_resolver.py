"""Reference resolver for 5e-database cross-references."""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.services.d5e.data_loader import D5eDataLoader


class ReferenceNotFoundError(Exception):
    """Raised when a reference cannot be resolved."""

    pass


class CircularReferenceError(Exception):
    """Raised when a circular reference is detected."""

    pass


class D5eReferenceResolver:
    """Resolves cross-references between D&D 5e entities.

    The 5e-database uses a reference system where entities reference each other
    via URL strings like "/api/spells/fireball". This class resolves these
    references to their actual data objects.
    """

    def __init__(self, data_loader: D5eDataLoader) -> None:
        """Initialize the reference resolver.

        Args:
            data_loader: The data loader to use for fetching referenced entities.
        """
        self._data_loader = data_loader
        self._reference_cache: Dict[str, Dict[str, Any]] = {}

    def resolve_reference(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a single reference to its full data.

        Args:
            reference: A reference object with 'index', 'name', and 'url' fields.

        Returns:
            The full data object for the referenced entity.

        Raises:
            ReferenceNotFoundError: If the reference cannot be found.
            ValueError: If the reference format is invalid.
        """
        if not self._is_reference(reference):
            raise ValueError("Invalid reference object")

        url = reference["url"]

        # Check cache first
        if url in self._reference_cache:
            return self._reference_cache[url]

        # Parse the URL to get category and index
        category, index = self._parse_reference_url(url)

        # Load the referenced data
        data = self._data_loader.get_by_index(category, index)

        if data is None:
            raise ReferenceNotFoundError(
                f"Reference not found: {category}/{index} from {url}"
            )

        # Cache the result
        self._reference_cache[url] = data

        return data

    def resolve_deep(
        self,
        obj: Any,
        max_depth: int = 10,
        _current_depth: int = 0,
        _visited_urls: Optional[Set[str]] = None,
    ) -> Any:
        """Recursively resolve all references in an object.

        This method traverses the object tree and resolves any reference
        objects it finds. It handles nested dictionaries and lists.

        Args:
            obj: The object to process. Can be a dict, list, or primitive.
            max_depth: Maximum recursion depth to prevent infinite loops.
            _current_depth: Internal parameter for tracking recursion depth.
            _visited_urls: Internal parameter for circular reference detection.

        Returns:
            The object with all references resolved.

        Raises:
            CircularReferenceError: If a circular reference is detected.
        """
        if _visited_urls is None:
            _visited_urls = set()

        # Check max depth
        if _current_depth >= max_depth:
            return obj

        # Handle dictionaries
        if isinstance(obj, dict):
            # Check if this is a reference
            if self._is_reference(obj):
                url = obj["url"]

                # Check for circular references
                if url in _visited_urls:
                    raise CircularReferenceError(f"Circular reference detected: {url}")

                # Add to visited set for this resolution path
                new_visited = _visited_urls.copy()
                new_visited.add(url)

                # Resolve the reference
                resolved = self.resolve_reference(obj)

                # Recursively resolve any references in the resolved object
                return self.resolve_deep(
                    resolved,
                    max_depth=max_depth,
                    _current_depth=_current_depth + 1,
                    _visited_urls=new_visited,
                )
            else:
                # Recursively process all values in the dictionary
                return {
                    key: self.resolve_deep(
                        value,
                        max_depth=max_depth,
                        _current_depth=_current_depth,
                        _visited_urls=_visited_urls,
                    )
                    for key, value in obj.items()
                }

        # Handle lists
        elif isinstance(obj, list):
            return [
                self.resolve_deep(
                    item,
                    max_depth=max_depth,
                    _current_depth=_current_depth,
                    _visited_urls=_visited_urls,
                )
                for item in obj
            ]

        # Return primitives as-is
        else:
            return obj

    def _is_reference(self, obj: Any) -> bool:
        """Check if an object is a reference.

        A reference object must be a dictionary with ONLY 'index', 'name', and 'url' fields.
        Objects with additional fields are considered resolved entities, not references.

        Args:
            obj: The object to check.

        Returns:
            True if the object is a reference, False otherwise.
        """
        if not isinstance(obj, dict):
            return False

        # Must have these three fields
        required_fields = {"index", "name", "url"}
        if not all(key in obj for key in required_fields):
            return False

        # If it has more than just these fields, it's not a reference
        # (it's a resolved entity)
        return len(obj.keys()) == len(required_fields)

    def _parse_reference_url(self, url: str) -> Tuple[str, str]:
        """Parse a reference URL to extract category and index.

        URLs are in the format: /api/{category}/{index}

        Args:
            url: The reference URL to parse.

        Returns:
            A tuple of (category, index).

        Raises:
            ValueError: If the URL format is invalid.
        """
        parts = url.strip("/").split("/")

        if len(parts) != 3 or parts[0] != "api":
            raise ValueError(f"Invalid reference URL: {url}")

        category = parts[1]
        index = parts[2]

        return category, index

    def clear_cache(self) -> None:
        """Clear the reference cache.

        This can be useful to free memory or force re-resolution of references.
        """
        self._reference_cache.clear()
