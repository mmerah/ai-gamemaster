"""Database-backed specialized repository for D&D 5e equipment.

This module provides advanced equipment-specific queries using SQLAlchemy.
"""

import logging
from typing import List, Optional, Set

from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError

from app.content.models import ContentPack, Equipment, MagicItem, WeaponProperty
from app.content.protocols import DatabaseManagerProtocol
from app.content.repositories.db_base_repository import BaseD5eDbRepository
from app.content.schemas import D5eEquipment, D5eMagicItem, D5eWeaponProperty
from app.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class DbEquipmentRepository(BaseD5eDbRepository[D5eEquipment]):
    """Database-backed repository for accessing equipment data with specialized queries."""

    def __init__(self, database_manager: DatabaseManagerProtocol) -> None:
        """Initialize the equipment repository."""
        super().__init__(
            model_class=D5eEquipment,
            entity_class=Equipment,
            database_manager=database_manager,
        )

        # Also create repositories for related data
        self._magic_item_repo = BaseD5eDbRepository[D5eMagicItem](
            model_class=D5eMagicItem,
            entity_class=MagicItem,
            database_manager=database_manager,
        )

        self._weapon_property_repo = BaseD5eDbRepository[D5eWeaponProperty](
            model_class=D5eWeaponProperty,
            entity_class=WeaponProperty,
            database_manager=database_manager,
        )

    def get_weapons(self, resolve_references: bool = False) -> List[D5eEquipment]:
        """Get all weapons.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of weapon equipment

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            all_equipment = self.list_all_with_options(
                resolve_references=resolve_references
            )
            return [item for item in all_equipment if item.weapon_category is not None]
        except Exception as e:
            logger.error(
                f"Error getting weapons: {e}",
                extra={"error": str(e)},
            )
            raise DatabaseError(
                "Failed to get weapons",
                details={"error": str(e)},
            )

    def get_armor(self, resolve_references: bool = False) -> List[D5eEquipment]:
        """Get all armor.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of armor equipment

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            all_equipment = self.list_all_with_options(
                resolve_references=resolve_references
            )
            return [item for item in all_equipment if item.armor_category is not None]
        except Exception as e:
            logger.error(
                f"Error getting armor: {e}",
                extra={"error": str(e)},
            )
            raise DatabaseError(
                "Failed to get armor",
                details={"error": str(e)},
            )

    def get_by_category(
        self, category_index: str, resolve_references: bool = False
    ) -> List[D5eEquipment]:
        """Get equipment by category.

        Args:
            category_index: The equipment category index
            resolve_references: Whether to resolve references

        Returns:
            List of equipment in that category
        """
        all_equipment = self.list_all_with_options(
            resolve_references=resolve_references
        )
        return [
            item
            for item in all_equipment
            if item.equipment_category.index == category_index
        ]

    def get_weapons_by_category(
        self, weapon_category: str, resolve_references: bool = False
    ) -> List[D5eEquipment]:
        """Get weapons of a specific category.

        Args:
            weapon_category: The weapon category (e.g., 'Simple', 'Martial')
            resolve_references: Whether to resolve references

        Returns:
            List of weapons in that category
        """
        weapons = self.get_weapons(resolve_references=resolve_references)
        return [
            weapon
            for weapon in weapons
            if weapon.weapon_category
            and weapon.weapon_category.lower() == weapon_category.lower()
        ]

    def get_armor_by_category(
        self, armor_category: str, resolve_references: bool = False
    ) -> List[D5eEquipment]:
        """Get armor of a specific category.

        Args:
            armor_category: The armor category (e.g., 'Light', 'Medium', 'Heavy')
            resolve_references: Whether to resolve references

        Returns:
            List of armor in that category
        """
        armor_list = self.get_armor(resolve_references=resolve_references)
        return [
            armor
            for armor in armor_list
            if armor.armor_category
            and armor.armor_category.lower() == armor_category.lower()
        ]

    def get_by_cost_range(
        self,
        min_cost: float,
        max_cost: float,
        unit: str = "gp",
        resolve_references: bool = False,
    ) -> List[D5eEquipment]:
        """Get equipment within a cost range.

        Args:
            min_cost: Minimum cost (inclusive)
            max_cost: Maximum cost (inclusive)
            unit: Currency unit (default: 'gp')
            resolve_references: Whether to resolve references

        Returns:
            List of equipment within the cost range

        Raises:
            DatabaseError: If database operation fails
            ValidationError: If invalid currency unit
        """
        try:
            # Conversion rates to gold pieces
            conversion = {"cp": 0.01, "sp": 0.1, "ep": 0.5, "gp": 1.0, "pp": 10.0}

            if unit not in conversion:
                raise ValidationError(
                    f"Invalid currency unit '{unit}'",
                    field="unit",
                    value=unit,
                )

            all_equipment = self.list_all_with_options(
                resolve_references=resolve_references
            )
            results = []

            for item in all_equipment:
                if item.cost:
                    # Convert item cost to gold pieces
                    item_cost_gp = item.cost.quantity * conversion.get(
                        item.cost.unit, 1.0
                    )

                    # Convert range to same unit as item
                    if unit != "gp":
                        factor = conversion.get(unit, 1.0)
                        min_gp = min_cost * factor
                        max_gp = max_cost * factor
                    else:
                        min_gp = min_cost
                        max_gp = max_cost

                    if min_gp <= item_cost_gp <= max_gp:
                        results.append(item)

            return results
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Error getting equipment by cost range: {e}",
                extra={
                    "min_cost": min_cost,
                    "max_cost": max_cost,
                    "unit": unit,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                "Failed to get equipment by cost range",
                details={
                    "min_cost": min_cost,
                    "max_cost": max_cost,
                    "unit": unit,
                    "error": str(e),
                },
            )

    def get_weapons_with_property(
        self, property_index: str, resolve_references: bool = False
    ) -> List[D5eEquipment]:
        """Get all weapons with a specific property.

        Args:
            property_index: The weapon property index (e.g., 'finesse', 'versatile')
            resolve_references: Whether to resolve references

        Returns:
            List of weapons with that property
        """
        weapons = self.get_weapons(resolve_references=resolve_references)
        return [
            weapon
            for weapon in weapons
            if weapon.properties
            and any(prop.index == property_index for prop in weapon.properties)
        ]

    def get_ranged_weapons(
        self, resolve_references: bool = False
    ) -> List[D5eEquipment]:
        """Get all ranged weapons.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of ranged weapons
        """
        weapons = self.get_weapons(resolve_references=resolve_references)
        return [
            weapon
            for weapon in weapons
            if weapon.weapon_range and weapon.weapon_range.lower() == "ranged"
        ]

    def get_melee_weapons(self, resolve_references: bool = False) -> List[D5eEquipment]:
        """Get all melee weapons.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of melee weapons
        """
        weapons = self.get_weapons(resolve_references=resolve_references)
        return [
            weapon
            for weapon in weapons
            if weapon.weapon_range and weapon.weapon_range.lower() == "melee"
        ]

    def get_tools(self, resolve_references: bool = False) -> List[D5eEquipment]:
        """Get all tools.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of tools
        """
        all_equipment = self.list_all_with_options(
            resolve_references=resolve_references
        )
        # Tools are equipment that aren't weapons or armor
        return [
            item
            for item in all_equipment
            if item.weapon_category is None
            and item.armor_category is None
            and "tools" in item.equipment_category.index.lower()
        ]

    def get_magic_items(self, resolve_references: bool = False) -> List[D5eMagicItem]:
        """Get all magic items.

        Args:
            resolve_references: Whether to resolve references

        Returns:
            List of magic items
        """
        return self._magic_item_repo.list_all_with_options(
            resolve_references=resolve_references
        )

    def get_magic_items_by_rarity(
        self, rarity: str, resolve_references: bool = False
    ) -> List[D5eMagicItem]:
        """Get magic items of a specific rarity.

        Args:
            rarity: The rarity (e.g., 'Common', 'Rare', 'Legendary')
            resolve_references: Whether to resolve references

        Returns:
            List of magic items of that rarity
        """
        all_magic_items = self.get_magic_items(resolve_references=resolve_references)
        rarity_lower = rarity.lower()
        return [
            item
            for item in all_magic_items
            if "name" in item.rarity and item.rarity["name"].lower() == rarity_lower
        ]

    def get_weapon_properties(self) -> List[D5eWeaponProperty]:
        """Get all weapon properties.

        Returns:
            List of weapon properties
        """
        return self._weapon_property_repo.list_all()

    def get_lightest_armor_by_ac(self, min_ac: int) -> Optional[D5eEquipment]:
        """Get the lightest armor that provides at least the specified AC.

        Args:
            min_ac: Minimum armor class required

        Returns:
            The lightest qualifying armor, or None
        """
        armor_list = self.get_armor(resolve_references=False)

        # Filter by AC and sort by weight
        qualifying_armor = []
        for armor in armor_list:
            if armor.armor_class and armor.armor_class.base >= min_ac:
                qualifying_armor.append(armor)

        if not qualifying_armor:
            return None

        # Sort by weight (if available)
        qualifying_armor.sort(key=lambda a: a.weight or float("inf"))
        return qualifying_armor[0]

    def get_available_equipment_categories(self) -> Set[str]:
        """Get all unique equipment categories.

        Returns:
            Set of category indices
        """
        all_equipment = self.list_all_with_options(resolve_references=False)
        return {item.equipment_category.index for item in all_equipment}

    def get_available_weapon_properties(self) -> Set[str]:
        """Get all unique weapon properties used in the equipment.

        Returns:
            Set of property indices
        """
        weapons = self.get_weapons(resolve_references=False)
        properties = set()

        for weapon in weapons:
            if weapon.properties:
                for prop in weapon.properties:
                    properties.add(prop.index)

        return properties

    def search_by_description(
        self, keyword: str, resolve_references: bool = False
    ) -> List[D5eEquipment]:
        """Search equipment by description keywords.

        Args:
            keyword: The keyword to search for (case-insensitive)
            resolve_references: Whether to resolve references

        Returns:
            List of equipment containing the keyword
        """
        all_equipment = self.list_all_with_options(
            resolve_references=resolve_references
        )
        keyword_lower = keyword.lower()

        results = []
        for item in all_equipment:
            # Check name
            if keyword_lower in item.name.lower():
                results.append(item)
                continue

            # Check description if available
            if hasattr(item, "desc") and item.desc:
                if any(keyword_lower in desc.lower() for desc in item.desc):
                    results.append(item)

        return results
