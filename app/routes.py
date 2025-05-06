import json
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple
from flask import Blueprint, render_template, request, jsonify, current_app
from .game.manager import get_game_manager
from .game.prompts import build_ai_prompt_context
from .ai_services.schemas import AIResponse
from .game.models import GameState, Combatant

main_bp = Blueprint('main', __name__)
logger = current_app.logger
    
# Helper to get AI Service
def _get_ai_service_or_error_response():
    ai_service = current_app.config.get('AI_SERVICE')
    if not ai_service:
        logger.error("AI Service not available.")
        game_manager = get_game_manager()
        try:
            game_manager.add_chat_message("system", "(Error: AI Service is not configured or failed to initialize.)", is_dice_result=True)
        except Exception as e: # Catch error if game_manager itself has issues
            logger.error(f"Failed to add AI service error message to chat: {e}")
        
        # Construct a valid error state for frontend
        error_state = game_manager.get_state_for_frontend() if game_manager else {}
        # Ensure no pending requests on error
        error_state["dice_requests"] = []
        error_state["error"] = "AI Service unavailable."
        return None, jsonify(create_frontend_response_data(game_manager, error_state, needs_backend_trigger=False)), 503
    return ai_service, None, None

# Helper to call AI and process response
def _call_ai_and_process_step(game_manager, ai_service, initial_instruction: Optional[str] = None) -> Tuple[Optional[AIResponse], List[Dict], int, bool]:
    """
    Manages one or more interaction cycles with the AI service if reruns are needed.
    Returns: (Final AIResponse object or None, final pending player dice requests, HTTP status, needs_backend_trigger for the *next distinct* step)
    """
    # This will hold the results of the *last* AI interaction in the loop
    final_ai_response_obj: Optional[AIResponse] = None
    final_pending_player_requests: List[Dict] = []
    final_status_code = 500
    final_needs_backend_trigger = False # For the *next distinct user-facing step*

    # Loop for internal AI reruns (e.g., after NPC rolls)
    # Max reruns to prevent infinite loops if AI keeps triggering reruns without player input
    MAX_AI_RERUNS = 5 
    rerun_count = 0
    current_instruction = initial_instruction

    while rerun_count < MAX_AI_RERUNS:
        rerun_count += 1
        logger.info(f"--- Starting AI Interaction Cycle {rerun_count}/{MAX_AI_RERUNS} (Instruction: {current_instruction or 'None'}) ---")

        if game_manager.is_ai_processing():
            logger.warning(f"AI is already processing during rerun cycle {rerun_count}. Aborting.")
            # Use the last known good values if available, otherwise error
            return final_ai_response_obj, final_pending_player_requests, final_status_code if final_status_code != 500 else 429, final_needs_backend_trigger

        game_manager.set_ai_processing(True)
        
        ai_response_obj: Optional[AIResponse] = None
        pending_player_requests: List[Dict] = []
        status_code = 500
        # This is the trigger for the *very next* step if this cycle is the last one
        # and an NPC turn follows without further reruns.
        current_cycle_needs_backend_trigger = False 
        # Flag for *this* cycle
        needs_internal_ai_rerun = False

        try:
            current_state_model: GameState = game_manager.get_current_state_model()
            # For reruns, the instruction is typically None unless specifically set
            messages = build_ai_prompt_context(current_state_model, game_manager, current_instruction)
            
            logger.info(f"Sending request to AI Service ({type(ai_service).__name__}) for cycle {rerun_count}...")
            ai_response_obj = ai_service.get_response(messages)

            if ai_response_obj is None:
                logger.error(f"AI service returned None in cycle {rerun_count}.")
                game_manager.add_chat_message("system", "(Error: Failed to get a valid response from the AI.)", is_dice_result=True)
                status_code = 500
                # Stop on AI error
                needs_internal_ai_rerun = False
                # Update final status before breaking
                final_status_code = status_code 
                break 
            
            logger.info(f"Successfully received AIResponse for cycle {rerun_count}.")
            
            pending_player_requests, needs_internal_ai_rerun = game_manager.process_ai_response(ai_response_obj)
            
            # Update final results with this cycle's outcome
            final_ai_response_obj = ai_response_obj
            final_pending_player_requests = pending_player_requests
            # If we got here, this cycle was successful
            final_status_code = 200

            # Determine if the *next distinct user-facing step* needs backend triggering.
            # This check is relevant if this current cycle *doesn't* lead to another internal rerun
            # AND there are no player requests.
            if not needs_internal_ai_rerun and not pending_player_requests:
                combat = game_manager.get_current_state_model().combat
                if combat.is_active and combat.combatants:
                    if 0 <= combat.current_turn_index < len(combat.combatants):
                        next_combatant = combat.combatants[combat.current_turn_index]
                        if not next_combatant.is_player:
                            current_cycle_needs_backend_trigger = True
                            logger.info(f"Cycle {rerun_count}: Next distinct step requires backend trigger for NPC: {next_combatant.name}")
                    else:
                        logger.error(f"Cycle {rerun_count}: Combat active but current turn index invalid.")
            
            final_needs_backend_trigger = current_cycle_needs_backend_trigger
            status_code = 200

        except Exception as e:
            logger.error(f"Exception during AI step processing (cycle {rerun_count}): {e}", exc_info=True)
            game_manager.add_chat_message("system", f"(Error processing AI step: {e})", is_dice_result=True)
            status_code = 500
            # Stop on error
            needs_internal_ai_rerun = False
            # Update final status before breaking
            final_status_code = status_code
            break
        finally:
            game_manager.set_ai_processing(False)
            logger.info(f"--- Ending AI Interaction Cycle {rerun_count} (Status: {status_code}, Internal Rerun: {needs_internal_ai_rerun}, Next Distinct Trigger: {current_cycle_needs_backend_trigger}) ---")

        if not needs_internal_ai_rerun:
            # If no more internal reruns are needed from this cycle, break the loop.
            # The final_needs_backend_trigger will determine if the frontend needs to call /trigger_next_step
            break
        
        # If a rerun is needed, the instruction for the next AI call is typically None,
        # as the AI should react to the state changes (e.g., NPC roll results in history).
        current_instruction = None 

    # Check if needs_internal_ai_rerun was still true
    if rerun_count == MAX_AI_RERUNS and needs_internal_ai_rerun:
        logger.warning(f"Max AI reruns ({MAX_AI_RERUNS}) reached. Stopping interaction.")
        game_manager.add_chat_message("system", "(System: AI interaction took too many steps. Please try again or simplify.)", is_dice_result=True)
        # Ensure we don't signal a backend trigger if we hit max reruns and it was still trying to rerun
        final_needs_backend_trigger = False
        # If the last step was technically successful but hit max reruns
        if final_status_code == 200:
            # Loop Detected (or similar appropriate error)
            final_status_code = 508 

    return final_ai_response_obj, final_pending_player_requests, final_status_code, final_needs_backend_trigger

