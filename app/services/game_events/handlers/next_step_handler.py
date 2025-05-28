"""
Handler for next step events.
"""

import logging
from typing import Dict, Any, Optional
from .base_handler import BaseEventHandler

logger = logging.getLogger(__name__)


class NextStepHandler(BaseEventHandler):
    """Handles next step events."""
    
    def _get_npc_turn_instruction(self) -> Optional[str]:
        """Check if it's an NPC's turn and return appropriate instruction."""
        from app.services.combat_service import CombatValidator
        
        game_state = self.game_state_repo.get_game_state()
        
        # Check if combat is active
        if not CombatValidator.is_combat_active(self.game_state_repo):
            return None
            
        # Get current combatant
        current_combatant_id = CombatValidator.get_current_combatant_id(self.game_state_repo)
        if not current_combatant_id:
            return None
            
        # Find the combatant
        current_combatant = next(
            (c for c in game_state.combat.combatants if c.id == current_combatant_id), 
            None
        )
        
        # If it's an NPC, check if we need instruction
        if current_combatant and not current_combatant.is_player:
            # Check if we've already added the turn instruction for this NPC
            # or if we're in the middle of a dice roll continuation
            if game_state.chat_history:
                # Look at recent messages
                last_n = min(10, len(game_state.chat_history))
                recent_messages = game_state.chat_history[-last_n:]
                
                for i, msg in enumerate(reversed(recent_messages)):
                    content = msg.get("content", "")
                    
                    # If we find the turn instruction, check if there's been a dice roll since
                    if content == f"It's {current_combatant.name}'s turn. Narrate their action.":
                        # Calculate the actual position in the recent_messages list
                        actual_position = last_n - i - 1
                        # Check if any messages after this are dice results for this NPC
                        remaining_msgs = recent_messages[actual_position + 1:]
                        logger.debug(f"Found turn instruction at position {actual_position}, checking {len(remaining_msgs)} messages after it")
                        for j, remaining_msg in enumerate(remaining_msgs):
                            remaining_content = remaining_msg.get("content", "")
                            # Check for NPC dice roll results
                            if "**NPC Rolls:**" in remaining_content and current_combatant.name in remaining_content:
                                logger.info(f"Found dice roll for {current_combatant.name} at position {j} after turn instruction - this is a continuation")
                                return None
                        
                        # No dice rolls found after instruction, skip duplicate
                        logger.info(f"Skipping duplicate NPC instruction for {current_combatant.name} - no dice rolls found after turn instruction")
                        return None
            
            logger.info(f"Detected NPC turn for: {current_combatant.name}")
            return f"It's {current_combatant.name}'s turn. Narrate their action."
            
        return None
    
    def handle(self) -> Dict[str, Any]:
        """Handle triggering the next step and return response data."""
        logger.info("Handling next step trigger...")
        
        # Check if AI is busy (use shared state if available)
        if self._shared_state and self._shared_state['ai_processing']:
            logger.warning("AI is busy. Next step rejected.")
            # Don't clear the backend trigger flag if AI is busy
            return self._create_error_response("AI is busy", status_code=429, preserve_backend_trigger=True)
        elif not self._shared_state and self._ai_processing:
            logger.warning("AI is busy. Next step rejected.")
            return self._create_error_response("AI is busy", status_code=429, preserve_backend_trigger=True)
        
        # Only clear the backend trigger flag after we confirm we can process
        if self._shared_state:
            self._shared_state['needs_backend_trigger'] = False
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        try:
            # Check if this is an NPC turn that needs narration
            npc_instruction = self._get_npc_turn_instruction()
            
            # If it's an NPC turn, add the instruction to chat history
            if npc_instruction:
                self.chat_service.add_message("user", npc_instruction, is_dice_result=False)
            
            # Process AI step using shared base functionality
            # Don't pass initial_instruction since we've added it to chat history
            ai_response_obj, _, status, needs_backend_trigger, collected_steps = self._call_ai_and_process_step(ai_service)
            
            response = self._create_frontend_response(needs_backend_trigger, status_code=status, ai_response=ai_response_obj)
            
            # Add collected steps for frontend animation
            if collected_steps:
                response["animation_steps"] = collected_steps
                
            return response
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_next_step: {e}", exc_info=True)
            # Clear the processing flag
            if self._shared_state:
                self._shared_state['ai_processing'] = False
            else:
                self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error processing next step.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
