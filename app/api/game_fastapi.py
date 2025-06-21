"""
Game API routes for handling game state, player actions, and dice rolls - FastAPI version.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies_fastapi import (
    get_character_service,
    get_dice_service,
    get_event_queue,
    get_game_orchestrator,
    get_game_state_repository,
)
from app.core.domain_interfaces import ICharacterService, IDiceRollingService
from app.core.orchestration_interfaces import IGameOrchestrator
from app.core.repository_interfaces import IGameStateRepository
from app.core.system_interfaces import IEventQueue
from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.events import (
    GameEventModel,
    GameEventResponseModel,
    GameEventType,
    PlayerActionEventModel,
)
from app.services.event_factory import create_game_state_snapshot_event
from app.utils.event_helpers import emit_event

logger = logging.getLogger(__name__)

# Create router for game API routes
router = APIRouter(prefix="/api", tags=["game"])


async def process_game_event(
    event_type: GameEventType, data: Any, orchestrator: IGameOrchestrator
) -> Tuple[Dict[str, Any], int]:
    """
    Helper to process game events consistently across routes.

    Args:
        event_type: The type of game event
        data: Event-specific data
        orchestrator: Game orchestrator instance

    Returns:
        Tuple of (response_dict, http_status_code)
    """
    try:
        # Create event model
        event = GameEventModel(type=event_type, data=data)

        # Process event through orchestrator
        response = orchestrator.handle_event(event)

        # Extract status code and prepare response
        status_code = response.status_code or 200
        response_data = response.model_dump(exclude_none=True)

        # Remove status_code from response data
        if "status_code" in response_data:
            del response_data["status_code"]

        return response_data, status_code

    except ValueError as e:
        logger.warning(f"Invalid request for {event_type.value}: {e}")
        return {"error": str(e)}, 400
    except Exception as e:
        logger.error(
            f"Internal error processing {event_type.value}: {e}", exc_info=True
        )
        return {"error": "Internal server error"}, 500


@router.get("/game_state")
async def get_game_state(
    emit_snapshot: bool = Query(
        False, description="Emit a GameStateSnapshotEvent for reconnection/sync"
    ),
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
    game_state_repo: IGameStateRepository = Depends(get_game_state_repository),
    event_queue: IEventQueue = Depends(get_event_queue),
    character_service: ICharacterService = Depends(get_character_service),
) -> Dict[str, Any]:
    """Get current game state for frontend."""
    try:
        # Check if we should emit a snapshot event
        if emit_snapshot:
            game_state = game_state_repo.get_game_state()

            # Create and emit snapshot event
            snapshot_event = create_game_state_snapshot_event(
                game_state,
                reason="reconnection",
                character_service=character_service,
            )
            emit_event(
                event_queue,
                snapshot_event,
                log_message="Emitted GameStateSnapshotEvent for reconnection",
                log_level=logging.INFO,
            )

        # Get current state without triggering any actions
        response_data = game_orchestrator.get_game_state()

        # Convert to dict and transform roles for frontend
        response_dict = response_data.model_dump(exclude_none=True)

        # Convert 'assistant' role to 'gm' in chat history for frontend compatibility
        if "chat_history" in response_dict:
            for msg in response_dict["chat_history"]:
                if msg.get("role") == "assistant":
                    msg["role"] = "gm"

        return response_dict

    except Exception as e:
        logger.error(f"Error in get_game_state: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/player_action")
async def player_action(
    action_data: Dict[str, Any],
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> Dict[str, Any]:
    """Handle player actions."""
    try:
        if not action_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No action data provided",
            )

        action_model = PlayerActionEventModel(**action_data)

        # Process through unified interface
        response_data, status_code = await process_game_event(
            GameEventType.PLAYER_ACTION, action_model, game_orchestrator
        )

        if status_code != 200:
            raise HTTPException(
                status_code=status_code,
                detail=response_data.get("error", "Unknown error"),
            )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in player_action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/submit_rolls")
async def submit_rolls(
    roll_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> Dict[str, Any]:
    """Handle dice roll submissions."""
    try:
        if roll_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No roll data provided",
            )

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
            response_data, status_code = await process_game_event(
                GameEventType.COMPLETED_ROLL_SUBMISSION,
                {"roll_results": roll_results},
                game_orchestrator,
            )
        else:
            # Legacy format: roll requests that need to be processed
            logger.info("Using legacy dice submission handler")
            # Ensure roll_data is a list
            if isinstance(roll_data, dict):
                roll_data_list = [roll_data]
            else:
                roll_data_list = roll_data
            roll_submissions = [
                DiceRollSubmissionModel(**roll) for roll in roll_data_list
            ]
            # Process through unified interface
            response_data, status_code = await process_game_event(
                GameEventType.DICE_SUBMISSION,
                {"rolls": roll_submissions},
                game_orchestrator,
            )

        if status_code != 200:
            raise HTTPException(
                status_code=status_code,
                detail=response_data.get("error", "Unknown error"),
            )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_rolls: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/trigger_next_step")
async def trigger_next_step(
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> Dict[str, Any]:
    """Trigger the next step in the game (usually for NPC turns)."""
    try:
        # Process through unified interface with empty data
        response_data, status_code = await process_game_event(
            GameEventType.NEXT_STEP,
            {},  # Empty dict for events without data
            game_orchestrator,
        )

        if status_code != 200:
            raise HTTPException(
                status_code=status_code,
                detail=response_data.get("error", "Unknown error"),
            )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in trigger_next_step: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/retry_last_ai_request")
async def retry_last_ai_request(
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> Dict[str, Any]:
    """Retry the last AI request that failed."""
    try:
        # Process through unified interface with empty data
        response_data, status_code = await process_game_event(
            GameEventType.RETRY,
            {},  # Empty dict for events without data
            game_orchestrator,
        )

        if status_code != 200:
            raise HTTPException(
                status_code=status_code,
                detail=response_data.get("error", "Unknown error"),
            )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in retry_last_ai_request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/perform_roll")
async def perform_roll(
    roll_data: Dict[str, Any],
    dice_service: IDiceRollingService = Depends(get_dice_service),
) -> Dict[str, Any]:
    """Perform an immediate dice roll and return the result."""
    try:
        if not roll_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No roll data provided",
            )

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required roll parameters",
            )

        # At this point we know the required parameters are not None
        # Perform the roll
        roll_result = dice_service.perform_roll(
            character_id=character_id,  # type: ignore[arg-type] # checked above
            roll_type=roll_type,  # type: ignore[arg-type] # checked above
            dice_formula=dice_formula,  # type: ignore[arg-type] # checked above
            skill=skill,
            ability=ability,
            dc=dc,
            reason=reason,
            original_request_id=request_id,
        )

        if roll_result.error:
            # Error case
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=roll_result.error,
            )

        # Success case - convert model to dict for JSON response
        return roll_result.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in perform_roll: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/game_state/save")
async def save_game_state(
    game_state_repo: IGameStateRepository = Depends(get_game_state_repository),
) -> Dict[str, Any]:
    """Manually save the current game state."""
    try:
        # Get the current game state
        game_state = game_state_repo.get_game_state()

        # Save it (this will use the appropriate file path based on campaign_id)
        game_state_repo.save_game_state(game_state)

        logger.info(f"Game state saved manually for campaign: {game_state.campaign_id}")

        return {
            "success": True,
            "message": "Game state saved successfully",
            "campaign_id": game_state.campaign_id,
        }

    except Exception as e:
        logger.error(f"Error in save_game_state: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
