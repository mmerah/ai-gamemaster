"""Base repository for D&D 5e data access.

This module provides a generic repository pattern that all specific D5e repositories
can inherit from. It handles common operations like getting by index, searching,
and filtering while integrating with the data loader, index builder, and reference resolver.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast, overload

from pydantic import BaseModel

from app.core.d5e_interfaces import D5eRepositoryProtocol
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import (
    D5eReferenceResolver,
    ReferenceNotFoundError,
)

# Type variable for the Pydantic model type
TModel = TypeVar("TModel", bound=BaseModel)


class BaseD5eRepository(D5eRepositoryProtocol[TModel], Generic[TModel]):
    """Generic repository implementation for D5e data access.

    This base class provides common functionality for all D5e repositories,
    including index-based lookups, searching, and reference resolution.

    Type Parameters:
        TModel: The Pydantic model type this repository returns
    """

    def __init__(
        self,
        category: str,
        model_class: Type[TModel],
        index_builder: D5eIndexBuilder,
        reference_resolver: D5eReferenceResolver,
    ) -> None:
        """Initialize the repository with dependencies.

        Args:
            category: The data category (e.g., 'spells', 'classes')
            model_class: The Pydantic model class to use for validation
            index_builder: Index builder for fast lookups
            reference_resolver: Resolver for handling references
        """
        self._category = category
        self._model_class = model_class
        self._index_builder = index_builder
        self._reference_resolver = reference_resolver

        # Build indices for this category on initialization
        self._index_builder.build_indices()

    def get_by_index(self, index: str) -> Optional[TModel]:
        """Get an entity by its unique index.

        Args:
            index: The unique identifier

        Returns:
            The entity if found, None otherwise
        """
        return self.get_by_index_with_options(index, resolve_references=True)

    def get_by_index_with_options(
        self, index: str, resolve_references: bool = True
    ) -> Optional[TModel]:
        """Get an entity by its unique index with options.

        Args:
            index: The unique identifier
            resolve_references: Whether to resolve references to full objects

        Returns:
            The entity if found, None otherwise
        """
        try:
            raw_data = self._index_builder.get_by_index(self._category, index)
            if not raw_data:
                return None

            # Resolve references if requested
            if resolve_references:
                raw_data = self._reference_resolver.resolve_deep(raw_data)

            # Convert to model
            return self._model_class(**raw_data)

        except ReferenceNotFoundError:
            # Reference resolution failed, return None
            return None
        except Exception:
            # Model validation or other error
            return None

    def get_by_name(self, name: str) -> Optional[TModel]:
        """Get an entity by its name (case-insensitive).

        Args:
            name: The entity name

        Returns:
            The entity if found, None otherwise
        """
        return self.get_by_name_with_options(name, resolve_references=True)

    def get_by_name_with_options(
        self, name: str, resolve_references: bool = True
    ) -> Optional[TModel]:
        """Get an entity by its name with options.

        Args:
            name: The entity name
            resolve_references: Whether to resolve references to full objects

        Returns:
            The entity if found, None otherwise
        """
        try:
            raw_data = self._index_builder.get_by_name(self._category, name)
            if not raw_data:
                return None

            # Resolve references if requested
            if resolve_references:
                raw_data = self._reference_resolver.resolve_deep(raw_data)

            # Convert to model
            return self._model_class(**raw_data)

        except ReferenceNotFoundError:
            return None
        except Exception:
            return None

    def list_all(self) -> List[TModel]:
        """Get all entities in this category.

        Returns:
            List of all entities
        """
        return self.list_all_with_options(resolve_references=False)

    def list_all_with_options(self, resolve_references: bool = False) -> List[TModel]:
        """Get all entities in this category with options.

        Args:
            resolve_references: Whether to resolve references (expensive for large datasets)

        Returns:
            List of all entities
        """
        all_data = self._index_builder.get_all_in_category(self._category)
        if not all_data:
            return []

        results: List[TModel] = []
        for raw_data in all_data:
            try:
                # Resolve references if requested
                if resolve_references:
                    raw_data = self._reference_resolver.resolve_deep(raw_data)

                # Convert to model
                model = self._model_class(**raw_data)
                results.append(model)
            except Exception:
                # Skip invalid entries
                continue

        return results

    def search(self, query: str) -> List[TModel]:
        """Search for entities by name (substring match).

        Args:
            query: The search query

        Returns:
            List of matching entities
        """
        return self.search_with_options(query, resolve_references=False)

    def search_with_options(
        self, query: str, resolve_references: bool = False
    ) -> List[TModel]:
        """Search for entities by name with options.

        Args:
            query: The search query
            resolve_references: Whether to resolve references

        Returns:
            List of matching entities
        """
        matches = self._index_builder.search(self._category, query)
        if not matches:
            return []

        results: List[TModel] = []
        for raw_data in matches:
            try:
                # Resolve references if requested
                if resolve_references:
                    raw_data = self._reference_resolver.resolve_deep(raw_data)

                # Convert to model
                model = self._model_class(**raw_data)
                results.append(model)
            except Exception:
                # Skip invalid entries
                continue

        return results

    def filter_by(self, **kwargs: Any) -> List[TModel]:
        """Filter entities by field values.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            List of matching entities
        """
        all_data = self._index_builder.get_all_in_category(self._category)
        if not all_data:
            return []

        results: List[TModel] = []
        for raw_data in all_data:
            # Check if all filter conditions match
            match = True
            for field, value in kwargs.items():
                if field not in raw_data or raw_data[field] != value:
                    match = False
                    break

            if match:
                try:
                    # Don't resolve references for filtering (performance)
                    model = self._model_class(**raw_data)
                    results.append(model)
                except Exception:
                    # Skip invalid entries
                    continue

        return results

    def exists(self, index: str) -> bool:
        """Check if an entity exists by index.

        Args:
            index: The unique identifier

        Returns:
            True if the entity exists
        """
        return self._index_builder.get_by_index(self._category, index) is not None

    def count(self) -> int:
        """Get the total number of entities in this category.

        Returns:
            The entity count
        """
        all_data = self._index_builder.get_all_in_category(self._category)
        return len(all_data) if all_data else 0

    def get_indices(self) -> List[str]:
        """Get all unique indices in this category.

        Returns:
            List of all indices
        """
        all_data = self._index_builder.get_all_in_category(self._category)
        if not all_data:
            return []

        return [item.get("index", "") for item in all_data if "index" in item]

    def get_names(self) -> List[str]:
        """Get all entity names in this category.

        Returns:
            List of all names
        """
        all_data = self._index_builder.get_all_in_category(self._category)
        if not all_data:
            return []

        return [item.get("name", "") for item in all_data if "name" in item]
