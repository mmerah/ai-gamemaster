"""
Routes game events to appropriate handlers and manages shared concerns.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from app.core.interfaces import (
    AIResponseProcessor,
    CharacterService,
    ChatService,
    CombatService,
    DiceRollingService,
    GameStateRepository,
    RAGService,
)
from app.domain.campaigns.service import CampaignService
from app.models.game_state import (
    AIRequestContextModel,
    GameEventModel,
    GameEventResponseModel,
)
from app.models.utils import SharedHandlerStateModel
from app.services.game_events.handlers.next_step_handler import NextStepHandler
from app.services.game_events.handlers.retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class EventRoutingService:
    """Routes game events to appropriate handlers and manages shared concerns."""

    def __init__(
        self,
        game_state_repo: GameStateRepository,
        character_service: CharacterService,
        dice_service: DiceRollingService,
        combat_service: CombatService,
        chat_service: ChatService,
        ai_response_processor: AIResponseProcessor,
        campaign_service: CampaignService,
        rag_service: Optional[RAGService] = None,
    ):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor
        self.campaign_service = campaign_service
        self.rag_service = rag_service

        # Shared retry context storage
        self._shared_ai_request_context: Optional[AIRequestContextModel] = None
        self._shared_ai_request_timestamp: Optional[float] = None

        # Shared AI processing flag to prevent concurrent AI calls
        self._shared_state = SharedHandlerStateModel(
            ai_processing=False, needs_backend_trigger=False
        )

        # Initialize general handlers
        self.next_step_handler = NextStepHandler(
            game_state_repo=game_state_repo,
            character_service=character_service,
            dice_service=dice_service,
            combat_service=combat_service,
            chat_service=chat_service,
            ai_response_processor=ai_response_processor,
            campaign_service=campaign_service,
            rag_service=rag_service,
        )

        self.retry_handler = RetryHandler(
            game_state_repo=game_state_repo,
            character_service=character_service,
            dice_service=dice_service,
            combat_service=combat_service,
            chat_service=chat_service,
            ai_response_processor=ai_response_processor,
            campaign_service=campaign_service,
            rag_service=rag_service,
        )

        # Event type to handler mapping (will be populated by GameOrchestrator)
        self.event_handlers: Dict[str, Callable[[Any], GameEventResponseModel]] = {}

        # Setup shared context for handlers
        self._setup_shared_context()

    def register_handler(
        self, event_type: str, handler: Callable[[Any], GameEventResponseModel]
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The event type to handle
            handler: The handler function
        """
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered handler for event type: {event_type}")

    def route_event(
        self, event: GameEventModel, _session_id: Optional[str] = None
    ) -> GameEventResponseModel:
        """Route an event to the appropriate handler.

        Args:
            event: The game event to route
            _session_id: Optional session ID (currently unused)

        Returns:
            Response from the handler

        Raises:
            ValueError: If no handler is registered for the event type
        """
        event_type = event.type
        logger.info(f"Routing event of type: {event_type}")

        # Check for built-in handlers first
        if event_type == "next_step":
            return self.handle_next_step_trigger()
        elif event_type == "retry":
            return self.handle_retry()

        # Check registered handlers
        handler = self.event_handlers.get(event_type)
        if not handler:
            error_msg = f"No handler registered for event type: {event_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Call the handler with event data
        return handler(event.data)

    def handle_next_step_trigger(self) -> GameEventResponseModel:
        """Handle triggering the next step."""
        return self.next_step_handler.handle()

    def handle_retry(self) -> GameEventResponseModel:
        """Handle retry request."""
        return self.retry_handler.handle()

    def store_ai_request_context(
        self, messages: List[Dict[str, str]], initial_instruction: Optional[str] = None
    ) -> None:
        """Store AI request context for potential retry.

        Args:
            messages: The messages sent to AI
            initial_instruction: Optional initial instruction
        """
        self._shared_ai_request_context = AIRequestContextModel(
            messages=messages.copy(),
            initial_instruction=initial_instruction,
        )
        self._shared_ai_request_timestamp = time.time()
        logger.debug("Stored AI request context for retry")

    def can_retry_last_request(self) -> bool:
        """Check if the last AI request can be retried.

        Returns:
            True if retry is possible, False otherwise
        """
        if not self._shared_ai_request_context or not self._shared_ai_request_timestamp:
            return False

        # Allow retry within 5 minutes
        return (time.time() - self._shared_ai_request_timestamp) <= 300

    def get_shared_state(self) -> SharedHandlerStateModel:
        """Get the shared state model.

        Returns:
            The shared state model
        """
        return self._shared_state

    def _setup_shared_context(self) -> None:
        """Set up shared context for handlers."""
        # Share context with handlers that need it
        for handler in [self.next_step_handler, self.retry_handler]:
            # Share the state model
            handler._shared_state = self._shared_state

            # Store original methods for potential restoration
            handler._original_store_ai_request_context = (  # type: ignore[attr-defined]
                handler._store_ai_request_context
            )
            handler._original_can_retry_last_request = handler._can_retry_last_request  # type: ignore[attr-defined]

            # Create a shared storage proxy that updates both the handler and routing service
            routing_service = self

            def shared_store_ai_request_context(
                messages: List[Dict[str, str]],
                initial_instruction: Optional[str] = None,
            ) -> None:
                """Store context in both the handler and the shared routing service."""
                # Store in routing service (shared)
                routing_service.store_ai_request_context(messages, initial_instruction)
                # Also update handler's local references
                handler._last_ai_request_context = (
                    routing_service._shared_ai_request_context
                )
                handler._last_ai_request_timestamp = (
                    routing_service._shared_ai_request_timestamp
                )

            def shared_can_retry_last_request() -> bool:
                """Check retry availability from shared context."""
                # Sync the handler's context with shared context
                handler._last_ai_request_context = (
                    routing_service._shared_ai_request_context
                )
                handler._last_ai_request_timestamp = (
                    routing_service._shared_ai_request_timestamp
                )
                # Use routing service's check
                return routing_service.can_retry_last_request()

            # Replace the methods with type-safe wrappers
            handler._store_ai_request_context = shared_store_ai_request_context  # type: ignore
            handler._can_retry_last_request = shared_can_retry_last_request  # type: ignore

            # Initialize the handler's context references to the shared ones
            handler._last_ai_request_context = self._shared_ai_request_context
            handler._last_ai_request_timestamp = self._shared_ai_request_timestamp
