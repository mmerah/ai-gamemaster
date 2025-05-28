"""
Handler for retry events.
"""

import logging
from typing import Dict, Any
from .base_handler import BaseEventHandler

logger = logging.getLogger(__name__)


class RetryHandler(BaseEventHandler):
    """Handles retry events."""
    
    def handle(self) -> Dict[str, Any]:
        """Handle retry request and return response data."""
        logger.info("Handling retry request...")
        
        # Check if AI is busy (use shared state if available)
        if self._shared_state and self._shared_state['ai_processing']:
            logger.warning("AI is busy. Retry rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        elif not self._shared_state and self._ai_processing:
            logger.warning("AI is busy. Retry rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Check if we can retry the last request
        if not self._can_retry_last_request():
            logger.warning("Cannot retry - no stored context or context too old")
            self.chat_service.add_message("system", "(No recent AI request to retry.)", is_dice_result=True)
            return self._create_error_response("No recent request to retry", status_code=400)
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        try:
            # Remove last AI message if it exists
            self._remove_last_ai_message()
            
            # Use stored context for retry
            stored_context = self._last_ai_request_context
            messages = stored_context.get("messages", [])
            initial_instruction = stored_context.get("initial_instruction")
            
            retry_instruction = "Please try again with a different approach."
            if initial_instruction:
                retry_instruction = f"{initial_instruction} Please try again with a different approach."
            
            # Process AI step with retry instruction using stored context
            ai_response_obj, _, status, needs_backend_trigger = self._call_ai_and_process_step(
                ai_service, 
                initial_instruction=retry_instruction,
                use_stored_context=True,
                messages_override=messages
            )
            
            return self._create_frontend_response(needs_backend_trigger, status_code=status, ai_response=ai_response_obj)
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_retry: {e}", exc_info=True)
            # Clear the processing flag
            if self._shared_state:
                self._shared_state['ai_processing'] = False
            else:
                self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error processing retry.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
    
    def _remove_last_ai_message(self) -> None:
        """Remove the last AI message from chat history."""
        game_state = self.game_state_repo.get_game_state()
        
        if game_state.chat_history and game_state.chat_history[-1].get("role") == "assistant":
            removed_message = game_state.chat_history.pop()
            logger.info(f"Removed last AI message for retry: {removed_message.get('content', '')[:100]}...")
        else:
            logger.warning("No AI message found to remove for retry")
