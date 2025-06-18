"""
Helper functions for API routes.
"""

import logging
from typing import Any, Dict, Tuple

from app.core.container import get_container
from app.models.events import GameEventModel, GameEventType

logger = logging.getLogger(__name__)


def process_game_event(
    event_type: GameEventType, data: Any
) -> Tuple[Dict[str, Any], int]:
    """
    Helper to process game events consistently across routes.

    Args:
        event_type: The type of game event
        data: Event-specific data

    Returns:
        Tuple of (response_dict, http_status_code)
    """
    try:
        # Create event model
        event = GameEventModel(type=event_type, data=data)

        # Get orchestrator and process event
        container = get_container()
        orchestrator = container.get_game_orchestrator()
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
