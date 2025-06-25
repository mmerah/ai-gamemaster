"""Processor for inventory and gold-related state updates."""

import logging
import random
from typing import Optional

from app.core.domain_interfaces import ICharacterService
from app.core.system_interfaces import IEventQueue
from app.models.events.game_state import ItemAddedEvent, PartyMemberUpdatedEvent
from app.models.events.utils import CharacterChangesModel
from app.models.game_state.main import GameStateModel
from app.models.updates import (
    GoldUpdateModel,
    InventoryAddUpdateModel,
    InventoryRemoveUpdateModel,
)
from app.models.utils import ItemModel
from app.utils.event_helpers import emit_event, emit_with_logging

logger = logging.getLogger(__name__)


class InventoryUpdater:
    """Handles inventory and gold-related state updates."""

    @staticmethod
    def apply_gold_change(
        game_state: GameStateModel,
        update: GoldUpdateModel,
        resolved_char_id: str,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Applies gold change to a specific character."""
        character_data = (
            character_service.get_character(resolved_char_id)
            if character_service
            else None
        )
        if character_data:
            # character_data is a NamedTuple with template and instance
            old_gold = character_data.instance.gold
            character_data.instance.gold += update.value

            # Build log message with details
            log_msg = f"Updated gold for {character_data.template.name} ({resolved_char_id}): {old_gold} -> {character_data.instance.gold} (Delta: {update.value})"
            details_parts = []
            if update.source:
                details_parts.append(f"source: {update.source}")
            if update.reason:
                details_parts.append(f"reason: {update.reason}")
            if update.description:
                details_parts.append(f"description: {update.description}")
            if details_parts:
                log_msg += f" - {', '.join(details_parts)}"
            logger.info(log_msg)

            # Emit PartyMemberUpdatedEvent with gold change
            # Extract source from flattened fields if available
            gold_source = None
            if update.source:
                gold_source = update.source
            elif update.reason:
                gold_source = update.reason

            event = PartyMemberUpdatedEvent(
                character_id=resolved_char_id,
                character_name=character_data.template.name,
                changes=CharacterChangesModel(gold=character_data.instance.gold),
                gold_source=gold_source,
                correlation_id=correlation_id,
            )
            emit_with_logging(
                event_queue,
                event,
                f"for {character_data.template.name}: gold {old_gold} -> {character_data.instance.gold}",
            )
        else:
            # Gold changes typically don't apply to NPCs in this manner
            logger.warning(
                f"Attempted to apply gold change to non-player or unknown ID '{resolved_char_id}'. Ignoring."
            )

    @staticmethod
    def apply_inventory_add(
        game_state: GameStateModel,
        update: InventoryAddUpdateModel,
        resolved_char_id: str,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Adds an item to a character's inventory."""
        character_data = (
            character_service.get_character(resolved_char_id)
            if character_service
            else None
        )
        if not character_data:
            logger.warning(
                f"InventoryAdd: Character ID '{resolved_char_id}' not found. Ignoring update."
            )
            return

        item_value = update.value

        # Handle ItemModel value
        if isinstance(item_value, ItemModel):
            # Already an ItemModel, just update quantity if provided
            item = item_value
            if update.quantity:
                item = ItemModel(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    quantity=update.quantity,
                )
            character_data.instance.inventory.append(item)

            # Build log message with details
            log_msg = f"Added item '{item.name}' (x{item.quantity}) to {character_data.template.name}'s inventory"
            details_parts = []
            if update.item_value:
                details_parts.append(f"value: {update.item_value}gp")
            if update.rarity:
                details_parts.append(f"rarity: {update.rarity}")
            if update.source:
                details_parts.append(f"source: {update.source}")
            if details_parts:
                log_msg += f" ({', '.join(details_parts)})"
            logger.info(log_msg)

            # Emit ItemAddedEvent
            item_gold_value = update.item_value
            item_rarity = update.rarity

            event = ItemAddedEvent(
                character_id=resolved_char_id,
                character_name=character_data.template.name,
                item_name=item.name,
                item_description=item.description,
                quantity=item.quantity,
                item_value=item_gold_value,
                item_rarity=item_rarity,
                correlation_id=correlation_id,
            )
            emit_with_logging(
                event_queue,
                event,
                f"for {item.name} added to {character_data.template.name}",
            )

        elif isinstance(item_value, str):
            # Handle string value - create simple ItemModel
            item_name = item_value
            quantity = 1
            item_description = ""

            # Override with flattened fields if provided
            if update.quantity:
                quantity = update.quantity
            if update.description:
                item_description = update.description

            item_id = f"simple_{item_name.lower().replace(' ', '_')}_{random.randint(100, 999)}"
            item = ItemModel(
                id=item_id,
                name=item_name,
                description=item_description,
                quantity=quantity,
            )
            character_data.instance.inventory.append(item)

            # Build log message with details
            log_msg = f"Added item '{item_name}' (x{quantity}) to {character_data.template.name}'s inventory"
            details_parts = []
            if update.item_value:
                details_parts.append(f"value: {update.item_value}gp")
            if update.rarity:
                details_parts.append(f"rarity: {update.rarity}")
            if update.source:
                details_parts.append(f"source: {update.source}")
            if details_parts:
                log_msg += f" ({', '.join(details_parts)})"
            logger.info(log_msg)

            # Emit ItemAddedEvent
            item_gold_value = update.item_value
            item_rarity = update.rarity

            event = ItemAddedEvent(
                character_id=resolved_char_id,
                character_name=character_data.template.name,
                item_name=item.name,
                item_description=item.description,
                quantity=item.quantity,
                item_value=item_gold_value,
                item_rarity=item_rarity,
                correlation_id=correlation_id,
            )
            emit_with_logging(
                event_queue,
                event,
                f"for {item.name} added to {character_data.template.name}",
            )

    @staticmethod
    def apply_inventory_remove(
        game_state: GameStateModel,
        update: InventoryRemoveUpdateModel,
        resolved_char_id: str,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:  # pylint: disable=unused-argument
        """Removes an item from a character's inventory."""
        character_data = (
            character_service.get_character(resolved_char_id)
            if character_service
            else None
        )
        if not character_data:
            logger.warning(
                f"InventoryRemove: Character ID '{resolved_char_id}' not found. Ignoring update."
            )
            return

        item_value = update.value
        item_name = ""

        # Value could be an item name (string) or an item ID (string)
        # This requires searching the inventory
        item_to_find = str(item_value)
        found_item_idx = -1

        # Inventory contains ItemModel instances
        for i, item in enumerate(character_data.instance.inventory):
            if item.name == item_to_find or item.id == item_to_find:
                found_item_idx = i
                item_name = item.name
                break

        if found_item_idx != -1:
            del character_data.instance.inventory[found_item_idx]
            logger.info(
                f"Removed item '{item_name}' from {character_data.template.name}'s inventory."
            )
        else:
            logger.warning(
                f"InventoryRemove: Item '{item_to_find}' not found in {character_data.template.name}'s inventory."
            )
