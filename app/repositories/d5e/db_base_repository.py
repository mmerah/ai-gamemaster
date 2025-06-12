"""Database-aware base repository for D&D 5e data access.

This module provides a generic repository pattern that all specific D5e repositories
can inherit from. It handles common operations like getting by index, searching,
and filtering while using SQLAlchemy to query the database directly.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.d5e_interfaces import D5eRepositoryProtocol
from app.database.connection import DatabaseManager
from app.database.models import BaseContent

# Type variable for the Pydantic model type
TModel = TypeVar("TModel", bound=BaseModel)

# Type variable for the SQLAlchemy model type
TEntity = TypeVar("TEntity", bound=BaseContent)


class BaseD5eDbRepository(D5eRepositoryProtocol[TModel], Generic[TModel]):
    """Generic database-backed repository implementation for D5e data access.

    This base class provides common functionality for all D5e repositories,
    including index-based lookups, searching, and content pack filtering.

    Type Parameters:
        TModel: The Pydantic model type this repository returns
    """

    def __init__(
        self,
        model_class: Type[TModel],
        entity_class: Type[TEntity],
        database_manager: DatabaseManager,
    ) -> None:
        """Initialize the repository with dependencies.

        Args:
            model_class: The Pydantic model class to use for validation
            entity_class: The SQLAlchemy entity class to query
            database_manager: Database manager for session management
        """
        self._model_class = model_class
        self._entity_class = entity_class
        self._database_manager = database_manager
        self._current_session: Session

    def _get_session(self) -> Session:
        """Get a database session from the context manager."""
        # This method is called within a context that already has a session
        # The actual session management happens in the public methods
        return self._current_session

    def _apply_content_pack_filter(
        self,
        query: Any,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Any:
        """Apply content pack filtering to a query.

        Args:
            query: The SQLAlchemy query
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            The filtered query
        """
        if content_pack_priority:
            # Filter to only include items from the specified content packs
            query = query.filter(
                self._entity_class.content_pack_id.in_(content_pack_priority)
            )
        else:
            # Default: only include items from active content packs
            # Use subquery to avoid attribute issues
            from app.database.models import ContentPack

            query = query.join(
                ContentPack, self._entity_class.content_pack_id == ContentPack.id
            ).filter(ContentPack.is_active)
        return query

    def _find_by_name_with_priority(
        self,
        session: Session,
        name: str,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Optional[BaseContent]:
        """Find an entity by name, respecting content pack priority.

        Args:
            session: The database session
            name: The entity name
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            The entity if found, None otherwise
        """
        if content_pack_priority:
            # Search through content packs in priority order
            for pack_id in content_pack_priority:
                entity = (
                    session.query(self._entity_class)
                    .filter(
                        and_(
                            func.lower(self._entity_class.name) == func.lower(name),
                            self._entity_class.content_pack_id == pack_id,
                        )
                    )
                    .first()
                )
                if entity:
                    return entity
            return None
        else:
            # Default: get from any active content pack
            from app.database.models import ContentPack

            entity = (
                session.query(self._entity_class)
                .join(ContentPack, self._entity_class.content_pack_id == ContentPack.id)
                .filter(
                    and_(
                        func.lower(self._entity_class.name) == func.lower(name),
                        ContentPack.is_active,
                    )
                )
                .first()
            )
            return entity

    def _entity_to_model(self, entity: TEntity) -> Optional[TModel]:
        """Convert a SQLAlchemy entity to a Pydantic model.

        Args:
            entity: The SQLAlchemy entity

        Returns:
            The Pydantic model instance, or None if validation fails
        """
        try:
            # Convert the entity to a dictionary
            data = {}
            for column in entity.__table__.columns:
                data[column.name] = getattr(entity, column.name)

            # Remove database-specific fields
            data.pop("content_pack_id", None)

            # Apply field name mappings for specific model types
            data = self._apply_field_mappings(data)

            # Create and return the model
            return self._model_class(**data)
        except Exception as e:
            # Log validation errors but don't crash - some database records may be incomplete
            import logging

            logger = logging.getLogger(__name__)
            entity_id = getattr(entity, "index", "unknown")
            logger.warning(
                f"Failed to convert {self._model_class.__name__} entity '{entity_id}' to model: {e}"
            )
            return None

    def _apply_field_mappings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field name mappings between database and Pydantic models.

        Args:
            data: The raw database data

        Returns:
            The data with field names mapped for Pydantic validation
        """
        import json

        from app.models.d5e.character import D5eClass, D5eSubclass

        # Import here to avoid circular imports
        from app.models.d5e.progression import D5eFeature

        # Parse JSON string fields into Python objects
        self._parse_json_fields(data)

        # Map database field names to Pydantic field names
        if self._model_class == D5eFeature:
            # Map class_ref to class for D5eFeature (using the JSON alias)
            if "class_ref" in data:
                data["class"] = data.pop("class_ref")
        elif self._model_class == D5eSubclass:
            # Map class_ref to class for D5eSubclass (using the JSON alias)
            if "class_ref" in data:
                data["class"] = data.pop("class_ref")

        return data

    def _parse_json_fields(self, data: Dict[str, Any]) -> None:
        """Parse JSON string fields into Python objects.

        Args:
            data: The raw database data to modify in place
        """
        import json

        # Define which fields should be parsed as JSON
        json_fields = {
            "proficiencies",
            "proficiency_choices",
            "saving_throws",
            "starting_equipment",
            "starting_equipment_options",
            "multi_classing",
            "subclasses",
            "spellcasting",
            "class_ref",
            "subclass",
            "desc",
            "parent",
            "prerequisites",
            "feature_specific",
        }

        for field_name in json_fields:
            if field_name in data:
                if isinstance(data[field_name], str):
                    try:
                        # Parse JSON string, handling 'null' strings
                        if data[field_name] == "null":
                            data[field_name] = None
                        else:
                            parsed_data = json.loads(data[field_name])
                            # Fix nested choice objects that use 'from' instead of 'from_'
                            parsed_data = self._fix_choice_from_fields(parsed_data)
                            data[field_name] = parsed_data
                    except (json.JSONDecodeError, TypeError):
                        # If parsing fails, keep the original value
                        pass
                else:
                    # Field is already parsed (by SQLAlchemy), but still needs choice field fixing
                    data[field_name] = self._fix_choice_from_fields(data[field_name])

    def _fix_choice_from_fields(self, obj: Any) -> Any:
        """Recursively fix choice objects that use 'from' instead of 'from_'.

        Args:
            obj: The object to process (can be dict, list, or any other type)

        Returns:
            The processed object with fixed choice fields
        """
        if isinstance(obj, dict):
            # Create a new dict to avoid modifying during iteration
            result = {}
            for key, value in obj.items():
                # Fix nested choice objects within options
                if key == "choice" and isinstance(value, dict):
                    choice = self._fix_choice_from_fields(value)
                    # Nested choices use 'from' but should use 'from_' for the Choice model
                    if "from" in choice and "from_" not in choice:
                        choice["from_"] = choice.pop("from")
                    result[key] = choice
                # Fix top-level starting equipment options
                elif key == "from_" and isinstance(value, dict):
                    # StartingEquipmentOption expects 'from' as the JSON key (aliased to from_)
                    result["from"] = self._fix_choice_from_fields(value)
                else:
                    # Recursively process the value
                    result[key] = self._fix_choice_from_fields(value)
            return result
        elif isinstance(obj, list):
            # Process each item in the list
            return [self._fix_choice_from_fields(item) for item in obj]
        else:
            # Return primitive values as-is
            return obj

    def get_by_index(self, index: str) -> Optional[TModel]:
        """Get an entity by its unique index.

        Args:
            index: The unique identifier

        Returns:
            The entity if found, None otherwise
        """
        return self.get_by_index_with_options(index)

    def get_by_index_with_options(
        self,
        index: str,
        resolve_references: bool = True,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Optional[TModel]:
        """Get an entity by its unique index with options.

        Args:
            index: The unique identifier
            resolve_references: Whether to resolve references (not used in DB version)
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            The entity if found, None otherwise
        """
        with self._database_manager.get_session() as session:
            self._current_session = session

            if content_pack_priority:
                # Search through content packs in priority order
                for pack_id in content_pack_priority:
                    entity = (
                        session.query(self._entity_class)
                        .filter(
                            and_(
                                self._entity_class.index == index,
                                self._entity_class.content_pack_id == pack_id,
                            )
                        )
                        .first()
                    )
                    if entity:
                        return self._entity_to_model(entity)
                return None
            else:
                # Default: get from any active content pack
                from app.database.models import ContentPack

                entity = (
                    session.query(self._entity_class)
                    .join(
                        ContentPack,
                        self._entity_class.content_pack_id == ContentPack.id,
                    )
                    .filter(
                        and_(
                            self._entity_class.index == index,
                            ContentPack.is_active,
                        )
                    )
                    .first()
                )
                if entity:
                    return self._entity_to_model(entity)
                return None

    def get_by_name(self, name: str) -> Optional[TModel]:
        """Get an entity by its name (case-insensitive).

        Args:
            name: The entity name

        Returns:
            The entity if found, None otherwise
        """
        return self.get_by_name_with_options(name)

    def get_by_name_with_options(
        self,
        name: str,
        resolve_references: bool = True,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Optional[TModel]:
        """Get an entity by its name with options.

        Args:
            name: The entity name
            resolve_references: Whether to resolve references (not used in DB version)
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            The entity if found, None otherwise
        """
        with self._database_manager.get_session() as session:
            self._current_session = session

            entity = self._find_by_name_with_priority(
                session, name, content_pack_priority
            )
            if entity:
                return self._entity_to_model(entity)
            return None

    def list_all(self) -> List[TModel]:
        """Get all entities in this category.

        Returns:
            List of all entities
        """
        return self.list_all_with_options()

    def list_all_with_options(
        self,
        resolve_references: bool = False,
        content_pack_priority: Optional[List[str]] = None,
    ) -> List[TModel]:
        """Get all entities in this category with options.

        Args:
            resolve_references: Whether to resolve references (not used in DB version)
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            List of all entities
        """
        with self._database_manager.get_session() as session:
            self._current_session = session

            query = session.query(self._entity_class)
            query = self._apply_content_pack_filter(query, content_pack_priority)

            entities = query.all()
            models = [self._entity_to_model(entity) for entity in entities]
            return [model for model in models if model is not None]

    def search(self, query: str) -> List[TModel]:
        """Search for entities by name (substring match).

        Args:
            query: The search query

        Returns:
            List of matching entities
        """
        return self.search_with_options(query)

    def search_with_options(
        self,
        query: str,
        resolve_references: bool = False,
        content_pack_priority: Optional[List[str]] = None,
    ) -> List[TModel]:
        """Search for entities by name with options.

        Args:
            query: The search query
            resolve_references: Whether to resolve references (not used in DB version)
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            List of matching entities
        """
        with self._database_manager.get_session() as session:
            self._current_session = session

            db_query = session.query(self._entity_class).filter(
                self._entity_class.name.ilike(f"%{query}%")
            )
            db_query = self._apply_content_pack_filter(db_query, content_pack_priority)

            entities = db_query.all()
            models = [self._entity_to_model(entity) for entity in entities]
            return [model for model in models if model is not None]

    def filter_by(self, **kwargs: Any) -> List[TModel]:
        """Filter entities by field values.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            List of matching entities
        """
        with self._database_manager.get_session() as session:
            self._current_session = session

            query = session.query(self._entity_class)

            # Apply filters
            for field, value in kwargs.items():
                if hasattr(self._entity_class, field):
                    query = query.filter(getattr(self._entity_class, field) == value)

            # Apply content pack filter (default to active packs)
            query = self._apply_content_pack_filter(query)

            entities = query.all()
            models = [self._entity_to_model(entity) for entity in entities]
            return [model for model in models if model is not None]

    def exists(self, index: str) -> bool:
        """Check if an entity exists by index.

        Args:
            index: The unique identifier

        Returns:
            True if the entity exists
        """
        with self._database_manager.get_session() as session:
            from app.database.models import ContentPack

            return (
                session.query(self._entity_class)
                .join(ContentPack, self._entity_class.content_pack_id == ContentPack.id)
                .filter(
                    and_(
                        self._entity_class.index == index,
                        ContentPack.is_active,
                    )
                )
                .count()
                > 0
            )

    def count(self) -> int:
        """Get the total number of entities in this category.

        Returns:
            The entity count
        """
        with self._database_manager.get_session() as session:
            from app.database.models import ContentPack

            return (
                session.query(self._entity_class)
                .join(ContentPack, self._entity_class.content_pack_id == ContentPack.id)
                .filter(ContentPack.is_active)
                .count()
            )

    def get_indices(self) -> List[str]:
        """Get all unique indices in this category.

        Returns:
            List of all indices
        """
        with self._database_manager.get_session() as session:
            from app.database.models import ContentPack

            results = (
                session.query(self._entity_class.index)
                .join(ContentPack, self._entity_class.content_pack_id == ContentPack.id)
                .filter(ContentPack.is_active)
                .all()
            )
            return [result[0] for result in results]

    def get_names(self) -> List[str]:
        """Get all entity names in this category.

        Returns:
            List of all names
        """
        with self._database_manager.get_session() as session:
            from app.database.models import ContentPack

            results = (
                session.query(self._entity_class.name)
                .join(ContentPack, self._entity_class.content_pack_id == ContentPack.id)
                .filter(ContentPack.is_active)
                .all()
            )
            return [result[0] for result in results]
