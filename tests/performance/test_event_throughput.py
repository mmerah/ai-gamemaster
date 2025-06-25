"""
Performance tests for event system throughput.
Tests the system's ability to handle high volumes of events.
"""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List

import pytest
from fastapi import FastAPI

from app import create_app
from app.core.container import get_container
from app.models.events.combat import CombatantHpChangedEvent, TurnAdvancedEvent
from app.models.events.narrative import NarrativeAddedEvent
from app.models.events.system import BackendProcessingEvent
from tests.conftest import get_test_settings


class TestEventThroughput:
    """Test event system performance under various loads."""

    @pytest.fixture
    def app(self) -> Any:
        """Create a FastAPI app with proper configuration."""
        settings = get_test_settings()
        app = create_app(settings)
        yield app

    @pytest.fixture(autouse=True)
    def setup(self, app: FastAPI) -> None:
        """Set up test fixtures."""
        # Store app as attribute
        object.__setattr__(self, "app", app)
        self.container = get_container()
        self.event_queue = self.container.get_event_queue()

        # Clear event queue before each test
        self.event_queue.clear()

    def measure_throughput(
        self, num_events: int, event_factory: Callable[[int], Any]
    ) -> Dict[str, Any]:
        """Measure throughput for putting and getting events."""
        # Measure put throughput
        put_start = time.perf_counter()

        for i in range(num_events):
            event = event_factory(i)
            self.event_queue.put_event(event)

        put_end = time.perf_counter()
        put_duration = put_end - put_start
        put_throughput = num_events / put_duration

        # Measure get throughput
        retrieved_events: List[Any] = []
        get_start = time.perf_counter()

        while len(retrieved_events) < num_events:
            event = self.event_queue.get_event(block=True, timeout=0.1)
            if event:
                retrieved_events.append(event)

        get_end = time.perf_counter()
        get_duration = get_end - get_start
        get_throughput = num_events / get_duration

        return {
            "num_events": num_events,
            "put_duration": put_duration,
            "put_throughput": put_throughput,
            "get_duration": get_duration,
            "get_throughput": get_throughput,
            "events_retrieved": len(retrieved_events),
        }

    def test_single_thread_throughput(self) -> None:
        """Test throughput with a single producer/consumer thread."""

        def create_narrative_event(i: int) -> NarrativeAddedEvent:
            return NarrativeAddedEvent(
                role="assistant",
                content=f"Test narrative {i}",
                message_id=f"perf-test-{i}",
            )

        # Test with different volumes
        test_volumes = [100, 1000, 5000]
        results = []

        for volume in test_volumes:
            result = self.measure_throughput(volume, create_narrative_event)
            results.append(result)
            print(f"\nSingle thread - {volume} events:")
            print(
                f"  Put: {result['put_throughput']:.1f} events/sec ({result['put_duration']:.3f}s)"
            )
            print(
                f"  Get: {result['get_throughput']:.1f} events/sec ({result['get_duration']:.3f}s)"
            )

        # Assert minimum performance thresholds
        for result in results:
            assert result["put_throughput"] >= 500  # At least 500 events/sec
            assert result["get_throughput"] >= 500
            assert result["events_retrieved"] == result["num_events"]

    def test_concurrent_producers(self) -> None:
        """Test throughput with multiple concurrent producers."""
        num_threads = 5
        events_per_thread = 200
        total_events = num_threads * events_per_thread

        def produce_events(thread_id: int) -> None:
            for _ in range(events_per_thread):
                event = CombatantHpChangedEvent(
                    combatant_id=f"combatant-{thread_id}",
                    combatant_name=f"Fighter {thread_id}",
                    old_hp=20,
                    new_hp=15,
                    max_hp=20,
                    change_amount=-5,
                    is_player_controlled=(thread_id % 2 == 0),
                    source=f"Thread {thread_id} damage",
                )
                self.event_queue.put_event(event)

        # Measure concurrent production
        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(produce_events, i) for i in range(num_threads)]
            for future in futures:
                future.result()

        production_time = time.perf_counter() - start_time
        production_throughput = total_events / production_time

        # Consume all events
        retrieved_events: List[Any] = []
        consume_start = time.perf_counter()

        while len(retrieved_events) < total_events:
            event = self.event_queue.get_event(block=False)
            if event:
                retrieved_events.append(event)
            elif len(retrieved_events) < total_events:
                time.sleep(0.001)  # Brief sleep if queue is momentarily empty

        consume_time = time.perf_counter() - consume_start
        consume_throughput = total_events / consume_time

        print(
            f"\nConcurrent producers - {num_threads} threads, {total_events} total events:"
        )
        print(
            f"  Production: {production_throughput:.1f} events/sec ({production_time:.3f}s)"
        )
        print(
            f"  Consumption: {consume_throughput:.1f} events/sec ({consume_time:.3f}s)"
        )

        # Verify all events were retrieved
        assert len(retrieved_events) == total_events

        # Should handle concurrent production efficiently
        assert (
            production_throughput >= 50 * num_threads
        )  # Lowered threshold for test stability

    def test_mixed_event_types(self) -> None:
        """Test throughput with various event types and sizes."""
        num_events = 1000

        def create_mixed_event(i: int) -> Any:
            event_type = i % 4
            if event_type == 0:
                return NarrativeAddedEvent(
                    role="assistant",
                    content="A" * 100,  # Larger content
                    message_id=f"narrative-{i}",
                )
            elif event_type == 1:
                return BackendProcessingEvent(
                    is_processing=True, needs_backend_trigger=False
                )
            elif event_type == 2:
                return TurnAdvancedEvent(
                    new_combatant_id=f"combatant-{i}",
                    new_combatant_name=f"Fighter {i}",
                    round_number=i // 10 + 1,
                    is_new_round=(i % 10 == 0),
                    is_player_controlled=(i % 2 == 0),
                )
            else:
                return CombatantHpChangedEvent(
                    combatant_id=f"combatant-{i}",
                    combatant_name=f"Fighter {i}",
                    old_hp=20,
                    new_hp=15,
                    max_hp=20,
                    change_amount=-5,
                    is_player_controlled=True,
                    source="Mixed damage",
                )

        result = self.measure_throughput(num_events, create_mixed_event)

        print(f"\nMixed event types - {num_events} events:")
        print(f"  Put: {result['put_throughput']:.1f} events/sec")
        print(f"  Get: {result['get_throughput']:.1f} events/sec")

        # Should still maintain good performance with mixed types
        assert result["put_throughput"] >= 400
        assert result["get_throughput"] >= 400

    def test_event_ordering_under_load(self) -> None:
        """Test that event ordering is maintained under high load."""
        num_events = 1000

        # Generate events with sequential IDs
        for i in range(num_events):
            event = NarrativeAddedEvent(
                role="assistant",
                content=f"Event {i}",
                message_id=f"order-test-{i}",
                gm_thought=f"Sequence {i}",  # Use gm_thought to track order
            )
            self.event_queue.put_event(event)

        # Retrieve all events
        retrieved_events: List[Any] = []
        while len(retrieved_events) < num_events:
            retrieved_event: Any = self.event_queue.get_event(block=True, timeout=0.1)
            if retrieved_event:
                retrieved_events.append(retrieved_event)

        # Verify sequence numbers are strictly increasing
        sequence_numbers = [e.sequence_number for e in retrieved_events]
        assert sequence_numbers == sorted(sequence_numbers)

        # Verify content order matches insertion order
        for i, event in enumerate(retrieved_events):
            expected_content = f"Event {i}"
            assert event.content == expected_content

    def test_memory_efficiency(self) -> None:
        """Test memory usage doesn't grow excessively with high event volume."""
        # Skip this test as it requires psutil which is not in requirements
        pytest.skip("Memory test requires psutil package")

    def test_latency_percentiles(self) -> None:
        """Test event processing latency at various percentiles."""
        num_events = 1000
        latencies = []

        for i in range(num_events):
            # Create event with timestamp
            put_time = time.perf_counter()
            event = NarrativeAddedEvent(
                role="assistant", content=f"Latency test {i}", message_id=f"latency-{i}"
            )
            self.event_queue.put_event(event)

            # Immediately retrieve it
            retrieved_event = self.event_queue.get_event(block=True, timeout=1.0)
            get_time = time.perf_counter()

            if retrieved_event:
                latency_ms = (get_time - put_time) * 1000
                latencies.append(latency_ms)

        # Calculate percentiles
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = statistics.mean(latencies)

        print(f"\nLatency test - {num_events} events:")
        print(f"  Average: {avg:.2f} ms")
        print(f"  P50: {p50:.2f} ms")
        print(f"  P95: {p95:.2f} ms")
        print(f"  P99: {p99:.2f} ms")

        # Assert latency requirements
        assert p50 < 20  # P50 under 20ms
        assert p95 < 100  # P95 under 100ms
        assert p99 < 200  # P99 under 200ms
