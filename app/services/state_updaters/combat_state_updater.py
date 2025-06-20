"""Processor for core combat state management."""

import logging
from typing import Optional

from app.core.domain_interfaces import ICharacterService
from app.core.system_interfaces import IEventQueue
from app.models.combat import CombatantModel, CombatStateModel
from app.models.events import (
    CombatantRemovedEvent,
    CombatEndedEvent,
    CombatStartedEvent,
    ErrorContextModel,
    GameErrorEvent,
)
from app.models.game_state import GameStateModel
from app.models.updates import CombatEndUpdateModel, CombatStartUpdateModel
from app.utils.event_helpers import emit_event, emit_with_logging

from .combat_condition_updater import CombatConditionUpdater
from .combat_helpers import add_combatants_to_active_combat, add_combatants_to_state
from .combat_hp_updater import CombatHPUpdater

logger = logging.getLogger(__name__)


class CombatStateUpdater:
    """Handles core combat state management."""

    # Re-export static methods from sub-updaters for convenience
    apply_hp_change = CombatHPUpdater.apply_hp_change
    apply_condition_add = CombatConditionUpdater.apply_condition_add
    apply_condition_remove = CombatConditionUpdater.apply_condition_remove

    @staticmethod
    def start_combat(
        game_state: GameStateModel,
        update: CombatStartUpdateModel,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Initializes combat state or adds combatants to existing combat."""
        if game_state.combat.is_active:
            logger.info(
                "Received combat_start while combat is already active. Adding new combatants."
            )
            # Add new combatants to existing combat
            add_combatants_to_active_combat(
                game_state, update, event_queue, correlation_id, character_service
            )
            return

        logger.info("Starting combat! Populating initial combatants list.")
        game_state.combat = CombatStateModel(
            is_active=True, round_number=1, current_turn_index=0
        )
        add_combatants_to_state(
            game_state, update, event_queue, correlation_id, character_service
        )
        logger.info(
            f"Combat started with {len(game_state.combat.combatants)} participants (Initiative Pending)."
        )
        game_state.combat._combat_just_started_flag = True

        # Emit CombatStartedEvent
        # Build combatants list for the event
        combatants_data = []

        # Add all combatants (players and NPCs)
        # Create a deep copy to avoid references being modified later
        for combatant in game_state.combat.combatants:
            # Create a copy of the combatant with current state
            combatant_copy = CombatantModel(
                id=combatant.id,
                name=combatant.name,
                initiative=combatant.initiative,
                initiative_modifier=combatant.initiative_modifier,
                current_hp=combatant.current_hp,
                max_hp=combatant.max_hp,
                armor_class=combatant.armor_class,
                conditions=combatant.conditions.copy(),  # Copy the list
                is_player=combatant.is_player,
                icon_path=combatant.icon_path,
            )
            combatants_data.append(combatant_copy)

        event = CombatStartedEvent(
            combatants=combatants_data,
            correlation_id=correlation_id,
        )
        emit_with_logging(event_queue, event, f"with {len(combatants_data)} combatants")

    @staticmethod
    def end_combat(
        game_state: GameStateModel,
        update: CombatEndUpdateModel,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Finalizes combat state."""
        if not game_state.combat.is_active:
            logger.warning("Received combat_end while combat is not active. Ignoring.")
            return

        # Validate that no active enemies remain before ending combat
        active_npcs = [
            c
            for c in game_state.combat.combatants
            if not c.is_player and not c.is_defeated
        ]

        if active_npcs:
            logger.warning(
                f"AI attempted to end combat but {len(active_npcs)} active enemies remain: {[c.name for c in active_npcs]}. Ignoring combat_end."
            )
            # Emit a warning event if needed
            # Create context using ErrorContext fields
            error_context = ErrorContextModel(event_type="combat_end")
            # Add user action if available from update reason
            if update.reason:
                error_context.user_action = f"End combat: {update.reason}"

            error_event = GameErrorEvent(
                error_message=f"Combat cannot end: {len(active_npcs)} active enemies remain",
                error_type="invalid_combat_end",
                severity="warning",
                recoverable=True,
                context=error_context,
                correlation_id=correlation_id,
            )
            emit_with_logging(
                event_queue, error_event, "for invalid combat end attempt"
            )
            return

        reason = update.reason or "Not specified"
        logger.info(f"Ending combat. Reason: {reason}")

        # Emit CombatEndedEvent before clearing combat state
        event = CombatEndedEvent(
            reason=reason,
            outcome_description=update.description,
            correlation_id=correlation_id,
        )
        emit_with_logging(event_queue, event, f"with reason: {reason}")

        game_state.combat = CombatStateModel()

        # Clear stored RAG context when combat ends since context changes significantly
        if hasattr(game_state, "_last_rag_context"):
            game_state._last_rag_context = None
            logger.debug("Cleared stored RAG context due to combat end")

    @staticmethod
    def remove_combatant_from_state(
        game_state: GameStateModel,
        combatant_id_to_remove: str,
        reason: Optional[str],
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Removes a combatant from active combat."""
        combat = game_state.combat
        if not combat.is_active:
            logger.warning(
                f"Attempted to remove '{combatant_id_to_remove}' but combat not active."
            )
            return

        removed_index = -1
        # Find the index of the combatant to be removed IN THE CURRENT LIST
        for i, c in enumerate(combat.combatants):
            if c.id == combatant_id_to_remove:
                removed_index = i
                break

        if removed_index == -1:
            logger.warning(
                f"Could not find '{combatant_id_to_remove}' in combatants list to remove."
            )
            return

        # Get name and details before removal for logging and event
        removed_combatant = combat.combatants[removed_index]
        removed_combatant_name = removed_combatant.name

        # Remove the combatant
        del combat.combatants[removed_index]

        reason = reason or "Removed"
        logger.info(
            f"Removed combatant '{removed_combatant_name}' (ID: {combatant_id_to_remove}) from combat. Reason: {reason}"
        )

        # Emit CombatantRemovedEvent
        event = CombatantRemovedEvent(
            combatant_id=combatant_id_to_remove,
            combatant_name=removed_combatant_name,
            reason=reason,
            correlation_id=correlation_id,
        )
        emit_with_logging(
            event_queue, event, f"for {removed_combatant_name} (reason: {reason})"
        )

        # Adjust current_turn_index
        if removed_index < combat.current_turn_index:
            combat.current_turn_index -= 1
            logger.debug(
                f"Adjusted current_turn_index due to removal before current: new index {combat.current_turn_index}"
            )
        elif removed_index == combat.current_turn_index:
            # If the removed combatant *was* the current one, the turn effectively ends for them.
            if (
                combat.current_turn_index >= len(combat.combatants)
                and len(combat.combatants) > 0
            ):
                combat.current_turn_index = 0  # Wrap around if it was the last one
                logger.debug(
                    "Current turn combatant removed was last; wrapped index to 0."
                )
            logger.debug(
                f"Current turn combatant '{removed_combatant_name}' removed. Index remains {combat.current_turn_index} (relative to new list)."
            )

        # Ensure current_turn_index is valid if list becomes empty
        if not combat.combatants:
            logger.info("All combatants removed.")
        elif combat.current_turn_index >= len(combat.combatants):
            logger.warning(
                f"current_turn_index ({combat.current_turn_index}) is out of bounds after removal. Resetting to 0."
            )
            combat.current_turn_index = 0

    @staticmethod
    def check_and_end_combat_if_over(
        game_state: GameStateModel,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Checks if combat should end automatically (e.g., all NPCs defeated)."""
        if not game_state.combat.is_active:
            return

        active_npcs_found = any(
            not c.is_player and not c.is_defeated for c in game_state.combat.combatants
        )

        if not active_npcs_found:
            logger.info(
                "Auto-detect: No active non-player combatants remaining. Ending combat."
            )
            CombatStateUpdater.end_combat(
                game_state,
                CombatEndUpdateModel(
                    reason="victory", description="All enemies defeated"
                ),
                event_queue,
                correlation_id,
                character_service,
            )
