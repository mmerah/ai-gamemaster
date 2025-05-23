"""
Game event handler service implementation.
"""
import logging
import time
from typing import Dict, List, Tuple, Optional
from flask import current_app
from app.core.interfaces import (
    GameEventHandler, GameStateRepository, CharacterService, 
    DiceRollingService, CombatService, ChatService, AIResponseProcessor
)
from app.services.character_service import CharacterValidator
from app.services.combat_service import CombatValidator, CombatFormatter
from app.services.chat_service import ChatFormatter
from app.ai_services.schemas import AIResponse

logger = logging.getLogger(__name__)


class GameEventHandlerImpl(GameEventHandler):
    """Implementation of game event handler."""
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService,
                 dice_service: DiceRollingService, combat_service: CombatService,
                 chat_service: ChatService, ai_response_processor: AIResponseProcessor):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor
        self._ai_processing = False
        
        # Retry functionality - store last AI request context
        self._last_ai_request_context = None
        self._last_ai_request_timestamp = None
    
    def handle_player_action(self, action_data: Dict) -> Dict:
        """Handle a player action and return response data."""
        logger.info("Handling player action...")
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        # Check if AI is busy
        if self._ai_processing:
            logger.warning("AI is busy. Player action rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Validate action
        validation_result = PlayerActionValidator.validate_action(action_data)
        if not validation_result.is_valid:
            if validation_result.is_empty_text:
                self.chat_service.add_message("system", "Please type something before sending.", is_dice_result=True)
            return self._create_error_response(validation_result.error_message, status_code=400)
        
        try:
            # Prepare and add player message
            player_message = self._prepare_player_message(action_data)
            if not player_message:
                return self._create_error_response("Invalid player turn", status_code=400)
            
            self.chat_service.add_message("user", player_message, is_dice_result=False)
            
            # Process AI step
            _, _, status, needs_backend_trigger = self._call_ai_and_process_step(ai_service)
            
            return self._create_frontend_response(needs_backend_trigger, status_code=status)
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_player_action: {e}", exc_info=True)
            self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error processing action.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
    
    def handle_dice_submission(self, roll_data: List[Dict]) -> Dict:
        """Handle submitted dice rolls and return response data."""
        logger.info("Handling dice submission...")
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        # Check if AI is busy
        if self._ai_processing:
            logger.warning("AI is busy. Submit rolls rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Validate roll data
        validation_result = DiceSubmissionValidator.validate_submission(roll_data)
        if not validation_result.is_valid:
            return self._create_error_response(validation_result.error_message, status_code=400)
        
        try:
            # Clear pending requests and process rolls
            self._clear_pending_dice_requests()
            is_initiative_round, actual_roll_outcomes = self._process_submitted_player_rolls(roll_data)
            
            logger.info("Player rolls processed, calling AI for next step...")
            _, _, status, needs_backend_trigger = self._call_ai_and_process_step(ai_service)
            
            response_data = self._create_frontend_response(needs_backend_trigger, status_code=status)
            response_data["submitted_roll_results"] = actual_roll_outcomes
            
            return response_data
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_dice_submission: {e}", exc_info=True)
            self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error submitting rolls.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
    
    def handle_completed_roll_submission(self, roll_results: List[Dict]) -> Dict:
        """Handle submission of already-completed roll results."""
        logger.info("Handling completed roll submission...")
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        # Check if AI is busy
        if self._ai_processing:
            logger.warning("AI is busy. Submit completed rolls rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Validate roll results data
        if not isinstance(roll_results, list):
            return self._create_error_response("Invalid data format, expected list of roll results", status_code=400)
        
        try:
            # Clear pending requests
            self._clear_pending_dice_requests()
            
            # Process the already-completed roll results
            is_initiative_round = self._process_completed_roll_results(roll_results)
            
            logger.info("Completed roll results processed, calling AI for next step...")
            _, _, status, needs_backend_trigger = self._call_ai_and_process_step(ai_service)
            
            response_data = self._create_frontend_response(needs_backend_trigger, status_code=status)
            response_data["submitted_roll_results"] = roll_results
            
            return response_data
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_completed_roll_submission: {e}", exc_info=True)
            self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error submitting completed rolls.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
    
    def handle_next_step_trigger(self) -> Dict:
        """Handle triggering the next step and return response data."""
        logger.info("Handling next step trigger...")
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        # Check if AI is busy
        if self._ai_processing:
            logger.warning("AI is busy. Trigger next step rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        try:
            npc_instruction = self._get_npc_turn_instruction()
            if npc_instruction:
                _, _, status, needs_backend_trigger = self._call_ai_and_process_step(
                    ai_service, initial_instruction=npc_instruction
                )
                return self._create_frontend_response(needs_backend_trigger, status_code=status)
            else:
                logger.debug("No NPC turn needed on trigger_next_step.")
                return self._create_frontend_response(needs_backend_trigger=False, status_code=200)
                
        except Exception as e:
            logger.error(f"Unhandled exception in handle_next_step_trigger: {e}", exc_info=True)
            self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error triggering next step.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
    
    def handle_retry_last_ai_request(self) -> Dict:
        """Handle retrying the last AI request that failed."""
        logger.info("Handling retry of last AI request...")
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        # Check if AI is busy
        if self._ai_processing:
            logger.warning("AI is busy. Retry rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Check if we have a stored request context
        if not self._last_ai_request_context:
            logger.warning("No stored AI request context available for retry.")
            return self._create_error_response("No previous AI request to retry", status_code=400)
        
        # Check if the stored request is not too old (5 minutes)
        if self._last_ai_request_timestamp and (time.time() - self._last_ai_request_timestamp > 300):
            logger.warning("Stored AI request context is too old for retry.")
            self._last_ai_request_context = None
            self._last_ai_request_timestamp = None
            return self._create_error_response("Previous AI request too old to retry", status_code=400)
        
        try:
            # Clear any error state first
            self._clear_pending_dice_requests()
            
            # Add a system message indicating retry
            self.chat_service.add_message("system", "(Retrying last AI request...)", is_dice_result=True)
            
            # Retry the AI call with stored context
            messages = self._last_ai_request_context["messages"]
            initial_instruction = self._last_ai_request_context.get("initial_instruction")
            
            _, _, status, needs_backend_trigger = self._call_ai_and_process_step(
                ai_service, initial_instruction=initial_instruction, use_stored_context=True, messages_override=messages
            )
            
            return self._create_frontend_response(needs_backend_trigger, status_code=status)
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_retry_last_ai_request: {e}", exc_info=True)
            self._ai_processing = False
            self.chat_service.add_message("system", f"(Error retrying AI request: {e})", is_dice_result=True)
            return self._create_error_response("Internal server error during retry", status_code=500)
    
    def _get_ai_service(self):
        """Get the AI service from Flask config."""
        ai_service = current_app.config.get('AI_SERVICE')
        if not ai_service:
            logger.error("AI Service not available.")
            self.chat_service.add_message("system", "(Error: AI Service is not configured or failed to initialize.)", is_dice_result=True)
        return ai_service
    
    def _call_ai_and_process_step(self, ai_service, initial_instruction: Optional[str] = None, 
                                  use_stored_context: bool = False, messages_override: Optional[List[Dict]] = None) -> Tuple[Optional[AIResponse], List[Dict], int, bool]:
        """Call AI and process the response."""
        logger.info(f"--- Starting AI Interaction Cycle (Instruction: {initial_instruction or 'None'}, UseStoredContext: {use_stored_context}) ---")
        
        if self._ai_processing:
            logger.warning("AI is already processing. Aborting.")
            return None, [], 429, False
        
        self._ai_processing = True
        ai_response_obj = None
        pending_player_requests = []
        status_code = 500
        needs_backend_trigger_for_next_distinct_step = False
        
        try:
            # Build AI prompt and get response
            if use_stored_context and messages_override:
                messages = messages_override
                logger.info("Using stored context for AI request retry")
            else:
                messages = self._build_ai_prompt_context(initial_instruction)
                # Store the context for potential retry (only if not already using stored context)
                self._store_ai_request_context(messages, initial_instruction)
            
            logger.info(f"Sending request to AI Service ({type(ai_service).__name__})...")
            ai_response_obj = ai_service.get_response(messages)
            
            if ai_response_obj is None:
                logger.error("AI service returned None.")
                error_msg = "(Error: Failed to get a valid response from the AI. You can try clicking 'Retry Last Request' if this was due to a parsing error.)"
                self.chat_service.add_message("system", error_msg, is_dice_result=True)
                status_code = 500
            else:
                logger.info("Successfully received AIResponse.")
                # Clear stored context on success
                if not use_stored_context:
                    self._last_ai_request_context = None
                    self._last_ai_request_timestamp = None
                
                # Process AI response
                pending_player_requests, npc_action_requires_ai_follow_up = (
                    self.ai_response_processor.process_response(ai_response_obj)
                )
                status_code = 200
                
                # Determine if backend trigger is needed
                needs_backend_trigger_for_next_distinct_step = self._determine_backend_trigger_needed(
                    npc_action_requires_ai_follow_up, pending_player_requests
                )
                
        except Exception as e:
            logger.error(f"Exception during AI step processing: {e}", exc_info=True)
            error_msg = f"(Error processing AI step: {e}. You can try clicking 'Retry Last Request' if this was due to a parsing error.)"
            self.chat_service.add_message("system", error_msg, is_dice_result=True)
            status_code = 500
            ai_response_obj = None
            pending_player_requests = []
            needs_backend_trigger_for_next_distinct_step = False
        finally:
            self._ai_processing = False
            logger.info(f"--- Ending AI Interaction Cycle (Status: {status_code}, Next Distinct Trigger: {needs_backend_trigger_for_next_distinct_step}) ---")
        
        return ai_response_obj, pending_player_requests, status_code, needs_backend_trigger_for_next_distinct_step
    
    def _store_ai_request_context(self, messages: List[Dict], initial_instruction: Optional[str] = None):
        """Store AI request context for potential retry."""
        self._last_ai_request_context = {
            "messages": messages.copy(),  # Make a copy to avoid mutation issues
            "initial_instruction": initial_instruction
        }
        self._last_ai_request_timestamp = time.time()
        logger.debug("Stored AI request context for potential retry")
    
    def _build_ai_prompt_context(self, initial_instruction: Optional[str] = None):
        """Build AI prompt context."""
        from app.game.prompts import build_ai_prompt_context
        game_state = self.game_state_repo.get_game_state()
        return build_ai_prompt_context(game_state, self, initial_instruction)
    
    def _determine_backend_trigger_needed(self, npc_action_requires_ai_follow_up: bool, pending_player_requests: List[Dict]) -> bool:
        """Determine if a backend trigger is needed for the next step."""
        if npc_action_requires_ai_follow_up:
            logger.info("NPC actions processed, and an AI follow-up for their outcome is needed. Setting backend trigger.")
            return True
        elif not pending_player_requests:
            # Check if the new current turn is an NPC
            game_state = self.game_state_repo.get_game_state()
            if CombatValidator.is_combat_active(self.game_state_repo):
                current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
                if current_combatant_id:
                    current_combatant = next(
                        (c for c in game_state.combat.combatants if c.id == current_combatant_id), 
                        None
                    )
                    if current_combatant and not current_combatant.is_player:
                        logger.info(f"Current AI step/turn segment complete. Next distinct turn is for NPC: {current_combatant.name}. Setting backend trigger.")
                        return True
        return False
    
    def _prepare_player_message(self, action_data: Dict) -> Optional[str]:
        """Prepare player message for chat history."""
        action_type = action_data.get('action_type')
        action_value = action_data.get('value')
        
        # Check if it's player's turn
        current_combatant_name = "Player"
        is_player_turn = False
        
        if CombatValidator.is_combat_active(self.game_state_repo):
            current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
            if current_combatant_id:
                game_state = self.game_state_repo.get_game_state()
                current_combatant = next(
                    (c for c in game_state.combat.combatants if c.id == current_combatant_id), 
                    None
                )
                if current_combatant:
                    if current_combatant.is_player:
                        is_player_turn = True
                        current_combatant_name = current_combatant.name
                    else:
                        logger.warning(f"Player action received but it's NPC turn ({current_combatant.name}). Ignoring.")
                        self.chat_service.add_message("system", "(It's not your turn!)", is_dice_result=True)
                        return None
        
        # Format message
        if action_type == 'free_text':
            player_message_content = f'"{action_value}"'
        else:
            logger.warning(f"Unknown action type '{action_type}' in _prepare_player_message. Value: {action_value}")
            player_message_content = f"(Performed unknown action: {action_type})"
        
        prefix = f"{current_combatant_name}: " if is_player_turn else ""
        return f"{prefix}{player_message_content}"
    
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
    
    def _get_npc_turn_instruction(self) -> Optional[str]:
        """Get instruction for NPC turn or turn continuation."""
        if not CombatValidator.is_combat_active(self.game_state_repo):
            logger.warning("Trigger next step called, but combat not active. No AI instruction.")
            return None
        
        current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
        if not current_combatant_id:
            logger.warning("Trigger next step called, but invalid combatant index. No AI instruction.")
            return None
        
        game_state = self.game_state_repo.get_game_state()
        current_combatant = next(
            (c for c in game_state.combat.combatants if c.id == current_combatant_id), 
            None
        )
        
        if not current_combatant:
            logger.warning("Trigger next step called, but no valid current combatant found. No AI instruction.")
            return None
        
        if not current_combatant.is_player:
            # Standard NPC turn
            logger.info(f"Triggering AI step for NPC turn: {current_combatant.name}")
            return f"It is now {current_combatant.name}'s turn (ID: {current_combatant.id}). Decide and describe their action(s) for this turn."
        else:
            # Check if this is a turn continuation scenario (player character but AI needs to continue)
            # This happens when AI set end_turn=false and NPC actions were auto-resolved
            game_state = self.game_state_repo.get_game_state()
            
            # Look for recent chat messages indicating NPC rolls were just performed
            recent_messages = game_state.chat_history[-3:] if len(game_state.chat_history) >= 3 else game_state.chat_history
            has_recent_npc_rolls = any(
                msg.get("role") == "user" and msg.get("is_dice_result") and "NPC Rolls:" in msg.get("content", "")
                for msg in recent_messages
            )
            
            if has_recent_npc_rolls:
                logger.info(f"Triggering AI step for turn continuation: {current_combatant.name} (player character with pending spell/action effects)")
                return f"Continue {current_combatant.name}'s turn (ID: {current_combatant.id}). Process the results of the saving throw(s) and any remaining spell/action effects."
            else:
                logger.warning("Trigger next step called, but it's player's turn with no indication of turn continuation needed. No AI instruction.")
                return None
    
    def _clear_pending_dice_requests(self) -> None:
        """Clear pending dice requests."""
        game_state = self.game_state_repo.get_game_state()
        game_state.pending_player_dice_requests = []
    
    def _create_frontend_response(self, needs_backend_trigger: bool = False, status_code: int = 200) -> Dict:
        """Create frontend response data."""
        response_data = self._get_state_for_frontend()
        response_data["needs_backend_trigger"] = needs_backend_trigger
        response_data["status_code"] = status_code
        
        # Add retry availability flag
        response_data["can_retry_last_request"] = self._can_retry_last_request()
        
        return response_data
    
    def _can_retry_last_request(self) -> bool:
        """Check if last AI request can be retried."""
        if not self._last_ai_request_context or not self._last_ai_request_timestamp:
            return False
        
        # Check if request is not too old (5 minutes)
        return (time.time() - self._last_ai_request_timestamp) <= 300
    
    def _create_error_response(self, error_message: str, status_code: int = 500) -> Dict:
        """Create error response data."""
        response_data = self._get_state_for_frontend()
        response_data["error"] = error_message
        response_data["needs_backend_trigger"] = False
        response_data["status_code"] = status_code
        response_data["dice_requests"] = []  # Ensure no pending requests on error
        return response_data
    
    def _get_state_for_frontend(self) -> Dict:
        """Get current game state formatted for frontend."""
        game_state = self.game_state_repo.get_game_state()
        
        return {
            "party": self._format_party_for_frontend(game_state.party),
            "location": game_state.current_location.get("name", "Unknown"),
            "location_description": game_state.current_location.get("description", ""),
            "chat_history": ChatFormatter.format_for_frontend(game_state.chat_history),
            "dice_requests": game_state.pending_player_dice_requests,
            "combat_info": CombatFormatter.format_combat_status(self.game_state_repo)
        }
    
    def _format_party_for_frontend(self, party_instances: Dict) -> List[Dict]:
        """Format party data for frontend."""
        from app.game import utils
        
        return [
            {
                "id": pc.id,
                "name": pc.name,
                "race": pc.race,
                "char_class": pc.char_class,
                "level": pc.level,
                "hp": pc.current_hp,
                "max_hp": pc.max_hp,
                "ac": pc.armor_class,
                "conditions": pc.conditions,
                "icon": pc.icon,
                "stats": pc.base_stats.model_dump(),
                "proficiencies": pc.proficiencies.model_dump(),
                "proficiency_bonus": utils.get_proficiency_bonus(pc.level)
            } for pc in party_instances.values()
        ]


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, is_valid: bool, error_message: str = "", is_empty_text: bool = False):
        self.is_valid = is_valid
        self.error_message = error_message
        self.is_empty_text = is_empty_text


class PlayerActionValidator:
    """Validator for player actions."""
    
    @staticmethod
    def validate_action(action_data: Optional[Dict]) -> ValidationResult:
        """Validate player action data."""
        if not action_data or 'action_type' not in action_data or 'value' not in action_data:
            return ValidationResult(False, "Invalid action format")
        
        if action_data['action_type'] == 'free_text' and not action_data['value']:
            return ValidationResult(False, "Empty action text", is_empty_text=True)
        
        return ValidationResult(True)


class DiceSubmissionValidator:
    """Validator for dice submissions."""
    
    @staticmethod
    def validate_submission(roll_data) -> ValidationResult:
        """Validate dice submission data."""
        if not isinstance(roll_data, list):
            return ValidationResult(False, "Invalid data format, expected list of rolls")
        
        return ValidationResult(True)
