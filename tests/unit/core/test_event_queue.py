"""
Unit tests for EventQueue implementation.
Following TDD - tests written before implementation.
"""

import threading
import time
from typing import List

from app.models.events.combat import CombatStartedEvent, TurnAdvancedEvent
from app.models.events.narrative import NarrativeAddedEvent


class TestEventQueue:
    """Test the thread-safe event queue implementation."""

    def test_event_queue_creation(self) -> None:
        """Test that EventQueue can be created."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()
        assert queue is not None
        assert queue.qsize() == 0

    def test_event_queue_put_and_get(self) -> None:
        """Test basic put and get operations."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()

        # Create test event
        event = NarrativeAddedEvent(role="assistant", content="Test narrative")

        # Put event
        queue.put_event(event)
        assert queue.qsize() == 1

        # Get event
        retrieved_event = queue.get_event(block=False)
        assert retrieved_event is not None
        assert retrieved_event.event_type == "narrative_added"
        # Type narrow to NarrativeAddedEvent to access content
        assert isinstance(retrieved_event, NarrativeAddedEvent)
        assert retrieved_event.content == "Test narrative"
        assert queue.qsize() == 0

    def test_event_queue_maintains_order(self) -> None:
        """Test that events dequeue in FIFO order."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()

        # Put multiple events
        event1 = NarrativeAddedEvent(role="assistant", content="First")
        event2 = CombatStartedEvent(combatants=[])
        event3 = TurnAdvancedEvent(
            new_combatant_id="pc_1", new_combatant_name="Elara", round_number=1
        )

        queue.put_event(event1)
        queue.put_event(event2)
        queue.put_event(event3)

        # Get events in order
        first_event = queue.get_event(block=False)
        assert first_event is not None
        assert isinstance(first_event, NarrativeAddedEvent)
        assert first_event.content == "First"

        second_event = queue.get_event(block=False)
        assert second_event is not None
        assert second_event.event_type == "combat_started"

        third_event = queue.get_event(block=False)
        assert third_event is not None
        assert third_event.event_type == "turn_advanced"

        assert queue.qsize() == 0

    def test_event_queue_blocking_get(self) -> None:
        """Test blocking get with timeout."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()

        # Get from empty queue with timeout
        start_time = time.time()
        event = queue.get_event(block=True, timeout=0.1)
        elapsed = time.time() - start_time

        assert event is None
        assert elapsed >= 0.1
        assert elapsed < 0.2  # Should timeout quickly

    def test_event_queue_thread_safe(self) -> None:
        """Test that multiple threads can safely add events."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()
        events_added: List[str] = []

        def add_events(thread_id: int, count: int) -> None:
            """Add events from a thread."""
            for i in range(count):
                event = NarrativeAddedEvent(
                    role="assistant", content=f"Thread {thread_id} event {i}"
                )
                queue.put_event(event)
                events_added.append(f"Thread {thread_id} event {i}")

        # Create multiple threads
        threads: List[threading.Thread] = []
        for i in range(5):
            thread = threading.Thread(target=add_events, args=(i, 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify all events were added
        assert queue.qsize() == 50  # 5 threads * 10 events each

        # Retrieve all events
        retrieved: List[str] = []
        while queue.qsize() > 0:
            event = queue.get_event(block=False)
            if event is not None and isinstance(event, NarrativeAddedEvent):
                retrieved.append(event.content)

        # All events should be present (order may vary due to threading)
        assert len(retrieved) == 50
        assert set(retrieved) == set(events_added)

    def test_event_sequence_numbers(self) -> None:
        """Test that events have increasing sequence numbers."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()

        # Add multiple events
        for i in range(10):
            event = NarrativeAddedEvent(role="assistant", content=f"Event {i}")
            queue.put_event(event)

        # Get events and check sequence numbers
        prev_seq = -1
        while queue.qsize() > 0:
            retrieved_event = queue.get_event(block=False)
            assert retrieved_event is not None
            assert retrieved_event.sequence_number > prev_seq
            prev_seq = retrieved_event.sequence_number

    def test_event_queue_clear(self) -> None:
        """Test clearing the queue."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()

        # Add events
        for i in range(5):
            queue.put_event(NarrativeAddedEvent(role="assistant", content=f"Event {i}"))

        assert queue.qsize() == 5

        # Clear queue
        queue.clear()
        assert queue.qsize() == 0

        # Should be able to add events after clearing
        queue.put_event(NarrativeAddedEvent(role="assistant", content="New event"))
        assert queue.qsize() == 1

    def test_event_queue_peek(self) -> None:
        """Test peeking at next event without removing it."""
        from app.core.event_queue import EventQueue

        queue = EventQueue()

        # Add event
        event = NarrativeAddedEvent(role="assistant", content="Test")
        queue.put_event(event)

        # Peek should return event without removing
        peeked = queue.peek()
        assert peeked is not None
        assert isinstance(peeked, NarrativeAddedEvent)
        assert peeked.content == "Test"
        assert queue.qsize() == 1  # Still in queue

        # Get should return same event
        retrieved = queue.get_event(block=False)
        assert retrieved is not None
        assert retrieved.event_id == peeked.event_id
        assert queue.qsize() == 0
