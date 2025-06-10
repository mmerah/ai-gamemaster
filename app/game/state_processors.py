import logging
import random
from typing import List, Optional

from app.core.interfaces import AIResponseProcessor
from app.game.calculators.dice_mechanics import get_ability_modifier
from app.models.events import (
    CombatantAddedEvent,
    CombatantHpChangedEvent,
    CombatantRemovedEvent,
    CombatantStatusChangedEvent,
    CombatEndedEvent,
    CombatStartedEvent,
    ErrorContextModel,
    GameErrorEvent,
    ItemAddedEvent,
    PartyMemberUpdatedEvent,
    QuestUpdatedEvent,
)
from app.models.models import (
    CombatantModel,
    CombatStateModel,
    GameStateModel,
    ItemModel,
)
from app.models.updates import (
    CombatEndUpdateModel,
    CombatStartUpdateModel,
    ConditionAddUpdateModel,
    ConditionRemoveUpdateModel,
    GoldUpdateModel,
    HPChangeUpdateModel,
    InventoryAddUpdateModel,
    InventoryRemoveUpdateModel,
    QuestUpdateModel,
)

logger = logging.getLogger(__name__)


def _get_correlation_id(game_manager: AIResponseProcessor) -> Optional[str]:
    """Get correlation ID from game_manager if available."""
    # Try to get correlation ID if it's available as an attribute
    return getattr(game_manager, "_current_correlation_id", None)


def _add_combatants_to_state(
    game_state: GameStateModel,
    combat_update: CombatStartUpdateModel,
    game_manager: AIResponseProcessor,
) -> None:
    """Adds player and NPC combatants to the combat state."""
    combat = game_state.combat

    # Get character service to access template data
    char_service = game_manager.character_service

    # Add Players
    for pc_id, pc_instance in game_state.party.items():
        # Get combined character data if character service is available
        if char_service:
            char_data = char_service.get_character(pc_id)
            if char_data:
                # Get DEX modifier for initiative tie-breaking
                dex_score = char_data.template.base_stats.DEX
                dex_modifier = (dex_score - 10) // 2

                # Calculate armor class from template data
                dex_mod = get_ability_modifier(dex_score)

                # Find equipped armor - this is a simplified check
                armor_class = 10 + dex_mod

                combatant = CombatantModel(
                    id=pc_id,
                    name=char_data.template.name,
                    initiative=-1,
                    initiative_modifier=dex_modifier,
                    current_hp=pc_instance.current_hp,
                    max_hp=pc_instance.max_hp,
                    armor_class=armor_class,
                    conditions=pc_instance.conditions.copy(),
                    is_player=True,
                    icon_path=char_data.template.portrait_path,
                )
                combat.combatants.append(combatant)
                logger.debug(
                    f"Added player {char_data.template.name} ({pc_id}) to initial combatants list."
                )
                continue
        else:
            logger.error(
                f"Character Service not available to add combatant ({pc_id}) to state."
            )
            continue

    # Add NPCs/Monsters
    for npc_data in combat_update.combatants:
        npc_id = npc_data.id
        npc_name = npc_data.name
        if npc_id in game_state.party or combat.get_combatant_by_id(npc_id) is not None:
            logger.warning(
                f"Duplicate combatant ID '{npc_id}' provided in combat_start. Skipping."
            )
            continue

        initial_hp = npc_data.hp
        if initial_hp <= 0:
            logger.warning(
                f"AI tried to start combat with defeated NPC '{npc_name}' (ID: {npc_id}, HP: {initial_hp}). Skipping."
            )
            continue

        # Calculate DEX modifier from stats
        dex_score = npc_data.stats.get("DEX", 10) if npc_data.stats else 10
        dex_modifier = (dex_score - 10) // 2

        combatant = CombatantModel(
            id=npc_id,
            name=npc_name,
            initiative=-1,
            initiative_modifier=dex_modifier,
            current_hp=initial_hp,
            max_hp=initial_hp,
            armor_class=npc_data.ac,
            conditions=[],
            is_player=False,
            icon_path=npc_data.icon_path,
            stats=npc_data.stats or {"DEX": 10},
            abilities=npc_data.abilities or [],
            attacks=npc_data.attacks or [],
            conditions_immune=None,
            resistances=None,
            vulnerabilities=None,
        )
        combat.combatants.append(combatant)
        logger.debug(
            f"Added NPC {npc_name} ({npc_id}) to combat tracker and combatants list."
        )


