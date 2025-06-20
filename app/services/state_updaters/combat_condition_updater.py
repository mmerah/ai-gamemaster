"""Processor for combat condition-related state updates."""

import logging
from typing import Optional

from app.core.domain_interfaces import ICharacterService
from app.core.system_interfaces import IEventQueue
from app.models.events import CombatantStatusChangedEvent
from app.models.game_state import GameStateModel
from app.models.updates import ConditionAddUpdateModel, ConditionRemoveUpdateModel
from app.utils.event_helpers import emit_event, emit_with_logging

logger = logging.getLogger(__name__)


class CombatConditionUpdater:
    """Handles condition-related state updates during combat."""

    @staticmethod
    def apply_condition_add(
        game_state: GameStateModel,
        update: ConditionAddUpdateModel,
        resolved_char_id: str,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Adds a condition to a character or NPC."""
        condition_name = update.value.lower()
        character_data = (
            character_service.get_character(resolved_char_id)
            if character_service
            else None
        )
        target_conditions_list = None
        target_name = (
            character_service.get_character_name(resolved_char_id)
            if character_service
            else resolved_char_id
        )
        is_player = False

        if character_data:
            # character_data is a NamedTuple with template and instance
            target_conditions_list = character_data.instance.conditions
            is_player = True
            target_name = character_data.template.name
        elif game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
            if combatant and not combatant.is_player:
                target_conditions_list = combatant.conditions
                is_player = False
                target_name = combatant.name
            else:
                logger.error(
                    f"Cannot add condition: NPC '{resolved_char_id}' not found in combat."
                )
                return
        else:
            logger.error(
                f"Cannot add condition: Resolved ID '{resolved_char_id}' not found."
            )
            return

        # Track changes for event emission
        changed = False

        if condition_name not in target_conditions_list:
            target_conditions_list.append(condition_name)
            changed = True

            # Log condition details if provided
            log_msg = f"Added condition '{condition_name}' to {target_name} ({resolved_char_id})"
            details_parts = []
            if update.duration:
                details_parts.append(f"duration: {update.duration}")
            if update.source:
                details_parts.append(f"source: {update.source}")
            if update.save_dc and update.save_type:
                details_parts.append(f"save: DC {update.save_dc} {update.save_type}")
            if details_parts:
                log_msg += f" ({', '.join(details_parts)})"
            logger.info(log_msg)
        else:
            logger.debug(
                f"Condition '{condition_name}' already present on {target_name} ({resolved_char_id})"
            )

        # Emit CombatantStatusChangedEvent if condition was added
        if changed:
            # Check if character is defeated (HP = 0 or has "defeated" condition)
            is_defeated = "defeated" in [c.lower() for c in target_conditions_list]
            if not is_defeated and character_data:
                is_defeated = character_data.instance.current_hp <= 0
            elif not is_defeated and not is_player:
                # Check NPC HP from combatant
                combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
                is_defeated = combatant is not None and combatant.current_hp <= 0

            event = CombatantStatusChangedEvent(
                combatant_id=resolved_char_id,
                combatant_name=target_name,
                new_conditions=list(
                    target_conditions_list
                ),  # Copy to avoid reference issues
                added_conditions=[condition_name],
                removed_conditions=[],
                is_defeated=is_defeated,
                condition_details=None,  # No longer using details dict
                correlation_id=correlation_id,
            )
            emit_with_logging(
                event_queue, event, f"for {target_name}: added=[{condition_name}]"
            )

    @staticmethod
    def apply_condition_remove(
        game_state: GameStateModel,
        update: ConditionRemoveUpdateModel,
        resolved_char_id: str,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Removes a condition from a character or NPC."""
        condition_name = update.value.lower()
        character_data = (
            character_service.get_character(resolved_char_id)
            if character_service
            else None
        )
        target_conditions_list = None
        target_name = (
            character_service.get_character_name(resolved_char_id)
            if character_service
            else resolved_char_id
        )
        is_player = False

        if character_data:
            # character_data is a NamedTuple with template and instance
            target_conditions_list = character_data.instance.conditions
            is_player = True
            target_name = character_data.template.name
        elif game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
            if combatant and not combatant.is_player:
                target_conditions_list = combatant.conditions
                is_player = False
                target_name = combatant.name
            else:
                logger.error(
                    f"Cannot remove condition: NPC '{resolved_char_id}' not found in combat."
                )
                return
        else:
            logger.error(
                f"Cannot remove condition: Resolved ID '{resolved_char_id}' not found."
            )
            return

        # Track changes for event emission
        changed = False

        if condition_name in target_conditions_list:
            target_conditions_list.remove(condition_name)
            changed = True
            logger.info(
                f"Removed condition '{condition_name}' from {target_name} ({resolved_char_id})"
            )
        else:
            logger.debug(
                f"Condition '{condition_name}' not found on {target_name} ({resolved_char_id}) to remove"
            )

        # Emit CombatantStatusChangedEvent if condition was removed
        if changed:
            # Check if character is defeated (HP = 0 or has "defeated" condition)
            is_defeated = "defeated" in [c.lower() for c in target_conditions_list]
            if not is_defeated and character_data:
                is_defeated = character_data.instance.current_hp <= 0
            elif not is_defeated and not is_player:
                # Check NPC HP from combatant
                combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
                is_defeated = combatant is not None and combatant.current_hp <= 0

            event = CombatantStatusChangedEvent(
                combatant_id=resolved_char_id,
                combatant_name=target_name,
                new_conditions=list(
                    target_conditions_list
                ),  # Copy to avoid reference issues
                added_conditions=[],
                removed_conditions=[condition_name],
                is_defeated=is_defeated,
                correlation_id=correlation_id,
            )
            emit_with_logging(
                event_queue, event, f"for {target_name}: removed=[{condition_name}]"
            )
