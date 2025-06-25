"""
Main AI response processor implementation.
"""

import logging
from typing import List, Optional, Tuple

from app.core.ai_interfaces import IAIResponseProcessor, IRAGService
from app.core.domain_interfaces import (
    ICharacterService,
    IChatService,
    ICombatService,
    IDiceRollingService,
)
from app.core.repository_interfaces import IGameStateRepository
from app.core.system_interfaces import IEventQueue
from app.models.combat.state import NextCombatantInfoModel
from app.models.dice import DiceRequestModel
from app.providers.ai.schemas import AIResponse
from app.services.ai_response_processors.interfaces import (
    IDiceRequestHandler,
    INarrativeProcessor,
    IRagProcessor,
    IStateUpdateProcessor,
)
from app.services.ai_response_processors.turn_advancement_handler import (
    TurnAdvancementHandler,
)

logger = logging.getLogger(__name__)


class AIResponseProcessor(IAIResponseProcessor):
    """Implementation of AI response processor as a thin coordinator."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        character_service: ICharacterService,
        dice_service: IDiceRollingService,
        combat_service: ICombatService,
        chat_service: IChatService,
        narrative_processor: INarrativeProcessor,
        state_update_processor: IStateUpdateProcessor,
        rag_processor: IRagProcessor,
        event_queue: IEventQueue,
        rag_service: Optional[IRAGService] = None,
    ):
        self.game_state_repo = game_state_repo
        self._character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.rag_service = rag_service
        self._event_queue = event_queue

        # Accept processors via dependency injection
        self._narrative_processor = narrative_processor
        self._state_update_processor = state_update_processor
        self._rag_processor = rag_processor

    @property
    def character_service(self) -> ICharacterService:
        """Get the character service."""
        return self._character_service

    @property
    def event_queue(self) -> IEventQueue:
        """Get the event queue."""
        return self._event_queue

    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Delegate to character service for compatibility with state processors."""
        return self.character_service.find_character_by_name_or_id(identifier)

    def process_response(
        self, ai_response: AIResponse, correlation_id: Optional[str] = None
    ) -> Tuple[List[DiceRequestModel], bool]:
        """Process an AI response and return pending requests and rerun flag."""
        logger.debug("Processing AIResponse object via IAIResponseProcessor...")

        # Pre-calculate next combatant BEFORE any game state changes
        next_combatant_info = self._pre_calculate_next_combatant(ai_response)

        # Handle narrative and location updates
        self._narrative_processor.process_narrative_and_location(
            ai_response, correlation_id
        )

        # Apply game state updates (pass correlation ID and resolver function)
        combat_started = self._state_update_processor.process_game_state_updates(
            ai_response, correlation_id, self.find_combatant_id_by_name_or_id
        )

        # Check and reset combat just started flag
        combat_just_started_flag = combat_started or self._check_and_reset_combat_flag()

        # Handle dice requests (NPC rolls happen here)
        dice_handler = self._create_dice_handler(correlation_id)
        pending_player_reqs, npc_rolls_performed, needs_rerun_after_npc_rolls = (
            dice_handler.process_dice_requests(ai_response, combat_just_started_flag)
        )

        # Check if current turn should continue after player dice resolution
        needs_turn_continuation = self._should_continue_current_turn(
            ai_response, pending_player_reqs
        )

        # Combine rerun conditions
        needs_ai_rerun = needs_rerun_after_npc_rolls or needs_turn_continuation

        # Handle turn advancement using pre-calculated info
        self._handle_turn_advancement(
            ai_response, needs_ai_rerun, bool(pending_player_reqs), next_combatant_info
        )

        # Update pending player requests in game state
        self._update_pending_requests(pending_player_reqs, needs_ai_rerun)

        # RAG Event Log Update Trigger
        self._rag_processor.process_rag_event_logging(ai_response)

        return pending_player_reqs, needs_ai_rerun

    def _pre_calculate_next_combatant(
        self, ai_response: AIResponse
    ) -> Optional[NextCombatantInfoModel]:
        """Pre-calculate who should be next before any combatant removals."""
        game_state = self.game_state_repo.get_game_state()

        # Only pre-calculate if combat is active and AI wants to end turn
        if not (
            game_state.combat.is_active
            and getattr(ai_response, "end_turn", None) is True
        ):
            return None

        # Check if any combatant removals are planned
        removal_updates = ai_response.combatant_removals

        if not removal_updates:
            return None  # No removals planned, normal advancement will work

        # Calculate who should be next after removal
        current_combatants = game_state.combat.combatants.copy()
        current_index = game_state.combat.current_turn_index

        if not (0 <= current_index < len(current_combatants)):
            logger.warning(
                f"Invalid current_turn_index {current_index}, cannot pre-calculate next combatant"
            )
            return None

        # Find which combatants will be removed
        removal_ids = set()
        for update in removal_updates:
            # Only process combatant_remove updates
            if not hasattr(update, "character_id"):
                continue
            removal_id = self.character_service.find_character_by_name_or_id(
                update.character_id
            )
            if removal_id:
                removal_ids.add(removal_id)

        # Simulate the removal to find the correct next combatant
        remaining_combatants = [
            c for c in current_combatants if c.id not in removal_ids
        ]

        if not remaining_combatants:
            logger.info("All combatants will be removed, combat should end")
            return NextCombatantInfoModel(
                combatant_id="",
                combatant_name="",
                is_player=False,
                should_end_combat=True,
                new_index=0,
                round_number=1,
                is_new_round=False,
            )

        # Find next valid combatant after current position
        next_index = current_index
        for _ in range(len(current_combatants)):
            next_index = (next_index + 1) % len(current_combatants)
            next_combatant = current_combatants[next_index]

            # Skip if this combatant will be removed
            if next_combatant.id in removal_ids:
                continue

            # Find the new index for this combatant in the remaining list
            try:
                new_index = next(
                    i
                    for i, c in enumerate(remaining_combatants)
                    if c.id == next_combatant.id
                )
                logger.debug(
                    f"Pre-calculated next combatant: {next_combatant.name} (ID: {next_combatant.id}) at new index {new_index}"
                )
                return NextCombatantInfoModel(
                    combatant_id=next_combatant.id,
                    combatant_name=next_combatant.name,
                    is_player=next_combatant.is_player,
                    should_end_combat=False,
                    new_index=new_index,
                    round_number=game_state.combat.round_number,
                    is_new_round=False,
                )
            except StopIteration:
                continue  # This shouldn't happen but just in case

        # If we get here, couldn't find a valid next combatant
        logger.warning("Could not determine valid next combatant after removals")
        return None

    def _check_and_reset_combat_flag(self) -> bool:
        """Check and reset the combat just started flag."""
        game_state = self.game_state_repo.get_game_state()
        combat_just_started_flag = getattr(
            game_state.combat, "_combat_just_started_flag", False
        )

        if combat_just_started_flag:
            game_state.combat._combat_just_started_flag = False

        return combat_just_started_flag

    def _create_dice_handler(
        self, correlation_id: Optional[str] = None
    ) -> IDiceRequestHandler:
        """Create dice request handler with current context."""
        # Import here to avoid circular dependencies
        from app.services.ai_response_processors.dice_request_handler import (
            DiceRequestHandler,
        )

        return DiceRequestHandler(
            self.game_state_repo,
            self.character_service,
            self.dice_service,
            self.chat_service,
            self.event_queue,
            correlation_id=correlation_id,
        )

    def _should_continue_current_turn(
        self, ai_response: AIResponse, pending_player_reqs: List[DiceRequestModel]
    ) -> bool:
        """Check if the current combatant's turn should auto-continue after player dice resolution.
        Enhancement for multi-step actions like Ice Knife spells where:
        1. AI requests saving throw (end_turn: false)
        2. Player submits dice -> should auto-continue to process results
        3. AI processes save, requests damage (end_turn: false)
        4. Player submits damage -> should auto-continue to apply damage
        5. AI applies damage and describes outcome (end_turn: true)
        """
        game_state = self.game_state_repo.get_game_state()

        # Only during active combat to prevent endless loops
        if not game_state.combat.is_active:
            logger.debug("Turn continuation: Not in combat, no continuation needed")
            return False

        # Only if AI explicitly said the turn isn't over
        ai_end_turn = getattr(ai_response, "end_turn", None)
        if ai_end_turn is not False:
            logger.debug(
                f"Turn continuation: AI end_turn={ai_end_turn}, no continuation needed"
            )
            return False

        # Only if no player requests are pending (they've been resolved)
        if pending_player_reqs:
            logger.debug(
                "Turn continuation: Player requests still pending, no continuation needed"
            )
            return False

        # CRITICAL: Only continue if there are pending roll results to process
        # This prevents auto-continuation when AI is just asking "What do you do?"
        pending_npc_results = getattr(game_state, "_pending_npc_roll_results", [])
        if not pending_npc_results:
            logger.debug(
                "Turn continuation: No pending NPC roll results to process, no continuation needed"
            )
            return False

        # Safety: Ensure we have a valid current combatant
        from app.domain.combat.combat_utilities import CombatValidator

        current_combatant_id = CombatValidator.get_current_combatant_id(
            self.game_state_repo
        )
        if not current_combatant_id:
            logger.warning(
                "Turn continuation: No valid current combatant, no continuation"
            )
            return False

        # All conditions met - current turn should continue to process dice results
        logger.info(
            f"Turn continuation: AI set end_turn=false, no pending player requests, {len(pending_npc_results)} NPC results to process. Auto-continuing turn for combatant {current_combatant_id}"
        )
        return True

    def _handle_turn_advancement(
        self,
        ai_response: AIResponse,
        needs_ai_rerun: bool,
        player_requests_pending: bool,
        next_combatant_info: Optional[NextCombatantInfoModel] = None,
    ) -> None:
        """Handle turn advancement based on AI signal."""
        turn_handler = TurnAdvancementHandler(
            self.game_state_repo, self.combat_service, self.event_queue
        )
        turn_handler.handle_turn_advancement(
            ai_response, needs_ai_rerun, player_requests_pending, next_combatant_info
        )

    def _update_pending_requests(
        self, pending_player_reqs: List[DiceRequestModel], needs_ai_rerun: bool
    ) -> None:
        """Update pending player requests in game state."""
        game_state = self.game_state_repo.get_game_state()

        if pending_player_reqs:
            # Add new requests from AI response to existing pending requests
            game_state.pending_player_dice_requests.extend(pending_player_reqs)
            logger.info(
                f"{len(pending_player_reqs)} new player dice requests added. Total pending: {len(game_state.pending_player_dice_requests)}."
            )
        # Note: No longer clearing all pending requests automatically.
        # Requests should only be cleared by specific handlers when they process them.
