"""
Game API routes for handling game state, player actions, and dice rolls.
"""

import logging
from typing import Tuple, Union

from flask import Blueprint, Response, jsonify, request

from app.core.container import get_container
from app.events.game_update_events import create_game_state_snapshot_event
from app.exceptions import BadRequestError, InternalServerError, ValidationError

logger = logging.getLogger(__name__)

# Create blueprint for game API routes
game_bp = Blueprint("game", __name__, url_prefix="/api")


@game_bp.route("/game_state")
def get_game_state() -> Union[Response, Tuple[Response, int]]:
    """Get current game state for frontend.

    Query parameters:
    - emit_snapshot: If 'true', emits a GameStateSnapshotEvent for reconnection/sync
    """
    try:
        container = get_container()
        game_event_manager = container.get_game_event_manager()

        # Check if we should emit a snapshot event
        emit_snapshot = request.args.get("emit_snapshot", "").lower() == "true"

        if emit_snapshot:
            # Get game state repository and event queue
            game_state_repo = container.get_game_state_repository()
            event_queue = container.get_event_queue()

            if event_queue:
                game_state = game_state_repo.get_game_state()

                # Get character service for creating combined character models
                character_service = container.get_character_service()

                # Create and emit snapshot event
                snapshot_event = create_game_state_snapshot_event(
                    game_state,
                    reason="reconnection",
                    character_service=character_service,
                )
                event_queue.put_event(snapshot_event)
                logger.info("Emitted GameStateSnapshotEvent for reconnection")

        # Get current state without triggering any actions
        response_data = game_event_manager.get_game_state()

        # Convert to dict and transform roles for frontend
        response_dict = response_data.model_dump(exclude_none=True)

        # Convert 'assistant' role to 'gm' in chat history for frontend compatibility
        if "chat_history" in response_dict:
            for msg in response_dict["chat_history"]:
                if msg.get("role") == "assistant":
                    msg["role"] = "gm"

        return jsonify(response_dict)
    except Exception as e:
        logger.error(f"Error getting game state: {e}", exc_info=True)
        raise InternalServerError("Failed to get game state", details={"error": str(e)})


@game_bp.route("/player_action", methods=["POST"])
def player_action() -> Union[Response, Tuple[Response, int]]:
    """Handle player actions."""
    container = get_container()
    game_event_manager = container.get_game_event_manager()

    action_data = request.get_json()
    if not action_data:
        raise BadRequestError("No action data provided")

    # Convert to PlayerActionEventModel
    from app.models import PlayerActionEventModel

    try:
        action_model = PlayerActionEventModel(**action_data)
    except Exception as e:
        logger.error(f"Invalid player action data: {e}")
        raise ValidationError(f"Invalid action data: {e!s}", field="action_data")

    # Handle the player action through the service
    response_model = game_event_manager.handle_player_action(action_model)
    status_code = response_model.status_code or 200
    response_data = response_model.model_dump(exclude_none=True)
    if "status_code" in response_data:
        del response_data["status_code"]

    return jsonify(response_data), status_code


