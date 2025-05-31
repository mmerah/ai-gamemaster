import logging
import random
from typing import Dict, List, Optional

from .models import GameState
from .models import Combatant, CombatState
from app.ai_services.schemas import (
    GoldUpdate, HPChangeUpdate, ConditionUpdate, CombatStartUpdate, CombatEndUpdate,
    CombatantRemoveUpdate, InventoryUpdate, QuestUpdate, InitialCombatantData, MonsterBaseStats
)
from app.events.game_update_events import (
    CombatStartedEvent, CombatantHpChangedEvent, CombatantStatusChangedEvent,
    CombatantAddedEvent, CombatantRemovedEvent, PartyMemberUpdatedEvent,
    QuestUpdatedEvent, ItemAddedEvent
)

logger = logging.getLogger(__name__)

def _get_correlation_id(game_manager) -> Optional[str]:
    """Get correlation ID from game_manager if available."""
    if game_manager and hasattr(game_manager, '_current_correlation_id'):
        return game_manager._current_correlation_id
    return None

def _add_combatants_to_state(game_state: GameState, combat_update: CombatStartUpdate, game_manager):
    """Adds player and NPC combatants to the combat state."""
    combat = game_state.combat
    # Add Players
    for pc_id, pc_instance in game_state.party.items():
        # Get DEX modifier for initiative tie-breaking
        dex_score = pc_instance.base_stats.DEX if hasattr(pc_instance, 'base_stats') else 10
        dex_modifier = (dex_score - 10) // 2
        
        combatant = Combatant(
            id=pc_id,
            name=pc_instance.name,
            initiative=-1,  # Will be set later
            initiative_modifier=dex_modifier,
            current_hp=pc_instance.current_hp,
            max_hp=pc_instance.max_hp,
            armor_class=pc_instance.armor_class,
            conditions=pc_instance.conditions.copy(),
            is_player=True,
            icon_path=getattr(pc_instance, 'portrait_path', None)
        )
        combat.combatants.append(combatant)
        logger.debug(f"Added player {pc_instance.name} ({pc_id}) to initial combatants list.")

    # Add NPCs/Monsters
    for npc_data in combat_update.combatants:
        npc_id = npc_data.id
        npc_name = npc_data.name
        if npc_id in combat.monster_stats or npc_id in game_state.party:
            logger.warning(f"Duplicate combatant ID '{npc_id}' provided in combat_start. Skipping.")
            continue

        initial_hp = npc_data.hp
        if initial_hp <= 0:
            logger.warning(f"AI tried to start combat with defeated NPC '{npc_name}' (ID: {npc_id}, HP: {initial_hp}). Skipping.")
            continue

        # Calculate DEX modifier from stats
        dex_score = npc_data.stats.get("DEX", 10) if npc_data.stats else 10
        dex_modifier = (dex_score - 10) // 2
        
        combatant = Combatant(
            id=npc_id,
            name=npc_name,
            initiative=-1,  # Will be set later
            initiative_modifier=dex_modifier,
            current_hp=initial_hp,
            max_hp=initial_hp,
            armor_class=npc_data.ac,
            conditions=[],
            is_player=False,
            icon_path=npc_data.icon_path
        )
        combat.combatants.append(combatant)
        
        # Store additional NPC data in monster_stats
        combat.monster_stats[npc_id] = MonsterBaseStats(
            name=npc_name,
            initial_hp=initial_hp,
            ac=npc_data.ac,
            stats=npc_data.stats or {"DEX": 10},
            abilities=npc_data.abilities or [],
            attacks=npc_data.attacks or []
        )
        logger.debug(f"Added NPC {npc_name} ({npc_id}) to combat tracker and combatants list.")

