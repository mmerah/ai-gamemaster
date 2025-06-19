"""
Game API routes for handling game state, player actions, and dice rolls.
"""

import logging
from typing import Tuple, Union

from flask import Blueprint, Response, jsonify, request

from app.api.dependencies import (
    get_character_service,
    get_dice_service,
    get_event_queue,
    get_game_orchestrator,
    get_game_state_repository,
)
from app.api.error_handlers import with_error_handling
from app.api.helpers import process_game_event
from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.events import GameEventType, PlayerActionEventModel
from app.services.event_factory import create_game_state_snapshot_event

logger = logging.getLogger(__name__)

# Create blueprint for game API routes
game_bp = Blueprint("game", __name__, url_prefix="/api")


@game_bp.route("/game_state")
@with_error_handling("get_game_state")
def get_game_state() -> Union[Response, Tuple[Response, int]]:
    """Get current game state for frontend.

    Query parameters:
    - emit_snapshot: If 'true', emits a GameStateSnapshotEvent for reconnection/sync
    """
    game_orchestrator = get_game_orchestrator()

    # Check if we should emit a snapshot event
    emit_snapshot = request.args.get("emit_snapshot", "").lower() == "true"

    if emit_snapshot:
        # Get game state repository and event queue
        game_state_repo = get_game_state_repository()
        event_queue = get_event_queue()

        if event_queue:
            game_state = game_state_repo.get_game_state()

            # Get character service for creating combined character models
            character_service = get_character_service()

            # Create and emit snapshot event
            snapshot_event = create_game_state_snapshot_event(
                game_state,
                reason="reconnection",
                character_service=character_service,
            )
            event_queue.put_event(snapshot_event)
            logger.info("Emitted GameStateSnapshotEvent for reconnection")

    # Get current state without triggering any actions
    response_data = game_orchestrator.get_game_state()

    # Convert to dict and transform roles for frontend
    response_dict = response_data.model_dump(exclude_none=True)

    # Convert 'assistant' role to 'gm' in chat history for frontend compatibility
    if "chat_history" in response_dict:
        for msg in response_dict["chat_history"]:
            if msg.get("role") == "assistant":
                msg["role"] = "gm"

    return jsonify(response_dict)


@game_bp.route("/player_action", methods=["POST"])
@with_error_handling("player_action")
def player_action() -> Union[Response, Tuple[Response, int]]:
    """Handle player actions."""
    action_data = request.get_json()
    if not action_data:
        return jsonify({"error": "No action data provided"}), 400

    action_model = PlayerActionEventModel(**action_data)

    # Process through unified interface
    response_data, status_code = process_game_event(
        GameEventType.PLAYER_ACTION, action_model
    )

    return jsonify(response_data), status_code


@game_bp.route("/submit_rolls", methods=["POST"])
@with_error_handling("submit_rolls")
def submit_rolls() -> Union[Response, Tuple[Response, int]]:
    """Handle dice roll submissions."""
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
        roll_results = [
            DiceRollResultResponseModel(**result)
            for result in roll_data["roll_results"]
        ]
        # Process through unified interface
        response_data, status_code = process_game_event(
            GameEventType.COMPLETED_ROLL_SUBMISSION,
            {"roll_results": roll_results},
        )
        return jsonify(response_data), status_code
    else:
        # Legacy format: roll requests that need to be processed
        logger.info("Using legacy dice submission handler")
        # Ensure roll_data is a list
        if isinstance(roll_data, dict):
            roll_data = [roll_data]
        roll_submissions = [DiceRollSubmissionModel(**roll) for roll in roll_data]
        # Process through unified interface
        response_data, status_code = process_game_event(
            GameEventType.DICE_SUBMISSION, {"rolls": roll_submissions}
        )
        return jsonify(response_data), status_code


@game_bp.route("/trigger_next_step", methods=["POST"])
@with_error_handling("trigger_next_step")
def trigger_next_step() -> Union[Response, Tuple[Response, int]]:
    """Trigger the next step in the game (usually for NPC turns)."""
    # Process through unified interface with empty data
    response_data, status_code = process_game_event(
        GameEventType.NEXT_STEP,
        {},  # Empty dict for events without data
    )
    return jsonify(response_data), status_code


@game_bp.route("/retry_last_ai_request", methods=["POST"])
@with_error_handling("retry_last_ai_request")
def retry_last_ai_request() -> Union[Response, Tuple[Response, int]]:
    """Retry the last AI request that failed."""
    # Process through unified interface with empty data
    response_data, status_code = process_game_event(
        GameEventType.RETRY,
        {},  # Empty dict for events without data
    )
    return jsonify(response_data), status_code


@game_bp.route("/perform_roll", methods=["POST"])
@with_error_handling("perform_roll")
def perform_roll() -> Union[Response, Tuple[Response, int]]:
    """Perform an immediate dice roll and return the result."""
    dice_service = get_dice_service()

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


@game_bp.route("/game_state/save", methods=["POST"])
@with_error_handling("save_game_state")
def save_game_state() -> Union[Response, Tuple[Response, int]]:
    """Manually save the current game state."""
    game_state_repo = get_game_state_repository()

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
