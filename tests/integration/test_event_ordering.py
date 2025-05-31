"""
Tests for event ordering and correlation ID tracking.
Ensures events maintain proper sequence and relationships.
"""
import pytest
import time
import threading
from typing import List
from unittest.mock import patch, Mock

from app import create_app
from app.core.container import get_container
from flask import current_app
from app.events.game_update_events import (
    BaseGameUpdateEvent,
    NarrativeAddedEvent,
    CombatStartedEvent,
    PlayerDiceRequestAddedEvent,
    CombatantHpChangedEvent,
    TurnAdvancedEvent,
    BackendProcessingEvent
)
from app.ai_services.schemas import AIResponse, HPChangeUpdate, CombatStartUpdate, DiceRequest, InitialCombatantData
from app.game.models import GameState, CharacterInstance


class TestEventOrdering:
    """Test event ordering and correlation."""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app with proper configuration."""
        from app.core.container import reset_container
        # Reset container before creating app to ensure clean state
        reset_container()
        
        from run import create_app
        app = create_app({
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False
        })
        with app.app_context():
            yield app
        
        # Clean up after test
        reset_container()
    
    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Set up test fixtures."""
        self.app = app
        self.container = get_container()
        self.event_queue = self.container.get_event_queue()
        self.game_state_repo = self.container.get_game_state_repository()
        self.ai_response_processor = self.container.get_ai_response_processor()
        
        # Clear event queue before each test
        self.event_queue.clear()
        
        # Set up game state
        game_state = GameState()
        game_state.party = {
            "hero": CharacterInstance(
                id="hero",
                name="Hero",
                race="Human",
                char_class="Fighter",
                level=5,
                max_hp=40,
                current_hp=40,
                armor_class=18,
                proficiency_bonus=3,
                base_stats={"STR": 18, "DEX": 14, "CON": 16, "INT": 10, "WIS": 12, "CHA": 8}
            )
        }
        self.game_state_repo._active_game_state = game_state
    
    def collect_events(self) -> List[BaseGameUpdateEvent]:
        """Collect all events from the queue."""
        events = []
        # Use the event queue from AI response processor if available
        queue = self.ai_response_processor.event_queue if hasattr(self.ai_response_processor, 'event_queue') and self.ai_response_processor.event_queue else self.event_queue
        
        while not queue.is_empty():
            event = queue.get_event(block=False)
            if event:
                events.append(event)
        return events
    
    def test_sequence_numbers_strictly_increasing(self):
        """Test that sequence numbers always increase."""
        # Generate events from multiple sources
        events_to_emit = []
        
        # Direct event emission
        for i in range(5):
            event = NarrativeAddedEvent(
                role="assistant",
                content=f"Direct event {i}",
                message_id=f"direct-{i}"
            )
            events_to_emit.append(event)
            self.event_queue.put_event(event)
        
        # Events from AI response processing
        ai_response = AIResponse(
            narrative="Starting combat with goblins!",
            reasoning="Combat encounter",
            game_state_updates=[
                CombatStartUpdate(
                    type="combat_start",
                    combatants=[
                        InitialCombatantData(id="goblin1", name="Goblin", hp=7, ac=13)
                    ]
                )
            ],
            dice_requests=[
                DiceRequest(
                    request_id="init-001",
                    character_ids=["hero"],
                    type="initiative",
                    dice_formula="1d20",
                    reason="Roll for initiative"
                )
            ]
        )
        
        self.ai_response_processor.process_response(ai_response)
        
        # More direct events
        for i in range(5, 10):
            event = BackendProcessingEvent(
                is_processing=i % 2 == 0,
                needs_backend_trigger=False
            )
            events_to_emit.append(event)
            self.event_queue.put_event(event)
        
        # Collect all events
        all_events = self.collect_events()
        
        # Verify sequence numbers
        sequence_numbers = [e.sequence_number for e in all_events]
        
        # Should be strictly increasing
        for i in range(1, len(sequence_numbers)):
            assert sequence_numbers[i] > sequence_numbers[i-1], \
                f"Sequence not increasing: {sequence_numbers[i-1]} -> {sequence_numbers[i]}"
        
        # Should have no gaps (consecutive)
        expected_sequences = list(range(sequence_numbers[0], sequence_numbers[0] + len(sequence_numbers)))
        assert sequence_numbers == expected_sequences, \
            f"Sequence gaps detected: expected {expected_sequences}, got {sequence_numbers}"
    
    def test_concurrent_event_emission_ordering(self):
        """Test ordering when events are emitted concurrently."""
        num_threads = 5
        events_per_thread = 20
        
        def emit_events(thread_id):
            for i in range(events_per_thread):
                event = NarrativeAddedEvent(
                    role="assistant",
                    content=f"Thread {thread_id} event {i}",
                    message_id=f"thread-{thread_id}-{i}"
                )
                self.event_queue.put_event(event)
                time.sleep(0.001)  # Small delay to increase contention
        
        # Start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=emit_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Collect events
        all_events = self.collect_events()
        
        # Should have all events
        assert len(all_events) == num_threads * events_per_thread
        
        # Sequence numbers should still be unique and ordered
        sequence_numbers = [e.sequence_number for e in all_events]
        assert len(set(sequence_numbers)) == len(sequence_numbers), "Duplicate sequence numbers found"
        assert sequence_numbers == sorted(sequence_numbers), "Sequence numbers not in order"
    
    def test_event_timestamp_ordering(self):
        """Test that timestamps reflect emission order."""
        # Emit events with controlled timing
        events = []
        
        for i in range(10):
            event = NarrativeAddedEvent(
                role="assistant",
                content=f"Timed event {i}",
                message_id=f"timed-{i}"
            )
            self.event_queue.put_event(event)
            events.append(event)
            time.sleep(0.01)  # 10ms between events
        
        # Collect events
        collected = self.collect_events()
        
        # Timestamps should generally increase (allowing for clock precision)
        for i in range(1, len(collected)):
            # Allow for same timestamp due to clock precision
            assert collected[i].timestamp >= collected[i-1].timestamp
        
        # Sequence numbers should strictly increase even if timestamps are same
        for i in range(1, len(collected)):
            if collected[i].timestamp == collected[i-1].timestamp:
                assert collected[i].sequence_number > collected[i-1].sequence_number
    
    def test_correlation_id_propagation(self):
        """Test that correlation IDs link related events."""
        # Currently, the system doesn't use correlation IDs
        # This test demonstrates how they could be used
        
        # Mock correlation ID usage
        correlation_id = "combat-sequence-001"
        
        # Events that would be correlated
        combat_start = CombatStartedEvent(
            combatants=[
                {"id": "hero", "name": "Hero", "initiative": 0, "is_player": True},
                {"id": "goblin", "name": "Goblin", "initiative": 0, "is_player": False}
            ],
            round_number=1
        )
        combat_start.correlation_id = correlation_id
        self.event_queue.put_event(combat_start)
        
        dice_request = PlayerDiceRequestAddedEvent(
            character_id="hero",
            character_name="Hero",
            request_id="req-001",
            roll_type="initiative",
            dice_formula="1d20",
            purpose="Roll for initiative"
        )
        dice_request.correlation_id = correlation_id
        self.event_queue.put_event(dice_request)
        
        turn_event = TurnAdvancedEvent(
            new_combatant_id="hero",
            new_combatant_name="Hero",
            round_number=1,
            is_new_round=False,
            is_player_controlled=True
        )
        turn_event.correlation_id = correlation_id
        self.event_queue.put_event(turn_event)
        
        # Collect events
        events = self.collect_events()
        
        # All events should have the same correlation ID
        correlation_ids = [e.correlation_id for e in events]
        assert all(cid == correlation_id for cid in correlation_ids)
    
    def test_event_ordering_across_game_flow(self):
        """Test ordering through a complete game flow."""
        collected_events = []
        
        # Step 1: Player action
        ai_service = self.app.config.get('AI_SERVICE')
        ai_service.get_response = Mock(return_value=AIResponse(
            narrative="You search the room carefully.",
            reasoning="Exploration action"
        ))
        
        # Trigger player action
        game_event_manager = self.container.get_game_event_manager()
        game_event_manager.handle_event({
                "type": "player_action",
                "data": {
                    "action_type": "free_text",
                    "value": "I search the room"
                }
            })
        
        # Collect batch 1
        batch1 = self.collect_events()
        collected_events.extend(batch1)
        
        # Step 2: Combat start via another player action
        ai_service.get_response = Mock(return_value=AIResponse(
            narrative="A goblin jumps out!",
            reasoning="Surprise combat",
            game_state_updates=[
                CombatStartUpdate(
                    type="combat_start",
                    combatants=[InitialCombatantData(id="goblin1", name="Goblin", hp=7, ac=13)]
                )
            ]
        ))
        
        # Trigger through game event handler to get backend_processing events
        game_event_manager.handle_event({
                "type": "player_action",
                "data": {
                    "action_type": "free_text",
                    "value": "I look around for danger"
                }
            })
        
        # Collect batch 2
        batch2 = self.collect_events()
        collected_events.extend(batch2)
        
        # Step 3: Damage via next step trigger
        ai_service.get_response = Mock(return_value=AIResponse(
            narrative="The goblin strikes!",
            reasoning="Enemy attack",
            game_state_updates=[
                HPChangeUpdate(
                    type="hp_change",
                    character_id="hero",
                    value=-5,
                    details={"source": "Goblin dagger"}
                )
            ]
        ))
        
        # Trigger through next step handler
        game_event_manager.handle_event({
                "type": "next_step",
                "data": {}
            })
        
        # Collect batch 3
        batch3 = self.collect_events()
        collected_events.extend(batch3)
        
        # Verify comprehensive ordering
        all_sequence_numbers = [e.sequence_number for e in collected_events]
        
        # Should be strictly increasing across all batches
        assert all_sequence_numbers == sorted(all_sequence_numbers)
        
        # Verify no duplicates
        assert len(set(all_sequence_numbers)) == len(all_sequence_numbers)
        
        # Verify expected event types in order
        event_types = [e.event_type for e in collected_events]
        
        # Should see backend processing, narratives, combat start, hp change
        assert "backend_processing" in event_types
        assert "narrative_added" in event_types
        assert "combat_started" in event_types
        assert "combatant_hp_changed" in event_types
    
    def test_event_ordering_with_errors(self):
        """Test that event ordering is maintained even with errors."""
        # Emit some normal events
        for i in range(3):
            event = NarrativeAddedEvent(
                role="assistant",
                content=f"Normal event {i}",
                message_id=f"normal-{i}"
            )
            self.event_queue.put_event(event)
        
        # Trigger an error
        ai_service = self.app.config.get('AI_SERVICE')
        ai_service.get_response = Mock(side_effect=Exception("Simulated AI error"))
        
        game_event_manager = self.container.get_game_event_manager()
        game_event_manager.handle_event({
                "type": "player_action",
                "data": {
                    "action_type": "free_text",
                    "value": "This will fail"
                }
            })
        
        # Emit more events after error
        for i in range(3, 6):
            event = NarrativeAddedEvent(
                role="assistant",
                content=f"After error event {i}",
                message_id=f"after-{i}"
            )
            self.event_queue.put_event(event)
        
        # Collect all events
        all_events = self.collect_events()
        
        # Should have normal events, backend processing events, error event, and after-error events
        event_types = [e.event_type for e in all_events]
        
        assert event_types.count("narrative_added") == 8
        assert "game_error" in event_types
        assert "backend_processing" in event_types  # Should have processing events
        
        # Sequence numbers should still be ordered
        sequence_numbers = [e.sequence_number for e in all_events]
        assert sequence_numbers == sorted(sequence_numbers)
        
        # Error event should be in correct position
        error_event_idx = next(i for i, e in enumerate(all_events) if e.event_type == "game_error")
        assert 3 <= error_event_idx <= 6  # Should be after first 3 events but could have backend_processing events