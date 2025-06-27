"""
Turn advancement processor for AI response processing.
"""

import logging
from typing import Optional

from app.core.domain_interfaces import ICombatService
from app.core.repository_interfaces import IGameStateRepository
from app.core.system_interfaces import IEventQueue
from app.models.combat.state import NextCombatantInfoModel
from app.models.events.combat import TurnAdvancedEvent
from app.models.updates import CombatEndUpdateModel
from app.providers.ai.schemas import AIResponse
from app.services.ai_processors.interfaces import ITurnAdvancementProcessor
from app.utils.event_helpers import emit_with_logging

logger = logging.getLogger(__name__)


class TurnAdvancementProcessor(ITurnAdvancementProcessor):
    """Processes turn advancement from AI responses."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        combat_service: ICombatService,
        event_queue: IEventQueue,
    ):
        self.game_state_repo = game_state_repo
        self.combat_service = combat_service
        self.event_queue = event_queue

    def handle_turn_advancement(
        self,
        ai_response: AIResponse,
        needs_ai_rerun: bool,
        player_requests_pending: bool,
        next_combatant_info: Optional[NextCombatantInfoModel] = None,
    ) -> None:
        """Handle turn advancement based on AI signal and current state."""
        game_state = self.game_state_repo.get_game_state()
        ai_signals_end_turn = getattr(ai_response, "end_turn", None)

        if game_state.combat.is_active and ai_signals_end_turn is True:
            if needs_ai_rerun:
                logger.warning(
                    "AI requested 'end_turn: true' but also triggered an AI rerun. Turn will advance *after* the rerun loop completes."
                )
            elif player_requests_pending:
                logger.warning(
                    "AI requested 'end_turn: true' but also requested player dice rolls. Turn will advance *after* player submits rolls."
                )
            else:
                logger.info(
                    "AI signaled end_turn=true and conditions met. Advancing turn."
                )

                # Use pre-calculated next combatant info if available
                if next_combatant_info:
                    self._advance_with_pre_calculated_info(
                        next_combatant_info, ai_response
                    )
                else:
                    # Normal turn advancement
                    self.combat_service.advance_turn()
        elif game_state.combat.is_active:
            if ai_signals_end_turn is False:
                logger.debug("AI explicitly set end_turn=false, turn not advancing.")
            elif ai_signals_end_turn is None:
                logger.debug(
                    "AI omitted end_turn field during combat, turn not advancing."
                )

    def _advance_with_pre_calculated_info(
        self, next_combatant_info: NextCombatantInfoModel, ai_response: AIResponse
    ) -> None:
        """Advance turn using pre-calculated combatant information."""
        game_state = self.game_state_repo.get_game_state()

        if next_combatant_info.should_end_combat:
            logger.info(
                "Pre-calculated info indicates combat should end (no remaining combatants)"
            )
            from app.services import state_updaters

            end_update = CombatEndUpdateModel(reason="All combatants removed")
            state_updaters.CombatStateUpdater.end_combat(
                game_state, end_update, self.event_queue, None, None
            )
            return

        # Set the current turn index to the pre-calculated position
        target_combatant_id = next_combatant_info.combatant_id
        new_index = next_combatant_info.new_index

        if target_combatant_id and new_index is not None:
            # Verify the combatant still exists at the expected position
            if (
                0 <= new_index < len(game_state.combat.combatants)
                and game_state.combat.combatants[new_index].id == target_combatant_id
            ):
                game_state.combat.current_turn_index = new_index
                current_combatant = game_state.combat.combatants[new_index]
                # Reset the turn instruction flag for the new turn
                game_state.combat.current_turn_instruction_given = False
                logger.info(
                    f"Turn advanced using pre-calculated info to: {current_combatant.name} (ID: {current_combatant.id})"
                )

                # Check if new round started (this happens when we wrap around to index 0 from a higher index)
                is_new_round = False
                if new_index == 0 and len(game_state.combat.combatants) > 1:
                    # Only increment round if we didn't start at index 0 initially
                    # Check if there were any combatant removals in the current response
                    previous_combatants_existed = bool(ai_response.combatant_removals)
                    if previous_combatants_existed:
                        game_state.combat.round_number += 1
                        is_new_round = True
                        logger.info(
                            f"Advanced to Combat Round {game_state.combat.round_number}"
                        )

                # Emit TurnAdvancedEvent using centralized helper
                turn_event = TurnAdvancedEvent(
                    new_combatant_id=current_combatant.id,
                    new_combatant_name=current_combatant.name,
                    round_number=game_state.combat.round_number,
                    is_new_round=is_new_round,
                    is_player_controlled=current_combatant.is_player,
                )
                # Use injected event queue
                emit_with_logging(
                    self.event_queue,
                    turn_event,
                    f"Turn advanced to {current_combatant.name}",
                )

                # Save the updated game state
                self.game_state_repo.save_game_state(game_state)

            else:
                logger.warning(
                    f"Pre-calculated combatant position mismatch. Expected {target_combatant_id} at index {new_index}, falling back to normal advancement"
                )
                self.combat_service.advance_turn()
        else:
            logger.warning(
                "Invalid pre-calculated turn info, falling back to normal advancement"
            )
            self.combat_service.advance_turn()