def _add_combatants_to_active_combat(game_state: GameState, combat_update: CombatStartUpdate, game_manager):
    """Adds new combatants to active combat (reinforcements)."""
    combat = game_state.combat
    
    # Only add NPCs/Monsters during active combat (not player characters)
    for npc_data in combat_update.combatants:
        npc_id = npc_data.id
        npc_name = npc_data.name
        if npc_id in combat.monster_stats or npc_id in game_state.party:
            logger.warning(f"Duplicate combatant ID '{npc_id}' provided in combat_start. Skipping.")
            continue

        initial_hp = npc_data.hp
        if initial_hp <= 0:
            logger.warning(f"AI tried to add defeated NPC '{npc_name}' (ID: {npc_id}, HP: {initial_hp}). Skipping.")
            continue

        # Calculate DEX modifier from stats
        dex_score = npc_data.stats.get("DEX", 10) if npc_data.stats else 10
        dex_modifier = (dex_score - 10) // 2
        
        # Create combatant with enhanced model
        combatant = Combatant(
            id=npc_id,
            name=npc_name,
            initiative=-1,  # Will be set later
            initiative_modifier=dex_modifier,
            current_hp=initial_hp,
            max_hp=initial_hp,
            armor_class=npc_data.ac,
            conditions=[],
            is_player=False,
            icon_path=npc_data.icon_path
        )
        combat.combatants.append(combatant)
        
        # Store additional NPC data in monster_stats
        combat.monster_stats[npc_id] = MonsterBaseStats(
            name=npc_name,
            initial_hp=initial_hp,
            ac=npc_data.ac,
            stats=npc_data.stats or {"DEX": 10},
            abilities=npc_data.abilities or [],
            attacks=npc_data.attacks or []
        )
        
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
                position_in_order=len(combat.combatants) - 1,  # Position at end
                correlation_id=_get_correlation_id(game_manager)
            )
            game_manager.event_queue.put_event(event)
            logger.debug(f"Emitted CombatantAddedEvent for {npc_name}")

def start_combat(game_state: GameState, update: CombatStartUpdate, game_manager):
    """Initializes combat state or adds combatants to existing combat."""
    if game_state.combat.is_active:
        logger.info("Received combat_start while combat is already active. Adding new combatants.")
        # Add new combatants to existing combat
        _add_combatants_to_active_combat(game_state, update, game_manager)
        return

    logger.info("Starting combat! Populating initial combatants list.")
    game_state.combat = CombatState(is_active=True, round_number=1, current_turn_index=0)
    _add_combatants_to_state(game_state, update, game_manager)
    logger.info(f"Combat started with {len(game_state.combat.combatants)} participants (Initiative Pending).")
    game_state.combat._combat_just_started_flag = True
    
    # Emit CombatStartedEvent
    if game_manager and game_manager.event_queue:
        # Build combatants list for the event
        combatants_data = []
        
        # Add all combatants (players and NPCs)
        for combatant in game_state.combat.combatants:
            if combatant.is_player:
                # Get player character instance
                pc_instance = game_state.party.get(combatant.id)
                if pc_instance:
                    combatants_data.append({
                        "id": combatant.id,
                        "name": combatant.name,
                        "is_player": True,
                        "hp": pc_instance.current_hp,
                        "max_hp": pc_instance.max_hp,
                        "ac": pc_instance.armor_class,
                        "initiative": combatant.initiative
                    })
            else:
                # Add NPC combatants (now using enhanced combatant data)
                combatants_data.append({
                    "id": combatant.id,
                    "name": combatant.name,
                    "is_player": False,
                    "hp": combatant.current_hp,
                    "max_hp": combatant.max_hp,
                    "ac": combatant.armor_class,
                    "initiative": combatant.initiative
                })
        
        event = CombatStartedEvent(
            combatants=combatants_data,
            correlation_id=_get_correlation_id(game_manager)
        )
        game_manager.event_queue.put_event(event)
        logger.debug(f"Emitted CombatStartedEvent with {len(combatants_data)} combatants")

