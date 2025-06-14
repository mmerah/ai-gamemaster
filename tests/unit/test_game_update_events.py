"""
Unit tests for game update event models.
Following TDD - tests written before implementation.
"""

import json
from datetime import datetime, timezone
from uuid import UUID


class TestBaseGameUpdateEvent:
    """Test the base game update event model."""

    def test_base_event_has_required_fields(self) -> None:
        """All events must have core identification fields."""
        # This test will fail until we implement BaseGameUpdateEvent
        from app.models.events import BaseGameEvent

        # Create event with minimal data
        event = BaseGameEvent(event_type="test_event")

        # Assert required fields exist
        assert hasattr(event, "event_id")
        assert hasattr(event, "timestamp")
        assert hasattr(event, "sequence_number")
        assert hasattr(event, "event_type")
        assert hasattr(event, "correlation_id")

    def test_event_id_is_unique_uuid(self) -> None:
        """Each event should have a unique UUID."""
        from app.models.events import BaseGameEvent

        event1 = BaseGameEvent(event_type="test")
        event2 = BaseGameEvent(event_type="test")

        # Event IDs should be valid UUIDs
        assert isinstance(UUID(event1.event_id), UUID)
        assert isinstance(UUID(event2.event_id), UUID)

        # Event IDs should be unique
        assert event1.event_id != event2.event_id

    def test_timestamp_auto_generated(self) -> None:
        """Timestamp should be automatically set to current time."""
        from app.models.events import BaseGameEvent

        before = datetime.now(timezone.utc)
        event = BaseGameEvent(event_type="test")
        after = datetime.now(timezone.utc)

        # Timestamp should be between test boundaries
        assert before <= event.timestamp <= after

    def test_sequence_number_increments(self) -> None:
        """Sequence numbers should increment globally."""
        from app.models.events import BaseGameEvent

        event1 = BaseGameEvent(event_type="test")
        event2 = BaseGameEvent(event_type="test")
        event3 = BaseGameEvent(event_type="test")

        # Sequence numbers should increment
        assert event2.sequence_number == event1.sequence_number + 1
        assert event3.sequence_number == event2.sequence_number + 1

    def test_correlation_id_optional(self) -> None:
        """Correlation ID should be optional."""
        from app.models.events import BaseGameEvent

        # Without correlation ID
        event1 = BaseGameEvent(event_type="test")
        assert event1.correlation_id is None

        # With correlation ID
        event2 = BaseGameEvent(event_type="test", correlation_id="combat_123")
        assert event2.correlation_id == "combat_123"

    def test_event_serialization_to_json(self) -> None:
        """Events must be JSON serializable for SSE."""
        from app.models.events import BaseGameEvent

        event = BaseGameEvent(
            event_type="test_event", correlation_id="test_correlation"
        )

        # Should serialize to JSON without errors
        json_str = event.model_dump_json()
        assert isinstance(json_str, str)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["event_type"] == "test_event"
        assert parsed["correlation_id"] == "test_correlation"
        assert "event_id" in parsed
        assert "timestamp" in parsed
        assert "sequence_number" in parsed


