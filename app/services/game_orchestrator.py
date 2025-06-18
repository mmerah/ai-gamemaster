"""
Main game orchestrator that coordinates specialized orchestration services.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from app.core.interfaces import (
    IAIResponseProcessor,
    ICharacterService,
    IChatService,
    ICombatService,
    IDiceRollingService,
    IGameStateRepository,
    IRAGService,
)
from app.domain.campaigns.campaign_service import CampaignService
from app.domain.combat.combat_utilities import CombatFormatter
from app.models.character import CharacterInstanceModel, CombinedCharacterModel
from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.game_state import (
    GameEventModel,
    GameEventResponseModel,
    PlayerActionEventModel,
)
from app.services.chat_service import ChatFormatter
from app.services.orchestration import (
    CombatOrchestrationService,
    EventRoutingService,
    NarrativeOrchestrationService,
)

logger = logging.getLogger(__name__)


class GameOrchestrator:
    """
    Coordinates between specialized orchestration services.
    Acts as a thin layer that delegates to appropriate services.
    """

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        character_service: ICharacterService,
        dice_service: IDiceRollingService,
        combat_service: ICombatService,
        chat_service: IChatService,
        ai_response_processor: IAIResponseProcessor,
        campaign_service: CampaignService,
        rag_service: Optional[IRAGService] = None,
    ) -> None:
        # Store core dependencies needed for state formatting
        self.game_state_repo = game_state_repo
        self.character_service = character_service

        # Initialize specialized orchestration services
        self.combat_orchestration = CombatOrchestrationService(
            game_state_repo=game_state_repo,
            character_service=character_service,
            dice_service=dice_service,
            combat_service=combat_service,
            chat_service=chat_service,
            ai_response_processor=ai_response_processor,
        )

        self.narrative_orchestration = NarrativeOrchestrationService(
            game_state_repo=game_state_repo,
            character_service=character_service,
            chat_service=chat_service,
            ai_response_processor=ai_response_processor,
            campaign_service=campaign_service,
            rag_service=rag_service,
        )

        self.event_routing = EventRoutingService(
            game_state_repo=game_state_repo,
            character_service=character_service,
            dice_service=dice_service,
            combat_service=combat_service,
            chat_service=chat_service,
            ai_response_processor=ai_response_processor,
            campaign_service=campaign_service,
            rag_service=rag_service,
        )

        # Initialize handlers with all required services
        self.narrative_orchestration.initialize_handler(dice_service, combat_service)
        self.combat_orchestration.initialize_handler(campaign_service, rag_service)

        # Register event handlers with the routing service
        self._register_event_handlers()

        # Setup shared context across all services
        self._setup_shared_context()

    def handle_player_action(
        self, action_data: PlayerActionEventModel
    ) -> GameEventResponseModel:
        """Handle a player action by delegating to narrative orchestration."""
        return self.narrative_orchestration.handle_player_message(action_data)

    def handle_dice_submission(
        self, roll_data: List[DiceRollSubmissionModel]
    ) -> GameEventResponseModel:
        """Handle submitted dice rolls by delegating to combat orchestration."""
        return self.combat_orchestration.handle_dice_submission(roll_data)

    def handle_completed_roll_submission(
        self, roll_results: List[DiceRollResultResponseModel]
    ) -> GameEventResponseModel:
        """Handle submission of already-completed roll results."""
        return self.combat_orchestration.handle_completed_roll_submission(roll_results)

    def handle_next_step_trigger(self) -> GameEventResponseModel:
        """Handle triggering the next step via event routing."""
        return self.event_routing.handle_next_step_trigger()

    def handle_retry(self) -> GameEventResponseModel:
        """Handle retry request via event routing."""
        return self.event_routing.handle_retry()

    def handle_event(
        self, event: GameEventModel, session_id: Optional[str] = None
    ) -> GameEventResponseModel:
        """Handle a game event by routing to the appropriate service.

        Args:
            event: Event dictionary or model with 'type' and 'data' fields
            session_id: Optional session ID (not used in current implementation)

        Returns:
            Response data from the appropriate handler
        """
        # Use event routing service to handle all events
        return self.event_routing.route_event(event, session_id)

    def get_game_state(self) -> GameEventResponseModel:
        """Get current game state for frontend."""
        return self._get_state_for_frontend()

    def _get_state_for_frontend(self) -> GameEventResponseModel:
        """Get current game state formatted for frontend."""
        game_state = self.game_state_repo.get_game_state()

        # Use dice requests directly (no conversion needed)
        dice_requests = game_state.pending_player_dice_requests

        return GameEventResponseModel(
            party=self._format_party_for_frontend(game_state.party),
            location=game_state.current_location.name
            if game_state.current_location
            else "Unknown",
            location_description=game_state.current_location.description
            if game_state.current_location
            else "",
            chat_history=ChatFormatter.format_for_frontend(game_state.chat_history),
            dice_requests=dice_requests,
            combat_info=CombatFormatter.format_combat_status(self.game_state_repo),
            can_retry_last_request=self.event_routing.can_retry_last_request(),
            needs_backend_trigger=self.event_routing.get_shared_state().needs_backend_trigger,
        )

    def _format_party_for_frontend(
        self, party_instances: Dict[str, CharacterInstanceModel]
    ) -> List[CombinedCharacterModel]:
        """Format party data for frontend."""
        # Use the character service to get full character data
        char_data_list: List[CombinedCharacterModel] = []

        for char_id, char_instance in party_instances.items():
            # Get full character data including template
            char_data = self.character_service.get_character(char_id)
            if char_data:
                template = char_data.template
                instance = char_data.instance

                # Use the factory method to create CombinedCharacterModel
                combined_model = CombinedCharacterModel.from_template_and_instance(
                    template=template, instance=instance, character_id=char_id
                )
                char_data_list.append(combined_model)

        return char_data_list

    def _register_event_handlers(self) -> None:
        """Register event type handlers with the event routing service."""

        # Register player action handler
        def handle_player_action(
            event_data: PlayerActionEventModel,
        ) -> GameEventResponseModel:
            return self.handle_player_action(event_data)

        self.event_routing.register_handler("player_action", handle_player_action)

        # Register dice submission handler
        def handle_dice_submission(event_data: Any) -> GameEventResponseModel:
            # Extract rolls from event data
            if hasattr(event_data, "rolls"):
                rolls = event_data.rolls
            else:
                rolls = []
            return self.handle_dice_submission(rolls)

        self.event_routing.register_handler("dice_submission", handle_dice_submission)

        logger.info("Registered event handlers with event routing service")

    def _setup_shared_context(self) -> None:
        """Set up shared context across all orchestration services.

        This ensures that AI request retry functionality works correctly
        across different services and handlers.
        """
        # Get shared state from event routing
        shared_state = self.event_routing.get_shared_state()

        # Share state with other orchestration services' handlers
        if self.narrative_orchestration.player_action_handler:
            self.narrative_orchestration.player_action_handler._shared_state = (
                shared_state
            )

        if self.combat_orchestration.dice_submission_handler:
            self.combat_orchestration.dice_submission_handler._shared_state = (
                shared_state
            )

        # Set up shared retry context for all handlers
        all_handlers: List[Any] = []
        if self.narrative_orchestration.player_action_handler:
            all_handlers.append(self.narrative_orchestration.player_action_handler)
        if self.combat_orchestration.dice_submission_handler:
            all_handlers.append(self.combat_orchestration.dice_submission_handler)

        for handler in all_handlers:
            # Create closures that capture the event routing service
            routing_service = self.event_routing

            def make_shared_store_context(handler: Any) -> Any:
                def shared_store_ai_request_context(
                    messages: List[Dict[str, str]],
                    initial_instruction: Optional[str] = None,
                ) -> None:
                    """Store context in the shared routing service."""
                    routing_service.store_ai_request_context(
                        messages, initial_instruction
                    )
                    # Also update handler's local references
                    handler._last_ai_request_context = (
                        routing_service._shared_ai_request_context
                    )
                    handler._last_ai_request_timestamp = (
                        routing_service._shared_ai_request_timestamp
                    )

                return shared_store_ai_request_context

            def make_shared_can_retry(handler: Any) -> Any:
                def shared_can_retry_last_request() -> bool:
                    """Check retry availability from shared context."""
                    # Sync the handler's context with shared context
                    handler._last_ai_request_context = (
                        routing_service._shared_ai_request_context
                    )
                    handler._last_ai_request_timestamp = (
                        routing_service._shared_ai_request_timestamp
                    )
                    return routing_service.can_retry_last_request()

                return shared_can_retry_last_request

            # Replace the methods
            handler._store_ai_request_context = make_shared_store_context(handler)
            handler._can_retry_last_request = make_shared_can_retry(handler)

            # Initialize the handler's context references to the shared ones
            handler._last_ai_request_context = (
                self.event_routing._shared_ai_request_context
            )
            handler._last_ai_request_timestamp = (
                self.event_routing._shared_ai_request_timestamp
            )

        # The event routing service already manages the shared context for its own handlers
        # (next_step_handler and retry_handler)

        logger.debug("Shared context setup complete across all orchestration services")