def end_combat(game_state: GameState, update: CombatEndUpdate, game_manager=None):
    """Finalizes combat state."""
    if not game_state.combat.is_active:
        logger.warning("Received combat_end while combat is not active. Ignoring.")
        return
    reason = update.details.get("reason", "Not specified") if update.details else "Not specified"
    logger.info(f"Ending combat. Reason: {reason}")
    
    # Emit CombatEndedEvent before clearing combat state
    if game_manager and game_manager.event_queue:
        from app.events.game_update_events import CombatEndedEvent
        event = CombatEndedEvent(
            reason=reason,
            outcome_description=update.details.get("outcome_description") if update.details else None,
            correlation_id=_get_correlation_id(game_manager)
        )
        game_manager.event_queue.put_event(event)
        logger.debug(f"Emitted CombatEndedEvent with reason: {reason}")
    
    game_state.combat = CombatState()
    
    # Clear stored RAG context when combat ends since context changes significantly
    if hasattr(game_state, '_last_rag_context'):
        game_state._last_rag_context = None
        logger.debug("Cleared stored RAG context due to combat end")

def remove_combatant_from_state(game_state: GameState, combatant_id_to_remove: str, details: Optional[Dict], game_manager):
    """Removes a combatant from active combat."""
    combat = game_state.combat
    if not combat.is_active:
        logger.warning(f"Attempted to remove '{combatant_id_to_remove}' but combat not active.")
        if combatant_id_to_remove in combat.monster_stats:
            del combat.monster_stats[combatant_id_to_remove]
        return
    
    removed_index = -1
    # Find the index of the combatant to be removed IN THE CURRENT LIST
    for i, c in enumerate(combat.combatants):
        if c.id == combatant_id_to_remove:
            removed_index = i
            break

    if removed_index == -1:
        logger.warning(f"Could not find '{combatant_id_to_remove}' in combatants list to remove.")
        return

    # Get name and details before removal for logging and event
    removed_combatant = combat.combatants[removed_index]
    removed_combatant_name = removed_combatant.name
    
    # Remove the combatant
    del combat.combatants[removed_index]
    
    reason = details.get("reason", "Removed") if details else "Removed"
    logger.info(f"Removed combatant '{removed_combatant_name}' (ID: {combatant_id_to_remove}) from combat. Reason: {reason}")
    
    # Emit CombatantRemovedEvent
    if game_manager and game_manager.event_queue:
        event = CombatantRemovedEvent(
            combatant_id=combatant_id_to_remove,
            combatant_name=removed_combatant_name,
            reason=reason,
            correlation_id=_get_correlation_id(game_manager)
        )
        game_manager.event_queue.put_event(event)
        logger.debug(f"Emitted CombatantRemovedEvent for {removed_combatant_name} (reason: {reason})")

    # Adjust current_turn_index
    # If the removed combatant was before the current turn's combatant in the list,
    # or if the removed combatant *was* the current turn's combatant and was at an index
    # now out of bounds or equal to the new list length.
    if removed_index < combat.current_turn_index:
        combat.current_turn_index -= 1
        logger.debug(f"Adjusted current_turn_index due to removal before current: new index {combat.current_turn_index}")
    elif removed_index == combat.current_turn_index:
        # If the removed combatant *was* the current one, the turn effectively ends for them.
        # The advance_turn logic will then pick the "next" one.
        # However, the index might now point to the combatant that *was* after the removed one.
        # Or, if it was the last in the list, current_turn_index might need to wrap around or be re-evaluated.
        # Let's ensure it's not out of bounds. If it becomes equal to len, advance_turn will handle wrap-around.
        if combat.current_turn_index >= len(combat.combatants) and len(combat.combatants) > 0:
            combat.current_turn_index = 0 # Wrap around if it was the last one
            logger.debug(f"Current turn combatant removed was last; wrapped index to 0.")
        # No change needed if it points to the new combatant at the same index,
        # as advance_turn will increment it.
        logger.debug(f"Current turn combatant '{removed_combatant_name}' removed. Index remains {combat.current_turn_index} (relative to new list).")

    # Ensure current_turn_index is valid if list becomes empty (should be handled by combat end)
    if not combat.combatants:
        logger.info("All combatants removed.")
        # Combat end should be triggered by check_and_end_combat_if_over
    elif combat.current_turn_index >= len(combat.combatants):
        logger.warning(f"current_turn_index ({combat.current_turn_index}) is out of bounds after removal. Resetting to 0.")
        combat.current_turn_index = 0

    if combatant_id_to_remove in combat.monster_stats:
        del combat.monster_stats[combatant_id_to_remove]
        logger.debug(f"Removed '{combatant_id_to_remove}' from monster_stats.")

