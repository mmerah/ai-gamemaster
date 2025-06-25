"""
Factory for creating character instances from templates and other data sources.
"""

import logging
from typing import Any, Dict, Optional

from app.content.schemas import D5eClass, D5eEquipment
from app.core.content_interfaces import IContentService
from app.domain.shared.calculators.character_stats import (
    calculate_armor_class,
    calculate_hit_points,
)
from app.domain.shared.calculators.dice_mechanics import get_ability_modifier
from app.models.character.instance import CharacterInstanceModel
from app.models.character.template import CharacterTemplateModel
from app.models.utils import ItemModel

logger = logging.getLogger(__name__)


class CharacterFactory:
    """Factory for creating character instances from various sources."""

    def __init__(self, content_service: IContentService):
        """
        Initialize the character factory with content service.

        Args:
            content_service: Service for accessing D&D 5e content
        """
        self.content_service = content_service

    def _find_equipped_armor(
        self,
        equipment: list[ItemModel],
        content_pack_priority: Optional[list[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find equipped armor from equipment list using content service."""
        for item in equipment:
            # Handle malformed equipment items
            if not hasattr(item, "name"):
                continue

            # Try to find the equipment in the content service
            equipment_data = self.content_service.get_equipment_by_name(
                item.name, content_pack_priority=content_pack_priority or ["dnd_5e_srd"]
            )

            if equipment_data and equipment_data.armor_class:
                # Check if it's armor (not a shield)
                if (
                    equipment_data.armor_category
                    and equipment_data.armor_category.lower() != "shield"
                ):
                    return {
                        "name": equipment_data.name,
                        "base_ac": equipment_data.armor_class.base,
                        "type": equipment_data.armor_category.lower(),
                        "max_dex_bonus": equipment_data.armor_class.max_bonus,
                        "str_minimum": equipment_data.str_minimum or 0,
                        "stealth_disadvantage": equipment_data.stealth_disadvantage
                        or False,
                    }
        return None

    def _has_shield_equipped(
        self,
        equipment: list[ItemModel],
        content_pack_priority: Optional[list[str]] = None,
    ) -> bool:
        """Check if character has a shield equipped."""
        for item in equipment:
            # Handle malformed equipment items
            if not hasattr(item, "name"):
                continue

            # Special case for shield
            if "shield" in item.name.lower():
                equipment_data = self.content_service.get_equipment_by_name(
                    item.name,
                    content_pack_priority=content_pack_priority or ["dnd_5e_srd"],
                )
                if (
                    equipment_data
                    and equipment_data.armor_category
                    and equipment_data.armor_category.lower() == "shield"
                ):
                    return True
        return False

    def _calculate_character_hit_points(
        self,
        template: CharacterTemplateModel,
        content_pack_priority: Optional[list[str]] = None,
    ) -> int:
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

        # Get hit die from class data using content service
        class_data = self.content_service.get_class_by_name(
            template.char_class,
            content_pack_priority=content_pack_priority or ["dnd_5e_srd"],
        )
        hit_die = class_data.hit_die if class_data else 8

        return calculate_hit_points(template.level, con_mod, hit_die)

    def _calculate_character_armor_class(
        self,
        template: CharacterTemplateModel,
        content_pack_priority: Optional[list[str]] = None,
    ) -> int:
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

        equipped_armor = self._find_equipped_armor(
            template.starting_equipment, content_pack_priority
        )
        has_shield = self._has_shield_equipped(
            template.starting_equipment, content_pack_priority
        )

        return calculate_armor_class(dex_mod, equipped_armor, has_shield)

    def from_template(
        self,
        template: CharacterTemplateModel,
        campaign_id: str = "default",
        content_pack_priority: Optional[list[str]] = None,
    ) -> CharacterInstanceModel:
        """
        Convert a character template to a character instance for the game.

        Args:
            template: CharacterTemplateModel object
            campaign_id: ID of the campaign this instance belongs to
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            CharacterInstanceModel instance
        """
        try:
            max_hp = self._calculate_character_hit_points(
                template, content_pack_priority
            )

            # Create instance data matching CharacterInstanceModel
            instance_data = {
                "id": template.id,  # Use template ID as instance ID
                "name": template.name,  # Character name from template
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