def _add_combatants_to_active_combat(
    game_state: GameStateModel,
    combat_update: CombatStartUpdateModel,
    game_manager: AIResponseProcessor,
) -> None:
    """Adds new combatants to active combat (reinforcements)."""
    combat = game_state.combat

    # Only add NPCs/Monsters during active combat (not player characters)
    for npc_data in combat_update.combatants:
        npc_id = npc_data.id
        npc_name = npc_data.name
        if npc_id in game_state.party or combat.get_combatant_by_id(npc_id) is not None:
            logger.warning(
                f"Duplicate combatant ID '{npc_id}' provided in combat_start. Skipping."
            )
            continue

        initial_hp = npc_data.hp
        if initial_hp <= 0:
            logger.warning(
                f"AI tried to add defeated NPC '{npc_name}' (ID: {npc_id}, HP: {initial_hp}). Skipping."
            )
            continue

        # Calculate DEX modifier from stats
        dex_score = npc_data.stats.get("DEX", 10) if npc_data.stats else 10
        dex_modifier = (dex_score - 10) // 2

        # Create combatant with enhanced model
        combatant = CombatantModel(
            id=npc_id,
            name=npc_name,
            initiative=-1,
            initiative_modifier=dex_modifier,
            current_hp=initial_hp,
            max_hp=initial_hp,
            armor_class=npc_data.ac,
            conditions=[],
            is_player=False,
            icon_path=npc_data.icon_path,
            stats=npc_data.stats or {"DEX": 10},
            abilities=npc_data.abilities or [],
            attacks=npc_data.attacks or [],
            conditions_immune=None,
            resistances=None,
            vulnerabilities=None,
        )
        combat.combatants.append(combatant)

        logger.info(f"Added reinforcement {npc_name} ({npc_id}) to active combat.")

        # Emit CombatantAddedEvent
        if game_manager and game_manager.event_queue:
            event = CombatantAddedEvent(
                combatant_id=npc_id,
                combatant_name=npc_name,
                hp=initial_hp,
                max_hp=initial_hp,
                ac=npc_data.ac,
                is_player_controlled=False,
                position_in_order=len(combat.combatants) - 1,
                correlation_id=_get_correlation_id(game_manager),
            )
            game_manager.event_queue.put_event(event)
            logger.debug(f"Emitted CombatantAddedEvent for {npc_name}")


def start_combat(
    game_state: GameStateModel,
    update: CombatStartUpdateModel,
    game_manager: AIResponseProcessor,
) -> None:
    """Initializes combat state or adds combatants to existing combat."""
    if game_state.combat.is_active:
        logger.info(
            "Received combat_start while combat is already active. Adding new combatants."
        )
        # Add new combatants to existing combat
        _add_combatants_to_active_combat(game_state, update, game_manager)
        return

    logger.info("Starting combat! Populating initial combatants list.")
    game_state.combat = CombatStateModel(
        is_active=True, round_number=1, current_turn_index=0
    )
    _add_combatants_to_state(game_state, update, game_manager)
    logger.info(
        f"Combat started with {len(game_state.combat.combatants)} participants (Initiative Pending)."
    )
    game_state.combat._combat_just_started_flag = True

    # Emit CombatStartedEvent
    if game_manager and game_manager.event_queue:
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
            combatants=combatants_data, correlation_id=_get_correlation_id(game_manager)
        )
        game_manager.event_queue.put_event(event)
        logger.debug(
            f"Emitted CombatStartedEvent with {len(combatants_data)} combatants"
        )


