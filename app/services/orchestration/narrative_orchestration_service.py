"""
Handles narrative and chat flow orchestration.
"""

import logging
from typing import Optional

from app.core.interfaces import (
    AIResponseProcessor,
    CharacterService,
    ChatService,
    CombatService,
    DiceRollingService,
    GameStateRepository,
    RAGService,
)
from app.domain.campaigns.campaign_service import CampaignService
from app.models.game_state import (
    GameEventResponseModel,
    PlayerActionEventModel,
)
from app.services.action_handlers.player_action_handler import PlayerActionHandler

logger = logging.getLogger(__name__)


class NarrativeOrchestrationService:
    """Handles narrative and chat flow orchestration."""

    def __init__(
        self,
        game_state_repo: GameStateRepository,
        character_service: CharacterService,
        chat_service: ChatService,
        ai_response_processor: AIResponseProcessor,
        campaign_service: CampaignService,
        rag_service: Optional[RAGService] = None,
    ):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor
        self.campaign_service = campaign_service
        self.rag_service = rag_service

        # Store dependencies for handler creation
        self._game_state_repo = game_state_repo
        self._character_service = character_service
        self._chat_service = chat_service
        self._ai_response_processor = ai_response_processor
        self._campaign_service = campaign_service
        self._rag_service = rag_service

        # Player action handler will be created after dice/combat services are injected
        self.player_action_handler: Optional[PlayerActionHandler] = None

    def initialize_handler(
        self, dice_service: DiceRollingService, combat_service: CombatService
    ) -> None:
        """Initialize the player action handler with all required services."""
        self.player_action_handler = PlayerActionHandler(
            game_state_repo=self._game_state_repo,
            character_service=self._character_service,
            dice_service=dice_service,
            combat_service=combat_service,
            chat_service=self._chat_service,
            ai_response_processor=self._ai_response_processor,
            campaign_service=self._campaign_service,
            rag_service=self._rag_service,
        )

    def handle_player_message(
        self, action_data: PlayerActionEventModel
    ) -> GameEventResponseModel:
        """Process player messages and generate AI responses.

        Args:
            action_data: Player action event data

        Returns:
            Game event response with AI-generated narrative
        """
        logger.info(f"Processing player action: {action_data.value[:50]}...")
        if not self.player_action_handler:
            raise RuntimeError("Player action handler not initialized")

        return self.player_action_handler.handle(action_data)