class TestSpecificGameEvents:
    """Test specific game event types."""

    def test_narrative_added_event(self) -> None:
        """Test narrative event structure."""
        from app.models.events import NarrativeAddedEvent

        event = NarrativeAddedEvent(
            role="assistant",
            content="The goblin attacks!",
            gm_thought="Rolling for goblin attack",
            audio_path="/static/audio/narration_123.mp3",
        )

        assert event.event_type == "narrative_added"
        assert event.role == "assistant"
        assert event.content == "The goblin attacks!"
        assert event.gm_thought == "Rolling for goblin attack"
        assert event.audio_path == "/static/audio/narration_123.mp3"

    def test_combat_started_event(self) -> None:
        """Test combat start event structure."""
        from app.models.combat import CombatantModel
        from app.models.events import CombatStartedEvent

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=15,
                current_hp=20,
                max_hp=20,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=12,
                current_hp=7,
                max_hp=7,
                armor_class=15,
                is_player=False,
            ),
        ]

        event = CombatStartedEvent(combatants=combatants, round_number=1)

        assert event.event_type == "combat_started"
        assert len(event.combatants) == 2
        assert event.round_number == 1

    def test_combatant_hp_changed_event(self) -> None:
        """Test HP change event structure."""
        from app.models.events import CombatantHpChangedEvent

        event = CombatantHpChangedEvent(
            combatant_id="pc_1",
            combatant_name="Elara",
            old_hp=20,
            new_hp=15,
            max_hp=20,
            change_amount=-5,
            is_player=True,
            source="Goblin attack",
        )

        assert event.event_type == "combatant_hp_changed"
        assert event.combatant_id == "pc_1"
        assert event.old_hp == 20
        assert event.new_hp == 15
        assert event.change_amount == -5
        assert event.source == "Goblin attack"

    def test_dice_roll_events(self) -> None:
        """Test dice roll event structures."""
        from app.models.events import (
            NpcDiceRollProcessedEvent,
            PlayerDiceRequestAddedEvent,
        )

        # Player dice request
        player_event = PlayerDiceRequestAddedEvent(
            request_id="req_123",
            character_id="pc_1",
            character_name="Elara",
            roll_type="attack",
            dice_formula="1d20+5",
            purpose="Attack goblin",
            dc=15,
        )

        assert player_event.event_type == "player_dice_request_added"
        assert player_event.request_id == "req_123"
        assert player_event.dice_formula == "1d20+5"

        # NPC dice roll
        npc_event = NpcDiceRollProcessedEvent(
            character_id="goblin_1",
            character_name="Goblin",
            roll_type="attack",
            dice_formula="1d20+4",
            total=18,
            details="1d20+4: [14] + 4 = 18",
            success=True,
            purpose="Attack Elara",
        )

        assert npc_event.event_type == "npc_dice_roll_processed"
        assert npc_event.total == 18
        assert npc_event.success is True

    def test_turn_advanced_event(self) -> None:
        """Test turn advancement event."""
        from app.models.events import TurnAdvancedEvent

        event = TurnAdvancedEvent(
            new_combatant_id="pc_2",
            new_combatant_name="Thorin",
            round_number=1,
            is_new_round=False,
            is_player=True,
        )

        assert event.event_type == "turn_advanced"
        assert event.new_combatant_id == "pc_2"
        assert event.is_new_round is False

    def test_backend_processing_event(self) -> None:
        """Test backend processing status event."""
        from app.models.events import BackendProcessingEvent

        # Processing started
        event1 = BackendProcessingEvent(is_processing=True, needs_backend_trigger=False)

        assert event1.event_type == "backend_processing"
        assert event1.is_processing is True

        # Processing complete, needs trigger
        event2 = BackendProcessingEvent(
            is_processing=False, needs_backend_trigger=True, trigger_reason="NPC turn"
        )

        assert event2.is_processing is False
        assert event2.needs_backend_trigger is True
        assert event2.trigger_reason == "NPC turn"

    def test_game_error_event(self) -> None:
        """Test error event structure."""
        from app.models.events import GameErrorEvent

        event = GameErrorEvent(
            error_message="Failed to process AI response",
            error_type="ai_service_error",
            error_code="AI_PARSE_ERROR",
            recoverable=True,
        )

        assert event.event_type == "game_error"
        assert event.error_message == "Failed to process AI response"
        assert event.error_type == "ai_service_error"
        assert event.error_code == "AI_PARSE_ERROR"
        assert event.recoverable is True
        # No is_retryable property in unified model


class TestEventInheritance:
    """Test that all events properly inherit from base."""

    def test_all_events_inherit_base_fields(self) -> None:
        """All specific events should have base event fields."""
        from app.models.events import (
            BaseGameEvent,
            CombatantHpChangedEvent,
            CombatStartedEvent,
            NarrativeAddedEvent,
        )

        # Test a few event types
        events = [
            NarrativeAddedEvent(role="user", content="test"),
            CombatStartedEvent(combatants=[], round_number=1),
            CombatantHpChangedEvent(
                combatant_id="test",
                combatant_name="Test",
                old_hp=10,
                new_hp=5,
                max_hp=10,
                change_amount=-5,
            ),
        ]

        for event in events:
            # Should have all base fields
            assert hasattr(event, "event_id")
            assert hasattr(event, "timestamp")
            assert hasattr(event, "sequence_number")
            assert hasattr(event, "event_type")
            assert hasattr(event, "correlation_id")

            # Should be instance of base class
            assert isinstance(event, BaseGameEvent)


class TestEventRegistry:
    """Test event type registry functionality."""

    def test_event_registry(self) -> None:
        """Test that event types can be looked up dynamically."""
        from app.events.definitions import get_event_class_by_type

        # Test a few event types
        narrative_class = get_event_class_by_type("narrative_added")
        assert narrative_class is not None
        assert narrative_class.__name__ == "NarrativeAddedEvent"

        combat_class = get_event_class_by_type("combat_started")
        assert combat_class is not None
        assert combat_class.__name__ == "CombatStartedEvent"

        # Test non-existent type
        assert get_event_class_by_type("non_existent_event") is None
