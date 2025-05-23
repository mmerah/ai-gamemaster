"""
AI response processor service implementation.
"""
import logging
import random
from typing import Dict, List, Tuple, Optional
from app.core.interfaces import (
    AIResponseProcessor, GameStateRepository, CharacterService, 
    DiceRollingService, CombatService, ChatService
)
from app.ai_services.schemas import AIResponse
from app.game import state_processors

logger = logging.getLogger(__name__)


class AIResponseProcessorImpl(AIResponseProcessor):
    """Implementation of AI response processor."""
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService,
                 dice_service: DiceRollingService, combat_service: CombatService, 
                 chat_service: ChatService):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
    
    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Delegate to character service for compatibility with state processors."""
        return self.character_service.find_character_by_name_or_id(identifier)
    
    def process_response(self, ai_response: AIResponse) -> Tuple[List[Dict], bool]:
        """Process an AI response and return pending requests and rerun flag."""
        logger.debug("Processing AIResponse object via AIResponseProcessor...")
        
        # Pre-calculate next combatant BEFORE any game state changes
        next_combatant_info = self._pre_calculate_next_combatant(ai_response)
        
        # Handle narrative and location updates
        self._handle_narrative_and_location(ai_response)
        
        # Apply game state updates
        combat_started_this_update = self._handle_game_state_updates(ai_response)
        
        # Check and reset combat just started flag
        combat_just_started_flag = self._check_and_reset_combat_flag()
        
        # Handle dice requests (NPC rolls happen here)
        pending_player_reqs, npc_rolls_performed, needs_rerun_after_npc_rolls = (
            self._handle_dice_requests(ai_response, combat_just_started_flag)
        )
        
        # Handle turn advancement using pre-calculated info
        self._handle_turn_advancement(ai_response, needs_rerun_after_npc_rolls, bool(pending_player_reqs), next_combatant_info)
        
        # Update pending player requests in game state
        self._update_pending_requests(pending_player_reqs, needs_rerun_after_npc_rolls)
        
        return pending_player_reqs, needs_rerun_after_npc_rolls
    
    def _handle_narrative_and_location(self, ai_response: AIResponse) -> None:
        """Handle AI narrative and location updates."""
        if ai_response.reasoning:
            logger.info(f"AI Reasoning: {ai_response.reasoning}")
        else:
            logger.warning("AI Response missing 'reasoning'.")
        
        # Add AI response to chat history
        self.chat_service.add_message(
            "assistant",
            ai_response.narrative,
            ai_response_json=ai_response.model_dump_json()
        )
        
        # Update location if provided
        if ai_response.location_update:
            self._update_location(ai_response.location_update)
    
    def _update_location(self, location_update) -> None:
        """Update the current location."""
        game_state = self.game_state_repo.get_game_state()
        
        if hasattr(location_update, 'model_dump'):
            old_name = game_state.current_location.get("name")
            game_state.current_location = location_update.model_dump()
            logger.info(f"Location updated from '{old_name}' to '{location_update.name}'.")
        elif location_update is not None:
            logger.warning(f"Invalid location_update data type: {type(location_update)}")
    
    def _handle_game_state_updates(self, ai_response: AIResponse) -> bool:
        """Apply game state updates from AI response."""
        game_state = self.game_state_repo.get_game_state()
        return state_processors.apply_game_state_updates(
            game_state,
            ai_response.game_state_updates,
            self  # Pass self as game_manager for compatibility
        )
    
    def _pre_calculate_next_combatant(self, ai_response: AIResponse) -> Optional[Dict]:
        """Pre-calculate who should be next before any combatant removals."""
        game_state = self.game_state_repo.get_game_state()
        
        # Only pre-calculate if combat is active and AI wants to end turn
        if not (game_state.combat.is_active and getattr(ai_response, 'end_turn', None) is True):
            return None
            
        # Check if any combatant removals are planned
        removal_updates = [
            update for update in ai_response.game_state_updates 
            if getattr(update, 'type', None) == 'combatant_remove'
        ]
        
        if not removal_updates:
            return None  # No removals planned, normal advancement will work
            
        # Calculate who should be next after removal
        current_combatants = game_state.combat.combatants.copy()
        current_index = game_state.combat.current_turn_index
        
        if not (0 <= current_index < len(current_combatants)):
            logger.warning(f"Invalid current_turn_index {current_index}, cannot pre-calculate next combatant")
            return None
            
        # Find which combatants will be removed
        removal_ids = set()
        for update in removal_updates:
            removal_id = self.character_service.find_character_by_name_or_id(update.character_id)
            if removal_id:
                removal_ids.add(removal_id)
                
        # Simulate the removal to find the correct next combatant
        remaining_combatants = [c for c in current_combatants if c.id not in removal_ids]
        
        if not remaining_combatants:
            logger.info("All combatants will be removed, combat should end")
            return {"should_end_combat": True}
            
        # Find next valid combatant after current position
        next_index = current_index
        for _ in range(len(current_combatants)):
            next_index = (next_index + 1) % len(current_combatants)
            next_combatant = current_combatants[next_index]
            
            # Skip if this combatant will be removed
            if next_combatant.id in removal_ids:
                continue
                
            # Find the new index for this combatant in the remaining list
            try:
                new_index = next(i for i, c in enumerate(remaining_combatants) if c.id == next_combatant.id)
                logger.debug(f"Pre-calculated next combatant: {next_combatant.name} (ID: {next_combatant.id}) at new index {new_index}")
                return {
                    "combatant_id": next_combatant.id,
                    "new_index": new_index,
                    "should_end_combat": False
                }
            except StopIteration:
                continue  # This shouldn't happen but just in case
                
        # If we get here, couldn't find a valid next combatant
        logger.warning("Could not determine valid next combatant after removals")
        return None

    def _check_and_reset_combat_flag(self) -> bool:
        """Check and reset the combat just started flag."""
        game_state = self.game_state_repo.get_game_state()
        combat_just_started_flag = getattr(game_state.combat, '_combat_just_started_flag', False)
        
        if combat_just_started_flag:
            game_state.combat._combat_just_started_flag = False
        
        return combat_just_started_flag
    
    def _handle_dice_requests(self, ai_response: AIResponse, combat_just_started: bool) -> Tuple[List[Dict], bool, bool]:
        """Handle dice requests from AI response."""
        dice_handler = DiceRequestHandler(
            self.game_state_repo, self.character_service, self.dice_service, self.chat_service
        )
        return dice_handler.process_dice_requests(ai_response, combat_just_started)
    
    def _handle_turn_advancement(self, ai_response: AIResponse, needs_ai_rerun: bool, player_requests_pending: bool, next_combatant_info: Optional[Dict] = None) -> None:
        """Handle turn advancement based on AI signal."""
        turn_handler = TurnAdvancementHandler(self.game_state_repo, self.combat_service)
        turn_handler.handle_turn_advancement(ai_response, needs_ai_rerun, player_requests_pending, next_combatant_info)
    
    def _update_pending_requests(self, pending_player_reqs: List[Dict], needs_rerun_after_npc_rolls: bool) -> None:
        """Update pending player requests in game state."""
        game_state = self.game_state_repo.get_game_state()
        
        if pending_player_reqs:
            game_state.pending_player_dice_requests = pending_player_reqs
            logger.info(f"{len(pending_player_reqs)} player dice requests pending.")
        elif not needs_rerun_after_npc_rolls:
            game_state.pending_player_dice_requests = []
            logger.debug("No pending player dice requests or AI rerun needed.")


class DiceRequestHandler:
    """Handles dice request processing for AI responses."""
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService,
                 dice_service: DiceRollingService, chat_service: ChatService):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.chat_service = chat_service
    
    def process_dice_requests(self, ai_response: AIResponse, combat_just_started: bool) -> Tuple[List[Dict], bool, bool]:
        """Process dice requests from AI response."""
        game_state = self.game_state_repo.get_game_state()
        party_char_ids_set = set(game_state.party.keys())
        
        player_requests_to_send = []
        npc_requests_to_roll_internally = []
        has_initiative_request_from_ai = False
        
        # Process each dice request
        for req_obj in ai_response.dice_requests:
            req_dict = req_obj.model_dump()
            resolved_char_ids = self._resolve_character_ids(req_dict.get("character_ids", []))
            
            if not resolved_char_ids:
                logger.error(f"Could not resolve any valid character IDs for dice request: {req_dict}")
                continue
            
            req_dict["character_ids"] = resolved_char_ids
            
            if req_dict.get("type") == "initiative":
                has_initiative_request_from_ai = True
            
            # Separate player vs NPC requests
            player_ids = [cid for cid in resolved_char_ids if cid in party_char_ids_set]
            npc_ids = [cid for cid in resolved_char_ids if cid not in party_char_ids_set]
            
            if player_ids:
                player_part = req_dict.copy()
                player_part["character_ids"] = player_ids
                player_requests_to_send.append(player_part)
            
            if npc_ids:
                npc_part = req_dict.copy()
                npc_part["character_ids"] = npc_ids
                npc_requests_to_roll_internally.append(npc_part)
        
        # Force initiative if combat just started and AI didn't request it
        if combat_just_started and not has_initiative_request_from_ai:
            self._force_initiative_rolls(player_requests_to_send, npc_requests_to_roll_internally, party_char_ids_set)
        
        # Perform NPC rolls
        game_state._pending_npc_roll_results = []  # Clear before new rolls
        npc_rolls_performed, _ = self._perform_npc_rolls(npc_requests_to_roll_internally)
        
        needs_ai_rerun = npc_rolls_performed and not player_requests_to_send
        if needs_ai_rerun:
            logger.info("NPC rolls performed and no player action required. Flagging for AI rerun.")
        
        return player_requests_to_send, npc_rolls_performed, needs_ai_rerun
    
    def _resolve_character_ids(self, req_char_ids_input: List[str]) -> List[str]:
        """Resolve character IDs, handling 'all' keyword."""
        game_state = self.game_state_repo.get_game_state()
        party_char_ids_set = set(game_state.party.keys())
        resolved_char_ids = set()
        
        if "all" in req_char_ids_input:
            if game_state.combat.is_active:
                # Include only non-defeated combatants
                for c in game_state.combat.combatants:
                    from app.services.character_service import CharacterValidator
                    if not CharacterValidator.is_character_defeated(c.id, self.game_state_repo):
                        resolved_char_ids.add(c.id)
                logger.info(f"Expanding 'all' in dice request to ACTIVE combatants: {list(resolved_char_ids)}")
            else:
                # All party members if not in combat
                resolved_char_ids.update(party_char_ids_set)
                logger.info(f"Expanding 'all' in dice request to party members: {list(resolved_char_ids)}")
            
            # Add any other specific IDs mentioned alongside 'all'
            for specific_id in req_char_ids_input:
                if specific_id != "all":
                    resolved = self.character_service.find_character_by_name_or_id(specific_id)
                    if resolved:
                        resolved_char_ids.add(resolved)
        else:
            # Resolve specific IDs
            for specific_id_input in req_char_ids_input:
                resolved = self.character_service.find_character_by_name_or_id(specific_id_input)
                if resolved:
                    resolved_char_ids.add(resolved)
                else:
                    logger.warning(f"Could not resolve ID '{specific_id_input}' in dice request.")
        
        return list(resolved_char_ids)
    
    def _force_initiative_rolls(self, player_requests: List[Dict], npc_requests: List[Dict], party_char_ids_set: set) -> None:
        """Force initiative rolls if combat started but AI didn't request them."""
        logger.warning("Combat started, but AI did not request initiative. Forcing initiative roll.")
        
        game_state = self.game_state_repo.get_game_state()
        ids_needing_init = [c.id for c in game_state.combat.combatants if c.initiative == -1]
        
        if ids_needing_init:
            forced_init_req = {
                "request_id": f"forced_init_{random.randint(1000,9999)}",
                "character_ids": ids_needing_init,
                "type": "initiative",
                "dice_formula": "1d20",
                "reason": "Combat Started! Roll Initiative!",
            }
            
            # Separate player/NPC for the forced request
            player_ids_forced = [cid for cid in ids_needing_init if cid in party_char_ids_set]
            npc_ids_forced = [cid for cid in ids_needing_init if cid not in party_char_ids_set]
            
            if player_ids_forced:
                player_part = forced_init_req.copy()
                player_part["character_ids"] = player_ids_forced
                player_requests.insert(0, player_part)
            
            if npc_ids_forced:
                npc_part = forced_init_req.copy()
                npc_part["character_ids"] = npc_ids_forced
                npc_requests.insert(0, npc_part)
        else:
            logger.error("Failed to resolve any combatants for forced initiative roll.")
    
    def _perform_npc_rolls(self, npc_requests_to_roll: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Perform NPC rolls internally."""
        if not npc_requests_to_roll:
            return False, []
        
        game_state = self.game_state_repo.get_game_state()
        npc_roll_results = []
        npc_rolls_performed = False
        
        logger.info(f"Performing {len(npc_requests_to_roll)} NPC roll request(s) internally...")
        
        for npc_req in npc_requests_to_roll:
            for npc_id in npc_req.get("character_ids", []):
                # Check if NPC is defeated
                from app.services.character_service import CharacterValidator
                if CharacterValidator.is_character_defeated(npc_id, self.game_state_repo):
                    logger.debug(f"Skipping roll for defeated NPC: {self.character_service.get_character_name(npc_id)} ({npc_id})")
                    continue
                
                # Perform the roll
                roll_result = self.dice_service.perform_roll(
                    character_id=npc_id,
                    roll_type=npc_req.get("type"),
                    dice_formula=npc_req.get("dice_formula"),
                    skill=npc_req.get("skill"),
                    ability=npc_req.get("ability"),
                    dc=npc_req.get("dc"),
                    reason=npc_req.get("reason", ""),
                    original_request_id=npc_req.get("request_id")
                )
                
                if roll_result and "error" not in roll_result:
                    npc_roll_results.append(roll_result)
                    npc_rolls_performed = True
                elif roll_result:
                    error_msg = f"(Error rolling for NPC {self.character_service.get_character_name(npc_id)}: {roll_result.get('error')})"
                    logger.error(error_msg)
                    self.chat_service.add_message("system", error_msg, is_dice_result=True)
        
        # Store NPC roll results and add to history
        if npc_roll_results:
            game_state._pending_npc_roll_results.extend(npc_roll_results)
            self._add_npc_rolls_to_history(npc_roll_results)
        
        return npc_rolls_performed, npc_roll_results
    
    def _add_npc_rolls_to_history(self, npc_roll_results: List[Dict]) -> None:
        """Add NPC roll results to chat history."""
        npc_roll_summaries = [r.get("result_summary") for r in npc_roll_results if r.get("result_summary")]
        npc_detailed_messages = [
            r.get("result_message", r.get("result_summary")) 
            for r in npc_roll_results 
            if r.get("result_message") or r.get("result_summary")
        ]
        
        if npc_roll_summaries:
            combined_summary = "**NPC Rolls:**\n" + "\n".join(npc_roll_summaries)
            combined_detailed = "**NPC Rolls:**\n" + "\n".join(npc_detailed_messages)
            self.chat_service.add_message(
                "user", combined_summary, 
                is_dice_result=True, 
                detailed_content=combined_detailed
            )


class TurnAdvancementHandler:
    """Handles turn advancement logic."""
    
    def __init__(self, game_state_repo: GameStateRepository, combat_service: CombatService):
        self.game_state_repo = game_state_repo
        self.combat_service = combat_service
    
    def handle_turn_advancement(self, ai_response: AIResponse, needs_ai_rerun: bool, player_requests_pending: bool, next_combatant_info: Optional[Dict] = None) -> None:
        """Handle turn advancement based on AI signal and current state."""
        game_state = self.game_state_repo.get_game_state()
        ai_signals_end_turn = getattr(ai_response, 'end_turn', None)
        
        if game_state.combat.is_active and ai_signals_end_turn is True:
            if needs_ai_rerun:
                logger.warning("AI requested 'end_turn: true' but also triggered an AI rerun. Turn will advance *after* the rerun loop completes.")
            elif player_requests_pending:
                logger.warning("AI requested 'end_turn: true' but also requested player dice rolls. Turn will advance *after* player submits rolls.")
            else:
                logger.info("AI signaled end_turn=true and conditions met. Advancing turn.")
                
                # Use pre-calculated next combatant info if available
                if next_combatant_info:
                    self._advance_with_pre_calculated_info(next_combatant_info)
                else:
                    # Normal turn advancement
                    self.combat_service.advance_turn()
        elif game_state.combat.is_active:
            if ai_signals_end_turn is False:
                logger.debug("AI explicitly set end_turn=false, turn not advancing.")
            elif ai_signals_end_turn is None:
                logger.debug("AI omitted end_turn field during combat, turn not advancing.")
    
    def _advance_with_pre_calculated_info(self, next_combatant_info: Dict) -> None:
        """Advance turn using pre-calculated combatant information."""
        game_state = self.game_state_repo.get_game_state()
        
        if next_combatant_info.get("should_end_combat"):
            logger.info("Pre-calculated info indicates combat should end (no remaining combatants)")
            from app.ai_services.schemas import CombatEndUpdate
            from app.game import state_processors
            end_update = CombatEndUpdate(
                type="combat_end", 
                details={"reason": "All combatants removed"}
            )
            state_processors.end_combat(game_state, end_update)
            return
        
        # Set the current turn index to the pre-calculated position
        target_combatant_id = next_combatant_info.get("combatant_id")
        new_index = next_combatant_info.get("new_index")
        
        if target_combatant_id and new_index is not None:
            # Verify the combatant still exists at the expected position
            if (0 <= new_index < len(game_state.combat.combatants) and 
                game_state.combat.combatants[new_index].id == target_combatant_id):
                
                game_state.combat.current_turn_index = new_index
                current_combatant = game_state.combat.combatants[new_index]
                logger.info(f"Turn advanced using pre-calculated info to: {current_combatant.name} (ID: {current_combatant.id})")
                
                # Check if new round started (this happens when we wrap around to index 0 from a higher index)
                if new_index == 0 and len(game_state.combat.combatants) > 1:
                    # Only increment round if we didn't start at index 0 initially
                    previous_combatants_existed = any(
                        update for update in getattr(self, '_recent_ai_response', {}).get('game_state_updates', [])
                        if getattr(update, 'type', None) == 'combatant_remove'
                    )
                    if previous_combatants_existed:
                        game_state.combat.round_number += 1
                        logger.info(f"Advanced to Combat Round {game_state.combat.round_number}")
                        
            else:
                logger.warning(f"Pre-calculated combatant position mismatch. Expected {target_combatant_id} at index {new_index}, falling back to normal advancement")
                self.combat_service.advance_turn()
        else:
            logger.warning("Invalid pre-calculated turn info, falling back to normal advancement")
            self.combat_service.advance_turn()
