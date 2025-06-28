"""
Integration test to verify SSE events are sent during async processing.

This tests that with the async fix, SSE events are sent in real-time
as they're generated, not buffered until after processing completes.
"""

import asyncio
import time
from typing import Any, List, Tuple
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI

from app.core.container import get_container
from app.models.events.base import BaseGameEvent
from app.models.events.event_types import GameEventType
from app.models.events.game_events import GameEventModel
from app.models.events.narrative import NarrativeAddedEvent
from app.providers.ai.schemas import AIResponse


class TestSSEAsyncEvents:
    """Test that SSE events are sent asynchronously during processing."""

    @pytest.mark.anyio
    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    async def test_events_emitted_during_async_processing(self, app: FastAPI) -> None:
        """Test that events emitted during AI processing are available immediately."""
        container = get_container()
        event_queue = container.get_event_queue()
        orchestrator = container.get_game_orchestrator()

        # Track events and their timing
        emitted_events: List[Tuple[float, NarrativeAddedEvent]] = []
        received_events: List[Tuple[float, BaseGameEvent]] = []

        # Create a consumer that processes events from the queue
        async def event_consumer() -> None:
            """Consume events from the queue asynchronously."""
            while True:
                # Use asyncio.to_thread to check queue in non-blocking way
                event = await asyncio.to_thread(event_queue.get_event, block=False)
                if event:
                    received_events.append((time.time(), event))
                else:
                    await asyncio.sleep(0.01)

                # Stop after we've received enough events
                if len(received_events) >= 3:
                    break

        # Mock AI service to emit events during processing
        ai_service = container.get_ai_service()

        def mock_ai_response(*args: Any, **kwargs: Any) -> AIResponse:
            """Mock AI that emits events during processing."""

            # Emit first event immediately
            event1 = NarrativeAddedEvent(
                role="assistant", content="Processing your action..."
            )
            event_queue.put_event(event1)
            emitted_events.append((time.time(), event1))

            # Simulate some processing
            time.sleep(0.01)

            # Emit second event
            event2 = NarrativeAddedEvent(
                role="assistant", content="The dice tumble across the table..."
            )
            event_queue.put_event(event2)
            emitted_events.append((time.time(), event2))

            # More processing
            time.sleep(0.01)

            # Return AI response
            return AIResponse(
                narrative="Your attack misses!",
                reasoning="Roll of 10 vs AC 15",
                dice_requests=[],
                end_turn=True,
            )

        with patch.object(ai_service, "get_response", side_effect=mock_ai_response):
            # Start the event consumer
            consumer_task = asyncio.create_task(event_consumer())

            # Give consumer time to start
            await asyncio.sleep(0.01)

            # Process an event (this will trigger AI processing)
            start_time = time.time()
            event = GameEventModel(type=GameEventType.NEXT_STEP, data={})

            # This should not block - events should be processed concurrently
            response = await orchestrator.handle_event(event)
            end_time = time.time()

            # Wait for consumer to finish
            await asyncio.wait_for(consumer_task, timeout=1.0)

            # Verify we got a response
            assert response is not None

            # Verify events were received during processing, not after
            processing_duration = end_time - start_time

            # At least some events should have been received before processing completed
            events_during_processing = [
                (ts, event) for ts, event in received_events if ts < end_time
            ]

            assert len(events_during_processing) >= 2, (
                f"Expected at least 2 events during processing, got {len(events_during_processing)}"
            )

            # Verify timing - events should be spread throughout processing
            if len(received_events) >= 2:
                first_event_delay = received_events[0][0] - start_time
                second_event_delay = received_events[1][0] - start_time

                # First event should be very early (< 50ms)
                assert first_event_delay < 0.05, (
                    f"First event took too long: {first_event_delay:.3f}s"
                )

                # Second event should come after first but during processing
                assert second_event_delay >= first_event_delay, (
                    "Second event should come after first"
                )

                # Both events should arrive during processing (not after)
                assert second_event_delay < processing_duration, (
                    "Events should arrive during processing, not after"
                )