# Helper to add the trigger flag to the response
def create_frontend_response_data(game_manager, current_state_override=None, needs_backend_trigger=False):
    """Creates the data structure for frontend responses."""
    response_data = current_state_override if current_state_override is not None else game_manager.get_state_for_frontend()
    response_data["needs_backend_trigger"] = needs_backend_trigger
    return response_data

# Flask Routes
@main_bp.route('/')
def index():
    logger.info(f"Serving index.html for request {request.remote_addr}")
    return render_template('index.html')

@main_bp.route('/api/game_state', methods=['GET'])
def get_initial_game_state():
    logger.info(f"GET /api/game_state request from {request.remote_addr}")
    game_manager = get_game_manager()
    # GameManager handles initialization; just get the frontend state
    response_data = create_frontend_response_data(game_manager, needs_backend_trigger=False)
    logger.debug(f"Returning initial game state: {response_data}")
    return jsonify(response_data)

def _validate_player_action_request(request_json: Optional[Dict]) -> Tuple[Optional[Dict], Optional[Tuple[jsonify, int]]]:
    if not request_json or 'action_type' not in request_json or 'value' not in request_json:
        logger.warning("Invalid player action request: Missing fields.")
        return None, (jsonify({"error": "Invalid action format"}), 400)
    if request_json['action_type'] == 'free_text' and not request_json['value']:
        logger.warning("Received empty free text action.")
        # Let game_manager handle adding this specific message
        return None, (jsonify({"error": "Empty action text"}), 400)
    return request_json, None

