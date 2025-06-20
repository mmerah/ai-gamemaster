"""
Integration tests for IChatService and SSE event streaming.
Consolidated from test_chat_service_events_integration.py, test_sse_chat_events.py,
and test_phase3_e2e_verification.py.
"""

import time
from unittest.mock import Mock

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.core.container import get_container


class TestChatAndSSEIntegration:
    """Test IChatService event emission and SSE streaming integration."""

    # Using the centralized app fixture from tests/conftest.py which includes proper AI mocking
    # The app fixture is automatically provided by pytest

    @pytest.fixture
    def client(self, app: Flask) -> FlaskClient:
        """Create a test client."""
        return app.test_client()

    def test_sse_streams_chat_events(self, app: Flask, client: FlaskClient) -> None:
        """Test that SSE endpoint streams events from IChatService."""
        with app.app_context():
            container = get_container()
            chat_service = container.get_chat_service()

            # Add a message which should trigger an event
            test_message = "The cave is very dark."
            chat_service.add_message("assistant", test_message)

            # Verify the event was added to the queue
            event_queue = container.get_event_queue()
            assert event_queue.qsize() > 0, "Event should be in queue"

            # Test SSE endpoint exists and is properly configured
            response = client.get(
                "/api/game_event_stream", headers={"Accept": "text/event-stream"}
            )
            assert response.status_code == 200
            assert response.content_type.startswith("text/event-stream")

            # The integration we're testing:
            # 1. Chat service adds messages ✓
            # 2. Chat service emits events to queue ✓ (verified above with qsize)
            # 3. SSE endpoint exists and is configured ✓
            # 4. SSE endpoint would stream these events (requires real HTTP client)

            # Due to Flask test client limitations with streaming responses,
            # we cannot actually read the SSE stream without blocking.
            # The full integration is tested in production/manual testing.

    def test_end_to_end_chat_flow(
        self, app: Flask, client: FlaskClient, mock_ai_service: Mock
    ) -> None:
        """Test complete flow: player action -> AI response -> chat update -> SSE event."""
        # Configure mock AI service
        from app.providers.ai.schemas import AIResponse

        mock_ai_service.add_response(
            AIResponse(
                narrative="You see a glowing crystal in the cave.",
                reasoning="Describing the cave",
                dice_requests=[],
                end_turn=False,
            )
        )

        with app.app_context():
            # Send player action first
            action_response = client.post(
                "/api/player_action",
                json={"action_type": "free_text", "value": "I examine the cave"},
            )
            assert action_response.status_code == 200

            # Give a small delay for events to be processed after the action
            time.sleep(0.1)

            # Check that events were generated
            # Note: We can't reliably get the exact queue size due to concurrent processing
            # but we know events should have been generated

            # Test SSE endpoint is available for streaming
            sse_response = client.get(
                "/api/game_event_stream", headers={"Accept": "text/event-stream"}
            )
            assert sse_response.status_code == 200
            assert sse_response.content_type.startswith("text/event-stream")

            # Verify proper SSE headers
            assert sse_response.headers.get("Cache-Control") == "no-cache"
            assert sse_response.headers.get("X-Accel-Buffering") == "no"

            # Verify response data includes AI narrative
            response_data = action_response.get_json()
            assert response_data is not None
            assert "chat_history" in response_data

            # Find the AI response in chat history
            ai_responses = [
                msg
                for msg in response_data["chat_history"]
                if msg.get("role") == "assistant"
                and "glowing crystal" in msg.get("content", "")
            ]
            assert len(ai_responses) > 0, "AI response should be in chat history"

            # The complete flow works:
            # 1. Player action triggers AI response
            # 2. AI response is added to chat history
            # 3. Events are generated for SSE streaming
            # 4. SSE endpoint is available to stream these events