def check_and_end_combat_if_over(game_state: GameState, game_manager):
    """Checks if combat should end automatically (e.g., all NPCs defeated)."""
    if not game_state.combat.is_active:
        return

    active_npcs_found = any(
        not c.is_player and not c.is_defeated
        for c in game_state.combat.combatants
    )

    if not active_npcs_found:
        logger.info("Auto-detect: No active non-player combatants remaining. Ending combat.")
        end_combat(game_state, CombatEndUpdate(type="combat_end", details={"reason": "No active enemies remaining"}), game_manager)

def apply_hp_change(game_state: GameState, update: HPChangeUpdate, resolved_char_id: str, game_manager):
    """Applies HP changes to a character or NPC."""
    delta = update.value
    player = game_manager.character_service.get_character(resolved_char_id) if game_manager else None
    
    # Determine source of the change
    source = update.details.get("source") if update.details else None

    if player:
        old_hp = player.current_hp
        new_hp = max(0, min(player.max_hp, player.current_hp + delta))
        player.current_hp = new_hp
        
        logger.info(f"Updated HP for {player.name} ({resolved_char_id}): {old_hp} -> {new_hp} (Delta: {delta})")
        
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
                event = CombatantHpChangedEvent(
                    combatant_id=resolved_char_id,
                    combatant_name=player.name,
                    old_hp=old_hp,
                    new_hp=new_hp,
                    max_hp=player.max_hp,
                    change_amount=delta,
                    is_player_controlled=True,
                    source=source,
                    correlation_id=correlation_id
                )
                game_manager.event_queue.put_event(event)
                logger.debug(f"Emitted CombatantHpChangedEvent for {player.name}: {old_hp} -> {new_hp}")
            else:
                # Not in combat - emit PartyMemberUpdatedEvent
                event = PartyMemberUpdatedEvent(
                    character_id=resolved_char_id,
                    character_name=player.name,
                    changes={"hp": {"old": old_hp, "new": new_hp}},
                    correlation_id=correlation_id
                )
                game_manager.event_queue.put_event(event)
                logger.debug(f"Emitted PartyMemberUpdatedEvent for {player.name}: HP {old_hp} -> {new_hp}")
        
        if new_hp == 0:
            logger.info(f"{player.name} has dropped to 0 HP!")
            
    elif game_state.combat.is_active:
        # Check if NPC exists in combat
        combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
        if not combatant or combatant.is_player:
            logger.error(f"Cannot apply HP change: NPC {resolved_char_id} not found in combat.")
            return
        
        old_hp = combatant.current_hp
        new_hp = max(0, min(combatant.max_hp, combatant.current_hp + delta))
        combatant.current_hp = new_hp
        
        character_name = combatant.name
        logger.info(f"Updated HP for NPC {character_name} ({resolved_char_id}): {old_hp} -> {new_hp} (Delta: {delta})")
        
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
                correlation_id=correlation_id
            )
            game_manager.event_queue.put_event(event)
            logger.debug(f"Emitted CombatantHpChangedEvent for {character_name}: {old_hp} -> {new_hp}")
        
        if new_hp == 0:
            logger.info(f"NPC {character_name} ({resolved_char_id}) has dropped to 0 HP!")
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
                        correlation_id=_get_correlation_id(game_manager)
                    )
                    game_manager.event_queue.put_event(status_event)
                    logger.debug(f"Emitted CombatantStatusChangedEvent for {character_name}: added '{defeated_condition}'")
    else:
        logger.error(f"Cannot apply HP change: Resolved ID '{resolved_char_id}' not found as player or active NPC.")

