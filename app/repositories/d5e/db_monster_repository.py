"""Database-backed specialized repository for D&D 5e monsters.

This module provides advanced monster-specific queries using SQLAlchemy.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import DatabaseManager
from app.database.models import ContentPack, Monster
from app.exceptions import DatabaseError, ValidationError
from app.models.d5e import D5eMonster
from app.repositories.d5e.db_base_repository import BaseD5eDbRepository

logger = logging.getLogger(__name__)


class DbMonsterRepository(BaseD5eDbRepository[D5eMonster]):
    """Database-backed repository for accessing monster data with specialized queries."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the monster repository."""
        super().__init__(
            model_class=D5eMonster,
            entity_class=Monster,
            database_manager=database_manager,
        )

    def get_by_challenge_rating(
        self, cr: float, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get all monsters with a specific challenge rating.

        Args:
            cr: The challenge rating
            resolve_references: Whether to resolve references

        Returns:
            List of monsters with the specified CR
        """
        return self.filter_by(challenge_rating=cr)

    def get_by_cr_range(
        self, min_cr: float, max_cr: float, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get monsters within a challenge rating range.

        Args:
            min_cr: Minimum challenge rating (inclusive)
            max_cr: Maximum challenge rating (inclusive)
            resolve_references: Whether to resolve references

        Returns:
            List of monsters within the CR range
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        return [
            monster
            for monster in all_monsters
            if min_cr <= monster.challenge_rating <= max_cr
        ]

    def get_by_type(
        self, monster_type: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get all monsters of a specific type.

        Args:
            monster_type: The monster type (e.g., 'dragon', 'undead', 'humanoid')
            resolve_references: Whether to resolve references

        Returns:
            List of monsters of the specified type
        """
        try:
            with self._database_manager.get_session() as session:
                self._current_session = session

                query = (
                    session.query(Monster)
                    .join(ContentPack, Monster.content_pack_id == ContentPack.id)
                    .filter(
                        and_(
                            ContentPack.is_active,
                            func.lower(Monster.type).contains(func.lower(monster_type)),
                        )
                    )
                )

                entities = query.all()
                models: List[D5eMonster] = []
                for entity in entities:
                    try:
                        model = self._entity_to_model(entity)
                        if model is not None:
                            models.append(model)
                    except ValidationError as e:
                        logger.warning(
                            f"Skipping invalid monster entity during type filter: {e}"
                        )
                return models
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting monsters by type '{monster_type}': {e}",
                extra={"monster_type": monster_type, "error": str(e)},
            )
            raise DatabaseError(
                "Failed to get monsters by type",
                details={"monster_type": monster_type, "error": str(e)},
            )

    def get_by_size(
        self, size: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get all monsters of a specific size.

        Args:
            size: The size category (e.g., 'Large', 'Medium', 'Tiny')
            resolve_references: Whether to resolve references

        Returns:
            List of monsters of the specified size
        """
        return self.filter_by(size=size)

    def get_by_alignment(
        self, alignment: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get all monsters with a specific alignment.

        Args:
            alignment: The alignment (e.g., 'chaotic evil', 'lawful good')
            resolve_references: Whether to resolve references

        Returns:
            List of monsters with the specified alignment
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        alignment_lower = alignment.lower()
        return [
            monster
            for monster in all_monsters
            if alignment_lower in monster.alignment.lower()
        ]

    def get_by_environment(
        self, environment: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get monsters that can be found in a specific environment.

        Note: The base 5e-database doesn't include environment data,
        so this would need to be added via metadata or custom fields.

        Args:
            environment: The environment type
            resolve_references: Whether to resolve references

        Returns:
            List of monsters from that environment
        """
        # Placeholder - would need environment data in the source
        return []

    def get_legendary_monsters(
        self, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get all monsters with legendary actions.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of legendary monsters
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        return [
            monster
            for monster in all_monsters
            if monster.legendary_actions is not None
            and len(monster.legendary_actions) > 0
        ]

    def get_by_damage_immunity(
        self, damage_type: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get monsters immune to a specific damage type.

        Args:
            damage_type: The damage type (e.g., 'fire', 'poison')
            resolve_references: Whether to resolve references

        Returns:
            List of monsters immune to that damage type
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        damage_type_lower = damage_type.lower()
        return [
            monster
            for monster in all_monsters
            if any(
                damage_type_lower in immunity.lower()
                for immunity in monster.damage_immunities
            )
        ]

    def get_by_damage_resistance(
        self, damage_type: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get monsters resistant to a specific damage type.

        Args:
            damage_type: The damage type
            resolve_references: Whether to resolve references

        Returns:
            List of monsters resistant to that damage type
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        damage_type_lower = damage_type.lower()
        return [
            monster
            for monster in all_monsters
            if any(
                damage_type_lower in resistance.lower()
                for resistance in monster.damage_resistances
            )
        ]

    def get_by_speed_type(
        self, speed_type: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Get monsters with a specific movement type.

        Args:
            speed_type: The speed type (e.g., 'fly', 'swim', 'burrow')
            resolve_references: Whether to resolve references

        Returns:
            List of monsters with that movement type
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        results = []

        for monster in all_monsters:
            # Check if the MonsterSpeed object has the requested attribute
            if (
                hasattr(monster.speed, speed_type)
                and getattr(monster.speed, speed_type) is not None
            ):
                results.append(monster)

        return results

    def get_spellcasters(self, resolve_references: bool = False) -> List[D5eMonster]:
        """Get all monsters that can cast spells.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of spellcasting monsters
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        results = []

        for monster in all_monsters:
            # Check special abilities for spellcasting
            if monster.special_abilities:
                has_spellcasting = any(
                    "spellcasting" in ability.name.lower()
                    for ability in monster.special_abilities
                )
                if has_spellcasting:
                    results.append(monster)

        return results

    def get_cr_distribution(self) -> Dict[float, int]:
        """Get the distribution of monsters by challenge rating.

        Returns:
            Dictionary mapping CR to count of monsters
        """
        try:
            with self._database_manager.get_session() as session:
                results = (
                    session.query(Monster.challenge_rating, func.count(Monster.index))
                    .join(ContentPack, Monster.content_pack_id == ContentPack.id)
                    .filter(ContentPack.is_active)
                    .group_by(Monster.challenge_rating)
                    .all()
                )

                return dict(sorted((float(cr), count) for cr, count in results))
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting CR distribution: {e}",
                extra={"error": str(e)},
            )
            raise DatabaseError(
                "Failed to get challenge rating distribution",
                details={"error": str(e)},
            )

    def get_type_distribution(self) -> Dict[str, int]:
        """Get the distribution of monsters by type.

        Returns:
            Dictionary mapping type to count of monsters
        """
        all_monsters = self.list_all_with_options(resolve_references=False)
        distribution: Dict[str, int] = {}

        for monster in all_monsters:
            # Extract base type (before parentheses)
            base_type = monster.type.split("(")[0].strip().lower()
            distribution[base_type] = distribution.get(base_type, 0) + 1

        return dict(sorted(distribution.items()))

    def get_available_types(self) -> Set[str]:
        """Get all unique monster types.

        Returns:
            Set of monster types
        """
        all_monsters = self.list_all_with_options(resolve_references=False)
        types = set()

        for monster in all_monsters:
            # Extract base type
            base_type = monster.type.split("(")[0].strip()
            types.add(base_type)

        return types

    def get_available_sizes(self) -> Set[str]:
        """Get all unique monster sizes.

        Returns:
            Set of size categories
        """
        try:
            with self._database_manager.get_session() as session:
                results = (
                    session.query(func.distinct(Monster.size))
                    .join(ContentPack, Monster.content_pack_id == ContentPack.id)
                    .filter(ContentPack.is_active)
                    .all()
                )

                return {result[0] for result in results if result[0] is not None}
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting available sizes: {e}",
                extra={"error": str(e)},
            )
            raise DatabaseError(
                "Failed to get available sizes",
                details={"error": str(e)},
            )

    def get_cr_range(self) -> Tuple[float, float]:
        """Get the minimum and maximum challenge ratings.

        Returns:
            Tuple of (min_cr, max_cr)
        """
        try:
            with self._database_manager.get_session() as session:
                result = (
                    session.query(
                        func.min(Monster.challenge_rating),
                        func.max(Monster.challenge_rating),
                    )
                    .join(ContentPack, Monster.content_pack_id == ContentPack.id)
                    .filter(ContentPack.is_active)
                    .first()
                )

                if result and result[0] is not None and result[1] is not None:
                    return (float(result[0]), float(result[1]))
                return (0.0, 0.0)
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting CR range: {e}",
                extra={"error": str(e)},
            )
            raise DatabaseError(
                "Failed to get challenge rating range",
                details={"error": str(e)},
            )

    def search_abilities(
        self, keyword: str, resolve_references: bool = False
    ) -> List[D5eMonster]:
        """Search for monsters with abilities containing a keyword.

        Args:
            keyword: The keyword to search for (case-insensitive)
            resolve_references: Whether to resolve references

        Returns:
            List of monsters with matching abilities
        """
        all_monsters = self.list_all_with_options(resolve_references=resolve_references)
        keyword_lower = keyword.lower()
        results = []

        for monster in all_monsters:
            found = False

            # Check actions
            if monster.actions:
                for action in monster.actions:
                    if (
                        keyword_lower in action.name.lower()
                        or keyword_lower in action.desc.lower()
                    ):
                        found = True
                        break

            # Check special abilities
            if not found and monster.special_abilities:
                for ability in monster.special_abilities:
                    if (
                        keyword_lower in ability.name.lower()
                        or keyword_lower in ability.desc.lower()
                    ):
                        found = True
                        break

            # Check legendary actions
            if not found and monster.legendary_actions:
                for action in monster.legendary_actions:
                    if (
                        keyword_lower in action.name.lower()
                        or keyword_lower in action.desc.lower()
                    ):
                        found = True
                        break

            if found:
                results.append(monster)

        return results
