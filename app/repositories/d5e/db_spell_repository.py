"""Database-backed specialized repository for D&D 5e spells.

This module provides advanced spell-specific queries using SQLAlchemy.
"""

import logging
from typing import List, Optional, Set

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import DatabaseManager
from app.database.models import ContentPack, Spell
from app.exceptions import DatabaseError, ValidationError
from app.models.d5e import D5eSpell
from app.repositories.d5e.db_base_repository import BaseD5eDbRepository

logger = logging.getLogger(__name__)


class DbSpellRepository(BaseD5eDbRepository[D5eSpell]):
    """Database-backed repository for accessing spell data with specialized queries."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the spell repository."""
        super().__init__(
            model_class=D5eSpell,
            entity_class=Spell,
            database_manager=database_manager,
        )

    def get_by_level(
        self, level: int, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all spells of a specific level.

        Args:
            level: The spell level (0 for cantrips, 1-9 for leveled spells)
            resolve_references: Whether to resolve references

        Returns:
            List of spells at the specified level
        """
        return self.filter_by(level=level)

    def get_by_school(
        self, school_index: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all spells from a specific school of magic.

        Args:
            school_index: The school index (e.g., 'evocation', 'necromancy')
            resolve_references: Whether to resolve references

        Returns:
            List of spells from the specified school
        """
        try:
            with self._database_manager.get_session() as session:
                self._current_session = session

                # Query spells where the school JSON contains the given index
                query = (
                    session.query(Spell)
                    .join(ContentPack, Spell.content_pack_id == ContentPack.id)
                    .filter(
                        and_(
                            ContentPack.is_active,
                            func.json_extract(Spell.school, "$.index") == school_index,
                        )
                    )
                )

                entities = query.all()
                models: List[D5eSpell] = []
                for entity in entities:
                    try:
                        model = self._entity_to_model(entity)
                        if model is not None:
                            models.append(model)
                    except ValidationError as e:
                        logger.warning(
                            f"Skipping invalid spell entity during school filter: {e}"
                        )
                return models
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting spells by school '{school_index}': {e}",
                extra={"school_index": school_index, "error": str(e)},
            )
            raise DatabaseError(
                "Failed to get spells by school",
                details={"school_index": school_index, "error": str(e)},
            )

    def get_by_class(
        self, class_index: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all spells available to a specific class.

        Args:
            class_index: The class index (e.g., 'wizard', 'cleric')
            resolve_references: Whether to resolve references

        Returns:
            List of spells available to the class
        """
        try:
            # Get all spells and filter in Python for now
            # TODO: Optimize with proper JSON SQL query when moving to PostgreSQL
            all_spells = self.list_all_with_options(
                resolve_references=resolve_references
            )
            return [
                spell
                for spell in all_spells
                if any(cls.index == class_index for cls in spell.classes)
            ]
        except Exception as e:
            logger.error(
                f"Error getting spells by class '{class_index}': {e}",
                extra={"class_index": class_index, "error": str(e)},
            )
            raise DatabaseError(
                "Failed to get spells by class",
                details={"class_index": class_index, "error": str(e)},
            )

    def get_by_class_and_level(
        self, class_index: str, level: int, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get spells available to a class at a specific level.

        Args:
            class_index: The class index
            level: The spell level
            resolve_references: Whether to resolve references

        Returns:
            List of matching spells
        """
        class_spells = self.get_by_class(class_index, resolve_references)
        return [spell for spell in class_spells if spell.level == level]

    def get_ritual_spells(self, resolve_references: bool = False) -> List[D5eSpell]:
        """Get all ritual spells.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of ritual spells
        """
        return self.filter_by(ritual=True)

    def get_concentration_spells(
        self, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get all concentration spells.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of concentration spells
        """
        return self.filter_by(concentration=True)

    def get_by_components(
        self,
        verbal: Optional[bool] = None,
        somatic: Optional[bool] = None,
        material: Optional[bool] = None,
        resolve_references: bool = False,
    ) -> List[D5eSpell]:
        """Get spells filtered by component requirements.

        Args:
            verbal: If specified, filter by verbal component requirement
            somatic: If specified, filter by somatic component requirement
            material: If specified, filter by material component requirement
            resolve_references: Whether to resolve references

        Returns:
            List of spells matching component criteria
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        results = []

        for spell in all_spells:
            # Check each component requirement if specified
            if verbal is not None and ("V" in spell.components) != verbal:
                continue
            if somatic is not None and ("S" in spell.components) != somatic:
                continue
            if material is not None and ("M" in spell.components) != material:
                continue

            results.append(spell)

        return results

    def get_by_casting_time(
        self, casting_time: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get spells with a specific casting time.

        Args:
            casting_time: The casting time (e.g., '1 action', '1 bonus action')
            resolve_references: Whether to resolve references

        Returns:
            List of spells with the specified casting time
        """
        with self._database_manager.get_session() as session:
            query = (
                session.query(Spell)
                .join(ContentPack, Spell.content_pack_id == ContentPack.id)
                .filter(
                    and_(
                        ContentPack.is_active,
                        func.lower(Spell.casting_time) == func.lower(casting_time),
                    )
                )
            )

            entities = query.all()
            models = [self._entity_to_model(entity) for entity in entities]
            return [model for model in models if model is not None]

    def get_by_range(
        self, range_str: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Get spells with a specific range.

        Args:
            range_str: The range (e.g., 'Self', 'Touch', '120 feet')
            resolve_references: Whether to resolve references

        Returns:
            List of spells with the specified range
        """
        with self._database_manager.get_session() as session:
            query = (
                session.query(Spell)
                .join(ContentPack, Spell.content_pack_id == ContentPack.id)
                .filter(
                    and_(
                        ContentPack.is_active,
                        func.lower(Spell.range) == func.lower(range_str),
                    )
                )
            )

            entities = query.all()
            models = [self._entity_to_model(entity) for entity in entities]
            return [model for model in models if model is not None]

    def get_available_schools(self) -> Set[str]:
        """Get all unique spell schools.

        Returns:
            Set of school indices
        """
        with self._database_manager.get_session() as session:
            results = (
                session.query(func.distinct(func.json_extract(Spell.school, "$.index")))
                .join(ContentPack, Spell.content_pack_id == ContentPack.id)
                .filter(ContentPack.is_active)
                .all()
            )

            return {result[0] for result in results if result[0] is not None}

    def get_max_level(self) -> int:
        """Get the highest spell level available.

        Returns:
            The maximum spell level (typically 9)
        """
        with self._database_manager.get_session() as session:
            result = (
                session.query(func.max(Spell.level))
                .join(ContentPack, Spell.content_pack_id == ContentPack.id)
                .filter(ContentPack.is_active)
                .scalar()
            )

            return result or 0

    def search_by_description(
        self, keyword: str, resolve_references: bool = False
    ) -> List[D5eSpell]:
        """Search for spells containing a keyword in their description.

        Args:
            keyword: The keyword to search for (case-insensitive)
            resolve_references: Whether to resolve references

        Returns:
            List of spells containing the keyword in their description
        """
        all_spells = self.list_all_with_options(resolve_references=resolve_references)
        keyword_lower = keyword.lower()

        results = []
        for spell in all_spells:
            # Check main description
            if any(keyword_lower in desc.lower() for desc in spell.desc):
                results.append(spell)
                continue

            # Check higher level description if present
            if spell.higher_level and any(
                keyword_lower in desc.lower() for desc in spell.higher_level
            ):
                results.append(spell)

        return results
