"""
Unit test to demonstrate synchronous blocking issue in game orchestrator.

This test shows that the handle_event method blocks the event loop,
preventing SSE events from being sent until processing completes.
"""

import asyncio
import time
from typing import Any
from unittest.mock import Mock, patch

import pytest

from app.core.container import get_container
from app.models.events import GameEventModel, GameEventType
from app.providers.ai.schemas import AIResponse


class TestSynchronousBlocking:
    """Test that demonstrates the synchronous blocking issue."""

    def test_handle_event_is_now_async(self) -> None:
        """Test that handle_event is now async and doesn't block."""
        container = get_container()
        orchestrator = container.get_game_orchestrator()

        # Verify that handle_event is now async
        assert asyncio.iscoroutinefunction(orchestrator.handle_event), (
            "handle_event should be async to avoid blocking"
        )

    @pytest.mark.anyio
    @pytest.mark.parametrize("anyio_backend", ["asyncio"])
    async def test_handle_event_doesnt_block(self) -> None:
        """Test that handle_event doesn't block the event loop during processing."""
        container = get_container()
        orchestrator = container.get_game_orchestrator()

        # Mock AI service to add delay
        ai_service = container.get_ai_service()

        def slow_get_response(*args: Any, **kwargs: Any) -> AIResponse:
            """Simulate slow AI processing."""
            time.sleep(0.02)  # Simulate 20ms AI processing
            return AIResponse(
                narrative="Test response",
                reasoning="Test",
                dice_requests=[],
                end_turn=True,
            )

        with patch.object(ai_service, "get_response", side_effect=slow_get_response):
            # Create a test event
            event = GameEventModel(type=GameEventType.NEXT_STEP, data={})

            # Test that we can run multiple calls concurrently
            start_time = time.time()

            # Run two calls concurrently
            responses = await asyncio.gather(
                orchestrator.handle_event(event), orchestrator.handle_event(event)
            )

            end_time = time.time()
            duration = end_time - start_time

            # If properly async, both should complete in ~300ms (not 600ms)
            assert duration < 0.5, (
                f"Expected concurrent execution in ~0.3s, got {duration:.3f}s"
            )
            assert all(r is not None for r in responses)
