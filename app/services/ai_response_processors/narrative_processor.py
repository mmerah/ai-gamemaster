"""
Narrative processor for AI response processing.
"""

import logging
from typing import Optional

from app.core.domain_interfaces import IChatService
from app.core.repository_interfaces import IGameStateRepository
from app.core.system_interfaces import IEventQueue
from app.models.events.game_state import LocationChangedEvent
from app.models.updates import LocationUpdateModel
from app.models.utils import LocationModel
from app.providers.ai.schemas import AIResponse
from app.services.ai_response_processors.interfaces import INarrativeProcessor
from app.utils.event_helpers import emit_with_logging

logger = logging.getLogger(__name__)


class NarrativeProcessor(INarrativeProcessor):
    """Handles narrative and location updates from AI responses."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        chat_service: IChatService,
        event_queue: IEventQueue,
    ):
        self.game_state_repo = game_state_repo
        self.chat_service = chat_service
        self.event_queue = event_queue

    def process_narrative_and_location(
        self, ai_response: AIResponse, correlation_id: Optional[str] = None
    ) -> None:
        """Process narrative and location updates from AI response."""
        # Log AI reasoning
        if ai_response.reasoning:
            logger.info(f"AI Reasoning: {ai_response.reasoning}")
        else:
            logger.warning("AI Response missing 'reasoning'.")

        # Add AI response to chat history
        self.chat_service.add_message(
            "assistant",
            ai_response.narrative,
            ai_response_json=ai_response.model_dump_json(),
            correlation_id=correlation_id,
        )

        # Update location if provided
        if ai_response.location_update:
            self._update_location(ai_response.location_update)

    def _update_location(self, location_update: LocationUpdateModel) -> None:
        """Update the current location and emit location change event."""
        game_state = self.game_state_repo.get_game_state()

        old_name = game_state.current_location.name
        game_state.current_location = LocationModel(
            name=location_update.name, description=location_update.description
        )
        logger.info(f"Location updated from '{old_name}' to '{location_update.name}'.")

        # Emit LocationChangedEvent
        emit_with_logging(
            self.event_queue,
            LocationChangedEvent(
                old_location_name=old_name,
                new_location_name=location_update.name,
                new_location_description=location_update.description,
            ),
            f"{old_name} -> {location_update.name}",
        )
