"""
Handler for dice submission events.
"""

import logging
from typing import Dict, Any, List, Tuple
from app.utils.validation import DiceSubmissionValidator
from app.services.combat_utilities import CombatValidator
from .base_handler import BaseEventHandler

logger = logging.getLogger(__name__)


class DiceSubmissionHandler(BaseEventHandler):
    """Handles dice submission events."""
    
    def handle(self, roll_data: List[Dict]) -> Dict[str, Any]:
        """Handle submitted dice rolls and return response data."""
        logger.info("Handling dice submission...")
        
        # Check if AI is busy (use shared state if available)
        if self._shared_state and self._shared_state['ai_processing']:
            logger.warning("AI is busy. Dice submission rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        elif not self._shared_state and self._ai_processing:
            logger.warning("AI is busy. Dice submission rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        # Validate roll data
        validation_result = DiceSubmissionValidator.validate_submission(roll_data)
        if not validation_result.is_valid:
            return self._create_error_response(validation_result.error_message, status_code=400)
        
        try:
            # Extract request IDs from submitted roll data
            submitted_request_ids = [
                roll.get("request_id") for roll in roll_data 
                if roll.get("request_id")
            ]
            
            # Clear only the specific pending requests that were submitted
            self._clear_pending_dice_requests(submitted_request_ids if submitted_request_ids else None)
            is_initiative_round, actual_roll_outcomes = self._process_submitted_player_rolls(roll_data)
            
            # Check if we should wait for more initiative rolls before calling AI
            if is_initiative_round and self._has_pending_initiative_rolls():
                logger.info("Initiative rolls processed, but more initiative rolls pending. Not calling AI yet.")
                # Return success response without triggering AI
                response_data = self._create_frontend_response(needs_backend_trigger=False, status_code=200)
                response_data["submitted_roll_results"] = actual_roll_outcomes
                return response_data
            
            logger.info("Player rolls processed, calling AI for next step...")
            ai_response_obj, _, status, needs_backend_trigger = self._call_ai_and_process_step(ai_service)
            
            response_data = self._create_frontend_response(needs_backend_trigger, status_code=status, ai_response=ai_response_obj)
            response_data["submitted_roll_results"] = actual_roll_outcomes
            
            # Animation steps removed - events via SSE now handle real-time updates
            
            return response_data
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_dice_submission: {e}", exc_info=True)
            # Clear the processing flag
            if self._shared_state:
                self._shared_state['ai_processing'] = False
            else:
                self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error submitting rolls.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
    
    def handle_completed_rolls(self, roll_results: List[Dict]) -> Dict[str, Any]:
        """Handle submission of already-completed roll results."""
        logger.info("Handling completed roll submission...")
        
        # Check if AI is busy (use shared state if available)
        if self._shared_state and self._shared_state['ai_processing']:
            logger.warning("AI is busy. Completed roll submission rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        elif not self._shared_state and self._ai_processing:
            logger.warning("AI is busy. Completed roll submission rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        # Validate roll results data
        if not isinstance(roll_results, list):
            return self._create_error_response("Invalid data format, expected list of roll results", status_code=400)
        
        try:
            # Extract request IDs from completed roll results
            submitted_request_ids = []
            for result in roll_results:
                if isinstance(result, dict):
                    # Check for request_id at the top level
                    if result.get("request_id"):
                        submitted_request_ids.append(result["request_id"])
                    # Also check within rolls dict if present
                    rolls = result.get("rolls", {})
                    if isinstance(rolls, dict):
                        for character_roll in rolls.values():
                            if isinstance(character_roll, dict) and character_roll.get("request_id"):
                                submitted_request_ids.append(character_roll["request_id"])
            
            # Clear only the specific pending requests that were submitted
            self._clear_pending_dice_requests(submitted_request_ids if submitted_request_ids else None)
            
            # Process the already-completed roll results
            is_initiative_round = self._process_completed_roll_results(roll_results)
            
            # Check if we should wait for more initiative rolls before calling AI
            if is_initiative_round and self._has_pending_initiative_rolls():
                logger.info("Initiative rolls processed, but more initiative rolls pending. Not calling AI yet.")
                # Return success response without triggering AI
                response_data = self._create_frontend_response(needs_backend_trigger=False, status_code=200)
                response_data["submitted_roll_results"] = roll_results
                return response_data
            
            logger.info("Completed roll results processed, calling AI for next step...")
            ai_response_obj, _, status, needs_backend_trigger = self._call_ai_and_process_step(ai_service)
            
            response_data = self._create_frontend_response(needs_backend_trigger, status_code=status, ai_response=ai_response_obj)
            response_data["submitted_roll_results"] = roll_results
            
            # Animation steps removed - events via SSE now handle real-time updates
            
            return response_data
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_completed_roll_submission: {e}", exc_info=True)
            # Clear the processing flag
            if self._shared_state:
                self._shared_state['ai_processing'] = False
            else:
                self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error submitting completed rolls.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
    
    def _process_submitted_player_rolls(self, roll_requests_data: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Process submitted player rolls."""
        player_roll_results_list = []
        roll_summaries_for_history = []
        detailed_roll_messages_for_history = []
        is_initiative_round = False
        
        # Determine submitter name
        submitter_name = "Player"
        if CombatValidator.is_combat_active(self.game_state_repo):
            current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
            if current_combatant_id:
                submitter_name = self.character_service.get_character_name(current_combatant_id)
        
        # Process each roll request
        for req_data in roll_requests_data:
            if not all(k in req_data for k in ["character_id", "roll_type", "dice_formula"]):
                logger.error(f"Skipping invalid player roll request data: {req_data}")
                continue
            
            # Check if submitted data includes a total (for test scenarios)
            if "total" in req_data and req_data["total"] is not None:
                logger.debug(f"Using legacy dice submission handler")
                # Use submitted total instead of rolling dice
                actual_char_id = self.character_service.find_character_by_name_or_id(req_data["character_id"])
                if not actual_char_id:
                    logger.error(f"Cannot process roll: Unknown character '{req_data['character_id']}'.")
                    continue
                
                char_name = self.character_service.get_character_name(actual_char_id)
                submitted_total = req_data["total"]
                
                # Construct roll result similar to dice service format
                roll_result = {
                    "request_id": req_data.get("request_id"),
                    "character_id": actual_char_id,
                    "character_name": char_name,
                    "roll_type": req_data["roll_type"],
                    "dice_formula": req_data["dice_formula"],
                    "character_modifier": 0,  # Total already includes modifiers
                    "total_result": submitted_total,
                    "dc": req_data.get("dc"),
                    "success": None,  # Will be determined if DC is provided
                    "reason": req_data.get("reason", ""),
                    "result_message": f"{char_name} rolls {req_data['roll_type'].title()}: {req_data['dice_formula']} -> [?] = **{submitted_total}**.",
                    "result_summary": f"{char_name} rolls {req_data['roll_type'].title()}: Result **{submitted_total}**."
                }
                
                # Determine success if DC is provided
                if req_data.get("dc") is not None:
                    roll_result["success"] = submitted_total >= req_data["dc"]
                    success_text = "Success!" if roll_result["success"] else "Failure."
                    roll_result["result_message"] += f" (DC {req_data['dc']}) {success_text}"
                    roll_result["result_summary"] += f" (DC {req_data['dc']}) {success_text}"
                    
                logger.info(f"Roll: {roll_result['result_message']} (Reason: {roll_result['reason']})")
            else:
                # Use dice service to perform actual roll
                roll_result = self.dice_service.perform_roll(
                    character_id=req_data["character_id"],
                    roll_type=req_data["roll_type"],
                    dice_formula=req_data["dice_formula"],
                    skill=req_data.get("skill"),
                    ability=req_data.get("ability"),
                    dc=req_data.get("dc"),
                    reason=req_data.get("reason", ""),
                    original_request_id=req_data.get("request_id")
                )
            
            if roll_result and "error" not in roll_result:
                player_roll_results_list.append(roll_result)
                if roll_result.get("result_summary"):
                    roll_summaries_for_history.append(roll_result["result_summary"])
                if roll_result.get("result_message"):
                    detailed_roll_messages_for_history.append(roll_result["result_message"])
                if roll_result.get("roll_type") == "initiative":
                    is_initiative_round = True
            elif roll_result:
                error_msg = f"(Error rolling for {req_data.get('character_name', req_data['character_id'])}: {roll_result.get('error')})"
                logger.error(error_msg)
                roll_summaries_for_history.append(error_msg)
                detailed_roll_messages_for_history.append(error_msg)
        
        # Add rolls to history
        if roll_summaries_for_history:
            prefix = f"**{submitter_name} Rolls Submitted:**\n"
            self.chat_service.add_message(
                "user", prefix + "\n".join(roll_summaries_for_history),
                is_dice_result=True,
                detailed_content=prefix + "\n".join(detailed_roll_messages_for_history)
            )
        
        # Handle initiative determination
        if is_initiative_round and CombatValidator.is_combat_active(self.game_state_repo):
            game_state = self.game_state_repo.get_game_state()
            all_initiative_results = player_roll_results_list + game_state._pending_npc_roll_results
            game_state._pending_npc_roll_results = []  # Clear after use
            self.combat_service.determine_initiative_order(all_initiative_results)
        
        return is_initiative_round, player_roll_results_list
    
    def _process_completed_roll_results(self, roll_results: List[Dict]) -> bool:
        """Process already-completed roll results without re-rolling."""
        roll_summaries_for_history = []
        detailed_roll_messages_for_history = []
        is_initiative_round = False
        
        # Determine submitter name
        submitter_name = "Player"
        if CombatValidator.is_combat_active(self.game_state_repo):
            current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
            if current_combatant_id:
                submitter_name = self.character_service.get_character_name(current_combatant_id)
        
        # Process each completed roll result
        for roll_result in roll_results:
            if roll_result and "error" not in roll_result:
                if roll_result.get("result_summary"):
                    roll_summaries_for_history.append(roll_result["result_summary"])
                if roll_result.get("result_message"):
                    detailed_roll_messages_for_history.append(roll_result["result_message"])
                if roll_result.get("roll_type") == "initiative":
                    is_initiative_round = True
            else:
                error_msg = f"(Error in roll result for {roll_result.get('character_name', 'unknown')}: {roll_result.get('error', 'unknown error')})"
                logger.error(error_msg)
                roll_summaries_for_history.append(error_msg)
                detailed_roll_messages_for_history.append(error_msg)
        
        # Add rolls to history
        if roll_summaries_for_history:
            prefix = f"**{submitter_name} Rolls Submitted:**\n"
            self.chat_service.add_message(
                "user", prefix + "\n".join(roll_summaries_for_history),
                is_dice_result=True,
                detailed_content=prefix + "\n".join(detailed_roll_messages_for_history)
            )
        
        # Handle initiative determination
        if is_initiative_round and CombatValidator.is_combat_active(self.game_state_repo):
            game_state = self.game_state_repo.get_game_state()
            all_initiative_results = roll_results + game_state._pending_npc_roll_results
            game_state._pending_npc_roll_results = []  # Clear after use
            self.combat_service.determine_initiative_order(all_initiative_results)
        
        return is_initiative_round
    
    def _has_pending_initiative_rolls(self) -> bool:
        """Check if there are any pending initiative rolls from other players."""
        game_state = self.game_state_repo.get_game_state()
        
        # Check if any pending dice requests are for initiative
        for req in game_state.pending_player_dice_requests:
            if req.type == "initiative":
                return True
        
        return False
