"""
Campaign management API routes - FastAPI version.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError as PydanticValidationError

from app.api.dependencies_fastapi import (
    get_campaign_instance_repository,
    get_campaign_service,
    get_game_state_repository,
)
from app.core.domain_interfaces import ICampaignService
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    IGameStateRepository,
)
from app.models.game_state import GameStateModel

logger = logging.getLogger(__name__)

# Create router for campaign API routes
router = APIRouter(prefix="/api", tags=["campaigns"])


@router.get("/campaign-instances")
async def get_campaign_instances(
    instance_repo: ICampaignInstanceRepository = Depends(
        get_campaign_instance_repository
    ),
) -> Dict[str, List[Dict[str, Any]]]:
    """Get all campaign instances (ongoing games)."""
    try:
        instances = instance_repo.list()
        logger.info(f"Retrieved {len(instances)} campaign instances")
        # Convert to dict for JSON serialization
        instances_data = []
        for instance in instances:
            instance_dict = {
                "id": instance.id,
                "name": instance.name,
                "template_id": instance.template_id,
                "character_ids": instance.character_ids,
                "party_size": len(instance.character_ids),
                "current_location": instance.current_location,
                "session_count": instance.session_count,
                "in_combat": instance.in_combat,
                "created_date": (
                    instance.created_date.isoformat() if instance.created_date else None
                ),
                "last_played": (
                    instance.last_played.isoformat() if instance.last_played else None
                ),
                "created_at": (
                    instance.created_date.isoformat() if instance.created_date else None
                ),  # Frontend compatibility
                "narration_enabled": instance.narration_enabled,
                "tts_voice": instance.tts_voice,
            }
            instances_data.append(instance_dict)

        return {"campaigns": instances_data}
    except Exception as e:
        logger.error(f"Error getting campaign instances: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve campaign instances",
        )


@router.post("/campaigns/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    campaign_service: ICampaignService = Depends(get_campaign_service),
    game_state_repo: IGameStateRepository = Depends(get_game_state_repository),
) -> Dict[str, Any]:
    """Start/load a campaign.

    IMPORTANT: Despite the route name, campaign_id here can be either:
    - A campaign instance ID (for loading an existing game)
    - A campaign template ID (for starting a new game - deprecated path)

    This endpoint loads a saved campaign instance and makes it the active game.
    If no saved state exists, it initializes from the campaign template.
    """
    try:
        loaded_game_state: Optional[GameStateModel] = None

        # Attempt to load existing saved state for this campaign
        if hasattr(game_state_repo, "load_campaign_state"):
            loaded_game_state = game_state_repo.load_campaign_state(campaign_id)

        final_game_state: GameStateModel
        if loaded_game_state:
            logger.info(f"Loaded existing game state for campaign {campaign_id}")
            final_game_state = loaded_game_state
        else:
            logger.info(
                f"No existing save for campaign {campaign_id}, initializing new state from definition."
            )
            game_state_model = campaign_service.start_campaign(
                campaign_id
            )  # Gets initial definition as GameStateModel
            if not game_state_model:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get initial campaign definition",
                )

            final_game_state = game_state_model

        # Save this state (either loaded or newly initialized)
        # This also makes it the "active" state in the repository's memory
        game_state_repo.save_game_state(final_game_state)

        return {
            "message": "Campaign started successfully",
            "initial_state": final_game_state.model_dump(),
        }
    except HTTPException:
        raise
    except PydanticValidationError as e:
        logger.error(f"Validation error in start_campaign: {e}")
        # Extract validation errors
        validation_errors = {}
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            validation_errors[field] = err["msg"]
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation failed",
                "validation_errors": validation_errors,
            },
        )
    except Exception as e:
        logger.error(f"Error starting campaign: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start campaign",
        )