def end_combat(
    game_state: GameStateModel,
    update: CombatEndUpdateModel,
    game_manager: Optional[AIResponseProcessor] = None,
) -> None:
    """Finalizes combat state."""
    if not game_state.combat.is_active:
        logger.warning("Received combat_end while combat is not active. Ignoring.")
        return

    # Validate that no active enemies remain before ending combat
    active_npcs = [
        c for c in game_state.combat.combatants if not c.is_player and not c.is_defeated
    ]

    if active_npcs:
        logger.warning(
            f"AI attempted to end combat but {len(active_npcs)} active enemies remain: {[c.name for c in active_npcs]}. Ignoring combat_end."
        )
        # Emit a warning event if needed
        if game_manager and game_manager.event_queue:
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
                correlation_id=_get_correlation_id(game_manager),
            )
            game_manager.event_queue.put_event(error_event)
            logger.debug("Emitted GameErrorEvent for invalid combat end attempt")
        return

    reason = update.reason or "Not specified"
    logger.info(f"Ending combat. Reason: {reason}")

    # Emit CombatEndedEvent before clearing combat state
    if game_manager and game_manager.event_queue:
        event = CombatEndedEvent(
            reason=reason,
            outcome_description=update.description,
            correlation_id=_get_correlation_id(game_manager),
        )
        game_manager.event_queue.put_event(event)
        logger.debug(f"Emitted CombatEndedEvent with reason: {reason}")

    game_state.combat = CombatStateModel()

    # Clear stored RAG context when combat ends since context changes significantly
    if hasattr(game_state, "_last_rag_context"):
        game_state._last_rag_context = None
        logger.debug("Cleared stored RAG context due to combat end")


