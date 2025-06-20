"""
Simple shared state management for the single-user game application.

Since this is a single-user application, we maintain a single global state
without complex threading or atomic operations.
"""

import time
from typing import List, Optional

from app.models.common import MessageDict
from app.models.events import AIRequestContextModel


class SharedStateManager:
    """Simple shared state manager for single-user game application."""

    def __init__(self) -> None:
        # Simple instance variables - no threading complexity
        self.ai_processing = False
        self.needs_backend_trigger = False
        self.last_ai_request_context: Optional[AIRequestContextModel] = None
        self.last_ai_request_timestamp: Optional[float] = None

    def set_ai_processing(self, processing: bool) -> None:
        """Set AI processing flag."""
        self.ai_processing = processing

    def is_ai_processing(self) -> bool:
        """Get AI processing flag."""
        return self.ai_processing

    def set_needs_backend_trigger(self, needs_trigger: bool) -> None:
        """Set backend trigger flag."""
        self.needs_backend_trigger = needs_trigger

    def get_needs_backend_trigger(self) -> bool:
        """Get backend trigger flag."""
        return self.needs_backend_trigger

    def store_ai_request_context(
        self, messages: List[MessageDict], initial_instruction: Optional[str] = None
    ) -> None:
        """Store AI request context for retry."""
        self.last_ai_request_context = AIRequestContextModel(
            messages=messages.copy(),  # Simple copy, no deep copy complexity
            initial_instruction=initial_instruction,
        )
        self.last_ai_request_timestamp = time.time()

    def get_ai_request_context(self) -> Optional[AIRequestContextModel]:
        """Get stored AI request context."""
        return self.last_ai_request_context

    def can_retry_last_request(self, max_age_seconds: int = 300) -> bool:
        """Check if retry is possible."""
        if not self.last_ai_request_context or not self.last_ai_request_timestamp:
            return False
        return (time.time() - self.last_ai_request_timestamp) <= max_age_seconds

    def reset_state(self) -> None:
        """Reset all state to initial values. Useful for testing."""
        self.ai_processing = False
        self.needs_backend_trigger = False
        self.last_ai_request_context = None
        self.last_ai_request_timestamp = None