@game_bp.route("/submit_rolls", methods=["POST"])
def submit_rolls() -> Union[Response, Tuple[Response, int]]:
    """Handle dice roll submissions."""
    try:
        container = get_container()
        game_event_manager = container.get_game_event_manager()

        roll_data = request.get_json()
        if roll_data is None:
            return jsonify({"error": "No roll data provided"}), 400

        logger.debug(f"Received roll data: {roll_data}")
        logger.debug(f"Roll data type: {type(roll_data)}")
        logger.debug(
            f"Has roll_results key: {'roll_results' in roll_data if isinstance(roll_data, dict) else 'Not a dict'}"
        )

        # Check if this is the new format with roll_results
        if isinstance(roll_data, dict) and "roll_results" in roll_data:
            # New format: roll results already computed
            logger.info("Using completed roll submission handler")
            from app.models import DiceRollResultResponseModel

            try:
                roll_results = [
                    DiceRollResultResponseModel(**result)
                    for result in roll_data["roll_results"]
                ]
                response_model = game_event_manager.handle_completed_roll_submission(
                    roll_results
                )
            except Exception as e:
                logger.error(f"Invalid roll results data: {e}")
                return jsonify({"error": f"Invalid roll results data: {e!s}"}), 400
        else:
            # Legacy format: roll requests that need to be processed
            logger.info("Using legacy dice submission handler")
            from app.models import DiceRollSubmissionModel

            try:
                # Ensure roll_data is a list
                if isinstance(roll_data, dict):
                    roll_data = [roll_data]
                roll_submissions = [
                    DiceRollSubmissionModel(**roll) for roll in roll_data
                ]
                response_model = game_event_manager.handle_dice_submission(
                    roll_submissions
                )
            except Exception as e:
                logger.error(f"Invalid dice submission data: {e}")
                return jsonify({"error": f"Invalid dice submission data: {e!s}"}), 400

        status_code = response_model.status_code or 200
        response_data = response_model.model_dump(exclude_none=True)
        if "status_code" in response_data:
            del response_data["status_code"]

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error(f"Unhandled exception in submit_rolls: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@game_bp.route("/trigger_next_step", methods=["POST"])
def trigger_next_step() -> Union[Response, Tuple[Response, int]]:
    """Trigger the next step in the game (usually for NPC turns)."""
    try:
        container = get_container()
        game_event_manager = container.get_game_event_manager()

        # Handle the next step trigger through the service
        response_model = game_event_manager.handle_next_step_trigger()
        status_code = response_model.status_code or 200
        response_data = response_model.model_dump(exclude_none=True)
        if "status_code" in response_data:
            del response_data["status_code"]

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error(f"Unhandled exception in trigger_next_step: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@game_bp.route("/retry_last_ai_request", methods=["POST"])
def retry_last_ai_request() -> Union[Response, Tuple[Response, int]]:
    """Retry the last AI request that failed."""
    try:
        container = get_container()
        game_event_manager = container.get_game_event_manager()

        # Handle the retry through the service
        response_model = game_event_manager.handle_retry()
        status_code = response_model.status_code or 200
        response_data = response_model.model_dump(exclude_none=True)
        if "status_code" in response_data:
            del response_data["status_code"]

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error(
            f"Unhandled exception in retry_last_ai_request: {e}", exc_info=True
        )
        return jsonify({"error": "Internal server error"}), 500


@game_bp.route("/perform_roll", methods=["POST"])
def perform_roll() -> Union[Response, Tuple[Response, int]]:
    """Perform an immediate dice roll and return the result."""
    try:
        container = get_container()
        dice_service = container.get_dice_service()

        roll_data = request.get_json()
        if not roll_data:
            return jsonify({"error": "No roll data provided"}), 400

        # Extract roll parameters
        character_id = roll_data.get("character_id")
        roll_type = roll_data.get("roll_type")
        dice_formula = roll_data.get("dice_formula")
        skill = roll_data.get("skill")
        ability = roll_data.get("ability")
        dc = roll_data.get("dc")
        reason = roll_data.get("reason", "")
        request_id = roll_data.get("request_id")

        if not all([character_id, roll_type, dice_formula]):
            return jsonify({"error": "Missing required roll parameters"}), 400

        # Perform the roll
        roll_result = dice_service.perform_roll(
            character_id=character_id,
            roll_type=roll_type,
            dice_formula=dice_formula,
            skill=skill,
            ability=ability,
            dc=dc,
            reason=reason,
            original_request_id=request_id,
        )

        if roll_result.error:
            # Error case
            return jsonify({"error": roll_result.error}), 400

        # Success case - convert model to dict for JSON response
        return jsonify(roll_result.model_dump())

    except Exception as e:
        logger.error(f"Unhandled exception in perform_roll: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@game_bp.route("/game_state/save", methods=["POST"])
def save_game_state() -> Union[Response, Tuple[Response, int]]:
    """Manually save the current game state."""
    try:
        container = get_container()
        game_state_repo = container.get_game_state_repository()

        # Get the current game state
        game_state = game_state_repo.get_game_state()

        # Save it (this will use the appropriate file path based on campaign_id)
        game_state_repo.save_game_state(game_state)

        logger.info(f"Game state saved manually for campaign: {game_state.campaign_id}")

        return jsonify(
            {
                "success": True,
                "message": "Game state saved successfully",
                "campaign_id": game_state.campaign_id,
            }
        )

    except Exception as e:
        logger.error(f"Error saving game state: {e}", exc_info=True)
        return jsonify({"error": f"Failed to save game state: {e!s}"}), 500