def remove_combatant_from_state(
    game_state: GameStateModel,
    combatant_id_to_remove: str,
    reason: Optional[str],
    game_manager: AIResponseProcessor,
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
    if game_manager and game_manager.event_queue:
        event = CombatantRemovedEvent(
            combatant_id=combatant_id_to_remove,
            combatant_name=removed_combatant_name,
            reason=reason,
            correlation_id=_get_correlation_id(game_manager),
        )
        game_manager.event_queue.put_event(event)
        logger.debug(
            f"Emitted CombatantRemovedEvent for {removed_combatant_name} (reason: {reason})"
        )

    # Adjust current_turn_index
    # If the removed combatant was before the current turn's combatant in the list[Any],
    # or if the removed combatant *was* the current turn's combatant and was at an index
    # now out of bounds or equal to the new list length.
    if removed_index < combat.current_turn_index:
        combat.current_turn_index -= 1
        logger.debug(
            f"Adjusted current_turn_index due to removal before current: new index {combat.current_turn_index}"
        )
    elif removed_index == combat.current_turn_index:
        # If the removed combatant *was* the current one, the turn effectively ends for them.
        # The advance_turn logic will then pick the "next" one.
        # However, the index might now point to the combatant that *was* after the removed one.
        # Or, if it was the last in the list[Any], current_turn_index might need to wrap around or be re-evaluated.
        # Let's ensure it's not out of bounds. If it becomes equal to len, advance_turn will handle wrap-around.
        if (
            combat.current_turn_index >= len(combat.combatants)
            and len(combat.combatants) > 0
        ):
            combat.current_turn_index = 0  # Wrap around if it was the last one
            logger.debug("Current turn combatant removed was last; wrapped index to 0.")
        # No change needed if it points to the new combatant at the same index,
        # as advance_turn will increment it.
        logger.debug(
            f"Current turn combatant '{removed_combatant_name}' removed. Index remains {combat.current_turn_index} (relative to new list[Any])."
        )

    # Ensure current_turn_index is valid if list becomes empty (should be handled by combat end)
    if not combat.combatants:
        logger.info("All combatants removed.")
        # Combat end should be triggered by check_and_end_combat_if_over
    elif combat.current_turn_index >= len(combat.combatants):
        logger.warning(
            f"current_turn_index ({combat.current_turn_index}) is out of bounds after removal. Resetting to 0."
        )
        combat.current_turn_index = 0


def check_and_end_combat_if_over(
    game_state: GameStateModel, game_manager: AIResponseProcessor
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
        end_combat(
            game_state,
            CombatEndUpdateModel(reason="No active enemies remaining"),
            game_manager,
        )


def apply_hp_change(
    game_state: GameStateModel,
    update: HPChangeUpdateModel,
    resolved_char_id: str,
    game_manager: AIResponseProcessor,
) -> None:
    """Applies HP changes to a character or NPC."""
    delta = update.value
    character_data = (
        game_manager.character_service.get_character(resolved_char_id)
        if game_manager
        else None
    )

    # Determine source of the change
    source = None
    # Combat damage - use flattened fields
    if update.attacker and update.weapon:
        attacker = update.attacker or "Unknown"
        weapon = update.weapon or "attack"
        damage_type = update.damage_type or ""
        critical = update.critical or False

        # Construct detailed source string
        source = f"{attacker}'s {weapon}"
        if damage_type:
            source += f" ({damage_type})"
        if critical:
            source += " [CRITICAL]"
    # Fallback to direct source if provided
    elif update.source:
        source = update.source

    if character_data:
        # character_data is a NamedTuple with template and instance
        character_instance = character_data.instance
        old_hp = character_instance.current_hp
        new_hp = max(
            0, min(character_instance.max_hp, character_instance.current_hp + delta)
        )
        character_instance.current_hp = new_hp

        # Get character name from template
        character_name = character_data.template.name

        logger.info(
            f"Updated HP for {character_name} ({resolved_char_id}): {old_hp} -> {new_hp} (Delta: {delta})"
        )

        # Update combatant if in combat
        if game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
            if combatant:
                combatant.current_hp = new_hp

        # Emit appropriate event based on combat state
        if game_manager and game_manager.event_queue:
            # Get correlation ID from game_manager if available
            correlation_id = _get_correlation_id(game_manager)

            if game_state.combat.is_active:
                # In combat - emit CombatantHpChangedEvent
                combat_event = CombatantHpChangedEvent(
                    combatant_id=resolved_char_id,
                    combatant_name=character_name,
                    old_hp=old_hp,
                    new_hp=new_hp,
                    max_hp=character_instance.max_hp,
                    change_amount=delta,
                    is_player_controlled=True,
                    source=source,
                    correlation_id=correlation_id,
                )
                game_manager.event_queue.put_event(combat_event)
                logger.debug(
                    f"Emitted CombatantHpChangedEvent for {character_name}: {old_hp} -> {new_hp}"
                )
            else:
                # Not in combat - emit PartyMemberUpdatedEvent
                party_event = PartyMemberUpdatedEvent(
                    character_id=resolved_char_id,
                    character_name=character_name,
                    changes={"current_hp": new_hp, "max_hp": character_instance.max_hp},
                    correlation_id=correlation_id,
                )
                game_manager.event_queue.put_event(party_event)
                logger.debug(
                    f"Emitted PartyMemberUpdatedEvent for {character_name}: HP {old_hp} -> {new_hp}"
                )

        if new_hp == 0:
            logger.info(f"{character_name} has dropped to 0 HP!")

    elif game_state.combat.is_active:
        # Check if NPC exists in combat
        combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
        if not combatant or combatant.is_player:
            logger.error(
                f"Cannot apply HP change: NPC {resolved_char_id} not found in combat."
            )
            return

        old_hp = combatant.current_hp
        new_hp = max(0, min(combatant.max_hp, combatant.current_hp + delta))
        combatant.current_hp = new_hp

        character_name = combatant.name
        logger.info(
            f"Updated HP for NPC {character_name} ({resolved_char_id}): {old_hp} -> {new_hp} (Delta: {delta})"
        )

        # Emit CombatantHpChangedEvent
        if game_manager and game_manager.event_queue:
            # Get correlation ID from game_manager if available
            correlation_id = _get_correlation_id(game_manager)

            event = CombatantHpChangedEvent(
                combatant_id=resolved_char_id,
                combatant_name=character_name,
                old_hp=old_hp,
                new_hp=new_hp,
                max_hp=combatant.max_hp,
                change_amount=delta,
                is_player_controlled=False,
                source=source,
                correlation_id=correlation_id,
            )
            game_manager.event_queue.put_event(event)
            logger.debug(
                f"Emitted CombatantHpChangedEvent for {character_name}: {old_hp} -> {new_hp}"
            )

        if new_hp == 0:
            logger.info(
                f"NPC {character_name} ({resolved_char_id}) has dropped to 0 HP!"
            )
            defeated_condition = "defeated"
            if defeated_condition not in [c.lower() for c in combatant.conditions]:
                combatant.conditions.append(defeated_condition)

                # Emit status change event for defeated condition
                if game_manager and game_manager.event_queue:
                    status_event = CombatantStatusChangedEvent(
                        combatant_id=resolved_char_id,
                        combatant_name=character_name,
                        new_conditions=combatant.conditions,
                        added_conditions=[defeated_condition],
                        removed_conditions=[],
                        is_defeated=True,
                        correlation_id=_get_correlation_id(game_manager),
                    )
                    game_manager.event_queue.put_event(status_event)
                    logger.debug(
                        f"Emitted CombatantStatusChangedEvent for {character_name}: added '{defeated_condition}'"
                    )
    else:
        logger.error(
            f"Cannot apply HP change: Resolved ID '{resolved_char_id}' not found as player or active NPC."
        )


def apply_condition_add(
    game_state: GameStateModel,
    update: ConditionAddUpdateModel,
    resolved_char_id: str,
    game_manager: AIResponseProcessor,
) -> None:
    """Adds a condition to a character or NPC."""
    condition_name = update.value.lower()
    character_data = (
        game_manager.character_service.get_character(resolved_char_id)
        if game_manager
        else None
    )
    target_conditions_list = None
    target_name = (
        game_manager.character_service.get_character_name(resolved_char_id)
        if game_manager
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
        log_msg = (
            f"Added condition '{condition_name}' to {target_name} ({resolved_char_id})"
        )
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
    if changed and game_manager.event_queue:
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
            correlation_id=_get_correlation_id(game_manager),
        )
        game_manager.event_queue.put_event(event)
        logger.debug(
            f"Emitted CombatantStatusChangedEvent for {target_name}: added=[{condition_name}]"
        )


def apply_condition_remove(
    game_state: GameStateModel,
    update: ConditionRemoveUpdateModel,
    resolved_char_id: str,
    game_manager: AIResponseProcessor,
) -> None:
    """Removes a condition from a character or NPC."""
    condition_name = update.value.lower()
    character_data = (
        game_manager.character_service.get_character(resolved_char_id)
        if game_manager
        else None
    )
    target_conditions_list = None
    target_name = (
        game_manager.character_service.get_character_name(resolved_char_id)
        if game_manager
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
    if changed and game_manager.event_queue:
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
            correlation_id=_get_correlation_id(game_manager),
        )
        game_manager.event_queue.put_event(event)
        logger.debug(
            f"Emitted CombatantStatusChangedEvent for {target_name}: removed=[{condition_name}]"
        )


def apply_gold_change(
    game_state: GameStateModel,
    update: GoldUpdateModel,
    resolved_char_id: str,
    game_manager: AIResponseProcessor,
) -> None:
    """Applies gold change to a specific character."""
    character_data = (
        game_manager.character_service.get_character(resolved_char_id)
        if game_manager
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
        if game_manager and game_manager.event_queue:
            # Extract source from flattened fields if available
            gold_source = None
            if update.source:
                gold_source = update.source
            elif update.reason:
                gold_source = update.reason

            event = PartyMemberUpdatedEvent(
                character_id=resolved_char_id,
                character_name=character_data.template.name,
                changes={"gold": character_data.instance.gold},
                gold_source=gold_source,
                correlation_id=_get_correlation_id(game_manager),
            )
            game_manager.event_queue.put_event(event)
            logger.debug(
                f"Emitted PartyMemberUpdatedEvent for {character_data.template.name}: gold {old_gold} -> {character_data.instance.gold}"
            )
    else:
        # Gold changes typically don't apply to NPCs in this manner
        logger.warning(
            f"Attempted to apply gold change to non-player or unknown ID '{resolved_char_id}'. Ignoring."
        )


def apply_inventory_add(
    game_state: GameStateModel,
    update: InventoryAddUpdateModel,
    resolved_char_id: str,
    game_manager: AIResponseProcessor,
) -> None:
    """Adds an item to a character's inventory."""
    character_data = (
        game_manager.character_service.get_character(resolved_char_id)
        if game_manager
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
        if game_manager and game_manager.event_queue:
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
                correlation_id=_get_correlation_id(game_manager),
            )
            game_manager.event_queue.put_event(event)
            logger.debug(
                f"Emitted ItemAddedEvent for {item.name} added to {character_data.template.name}"
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

        item_id = (
            f"simple_{item_name.lower().replace(' ', '_')}_{random.randint(100, 999)}"
        )
        item = ItemModel(
            id=item_id, name=item_name, description=item_description, quantity=quantity
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
        if game_manager and game_manager.event_queue:
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
                correlation_id=_get_correlation_id(game_manager),
            )
            game_manager.event_queue.put_event(event)
            logger.debug(
                f"Emitted ItemAddedEvent for {item.name} added to {character_data.template.name}"
            )


def apply_inventory_remove(
    game_state: GameStateModel,
    update: InventoryRemoveUpdateModel,
    resolved_char_id: str,
    game_manager: AIResponseProcessor,
) -> None:  # pylint: disable=unused-argument
    """Removes an item from a character's inventory."""
    character_data = (
        game_manager.character_service.get_character(resolved_char_id)
        if game_manager
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


def apply_quest_update(
    game_state: GameStateModel,
    update: QuestUpdateModel,
    game_manager: Optional[AIResponseProcessor],
) -> None:
    """Applies updates to an existing quest."""
    quest = game_state.active_quests.get(update.quest_id)
    if not quest:
        logger.warning(
            f"QuestUpdateModel for unknown quest_id '{update.quest_id}'. Ignoring."
        )
        return

    # Track original values for event
    old_status = quest.status

    updated = False
    status_changed = False
    description_changed = False

    # Apply status update
    if update.status and quest.status != update.status:
        logger.info(
            f"Updating quest '{quest.title}' (ID: {update.quest_id}) status: '{quest.status}' -> '{update.status}'."
        )
        quest.status = update.status
        status_changed = True
        updated = True

    # Apply flattened fields update - log any quest-specific fields
    if any(
        [
            update.objectives_completed,
            update.objectives_total,
            update.rewards_experience,
            update.rewards_gold,
            update.rewards_items,
            update.rewards_reputation,
        ]
    ):
        # Log the flattened fields but note that QuestModel doesn't support all of them
        logger.info(
            f"Quest update for '{quest.title}' (ID: {update.quest_id}) includes additional fields"
        )
        logger.warning(
            "QuestModel doesn't support all flattened fields - only status is applied"
        )
        # Still mark as updated to emit the event
        updated = True

    if not updated:
        logger.debug(
            f"QuestUpdateModel for '{update.quest_id}' received but no changes applied."
        )

    # Emit QuestUpdatedEvent if quest was updated
    if updated and game_manager and game_manager.event_queue:
        event = QuestUpdatedEvent(
            quest_id=update.quest_id,
            quest_title=quest.title,
            old_status=old_status if status_changed else None,
            new_status=quest.status if status_changed else old_status,
            description_update=quest.description if description_changed else None,
            correlation_id=_get_correlation_id(game_manager),
        )
        game_manager.event_queue.put_event(event)
        logger.debug(f"Emitted QuestUpdatedEvent for quest '{quest.title}'")


def _get_target_ids_for_update(
    game_state: GameStateModel,
    character_id_field: str,
    game_manager: AIResponseProcessor,
) -> List[str]:
    """
    Resolves a character_id field that might be a specific ID, "party", or "all_players".
    Returns a list of specific character IDs.
    """
    if character_id_field.lower() in ["party", "all_players", "all_pcs"]:
        return list(game_state.party.keys())

    # Try to resolve as a single specific ID
    resolved_id = (
        game_manager.find_combatant_id_by_name_or_id(character_id_field)
        if game_manager
        else character_id_field
    )
    if resolved_id:
        return [resolved_id]

    logger.warning(
        f"Could not resolve '{character_id_field}' to any specific character or party keyword."
    )
    return []
