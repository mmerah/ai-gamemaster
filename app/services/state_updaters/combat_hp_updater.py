"""Processor for combat HP-related state updates."""

import logging
from typing import Optional

from app.core.domain_interfaces import ICharacterService
from app.core.system_interfaces import IEventQueue
from app.models.events.combat import (
    CombatantHpChangedEvent,
    CombatantStatusChangedEvent,
)
from app.models.events.game_state import PartyMemberUpdatedEvent
from app.models.game_state.main import GameStateModel
from app.models.updates import HPChangeUpdateModel
from app.utils.event_helpers import emit_event, emit_with_logging

logger = logging.getLogger(__name__)


class CombatHPUpdater:
    """Handles HP-related state updates during combat."""

    @staticmethod
    def apply_hp_change(
        game_state: GameStateModel,
        update: HPChangeUpdateModel,
        resolved_char_id: str,
        event_queue: IEventQueue,
        correlation_id: Optional[str] = None,
        character_service: Optional[ICharacterService] = None,
    ) -> None:
        """Applies HP changes to a character or NPC."""
        delta = update.value
        character_data = (
            character_service.get_character(resolved_char_id)
            if character_service
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
                emit_with_logging(
                    event_queue, combat_event, f"{character_name}: {old_hp} -> {new_hp}"
                )
            else:
                # Not in combat - emit PartyMemberUpdatedEvent
                party_event = PartyMemberUpdatedEvent(
                    character_id=resolved_char_id,
                    character_name=character_name,
                    changes={
                        "current_hp": new_hp,
                        "max_hp": character_instance.max_hp,
                    },
                    correlation_id=correlation_id,
                )
                emit_with_logging(
                    event_queue,
                    party_event,
                    f"{character_name}: HP {old_hp} -> {new_hp}",
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
            emit_with_logging(
                event_queue, event, f"{character_name}: {old_hp} -> {new_hp}"
            )

            if new_hp == 0:
                logger.info(
                    f"NPC {character_name} ({resolved_char_id}) has dropped to 0 HP!"
                )
                defeated_condition = "defeated"
                if defeated_condition not in [c.lower() for c in combatant.conditions]:
                    combatant.conditions.append(defeated_condition)

                    # Emit status change event for defeated condition
                    status_event = CombatantStatusChangedEvent(
                        combatant_id=resolved_char_id,
                        combatant_name=character_name,
                        new_conditions=combatant.conditions,
                        added_conditions=[defeated_condition],
                        removed_conditions=[],
                        is_defeated=True,
                        correlation_id=correlation_id,
                    )
                    emit_with_logging(
                        event_queue,
                        status_event,
                        f"{character_name}: added '{defeated_condition}'",
                    )
        else:
            logger.error(
                f"Cannot apply HP change: Resolved ID '{resolved_char_id}' not found as player or active NPC."
            )
