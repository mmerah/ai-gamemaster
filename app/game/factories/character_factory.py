"""
Factory for creating character instances from templates and other data sources.
"""

import logging
from typing import Dict, Optional

from app.game.calculators.character_stats import (
    calculate_armor_class,
    calculate_hit_points,
)
from app.game.calculators.dice_mechanics import get_ability_modifier
from app.models import (
    ArmorModel,
    CharacterInstanceModel,
    CharacterTemplateModel,
    D5EClassModel,
    ItemModel,
)

logger = logging.getLogger(__name__)


class CharacterFactory:
    """Factory for creating character instances from various sources."""

    def __init__(
        self,
        d5e_classes_data: Optional[Dict[str, D5EClassModel]] = None,
        armor_data: Optional[Dict[str, ArmorModel]] = None,
    ):
        """
        Initialize the character factory with D&D 5e data.

        Args:
            d5e_classes_data: Dictionary of class data from D&D 5e
            armor_data: Dictionary of armor data
        """
        self.d5e_classes_data = d5e_classes_data or {}
        self.armor_data = armor_data or self._get_default_armor_data()

    def _get_default_armor_data(self) -> Dict[str, ArmorModel]:
        """Get default armor data if none provided."""
        return {
            "leather armor": ArmorModel(
                name="leather armor",
                base_ac=11,
                type="light",
                strength_requirement=0,
                stealth_disadvantage=False,
            ),
            "studded leather": ArmorModel(
                name="studded leather",
                base_ac=12,
                type="light",
                strength_requirement=0,
                stealth_disadvantage=False,
            ),
            "scale mail": ArmorModel(
                name="scale mail",
                base_ac=14,
                type="medium",
                max_dex_bonus=2,
                strength_requirement=0,
                stealth_disadvantage=True,
            ),
            "chain mail": ArmorModel(
                name="chain mail",
                base_ac=16,
                type="heavy",
                max_dex_bonus=0,
                strength_requirement=13,
                stealth_disadvantage=True,
            ),
            "plate": ArmorModel(
                name="plate",
                base_ac=18,
                type="heavy",
                max_dex_bonus=0,
                strength_requirement=15,
                stealth_disadvantage=True,
            ),
            "shield": ArmorModel(
                name="shield",
                base_ac=0,
                ac_bonus=2,
                type="shield",
                strength_requirement=0,
                stealth_disadvantage=False,
            ),
        }

    def _find_equipped_armor(self, equipment: list[ItemModel]) -> Optional[ArmorModel]:
        """Find equipped armor from equipment list."""
        for item in equipment:
            # Handle malformed equipment items
            if not hasattr(item, "name"):
                continue
            item_name = item.name.lower()
            armor = self.armor_data.get(item_name)
            if armor:
                armor_type = armor.type
                if armor_type != "shield":
                    return self.armor_data[item_name]
        return None

    def _has_shield_equipped(self, equipment: list[ItemModel]) -> bool:
        """Check if character has a shield equipped."""
        for item in equipment:
            # Handle malformed equipment items
            if not hasattr(item, "name"):
                continue
            item_name = item.name.lower()
            if item_name == "shield":
                return True
            armor = self.armor_data.get(item_name)
            if armor:
                armor_type = armor.type
                if armor_type == "shield":
                    return True
        return False

    def _calculate_character_hit_points(self, template: CharacterTemplateModel) -> int:
        """Calculate hit points for a character from template."""
        # Handle both dict and BaseStatsModel
        try:
            con_stat = getattr(
                template.base_stats, "CON", 10
            )  # Default to 10 if missing
            if con_stat is None or not isinstance(con_stat, int):
                con_stat = 10  # Default to 10 for invalid values
        except AttributeError:
            con_stat = 10  # Default to 10 if base_stats doesn't exist
        con_mod = get_ability_modifier(con_stat)

        # Get hit die from class data
        class_data = (
            self.d5e_classes_data.get(template.char_class.lower())
            if self.d5e_classes_data
            else None
        )
        hit_die = class_data.hit_die if class_data else 8

        return calculate_hit_points(template.level, con_mod, hit_die)

    def _calculate_character_armor_class(self, template: CharacterTemplateModel) -> int:
        """Calculate armor class for a character from template."""
        # Handle both dict and BaseStatsModel
        try:
            dex_stat = getattr(
                template.base_stats, "DEX", 10
            )  # Default to 10 if missing
            if dex_stat is None or not isinstance(dex_stat, int):
                dex_stat = 10  # Default to 10 for invalid values
        except AttributeError:
            dex_stat = 10  # Default to 10 if base_stats doesn't exist
        dex_mod = get_ability_modifier(dex_stat)

        equipped_armor = self._find_equipped_armor(template.starting_equipment)
        has_shield = self._has_shield_equipped(template.starting_equipment)

        return calculate_armor_class(dex_mod, equipped_armor, has_shield)

    def from_template(
        self, template: CharacterTemplateModel, campaign_id: str = "default"
    ) -> CharacterInstanceModel:
        """
        Convert a character template to a character instance for the game.

        Args:
            template: CharacterTemplateModel object
            campaign_id: ID of the campaign this instance belongs to

        Returns:
            CharacterInstanceModel instance
        """
        try:
            max_hp = self._calculate_character_hit_points(template)

            # Create instance data matching CharacterInstanceModel
            instance_data = {
                "template_id": template.id,
                "campaign_id": campaign_id,
                "current_hp": max_hp,
                "max_hp": max_hp,
                "temp_hp": 0,
                "experience_points": 0,
                "level": template.level,
                "spell_slots_used": {},
                "hit_dice_used": 0,
                "death_saves": {"successes": 0, "failures": 0},
                "inventory": [
                    item.model_dump() if hasattr(item, "model_dump") else item
                    for item in template.starting_equipment
                ],
                "gold": template.starting_gold,
                "conditions": [],
                "exhaustion_level": 0,
                "notes": "",
                "achievements": [],
                "relationships": {},
            }

            return CharacterInstanceModel(**instance_data)

        except Exception as e:
            logger.error(
                f"Error converting template {template.id} to character instance: {e}"
            )
            raise


def create_character_factory(
    d5e_classes_data: Optional[Dict[str, D5EClassModel]] = None,
    armor_data: Optional[Dict[str, ArmorModel]] = None,
) -> CharacterFactory:
    """
    Create a character factory instance.

    Args:
        d5e_classes_data: D&D 5e class data
        armor_data: Armor data

    Returns:
        CharacterFactory instance
    """
    return CharacterFactory(d5e_classes_data, armor_data)
