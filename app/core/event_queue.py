"""
Thread-safe event queue implementation for the event-driven system.
"""

import logging
import queue
import threading
import uuid
from typing import Callable, Dict, List, Optional

from app.models.events import BaseGameEvent

logger = logging.getLogger(__name__)


class EventQueue:
    """Thread-safe FIFO queue for game update events."""

    def __init__(self, maxsize: int = 0):
        """
        Initialize the event queue.

        Args:
            maxsize: Maximum queue size (0 for unlimited)
        """
        self._queue: queue.Queue[BaseGameEvent] = queue.Queue(maxsize=maxsize)
        self._lock = threading.RLock()
        self._subscribers: Dict[str, Callable[[BaseGameEvent], None]] = {}
        self._all_subscribers: List[Callable[[BaseGameEvent], None]] = []

    def put_event(self, event: BaseGameEvent) -> None:
        """
        Add an event to the queue.

        Args:
            event: The game update event to add
        """
        try:
            self._queue.put(event, block=False)
            # Notify all subscribers
            with self._lock:
                for subscriber in self._all_subscribers:
                    try:
                        subscriber(event)
                    except Exception as e:
                        logger.error(f"Subscriber error: {e}")
        except queue.Full:
            logger.error(f"Event queue is full, dropping event: {event.event_type}")

    def emit(self, event: BaseGameEvent) -> None:
        """Alias for put_event for compatibility."""
        self.put_event(event)

    def get_event(
        self, block: bool = True, timeout: Optional[float] = None
    ) -> Optional[BaseGameEvent]:
        """
        Get the next event from the queue.

        Args:
            block: Whether to block if queue is empty
            timeout: Timeout in seconds (None for infinite)

        Returns:
            The next event or None if timeout/non-blocking and empty
        """
        try:
            event = self._queue.get(block=block, timeout=timeout)
            return event
        except queue.Empty:
            return None

    def qsize(self) -> int:
        """
        Get the approximate size of the queue.

        Returns:
            Number of events in the queue
        """
        return self._queue.qsize()

    def clear(self) -> None:
        """Clear all events from the queue."""
        with self._lock:
            # Create new queue to clear
            self._queue = queue.Queue(maxsize=self._queue.maxsize)
            logger.info("Event queue cleared")

    def peek(self) -> Optional[BaseGameEvent]:
        """
        Peek at the next event without removing it.

        Returns:
            The next event or None if empty
        """
        with self._lock:
            try:
                # Get the item
                item = self._queue.get_nowait()
                # Put it back immediately
                self._queue.put(item)
                return item
            except queue.Empty:
                return None

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()

    def subscribe_all(self, handler: Callable[[BaseGameEvent], None]) -> str:
        """Subscribe to all events."""
        subscription_id = str(uuid.uuid4())
        with self._lock:
            self._all_subscribers.append(handler)
            self._subscribers[subscription_id] = handler
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        with self._lock:
            handler = self._subscribers.pop(subscription_id, None)
            if handler and handler in self._all_subscribers:
                self._all_subscribers.remove(handler)
