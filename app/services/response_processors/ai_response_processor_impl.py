"""
Main AI response processor implementation.
"""
import logging
from typing import Dict, List, Tuple, Optional
from app.core.interfaces import (
    AIResponseProcessor, GameStateRepository, CharacterService, 
    DiceRollingService, CombatService, ChatService
)
from app.core.event_queue import EventQueue
from app.ai_services.schemas import AIResponse, DiceRequest
from app.game import state_processors
from .dice_request_handler import DiceRequestHandler
from .turn_advancement_handler import TurnAdvancementHandler

logger = logging.getLogger(__name__)


class AIResponseProcessorImpl(AIResponseProcessor):
    """Implementation of AI response processor."""
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService,
                 dice_service: DiceRollingService, combat_service: CombatService, 
                 chat_service: ChatService, event_queue: Optional[EventQueue] = None):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.combat_service = combat_service
        self.chat_service = chat_service
        self.event_queue = event_queue
    
    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Delegate to character service for compatibility with state processors."""
        return self.character_service.find_character_by_name_or_id(identifier)
    
    def process_response(self, ai_response: AIResponse, correlation_id: Optional[str] = None) -> Tuple[List[Dict], bool]:
        """Process an AI response and return pending requests and rerun flag."""
        logger.debug("Processing AIResponse object via AIResponseProcessor...")
        
        # Pre-calculate next combatant BEFORE any game state changes
        next_combatant_info = self._pre_calculate_next_combatant(ai_response)
        
        # Handle narrative and location updates
        self._handle_narrative_and_location(ai_response, correlation_id)
        
        # Apply game state updates
        self._handle_game_state_updates(ai_response, correlation_id)
        
        # Check and reset combat just started flag
        combat_just_started_flag = self._check_and_reset_combat_flag()
        
        # Handle dice requests (NPC rolls happen here)
        pending_player_reqs, npc_rolls_performed, needs_rerun_after_npc_rolls = (
            self._handle_dice_requests(ai_response, combat_just_started_flag, correlation_id)
        )
        
        # Check if current turn should continue after player dice resolution
        needs_turn_continuation = self._should_continue_current_turn(ai_response, pending_player_reqs)
        
        # Combine rerun conditions
        needs_ai_rerun = needs_rerun_after_npc_rolls or needs_turn_continuation
        
        # Handle turn advancement using pre-calculated info
        self._handle_turn_advancement(ai_response, needs_ai_rerun, bool(pending_player_reqs), next_combatant_info)
        
        # Update pending player requests in game state
        self._update_pending_requests(pending_player_reqs, needs_ai_rerun)

        # RAG Event Log Update Trigger
        try:
            # Only attempt to update event log if we have a narrative
            if ai_response.narrative:
                from app.core.container import get_container
                game_state = self.game_state_repo.get_game_state()
                
                # Only update if we have a campaign ID
                if game_state.campaign_id:
                    # Generate event summary from narrative
                    summary = ai_response.narrative.strip()[:300]
                    
                    # Simple keyword extraction
                    import re
                    words = re.findall(r"\b\w+\b", summary.lower())
                    stopwords = {"the", "and", "a", "an", "to", "of", "in", "on", "at", "for", "with", "by", "is", "it", "as", "from", "that", "this", "was", "are", "be", "or", "but", "if", "then", "so", "do", "did", "has", "have", "had"}
                    keywords = list({w for w in words if len(w) > 3 and w not in stopwords})[:8]
                    
                    # Use the public add_event method
                    container = get_container()
                    rag_service = container.get_rag_service()
                    rag_service.add_event(
                        campaign_id=game_state.campaign_id,
                        event_summary=summary,
                        keywords=keywords
                    )
                    logger.debug("Event log updated with new event from AI response.")
        except Exception as e:
            # Log error but don't fail the response processing
            logger.warning(f"Failed to update event log after AI response: {e}")

        return pending_player_reqs, needs_ai_rerun
    
    def _handle_narrative_and_location(self, ai_response: AIResponse, correlation_id: Optional[str] = None) -> None:
        """Handle AI narrative and location updates."""
        if ai_response.reasoning:
            logger.info(f"AI Reasoning: {ai_response.reasoning}")
        else:
            logger.warning("AI Response missing 'reasoning'.")
        
        # Add AI response to chat history
        self.chat_service.add_message(
            "assistant",
            ai_response.narrative,
            ai_response_json=ai_response.model_dump_json(),
            correlation_id=correlation_id
        )
        
        # Update location if provided
        if ai_response.location_update:
            self._update_location(ai_response.location_update)
    
    def _update_location(self, location_update) -> None:
        """Update the current location."""
        game_state = self.game_state_repo.get_game_state()
        
        if hasattr(location_update, 'model_dump'):
            old_name = game_state.current_location.get("name")
            game_state.current_location = location_update.model_dump()
            logger.info(f"Location updated from '{old_name}' to '{location_update.name}'.")
            
            # Emit LocationChangedEvent
            if self.event_queue:
                from app.events.game_update_events import LocationChangedEvent
                event = LocationChangedEvent(
                    old_location_name=old_name,
                    new_location_name=location_update.name,
                    new_location_description=location_update.description if hasattr(location_update, 'description') else ""
                )
                self.event_queue.put_event(event)
                logger.debug(f"Emitted LocationChangedEvent: {old_name} -> {location_update.name}")
        elif location_update is not None:
            logger.warning(f"Invalid location_update data type: {type(location_update)}")
    
    def _handle_game_state_updates(self, ai_response: AIResponse, correlation_id: Optional[str] = None) -> bool:
        """Apply game state updates from AI response."""
        game_state = self.game_state_repo.get_game_state()
        
        # Store correlation ID in the game_manager context for state processors
        original_correlation_id = getattr(self, '_current_correlation_id', None)
        self._current_correlation_id = correlation_id
        
        try:
            return state_processors.apply_game_state_updates(
                game_state,
                ai_response.game_state_updates,
                self  # Pass self as game_manager for compatibility
            )
        finally:
            # Restore original correlation ID
            self._current_correlation_id = original_correlation_id
    
    def _pre_calculate_next_combatant(self, ai_response: AIResponse) -> Optional[Dict]:
        """Pre-calculate who should be next before any combatant removals."""
        game_state = self.game_state_repo.get_game_state()
        
        # Only pre-calculate if combat is active and AI wants to end turn
        if not (game_state.combat.is_active and getattr(ai_response, 'end_turn', None) is True):
            return None
            
        # Check if any combatant removals are planned
        removal_updates = [
            update for update in ai_response.game_state_updates 
            if getattr(update, 'type', None) == 'combatant_remove'
        ]
        
        if not removal_updates:
            return None  # No removals planned, normal advancement will work
            
        # Calculate who should be next after removal
        current_combatants = game_state.combat.combatants.copy()
        current_index = game_state.combat.current_turn_index
        
        if not (0 <= current_index < len(current_combatants)):
            logger.warning(f"Invalid current_turn_index {current_index}, cannot pre-calculate next combatant")
            return None
            
        # Find which combatants will be removed
        removal_ids = set()
        for update in removal_updates:
            removal_id = self.character_service.find_character_by_name_or_id(update.character_id)
            if removal_id:
                removal_ids.add(removal_id)
                
        # Simulate the removal to find the correct next combatant
        remaining_combatants = [c for c in current_combatants if c.id not in removal_ids]
        
        if not remaining_combatants:
            logger.info("All combatants will be removed, combat should end")
            return {"should_end_combat": True}
            
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
                new_index = next(i for i, c in enumerate(remaining_combatants) if c.id == next_combatant.id)
                logger.debug(f"Pre-calculated next combatant: {next_combatant.name} (ID: {next_combatant.id}) at new index {new_index}")
                return {
                    "combatant_id": next_combatant.id,
                    "new_index": new_index,
                    "should_end_combat": False
                }
            except StopIteration:
                continue  # This shouldn't happen but just in case
                
        # If we get here, couldn't find a valid next combatant
        logger.warning("Could not determine valid next combatant after removals")
        return None

    def _check_and_reset_combat_flag(self) -> bool:
        """Check and reset the combat just started flag."""
        game_state = self.game_state_repo.get_game_state()
        combat_just_started_flag = getattr(game_state.combat, '_combat_just_started_flag', False)
        
        if combat_just_started_flag:
            game_state.combat._combat_just_started_flag = False
        
        return combat_just_started_flag
    
    def _handle_dice_requests(self, ai_response: AIResponse, combat_just_started: bool, correlation_id: Optional[str] = None) -> Tuple[List[DiceRequest], bool, bool]:
        """Handle dice requests from AI response."""
        dice_handler = DiceRequestHandler(
            self.game_state_repo, self.character_service, self.dice_service, self.chat_service, self.event_queue,
            correlation_id=correlation_id
        )
        return dice_handler.process_dice_requests(ai_response, combat_just_started)
    
    def _should_continue_current_turn(self, ai_response: AIResponse, pending_player_reqs: List[DiceRequest]) -> bool:
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
        ai_end_turn = getattr(ai_response, 'end_turn', None)
        if ai_end_turn is not False:
            logger.debug(f"Turn continuation: AI end_turn={ai_end_turn}, no continuation needed")
            return False
        
        # Only if no player requests are pending (they've been resolved)
        if pending_player_reqs:
            logger.debug("Turn continuation: Player requests still pending, no continuation needed")
            return False
        
        # CRITICAL: Only continue if there are pending roll results to process
        # This prevents auto-continuation when AI is just asking "What do you do?"
        pending_npc_results = getattr(game_state, '_pending_npc_roll_results', [])
        if not pending_npc_results:
            logger.debug("Turn continuation: No pending NPC roll results to process, no continuation needed")
            return False
        
        # Safety: Ensure we have a valid current combatant
        from app.services.combat_utilities import CombatValidator
        current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
        if not current_combatant_id:
            logger.warning("Turn continuation: No valid current combatant, no continuation")
            return False
        
        # All conditions met - current turn should continue to process dice results
        logger.info(f"Turn continuation: AI set end_turn=false, no pending player requests, {len(pending_npc_results)} NPC results to process. Auto-continuing turn for combatant {current_combatant_id}")
        return True
    
    def _handle_turn_advancement(self, ai_response: AIResponse, needs_ai_rerun: bool, player_requests_pending: bool, next_combatant_info: Optional[Dict] = None) -> None:
        """Handle turn advancement based on AI signal."""
        turn_handler = TurnAdvancementHandler(self.game_state_repo, self.combat_service)
        turn_handler.handle_turn_advancement(ai_response, needs_ai_rerun, player_requests_pending, next_combatant_info)
    
    def _update_pending_requests(self, pending_player_reqs: List["DiceRequest"], needs_ai_rerun: bool) -> None:
        """Update pending player requests in game state."""
        game_state = self.game_state_repo.get_game_state()
        
        if pending_player_reqs:
            # Add new requests from AI response to existing pending requests
            game_state.pending_player_dice_requests.extend(pending_player_reqs)
            logger.info(f"{len(pending_player_reqs)} new player dice requests added. Total pending: {len(game_state.pending_player_dice_requests)}.")
        # Note: No longer clearing all pending requests automatically.
        # Requests should only be cleared by specific handlers when they process them.
