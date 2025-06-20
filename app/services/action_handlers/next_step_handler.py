"""
Handler for next step events.
"""

import logging
from typing import Optional

from app.core.handler_interfaces import INextStepHandler
from app.models.events import GameEventResponseModel

from .base_handler import BaseEventHandler

logger = logging.getLogger(__name__)


class NextStepHandler(BaseEventHandler, INextStepHandler):
    """Handles next step events."""

    def _get_npc_turn_instruction(self) -> Optional[str]:
        """Check if it's an NPC's turn and return appropriate instruction."""
        from app.domain.combat.combat_utilities import CombatValidator

        game_state = self.game_state_repo.get_game_state()

        # Check if combat is active
        if not CombatValidator.is_combat_active(self.game_state_repo):
            return None

        # Get current combatant
        current_combatant_id = CombatValidator.get_current_combatant_id(
            self.game_state_repo
        )
        if not current_combatant_id:
            return None

        # Find the combatant
        current_combatant = next(
            (c for c in game_state.combat.combatants if c.id == current_combatant_id),
            None,
        )

        # If it's an NPC, check if we need instruction
        if current_combatant and not current_combatant.is_player:
            # Check if instruction was already given for this turn using the flag
            if game_state.combat.current_turn_instruction_given:
                logger.info(
                    f"Turn instruction already given for {current_combatant.name} this turn"
                )
                return None

            # Mark that we're giving the instruction
            game_state.combat.current_turn_instruction_given = True
            self.game_state_repo.save_game_state(game_state)

            logger.info(f"Detected NPC turn for: {current_combatant.name}")
            return f"It's {current_combatant.name}'s turn. Narrate their action."

        return None

    def handle(self) -> GameEventResponseModel:
        """Handle triggering the next step and return response data."""
        logger.info("Handling next step trigger...")

        # Check if AI is busy
        if self._shared_state_manager and self._shared_state_manager.is_ai_processing():
            logger.warning("AI is busy. Next step rejected.")
            # Don't clear the backend trigger flag if AI is busy
            return self._create_error_response(
                "AI is busy", status_code=429, preserve_backend_trigger=True
            )

        # Set AI processing flag
        if self._shared_state_manager:
            self._shared_state_manager.set_ai_processing(True)

        # Only clear the backend trigger flag after we confirm we can process
        if self._shared_state_manager:
            self._shared_state_manager.set_needs_backend_trigger(False)

        # Get AI service
        try:
            ai_service = self._get_ai_service()
        except RuntimeError as e:
            return self._create_error_response(str(e))

        try:
            # Check if this is an NPC turn that needs narration
            npc_instruction = self._get_npc_turn_instruction()

            # Process AI step using shared base functionality
            # Pass npc_instruction as initial_instruction instead of adding to chat history
            ai_response_obj, _, status, needs_backend_trigger = (
                self._call_ai_and_process_step(
                    ai_service, initial_instruction=npc_instruction
                )
            )

            response = self._create_frontend_response(
                needs_backend_trigger, status_code=status
            )

            # Animation steps removed - events via SSE now handle real-time updates

            return response

        except Exception as e:
            logger.error(f"Unhandled exception in handle_next_step: {e}", exc_info=True)
            # Clear the processing flag
            if self._shared_state_manager:
                self._shared_state_manager.set_ai_processing(False)
            self.chat_service.add_message(
                "system",
                "(Internal Server Error processing next step.)",
                is_dice_result=True,
            )
            return self._create_error_response("Internal server error", status_code=500)
