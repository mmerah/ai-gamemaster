"""
Event emission helper functions.

This module provides utilities for emitting events in a consistent way
throughout the application, handling null-safety and optional logging.
"""

import logging
from typing import Optional

from app.core.system_interfaces import IEventQueue
from app.models.events.base import BaseGameEvent

logger = logging.getLogger(__name__)


def emit_event(
    event_queue: IEventQueue,
    event: BaseGameEvent,
    log_message: Optional[str] = None,
    log_level: int = logging.DEBUG,
) -> None:
    """
    Emit an event.

    Args:
        event_queue: The event queue instance
        event: The event to emit
        log_message: Optional message to log when event is emitted
        log_level: Log level for the message (default: DEBUG)
    """
    event_queue.put_event(event)
    if log_message:
        logger.log(log_level, log_message)


def emit_with_logging(
    event_queue: IEventQueue,
    event: BaseGameEvent,
    event_description: str,
) -> None:
    """
    Emit an event with standard debug logging.

    Args:
        event_queue: The event queue instance
        event: The event to emit
        event_description: Human-readable description of the event
    """
    emit_event(
        event_queue,
        event,
        log_message=f"Emitted {event.__class__.__name__}: {event_description}",
        log_level=logging.DEBUG,
    )
