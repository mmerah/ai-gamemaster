"""
Test helper utilities to ensure proper test isolation.
"""

import os
import sys
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional, Type
from unittest import TestCase


def ensure_clean_imports() -> None:
    """
    Ensure clean imports by removing potentially problematic modules.
    This helps avoid the '_has_torch_function' error when tests reload modules.
    """
    # Modules that can cause issues when reloaded
    problematic_modules = [
        "torch",
        "numpy",
        "transformers",
        "sentence_transformers",
        "kokoro",
        "app.services.rag.knowledge_bases",
        "app.tts_services.kokoro_service",
    ]

    # Get current module names to avoid modifying dict during iteration
    current_modules = list(sys.modules.keys())

    for module in current_modules:
        # Remove problematic modules and their submodules
        for prob_module in problematic_modules:
            if module == prob_module or module.startswith(prob_module + "."):
                sys.modules.pop(module, None)


def setup_test_environment() -> None:
    """
    Set up a clean test environment with proper configuration.
    """
    # Set environment variables before any imports
    os.environ["RAG_ENABLED"] = "false"
    os.environ["TTS_PROVIDER"] = "disabled"

    # Clean up any previously imported modules
    ensure_clean_imports()


class IsolatedTestCase(TestCase):
    """
    Mixin for test cases that need proper isolation from ML dependencies.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level test isolation."""
        setup_test_environment()
        super().setUpClass()

    def setUp(self) -> None:
        """Set up test-level isolation."""
        # Ensure environment is clean for each test
        os.environ["RAG_ENABLED"] = "false"
        os.environ["TTS_PROVIDER"] = "disabled"
        super().setUp()


# Import event types only after ensuring clean environment
from app.ai_services.schemas import AIResponse
from app.core.event_queue import EventQueue
from app.models.events import BaseGameEvent
from app.models.models import CharacterInstanceModel, GameStateModel


