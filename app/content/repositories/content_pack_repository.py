"""Repository for managing content packs.

This module provides data access for content packs, which organize D&D content
into collections that can be activated/deactivated and prioritized.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import (
    AbilityScore,
    Alignment,
    Background,
    CharacterClass,
    Condition,
    ContentPack,
    DamageType,
    Equipment,
    EquipmentCategory,
    Feat,
    Feature,
    Language,
    Level,
    MagicItem,
    MagicSchool,
    Monster,
    Proficiency,
    Race,
    Rule,
    RuleSection,
    Skill,
    Spell,
    Subclass,
    Subrace,
    Trait,
    WeaponProperty,
)
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentPackWithStats,
    D5eContentPack,
)
from app.exceptions import (
    ContentPackNotFoundError,
    DatabaseError,
    DuplicateEntityError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# System pack IDs that cannot be deleted or deactivated
SYSTEM_PACK_IDS = {"dnd_5e_srd"}


class ContentPackRepository:
    """Repository for content pack management.

    Provides CRUD operations for content packs with protection for system packs.
    """

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the repository with database manager.

        Args:
            database_manager: Database manager for session management
        """
        self._database_manager = database_manager

    def get_by_id(self, pack_id: str) -> Optional[D5eContentPack]:
        """Get a content pack by ID.

        Args:
            pack_id: The content pack ID

        Returns:
            The content pack if found, None otherwise
        """
        try:
            with self._database_manager.get_session() as session:
                entity = session.query(ContentPack).filter_by(id=pack_id).first()
                return self._entity_to_model(entity) if entity else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting content pack {pack_id}: {e}")
            raise DatabaseError(f"Failed to get content pack: {e}") from e

    def get_all(self, active_only: bool = False) -> List[D5eContentPack]:
        """Get all content packs.

        Args:
            active_only: If True, only return active packs

        Returns:
            List of content packs
        """
        try:
            with self._database_manager.get_session() as session:
                query = session.query(ContentPack)
                if active_only:
                    query = query.filter_by(is_active=True)

                entities = query.order_by(ContentPack.name).all()
                return [self._entity_to_model(entity) for entity in entities]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting content packs: {e}")
            raise DatabaseError(f"Failed to get content packs: {e}") from e

    def get_by_author(self, author: str) -> List[D5eContentPack]:
        """Get all content packs by a specific author.

        Args:
            author: The author name

        Returns:
            List of content packs by the author
        """
        try:
            with self._database_manager.get_session() as session:
                entities = (
                    session.query(ContentPack)
                    .filter_by(author=author)
                    .order_by(ContentPack.name)
                    .all()
                )
                return [self._entity_to_model(entity) for entity in entities]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting packs by author {author}: {e}")
            raise DatabaseError(f"Failed to get packs by author: {e}") from e

    def create(self, pack_data: ContentPackCreate) -> D5eContentPack:
        """Create a new content pack.

        Args:
            pack_data: Data for creating the content pack

        Returns:
            The created content pack

        Raises:
            EntityAlreadyExistsError: If a pack with the same ID already exists
            ValidationError: If the pack data is invalid
        """
        try:
            with self._database_manager.get_session() as session:
                # Generate ID from name
                pack_id = self._generate_pack_id(pack_data.name)

                # Check if ID already exists
                existing = session.query(ContentPack).filter_by(id=pack_id).first()
                if existing:
                    raise DuplicateEntityError("ContentPack", pack_id)

                # Create new entity
                entity = ContentPack(
                    id=pack_id,
                    name=pack_data.name,
                    description=pack_data.description,
                    version=pack_data.version,
                    author=pack_data.author,
                    is_active=pack_data.is_active,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                session.add(entity)
                session.commit()
                session.refresh(entity)

                return self._entity_to_model(entity)
        except SQLAlchemyError as e:
            logger.error(f"Database error creating content pack: {e}")
            raise DatabaseError(f"Failed to create content pack: {e}") from e

    def update(self, pack_id: str, pack_data: ContentPackUpdate) -> D5eContentPack:
        """Update an existing content pack.

        Args:
            pack_id: The content pack ID
            pack_data: Data for updating the content pack

        Returns:
            The updated content pack

        Raises:
            ContentPackNotFoundError: If the pack doesn't exist
            ValidationError: If trying to update a system pack
        """
        try:
            with self._database_manager.get_session() as session:
                entity = session.query(ContentPack).filter_by(id=pack_id).first()
                if not entity:
                    raise ContentPackNotFoundError(pack_id)

                # Check if trying to deactivate a system pack
                if pack_id in SYSTEM_PACK_IDS and pack_data.is_active is False:
                    raise ValidationError(f"Cannot update system pack '{pack_id}'")

                # Update fields
                update_dict = pack_data.model_dump(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(entity, field, value)

                entity.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

                session.commit()
                session.refresh(entity)

                return self._entity_to_model(entity)
        except SQLAlchemyError as e:
            logger.error(f"Database error updating content pack {pack_id}: {e}")
            raise DatabaseError(f"Failed to update content pack: {e}") from e

    def activate(self, pack_id: str) -> D5eContentPack:
        """Activate a content pack.

        Args:
            pack_id: The content pack ID

        Returns:
            The activated content pack
        """
        return self.update(pack_id, ContentPackUpdate(is_active=True))

    def deactivate(self, pack_id: str) -> D5eContentPack:
        """Deactivate a content pack.

        Args:
            pack_id: The content pack ID

        Returns:
            The deactivated content pack

        Raises:
            ValidationError: If trying to deactivate a system pack
        """
        if pack_id in SYSTEM_PACK_IDS:
            raise ValidationError(f"Cannot deactivate system pack '{pack_id}'")

        return self.update(pack_id, ContentPackUpdate(is_active=False))

    def delete(self, pack_id: str) -> bool:
        """Delete a content pack and all its content.

        Args:
            pack_id: The content pack ID

        Returns:
            True if deleted successfully

        Raises:
            ContentPackNotFoundError: If the pack doesn't exist
            ValidationError: If trying to delete a system pack
        """
        if pack_id in SYSTEM_PACK_IDS:
            raise ValidationError(f"Cannot delete system pack '{pack_id}'")

        try:
            with self._database_manager.get_session() as session:
                entity = session.query(ContentPack).filter_by(id=pack_id).first()
                if not entity:
                    raise ContentPackNotFoundError(pack_id)

                # Delete the pack (cascade will delete all content)
                session.delete(entity)
                session.commit()

                return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting content pack {pack_id}: {e}")
            raise DatabaseError(f"Failed to delete content pack: {e}") from e

    def get_statistics(self, pack_id: str) -> ContentPackWithStats:
        """Get a content pack with statistics about its contents.

        Args:
            pack_id: The content pack ID

        Returns:
            Content pack with statistics

        Raises:
            ContentPackNotFoundError: If the pack doesn't exist
        """
        content_pack = self.get_by_id(pack_id)
        if not content_pack:
            raise ContentPackNotFoundError(pack_id)

        try:
            with self._database_manager.get_session() as session:
                # Count entities for each type
                statistics: Dict[str, int] = {
                    "spells": self._count_entities(session, Spell, pack_id),
                    "monsters": self._count_entities(session, Monster, pack_id),
                    "equipment": self._count_entities(session, Equipment, pack_id),
                    "magic_items": self._count_entities(session, MagicItem, pack_id),
                    "classes": self._count_entities(session, CharacterClass, pack_id),
                    "races": self._count_entities(session, Race, pack_id),
                    "backgrounds": self._count_entities(session, Background, pack_id),
                    "feats": self._count_entities(session, Feat, pack_id),
                    "features": self._count_entities(session, Feature, pack_id),
                    "traits": self._count_entities(session, Trait, pack_id),
                    "subraces": self._count_entities(session, Subrace, pack_id),
                    "subclasses": self._count_entities(session, Subclass, pack_id),
                    "ability_scores": self._count_entities(
                        session, AbilityScore, pack_id
                    ),
                    "skills": self._count_entities(session, Skill, pack_id),
                    "proficiencies": self._count_entities(
                        session, Proficiency, pack_id
                    ),
                    "languages": self._count_entities(session, Language, pack_id),
                    "alignments": self._count_entities(session, Alignment, pack_id),
                    "conditions": self._count_entities(session, Condition, pack_id),
                    "damage_types": self._count_entities(session, DamageType, pack_id),
                    "equipment_categories": self._count_entities(
                        session, EquipmentCategory, pack_id
                    ),
                    "levels": self._count_entities(session, Level, pack_id),
                    "magic_schools": self._count_entities(
                        session, MagicSchool, pack_id
                    ),
                    "rules": self._count_entities(session, Rule, pack_id),
                    "rule_sections": self._count_entities(
                        session, RuleSection, pack_id
                    ),
                    "weapon_properties": self._count_entities(
                        session, WeaponProperty, pack_id
                    ),
                }

                # Calculate total
                total = sum(statistics.values())
                statistics["total"] = total

                return ContentPackWithStats(
                    **content_pack.model_dump(), statistics=statistics
                )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting pack statistics: {e}")
            raise DatabaseError(f"Failed to get pack statistics: {e}") from e

    def _count_entities(
        self, session: Session, entity_class: type, pack_id: str
    ) -> int:
        """Count entities of a given type in a content pack.

        Args:
            session: The database session
            entity_class: The entity class to count
            pack_id: The content pack ID

        Returns:
            Number of entities
        """
        return session.query(entity_class).filter_by(content_pack_id=pack_id).count()

    def _entity_to_model(self, entity: ContentPack) -> D5eContentPack:
        """Convert a SQLAlchemy entity to a Pydantic model.

        Args:
            entity: The SQLAlchemy entity

        Returns:
            The Pydantic model
        """
        return D5eContentPack.model_validate(entity)

    def _generate_pack_id(self, name: str) -> str:
        """Generate a pack ID from a name.

        Args:
            name: The pack name

        Returns:
            A valid pack ID
        """
        # Convert to lowercase, replace spaces with underscores, remove special chars
        pack_id = name.lower().replace(" ", "_")
        # Keep only alphanumeric and underscore
        pack_id = "".join(c for c in pack_id if c.isalnum() or c == "_")
        return pack_id
