"""
Campaign management API routes.
"""

import logging
from typing import Optional, Tuple, Union

from flask import Blueprint, Response, jsonify
from pydantic import ValidationError

from app.core.container import get_container
from app.models.game_state import GameStateModel

logger = logging.getLogger(__name__)

# Create blueprint for campaign API routes
campaign_bp = Blueprint("campaign", __name__, url_prefix="/api")


@campaign_bp.route("/campaign-instances")
def get_campaign_instances() -> Union[Response, Tuple[Response, int]]:
    """Get all campaign instances (ongoing games)."""
    try:
        container = get_container()
        instance_repo = container.get_campaign_instance_repository()

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
                "created_date": instance.created_date.isoformat()
                if instance.created_date
                else None,
                "last_played": instance.last_played.isoformat()
                if instance.last_played
                else None,
                "created_at": instance.created_date.isoformat()
                if instance.created_date
                else None,  # Frontend compatibility
                "narration_enabled": instance.narration_enabled,
                "tts_voice": instance.tts_voice,
            }
            instances_data.append(instance_dict)

        return jsonify({"campaigns": instances_data})

    except Exception as e:
        logger.error(f"Error getting campaign instances: {e}", exc_info=True)
        return jsonify({"error": "Failed to get campaign instances"}), 500


@campaign_bp.route("/campaigns/<campaign_id>/start", methods=["POST"])
def start_campaign(campaign_id: str) -> Union[Response, Tuple[Response, int]]:
    """Start/load a campaign.

    IMPORTANT: Despite the route name, campaign_id here can be either:
    - A campaign instance ID (for loading an existing game)
    - A campaign template ID (for starting a new game - deprecated path)

    This endpoint loads a saved campaign instance and makes it the active game.
    If no saved state exists, it initializes from the campaign template.
    """
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()

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
                return jsonify(
                    {"error": "Failed to get initial campaign definition"}
                ), 400

            final_game_state = game_state_model

        # Save this state (either loaded or newly initialized)
        # This also makes it the "active" state in the repository's memory
        game_state_repo.save_game_state(final_game_state)

        return jsonify(
            {
                "message": "Campaign started successfully",
                "initial_state": final_game_state.model_dump(),
            }
        )

    except ValidationError as e:
        logger.error(f"Validation error starting campaign {campaign_id}: {e}")
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        logger.error(f"Error starting campaign {campaign_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to start campaign"}), 500