class EventRecorder:
    """
    Records events for testing purposes.
    Allows inspection of event sequences and validation of event data.
    """

    def __init__(self) -> None:
        self.events: List[BaseGameEvent] = []
        self._enabled = True

    def record_event(self, event: BaseGameEvent) -> None:
        """Record an event if recording is enabled."""
        if self._enabled and isinstance(event, BaseGameEvent):
            self.events.append(event)

    def get_events(self) -> List[BaseGameEvent]:
        """Get all recorded events."""
        return self.events.copy()

    def get_events_by_type(self, event_type: str) -> List[BaseGameEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def get_event_types(self) -> List[str]:
        """Get the sequence of event types in order."""
        return [e.event_type for e in self.events]

    def get_latest_event(
        self, event_type: Optional[str] = None
    ) -> Optional[BaseGameEvent]:
        """Get the most recent event, optionally filtered by type."""
        if event_type:
            filtered = self.get_events_by_type(event_type)
            return filtered[-1] if filtered else None
        return self.events[-1] if self.events else None

    def has_event_type(self, event_type: str) -> bool:
        """Check if any event of the given type was recorded."""
        return any(e.event_type == event_type for e in self.events)

    def count_events(self, event_type: Optional[str] = None) -> int:
        """Count events, optionally filtered by type."""
        if event_type:
            return len(self.get_events_by_type(event_type))
        return len(self.events)

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()

    def disable(self) -> None:
        """Disable event recording."""
        self._enabled = False

    def enable(self) -> None:
        """Enable event recording."""
        self._enabled = True

    def assert_event_sequence(self, expected_types: List[str]) -> None:
        """Assert that events occurred in the expected sequence."""
        actual_types = self.get_event_types()
        assert actual_types == expected_types, (
            f"Event sequence mismatch:\n"
            f"Expected: {expected_types}\n"
            f"Actual:   {actual_types}"
        )

    def assert_event_count(self, event_type: str, expected_count: int) -> None:
        """Assert that a specific number of events of a type occurred."""
        actual_count = self.count_events(event_type)
        assert actual_count == expected_count, (
            f"Expected {expected_count} '{event_type}' events, but found {actual_count}"
        )

    def find_event_with_data(
        self, event_type: str, **kwargs: Any
    ) -> Optional[BaseGameEvent]:
        """Find an event of a type with specific attribute values."""
        for event in self.get_events_by_type(event_type):
            match = True
            for key, value in kwargs.items():
                if not hasattr(event, key) or getattr(event, key) != value:
                    match = False
                    break
            if match:
                return event
        return None

    def find_all_events_with_data(
        self, event_type: str, **kwargs: Any
    ) -> List[BaseGameEvent]:
        """Find all events of a type with specific attribute values."""
        matching_events = []
        for event in self.get_events_by_type(event_type):
            match = True
            for key, value in kwargs.items():
                if not hasattr(event, key) or getattr(event, key) != value:
                    match = False
                    break
            if match:
                matching_events.append(event)
        return matching_events

    def get_events_of_type(
        self, event_class: Type[BaseGameEvent]
    ) -> List[BaseGameEvent]:
        """Get all events of a specific class type."""
        return [e for e in self.events if isinstance(e, event_class)]

    def get_all_events(self) -> List[BaseGameEvent]:
        """Get all recorded events."""
        return self.events.copy()

    def has_gaps(self) -> bool:
        """Check if there are gaps in sequence numbers (indicating dropped events)."""
        if len(self.events) < 2:
            return False

        sequence_numbers = [
            e.sequence_number for e in self.events if hasattr(e, "sequence_number")
        ]
        if not sequence_numbers:
            return False

        sequence_numbers.sort()
        for i in range(1, len(sequence_numbers)):
            if sequence_numbers[i] - sequence_numbers[i - 1] > 1:
                return True
        return False

    def attach_to_queue(self, event_queue: EventQueue) -> None:
        """Attach recorder to an event queue to automatically record events."""
        # Monkey patch the put_event method
        original_put = event_queue.put_event

        def recording_put(event: BaseGameEvent) -> Any:
            self.record_event(event)
            return original_put(event)

        event_queue.put_event = recording_put  # type: ignore[method-assign]

    @contextmanager
    def capture_events(self, event_queue: EventQueue) -> Iterator["EventRecorder"]:
        """Context manager to capture events from an event queue."""
        # Subscribe to all events
        subscription_id = event_queue.subscribe_all(self.record_event)

        try:
            yield self
        finally:
            # Unsubscribe
            event_queue.unsubscribe(subscription_id)

    def assert_backend_processing_pattern(self) -> None:
        """Assert that BackendProcessingEvent follows the expected first=True, last=False pattern."""
        if not self.events:
            return

        backend_events = self.get_events_by_type("backend_processing")
        if len(backend_events) < 2:
            # Should have at least start and end events for any AI processing
            assert len(backend_events) == 0, (
                "BackendProcessingEvent should come in pairs (start=True, end=False)"
            )
            return

        # Should be an even number (pairs of start/end)
        assert len(backend_events) % 2 == 0, (
            f"BackendProcessingEvent should come in pairs, got {len(backend_events)}"
        )

        # Check that they alternate True/False correctly
        for i in range(0, len(backend_events), 2):
            start_event = backend_events[i]
            end_event = backend_events[i + 1]

            assert hasattr(start_event, "is_processing"), (
                "BackendProcessingEvent should have is_processing attribute"
            )
            assert hasattr(end_event, "is_processing"), (
                "BackendProcessingEvent should have is_processing attribute"
            )

            assert start_event.is_processing is True, (
                f"Expected is_processing=True for start event {i // 2 + 1}"
            )
            assert end_event.is_processing is False, (
                f"Expected is_processing=False for end event {i // 2 + 1}"
            )

    def assert_first_last_events(self, first_type: str, last_type: str) -> None:
        """Assert that the first and last events are of specific types."""
        assert len(self.events) > 0, "No events recorded"
        assert self.events[0].event_type == first_type, (
            f"Expected first event to be '{first_type}', got '{self.events[0].event_type}'"
        )
        assert self.events[-1].event_type == last_type, (
            f"Expected last event to be '{last_type}', got '{self.events[-1].event_type}'"
        )

    def get_event_subsequence(
        self, start_index: int, end_index: Optional[int] = None
    ) -> List[BaseGameEvent]:
        """Get a subsequence of events by index range."""
        return self.events[start_index:end_index]

    def assert_event_present_with_data(
        self, event_type: str, **kwargs: Any
    ) -> BaseGameEvent:
        """Assert that an event of the specified type with specific data exists, and return it."""
        event = self.find_event_with_data(event_type, **kwargs)
        assert event is not None, (
            f"Expected {event_type} event with data {kwargs} not found"
        )
        return event

    def replay_events(
        self,
        handler_func: Callable[[BaseGameEvent], None],
        delay: float = 0.0,
        filter_types: Optional[List[str]] = None,
    ) -> None:
        """
        Replay recorded events through a handler function.

        Args:
            handler_func: Function to call with each event
            delay: Optional delay between events (seconds)
            filter_types: Optional list of event types to replay (None = all)
        """
        import time

        events_to_replay = self.events
        if filter_types:
            events_to_replay = [e for e in self.events if e.event_type in filter_types]

        for event in events_to_replay:
            handler_func(event)
            if delay > 0:
                time.sleep(delay)

    def save_to_file(self, filepath: str) -> None:
        """Save recorded events to a JSON file for later replay."""
        import json

        events_data = []
        for event in self.events:
            events_data.append(
                {"event_type": event.event_type, "data": event.model_dump()}
            )

        with open(filepath, "w") as f:
            json.dump(events_data, f, indent=2, default=str)

    def load_from_file(self, filepath: str) -> None:
        """Load events from a JSON file."""
        import json

        from app.events.game_update_events import get_event_class_by_type

        with open(filepath) as f:
            events_data = json.load(f)

        self.clear()
        for event_data in events_data:
            event_type = event_data["event_type"]
            event_class = get_event_class_by_type(event_type)
            if event_class:
                event = event_class(**event_data["data"])
                self.record_event(event)


def create_mock_game_state(
    combat_active: bool = False,
    combatants: Optional[List[Dict[str, Any]]] = None,
    current_turn_index: int = 0,
    round_number: int = 1,
    party: Optional[Dict[str, CharacterInstanceModel]] = None,
) -> GameStateModel:
    """Create a mock game state for testing."""
    from app.models.models import (
        CombatantModel,
        CombatStateModel,
        GameStateModel,
        LocationModel,
    )

    # Create combat state
    combat_state = CombatStateModel(
        is_active=combat_active,
        combatants=[],
        current_turn_index=current_turn_index,
        round_number=round_number,
    )

    if combatants:
        for c in combatants:
            combatant = CombatantModel(**c)
            combat_state.combatants.append(combatant)

    # Create game state
    game_state = GameStateModel(
        campaign_id="test_campaign",
        party=party or {},
        current_location=LocationModel(
            name="Test Location", description="A test location"
        ),
        chat_history=[],
        pending_player_dice_requests=[],
        combat=combat_state,
    )

    return game_state


def create_mock_ai_response(
    narrative: str = "Test narrative",
    dice_requests: Optional[List[Dict[str, Any]]] = None,
    game_state_updates: Optional[List[Any]] = None,
    end_turn: bool = False,
    location_update: Optional[Dict[str, Any]] = None,
) -> AIResponse:
    """Create a mock AI response for testing."""
    from app.ai_services.schemas import AIResponse
    from app.models.models import DiceRequestModel
    from app.models.updates import LocationUpdateModel

    # Create actual AIResponse object
    ai_response = AIResponse(
        narrative=narrative,
        reasoning="Test reasoning",
        dice_requests=[],
        end_turn=end_turn,
        location_update=LocationUpdateModel(**location_update)
        if location_update
        else None,
    )

    # Add dice requests if provided
    if dice_requests:
        for dr in dice_requests:
            dice_req = DiceRequestModel(**dr)
            ai_response.dice_requests.append(dice_req)

    return ai_response


def assert_event_has_fields(event: BaseGameEvent, **expected_fields: Any) -> None:
    """Assert that an event has specific field values."""
    for field, expected_value in expected_fields.items():
        actual_value = getattr(event, field, None)
        assert actual_value == expected_value, (
            f"Event field '{field}' mismatch: "
            f"expected {expected_value}, got {actual_value}"
        )


# Tests for EventRecorder functionality
import tempfile


class TestEventRecorder:
    """Test EventRecorder functionality."""

    def test_basic_replay(self) -> None:
        """Test basic event replay functionality."""
        from app.models.events import NarrativeAddedEvent

        recorder = EventRecorder()

        # Record some events
        event1 = NarrativeAddedEvent(role="assistant", content="Hello")
        event2 = NarrativeAddedEvent(role="user", content="Hi there")

        recorder.record_event(event1)
        recorder.record_event(event2)

        # Replay events
        replayed: List[BaseGameEvent] = []
        recorder.replay_events(lambda e: replayed.append(e))

        assert len(replayed) == 2
        # Cast to NarrativeAddedEvent to access content attribute
        from app.models.events import NarrativeAddedEvent

        assert (
            isinstance(replayed[0], NarrativeAddedEvent)
            and replayed[0].content == "Hello"
        )
        assert (
            isinstance(replayed[1], NarrativeAddedEvent)
            and replayed[1].content == "Hi there"
        )

    def test_replay_with_filter(self) -> None:
        """Test replaying only specific event types."""
        from app.models.events import CombatStartedEvent, NarrativeAddedEvent

        recorder = EventRecorder()

        # Record mixed events
        recorder.record_event(
            NarrativeAddedEvent(role="assistant", content="Story begins")
        )
        recorder.record_event(CombatStartedEvent(combatants=[], round_number=1))
        recorder.record_event(
            NarrativeAddedEvent(role="assistant", content="Combat narrative")
        )

        # Replay only narrative events
        narrative_events: List[BaseGameEvent] = []
        recorder.replay_events(
            lambda e: narrative_events.append(e), filter_types=["narrative_added"]
        )

        assert len(narrative_events) == 2
        assert all(e.event_type == "narrative_added" for e in narrative_events)

    def test_save_and_load_events(self) -> None:
        """Test saving and loading events from file."""
        from app.models.events import BackendProcessingEvent, NarrativeAddedEvent

        recorder = EventRecorder()

        # Record some events
        recorder.record_event(NarrativeAddedEvent(role="user", content="Test message"))
        recorder.record_event(BackendProcessingEvent(is_processing=True))
        original_count = len(recorder.events)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            recorder.save_to_file(temp_path)

            # Load into new recorder
            new_recorder = EventRecorder()
            new_recorder.load_from_file(temp_path)

            # Verify events match
            assert len(new_recorder.events) == original_count

            # Check first and last events
            assert new_recorder.events[0].event_type == recorder.events[0].event_type
            assert new_recorder.events[-1].event_type == recorder.events[-1].event_type

        finally:
            os.unlink(temp_path)

    def test_replay_to_event_queue(self) -> None:
        """Test replaying events to an event queue."""
        from app.core.event_queue import EventQueue
        from app.models.events import BackendProcessingEvent, NarrativeAddedEvent

        # Create a sequence
        recorder = EventRecorder()
        recorder.record_event(BackendProcessingEvent(is_processing=True))
        recorder.record_event(NarrativeAddedEvent(role="assistant", content="Test"))
        recorder.record_event(BackendProcessingEvent(is_processing=False))

        # Create event queue
        queue = EventQueue()

        # Replay to queue
        recorder.replay_events(lambda e: queue.put_event(e))

        # Verify events in queue
        assert queue.qsize() == len(recorder.events)

        # Get first event
        first_event = queue.get_event(block=False)
        assert (
            first_event is not None and first_event.event_type == "backend_processing"
        )

    def test_event_recorder_comprehensive_capabilities(self) -> None:
        """Test all EventRecorder methods for test utility validation."""
        from app.models.events import (
            BackendProcessingEvent,
            CombatantHpChangedEvent,
            CombatStartedEvent,
            NarrativeAddedEvent,
        )
        from app.models.models import CombatantModel

        recorder = EventRecorder()

        # Test basic recording
        event1 = NarrativeAddedEvent(role="assistant", content="Combat begins!")
        event2 = CombatStartedEvent(
            combatants=[
                CombatantModel(
                    id="pc_1",
                    name="Hero",
                    initiative=10,
                    current_hp=25,
                    max_hp=25,
                    armor_class=16,
                    is_player=True,
                )
            ]
        )
        event3 = CombatantHpChangedEvent(
            combatant_id="pc_1",
            combatant_name="Hero",
            old_hp=25,
            new_hp=20,
            max_hp=25,
            change_amount=-5,
            is_player_controlled=True,
            source="Goblin attack",
        )
        event4 = BackendProcessingEvent(is_processing=True)

        recorder.record_event(event1)
        recorder.record_event(event2)
        recorder.record_event(event3)
        recorder.record_event(event4)

        # Test get_events
        all_events = recorder.get_events()
        assert len(all_events) == 4

        # Test get_events_by_type
        narrative_events = recorder.get_events_by_type("narrative_added")
        assert len(narrative_events) == 1
        assert (
            isinstance(narrative_events[0], NarrativeAddedEvent)
            and narrative_events[0].content == "Combat begins!"
        )

        # Test count_events
        assert recorder.count_events("narrative_added") == 1
        assert recorder.count_events("combat_started") == 1
        assert recorder.count_events("nonexistent") == 0

        # Test has_event_type
        assert recorder.has_event_type("narrative_added")
        assert recorder.has_event_type("combat_started")
        assert not recorder.has_event_type("nonexistent")

        # Test find_event_with_data
        hp_event = recorder.find_event_with_data(
            "combatant_hp_changed", combatant_id="pc_1"
        )
        assert hp_event is not None
        assert (
            isinstance(hp_event, CombatantHpChangedEvent)
            and hp_event.change_amount == -5
        )

        no_match = recorder.find_event_with_data(
            "combatant_hp_changed", combatant_id="pc_2"
        )
        assert no_match is None

        # Test find_all_events_with_data
        backend_events = recorder.find_all_events_with_data(
            "backend_processing", is_processing=True
        )
        assert len(backend_events) == 1

        # Test clear
        recorder.clear()
        assert len(recorder.get_events()) == 0

        # Test get_event_sequence for event ordering
        recorder.record_event(event1)
        recorder.record_event(event2)
        sequence = recorder.get_event_types()
        assert sequence == ["narrative_added", "combat_started"]

        # Test save and load functionality
        import json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            recorder.save_to_file(f.name)

            # Load and verify
            with open(f.name) as rf:
                data = json.load(rf)
                assert len(data) == 2
                assert data[0]["event_type"] == "narrative_added"
