"""
Server-Sent Events (SSE) routes for real-time event streaming.
"""

import json
import logging
import time
from typing import Any, Dict, Generator

from flask import Blueprint, Response, stream_with_context

from app.core.container import get_container
from app.models.events import BaseGameEvent
from app.settings import get_settings

logger = logging.getLogger(__name__)

sse_bp = Blueprint("sse", __name__)


def generate_sse_events(
    test_mode: bool = False, test_timeout: float = 2.0
) -> Generator[str, None, None]:
    """Generator function that yields SSE formatted events."""
    container = get_container()
    event_queue = container.get_event_queue()

    # Send initial connection event
    yield 'event: connected\ndata: {"status": "connected"}\n\n'

    last_heartbeat = time.time()
    settings = get_settings()
    heartbeat_interval = settings.sse.heartbeat_interval
    start_time = time.time() if test_mode else None

    while True:
        # In test mode, stop after timeout
        if test_mode and start_time and (time.time() - start_time) > test_timeout:
            break
        try:
            # Check for events (non-blocking with short timeout)
            settings = get_settings()
            event = event_queue.get_event(
                block=True, timeout=settings.sse.event_timeout
            )

            if event and isinstance(event, BaseGameEvent):
                # Format event as SSE
                event_data = event.model_dump_json()
                yield f"data: {event_data}\n\n"
                logger.debug(f"Sent SSE event: {event.event_type}")

            # Send periodic heartbeat to keep connection alive
            current_time = time.time()
            if current_time - last_heartbeat > heartbeat_interval:
                yield ":heartbeat\n\n"
                last_heartbeat = current_time

        except Exception as e:
            logger.error(f"Error in SSE generator: {e}")
            # Send error event
            error_data = json.dumps(
                {"event_type": "error", "message": "Internal server error"}
            )
            yield f"event: error\ndata: {error_data}\n\n"
            break


@sse_bp.route("/api/game_event_stream")
def game_event_stream() -> Response:
    """
    SSE endpoint for streaming game update events to clients.

    Returns:
        Response: SSE stream response
    """
    logger.info("Client connected to SSE stream")

    # Check if in test mode (Flask testing client sets this)
    from flask import current_app

    test_mode = current_app.config.get("TESTING", False)

    def stream() -> Generator[str, None, None]:
        """Inner generator with error handling."""
        try:
            yield from generate_sse_events(test_mode=test_mode, test_timeout=1.0)
        except GeneratorExit:
            logger.info("Client disconnected from SSE stream")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
        finally:
            logger.debug("SSE stream ended")

    response = Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # Configure based on your needs
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )

    return response


@sse_bp.route("/api/game_event_stream/health")
def sse_health_check() -> Dict[str, Any]:
    """Health check endpoint for SSE service."""
    container = get_container()
    event_queue = container.get_event_queue()

    return {
        "status": "healthy",
        "queue_size": event_queue.qsize(),
        "timestamp": time.time(),
    }