def apply_condition_update(game_state: GameState, update: ConditionUpdate, resolved_char_id: str, game_manager):
    """Applies condition changes to a character or NPC."""
    condition_name = update.value.lower()
    player = game_manager.character_service.get_character(resolved_char_id) if game_manager else None
    target_conditions_list = None
    target_name = game_manager.character_service.get_character_name(resolved_char_id) if game_manager else resolved_char_id
    is_player = False

    if player:
        target_conditions_list = player.conditions
        is_player = True
        target_name = player.name
    elif game_state.combat.is_active:
        combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
        if combatant and not combatant.is_player:
            target_conditions_list = combatant.conditions
            is_player = False
            target_name = combatant.name
        else:
            logger.error(f"Cannot apply Condition update: NPC '{resolved_char_id}' not found in combat.")
            return
    else:
        logger.error(f"Cannot apply Condition update: Resolved ID '{resolved_char_id}' not found.")
        return

    # Track changes for event emission
    added_conditions = []
    removed_conditions = []
    changed = False

    if update.type == "condition_add":
        if condition_name not in target_conditions_list:
            target_conditions_list.append(condition_name)
            added_conditions.append(condition_name)
            changed = True
            logger.info(f"Added condition '{condition_name}' to {target_name} ({resolved_char_id})")
        else:
            logger.debug(f"Condition '{condition_name}' already present on {target_name} ({resolved_char_id})")
    elif update.type == "condition_remove":
        if condition_name in target_conditions_list:
            target_conditions_list.remove(condition_name)
            removed_conditions.append(condition_name)
            changed = True
            logger.info(f"Removed condition '{condition_name}' from {target_name} ({resolved_char_id})")
        else:
            logger.debug(f"Condition '{condition_name}' not found on {target_name} ({resolved_char_id}) to remove")

    # Emit CombatantStatusChangedEvent if conditions changed
    if changed and game_manager.event_queue:
        # Check if character is defeated (HP = 0 or has "defeated" condition)
        is_defeated = "defeated" in [c.lower() for c in target_conditions_list]
        if not is_defeated and player:
            is_defeated = player.current_hp <= 0
        elif not is_defeated and not is_player:
            # Check NPC HP from combatant
            combatant = game_state.combat.get_combatant_by_id(resolved_char_id)
            is_defeated = combatant and combatant.current_hp <= 0

        event = CombatantStatusChangedEvent(
            combatant_id=resolved_char_id,
            combatant_name=target_name,
            new_conditions=list(target_conditions_list),  # Copy to avoid reference issues
            added_conditions=added_conditions,
            removed_conditions=removed_conditions,
            is_defeated=is_defeated,
            correlation_id=_get_correlation_id(game_manager)
        )
        game_manager.event_queue.put_event(event)
        logger.debug(f"Emitted CombatantStatusChangedEvent for {target_name}: added={added_conditions}, removed={removed_conditions}")

def apply_gold_change(game_state: GameState, update: GoldUpdate, resolved_char_id: str, game_manager):
    """Applies gold change to a specific character."""
    player = game_manager.character_service.get_character(resolved_char_id) if game_manager else None
    if player:
        old_gold = player.gold
        player.gold += update.value
        logger.info(f"Updated gold for {player.name} ({resolved_char_id}): {old_gold} -> {player.gold} (Delta: {update.value})")
    else:
        # Gold changes typically don't apply to NPCs in this manner
        logger.warning(f"Attempted to apply gold change to non-player or unknown ID '{resolved_char_id}'. Ignoring.")

