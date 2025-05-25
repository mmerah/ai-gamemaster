"""
Handler for next step events.
"""

import logging
from typing import Dict, Any
from .base_handler import BaseEventHandler

logger = logging.getLogger(__name__)


class NextStepHandler(BaseEventHandler):
    """Handles next step events."""
    
    def handle(self) -> Dict[str, Any]:
        """Handle triggering the next step and return response data."""
        logger.info("Handling next step trigger...")
        
        # Check if AI is busy
        if self._ai_processing:
            logger.warning("AI is busy. Next step rejected.")
            return self._create_error_response("AI is busy", status_code=429)
        
        # Get AI service
        ai_service = self._get_ai_service()
        if not ai_service:
            return self._create_error_response("AI Service unavailable.")
        
        try:
            # Process AI step using shared base functionality
            ai_response_obj, _, status, needs_backend_trigger = self._call_ai_and_process_step(ai_service)
            
            return self._create_frontend_response(needs_backend_trigger, status_code=status, ai_response=ai_response_obj)
            
        except Exception as e:
            logger.error(f"Unhandled exception in handle_next_step: {e}", exc_info=True)
            self._ai_processing = False
            self.chat_service.add_message("system", "(Internal Server Error processing next step.)", is_dice_result=True)
            return self._create_error_response("Internal server error", status_code=500)
