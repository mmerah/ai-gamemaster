"""
Main game event manager that coordinates all event handlers.
"""

import logging
import time
from typing import Callable, Dict, List, Optional

from app.core.interfaces import (
    AIResponseProcessor,
    CharacterService,
    ChatService,
    CombatService,
    DiceRollingService,
    GameStateRepository,
)
from app.core.rag_interfaces import RAGService
from app.models.models import (
    AIRequestContextModel,
    CharacterInstanceModel,
    CombinedCharacterModel,
    DiceRollResultResponseModel,
    DiceRollSubmissionModel,
    GameEventModel,
    GameEventResponseModel,
    PlayerActionEventModel,
    SharedHandlerStateModel,
)
from app.services.campaign_service import CampaignService
from app.services.chat_service import ChatFormatter
from app.services.combat_utilities import CombatFormatter

from .handlers import (
    DiceSubmissionHandler,
    NextStepHandler,
    PlayerActionHandler,
    RetryHandler,
)

logger = logging.getLogger(__name__)


class GameEventManager:
    """
    Manages all game events and delegates to appropriate handlers.
    This replaces the monolithic GameEventHandler.
    """

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
    ) -> None:
        # Store dependencies
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor
        self.campaign_service = campaign_service
        self.rag_service = rag_service

        # Shared retry context storage across all handlers
        self._shared_ai_request_context: Optional[AIRequestContextModel] = None
        self._shared_ai_request_timestamp: Optional[float] = None

        # Shared AI processing flag to prevent concurrent AI calls
        # Use a model instance to ensure the reference is shared properly
        self._shared_state = SharedHandlerStateModel(
            ai_processing=False, needs_backend_trigger=False
        )

        # Initialize handlers
        self.player_action_handler = PlayerActionHandler(
            game_state_repo,
            character_service,
            dice_service,
            combat_service,
            chat_service,
            ai_response_processor,
            campaign_service,
            rag_service,
        )

        self.dice_submission_handler = DiceSubmissionHandler(
            game_state_repo,
            character_service,
            dice_service,
            combat_service,
            chat_service,
            ai_response_processor,
            campaign_service,
            rag_service,
        )

        self.next_step_handler = NextStepHandler(
            game_state_repo,
            character_service,
            dice_service,
            combat_service,
            chat_service,
            ai_response_processor,
            campaign_service,
            rag_service,
        )

        self.retry_handler = RetryHandler(
            game_state_repo,
            character_service,
            dice_service,
            combat_service,
            chat_service,
            ai_response_processor,
            campaign_service,
            rag_service,
        )

        # Share context storage across all handlers
        self._setup_shared_context()

    def handle_player_action(
        self, action_data: PlayerActionEventModel
    ) -> GameEventResponseModel:
        """Handle a player action."""
        return self.player_action_handler.handle(action_data)

    def handle_dice_submission(
        self, roll_data: List[DiceRollSubmissionModel]
    ) -> GameEventResponseModel:
        """Handle submitted dice rolls."""
        return self.dice_submission_handler.handle(roll_data)

    def handle_completed_roll_submission(
        self, roll_results: List[DiceRollResultResponseModel]
    ) -> GameEventResponseModel:
        """Handle submission of already-completed roll results."""
        return self.dice_submission_handler.handle_completed_rolls(roll_results)

    def handle_next_step_trigger(self) -> GameEventResponseModel:
        """Handle triggering the next step."""
        return self.next_step_handler.handle()

    def handle_retry(self) -> GameEventResponseModel:
        """Handle retry request."""
        return self.retry_handler.handle()

    def handle_event(
        self, event: GameEventModel, session_id: Optional[str] = None
    ) -> GameEventResponseModel:
        """Handle a game event based on its type.

        Args:
            event: Event dictionary or model with 'type' and 'data' fields
            session_id: Optional session ID (not used in current implementation)

        Returns:
            Response data from the appropriate handler
        """
        event_type = event.type
        event_data = event.data

        if event_type == "player_action":
            # event_data is PlayerActionEventModel
            return self.handle_player_action(event_data)  # type: ignore[arg-type]
        elif event_type == "dice_submission":
            # event_data is either DiceSubmissionEvent or DiceSubmissionEventModel
            if hasattr(event_data, "rolls"):
                rolls = event_data.rolls
            else:
                rolls = []
            return self.handle_dice_submission(rolls)
        elif event_type == "next_step":
            return self.handle_next_step_trigger()
        elif event_type == "retry":
            return self.handle_retry()

        # Should never reach here if event_type is exhaustive
        assert False, f"Unknown event type: {event_type}"

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
            can_retry_last_request=self.retry_handler._can_retry_last_request(),
            needs_backend_trigger=self._shared_state.needs_backend_trigger,
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

    def _setup_shared_context(self) -> None:
        """Set up shared retry context for all handlers.

        This method implements a shared context pattern between all event handlers to ensure
        AI request retry functionality works correctly across different handler types.

        Why this approach:
        - All handlers need access to the same "last AI request" for retry functionality
        - A request made by one handler should be retryable by the retry handler
        - Prevents race conditions when multiple handlers might process events

        How it works:
        1. Replaces each handler's individual context storage with shared references
        2. Overrides the _store_ai_request_context method to update the shared context
        3. Overrides the _can_retry_last_request method to check the shared context

        Note: This dynamic method replacement ensures that regardless of which handler
        processes an event, the retry context is always consistent and accessible.
        """
        # Replace individual handler context with shared references
        for handler in [
            self.player_action_handler,
            self.dice_submission_handler,
            self.next_step_handler,
            self.retry_handler,
        ]:
            # Override their individual context storage with shared references
            handler._last_ai_request_context = self._shared_ai_request_context
            handler._last_ai_request_timestamp = self._shared_ai_request_timestamp

            # Share the AI processing state to prevent concurrent AI calls
            handler._shared_state = self._shared_state

            # Override their storage methods to update shared context
            def make_shared_store() -> Callable[
                [List[Dict[str, str]], Optional[str]], None
            ]:
                def shared_store(
                    messages: List[Dict[str, str]],
                    initial_instruction: Optional[str] = None,
                ) -> None:
                    self._shared_ai_request_context = AIRequestContextModel(
                        messages=messages.copy(),
                        initial_instruction=initial_instruction,
                    )
                    self._shared_ai_request_timestamp = time.time()
                    # Update all handlers to point to new shared context
                    for other_handler in [
                        self.player_action_handler,
                        self.dice_submission_handler,
                        self.next_step_handler,
                        self.retry_handler,
                    ]:
                        other_handler._last_ai_request_context = (
                            self._shared_ai_request_context
                        )
                        other_handler._last_ai_request_timestamp = (
                            self._shared_ai_request_timestamp
                        )

                return shared_store

            setattr(handler, "_store_ai_request_context", make_shared_store())

            # Override the can_retry method to use shared context
            def make_shared_can_retry() -> Callable[[], bool]:
                def shared_can_retry() -> bool:
                    if (
                        not self._shared_ai_request_context
                        or not self._shared_ai_request_timestamp
                    ):
                        return False
                    return (time.time() - self._shared_ai_request_timestamp) <= 300

                return shared_can_retry

            setattr(handler, "_can_retry_last_request", make_shared_can_retry())
