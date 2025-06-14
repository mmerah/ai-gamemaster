"""
Integration tests for ChatService and SSE event streaming.
Consolidated from test_chat_service_events_integration.py, test_sse_chat_events.py,
and test_phase3_e2e_verification.py.
"""

import json
import time
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.core.container import get_container


class TestChatAndSSEIntegration:
    """Test ChatService event emission and SSE streaming integration."""

    # Using the centralized app fixture from tests/conftest.py which includes proper AI mocking
    # The app fixture is automatically provided by pytest

    @pytest.fixture
    def client(self, app: Flask) -> FlaskClient:
        """Create a test client."""
        return app.test_client()

    def test_sse_streams_chat_events(self, app: Flask, client: FlaskClient) -> None:
        """Test that SSE endpoint streams events from ChatService."""
        with app.app_context():
            container = get_container()
            chat_service = container.get_chat_service()

            # Connect to SSE stream
            response = client.get(
                "/api/game_event_stream", headers={"Accept": "text/event-stream"}
            )
            assert response.status_code == 200

            # Read initial connection event
            data = b""
            for chunk in response.response:
                if isinstance(chunk, bytes):
                    data += chunk
                else:
                    data += chunk.encode("utf-8")
                if b"\n\n" in data:
                    break

            lines = data.decode("utf-8").strip().split("\n")
            assert any("connected" in line for line in lines)

            # Add a message which should trigger an event
            test_message = "The cave is very dark."
            chat_service.add_message("assistant", test_message)

            # Read the narrative event
            data = b""
            start_time = time.time()
            while time.time() - start_time < 2.0:  # 2 second timeout
                for chunk in response.response:
                    if isinstance(chunk, bytes):
                        data += chunk
                    else:
                        data += chunk.encode("utf-8")
                    if b"\n\n" in data:
                        break
                if b"narrative_added" in data:
                    break
                time.sleep(0.01)

            # Parse the event
            event_data = data.decode("utf-8")
            assert "data:" in event_data

            # Extract JSON from SSE data
            for line in event_data.split("\n"):
                if line.startswith("data:") and "narrative_added" in line:
                    json_str = line[5:].strip()  # Remove 'data:' prefix
                    event = json.loads(json_str)
                    assert event["event_type"] == "narrative_added"
                    assert event["content"] == test_message
                    assert event["role"] == "assistant"
                    break
            else:
                pytest.fail("narrative_added event not found in SSE stream")

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
            # Connect to SSE stream
            sse_response = client.get(
                "/api/game_event_stream", headers={"Accept": "text/event-stream"}
            )
            assert sse_response.status_code == 200

            # Skip connection event
            data = b""
            for chunk in sse_response.response:
                if isinstance(chunk, bytes):
                    data += chunk
                else:
                    data += chunk.encode("utf-8")
                if b"\n\n" in data:
                    break

            # Send player action
            action_response = client.post(
                "/api/player_action",
                json={"action_type": "free_text", "value": "I examine the cave"},
            )
            assert action_response.status_code == 200

            # Collect SSE events
            events: List[Dict[str, Any]] = []
            data = b""
            start_time = time.time()

            while time.time() - start_time < 3.0:  # 3 second timeout
                for chunk in sse_response.response:
                    if isinstance(chunk, bytes):
                        data += chunk
                    else:
                        data += chunk.encode("utf-8")
                    while b"\n\n" in data:
                        event_data, data = data.split(b"\n\n", 1)
                        event_str = event_data.decode("utf-8")

                        for line in event_str.split("\n"):
                            if line.startswith("data:") and "{" in line:
                                try:
                                    json_str = line[5:].strip()
                                    event = json.loads(json_str)
                                    events.append(event)
                                except json.JSONDecodeError:
                                    pass

                # Check if we have the events we need
                event_types = [e.get("event_type") for e in events]
                if "narrative_added" in event_types:
                    # Found our AI response event
                    break

                time.sleep(0.01)

            # Verify we got the expected events
            event_types = [e.get("event_type") for e in events]
            assert "narrative_added" in event_types, (
                f"Expected narrative_added in {event_types}"
            )

            # Find and verify the AI response
            for event in events:
                if (
                    event.get("event_type") == "narrative_added"
                    and event.get("role") == "assistant"
                ):
                    assert "glowing crystal" in event.get("content", "")
                    break
            else:
                pytest.fail("AI response narrative not found in events")
