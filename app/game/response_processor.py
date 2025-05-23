import logging
import random
from typing import List, Dict, Tuple, Optional

from app.ai_services.schemas import AIResponse
from .models import GameState
from . import state_processors

logger = logging.getLogger(__name__)

class ResponseProcessor:
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def _handle_narrative_and_location(self, ai_response: AIResponse):
        """Adds AI narrative to history and updates location."""
        if ai_response.reasoning:
            logger.info(f"AI Reasoning: {ai_response.reasoning}")
        else:
            logger.warning("AI Response missing 'reasoning'.")

        # Add full AI response JSON to history for assistant messages
        self.game_manager.add_chat_message(
            "assistant",
            ai_response.narrative,
            ai_response_json=ai_response.model_dump_json()
        )
        self.game_manager.update_location(ai_response.location_update)

    def _handle_game_state_updates(self, ai_response: AIResponse) -> bool:
        """Applies game state updates from AI response."""
        return state_processors.apply_game_state_updates(
            self.game_manager.get_current_state_model(),
            ai_response.game_state_updates,
            self.game_manager
        )

    def _resolve_dice_request_character_ids(self, req_char_ids_input: List[str]) -> List[str]:
        """Resolves 'all' and specific character IDs for a dice request."""
        game_state = self.game_manager.get_current_state_model()
        party_char_ids_set = set(game_state.party.keys())
        resolved_char_ids = set()

        if "all" in req_char_ids_input:
            if game_state.combat.is_active:
                # Include only non-defeated combatants if 'all' is used in combat
                for c in game_state.combat.combatants:
                    is_defeated = False
                    player = self.game_manager.character_service.get_character(c.id)
                    if player and player.current_hp <= 0: is_defeated = True
                    elif c.id in game_state.combat.monster_stats:
                        monster = game_state.combat.monster_stats[c.id]
                        if monster.get("hp", 1) <= 0 or "Defeated" in monster.get("conditions", []):
                            is_defeated = True
                    if not is_defeated:
                        resolved_char_ids.add(c.id)
                logger.info(f"Expanding 'all' in dice request to ACTIVE combatants: {list(resolved_char_ids)}")
            else:
                # All party members if not in combat
                resolved_char_ids.update(party_char_ids_set)
                logger.info(f"Expanding 'all' in dice request to party members: {list(resolved_char_ids)}")
            # Add any other specific IDs mentioned alongside 'all'
            for specific_id in req_char_ids_input:
                if specific_id != "all":
                    resolved = self.game_manager.find_combatant_id_by_name_or_id(specific_id)
                    if resolved: resolved_char_ids.add(resolved)
        else:
            for specific_id_input in req_char_ids_input:
                resolved = self.game_manager.find_combatant_id_by_name_or_id(specific_id_input)
                if resolved: resolved_char_ids.add(resolved)
                else: logger.warning(f"Could not resolve ID '{specific_id_input}' in dice request.")
        
        return list(resolved_char_ids)

    def _perform_npc_rolls(self, npc_requests_to_roll: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Performs NPC rolls internally and returns if rolls were made and their results."""
        game_state = self.game_manager.get_current_state_model()
        npc_roll_results = []
        npc_rolls_performed = False

        if not npc_requests_to_roll:
            return False, []

        logger.info(f"Performing {len(npc_requests_to_roll)} NPC roll request(s) internally...")
        for npc_req in npc_requests_to_roll:
            for npc_id in npc_req.get("character_ids", []):
                # Check defeat status before rolling for NPC
                is_defeated = False
                if game_state.combat.is_active and npc_id in game_state.combat.monster_stats:
                    monster = game_state.combat.monster_stats[npc_id]
                    if monster.get("hp", 1) <= 0 or "Defeated" in monster.get("conditions", []):
                        is_defeated = True
                        logger.debug(f"Skipping roll for defeated NPC: {self.game_manager.get_combatant_name(npc_id)} ({npc_id})")
                elif not game_state.combat.is_active:
                    # Should not happen if NPC is in combat request
                    logger.warning(f"Attempting NPC roll for {npc_id} outside of active combat. Skipping.")
                    continue
                elif npc_id not in game_state.combat.monster_stats:
                    # NPC not in tracker
                    logger.error(f"Attempting NPC roll for {npc_id} but they are not in monster_stats. Skipping.")
                    continue

                if is_defeated:
                    continue

                # Perform the roll
                roll_result = self.game_manager.perform_roll(
                    character_id=npc_id, roll_type=npc_req.get("type"),
                    dice_formula=npc_req.get("dice_formula"), skill=npc_req.get("skill"),
                    ability=npc_req.get("ability"), dc=npc_req.get("dc"),
                    reason=npc_req.get("reason", ""),
                    original_request_id=npc_req.get("request_id")
                )
                if roll_result and "error" not in roll_result:
                    npc_roll_results.append(roll_result)
                    npc_rolls_performed = True
                elif roll_result: # Error in roll
                    error_msg = f"(Error rolling for NPC {self.game_manager.get_combatant_name(npc_id)}: {roll_result.get('error')})"
                    logger.error(error_msg)
                    self.game_manager.add_chat_message("system", error_msg, is_dice_result=True)
        
        # Store NPC roll results for initiative determination or AI context
        if npc_roll_results:
            game_state._pending_npc_roll_results.extend(npc_roll_results)
            # Add to history
            npc_roll_summaries = [r.get("result_summary") for r in npc_roll_results if r.get("result_summary")]
            npc_detailed_messages = [r.get("result_message", r.get("result_summary")) for r in npc_roll_results if r.get("result_message") or r.get("result_summary")]
            if npc_roll_summaries:
                combined_summary = "**NPC Rolls:**\n" + "\n".join(npc_roll_summaries)
                combined_detailed = "**NPC Rolls:**\n" + "\n".join(npc_detailed_messages)
                self.game_manager.add_chat_message("user", combined_summary, is_dice_result=True, detailed_content=combined_detailed)

        return npc_rolls_performed, npc_roll_results


    def _handle_dice_requests(self, ai_response: AIResponse, combat_just_started: bool) -> Tuple[List[Dict], bool, bool]:
        """
        Processes dice requests from AI, separating player/NPC rolls, performing NPC rolls.
        Returns: (pending_player_dice_requests, npc_rolls_performed, needs_ai_rerun_due_to_npc_rolls)
        """
        game_state = self.game_manager.get_current_state_model()
        party_char_ids_set = set(game_state.party.keys())
        
        player_requests_to_send = []
        npc_requests_to_roll_internally = []
        has_initiative_request_from_ai = False

        for req_obj in ai_response.dice_requests:
            req_dict = req_obj.model_dump()
            req_char_ids_input = req_dict.get("character_ids", [])
            if not req_char_ids_input:
                logger.warning(f"Dice request missing character_ids: {req_dict}")
                continue

            resolved_char_ids = self._resolve_dice_request_character_ids(req_char_ids_input)
            if not resolved_char_ids:
                logger.error(f"Could not resolve any valid character IDs for dice request: {req_dict}")
                continue
            
            # Update with resolved list
            req_dict["character_ids"] = resolved_char_ids
            if req_dict.get("type") == "initiative":
                has_initiative_request_from_ai = True

            # Separate player vs NPC based on resolved IDs
            player_ids_in_req = [cid for cid in resolved_char_ids if cid in party_char_ids_set]
            npc_ids_in_req = [cid for cid in resolved_char_ids if cid not in party_char_ids_set]

            if player_ids_in_req:
                player_part = req_dict.copy()
                player_part["character_ids"] = player_ids_in_req
                player_requests_to_send.append(player_part)
            if npc_ids_in_req:
                npc_part = req_dict.copy()
                npc_part["character_ids"] = npc_ids_in_req
                npc_requests_to_roll_internally.append(npc_part)

        # Force Initiative Roll if combat just started and AI didn't request it
        if combat_just_started and not has_initiative_request_from_ai:
            logger.warning("Combat started, but AI did not request initiative. Forcing initiative roll.")
            # Get all combatants that haven't rolled initiative yet (initiative == -1)
            ids_needing_init = [c.id for c in game_state.combat.combatants if c.initiative == -1]
            if ids_needing_init:
                forced_init_req = {
                    "request_id": f"forced_init_{random.randint(1000,9999)}",
                    "character_ids": ids_needing_init, "type": "initiative",
                    "dice_formula": "1d20", "reason": "Combat Started! Roll Initiative!",
                }
                # Separate player/NPC for the forced request
                player_ids_forced = [cid for cid in ids_needing_init if cid in party_char_ids_set]
                npc_ids_forced = [cid for cid in ids_needing_init if cid not in party_char_ids_set]
                if player_ids_forced:
                    player_part = forced_init_req.copy(); player_part["character_ids"] = player_ids_forced
                    player_requests_to_send.insert(0, player_part) # Add to front
                if npc_ids_forced:
                    npc_part = forced_init_req.copy(); npc_part["character_ids"] = npc_ids_forced
                    npc_requests_to_roll_internally.insert(0, npc_part) # Add to front
            else:
                logger.error("Failed to resolve any combatants for forced initiative roll (all might have init already?).")


        # Perform NPC Rolls. Clear before new NPC rolls
        self.game_manager.clear_pending_npc_roll_results()
        npc_rolls_performed, _ = self._perform_npc_rolls(npc_requests_to_roll_internally)
        
        needs_ai_rerun = npc_rolls_performed and not player_requests_to_send
        if needs_ai_rerun:
            logger.info("NPC rolls performed and no player action required. Flagging for AI rerun.")
        
        return player_requests_to_send, npc_rolls_performed, needs_ai_rerun

    def _handle_turn_advancement(self, ai_response: AIResponse, needs_ai_rerun: bool, player_requests_pending: bool):
        """Checks AI signal and advances turn if conditions are met."""
        game_state = self.game_manager.get_current_state_model()
        ai_signals_end_turn = getattr(ai_response, 'end_turn', None)

        if game_state.combat.is_active and ai_signals_end_turn is True:
            if needs_ai_rerun:
                logger.warning("AI requested 'end_turn: true' but also triggered an AI rerun. Turn will advance *after* the rerun loop completes.")
            elif player_requests_pending:
                logger.warning("AI requested 'end_turn: true' but also requested player dice rolls. Turn will advance *after* player submits rolls.")
            else:
                logger.info("AI signaled end_turn=true and conditions met. Advancing turn.")
                self.game_manager.advance_turn()
        elif game_state.combat.is_active:
            if ai_signals_end_turn is False: logger.debug("AI explicitly set end_turn=false, turn not advancing.")
            elif ai_signals_end_turn is None: logger.debug("AI omitted end_turn field during combat, turn not advancing.")


    def process(self, ai_response: AIResponse) -> Tuple[List[Dict], bool]:
        """
        Processes a validated AIResponse object, updates game state, and determines next steps.
        Returns: (pending_player_dice_requests, needs_ai_rerun_for_next_step)
        """
        logger.debug("Processing AIResponse object via ResponseProcessor...")
        game_state = self.game_manager.get_current_state_model()

        self._handle_narrative_and_location(ai_response)
        combat_started_this_update = self._handle_game_state_updates(ai_response)
        
        # Reset the internal flag after checking it
        combat_just_started_flag = getattr(game_state.combat, '_combat_just_started_flag', False)
        if combat_just_started_flag:
            game_state.combat._combat_just_started_flag = False # Consume the flag

        # Handle dice requests (NPC rolls happen here)
        pending_player_reqs, npc_rolls_performed, needs_rerun_after_npc_rolls = self._handle_dice_requests(
            ai_response, combat_just_started_flag
        )

        # Handle turn advancement based on AI signal and current state
        self._handle_turn_advancement(ai_response, needs_rerun_after_npc_rolls, bool(pending_player_reqs))

        # Set pending player requests in game state
        if pending_player_reqs:
            self.game_manager.set_pending_player_dice_requests(pending_player_reqs)
            logger.info(f"{len(pending_player_reqs)} player dice requests pending.")
        elif not needs_rerun_after_npc_rolls:
            # Clear only if no rerun and no new requests
            self.game_manager.clear_pending_player_dice_requests()
            logger.debug("No pending player dice requests or AI rerun needed.")
            
        return pending_player_reqs, needs_rerun_after_npc_rolls
