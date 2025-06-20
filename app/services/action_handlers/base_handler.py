"""
Base handler for game events with enhanced RAG integration.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from app.core.ai_interfaces import IAIResponseProcessor, IRAGService
from app.core.domain_interfaces import (
    ICampaignService,
    ICharacterService,
    IChatService,
    ICombatService,
    IDiceRollingService,
)
from app.core.repository_interfaces import (
    ICharacterTemplateRepository,
    IGameStateRepository,
)
from app.core.system_interfaces import IEventQueue
from app.domain.combat.combat_utilities import CombatFormatter, CombatValidator
from app.models.character import CharacterInstanceModel, CombinedCharacterModel
from app.models.common import MessageDict
from app.models.dice import DiceRequestModel
from app.models.events import (
    BackendProcessingEvent,
    ErrorContextModel,
    GameErrorEvent,
    GameEventResponseModel,
    PlayerDiceRequestsClearedEvent,
)
from app.providers.ai.base import BaseAIService
from app.providers.ai.prompt_builder import build_ai_prompt_context
from app.providers.ai.schemas import AIResponse
from app.services.chat_service import ChatFormatter
from app.services.shared_state_manager import SharedStateManager
from app.settings import get_settings
from app.utils.event_helpers import emit_with_logging

logger = logging.getLogger(__name__)


# Maximum depth for automatic AI continuation to prevent infinite loops
# This needs to be high enough to handle complex combat sequences:
# - Simple attack: 2-3 calls (attack roll, damage roll, apply damage)
# - Complex turn: 6-8 calls (movement, multiple attacks, special abilities, reactions)
# - Multi-reaction chain: 10-15 calls (opportunity attacks, counterspells, etc.)
settings = get_settings()
MAX_AI_CONTINUATION_DEPTH = settings.ai.max_continuation_depth


class BaseEventHandler(ABC):
    """Base class for all game event handlers with enhanced RAG integration."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        character_service: ICharacterService,
        dice_service: IDiceRollingService,
        combat_service: ICombatService,
        chat_service: IChatService,
        ai_response_processor: IAIResponseProcessor,
        campaign_service: ICampaignService,
        event_queue: IEventQueue,
        rag_service: Optional[IRAGService] = None,
    ):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor
        self.campaign_service = campaign_service
        self.event_queue = event_queue
        self.rag_service = rag_service

        # Will be set by GameOrchestrator
        self._shared_state_manager: Optional["SharedStateManager"] = None

        # Correlation ID for related events in the same action sequence
        self._current_correlation_id: Optional[str] = None

    @abstractmethod
    def handle(self, *args: Any, **kwargs: Any) -> GameEventResponseModel:
        """Handle the specific event type."""
        pass

    def get_character_template_repository(self) -> ICharacterTemplateRepository:
        """Get the character template repository from campaign service."""
        return self.campaign_service.get_character_template_repository()

    def _get_ai_service(self) -> BaseAIService:
        """Get the AI service from container."""
        from app.core.container import get_container

        container = get_container()
        ai_service = container.get_ai_service()

        if not ai_service:
            error_msg = "AI Service is not configured or failed to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return ai_service

    def _create_error_response(
        self,
        error_message: str,
        status_code: int = 500,
        preserve_backend_trigger: bool = False,
    ) -> GameEventResponseModel:
        """Create error response data."""
        response_data = self._get_state_for_frontend()
        response_data.error = error_message

        # For busy errors (429), preserve the backend trigger state that was already set by _get_state_for_frontend()
        # Otherwise, clear it
        if not preserve_backend_trigger:
            response_data.needs_backend_trigger = False

        response_data.status_code = status_code
        response_data.dice_requests = []  # Ensure no pending requests on error

        # Add retry availability flag
        response_data.can_retry_last_request = self._can_retry_last_request()

        return response_data

    def _create_frontend_response(
        self,
        needs_backend_trigger: bool = False,
        status_code: int = 200,
    ) -> GameEventResponseModel:
        """Create frontend response data."""
        response_data = self._get_state_for_frontend()
        response_data.needs_backend_trigger = needs_backend_trigger
        response_data.status_code = status_code

        # Update shared state with backend trigger status
        if self._shared_state_manager:
            self._shared_state_manager.set_needs_backend_trigger(needs_backend_trigger)

        # Add retry availability flag
        response_data.can_retry_last_request = self._can_retry_last_request()

        return response_data

    def _get_state_for_frontend(self) -> GameEventResponseModel:
        """Get current game state formatted for frontend."""
        game_state = self.game_state_repo.get_game_state()

        # Use dice requests directly (no conversion needed)
        dice_requests = game_state.pending_player_dice_requests

        needs_backend_trigger = (
            self._shared_state_manager.get_needs_backend_trigger()
            if self._shared_state_manager
            else False
        )

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
            needs_backend_trigger=needs_backend_trigger,
        )

    def _format_party_for_frontend(
        self, party_instances: Dict[str, CharacterInstanceModel]
    ) -> List[CombinedCharacterModel]:
        """Format party data for frontend."""
        # Use the character service from handler initialization
        char_data_list: List[CombinedCharacterModel] = []
        character_service = self.character_service

        for char_id, _ in party_instances.items():
            # Get full character data including template
            char_data = character_service.get_character(char_id)
            if char_data:
                template = char_data.template
                instance = char_data.instance

                # Use the factory method to create CombinedCharacterModel
                combined_model = CombinedCharacterModel.from_template_and_instance(
                    template=template, instance=instance, character_id=char_id
                )
                char_data_list.append(combined_model)

        return char_data_list

    def _call_ai_and_process_step(
        self,
        ai_service: BaseAIService,
        initial_instruction: Optional[str] = None,
        use_stored_context: bool = False,
        messages_override: Optional[List[MessageDict]] = None,
        player_action_for_rag_query: Optional[str] = None,
        continuation_depth: int = 0,
    ) -> Tuple[Optional[AIResponse], List[DiceRequestModel], int, bool]:
        """Call AI and process the response."""
        logger.info(
            f"Starting AI cycle (instruction: {initial_instruction or 'none'}, depth: {continuation_depth})"
        )

        # For continuation calls, we're already in the processing state
        if continuation_depth == 0:
            # Check shared state manager - processing flag should already be set by handler
            if self._shared_state_manager:
                if self._shared_state_manager.is_ai_processing():
                    logger.debug("AI processing flag already set by handler")
                else:
                    logger.warning(
                        "AI processing flag not set - this should not happen"
                    )
            else:
                logger.warning("SharedStateManager not available")

            # Generate a new correlation ID for this action sequence
            self._current_correlation_id = str(uuid4())
            logger.debug(
                f"Generated correlation ID for action sequence: {self._current_correlation_id}"
            )

            # Emit BackendProcessingEvent(is_processing=True) at start
            event = BackendProcessingEvent(
                is_processing=True, correlation_id=self._current_correlation_id
            )
            emit_with_logging(self.event_queue, event, "is_processing=True")
        ai_response_obj: Optional[AIResponse] = None
        pending_player_requests: List[DiceRequestModel] = []
        status_code = 500
        needs_backend_trigger_for_next_distinct_step = False

        try:
            # Build AI prompt and get response
            if use_stored_context and messages_override:
                messages = messages_override
                logger.info("Using stored context for AI request retry")
            else:
                messages = self._build_ai_prompt_context(
                    initial_instruction, player_action_for_rag_query
                )
                # Store the context for potential retry (only if not already using stored context)
                if self._shared_state_manager:
                    self._shared_state_manager.store_ai_request_context(
                        messages, initial_instruction
                    )

            logger.info("Sending request to AI service")
            ai_response_obj = ai_service.get_response(messages)

            if ai_response_obj is None:
                logger.error("AI service returned None.")
                error_msg = "(Error: The AI service appears to be rate limiting requests. This typically happens when too many requests are sent in a short time. Please wait 30-60 seconds before clicking 'Retry Last Request' to allow the rate limit to reset.)"
                self.chat_service.add_message("system", error_msg, is_dice_result=True)
                status_code = 500
                # Ensure needs_backend_trigger is False on error to prevent rapid retries
                needs_backend_trigger_for_next_distinct_step = False
            else:
                logger.info("Successfully received AIResponse.")
                # Keep stored context available for retry - don't clear on success

                # Process AI response
                pending_player_requests, npc_action_requires_ai_follow_up = (
                    self.ai_response_processor.process_response(
                        ai_response_obj, self._current_correlation_id
                    )
                )
                status_code = 200

                # Events are now emitted directly, no need to collect steps

                # Determine if backend trigger is needed
                needs_backend_trigger_for_next_distinct_step = (
                    self._determine_backend_trigger_needed(
                        npc_action_requires_ai_follow_up, pending_player_requests
                    )
                )

        except Exception as e:
            logger.error(f"Exception during AI step processing: {e}", exc_info=True)
            error_msg = f"(Error processing AI step: {e}. You can try clicking 'Retry Last Request' if this was due to a parsing error.)"
            self.chat_service.add_message("system", error_msg, is_dice_result=True)

            # Emit GameErrorEvent
            # Build ErrorContext with proper fields
            error_context = ErrorContextModel(event_type="ai_processing")
            if initial_instruction:
                error_context.ai_response = initial_instruction[
                    :200
                ]  # First 200 chars of instruction

            error_event = GameErrorEvent(
                error_message=str(e),
                error_type="ai_service_error",
                severity="error",
                recoverable=True,
                context=error_context,
            )
            emit_with_logging(
                self.event_queue, error_event, f"for AI processing error: {e}"
            )

            status_code = 500
            ai_response_obj = None
            pending_player_requests = []
            needs_backend_trigger_for_next_distinct_step = False
        finally:
            # Only clear the processing flag and emit event on the outermost call
            if continuation_depth == 0:
                if self._shared_state_manager:
                    self._shared_state_manager.set_ai_processing(False)

                # Emit BackendProcessingEvent(is_processing=False) at end
                event = BackendProcessingEvent(
                    is_processing=False,
                    needs_backend_trigger=needs_backend_trigger_for_next_distinct_step,
                    correlation_id=self._current_correlation_id,
                )
                emit_with_logging(
                    self.event_queue,
                    event,
                    f"is_processing=False, needs_backend_trigger={needs_backend_trigger_for_next_distinct_step}",
                )

                # Clear correlation ID after the action sequence is complete
                self._current_correlation_id = None
            logger.info(
                f"AI cycle complete (status: {status_code}, depth: {continuation_depth})"
            )

        # If we need a backend trigger and there are no pending player requests,
        # automatically continue the AI flow (with depth limit to prevent infinite loops)
        if (
            needs_backend_trigger_for_next_distinct_step
            and not pending_player_requests
            and status_code == 200
        ):
            if continuation_depth < MAX_AI_CONTINUATION_DEPTH:
                logger.info(
                    f"Backend trigger needed and no player requests pending. Auto-continuing AI flow (depth: {continuation_depth + 1})..."
                )

                # Check if we need to add NPC turn instruction for the continuation
                continuation_instruction = self._get_continuation_instruction()
                if continuation_instruction:
                    self.chat_service.add_message(
                        "user", continuation_instruction, is_dice_result=False
                    )

                # Recursively call to continue the flow
                return self._call_ai_and_process_step(
                    ai_service, continuation_depth=continuation_depth + 1
                )
            else:
                # Hit depth limit - force end the current turn to prevent getting stuck
                logger.warning(
                    f"AI continuation depth limit reached ({MAX_AI_CONTINUATION_DEPTH}). Forcing turn end to prevent infinite loop."
                )

                # Add error message to chat
                error_msg = f"(System: AI processing depth limit reached. Forcibly ending {self._get_current_turn_character_name()}'s turn to prevent infinite loop. If this was unexpected, you may retry or continue manually.)"
                self.chat_service.add_message("system", error_msg, is_dice_result=True)

                # Force end the current turn if in combat
                if CombatValidator.is_combat_active(self.game_state_repo):
                    self.combat_service.advance_turn()
                    # No need to manually save - advance_turn should handle state updates
                    logger.info("Forced turn advancement due to depth limit")

                # Clear the backend trigger flag
                needs_backend_trigger_for_next_distinct_step = False

        return (
            ai_response_obj,
            pending_player_requests,
            status_code,
            needs_backend_trigger_for_next_distinct_step,
        )

    def _build_ai_prompt_context(
        self,
        initial_instruction: Optional[str] = None,
        player_action_for_rag_query: Optional[str] = None,
    ) -> List[MessageDict]:
        """
        Build AI prompt context using the prompt building function.

        Args:
            initial_instruction: System-generated instruction to guide AI for the current step
            player_action_for_rag_query: Raw player action text used solely for RAG query generation
        """
        game_state = self.game_state_repo.get_game_state()

        # Call the prompt building function
        # Pass player_action_for_rag_query for RAG context generation
        # Pass initial_instruction as the system instruction for this step
        messages = build_ai_prompt_context(
            game_state, self, player_action_for_rag_query, initial_instruction
        )

        return messages

    def _determine_backend_trigger_needed(
        self,
        npc_action_requires_ai_follow_up: bool,
        pending_player_requests: List[DiceRequestModel],
    ) -> bool:
        """Determine if a backend trigger is needed for the next step."""
        if npc_action_requires_ai_follow_up:
            logger.info(
                "NPC actions processed, and an AI follow-up for their outcome is needed. Setting backend trigger."
            )
            return True
        elif not pending_player_requests:
            # Check if the new current turn is an NPC
            game_state = self.game_state_repo.get_game_state()
            if CombatValidator.is_combat_active(self.game_state_repo):
                current_combatant_id = CombatValidator.get_current_combatant_id(
                    self.game_state_repo
                )
                if current_combatant_id:
                    current_combatant = next(
                        (
                            c
                            for c in game_state.combat.combatants
                            if c.id == current_combatant_id
                        ),
                        None,
                    )
                    if current_combatant and not current_combatant.is_player:
                        logger.info(
                            f"Current AI step/turn segment complete. Next distinct turn is for NPC: {current_combatant.name}. Setting backend trigger."
                        )
                        return True
        return False

    def _get_continuation_instruction(self) -> Optional[str]:
        """Check if we need to add an instruction for continuation (e.g., NPC turn)."""
        # Import here to avoid circular imports
        from app.services.action_handlers.next_step_handler import NextStepHandler

        # Create a temporary NextStepHandler instance to use its logic
        temp_handler = NextStepHandler(
            self.game_state_repo,
            self.character_service,
            self.dice_service,
            self.combat_service,
            self.chat_service,
            self.ai_response_processor,
            self.campaign_service,
            self.event_queue,
            self.rag_service,
        )
        temp_handler._shared_state_manager = self._shared_state_manager

        # Use its NPC turn detection logic
        return temp_handler._get_npc_turn_instruction()

    def _can_retry_last_request(self) -> bool:
        """Check if last AI request can be retried."""
        if not self._shared_state_manager:
            return False

        return self._shared_state_manager.can_retry_last_request(
            settings.ai.retry_context_timeout
        )

    def _clear_pending_dice_requests(
        self, submitted_request_ids: Optional[List[str]] = None
    ) -> None:
        """
        Clear pending dice requests.

        Args:
            submitted_request_ids: List of request IDs that were submitted. If None, clears all pending requests.
        """
        game_state = self.game_state_repo.get_game_state()

        if submitted_request_ids is None:
            # Legacy behavior: clear all pending requests
            cleared_ids = [
                req.request_id
                for req in game_state.pending_player_dice_requests
                if req.request_id
            ]
            game_state.pending_player_dice_requests = []
        else:
            # New behavior: only clear specific submitted requests
            cleared_ids = []
            remaining_requests = []

            for req in game_state.pending_player_dice_requests:
                req_id = req.request_id
                if req_id and req_id in submitted_request_ids:
                    cleared_ids.append(req_id)
                else:
                    remaining_requests.append(req)

            game_state.pending_player_dice_requests = remaining_requests

        # Emit PlayerDiceRequestsClearedEvent if any were cleared
        if cleared_ids:
            # Get event queue if available
            event = PlayerDiceRequestsClearedEvent(
                cleared_request_ids=cleared_ids,
                correlation_id=self._current_correlation_id,
            )
            emit_with_logging(
                self.event_queue, event, f"for {len(cleared_ids)} requests"
            )

    def _get_current_turn_character_name(self) -> str:
        """Get the name of the character whose turn it currently is."""
        if CombatValidator.is_combat_active(self.game_state_repo):
            current_combatant_id = CombatValidator.get_current_combatant_id(
                self.game_state_repo
            )
            if current_combatant_id:
                return self.character_service.get_character_name(current_combatant_id)

        return "the current character"
