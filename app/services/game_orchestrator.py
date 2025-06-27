"""
Main game orchestrator that directly manages action handlers for game events.
"""

import asyncio
import logging
from typing import Dict, List

from app.core.domain_interfaces import ICharacterService
from app.core.handler_interfaces import (
    IDiceSubmissionHandler,
    INextStepHandler,
    IPlayerActionHandler,
    IRetryHandler,
)
from app.core.orchestration_interfaces import IGameOrchestrator
from app.core.repository_interfaces import IGameStateRepository
from app.domain.combat.combat_utilities import CombatFormatter
from app.models.character.combined import CombinedCharacterModel
from app.models.character.instance import CharacterInstanceModel
from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.events.event_types import GameEventType
from app.models.events.game_events import (
    GameEventModel,
    GameEventResponseModel,
    PlayerActionEventModel,
)
from app.services.chat_service import ChatFormatter
from app.services.shared_state_manager import SharedStateManager

logger = logging.getLogger(__name__)


class GameOrchestrator(IGameOrchestrator):
    """
    Main game orchestrator with a single public entry point.

    Usage:
        orchestrator = container.get_game_orchestrator()
        event = GameEventModel(
            type=GameEventType.PLAYER_ACTION,
            data=PlayerActionEventModel(value="I cast fireball")
        )
        response = orchestrator.handle_event(event)
    """

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        character_service: ICharacterService,
        shared_state_manager: SharedStateManager,
        player_action_handler: IPlayerActionHandler,
        dice_submission_handler: IDiceSubmissionHandler,
        next_step_handler: INextStepHandler,
        retry_handler: IRetryHandler,
    ) -> None:
        # Store core dependencies
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.shared_state_manager = shared_state_manager

        # Store injected handlers
        self.player_action_handler = player_action_handler
        self.dice_submission_handler = dice_submission_handler
        self.next_step_handler = next_step_handler
        self.retry_handler = retry_handler

        # Setup shared state manager for all handlers
        self._setup_shared_context()

    def _handle_player_action(
        self, action_data: PlayerActionEventModel
    ) -> GameEventResponseModel:
        """Handle a player action by delegating to player action handler."""
        return self.player_action_handler.handle(action_data)

    def _handle_dice_submission(
        self, roll_data: List[DiceRollSubmissionModel]
    ) -> GameEventResponseModel:
        """Handle submitted dice rolls by delegating to dice submission handler."""
        return self.dice_submission_handler.handle(roll_data)

    def _handle_completed_roll_submission(
        self, roll_results: List[DiceRollResultResponseModel]
    ) -> GameEventResponseModel:
        """Handle submission of already-completed roll results."""
        return self.dice_submission_handler.handle_completed_rolls(roll_results)

    def _handle_next_step_trigger(self) -> GameEventResponseModel:
        """Handle triggering the next step."""
        return self.next_step_handler.handle()

    def _handle_retry(self) -> GameEventResponseModel:
        """Handle retry request."""
        return self.retry_handler.handle()

    async def handle_event(self, event: GameEventModel) -> GameEventResponseModel:
        """
        Process any game event.

        This is the ONLY public method for event processing.
        All game actions should be wrapped in a GameEventModel.

        Args:
            event: The game event to process

        Returns:
            Response containing game state updates

        Raises:
            ValueError: If event type is unknown or data is invalid
        """
        event_type = event.type
        event_data = event.data

        if event_type == GameEventType.PLAYER_ACTION:
            # Ensure event_data is the correct type
            if isinstance(event_data, PlayerActionEventModel):
                return await asyncio.to_thread(self._handle_player_action, event_data)
            else:
                logger.error(
                    f"Invalid event data type for player_action: {type(event_data)}"
                )
                raise ValueError(
                    f"Invalid event data type for player_action: {type(event_data)}"
                )
        elif event_type == GameEventType.DICE_SUBMISSION:
            # Extract rolls from event data
            if hasattr(event_data, "rolls"):
                rolls = event_data.rolls
            else:
                rolls = []
            return await asyncio.to_thread(self._handle_dice_submission, rolls)
        elif event_type == GameEventType.COMPLETED_ROLL_SUBMISSION:
            # Extract roll results from event data
            if hasattr(event_data, "roll_results"):
                roll_results = event_data.roll_results
            elif isinstance(event_data, dict) and "roll_results" in event_data:
                # Handle dict format
                roll_results = event_data["roll_results"]
            else:
                roll_results = []
            return await asyncio.to_thread(
                self._handle_completed_roll_submission, roll_results
            )
        elif event_type == GameEventType.NEXT_STEP:
            return await asyncio.to_thread(self._handle_next_step_trigger)
        elif event_type == GameEventType.RETRY:
            return await asyncio.to_thread(self._handle_retry)
        else:
            raise ValueError(f"Unknown event type: {event_type.value}")

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
            can_retry_last_request=self.shared_state_manager.can_retry_last_request(),
            needs_backend_trigger=self.shared_state_manager.get_needs_backend_trigger(),
        )

    def _format_party_for_frontend(
        self, party_instances: Dict[str, CharacterInstanceModel]
    ) -> List[CombinedCharacterModel]:
        """Format party data for frontend."""
        # Use the character service to get full character data
        char_data_list: List[CombinedCharacterModel] = []

        for char_id, _ in party_instances.items():
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
        """Set up shared context across all handlers.

        This ensures that AI request retry functionality works correctly
        across different handlers.
        """
        # Import here to avoid circular imports
        from app.services.event_handlers.base_handler import BaseEventHandler

        # Share state manager with all handlers
        all_handlers = [
            self.player_action_handler,
            self.dice_submission_handler,
            self.next_step_handler,
            self.retry_handler,
        ]

        for handler in all_handlers:
            # Give each handler a reference to the shared state manager
            # We know these are BaseEventHandler instances, so cast them
            if isinstance(handler, BaseEventHandler):
                handler._shared_state_manager = self.shared_state_manager

        logger.debug("Shared context setup complete across all handlers")
