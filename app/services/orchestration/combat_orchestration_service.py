"""
Handles combat-specific game flow orchestration.
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from app.core.interfaces import (
    AIResponseProcessor,
    CharacterService,
    ChatService,
    CombatService,
    DiceRollingService,
    GameStateRepository,
    RAGService,
)
from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.game_state import GameEventResponseModel
from app.services.game_events.handlers.dice_submission_handler import (
    DiceSubmissionHandler,
)

if TYPE_CHECKING:
    from app.domain.campaigns.service import CampaignService

logger = logging.getLogger(__name__)


class CombatOrchestrationService:
    """Handles combat-specific game flow orchestration."""

    def __init__(
        self,
        game_state_repo: GameStateRepository,
        character_service: CharacterService,
        dice_service: DiceRollingService,
        combat_service: CombatService,
        chat_service: ChatService,
        ai_response_processor: AIResponseProcessor,
    ):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor

        # Store dependencies for handler creation
        self._game_state_repo = game_state_repo
        self._character_service = character_service
        self._dice_service = dice_service
        self._combat_service = combat_service
        self._chat_service = chat_service
        self._ai_response_processor = ai_response_processor

        # Dice submission handler will be created after campaign service is injected
        self.dice_submission_handler: Optional[DiceSubmissionHandler] = None

    def initialize_handler(
        self,
        campaign_service: "CampaignService",
        rag_service: Optional[RAGService] = None,
    ) -> None:
        """Initialize the dice submission handler with all required services."""
        self.dice_submission_handler = DiceSubmissionHandler(
            game_state_repo=self._game_state_repo,
            character_service=self._character_service,
            dice_service=self._dice_service,
            combat_service=self._combat_service,
            chat_service=self._chat_service,
            ai_response_processor=self._ai_response_processor,
            campaign_service=campaign_service,
            rag_service=rag_service,
        )

    def handle_dice_submission(
        self, roll_data: List[DiceRollSubmissionModel]
    ) -> GameEventResponseModel:
        """Process dice roll submissions for combat.

        Args:
            roll_data: List of dice roll submissions

        Returns:
            Game event response with updated state
        """
        logger.info(f"Processing {len(roll_data)} dice roll submissions")
        if not self.dice_submission_handler:
            raise RuntimeError("Dice submission handler not initialized")

        return self.dice_submission_handler.handle(roll_data)

    def handle_completed_roll_submission(
        self, roll_results: List[DiceRollResultResponseModel]
    ) -> GameEventResponseModel:
        """Handle submission of already-completed roll results.

        Args:
            roll_results: List of completed dice roll results

        Returns:
            Game event response with updated state
        """
        logger.info(f"Processing {len(roll_results)} completed roll results")
        if not self.dice_submission_handler:
            raise RuntimeError("Dice submission handler not initialized")

        return self.dice_submission_handler.handle_completed_rolls(roll_results)
