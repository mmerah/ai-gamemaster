"""Service for indexing content with vector embeddings.

This module provides vector embedding generation for content entities,
enabling semantic search capabilities through the RAG system.
"""

import logging
from typing import Dict, Optional, Type

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.content.content_types import CONTENT_TYPE_TO_ENTITY
from app.content.models import (
    Background,
    BaseContent,
    CharacterClass,
    Equipment,
    Feat,
    Monster,
    Race,
    Spell,
)
from app.content.protocols import DatabaseManagerProtocol
from app.core.content_interfaces import IIndexingService
from app.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class IndexingService(IIndexingService):
    """Service for generating and updating vector embeddings for content.

    This service handles the generation of vector embeddings for content entities,
    enabling semantic search through the RAG system.
    """

    def __init__(
        self,
        database_manager: DatabaseManagerProtocol,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        """Initialize the indexing service.

        Args:
            database_manager: Database manager for session management
            model_name: Name of the sentence transformer model to use
        """
        self._database_manager = database_manager
        self._model_name = model_name
        self._model: Optional[SentenceTransformer] = None

    def _get_model(self) -> SentenceTransformer:
        """Get or initialize the sentence transformer model.

        Returns:
            The sentence transformer model
        """
        if self._model is None:
            logger.info(f"Loading sentence transformer model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def index_content_pack(self, content_pack_id: str) -> Dict[str, int]:
        """Generate embeddings for all content in a content pack.

        Args:
            content_pack_id: The content pack ID to index

        Returns:
            Dictionary mapping content types to number of items indexed
        """
        results = {}

        try:
            with self._database_manager.get_session() as session:
                # Process each content type
                for content_type, entity_class in CONTENT_TYPE_TO_ENTITY.items():
                    count = self._index_entity_type(
                        session, entity_class, content_pack_id
                    )
                    if count > 0:
                        results[content_type] = count

                session.commit()

            logger.info(
                f"Indexed content pack '{content_pack_id}': {sum(results.values())} total items"
            )
            return results

        except SQLAlchemyError as e:
            logger.error(f"Database error indexing content pack {content_pack_id}: {e}")
            raise DatabaseError(f"Failed to index content pack: {e}") from e

    def index_content_type(
        self, content_type: str, content_pack_id: Optional[str] = None
    ) -> int:
        """Generate embeddings for all content of a specific type.

        Args:
            content_type: The type of content to index
            content_pack_id: Optional content pack ID to filter by

        Returns:
            Number of items indexed
        """
        entity_class = CONTENT_TYPE_TO_ENTITY.get(content_type)
        if not entity_class:
            raise ValueError(f"Unknown content type: {content_type}")

        try:
            with self._database_manager.get_session() as session:
                count = self._index_entity_type(session, entity_class, content_pack_id)
                session.commit()

            logger.info(f"Indexed {count} {content_type} items")
            return count

        except SQLAlchemyError as e:
            logger.error(f"Database error indexing {content_type}: {e}")
            raise DatabaseError(f"Failed to index {content_type}: {e}") from e

    def update_entity_embedding(
        self, entity_class: Type[BaseContent], entity_index: str
    ) -> bool:
        """Update the embedding for a single entity.

        Args:
            entity_class: The entity class
            entity_index: The entity index/ID

        Returns:
            True if successful
        """
        try:
            with self._database_manager.get_session() as session:
                entity = (
                    session.query(entity_class).filter_by(index=entity_index).first()
                )
                if not entity:
                    logger.warning(
                        f"Entity not found: {entity_class.__name__} {entity_index}"
                    )
                    return False

                # Generate text representation
                text = self._create_content_text(entity)

                # Generate embedding
                model = self._get_model()
                embedding = model.encode(text, normalize_embeddings=True)

                # Update entity - the VECTOR TypeDecorator handles conversion to bytes
                entity.embedding = embedding.astype(np.float32)  # type: ignore[attr-defined]
                session.commit()

                return True

        except SQLAlchemyError as e:
            logger.error(f"Database error updating embedding: {e}")
            raise DatabaseError(f"Failed to update embedding: {e}") from e

    def _index_entity_type(
        self,
        session: Session,
        entity_class: Type[BaseContent],
        content_pack_id: Optional[str] = None,
    ) -> int:
        """Index all entities of a specific type.

        Args:
            session: Database session
            entity_class: The entity class to index
            content_pack_id: Optional content pack ID to filter by

        Returns:
            Number of items indexed
        """
        # Build query
        query = session.query(entity_class)
        if content_pack_id:
            query = query.filter_by(content_pack_id=content_pack_id)

        # Get entities without embeddings
        entities = query.filter(entity_class.embedding.is_(None)).all()

        if not entities:
            return 0

        # Generate text representations
        texts = [self._create_content_text(entity) for entity in entities]

        # Generate embeddings in batch
        model = self._get_model()
        embeddings = model.encode(
            texts, normalize_embeddings=True, show_progress_bar=True
        )

        # Update entities - the VECTOR TypeDecorator handles conversion to bytes
        for entity, embedding in zip(entities, embeddings):
            entity.embedding = embedding.astype(np.float32)

        return len(entities)

    def _create_content_text(self, entity: BaseContent) -> str:
        """Create a text representation of an entity for embedding.

        This method creates a structured text representation that captures
        the most important searchable aspects of each entity type.

        Args:
            entity: The entity to create text for

        Returns:
            Text representation of the entity
        """
        # Common fields
        parts = [f"Name: {entity.name}"]

        # Type-specific content
        if isinstance(entity, Spell):
            parts.extend(
                [
                    f"Level: {entity.level}",
                    f"School: {entity.school}",
                    f"Classes: {', '.join(entity.classes or [])}",
                    f"Description: {' '.join(entity.desc or [])}",
                ]
            )
            if entity.higher_level:
                parts.append(f"Higher Level: {' '.join(entity.higher_level)}")

        elif isinstance(entity, Monster):
            parts.extend(
                [
                    f"Type: {entity.type}",
                    f"Size: {entity.size}",
                    f"Challenge Rating: {entity.challenge_rating}",
                    f"Hit Points: {entity.hit_points}",
                ]
            )
            if hasattr(entity, "desc") and entity.desc:
                parts.append(f"Description: {entity.desc}")

        elif isinstance(entity, Equipment):
            parts.extend(
                [
                    f"Category: {entity.equipment_category}",
                ]
            )
            if entity.desc:
                parts.append(f"Description: {' '.join(entity.desc)}")
            if entity.weapon_category:
                parts.append(f"Weapon Category: {entity.weapon_category}")
            if entity.armor_category:
                parts.append(f"Armor Category: {entity.armor_category}")

        elif isinstance(entity, CharacterClass):
            parts.extend(
                [
                    f"Hit Die: {entity.hit_die}",
                ]
            )
            if hasattr(entity, "desc") and entity.desc:
                parts.append(f"Description: {entity.desc}")

        elif isinstance(entity, Race):
            if hasattr(entity, "desc") and entity.desc:
                parts.append(f"Description: {entity.desc}")
            if entity.size:
                parts.append(f"Size: {entity.size}")
            if entity.speed:
                parts.append(f"Speed: {entity.speed}")

        elif isinstance(entity, Feat):
            if entity.desc:
                parts.append(f"Description: {' '.join(entity.desc)}")
            if entity.prerequisites:
                parts.append(f"Prerequisites: {entity.prerequisites}")

        elif isinstance(entity, Background):
            if hasattr(entity, "desc") and entity.desc:
                parts.append(f"Description: {entity.desc}")
            if entity.feature:
                parts.append(f"Feature: {entity.feature['name']}")

        else:
            # Generic handling for other types
            if hasattr(entity, "desc"):
                desc = entity.desc
                if isinstance(desc, list):
                    desc = " ".join(desc)
                if desc:
                    parts.append(f"Description: {desc}")

        # Join all parts
        return " | ".join(parts)
