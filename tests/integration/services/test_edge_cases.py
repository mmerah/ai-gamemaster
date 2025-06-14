"""
Integration tests for edge cases and unique scenarios not covered by comprehensive backend tests.
Consolidated from various other test files to reduce redundancy.
"""

from typing import Generator, cast
from unittest.mock import Mock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.core.container import ServiceContainer
from app.models.character import CharacterInstanceModel
from app.models.combat import CombatantModel, CombatStateModel
from app.models.dice import DiceRequestModel
from app.models.events import (
    BaseGameEvent,
    CombatantRemovedEvent,
    CombatStartedEvent,
    GameErrorEvent,
    GameStateSnapshotEvent,
    NarrativeAddedEvent,
    PlayerDiceRequestsClearedEvent,
)
from app.models.updates import CombatantRemoveUpdateModel
from app.models.utils import LocationModel
from app.providers.ai.schemas import AIResponse
from tests.test_helpers import EventRecorder


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios."""

    @pytest.fixture
    def client(self, app: Flask) -> FlaskClient:
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def container(self, app: Flask) -> Generator[ServiceContainer, None, None]:
        """Get service container."""
        with app.app_context():
            from app.core.container import get_container

            yield get_container()

    def test_error_handling_and_recovery(
        self,
        client: FlaskClient,
        container: ServiceContainer,
        monkeypatch: pytest.MonkeyPatch,
        app: Flask,
        mock_ai_service: Mock,
    ) -> None:
        """Test that the system handles errors gracefully and emits error events."""
        # Set up mock AI service to fail
        mock_ai_service.get_structured_response.side_effect = Exception(
            "API rate limit reached"
        )
        mock_ai_service.get_response.side_effect = Exception("API rate limit reached")

        # Set up event recording
        recorder = EventRecorder()
        event_queue = container.get_event_queue()
        original_put = event_queue.put_event

        def record_and_emit(event: BaseGameEvent) -> None:
            recorder.record_event(event)
            return original_put(event)

        monkeypatch.setattr(event_queue, "put_event", record_and_emit)

        # Send player action that will trigger AI error
        response = client.post(
            "/api/player_action",
            json={"action_type": "free_text", "value": "I attack the goblin!"},
        )

        # Should get response with 500 status code
        # The error is handled within the handler and returns frontend data with status 500
        assert response.status_code == 500
        data = response.json
        # Check that the error was added to chat history
        assert data is not None
        assert "chat_history" in data
        assert any(
            "Error processing AI step" in msg["content"] for msg in data["chat_history"]
        )

        # Should emit error event
        error_events = recorder.get_events_by_type("game_error")
        assert len(error_events) > 0
        error_event = cast(GameErrorEvent, error_events[0])
        assert "API rate limit" in error_event.error_message

        # Test retry functionality
        mock_ai_service.get_structured_response.side_effect = None
        mock_ai_service.get_response.side_effect = None
        mock_ai_service.get_structured_response.return_value = AIResponse(
            narrative="You swing your sword at the goblin!", game_state_updates=[]
        )
        mock_ai_service.get_response.return_value = AIResponse(
            narrative="You swing your sword at the goblin!", game_state_updates=[]
        )

        # Retry should work
        retry_response = client.post("/api/retry_last_ai_request")
        assert retry_response.status_code == 200
        # The response does not have a 'success' field, check for no error instead
        retry_data = retry_response.json
        assert retry_data is not None
        assert "error" not in retry_data

        # Note: In this error scenario, no assistant message was created initially,
        # so there's no message to supersede. The superseded event only happens
        # when retrying after a successful AI response.

        # Should emit narrative after successful retry
        narrative_events = recorder.get_events_by_type("narrative_added")
        assert any(
            "swing your sword" in cast(NarrativeAddedEvent, e).content
            for e in narrative_events
        )

    def test_retry_supersedes_previous_message(
        self,
        client: FlaskClient,
        container: ServiceContainer,
        monkeypatch: pytest.MonkeyPatch,
        app: Flask,
        mock_ai_service: Mock,
    ) -> None:
        """Test that retrying a successful AI response marks the previous message as superseded."""
        # Configure mock AI responses
        mock_ai_service.add_response(
            AIResponse(
                narrative="You find a hidden compartment in the wall.",
                reasoning="Searching the room",
                dice_requests=[],
                end_turn=False,
            )
        )
        # Add response for retry
        mock_ai_service.add_response(
            AIResponse(
                narrative="Upon closer inspection, you discover a secret door!",
                reasoning="Retrying search",
                dice_requests=[],
                end_turn=False,
            )
        )
        # Set up event recording
        recorder = EventRecorder()
        event_queue = container.get_event_queue()
        original_put = event_queue.put_event

        def record_and_emit(event: BaseGameEvent) -> None:
            recorder.record_event(event)
            return original_put(event)

        monkeypatch.setattr(event_queue, "put_event", record_and_emit)

        # First, send a successful player action
        response = client.post(
            "/api/player_action",
            json={"action_type": "free_text", "value": "I search the room"},
        )

        assert response.status_code == 200

        # Find the AI response message
        narrative_events = recorder.get_events_by_type("narrative_added")
        ai_messages = [
            e
            for e in narrative_events
            if cast(NarrativeAddedEvent, e).role == "assistant"
        ]
        assert len(ai_messages) > 0, "Expected at least one AI message"
        original_message_id = cast(NarrativeAddedEvent, ai_messages[-1]).message_id

        # Now retry the action
        retry_response = client.post("/api/retry_last_ai_request")
        assert retry_response.status_code == 200

        # Should emit message_superseded event for the previous message
        superseded_events = recorder.get_events_by_type("message_superseded")
        assert len(superseded_events) > 0, (
            "Expected at least one message_superseded event"
        )
        # Import MessageSupersededEvent type
        from app.models.events import MessageSupersededEvent

        superseded_event = cast(MessageSupersededEvent, superseded_events[0])
        assert superseded_event.message_id == original_message_id
        assert superseded_event.reason == "retry"

        # Should also have a new narrative message
        new_narrative_events = recorder.get_events_by_type("narrative_added")
        new_ai_messages = [
            e
            for e in new_narrative_events
            if cast(NarrativeAddedEvent, e).role == "assistant"
        ]
        assert len(new_ai_messages) > len(ai_messages), (
            "Expected a new AI message after retry"
        )

    def test_state_snapshot_for_reconnection(
        self, client: FlaskClient, container: ServiceContainer
    ) -> None:
        """Test that state snapshots are generated for client reconnection."""
        # Initialize game state with party members
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()

        # Add party members
        game_state.party = {
            "test_member": CharacterInstanceModel(
                template_id="test_template",
                campaign_id="test_campaign",
                current_hp=20,
                max_hp=20,
                level=1,
            )
        }
        # Set location
        game_state.current_location = LocationModel(
            name="Test Location", description="A test location"
        )
        game_state_repo.save_game_state(game_state)

        recorder = EventRecorder()
        event_queue = container.get_event_queue()

        original_put = event_queue.put_event

        def record_and_emit(event: BaseGameEvent) -> None:
            recorder.record_event(event)
            return original_put(event)

        with patch.object(event_queue, "put_event", side_effect=record_and_emit):
            # Request state snapshot
            response = client.get("/api/game_state?emit_snapshot=true")
            assert response.status_code == 200

            # Should emit snapshot event
            snapshot_events = recorder.get_events_by_type("game_state_snapshot")
            assert len(snapshot_events) == 1

            snapshot = cast(GameStateSnapshotEvent, snapshot_events[0])
            # Combat state can be None if no combat is active
            assert hasattr(snapshot, "combat_state")
            # Check that snapshot contains expected data
            assert hasattr(snapshot, "party_members")
            # The party_members field may be a list representation of the party dict
            # Just verify the snapshot was created successfully
            assert snapshot.location is not None
            assert snapshot.active_quests is not None


class TestCombatEdgeCases:
    """Test combat edge cases not covered by basic scenarios."""

    # Using the centralized app fixture from tests/conftest.py which includes proper AI mocking
    # The app fixture is automatically provided by pytest

    @pytest.fixture
    def container(self, app: Flask) -> Generator[ServiceContainer, None, None]:
        """Get service container."""
        with app.app_context():
            from app.core.container import get_container

            yield get_container()

    def test_combatant_removed_event(self, container: ServiceContainer) -> None:
        """Test that combatants can be removed (flee/escape)."""
        recorder = EventRecorder()
        event_queue = container.get_event_queue()

        # Set up combat with some combatants
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=[
                CombatantModel(
                    id="pc_1",
                    name="Hero",
                    initiative=20,
                    current_hp=25,
                    max_hp=25,
                    armor_class=16,
                    is_player=True,
                ),
                CombatantModel(
                    id="goblin_1",
                    name="Goblin",
                    initiative=15,
                    current_hp=7,
                    max_hp=7,
                    armor_class=13,
                    is_player=False,
                ),
                CombatantModel(
                    id="goblin_2",
                    name="Fleeing Goblin",
                    initiative=10,
                    current_hp=5,
                    max_hp=7,
                    armor_class=13,
                    is_player=False,
                ),
            ],
        )
        game_state_repo.save_game_state(game_state)

        original_put = event_queue.put_event

        def record_and_emit(event: BaseGameEvent) -> None:
            recorder.record_event(event)
            return original_put(event)

        with patch.object(event_queue, "put_event", side_effect=record_and_emit):
            # Mock AI response with combatant removal
            ai_response_processor = container.get_ai_response_processor()
            mock_response = AIResponse(
                narrative="The wounded goblin flees in terror!",
                combatant_removals=[
                    CombatantRemoveUpdateModel(character_id="goblin_2", reason="fled")
                ],
            )

            # Process the response
            ai_response_processor.process_response(mock_response, "player_action")

            # Verify combatant removed event
            removed_events = recorder.get_events_by_type("combatant_removed")
            assert len(removed_events) == 1
            removed_event = cast(CombatantRemovedEvent, removed_events[0])
            assert removed_event.combatant_id == "goblin_2"
            assert removed_event.reason == "fled"

            # Verify combatant actually removed from state
            updated_state = game_state_repo.get_game_state()
            assert len(updated_state.combat.combatants) == 2
            assert not any(c.id == "goblin_2" for c in updated_state.combat.combatants)

    def test_player_dice_requests_cleared_event(
        self, container: ServiceContainer
    ) -> None:
        """Test that dice requests are properly cleared after submission."""
        recorder = EventRecorder()
        event_queue = container.get_event_queue()

        # Set up game state with pending dice requests
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()
        game_state.pending_player_dice_requests = [
            DiceRequestModel(
                request_id="req_1",
                character_ids=["pc_1"],
                type="attack",
                dice_formula="1d20+5",
                reason="Attack roll",
            )
        ]
        game_state_repo.save_game_state(game_state)

        original_put = event_queue.put_event

        def record_and_emit(event: BaseGameEvent) -> None:
            recorder.record_event(event)
            return original_put(event)

        with patch.object(event_queue, "put_event", side_effect=record_and_emit):
            # Submit dice roll results
            game_orchestrator = container.get_game_orchestrator()
            from app.models.dice import DiceRollResultResponseModel

            game_orchestrator.handle_completed_roll_submission(
                [
                    DiceRollResultResponseModel(
                        request_id="req_1",
                        character_id="pc_1",
                        character_name="Hero",
                        roll_type="attack",
                        dice_formula="1d20+5",
                        character_modifier=5,
                        total_result=23,
                        reason="Attack roll",
                        result_message="Hero rolls Attack: 1d20+5 -> [18] + 5 = **23**.",
                        result_summary="Attack: 23",
                    )
                ]
            )

            # Verify dice requests cleared event
            cleared_events = recorder.get_events_by_type("player_dice_requests_cleared")
            assert len(cleared_events) == 1
            cleared_event = cast(PlayerDiceRequestsClearedEvent, cleared_events[0])
            assert len(cleared_event.cleared_request_ids) == 1

            # Verify requests actually cleared
            updated_state = game_state_repo.get_game_state()
            assert len(updated_state.pending_player_dice_requests) == 0
