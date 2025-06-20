"""
Handler for player action events.
"""

import logging

from app.core.handler_interfaces import IPlayerActionHandler
from app.domain.combat.combat_utilities import CombatValidator
from app.models.events import GameEventResponseModel, PlayerActionEventModel
from app.utils.validation.action_validators import PlayerActionValidator

from .base_handler import BaseEventHandler

logger = logging.getLogger(__name__)


class PlayerActionHandler(BaseEventHandler, IPlayerActionHandler):
    """Handles player action events."""

    def handle(self, action_data: PlayerActionEventModel) -> GameEventResponseModel:
        """Handle a player action and return response data."""
        logger.info("Handling player action...")

        # Get AI service
        try:
            ai_service = self._get_ai_service()
        except RuntimeError as e:
            return self._create_error_response(str(e))

        # Check if AI is busy using shared state manager
        if self._shared_state_manager and self._shared_state_manager.is_ai_processing():
            logger.warning("AI is busy. Player action rejected.")
            return self._create_error_response("AI is busy", status_code=429)

        # Set AI processing flag
        if self._shared_state_manager:
            self._shared_state_manager.set_ai_processing(True)

        # Validate action - convert model to dict for validator
        validation_result = PlayerActionValidator.validate_action(
            action_data.model_dump()
        )
        if not validation_result.is_valid:
            if validation_result.is_empty_text:
                self.chat_service.add_message(
                    "system",
                    "Please type something before sending.",
                    is_dice_result=True,
                )
            return self._create_error_response(
                validation_result.error_message, status_code=400
            )

        try:
            # Extract raw player action for RAG system
            raw_player_action = (
                action_data.value if action_data.action_type == "free_text" else None
            )

            # Clear stored RAG context since this is a new player action
            if raw_player_action and self.rag_service:
                from app.content.rag.rag_context_builder import rag_context_builder

                game_state = self.game_state_repo.get_game_state()
                rag_context_builder.clear_stored_rag_context(game_state)

            # Prepare and add player message
            player_message = self._prepare_player_message(action_data)
            if not player_message:
                return self._create_error_response(
                    "Invalid player turn", status_code=400
                )

            self.chat_service.add_message("user", player_message, is_dice_result=False)

            # Process AI step using shared base functionality, passing raw action for RAG
            _, _, status, needs_backend_trigger = self._call_ai_and_process_step(
                ai_service, player_action_for_rag_query=raw_player_action
            )

            response = self._create_frontend_response(
                needs_backend_trigger, status_code=status
            )

            # Animation steps removed - events via SSE now handle real-time updates

            return response

        except Exception as e:
            logger.error(
                f"Unhandled exception in handle_player_action: {e}", exc_info=True
            )
            # Clear the processing flag
            if self._shared_state_manager:
                self._shared_state_manager.set_ai_processing(False)
            self.chat_service.add_message(
                "system",
                "(Internal Server Error processing action.)",
                is_dice_result=True,
            )
            return self._create_error_response("Internal server error", status_code=500)

    def _prepare_player_message(self, action_data: PlayerActionEventModel) -> str:
        """Prepare player message for chat history."""
        action_type = action_data.action_type
        action_value = action_data.value

        # Check if it's player's turn
        current_combatant_name = "Player"
        is_player_turn = False

        if CombatValidator.is_combat_active(self.game_state_repo):
            current_combatant_id = CombatValidator.get_current_combatant_id(
                self.game_state_repo
            )
            if current_combatant_id:
                game_state = self.game_state_repo.get_game_state()
                current_combatant = next(
                    (
                        c
                        for c in game_state.combat.combatants
                        if c.id == current_combatant_id
                    ),
                    None,
                )
                if current_combatant:
                    if current_combatant.is_player:
                        is_player_turn = True
                        current_combatant_name = current_combatant.name
                    else:
                        logger.warning(
                            f"Player action received but it's NPC turn ({current_combatant.name}). Ignoring."
                        )
                        self.chat_service.add_message(
                            "system", "(It's not your turn!)", is_dice_result=True
                        )
                        return ""

        # Format message
        if action_type == "free_text":
            player_message_content = f'"{action_value}"'
        else:
            logger.warning(
                f"Unknown action type '{action_type}' in _prepare_player_message. Value: {action_value}"
            )
            player_message_content = f"(Performed unknown action: {action_type})"

        prefix = f"{current_combatant_name}: " if is_player_turn else ""
        return f"{prefix}{player_message_content}"
