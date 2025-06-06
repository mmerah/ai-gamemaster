"""
Test helper utilities to ensure proper test isolation.
"""
import os
import sys
from typing import List, Optional, Any, Type
from unittest import mock


def ensure_clean_imports():
    """
    Ensure clean imports by removing potentially problematic modules.
    This helps avoid the '_has_torch_function' error when tests reload modules.
    """
    # Modules that can cause issues when reloaded
    problematic_modules = [
        'torch',
        'numpy',
        'transformers',
        'sentence_transformers',
        'kokoro',
        'app.services.rag.knowledge_bases',
        'app.tts_services.kokoro_service',
    ]
    
    # Get current module names to avoid modifying dict during iteration
    current_modules = list(sys.modules.keys())
    
    for module in current_modules:
        # Remove problematic modules and their submodules
        for prob_module in problematic_modules:
            if module == prob_module or module.startswith(prob_module + '.'):
                sys.modules.pop(module, None)


def setup_test_environment():
    """
    Set up a clean test environment with proper configuration.
    """
    # Set environment variables before any imports
    os.environ['RAG_ENABLED'] = 'false'
    os.environ['TTS_PROVIDER'] = 'disabled'
    
    # Clean up any previously imported modules
    ensure_clean_imports()


class IsolatedTestCase:
    """
    Mixin for test cases that need proper isolation from ML dependencies.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level test isolation."""
        setup_test_environment()
        super().setUpClass()
    
    def setUp(self):
        """Set up test-level isolation."""
        # Ensure environment is clean for each test
        os.environ['RAG_ENABLED'] = 'false'
        os.environ['TTS_PROVIDER'] = 'disabled'
        super().setUp()


# Import event types only after ensuring clean environment
from app.events.game_update_events import BaseGameUpdateEvent


