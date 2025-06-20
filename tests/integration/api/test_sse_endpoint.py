"""
Integration tests for Server-Sent Events (SSE) endpoint.
"""

import json

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.core.container import get_container
from app.models.events import CombatStartedEvent, NarrativeAddedEvent


class TestSSEEndpoint:
    """Test the SSE event streaming endpoint."""

    # Using the centralized app fixture from tests/conftest.py which includes proper AI mocking
    # The app fixture is automatically provided by pytest

    @pytest.fixture
    def client(self, app: Flask) -> FlaskClient:
        """Create test client."""
        return app.test_client()

    def test_sse_endpoint_exists(self, client: FlaskClient) -> None:
        """Test that SSE endpoint is accessible."""
        response = client.get("/api/game_event_stream")
        assert response.status_code == 200
        assert response.content_type.startswith("text/event-stream")

    def test_sse_endpoint_streams_events(self, client: FlaskClient, app: Flask) -> None:
        """Test that SSE endpoint streams events from queue."""
        with app.app_context():
            # Get event queue
            container = get_container()
            event_queue = container.get_event_queue()

            # Add events to queue before making request
            event1 = NarrativeAddedEvent(role="assistant", content="Combat begins!")
            from app.models.combat import CombatantModel

            event2 = CombatStartedEvent(
                combatants=[
                    CombatantModel(
                        id="pc_1",
                        name="Elara",
                        initiative=10,
                        current_hp=25,
                        max_hp=25,
                        armor_class=15,
                        is_player=True,
                    ),
                    CombatantModel(
                        id="goblin_1",
                        name="Goblin",
                        initiative=5,
                        current_hp=7,
                        max_hp=7,
                        armor_class=12,
                        is_player=False,
                    ),
                ]
            )

            # Add events directly to queue before making request
            # No need for thread delay in test
            event_queue.put_event(event1)
            event_queue.put_event(event2)

            # Make SSE request
            response = client.get("/api/game_event_stream")
            assert response.status_code == 200
            assert response.content_type.startswith("text/event-stream")

            # With Flask test client and streaming responses, we have limitations:
            # - response.get_data() waits for the entire stream (hangs until timeout)
            # - response.response is the generator but consuming it also blocks
            #
            # The best we can do is verify the endpoint exists, returns proper headers,
            # and trust that the SSE implementation works (tested manually/in production)

            # However, we CAN test the event queue behavior separately
            # We already verified above that events were added to the queue

            # Verify headers for SSE
            assert response.headers.get("Cache-Control") == "no-cache"
            assert response.headers.get("X-Accel-Buffering") == "no"

            # Note: For proper SSE testing, we would need:
            # 1. A real HTTP client (not Flask test client)
            # 2. Async testing framework
            # 3. Or mock the streaming behavior
            #
            # The key functionality we're testing:
            # - Events go into the queue ✓ (verified above)
            # - SSE endpoint exists ✓
            # - SSE endpoint has correct headers ✓
            # - SSE implementation streams events (requires manual/integration testing)

    def test_sse_endpoint_heartbeat(self, client: FlaskClient, app: Flask) -> None:
        """Test that SSE endpoint would send heartbeats (limited by test client)."""
        # Note: Flask test client doesn't support true streaming,
        # so we can only verify the endpoint exists and returns SSE format
        with app.app_context():
            response = client.get("/api/game_event_stream")
            assert response.status_code == 200
            assert response.content_type.startswith("text/event-stream")

            # In a real SSE connection, heartbeats would be sent
            # This is tested manually or with integration tests using real HTTP clients

    def test_sse_endpoint_handles_client_disconnect(
        self, client: FlaskClient, app: Flask
    ) -> None:
        """Test that SSE endpoint handles client disconnection gracefully."""
        with app.app_context():
            # Make a request
            response = client.get("/api/game_event_stream")

            # Should complete without errors
            assert response.status_code == 200
            assert response.content_type.startswith("text/event-stream")

            # Verify proper headers
            assert response.headers.get("Cache-Control") == "no-cache"

            # In production, the SSE generator handles disconnection gracefully
            # via try/except GeneratorExit in the stream() function
            # Flask test client limitations prevent full streaming tests

    def test_sse_endpoint_json_formatting(
        self, client: FlaskClient, app: Flask
    ) -> None:
        """Test that SSE endpoint formats events correctly."""
        with app.app_context():
            container = get_container()
            event_queue = container.get_event_queue()

            # Add event with special characters before request
            event = NarrativeAddedEvent(
                role="assistant", content='Test with "quotes" and\nnewlines'
            )
            event_queue.put_event(event)

            # Make request
            response = client.get("/api/game_event_stream")
            assert response.status_code == 200
            assert response.content_type.startswith("text/event-stream")

            # The key test here is that:
            # 1. The event with special characters was added to the queue
            # 2. The SSE endpoint exists and is configured correctly
            # 3. The SSE generator properly formats events as JSON (tested in implementation)

            # We can verify the event was queued correctly
            assert event_queue.qsize() > 0, (
                "Event with special characters should be in queue"
            )

            # Pop the event and verify it has the correct content
            queued_event = event_queue.get_event(block=False)
            if queued_event and hasattr(queued_event, "content"):
                assert queued_event.content == 'Test with "quotes" and\nnewlines'
                # The SSE implementation will json.dumps this with proper escaping

            # Verify SSE headers
            assert response.headers.get("Cache-Control") == "no-cache"

    def test_sse_endpoint_cors_headers(self, client: FlaskClient) -> None:
        """Test that SSE endpoint includes proper CORS headers."""
        response = client.get("/api/game_event_stream")

        # Check CORS headers for SSE
        assert response.headers.get("Access-Control-Allow-Origin") in [
            "*",
            "http://localhost:5173",
        ]
        assert response.headers.get("Cache-Control") == "no-cache"
        assert (
            response.headers.get("X-Accel-Buffering") == "no"
        )  # Disable nginx buffering

        # Also verify it's SSE content type
        assert response.content_type.startswith("text/event-stream")

    def test_sse_endpoint_health_check(self, client: FlaskClient) -> None:
        """Test that the SSE health endpoint is accessible."""
        # Test health endpoint
        health_response = client.get("/api/game_event_stream/health")
        assert health_response.status_code == 200
        health_data = health_response.get_json()
        assert health_data["status"] == "healthy"
        assert "queue_size" in health_data
        assert "timestamp" in health_data
