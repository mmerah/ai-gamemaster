"""System-level interfaces for the AI Game Master.

This module defines interfaces for core system components like
event queues and other infrastructure services.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from app.models.events.base import BaseGameEvent


class IEventQueue(ABC):
    """Interface for event queue operations."""

    @abstractmethod
    def put_event(self, event: BaseGameEvent) -> None:
        """Add an event to the queue."""
        pass

    @abstractmethod
    def emit(self, event: BaseGameEvent) -> None:
        """Alias for put_event for compatibility."""
        pass

    @abstractmethod
    def get_event(
        self, block: bool = True, timeout: Optional[float] = None
    ) -> Optional[BaseGameEvent]:
        """Get the next event from the queue."""
        pass

    @abstractmethod
    def qsize(self) -> int:
        """Get the approximate size of the queue."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all events from the queue."""
        pass

    @abstractmethod
    def peek(self) -> Optional[BaseGameEvent]:
        """Peek at the next event without removing it."""
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        pass

    @abstractmethod
    def subscribe_all(self, handler: Callable[[BaseGameEvent], None]) -> str:
        """Subscribe to all events."""
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        pass