class EventRecorder:
    """
    Records events for testing purposes.
    Allows inspection of event sequences and validation of event data.
    """
    
    def __init__(self):
        self.events: List[BaseGameUpdateEvent] = []
        self._enabled = True
        
    def record_event(self, event: BaseGameUpdateEvent) -> None:
        """Record an event if recording is enabled."""
        if self._enabled and isinstance(event, BaseGameUpdateEvent):
            self.events.append(event)
    
    def get_events(self) -> List[BaseGameUpdateEvent]:
        """Get all recorded events."""
        return self.events.copy()
    
    def get_events_by_type(self, event_type: str) -> List[BaseGameUpdateEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_event_types(self) -> List[str]:
        """Get the sequence of event types in order."""
        return [e.event_type for e in self.events]
    
    def get_latest_event(self, event_type: Optional[str] = None) -> Optional[BaseGameUpdateEvent]:
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
            f"Expected {expected_count} '{event_type}' events, "
            f"but found {actual_count}"
        )
    
    def find_event_with_data(self, event_type: str, **kwargs) -> Optional[BaseGameUpdateEvent]:
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
    
    def find_all_events_with_data(self, event_type: str, **kwargs) -> List[BaseGameUpdateEvent]:
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
    
    def get_events_of_type(self, event_class: Type[BaseGameUpdateEvent]) -> List[BaseGameUpdateEvent]:
        """Get all events of a specific class type."""
        return [e for e in self.events if isinstance(e, event_class)]
    
    def get_all_events(self) -> List[BaseGameUpdateEvent]:
        """Get all recorded events."""
        return self.events.copy()
    
    def has_gaps(self) -> bool:
        """Check if there are gaps in sequence numbers (indicating dropped events)."""
        if len(self.events) < 2:
            return False
        
        sequence_numbers = [e.sequence_number for e in self.events if hasattr(e, 'sequence_number')]
        if not sequence_numbers:
            return False
            
        sequence_numbers.sort()
        for i in range(1, len(sequence_numbers)):
            if sequence_numbers[i] - sequence_numbers[i-1] > 1:
                return True
        return False
    
    def attach_to_queue(self, event_queue) -> None:
        """Attach recorder to an event queue to automatically record events."""
        # Monkey patch the put_event method
        original_put = event_queue.put_event
        
        def recording_put(event):
            self.record_event(event)
            return original_put(event)
        
        event_queue.put_event = recording_put
    
    def assert_backend_processing_pattern(self) -> None:
        """Assert that BackendProcessingEvent follows the expected first=True, last=False pattern."""
        if not self.events:
            return
            
        backend_events = self.get_events_by_type("backend_processing")
        if len(backend_events) < 2:
            # Should have at least start and end events for any AI processing
            assert len(backend_events) == 0, "BackendProcessingEvent should come in pairs (start=True, end=False)"
            return
            
        # Should be an even number (pairs of start/end)
        assert len(backend_events) % 2 == 0, f"BackendProcessingEvent should come in pairs, got {len(backend_events)}"
        
        # Check that they alternate True/False correctly
        for i in range(0, len(backend_events), 2):
            start_event = backend_events[i]
            end_event = backend_events[i + 1]
            
            assert hasattr(start_event, 'is_processing'), "BackendProcessingEvent should have is_processing attribute"
            assert hasattr(end_event, 'is_processing'), "BackendProcessingEvent should have is_processing attribute"
            
            assert start_event.is_processing is True, f"Expected is_processing=True for start event {i//2+1}"
            assert end_event.is_processing is False, f"Expected is_processing=False for end event {i//2+1}"
    
    def assert_first_last_events(self, first_type: str, last_type: str) -> None:
        """Assert that the first and last events are of specific types."""
        assert len(self.events) > 0, "No events recorded"
        assert self.events[0].event_type == first_type, f"Expected first event to be '{first_type}', got '{self.events[0].event_type}'"
        assert self.events[-1].event_type == last_type, f"Expected last event to be '{last_type}', got '{self.events[-1].event_type}'"
    
    def get_event_subsequence(self, start_index: int, end_index: Optional[int] = None) -> List[BaseGameUpdateEvent]:
        """Get a subsequence of events by index range."""
        return self.events[start_index:end_index]
    
    def assert_event_present_with_data(self, event_type: str, **kwargs) -> BaseGameUpdateEvent:
        """Assert that an event of the specified type with specific data exists, and return it."""
        event = self.find_event_with_data(event_type, **kwargs)
        assert event is not None, f"Expected {event_type} event with data {kwargs} not found"
        return event
    
    def replay_events(self, handler_func, delay: float = 0.0, filter_types: Optional[List[str]] = None) -> None:
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
            events_data.append({
                'event_type': event.event_type,
                'data': event.model_dump()
            })
        
        with open(filepath, 'w') as f:
            json.dump(events_data, f, indent=2, default=str)
    
    def load_from_file(self, filepath: str) -> None:
        """Load events from a JSON file."""
        import json
        from app.events.game_update_events import get_event_class_by_type
        
        with open(filepath, 'r') as f:
            events_data = json.load(f)
        
        self.clear()
        for event_data in events_data:
            event_type = event_data['event_type']
            event_class = get_event_class_by_type(event_type)
            if event_class:
                event = event_class(**event_data['data'])
                self.record_event(event)

def create_mock_game_state(
    combat_active: bool = False,
    combatants: Optional[List[dict]] = None,
    current_turn_index: int = 0,
    round_number: int = 1,
    party: Optional[dict] = None
) -> Any:
    """Create a mock game state for testing."""
    from unittest.mock import Mock
    
    game_state = Mock()
    
    # Combat state
    game_state.combat = Mock()
    game_state.combat.is_active = combat_active
    game_state.combat.combatants = []
    game_state.combat.current_turn_index = current_turn_index
    game_state.combat.round_number = round_number
    game_state.combat.monster_stats = {}
    
    if combatants:
        for c in combatants:
            combatant = Mock()
            for key, value in c.items():
                setattr(combatant, key, value)
            game_state.combat.combatants.append(combatant)
    
    # Party
    game_state.party = party or {}
    
    # Other common attributes
    game_state.campaign_id = "test_campaign"
    game_state.current_location = {"name": "Test Location"}
    game_state.chat_history = []
    game_state.pending_player_dice_requests = []
    
    return game_state


