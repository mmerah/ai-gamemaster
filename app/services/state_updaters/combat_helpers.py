"""Helper functions for combat state processing."""

import logging

from app.core.interfaces import AIResponseProcessor
from app.domain.shared.calculators.dice_mechanics import get_ability_modifier
from app.models.combat import CombatantModel
from app.models.events import CombatantAddedEvent
from app.models.game_state import GameStateModel
from app.models.updates import CombatStartUpdateModel

from .utils import get_correlation_id

logger = logging.getLogger(__name__)


def add_combatants_to_state(
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


def add_combatants_to_active_combat(
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
                correlation_id=get_correlation_id(game_manager),
            )
            game_manager.event_queue.put_event(event)
            logger.debug(f"Emitted CombatantAddedEvent for {npc_name}")
