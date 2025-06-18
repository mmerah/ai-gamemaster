"""
Main game orchestrator that directly manages action handlers for game events.
"""

import logging
from typing import Any, Dict, List, Optional

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
from app.services.action_handlers.dice_submission_handler import DiceSubmissionHandler
from app.services.action_handlers.next_step_handler import NextStepHandler
from app.services.action_handlers.player_action_handler import PlayerActionHandler
from app.services.action_handlers.retry_handler import RetryHandler
from app.services.chat_service import ChatFormatter
from app.services.shared_state_manager import SharedStateManager

logger = logging.getLogger(__name__)


class GameOrchestrator:
    """
    Main game orchestrator that directly manages action handlers for game events.
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
        shared_state_manager: SharedStateManager,
        rag_service: Optional[IRAGService] = None,
    ) -> None:
        # Store core dependencies
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.shared_state_manager = shared_state_manager

        # Initialize action handlers directly
        self.player_action_handler = PlayerActionHandler(
            game_state_repo=game_state_repo,
            character_service=character_service,
            dice_service=dice_service,
            combat_service=combat_service,
            chat_service=chat_service,
            ai_response_processor=ai_response_processor,
            campaign_service=campaign_service,
            rag_service=rag_service,
        )

        self.dice_submission_handler = DiceSubmissionHandler(
            game_state_repo=game_state_repo,
            character_service=character_service,
            dice_service=dice_service,
            combat_service=combat_service,
            chat_service=chat_service,
            ai_response_processor=ai_response_processor,
            campaign_service=campaign_service,
            rag_service=rag_service,
        )

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

        # Setup shared state manager for all handlers
        self._setup_shared_context()

    def handle_player_action(
        self, action_data: PlayerActionEventModel
    ) -> GameEventResponseModel:
        """Handle a player action by delegating to player action handler."""
        return self.player_action_handler.handle(action_data)

    def handle_dice_submission(
        self, roll_data: List[DiceRollSubmissionModel]
    ) -> GameEventResponseModel:
        """Handle submitted dice rolls by delegating to dice submission handler."""
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
        """Handle a game event by routing to the appropriate handler.

        Args:
            event: Event model with 'type' and 'data' fields
            session_id: Optional session ID (not used in single-player app)

        Returns:
            Response data from the appropriate handler
        """
        event_type = event.type
        event_data = event.data

        if event_type == "player_action":
            # Ensure event_data is the correct type
            if isinstance(event_data, PlayerActionEventModel):
                return self.handle_player_action(event_data)
            else:
                logger.error(
                    f"Invalid event data type for player_action: {type(event_data)}"
                )
                raise ValueError(
                    f"Invalid event data type for player_action: {type(event_data)}"
                )
        elif event_type == "dice_submission":
            # Extract rolls from event data
            if hasattr(event_data, "rolls"):
                rolls = event_data.rolls
            else:
                rolls = []
            return self.handle_dice_submission(rolls)
        elif event_type == "next_step":
            return self.handle_next_step_trigger()
        elif event_type == "retry":
            return self.handle_retry()
        # Note: else clause removed as all possible Literal values are covered

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
        """Set up shared context across all handlers.

        This ensures that AI request retry functionality works correctly
        across different handlers.
        """
        # Share state manager with all handlers
        all_handlers = [
            self.player_action_handler,
            self.dice_submission_handler,
            self.next_step_handler,
            self.retry_handler,
        ]

        for handler in all_handlers:
            # Give each handler a reference to the shared state manager
            handler._shared_state_manager = self.shared_state_manager

        logger.debug("Shared context setup complete across all handlers")