# Placeholder for inventory - needs more fleshing out based on Item model
def apply_inventory_update(game_state: GameState, update: InventoryUpdate, resolved_char_id: str, game_manager):
    player = game_manager.character_service.get_character(resolved_char_id) if game_manager else None
    if not player:
        logger.warning(f"InventoryUpdate: Character ID '{resolved_char_id}' not found. Ignoring update.")
        return

    item_value = update.value
    item_name = ""

    if update.type == "inventory_add":
        # Assuming value is a dict for new items, or string for simple item names (less ideal)
        if isinstance(item_value, dict):
            item_name = item_value.get("name", "Unknown Item")
            item_description = item_value.get("description", "")
            # Potentially create an Item object here if your inventory stores them
            # For now, let's assume we just log it or add the dict directly if schema allows
            # Or Item(**item_value)
            player.inventory.append(item_value)
            logger.info(f"Added item '{item_name}' to {player.name}'s inventory.")
            
            # Emit ItemAddedEvent
            if game_manager and game_manager.event_queue:
                event = ItemAddedEvent(
                    character_id=resolved_char_id,
                    character_name=player.name,
                    item_name=item_name,
                    item_description=item_description,
                    quantity=item_value.get("quantity", 1),
                    correlation_id=_get_correlation_id(game_manager)
                )
                game_manager.event_queue.put_event(event)
                logger.debug(f"Emitted ItemAddedEvent for {item_name} added to {player.name}")
        elif isinstance(item_value, str):
            item_name = item_value
            player.inventory.append({"name": item_name, "id": f"simple_{item_name.lower().replace(' ','_')}_{random.randint(100,999)}"}) # Example simple add
            logger.info(f"Added simple item '{item_name}' to {player.name}'s inventory.")
            
            # Emit ItemAddedEvent
            if game_manager and game_manager.event_queue:
                event = ItemAddedEvent(
                    character_id=resolved_char_id,
                    character_name=player.name,
                    item_name=item_name,
                    item_description="",
                    quantity=1,
                    correlation_id=_get_correlation_id(game_manager)
                )
                game_manager.event_queue.put_event(event)
                logger.debug(f"Emitted ItemAddedEvent for {item_name} added to {player.name}")
        else:
            logger.error(f"Inventory_add: Invalid item value type for {player.name}: {item_value}")

    elif update.type == "inventory_remove":
        # Value could be an item name (string) or an item ID (string)
        # This requires searching the inventory
        item_to_find = str(item_value)
        found_item_idx = -1
        for i, item_in_inv in enumerate(player.inventory):
            if isinstance(item_in_inv, dict) and (item_in_inv.get("name") == item_to_find or item_in_inv.get("id") == item_to_find):
                found_item_idx = i
                item_name = item_in_inv.get("name", item_to_find)
                break
            elif isinstance(item_in_inv, str) and item_in_inv == item_to_find:
                found_item_idx = i
                item_name = item_in_inv
                break
        
        if found_item_idx != -1:
            del player.inventory[found_item_idx]
            logger.info(f"Removed item '{item_name}' from {player.name}'s inventory.")
        else:
            logger.warning(f"Inventory_remove: Item '{item_to_find}' not found in {player.name}'s inventory.")