def create_mock_ai_response(
    narrative: str = "Test narrative",
    dice_requests: Optional[List[dict]] = None,
    game_state_updates: Optional[List[Any]] = None,
    end_turn: bool = False,
    location_update: Optional[dict] = None
) -> Any:
    """Create a mock AI response for testing."""
    from unittest.mock import Mock
    from app.ai_services.schemas import AIResponse, DiceRequest
    
    # Create actual AIResponse object
    ai_response = AIResponse(
        narrative=narrative,
        reasoning="Test reasoning",
        dice_requests=[],
        game_state_updates=game_state_updates or [],
        end_turn=end_turn,
        location_update=location_update
    )
    
    # Add dice requests if provided
    if dice_requests:
        for dr in dice_requests:
            dice_req = DiceRequest(**dr)
            ai_response.dice_requests.append(dice_req)
    
    return ai_response


def assert_event_has_fields(event: BaseGameUpdateEvent, **expected_fields) -> None:
    """Assert that an event has specific field values."""
    for field, expected_value in expected_fields.items():
        actual_value = getattr(event, field, None)
        assert actual_value == expected_value, (
            f"Event field '{field}' mismatch: "
            f"expected {expected_value}, got {actual_value}"
        )


# Tests for EventRecorder functionality
import pytest
import tempfile
import os


class TestEventRecorder:
    """Test EventRecorder functionality."""
    
    def test_basic_replay(self):
        """Test basic event replay functionality."""
        from app.events.game_update_events import NarrativeAddedEvent
        
        recorder = EventRecorder()
        
        # Record some events
        event1 = NarrativeAddedEvent(role="assistant", content="Hello")
        event2 = NarrativeAddedEvent(role="user", content="Hi there")
        
        recorder.record_event(event1)
        recorder.record_event(event2)
        
        # Replay events
        replayed = []
        recorder.replay_events(lambda e: replayed.append(e))
        
        assert len(replayed) == 2
        assert replayed[0].content == "Hello"
        assert replayed[1].content == "Hi there"
    
    def test_replay_with_filter(self):
        """Test replaying only specific event types."""
        from app.events.game_update_events import NarrativeAddedEvent, CombatStartedEvent
        
        recorder = EventRecorder()
        
        # Record mixed events
        recorder.record_event(NarrativeAddedEvent(role="assistant", content="Story begins"))
        recorder.record_event(CombatStartedEvent(combatants=[], round_number=1))
        recorder.record_event(NarrativeAddedEvent(role="assistant", content="Combat narrative"))
        
        # Replay only narrative events
        narrative_events = []
        recorder.replay_events(
            lambda e: narrative_events.append(e),
            filter_types=["narrative_added"]
        )
        
        assert len(narrative_events) == 2
        assert all(e.event_type == "narrative_added" for e in narrative_events)
    
    def test_save_and_load_events(self):
        """Test saving and loading events from file."""
        from app.events.game_update_events import NarrativeAddedEvent, BackendProcessingEvent
        
        recorder = EventRecorder()
        
        # Record some events
        recorder.record_event(NarrativeAddedEvent(role="user", content="Test message"))
        recorder.record_event(BackendProcessingEvent(is_processing=True))
        original_count = len(recorder.events)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
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
    
    def test_replay_to_event_queue(self):
        """Test replaying events to an event queue."""
        from app.core.event_queue import EventQueue
        from app.events.game_update_events import BackendProcessingEvent, NarrativeAddedEvent
        
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
        assert first_event.event_type == "backend_processing"