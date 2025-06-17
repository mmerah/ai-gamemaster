"""
Test for PlayerDiceRequestsClearedEvent fix to ensure only specific submitted requests are cleared.
"""

from __future__ import annotations

from typing import List, Protocol

import pytest
from flask import Flask

# Use centralized app fixture from tests/conftest.py
from app.core.container import ServiceContainer, get_container
from app.core.event_queue import EventQueue
from app.core.interfaces import GameStateRepository
from app.models.character import CharacterInstanceModel
from app.models.dice import DiceRequestModel
from app.models.events import (
    BaseGameEvent,
    PlayerDiceRequestAddedEvent,
    PlayerDiceRequestsClearedEvent,
)
from app.providers.ai.schemas import AIResponse


class MockAIServiceProtocol(Protocol):
    """Protocol for mock AI service used in tests."""

    def add_response(self, response: AIResponse) -> None: ...


class TestPlayerDiceRequestsClearedFix:
    """Test the fix for PlayerDiceRequestsClearedEvent to only clear specific requests."""

    # Using the centralized app fixture from tests/conftest.py which includes proper AI mocking
    # The app fixture is automatically provided by pytest

    @pytest.fixture
    def container(self, app: Flask) -> ServiceContainer:
        """Get the service container."""
        with app.app_context():
            return get_container()

    def collect_events(self, container: ServiceContainer) -> List[BaseGameEvent]:
        """Collect all events from the event queue."""
        events = []
        event_queue: EventQueue = container.get_event_queue()

        while not event_queue.is_empty():
            event = event_queue.get_event(block=False)
            if event:
                events.append(event)

        return events

    def test_only_submitted_dice_requests_are_cleared(
        self, app: Flask, mock_ai_service: MockAIServiceProtocol
    ) -> None:
        """
        Test that PlayerDiceRequestsClearedEvent only contains the request IDs
        that were actually submitted, not all pending requests.
        """
        with app.test_request_context():
            with app.test_client() as client:
                # Setup: Create game state with two characters
                container = get_container()
                game_state_repo: GameStateRepository = (
                    container.get_game_state_repository()
                )
                game_state = game_state_repo.get_game_state()

                # Add two characters to party
                char1 = CharacterInstanceModel(
                    id="fighter",
                    name="Fighter",
                    template_id="fighter_template",
                    campaign_id="test_campaign",
                    level=1,
                    current_hp=20,
                    max_hp=20,
                    temp_hp=0,
                    experience_points=0,
                    spell_slots_used={},
                    hit_dice_used=0,
                    death_saves={"successes": 0, "failures": 0},
                    conditions=[],
                    inventory=[],
                    gold=0,
                    exhaustion_level=0,
                    notes="",
                    achievements=[],
                    relationships={},
                )
                char2 = CharacterInstanceModel(
                    id="wizard",
                    name="Wizard",
                    template_id="wizard_template",
                    campaign_id="test_campaign",
                    level=1,
                    current_hp=15,
                    max_hp=15,
                    temp_hp=0,
                    experience_points=0,
                    spell_slots_used={},
                    hit_dice_used=0,
                    death_saves={"successes": 0, "failures": 0},
                    conditions=[],
                    inventory=[],
                    gold=0,
                    exhaustion_level=0,
                    notes="",
                    achievements=[],
                    relationships={},
                )
                game_state.party["fighter"] = char1
                game_state.party["wizard"] = char2
                game_state_repo.save_game_state(game_state)

                # Configure mock AI to request dice rolls for both characters
                mock_ai_service.add_response(
                    AIResponse(
                        narrative="Both of you make perception checks!",
                        reasoning="Requesting perception checks",
                        dice_requests=[
                            DiceRequestModel(
                                request_id="roll_1",
                                character_ids=["fighter"],
                                type="ability_check",
                                dice_formula="1d20+2",
                                ability="wisdom",
                                reason="Perception check",
                            ),
                            DiceRequestModel(
                                request_id="roll_2",
                                character_ids=["wizard"],
                                type="ability_check",
                                dice_formula="1d20+3",
                                ability="wisdom",
                                reason="Perception check",
                            ),
                        ],
                        end_turn=False,
                    )
                )

                # Clear event queue
                event_queue: EventQueue = container.get_event_queue()
                event_queue.clear()

                # Trigger the AI to create dice requests
                response = client.post(
                    "/api/player_action",
                    json={"action_type": "free_text", "value": "We search the room"},
                )
                assert response.status_code == 200

                # Collect events and verify dice requests were added
                events = self.collect_events(container)
                dice_added_events = [
                    e for e in events if isinstance(e, PlayerDiceRequestAddedEvent)
                ]
                assert len(dice_added_events) == 2

                # Configure mock for AI response after dice submission
                mock_ai_service.add_response(
                    AIResponse(
                        narrative="The fighter notices a hidden door!",
                        reasoning="Processing perception results",
                        dice_requests=[],
                        end_turn=False,
                    )
                )

                # Clear event queue for next phase
                event_queue.clear()

                # Submit only ONE of the two dice rolls (fighter's roll only)
                response = client.post(
                    "/api/submit_rolls",
                    json=[
                        {
                            "character_id": "fighter",
                            "roll_type": "ability_check",
                            "dice_formula": "1d20+2",
                            "total": 17,
                            "request_id": "roll_1",  # Include the request ID
                        }
                    ],
                )
                assert response.status_code == 200

                # Collect events after submission
                events = self.collect_events(container)

                # Find the PlayerDiceRequestsClearedEvent
                cleared_events = [
                    e for e in events if isinstance(e, PlayerDiceRequestsClearedEvent)
                ]
                assert len(cleared_events) == 1, "Should have exactly one cleared event"

                cleared_event = cleared_events[0]

                # CRITICAL: The cleared event should only contain the submitted request ID
                assert len(cleared_event.cleared_request_ids) == 1, (
                    f"Should only clear the submitted request, got {cleared_event.cleared_request_ids}"
                )
                assert "roll_1" in cleared_event.cleared_request_ids, (
                    "Should contain the fighter's roll ID"
                )
                assert "roll_2" not in cleared_event.cleared_request_ids, (
                    "Should NOT contain the wizard's roll ID"
                )

                # Verify the wizard's request is still pending
                response_data = response.get_json()
                pending_requests = response_data.get("dice_requests", [])
                assert len(pending_requests) == 1, (
                    "Wizard's request should still be pending"
                )
                assert pending_requests[0]["request_id"] == "roll_2"

    def test_multiple_submissions_clear_correctly(
        self, app: Flask, mock_ai_service: MockAIServiceProtocol
    ) -> None:
        """Test that multiple dice submissions in one call clear all submitted IDs."""
        with app.test_request_context():
            with app.test_client() as client:
                # Setup similar to above
                container = get_container()
                game_state_repo: GameStateRepository = (
                    container.get_game_state_repository()
                )
                game_state = game_state_repo.get_game_state()

                # Add three characters
                for _, char_id in enumerate(["char1", "char2", "char3"]):
                    char = CharacterInstanceModel(
                        id=char_id,
                        name=char_id.title(),
                        template_id=f"{char_id}_template",
                        campaign_id="test_campaign",
                        level=1,
                        current_hp=20,
                        max_hp=20,
                        temp_hp=0,
                        experience_points=0,
                        spell_slots_used={},
                        hit_dice_used=0,
                        death_saves={"successes": 0, "failures": 0},
                        conditions=[],
                        inventory=[],
                        gold=0,
                        exhaustion_level=0,
                        notes="",
                        achievements=[],
                        relationships={},
                    )
                    game_state.party[char_id] = char
                game_state_repo.save_game_state(game_state)

                # Configure mock AI to request dice rolls for all three
                mock_ai_service.add_response(
                    AIResponse(
                        narrative="Everyone roll for initiative!",
                        reasoning="Starting combat",
                        dice_requests=[
                            DiceRequestModel(
                                request_id=f"init_{i}",
                                character_ids=[char_id],
                                type="initiative",
                                dice_formula="1d20",
                                reason="Initiative",
                            )
                            for i, char_id in enumerate(["char1", "char2", "char3"])
                        ],
                        end_turn=False,
                    )
                )

                # Trigger dice requests
                response = client.post(
                    "/api/player_action",
                    json={"action_type": "free_text", "value": "Attack!"},
                )
                assert response.status_code == 200

                # Configure mock for AI response after dice submission
                mock_ai_service.add_response(
                    AIResponse(
                        narrative="Combat order determined!",
                        reasoning="Processing initiative",
                        dice_requests=[],
                        end_turn=False,
                    )
                )

                # Clear event queue
                event_queue: EventQueue = container.get_event_queue()
                event_queue.clear()

                # Submit two out of three rolls
                response = client.post(
                    "/api/submit_rolls",
                    json=[
                        {
                            "character_id": "char1",
                            "roll_type": "initiative",
                            "dice_formula": "1d20",
                            "total": 15,
                            "request_id": "init_0",  # Include the request ID
                        },
                        {
                            "character_id": "char3",
                            "roll_type": "initiative",
                            "dice_formula": "1d20",
                            "total": 8,
                            "request_id": "init_2",  # Include the request ID
                        },
                    ],
                )
                assert response.status_code == 200

                # Collect and verify cleared event
                events = self.collect_events(container)
                cleared_events = [
                    e for e in events if isinstance(e, PlayerDiceRequestsClearedEvent)
                ]
                assert len(cleared_events) == 1

                cleared_event = cleared_events[0]
                assert len(cleared_event.cleared_request_ids) == 2
                assert "init_0" in cleared_event.cleared_request_ids  # char1's roll
                assert "init_2" in cleared_event.cleared_request_ids  # char3's roll
                assert (
                    "init_1" not in cleared_event.cleared_request_ids
                )  # char2's roll NOT cleared