def apply_quest_update(game_state: GameState, update: QuestUpdate, game_manager=None):
    """Applies updates to an existing quest."""
    quest = game_state.active_quests.get(update.quest_id)
    if not quest:
        logger.warning(f"QuestUpdate for unknown quest_id '{update.quest_id}'. Ignoring.")
        return

    # Track original values for event
    old_status = quest.status
    
    updated = False
    status_changed = False
    description_changed = False
    
    # Apply status update
    if update.status and quest.status != update.status:
        logger.info(f"Updating quest '{quest.title}' (ID: {update.quest_id}) status: '{quest.status}' -> '{update.status}'.")
        quest.status = update.status
        status_changed = True
        updated = True
    
    # Apply details update
    if update.details:
        if not isinstance(quest.details, dict): 
            quest.details = {}
        logger.info(f"Merging details into quest '{quest.title}' (ID: {update.quest_id}): {update.details}")
        quest.details.update(update.details)
        updated = True
    
    if not updated:
        logger.debug(f"QuestUpdate for '{update.quest_id}' received but no changes applied.")
    
    # Emit QuestUpdatedEvent if quest was updated
    if updated and game_manager and hasattr(game_manager, 'event_queue') and game_manager.event_queue:
        event = QuestUpdatedEvent(
            quest_id=update.quest_id,
            quest_title=quest.title,
            old_status=old_status if status_changed else None,
            new_status=quest.status if status_changed else old_status,
            description_update=quest.description if description_changed else None,
            correlation_id=_get_correlation_id(game_manager)
        )
        game_manager.event_queue.put_event(event)
        logger.debug(f"Emitted QuestUpdatedEvent for quest '{quest.title}'")

def _get_target_ids_for_update(game_state: GameState, character_id_field: str, game_manager) -> List[str]:
    """
    Resolves a character_id field that might be a specific ID, "party", or "all_players".
    Returns a list of specific character IDs.
    """
    if character_id_field.lower() in ["party", "all_players", "all_pcs"]:
        return list(game_state.party.keys())
    
    # Try to resolve as a single specific ID
    resolved_id = game_manager.find_combatant_id_by_name_or_id(character_id_field) if game_manager else character_id_field
    if resolved_id:
        return [resolved_id]
    
    logger.warning(f"Could not resolve '{character_id_field}' to any specific character or party keyword.")
    return []