def _prepare_player_message_for_history(player_action_data: Dict, game_manager) -> Optional[str]:
    action_type = player_action_data.get('action_type')
    action_value = player_action_data.get('value')
    
    # Default
    current_combatant_name = "Player"
    is_player_turn = False
    combat = game_manager.get_current_state_model().combat
    if combat.is_active and combat.combatants and 0 <= combat.current_turn_index < len(combat.combatants):
        current_combatant = combat.combatants[combat.current_turn_index]
        if current_combatant.is_player:
            is_player_turn = True
            current_combatant_name = current_combatant.name
        else:
            # It's an NPC's turn, return early
            logger.warning(f"Player action received but it's NPC turn ({current_combatant.name}). Ignoring.")
            game_manager.add_chat_message("system", "(It's not your turn!)", is_dice_result=True)
            return None

    if action_type == 'free_text':
        player_message_content = f"\"{action_value}\""
    else:
        # Should be caught by validation, but as a fallback
        logger.warning(f"Unknown action type '{action_type}' in _prepare_player_message. Value: {action_value}")
        player_message_content = f"(Performed unknown action: {action_type})"
    
    prefix = f"{current_combatant_name}: " if is_player_turn else ""
    return f"{prefix}{player_message_content}"

@main_bp.route('/api/player_action', methods=['POST'])
def handle_player_action():
    logger.info(f"POST /api/player_action request from {request.remote_addr}")
    game_manager = get_game_manager()
    ai_service, error_resp, status = _get_ai_service_or_error_response()
    if error_resp:
        return error_resp, status

    if game_manager.is_ai_processing():
        logger.warning("AI is busy. Player action rejected.")
        return jsonify(create_frontend_response_data(game_manager, {"error": "AI is busy"}, needs_backend_trigger=False)), 429

    player_action_data, validation_error = _validate_player_action_request(request.json)
    if validation_error:
        # If it's an empty text error, add a message
        if player_action_data is None and "Empty action text" in validation_error[0].get_json().get("error", ""):
            game_manager.add_chat_message("system", "Please type something before sending.", is_dice_result=True)
            return jsonify(create_frontend_response_data(game_manager, needs_backend_trigger=False)), 400
        return validation_error

    try:
        player_message_for_history = _prepare_player_message_for_history(player_action_data, game_manager)
        if player_message_for_history is None:
            # e.g. not player's turn
            return jsonify(create_frontend_response_data(game_manager, needs_backend_trigger=False)), 400
        
        game_manager.add_chat_message("user", player_message_for_history, is_dice_result=False)
        _, _, status, needs_backend_trigger = _call_ai_and_process_step(game_manager, ai_service)
        return jsonify(create_frontend_response_data(game_manager, needs_backend_trigger=needs_backend_trigger)), status

    except Exception as e:
        logger.error(f"Unhandled exception in handle_player_action: {e}", exc_info=True)
        if game_manager.is_ai_processing():
            game_manager.set_ai_processing(False)
        game_manager.add_chat_message("system", "(Internal Server Error processing action.)", is_dice_result=True)
        return jsonify(create_frontend_response_data(game_manager, {"error": "Internal server error"}, needs_backend_trigger=False)), 500

def _validate_submit_rolls_request(request_json: Any) -> Tuple[Optional[List[Dict]], Optional[Tuple[jsonify, int]]]:
    if not isinstance(request_json, list):
        logger.error(f"Invalid data for submit_rolls (expected list): {request_json}")
        return None, (jsonify({"error": "Invalid data format, expected list of rolls"}), 400)
    # Further validation for each item in the list can be added here if needed
    return request_json, None

def _process_submitted_player_rolls(roll_requests_data: List[Dict], game_manager) -> bool:
    """Performs player rolls and adds results to history. Returns if initiative was rolled."""
    player_roll_results = []
    roll_summaries_for_history = []
    detailed_roll_messages_for_history = []
    is_initiative_round = False
    
    # Determine submitter name before rolls change turn potentially
    submitter_name = "Player"
    combat = game_manager.get_current_state_model().combat
    if combat.is_active and combat.combatants and 0 <= combat.current_turn_index < len(combat.combatants):
        submitter_name = combat.combatants[combat.current_turn_index].name

    for req_data in roll_requests_data:
        if not all(k in req_data for k in ["character_id", "roll_type", "dice_formula"]):
            logger.error(f"Skipping invalid player roll request data: {req_data}")
            continue
        
        roll_result = game_manager.perform_roll(
            character_id=req_data["character_id"], roll_type=req_data["roll_type"],
            dice_formula=req_data["dice_formula"], skill=req_data.get("skill"),
            ability=req_data.get("ability"), dc=req_data.get("dc"),
            reason=req_data.get("reason", "")
        )
        if roll_result and "error" not in roll_result:
            player_roll_results.append(roll_result)
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

    if roll_summaries_for_history:
        prefix = f"**{submitter_name} Rolls Submitted:**\n"
        game_manager.add_chat_message(
            "user", prefix + "\n".join(roll_summaries_for_history),
            is_dice_result=True,
            detailed_content=prefix + "\n".join(detailed_roll_messages_for_history)
        )
    
    if is_initiative_round and game_manager.get_current_state_model().combat.is_active:
        all_initiative_results = player_roll_results + game_manager.get_current_state_model()._pending_npc_roll_results
        # Clear after use
        game_manager.clear_pending_npc_roll_results()
        game_manager._determine_initiative_order(all_initiative_results)
        
    return is_initiative_round

