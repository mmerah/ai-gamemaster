"""
Base handler for game events with enhanced RAG integration.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from app.core.interfaces import (
    GameStateRepository, CharacterService, DiceRollingService, 
    CombatService, ChatService, AIResponseProcessor
)
from app.core.rag_interfaces import RAGService
from app.services.campaign_service import CampaignService
from app.ai_services.schemas import AIResponse

logger = logging.getLogger(__name__)

# Maximum depth for automatic AI continuation to prevent infinite loops
# This needs to be high enough to handle complex combat sequences:
# - Simple attack: 2-3 calls (attack roll, damage roll, apply damage)
# - Complex turn: 6-8 calls (movement, multiple attacks, special abilities, reactions)
# - Multi-reaction chain: 10-15 calls (opportunity attacks, counterspells, etc.)
MAX_AI_CONTINUATION_DEPTH = 20


class BaseEventHandler(ABC):
    """Base class for all game event handlers with enhanced RAG integration."""
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService,
                 dice_service: DiceRollingService, combat_service: CombatService,
                 chat_service: ChatService, ai_response_processor: AIResponseProcessor,
                 campaign_service: CampaignService, rag_service: RAGService = None):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.ai_response_processor = ai_response_processor
        self.campaign_service = campaign_service
        self.rag_service = rag_service
        
        # Shared state for AI processing
        self._ai_processing = False
        self._shared_state = None  # Will be set by GameEventManager
        
        # Correlation ID for related events in the same action sequence
        self._current_correlation_id = None
        
        # Retry functionality - store last AI request context
        self._last_ai_request_context = None
        self._last_ai_request_timestamp = None
    
    @abstractmethod
    def handle(self, *args, **kwargs) -> Dict[str, Any]:
        """Handle the specific event type."""
        pass
    
    def _get_ai_service(self):
        """Get the AI service from Flask config or test environment."""
        try:
            from flask import current_app
            ai_service = current_app.config.get('AI_SERVICE')
            if not ai_service:
                logger.error("AI Service not available.")
                self.chat_service.add_message("system", "(Error: AI Service is not configured or failed to initialize.)", is_dice_result=True)
            return ai_service
        except RuntimeError:
            # We're probably in a test environment without Flask context
            # Try to get the AI service from container or return a mock
            logger.warning("No Flask context available, likely in test environment")
            return None
    
    def _create_error_response(self, error_message: str, status_code: int = 500, preserve_backend_trigger: bool = False) -> Dict[str, Any]:
        """Create error response data."""
        response_data = self._get_state_for_frontend()
        response_data["error"] = error_message
        
        # For busy errors (429), preserve the backend trigger state that was already set by _get_state_for_frontend()
        # Otherwise, clear it
        if not preserve_backend_trigger:
            response_data["needs_backend_trigger"] = False
            
        response_data["status_code"] = status_code
        response_data["dice_requests"] = []  # Ensure no pending requests on error
        
        # Add retry availability flag
        response_data["can_retry_last_request"] = self._can_retry_last_request()
        
        return response_data
    
    def _create_frontend_response(self, needs_backend_trigger: bool = False, status_code: int = 200, ai_response=None) -> Dict[str, Any]:
        """Create frontend response data."""
        response_data = self._get_state_for_frontend()
        response_data["needs_backend_trigger"] = needs_backend_trigger
        response_data["status_code"] = status_code
        
        # Update shared state with backend trigger status
        if self._shared_state:
            self._shared_state['needs_backend_trigger'] = needs_backend_trigger
        
        # Add retry availability flag
        response_data["can_retry_last_request"] = self._can_retry_last_request()
        
        # Generate narration if enabled
        if ai_response:
            narration_url = self._generate_narration_if_enabled(ai_response)
            if narration_url:
                response_data["narration_url"] = narration_url
        
        return response_data
    
    def _get_state_for_frontend(self) -> Dict[str, Any]:
        """Get current game state formatted for frontend."""
        from app.services.combat_utilities import CombatFormatter
        from app.services.chat_service import ChatFormatter
        
        game_state = self.game_state_repo.get_game_state()
        
        return {
            "party": self._format_party_for_frontend(game_state.party),
            "location": game_state.current_location.get("name", "Unknown"),
            "location_description": game_state.current_location.get("description", ""),
            "chat_history": ChatFormatter.format_for_frontend(game_state.chat_history),
            "dice_requests": [req.model_dump() if hasattr(req, 'model_dump') else req for req in game_state.pending_player_dice_requests],
            "combat_info": CombatFormatter.format_combat_status(self.game_state_repo),
            "needs_backend_trigger": self._shared_state.get('needs_backend_trigger', False) if self._shared_state else False
        }
    
    def _format_party_for_frontend(self, party_instances: Dict) -> list:
        """Format party data for frontend."""
        from app.game.calculators.dice_mechanics import get_proficiency_bonus
        
        return [
            {
                "id": pc.id,
                "name": pc.name,
                "race": pc.race,
                "char_class": pc.char_class,
                "level": pc.level,
                "hp": pc.current_hp,
                "max_hp": pc.max_hp,
                "ac": pc.armor_class,
                "conditions": pc.conditions,
                "icon": pc.icon,
                "stats": pc.base_stats.model_dump(),
                "proficiencies": pc.proficiencies.model_dump(),
                "proficiency_bonus": get_proficiency_bonus(pc.level)
            } for pc in party_instances.values()
        ]
    
    def _call_ai_and_process_step(self, ai_service, initial_instruction: Optional[str] = None, 
                                  use_stored_context: bool = False, messages_override: Optional[List[Dict]] = None,
                                  player_action_for_rag_query: Optional[str] = None, continuation_depth: int = 0) -> Tuple[Optional[AIResponse], List[Dict], int, bool]:
        """Call AI and process the response."""
        logger.info(f"Starting AI cycle (instruction: {initial_instruction or 'none'}, depth: {continuation_depth})")
        
        # Get event queue if available
        event_queue = None
        try:
            from app.core.container import get_container
            container = get_container()
            event_queue = container.get_event_queue()
        except Exception as e:
            logger.debug(f"Could not get event queue: {e}")
            # Test environment or no queue available
            pass
        
        # For continuation calls, we're already in the processing state
        if continuation_depth == 0:
            # Check shared state if available, otherwise use local state
            if self._shared_state:
                if self._shared_state['ai_processing']:
                    logger.warning("AI is already processing. Aborting.")
                    return None, [], 429, False
                self._shared_state['ai_processing'] = True
            else:
                if self._ai_processing:
                    logger.warning("AI is already processing. Aborting.")
                    return None, [], 429, False
                self._ai_processing = True
            
            # Generate a new correlation ID for this action sequence
            from uuid import uuid4
            self._current_correlation_id = str(uuid4())
            logger.debug(f"Generated correlation ID for action sequence: {self._current_correlation_id}")
            
            # Emit BackendProcessingEvent(is_processing=True) at start
            if event_queue:
                from app.events.game_update_events import BackendProcessingEvent
                event = BackendProcessingEvent(is_processing=True, correlation_id=self._current_correlation_id)
                event_queue.put_event(event)
                logger.debug("Emitted BackendProcessingEvent(is_processing=True)")
        ai_response_obj = None
        pending_player_requests = []
        status_code = 500
        needs_backend_trigger_for_next_distinct_step = False
        
        try:
            # Build AI prompt and get response
            if use_stored_context and messages_override:
                messages = messages_override
                logger.info("Using stored context for AI request retry")
            else:
                messages = self._build_ai_prompt_context(initial_instruction, player_action_for_rag_query)
                # Store the context for potential retry (only if not already using stored context)
                self._store_ai_request_context(messages, initial_instruction)
            
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
                # Clear stored context on success
                if not use_stored_context:
                    self._last_ai_request_context = None
                    self._last_ai_request_timestamp = None
                
                # Process AI response
                pending_player_requests, npc_action_requires_ai_follow_up = (
                    self.ai_response_processor.process_response(ai_response_obj, self._current_correlation_id)
                )
                status_code = 200
                
                # Events are now emitted directly, no need to collect steps
                
                # Determine if backend trigger is needed
                needs_backend_trigger_for_next_distinct_step = self._determine_backend_trigger_needed(
                    npc_action_requires_ai_follow_up, pending_player_requests
                )
                
        except Exception as e:
            logger.error(f"Exception during AI step processing: {e}", exc_info=True)
            error_msg = f"(Error processing AI step: {e}. You can try clicking 'Retry Last Request' if this was due to a parsing error.)"
            self.chat_service.add_message("system", error_msg, is_dice_result=True)
            
            # Emit GameErrorEvent
            if event_queue:
                from app.events.game_update_events import GameErrorEvent
                error_event = GameErrorEvent(
                    error_message=str(e),
                    error_type="ai_service_error",
                    severity="error",
                    recoverable=True,
                    context={
                        "phase": "ai_processing",
                        "instruction": initial_instruction,
                        "continuation_depth": continuation_depth
                    }
                )
                event_queue.put_event(error_event)
                logger.debug(f"Emitted GameErrorEvent for AI processing error: {e}")
            
            status_code = 500
            ai_response_obj = None
            pending_player_requests = []
            needs_backend_trigger_for_next_distinct_step = False
        finally:
            # Only clear the processing flag and emit event on the outermost call
            if continuation_depth == 0:
                if self._shared_state:
                    self._shared_state['ai_processing'] = False
                else:
                    self._ai_processing = False
                
                # Emit BackendProcessingEvent(is_processing=False) at end
                if event_queue:
                    from app.events.game_update_events import BackendProcessingEvent
                    event = BackendProcessingEvent(
                        is_processing=False,
                        needs_backend_trigger=needs_backend_trigger_for_next_distinct_step,
                        correlation_id=self._current_correlation_id
                    )
                    event_queue.put_event(event)
                    logger.debug(f"Emitted BackendProcessingEvent(is_processing=False, needs_backend_trigger={needs_backend_trigger_for_next_distinct_step})")
                
                # Clear correlation ID after the action sequence is complete
                self._current_correlation_id = None
            logger.info(f"AI cycle complete (status: {status_code}, depth: {continuation_depth})")
        
        # If we need a backend trigger and there are no pending player requests, 
        # automatically continue the AI flow (with depth limit to prevent infinite loops)
        if needs_backend_trigger_for_next_distinct_step and not pending_player_requests and status_code == 200:
            if continuation_depth < MAX_AI_CONTINUATION_DEPTH:
                logger.info(f"Backend trigger needed and no player requests pending. Auto-continuing AI flow (depth: {continuation_depth + 1})...")
                
                # Check if we need to add NPC turn instruction for the continuation
                continuation_instruction = self._get_continuation_instruction()
                if continuation_instruction:
                    self.chat_service.add_message("user", continuation_instruction, is_dice_result=False)
                
                # Recursively call to continue the flow
                return self._call_ai_and_process_step(ai_service, continuation_depth=continuation_depth + 1)
            else:
                # Hit depth limit - force end the current turn to prevent getting stuck
                logger.warning(f"AI continuation depth limit reached ({MAX_AI_CONTINUATION_DEPTH}). Forcing turn end to prevent infinite loop.")
                
                # Add error message to chat
                error_msg = f"(System: AI processing depth limit reached. Forcibly ending {self._get_current_turn_character_name()}'s turn to prevent infinite loop. If this was unexpected, you may retry or continue manually.)"
                self.chat_service.add_message("system", error_msg, is_dice_result=True)
                
                # Force end the current turn if in combat
                from app.services.combat_utilities import CombatValidator
                if CombatValidator.is_combat_active(self.game_state_repo):
                    game_state = self.game_state_repo.get_game_state()
                    updated_game_state = self.combat_service.advance_turn(game_state)
                    self.game_state_repo.save_game_state(updated_game_state)
                    logger.info("Forced turn advancement due to depth limit")
                
                # Clear the backend trigger flag
                needs_backend_trigger_for_next_distinct_step = False
        
        return ai_response_obj, pending_player_requests, status_code, needs_backend_trigger_for_next_distinct_step
    
    def _generate_narration_if_enabled(self, ai_response: Optional[AIResponse]) -> Optional[str]:
        """Generates narration audio if campaign settings allow and AI response is valid."""
        if not ai_response or not ai_response.narrative:
            return None

        game_state = self.game_state_repo.get_game_state()
        if not game_state.campaign_id:
            return None

        campaign = self.campaign_service.get_campaign(game_state.campaign_id)
        if not campaign or not campaign.narration_enabled or not campaign.tts_voice:
            return None
        
        try:
            from app.core.container import get_container
            container = get_container()
            tts_service = container.get_tts_service()
            if not tts_service:
                return None

            relative_audio_path = tts_service.synthesize_speech(ai_response.narrative, campaign.tts_voice)
            return f"/static/{relative_audio_path}" if relative_audio_path else None
        except Exception as e:
            logger.warning(f"Failed to generate narration: {e}")
            return None
    
    def _store_ai_request_context(self, messages: List[Dict], initial_instruction: Optional[str] = None):
        """Store AI request context for potential retry."""
        self._last_ai_request_context = {
            "messages": messages.copy(),  # Make a copy to avoid mutation issues
            "initial_instruction": initial_instruction
        }
        self._last_ai_request_timestamp = time.time()
        logger.debug("Stored AI request context for potential retry")
    
    def _build_ai_prompt_context(self, initial_instruction: Optional[str] = None, player_action_for_rag_query: Optional[str] = None):
        """
        Build AI prompt context using the prompt building function.
        
        Args:
            initial_instruction: System-generated instruction to guide AI for the current step
            player_action_for_rag_query: Raw player action text used solely for RAG query generation
        """
        game_state = self.game_state_repo.get_game_state()

        # Ensure campaign KBs are loaded for the current context
        if self.rag_service and hasattr(self.rag_service, "_ensure_campaign_kbs_loaded"):
            self.rag_service._ensure_campaign_kbs_loaded()
        
        # Use prompt builder
        from app.game.prompt_builder import build_ai_prompt_context
        logger.debug("Using prompt builder")
        
        # Call the prompt building function
        # Pass player_action_for_rag_query for RAG context generation
        # Pass initial_instruction as the system instruction for this step
        messages = build_ai_prompt_context(game_state, self, player_action_for_rag_query, initial_instruction)
        
        return messages
    
    def _determine_backend_trigger_needed(self, npc_action_requires_ai_follow_up: bool, pending_player_requests: List[Dict]) -> bool:
        """Determine if a backend trigger is needed for the next step."""
        from app.services.combat_utilities import CombatValidator
        
        if npc_action_requires_ai_follow_up:
            logger.info("NPC actions processed, and an AI follow-up for their outcome is needed. Setting backend trigger.")
            return True
        elif not pending_player_requests:
            # Check if the new current turn is an NPC
            game_state = self.game_state_repo.get_game_state()
            if CombatValidator.is_combat_active(self.game_state_repo):
                current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
                if current_combatant_id:
                    current_combatant = next(
                        (c for c in game_state.combat.combatants if c.id == current_combatant_id), 
                        None
                    )
                    if current_combatant and not current_combatant.is_player:
                        logger.info(f"Current AI step/turn segment complete. Next distinct turn is for NPC: {current_combatant.name}. Setting backend trigger.")
                        return True
        return False
    
    def _get_continuation_instruction(self) -> Optional[str]:
        """Check if we need to add an instruction for continuation (e.g., NPC turn)."""
        # Import here to avoid circular imports
        from app.services.game_events.handlers.next_step_handler import NextStepHandler
        
        # Create a temporary NextStepHandler instance to use its logic
        temp_handler = NextStepHandler(
            self.game_state_repo, self.character_service, self.dice_service,
            self.combat_service, self.chat_service, self.ai_response_processor,
            self.campaign_service, self.rag_service
        )
        temp_handler._shared_state = self._shared_state
        
        # Use its NPC turn detection logic
        return temp_handler._get_npc_turn_instruction()
    
    def _get_combat_info_snapshot(self) -> Dict[str, Any]:
        """Get current combat info for snapshot."""
        from app.services.combat_utilities import CombatFormatter
        return CombatFormatter.format_combat_status(self.game_state_repo)
    
    def _can_retry_last_request(self) -> bool:
        """Check if last AI request can be retried."""
        if not self._last_ai_request_context or not self._last_ai_request_timestamp:
            return False
        
        # Check if request is not too old (5 minutes)
        return (time.time() - self._last_ai_request_timestamp) <= 300
    
    def _clear_pending_dice_requests(self, submitted_request_ids: Optional[List[str]] = None) -> None:
        """
        Clear pending dice requests.
        
        Args:
            submitted_request_ids: List of request IDs that were submitted. If None, clears all pending requests.
        """
        game_state = self.game_state_repo.get_game_state()
        
        if submitted_request_ids is None:
            # Legacy behavior: clear all pending requests
            cleared_ids = [req.request_id for req in game_state.pending_player_dice_requests if req.request_id]
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
            event_queue = None
            try:
                from app.core.container import get_container
                container = get_container()
                event_queue = container.get_event_queue()
            except Exception as e:
                logger.debug(f"Could not get event queue: {e}")
                
            if event_queue:
                from app.events.game_update_events import PlayerDiceRequestsClearedEvent
                event = PlayerDiceRequestsClearedEvent(
                    cleared_request_ids=cleared_ids,
                    correlation_id=self._current_correlation_id
                )
                event_queue.put_event(event)
                logger.debug(f"Emitted PlayerDiceRequestsClearedEvent for {len(cleared_ids)} requests")
    
    def _get_current_turn_character_name(self) -> str:
        """Get the name of the character whose turn it currently is."""
        from app.services.combat_utilities import CombatValidator
        
        if CombatValidator.is_combat_active(self.game_state_repo):
            current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
            if current_combatant_id:
                return self.character_service.get_character_name(current_combatant_id)
        
        return "the current character"
