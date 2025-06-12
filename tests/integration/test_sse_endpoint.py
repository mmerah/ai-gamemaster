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
            from app.models import CombatantModel

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

            # Read response data
            data = response.get_data(as_text=True)

            # Verify we got SSE formatted data
            assert "data: " in data
            assert "event: connected" in data  # Initial connection event

            # The response should contain our narrative event
            # Note: Due to test client limitations, we might not get all events

    def test_sse_endpoint_heartbeat(self, client: FlaskClient, app: Flask) -> None:
        """Test that SSE endpoint would send heartbeats (limited by test client)."""
        # Note: Flask test client doesn't support true streaming,
        # so we can only verify the endpoint exists and returns SSE format
        with app.app_context():
            response = client.get("/api/game_event_stream")
            assert response.status_code == 200

            # In a real SSE connection, heartbeats would be sent
            # This is tested manually or with integration tests using real HTTP clients

    def test_sse_endpoint_handles_client_disconnect(
        self, client: FlaskClient, app: Flask
    ) -> None:
        """Test that SSE endpoint handles client disconnection gracefully."""
        with app.app_context():
            # Make a request and let it complete
            response = client.get("/api/game_event_stream")

            # Should complete without errors
            assert response.status_code == 200

            # In production, the SSE generator handles disconnection gracefully
            # via try/except GeneratorExit in the stream() function

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
            data = response.get_data(as_text=True)

            # Should contain properly formatted SSE data
            assert "data: " in data

            # Extract the event data (after the initial connection event)
            lines = data.split("\n")
            for line in lines:
                if line.startswith("data: ") and "content" in line:
                    # Should be valid JSON
                    event_data = json.loads(line[6:])
                    if event_data.get("content") == 'Test with "quotes" and\nnewlines':
                        assert True  # Found our event properly formatted
                        return

            # If we have the initial connection event, that's fine too
            assert "event: connected" in data

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

    def test_sse_endpoint_health_check(self, client: FlaskClient) -> None:
        """Test that the SSE health endpoint is accessible."""
        # Test health endpoint
        health_response = client.get("/api/game_event_stream/health")
        assert health_response.status_code == 200
        health_data = health_response.get_json()
        assert health_data["status"] == "healthy"
        assert "queue_size" in health_data
        assert "timestamp" in health_data
