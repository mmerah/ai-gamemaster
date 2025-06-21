"""
Server-Sent Events (SSE) routes for real-time event streaming - FastAPI version.
"""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.responses import Response

from app.api.dependencies_fastapi import get_event_queue, get_settings
from app.core.system_interfaces import IEventQueue
from app.models.events import BaseGameEvent
from app.settings import Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["sse"])


async def generate_sse_events(
    event_queue: IEventQueue,
    settings: Settings,
    test_mode: bool = False,
    test_timeout: float = 2.0,
) -> AsyncGenerator[str, None]:
    """Async generator function that yields SSE formatted events."""

    # Send initial connection event
    yield 'event: connected\ndata: {"status": "connected"}\n\n'

    last_heartbeat = time.time()
    heartbeat_interval = settings.sse.heartbeat_interval
    start_time = time.time() if test_mode else None

    while True:
        # In test mode, stop after timeout
        if test_mode and start_time and (time.time() - start_time) > test_timeout:
            break

        try:
            # Check for events with short timeout to allow heartbeats
            # Note: get_event is synchronous, so we run it in a thread pool
            event = await asyncio.to_thread(
                event_queue.get_event, block=True, timeout=settings.sse.event_timeout
            )

            if event and isinstance(event, BaseGameEvent):
                # Format event as SSE
                # Use model_dump with exclude_none=True to avoid sending null fields
                event_dict = event.model_dump(exclude_none=True)
                event_data = json.dumps(event_dict, default=str)
                yield f"data: {event_data}\n\n"
                logger.debug(f"Sent SSE event: {event.event_type}")

            # Send periodic heartbeat to keep connection alive
            current_time = time.time()
            if current_time - last_heartbeat > heartbeat_interval:
                yield ":heartbeat\n\n"
                last_heartbeat = current_time

            # Small async sleep to prevent blocking
            await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Error in SSE generator: {e}")
            # Send error event
            error_data = json.dumps(
                {"event_type": "error", "message": "Internal server error"}
            )
            yield f"event: error\ndata: {error_data}\n\n"
            break


@router.get("/game_event_stream")
async def game_event_stream(
    request: Request,
    event_queue: IEventQueue = Depends(get_event_queue),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """
    SSE endpoint for streaming game update events to clients.

    Returns:
        StreamingResponse: SSE stream response
    """
    logger.info("Client connected to SSE stream")

    # Check if in test mode (set via app state during testing)
    test_mode = getattr(request.app.state, "testing", False)

    async def event_generator() -> AsyncGenerator[str, None]:
        """Inner async generator with error handling."""
        try:
            async for event in generate_sse_events(
                event_queue, settings, test_mode=test_mode, test_timeout=1.0
            ):
                yield event
        except asyncio.CancelledError:
            logger.info("Client disconnected from SSE stream")
            raise
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
        finally:
            logger.debug("SSE stream ended")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # Configure based on your needs
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


@router.get("/game_event_stream/health")
async def sse_health_check(
    event_queue: IEventQueue = Depends(get_event_queue),
) -> Dict[str, Any]:
    """Health check endpoint for SSE service."""

    return {
        "status": "healthy",
        "queue_size": event_queue.qsize(),
        "timestamp": time.time(),
    }