@main_bp.route('/api/submit_rolls', methods=['POST'])
def handle_submit_rolls():
    logger.info(f"POST /api/submit_rolls request from {request.remote_addr}")
    game_manager = get_game_manager()
    ai_service, error_resp, status = _get_ai_service_or_error_response()
    if error_resp:
        return error_resp, status

    if game_manager.is_ai_processing():
        logger.warning("AI is busy. Submit rolls rejected.")
        return jsonify(create_frontend_response_data(game_manager, {"error": "AI is busy"}, needs_backend_trigger=False)), 429

    player_roll_requests_data, validation_error = _validate_submit_rolls_request(request.json)
    if validation_error:
        return validation_error
    
    try:
        # Clear requests now that they are being submitted
        game_manager.clear_pending_player_dice_requests()
        _process_submitted_player_rolls(player_roll_requests_data, game_manager)

        logger.info("Player rolls processed, calling AI for next step...")
        _, _, status, needs_backend_trigger = _call_ai_and_process_step(game_manager, ai_service)
        
        return jsonify(create_frontend_response_data(game_manager, needs_backend_trigger=needs_backend_trigger)), status

    except Exception as e:
        logger.error(f"Unhandled exception in handle_submit_rolls: {e}", exc_info=True)
        if game_manager.is_ai_processing():
            game_manager.set_ai_processing(False)
        game_manager.add_chat_message("system", "(Internal Server Error submitting rolls.)", is_dice_result=True)
        return jsonify(create_frontend_response_data(game_manager, {"error": "Internal server error"}, needs_backend_trigger=False)), 500
      
def _get_npc_turn_instruction(game_manager) -> Optional[str]:
    combat = game_manager.get_current_state_model().combat
    if combat.is_active and combat.combatants and 0 <= combat.current_turn_index < len(combat.combatants):
        current_combatant = combat.combatants[combat.current_turn_index]
        if not current_combatant.is_player:
            logger.info(f"Triggering AI step for NPC turn: {current_combatant.name}")
            return f"It is now {current_combatant.name}'s turn (ID: {current_combatant.id}). Decide and describe their action(s) for this turn."
        else:
            logger.warning("Trigger next step called, but it's player's turn. No AI instruction needed.")
    else:
        logger.warning("Trigger next step called, but combat not active or invalid index. No AI instruction.")
    return None

@main_bp.route('/api/trigger_next_step', methods=['POST'])
def handle_trigger_next_step():
    logger.info("POST /api/trigger_next_step request received")
    game_manager = get_game_manager()
    ai_service, error_resp, status = _get_ai_service_or_error_response()
    if error_resp:
        return error_resp, status

    if game_manager.is_ai_processing():
        logger.warning("AI is busy. Trigger next step rejected.")
        return jsonify(create_frontend_response_data(game_manager, {"error": "AI is busy"}, needs_backend_trigger=False)), 429

    try:
        npc_instruction = _get_npc_turn_instruction(game_manager)
        if npc_instruction:
            _, _, status, needs_backend_trigger = _call_ai_and_process_step(
                game_manager, ai_service, initial_instruction=npc_instruction
            )
            return jsonify(create_frontend_response_data(game_manager, needs_backend_trigger=needs_backend_trigger)), status
        else:
            # No NPC turn needed (e.g., player's turn, combat inactive)
            logger.debug("No NPC turn needed on trigger_next_step.")
            return jsonify(create_frontend_response_data(game_manager, needs_backend_trigger=False)), 200

    except Exception as e:
        logger.error(f"Unhandled exception in handle_trigger_next_step: {e}", exc_info=True)
        if game_manager.is_ai_processing():
            game_manager.set_ai_processing(False)
        game_manager.add_chat_message("system", "(Internal Server Error triggering next step.)", is_dice_result=True)
        return jsonify(create_frontend_response_data(game_manager, {"error": "Internal server error"}, needs_backend_trigger=False)), 500
    