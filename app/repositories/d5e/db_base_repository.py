"""Database-aware base repository for D&D 5e data access.

This module provides a generic repository pattern that all specific D5e repositories
can inherit from. It handles common operations like getting by index, searching,
and filtering while using SQLAlchemy to query the database directly.
"""

import logging
import threading
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.d5e_interfaces import D5eRepositoryProtocol
from app.database.connection import DatabaseManager
from app.database.models import BaseContent
from app.exceptions import (
    ContentPackNotFoundError,
    DatabaseError,
    EntityNotFoundError,
    SessionError,
    ValidationError,
)

logger = logging.getLogger(__name__)

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

    # Class-level cache for field mappings to improve performance
    _field_mapping_cache: Dict[Type[BaseModel], Dict[str, str]] = {}
    _json_fields_cache: Dict[Type[BaseModel], set[str]] = {}

    # Thread lock for safe cache initialization
    _cache_init_lock = threading.Lock()

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

        # Pre-cache field mappings for this model type
        self._init_field_mappings()

    def _init_field_mappings(self) -> None:
        """Initialize field mapping cache for this model type.

        Thread-safe initialization using double-checked locking pattern.
        """
        if self._model_class not in self._field_mapping_cache:
            # Acquire lock for thread-safe cache initialization
            with self._cache_init_lock:
                # Double-check inside lock to prevent race conditions
                if self._model_class not in self._field_mapping_cache:
                    # Build field mappings based on model type
                    mappings: Dict[str, str] = {}
                    json_fields: set[str] = {
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
                        "spells",  # For subclasses
                        "race",  # For traits
                    }

                    # Import here to avoid circular imports
                    from app.models.d5e.character import D5eClass, D5eSubclass
                    from app.models.d5e.progression import D5eFeature

                    # Add model-specific mappings
                    if self._model_class == D5eFeature:
                        mappings["class_ref"] = "class"
                    elif self._model_class == D5eSubclass:
                        mappings["class_ref"] = "class"

                    self._field_mapping_cache[self._model_class] = mappings
                    self._json_fields_cache[self._model_class] = json_fields

    def _get_session(self) -> Session:
        """Get a database session from the context manager.

        Raises:
            SessionError: If no session is available
        """
        # This method is called within a context that already has a session
        # The actual session management happens in the public methods
        if not hasattr(self, "_current_session") or not self._current_session:
            raise SessionError("No active database session")
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

        This method ensures that:
        1. Only column data is extracted (no lazy-loaded relationships)
        2. Data is properly validated through Pydantic
        3. No SQLAlchemy objects escape the repository boundary

        Args:
            entity: The SQLAlchemy entity

        Returns:
            The Pydantic model instance, or None if validation fails
        """
        try:
            # Convert the entity to a dictionary, extracting only column values
            # This prevents any relationship attributes from being accessed
            data = {}
            for column in entity.__table__.columns:
                # Get column value directly to avoid lazy loading
                value = getattr(entity, column.name)

                # Ensure we don't have any SQLAlchemy objects
                if hasattr(value, "__table__"):
                    logger.warning(
                        f"Skipping SQLAlchemy object in column {column.name} "
                        f"for {self._model_class.__name__}"
                    )
                    continue

                data[column.name] = value

            # Remove database-specific fields
            data.pop("content_pack_id", None)

            # Apply field name mappings for specific model types
            data = self._apply_field_mappings(data)

            # Create and return the model
            # This ensures complete validation and no SQLAlchemy objects remain
            model = self._model_class(**data)

            # Validate model purity in debug mode
            if self._should_validate_model_purity():
                self._validate_model_purity(model)

            # Explicitly detach from any SQLAlchemy session
            # by returning a fresh model instance
            return model

        except Exception as e:
            # Log validation errors and raise specific exception
            entity_id = getattr(entity, "index", "unknown")
            entity_name = getattr(entity, "name", "unknown")
            logger.error(
                f"Failed to convert {self._model_class.__name__} entity '{entity_id}' to model: {e}",
                extra={
                    "entity_type": self._model_class.__name__,
                    "entity_id": entity_id,
                    "entity_name": entity_name,
                    "error": str(e),
                },
            )
            raise ValidationError(
                f"Failed to validate {self._model_class.__name__} '{entity_name}'",
                field="entity",
                value=entity_id,
            )

    def _apply_field_mappings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field name mappings between database and Pydantic models.

        Uses cached field mappings for performance.

        Args:
            data: The raw database data

        Returns:
            The data with field names mapped for Pydantic validation
        """
        # Parse JSON string fields into Python objects
        self._parse_json_fields(data)

        # Apply cached field mappings
        mappings = self._field_mapping_cache.get(self._model_class, {})
        for db_field, model_field in mappings.items():
            if db_field in data:
                data[model_field] = data.pop(db_field)

        return data

    def _parse_json_fields(self, data: Dict[str, Any]) -> None:
        """Parse JSON string fields into Python objects.

        Uses cached JSON field list for performance.

        Args:
            data: The raw database data to modify in place
        """
        import json

        # Use cached JSON fields
        json_fields = self._json_fields_cache.get(self._model_class, set())

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

    def _should_validate_model_purity(self) -> bool:
        """Check if model purity validation should be performed.

        Returns:
            True if running in debug mode, False otherwise
        """
        # Check multiple possible debug indicators
        import os

        # Check for common debug environment variables
        debug_env = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
        app_debug = os.getenv("APP_DEBUG", "").lower() in ("true", "1", "yes")
        flask_debug = os.getenv("FLASK_DEBUG", "").lower() in ("true", "1", "yes")

        # Also check if we're in a test environment
        testing = os.getenv("TESTING", "").lower() in ("true", "1", "yes")
        pytest_current_test = os.getenv("PYTEST_CURRENT_TEST") is not None

        return any([debug_env, app_debug, flask_debug, testing, pytest_current_test])

    def _validate_model_purity(self, model: TModel) -> TModel:
        """Validate that the model has no references to SQLAlchemy objects.

        This is a safety check to ensure complete separation between
        the data layer and domain layer. Only runs in debug/test mode
        for performance reasons.

        Args:
            model: The Pydantic model to check

        Returns:
            The same model (for chaining)

        Raises:
            ValidationError: If SQLAlchemy objects are detected
        """
        # Pydantic models are already pure Python objects
        # This method serves as documentation and a safety checkpoint
        model_dict = model.model_dump()
        for field_name, value in model_dict.items():
            if hasattr(value, "__table__"):
                raise ValidationError(
                    f"SQLAlchemy object leaked in field '{field_name}'",
                    field=field_name,
                    value=str(type(value)),
                )
        return model

    def get_by_index(self, index: str) -> Optional[TModel]:
        """Get an entity by its unique index.

        Args:
            index: The unique identifier

        Returns:
            The entity if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
            ValidationError: If entity validation fails
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
        try:
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
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting {self._model_class.__name__} by index '{index}': {e}",
                extra={
                    "entity_type": self._model_class.__name__,
                    "index": index,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to retrieve {self._model_class.__name__} by index",
                details={"index": index, "error": str(e)},
            )

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
        try:
            with self._database_manager.get_session() as session:
                self._current_session = session

                entity = self._find_by_name_with_priority(
                    session, name, content_pack_priority
                )
                if entity:
                    return self._entity_to_model(entity)
                return None
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting {self._model_class.__name__} by name '{name}': {e}",
                extra={
                    "entity_type": self._model_class.__name__,
                    "name": name,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to retrieve {self._model_class.__name__} by name",
                details={"name": name, "error": str(e)},
            )

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
        try:
            with self._database_manager.get_session() as session:
                self._current_session = session

                query = session.query(self._entity_class)
                query = self._apply_content_pack_filter(query, content_pack_priority)

                entities = query.all()
                models: List[TModel] = []
                for entity in entities:
                    try:
                        model = self._entity_to_model(entity)
                        if model is not None:
                            models.append(model)
                    except ValidationError as e:
                        # Log but continue processing other entities
                        logger.warning(
                            f"Skipping invalid {self._model_class.__name__} entity: {e}"
                        )
                return models
        except SQLAlchemyError as e:
            logger.error(
                f"Database error listing all {self._model_class.__name__}: {e}",
                extra={"entity_type": self._model_class.__name__, "error": str(e)},
            )
            raise DatabaseError(
                f"Failed to list {self._model_class.__name__} entities",
                details={"error": str(e)},
            )

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
        try:
            with self._database_manager.get_session() as session:
                self._current_session = session

                db_query = session.query(self._entity_class).filter(
                    self._entity_class.name.ilike(f"%{query}%")
                )
                db_query = self._apply_content_pack_filter(
                    db_query, content_pack_priority
                )

                entities = db_query.all()
                models: List[TModel] = []
                for entity in entities:
                    try:
                        model = self._entity_to_model(entity)
                        if model is not None:
                            models.append(model)
                    except ValidationError as e:
                        # Log but continue processing other entities
                        logger.warning(
                            f"Skipping invalid {self._model_class.__name__} entity during search: {e}"
                        )
                return models
        except SQLAlchemyError as e:
            logger.error(
                f"Database error searching {self._model_class.__name__} with query '{query}': {e}",
                extra={
                    "entity_type": self._model_class.__name__,
                    "query": query,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to search {self._model_class.__name__} entities",
                details={"query": query, "error": str(e)},
            )

    def filter_by(self, **kwargs: Any) -> List[TModel]:
        """Filter entities by field values.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            List of matching entities
        """
        try:
            with self._database_manager.get_session() as session:
                self._current_session = session

                query = session.query(self._entity_class)

                # Apply filters
                for field, value in kwargs.items():
                    if hasattr(self._entity_class, field):
                        query = query.filter(
                            getattr(self._entity_class, field) == value
                        )
                    else:
                        raise ValidationError(
                            f"Invalid filter field '{field}' for {self._model_class.__name__}",
                            field=field,
                        )

                # Apply content pack filter (default to active packs)
                query = self._apply_content_pack_filter(query)

                entities = query.all()
                models: List[TModel] = []
                for entity in entities:
                    try:
                        model = self._entity_to_model(entity)
                        if model is not None:
                            models.append(model)
                    except ValidationError as e:
                        # Log but continue processing other entities
                        logger.warning(
                            f"Skipping invalid {self._model_class.__name__} entity during filter: {e}"
                        )
                return models
        except SQLAlchemyError as e:
            logger.error(
                f"Database error filtering {self._model_class.__name__}: {e}",
                extra={
                    "entity_type": self._model_class.__name__,
                    "filters": kwargs,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to filter {self._model_class.__name__} entities",
                details={"filters": kwargs, "error": str(e)},
            )

    def exists(self, index: str) -> bool:
        """Check if an entity exists by index.

        Args:
            index: The unique identifier

        Returns:
            True if the entity exists

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self._database_manager.get_session() as session:
                from app.database.models import ContentPack

                return (
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
                    .count()
                    > 0
                )
        except SQLAlchemyError as e:
            logger.error(
                f"Database error checking existence of {self._model_class.__name__} '{index}': {e}",
                extra={
                    "entity_type": self._model_class.__name__,
                    "index": index,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to check existence of {self._model_class.__name__}",
                details={"index": index, "error": str(e)},
            )

    def count(self) -> int:
        """Get the total number of entities in this category.

        Returns:
            The entity count

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self._database_manager.get_session() as session:
                from app.database.models import ContentPack

                return (
                    session.query(self._entity_class)
                    .join(
                        ContentPack,
                        self._entity_class.content_pack_id == ContentPack.id,
                    )
                    .filter(ContentPack.is_active)
                    .count()
                )
        except SQLAlchemyError as e:
            logger.error(
                f"Database error counting {self._model_class.__name__} entities: {e}",
                extra={"entity_type": self._model_class.__name__, "error": str(e)},
            )
            raise DatabaseError(
                f"Failed to count {self._model_class.__name__} entities",
                details={"error": str(e)},
            )

    def get_indices(self) -> List[str]:
        """Get all unique indices in this category.

        Returns:
            List of all indices

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self._database_manager.get_session() as session:
                from app.database.models import ContentPack

                results = (
                    session.query(self._entity_class.index)
                    .join(
                        ContentPack,
                        self._entity_class.content_pack_id == ContentPack.id,
                    )
                    .filter(ContentPack.is_active)
                    .all()
                )
                return [result[0] for result in results]
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting indices for {self._model_class.__name__}: {e}",
                extra={"entity_type": self._model_class.__name__, "error": str(e)},
            )
            raise DatabaseError(
                f"Failed to get indices for {self._model_class.__name__}",
                details={"error": str(e)},
            )

    def get_names(self) -> List[str]:
        """Get all entity names in this category.

        Returns:
            List of all names

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self._database_manager.get_session() as session:
                from app.database.models import ContentPack

                results = (
                    session.query(self._entity_class.name)
                    .join(
                        ContentPack,
                        self._entity_class.content_pack_id == ContentPack.id,
                    )
                    .filter(ContentPack.is_active)
                    .all()
                )
                return [result[0] for result in results]
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting names for {self._model_class.__name__}: {e}",
                extra={"entity_type": self._model_class.__name__, "error": str(e)},
            )
            raise DatabaseError(
                f"Failed to get names for {self._model_class.__name__}",
                details={"error": str(e)},
            )
