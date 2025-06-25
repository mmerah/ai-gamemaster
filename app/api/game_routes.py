"""
Game API routes for handling game state, player actions, and dice rolls - FastAPI version.
"""

import logging
from typing import Any, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies import (
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
from app.models.api import (
    PerformRollRequest,
    PlayerActionRequest,
    SaveGameResponse,
    SubmitRollsRequest,
)
from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.events.event_types import GameEventType
from app.models.events.game_events import (
    GameEventModel,
    GameEventResponseModel,
    PlayerActionEventModel,
)
from app.models.game_state.main import GameStateModel
from app.services.event_factory import create_game_state_snapshot_event
from app.utils.event_helpers import emit_event

logger = logging.getLogger(__name__)

# Create router for game API routes
router = APIRouter(prefix="/api", tags=["game"])


async def process_game_event(
    event_type: GameEventType, data: Any, orchestrator: IGameOrchestrator
) -> Tuple[GameEventResponseModel, int]:
    """
    Helper to process game events consistently across routes.

    Args:
        event_type: The type of game event
        data: Event-specific data
        orchestrator: Game orchestrator instance

    Returns:
        Tuple of (response_model, http_status_code)
    """
    # Create event model
    event = GameEventModel(type=event_type, data=data)

    # Process event through orchestrator
    response = await orchestrator.handle_event(event)

    # Extract status code
    status_code = response.status_code or 200

    return response, status_code


@router.get(
    "/game_state", response_model=GameStateModel, response_model_exclude_none=True
)
async def get_game_state(
    emit_snapshot: bool = Query(
        False, description="Emit a GameStateSnapshotEvent for reconnection/sync"
    ),
    game_state_repo: IGameStateRepository = Depends(get_game_state_repository),
    event_queue: IEventQueue = Depends(get_event_queue),
    character_service: ICharacterService = Depends(get_character_service),
) -> GameStateModel:
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
        # No role transformation needed - frontend should handle "assistant" role
        return game_state_repo.get_game_state()

    except Exception as e:
        logger.error(f"Error in get_game_state: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/player_action",
    response_model=GameEventResponseModel,
    response_model_exclude_none=True,
)
async def player_action(
    request: PlayerActionRequest,
    response: Response,
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> GameEventResponseModel:
    """Handle player actions."""
    try:
        # Convert request to event model
        action_model = PlayerActionEventModel(
            action_type=request.action_type,
            value=request.value,
            character_id=request.character_id,
        )

        # Process through unified interface
        result, status_code = await process_game_event(
            GameEventType.PLAYER_ACTION, action_model, game_orchestrator
        )

        # Set the HTTP status code
        response.status_code = status_code

        # Return the response regardless of status code
        # The response model includes the error and full game state
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in player_action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/submit_rolls",
    response_model=GameEventResponseModel,
    response_model_exclude_none=True,
)
async def submit_rolls(
    request: SubmitRollsRequest,
    response: Response,
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> GameEventResponseModel:
    """Handle dice roll submissions."""
    try:
        # Check if this is the new format with roll_results
        if request.roll_results is not None:
            # New format: roll results already computed
            logger.info("Using completed roll submission handler")
            # Process through unified interface
            result, status_code = await process_game_event(
                GameEventType.COMPLETED_ROLL_SUBMISSION,
                {"roll_results": request.roll_results},
                game_orchestrator,
            )
        else:
            # Legacy format: roll requests that need to be processed
            logger.info("Using legacy dice submission handler")
            # Ensure rolls is a list
            if isinstance(request.rolls, DiceRollSubmissionModel):
                roll_submissions = [request.rolls]
            elif request.rolls is not None:
                roll_submissions = request.rolls
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No roll data provided",
                )
            # Process through unified interface
            result, status_code = await process_game_event(
                GameEventType.DICE_SUBMISSION,
                {"rolls": roll_submissions},
                game_orchestrator,
            )

        # Set the HTTP status code
        response.status_code = status_code

        # Return the response regardless of status code
        # The response model includes the error and full game state
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_rolls: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/trigger_next_step",
    response_model=GameEventResponseModel,
    response_model_exclude_none=True,
)
async def trigger_next_step(
    response: Response,
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> GameEventResponseModel:
    """Trigger the next step in the game (usually for NPC turns)."""
    try:
        # Process through unified interface with empty data
        result, status_code = await process_game_event(
            GameEventType.NEXT_STEP,
            {},  # Empty dict for events without data
            game_orchestrator,
        )

        # Set the HTTP status code
        response.status_code = status_code

        # Return the response regardless of status code
        # The response model includes the error and full game state
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in trigger_next_step: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/retry_last_ai_request",
    response_model=GameEventResponseModel,
    response_model_exclude_none=True,
)
async def retry_last_ai_request(
    response: Response,
    game_orchestrator: IGameOrchestrator = Depends(get_game_orchestrator),
) -> GameEventResponseModel:
    """Retry the last AI request that failed."""
    try:
        # Process through unified interface with empty data
        result, status_code = await process_game_event(
            GameEventType.RETRY,
            {},  # Empty dict for events without data
            game_orchestrator,
        )

        # Set the HTTP status code
        response.status_code = status_code

        # Return the response regardless of status code
        # The response model includes the error and full game state
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in retry_last_ai_request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/perform_roll", response_model=DiceRollResultResponseModel)
async def perform_roll(
    request: PerformRollRequest,
    dice_service: IDiceRollingService = Depends(get_dice_service),
) -> DiceRollResultResponseModel:
    """Perform an immediate dice roll and return the result."""
    try:
        # Perform the roll
        roll_result = dice_service.perform_roll(
            character_id=request.character_id,
            roll_type=request.roll_type,
            dice_formula=request.dice_formula,
            skill=request.skill,
            ability=request.ability,
            dc=request.dc,
            reason=request.reason,
            original_request_id=request.request_id,
        )

        # Return the result directly - it's already a DiceRollResultResponseModel
        return roll_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in perform_roll: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/game_state/save", response_model=SaveGameResponse)
async def save_game_state(
    game_state_repo: IGameStateRepository = Depends(get_game_state_repository),
) -> SaveGameResponse:
    """Manually save the current game state."""
    try:
        # Get the current game state
        game_state = game_state_repo.get_game_state()

        # Save it (this will use the appropriate file path based on campaign_id)
        game_state_repo.save_game_state(game_state)

        logger.info(f"Game state saved manually for campaign: {game_state.campaign_id}")

        return SaveGameResponse(
            success=True,
            save_file=f"campaign_{game_state.campaign_id}",
            message="Game state saved successfully",
            campaign_id=game_state.campaign_id,
        )

    except Exception as e:
        logger.error(f"Error in save_game_state: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
