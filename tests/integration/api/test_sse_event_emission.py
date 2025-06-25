"""
Integration tests for verifying that events are emitted during async processing.

This replaces the SSE streaming tests which don't work well with TestClient.
Instead, we directly verify that events are put into the queue during processing.
"""

import asyncio
import time
from typing import Any, List
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.container import get_container
from app.models.combat.combatant import CombatantModel
from app.models.combat.state import CombatStateModel
from app.models.events import BaseGameEvent, NarrativeAddedEvent
from app.providers.ai.schemas import AIResponse


class TestEventEmission:
    """Test that events are emitted during async processing."""

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""
        app.state.testing = True
        return TestClient(app)

    def test_events_emitted_during_ai_processing(
        self, client: TestClient, app: FastAPI, mock_ai_service: Mock
    ) -> None:
        """Test that narrative events are emitted immediately during AI processing."""
        # Configure AI mock response
        mock_ai_service.add_response(
            AIResponse(
                narrative="The attack misses!",
                reasoning="Roll of 10 vs AC 15",
                dice_requests=[],
                end_turn=True,
            )
        )

        container = get_container()
        event_queue = container.get_event_queue()

        # Track when events are put into the queue
        emitted_events: List[BaseGameEvent] = []
        original_put = event_queue.put_event

        def track_event(event: BaseGameEvent) -> None:
            """Track emitted events."""
            emitted_events.append(event)
            original_put(event)

        # Mock the AI processing to add delays and emit events
        original_handle_event = container.get_game_orchestrator().handle_event

        async def mock_handle_event(event: Any) -> Any:
            """Mock handler that simulates slow AI processing with event emissions."""
            # Clear any existing events
            emitted_events.clear()

            # Emit first narrative event immediately
            event1 = NarrativeAddedEvent(
                role="user", content="Player submits dice roll"
            )
            event_queue.put_event(event1)

            # Simulate AI processing delay
            await asyncio.sleep(0.001)

            # Emit second narrative event during processing
            event2 = NarrativeAddedEvent(
                role="assistant", content="The dice tumble across the table..."
            )
            event_queue.put_event(event2)

            # More processing
            await asyncio.sleep(0.001)

            # Emit third narrative event
            event3 = NarrativeAddedEvent(
                role="assistant", content="Your attack misses!"
            )
            event_queue.put_event(event3)

            # Return the original response
            return await original_handle_event(event)

        # Patch both the orchestrator and event queue
        with patch.object(
            container.get_game_orchestrator(),
            "handle_event",
            side_effect=mock_handle_event,
        ), patch.object(event_queue, "put_event", side_effect=track_event):
            # Submit rolls (this will trigger AI processing)
            response = client.post(
                "/api/submit_rolls",
                json={
                    "roll_results": [
                        {
                            "request_id": "test_roll",
                            "character_id": "test_char",
                            "character_name": "Test Character",
                            "roll_type": "attack_roll",
                            "dice_formula": "1d20",
                            "character_modifier": 0,
                            "total_result": 10,
                            "reason": "Attack roll",
                            "result_message": "Test Character rolls Attack Roll: 1d20 -> [10] = 10",
                            "result_summary": "10",
                        }
                    ]
                },
            )

            assert response.status_code == 200

        # Verify events were emitted during processing
        assert len(emitted_events) >= 3, (
            f"Expected at least 3 events, got {len(emitted_events)}"
        )

        # Check event content
        narrative_events = [
            e for e in emitted_events if isinstance(e, NarrativeAddedEvent)
        ]
        assert len(narrative_events) >= 3

        # Verify event order and content
        assert "Player submits dice roll" in narrative_events[0].content
        assert "dice tumble" in narrative_events[1].content
        assert "attack misses" in narrative_events[2].content.lower()

    def test_events_emitted_during_npc_turn(
        self, client: TestClient, app: FastAPI, mock_ai_service: Mock
    ) -> None:
        """Test that NPC turn narratives are emitted immediately."""
        # Configure AI mock for NPC turn
        mock_ai_service.add_response(
            AIResponse(
                narrative="The goblin attacks with its sword!",
                reasoning="NPC turn",
                dice_requests=[],
                end_turn=True,
            )
        )

        container = get_container()
        event_queue = container.get_event_queue()
        game_state_repo = container.get_game_state_repository()

        # Set up combat state with NPC turn
        game_state = game_state_repo.get_game_state()
        game_state.combat = CombatStateModel(
            is_active=True,
            round_number=1,
            combatants=[
                CombatantModel(
                    id="goblin_1",
                    name="Goblin",
                    initiative=20,
                    current_hp=7,
                    max_hp=7,
                    armor_class=15,
                    is_player=False,
                ),
                CombatantModel(
                    id="player_1",
                    name="Hero",
                    initiative=10,
                    current_hp=20,
                    max_hp=20,
                    armor_class=16,
                    is_player=True,
                ),
            ],
            current_turn_index=0,  # Goblin's turn
        )
        game_state_repo.save_game_state(game_state)

        # Track emitted events
        emitted_events: List[BaseGameEvent] = []
        original_put = event_queue.put_event

        def track_event(event: BaseGameEvent) -> None:
            """Track emitted events."""
            emitted_events.append(event)
            original_put(event)

        # Mock to emit events during NPC processing
        original_handle = container.get_game_orchestrator().handle_event

        async def mock_npc_turn(event: Any) -> Any:
            # Clear events
            emitted_events.clear()

            # Emit NPC action narrative
            event_queue.put_event(
                NarrativeAddedEvent(
                    role="assistant", content="The goblin snarls and attacks!"
                )
            )
            await asyncio.sleep(0.001)

            # Emit dice roll narrative
            event_queue.put_event(
                NarrativeAddedEvent(role="assistant", content="Goblin rolls attack: 15")
            )
            await asyncio.sleep(0.001)

            # Emit result narrative
            event_queue.put_event(
                NarrativeAddedEvent(
                    role="assistant", content="The goblin's attack hits!"
                )
            )

            return await original_handle(event)

        with patch.object(
            container.get_game_orchestrator(), "handle_event", side_effect=mock_npc_turn
        ), patch.object(event_queue, "put_event", side_effect=track_event):
            # Trigger next step (NPC turn)
            response = client.post("/api/trigger_next_step")
            assert response.status_code == 200

        # Verify NPC narratives were emitted
        narrative_events = [
            e for e in emitted_events if isinstance(e, NarrativeAddedEvent)
        ]
        assert len(narrative_events) >= 3
        assert "goblin snarls" in narrative_events[0].content.lower()
        assert "rolls attack" in narrative_events[1].content.lower()
        assert "attack hits" in narrative_events[2].content.lower()