def apply_game_state_updates(game_state: GameState, updates: list, game_manager) -> bool:
    """
    Applies a list of validated GameStateUpdate objects to the game state.
    Returns True if combat was started during these updates.
    """
    if not updates:
        return False

    logger.info(f"Applying {len(updates)} game state update(s)...")
    combat_started_this_update_cycle = False
    combat_explicitly_ended_by_ai = False

    for update_obj in updates:
        update_type = getattr(update_obj, 'type', None)
        if not update_type:
            logger.error(f"Skipping game state update with missing 'type': {update_obj}")
            continue
        
        # Get the raw character_id string from the AI's update
        raw_char_id_from_ai = getattr(update_obj, 'character_id', None)

        # Determine target IDs: can be single or multiple (for "party")
        target_ids: List[str] = []
        if raw_char_id_from_ai:
            # For updates that can target "party" (like ConditionUpdate, GoldUpdate)
            if update_type in ["condition_add", "condition_remove", "gold_change", "inventory_add", "inventory_remove"]:
                 target_ids = _get_target_ids_for_update(game_state, raw_char_id_from_ai, game_manager)
            else: # For other updates, assume it's a single specific ID
                specific_id = game_manager.find_combatant_id_by_name_or_id(raw_char_id_from_ai)
                if specific_id:
                    target_ids = [specific_id]
        
        if not target_ids and raw_char_id_from_ai and update_type not in ["combat_start", "combat_end", "quest_update"]:
            # If raw_char_id was provided but couldn't be resolved and it's not a global update type
            logger.error(f"{update_type.capitalize()}: Unknown character_id '{raw_char_id_from_ai}' and not a party keyword.")
            
            # Emit GameErrorEvent for invalid character reference
            if hasattr(game_manager, 'event_queue') and game_manager.event_queue:
                from app.events.game_update_events import GameErrorEvent
                error_event = GameErrorEvent(
                    error_message=f"Unknown character_id '{raw_char_id_from_ai}' and not a party keyword",
                    error_type="invalid_reference",
                    severity="warning",
                    recoverable=True,
                    context={
                        "character_id": raw_char_id_from_ai,
                        "update_type": update_type
                    },
                    correlation_id=_get_correlation_id(game_manager)
                )
                game_manager.event_queue.put_event(error_event)
                logger.debug(f"Emitted GameErrorEvent for invalid character reference: {raw_char_id_from_ai}")
            
            continue # Skip this update if no valid target

        logger.debug(f"Applying update: {update_obj.model_dump_json(indent=2)} to targets: {target_ids or 'Global'}")

        try:
            # Updates that iterate over target_ids
            if update_type == "hp_change" and isinstance(update_obj, HPChangeUpdate):
                for char_id in target_ids: apply_hp_change(game_state, update_obj, char_id, game_manager)
            elif update_type in ["condition_add", "condition_remove"] and isinstance(update_obj, ConditionUpdate):
                for char_id in target_ids: apply_condition_update(game_state, update_obj, char_id, game_manager)
            elif update_type == "gold_change" and isinstance(update_obj, GoldUpdate):
                for char_id in target_ids: apply_gold_change(game_state, update_obj, char_id, game_manager)
            elif update_type in ["inventory_add", "inventory_remove"] and isinstance(update_obj, InventoryUpdate):
                 for char_id in target_ids: apply_inventory_update(game_state, update_obj, char_id, game_manager)
            
            # Updates that don't iterate or have specific targetting logic
            elif update_type == "combat_start" and isinstance(update_obj, CombatStartUpdate):
                start_combat(game_state, update_obj, game_manager)
                combat_started_this_update_cycle = True
            elif update_type == "combat_end" and isinstance(update_obj, CombatEndUpdate):
                if game_state.combat.is_active:
                    end_combat(game_state, update_obj, game_manager)
                    combat_explicitly_ended_by_ai = True
                else:
                    logger.warning("AI sent 'combat_end' but combat was already inactive.")
            elif update_type == "combatant_remove" and isinstance(update_obj, CombatantRemoveUpdate):
                # combatant_remove should always have a specific ID from the AI
                specific_id_for_removal = game_manager.find_combatant_id_by_name_or_id(update_obj.character_id)
                if specific_id_for_removal:
                    remove_combatant_from_state(game_state, specific_id_for_removal, update_obj.details, game_manager)
                else:
                    logger.error(f"CombatantRemove: Unknown character_id '{update_obj.character_id}'")
                    
                    # Emit GameErrorEvent for invalid combatant removal
                    if hasattr(game_manager, 'event_queue') and game_manager.event_queue:
                        from app.events.game_update_events import GameErrorEvent
                        error_event = GameErrorEvent(
                            error_message=f"CombatantRemove: Unknown character_id '{update_obj.character_id}'",
                            error_type="invalid_reference",
                            severity="warning",
                            recoverable=True,
                            context={
                                "character_id": update_obj.character_id,
                                "update_type": "combatant_remove"
                            },
                            correlation_id=_get_correlation_id(game_manager)
                        )
                        game_manager.event_queue.put_event(error_event)
                        logger.debug(f"Emitted GameErrorEvent for invalid combatant removal: {update_obj.character_id}")
            elif update_type == "quest_update" and isinstance(update_obj, QuestUpdate):
                apply_quest_update(game_state, update_obj, game_manager) # Quest updates are global by quest_id
            else:
                # This case might be hit if an update type was meant to iterate but wasn't listed above,
                # or if it's an unhandled type.
                if target_ids: # If we resolved target_ids but didn't have a loop for this type
                    logger.warning(f"Unhandled game state update type '{update_type}' for resolved targets {target_ids}.")
                elif update_type not in ["combat_start", "combat_end", "quest_update"]: # If no targets and not a global type
                    logger.warning(f"Unhandled game state update type: {update_type} or mismatched Pydantic model (no targets resolved).")

        except AttributeError as ae:
            logger.error(f"Attribute error applying {update_type}: {ae}. Check schema vs handler.", exc_info=True)
        except Exception as e:
            logger.error(f"Error applying {update_type} ({update_obj.model_dump()}): {e}", exc_info=True)

    if game_state.combat.is_active and not combat_explicitly_ended_by_ai:
        check_and_end_combat_if_over(game_state, game_manager)

    return combat_started_this_update_cycle
