"""
Thread-safe event queue implementation for the event-driven system.
"""
import queue
import threading
from typing import Optional
from app.events.game_update_events import BaseGameUpdateEvent
import logging

logger = logging.getLogger(__name__)


class EventQueue:
    """Thread-safe FIFO queue for game update events."""
    
    def __init__(self, maxsize: int = 0):
        """
        Initialize the event queue.
        
        Args:
            maxsize: Maximum queue size (0 for unlimited)
        """
        self._queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.RLock()
    
    def put_event(self, event: BaseGameUpdateEvent) -> None:
        """
        Add an event to the queue.
        
        Args:
            event: The game update event to add
        """
        try:
            self._queue.put(event, block=False)
        except queue.Full:
            logger.error(f"Event queue is full, dropping event: {event.event_type}")
    
    def get_event(self, block: bool = True, timeout: Optional[float] = None) -> Optional[BaseGameUpdateEvent]:
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
    
    def peek(self) -> Optional[BaseGameUpdateEvent]:
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
    
    def is_full(self) -> bool:
        """Check if the queue is full."""
        return self._queue.full()