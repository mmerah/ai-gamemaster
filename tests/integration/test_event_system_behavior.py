"""
Integration tests for event system behavior.
Tests event ordering, sequence numbers, timestamps, and correlation IDs.
Consolidates test_event_ordering.py and test_correlation_ids.py
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
from app.ai_services.schemas import AIResponse
from app.game.unified_models import (
    HPChangeUpdate, CombatStartUpdate, DiceRequest, InitialCombatantData, 
    GameStateModel, CharacterInstanceModel, CombatStateModel, CombatantModel,
    MonsterBaseStats
)
from tests.test_helpers import EventRecorder


class TestEventSystemBehavior:
    """Test event system behavior including ordering and correlation."""
    
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
            'RAG_ENABLED': False,
            'TESTING': True
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
        game_state = GameStateModel()
        game_state.party = {
            "hero": CharacterInstanceModel(
                template_id="hero_template",
                campaign_id="test_campaign",
                level=5,
                max_hp=40,
                current_hp=40,
                conditions=[],
                inventory=[]
            )
        }
        self.game_state_repo._active_game_state = game_state
    
    @pytest.fixture
    def event_recorder(self):
        """Set up EventRecorder to capture all events."""
        recorder = EventRecorder()
        
        original_put_event = self.event_queue.put_event
        
        def record_and_emit(event):
            recorder.record_event(event)
            return original_put_event(event)
        
        patcher = patch.object(self.event_queue, 'put_event', side_effect=record_and_emit)
        patcher.start()
        
        yield recorder
        
        patcher.stop()
    
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
    
    def setup_combat_scenario(self):
        """Setup a combat scenario for testing."""
        game_state = self.game_state_repo.get_game_state()
        
        # Setup party
        game_state.party = {
            "player1": CharacterInstanceModel(
                template_id="player1_template",
                campaign_id="test_campaign",
                level=3,
                current_hp=20,
                max_hp=20,
                conditions=[],
                inventory=[]
            )
        }
        
        # Setup combat
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=[
                CombatantModel(id="player1", name="Test Hero", initiative=15, current_hp=20, max_hp=20, armor_class=15, is_player=True),
                CombatantModel(id="goblin1", name="Test Goblin", initiative=10, current_hp=8, max_hp=8, armor_class=12, is_player=False)
            ],
            current_turn_index=0,  # Player's turn
            round_number=1
        )
        
        # Add goblin to monster_stats
        game_state.combat.monster_stats = {
            "goblin1": MonsterBaseStats(
                name="Test Goblin",
                initial_hp=8,
                ac=12,
                stats={"STR": 8, "DEX": 14, "CON": 12, "INT": 7, "WIS": 9, "CHA": 8}
            )
        }
        
        return game_state
    
    # ========== Event Ordering Tests ==========
    
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
    
    # ========== Correlation ID Tests ==========
    
    def test_player_action_correlation_id(self, event_recorder):
        """Test that events from a single player action share the same correlation ID."""
        # Setup scenario
        game_state = self.setup_combat_scenario()
        game_event_manager = self.container.get_game_event_manager()
        ai_service = self.app.config.get('AI_SERVICE')
        
        event_recorder.clear()
        
        # Mock AI response that requests a dice roll
        ai_response = AIResponse(
            narrative="The hero attacks with their sword!",
            reasoning="Player attack action",
            dice_requests=[
                DiceRequest(
                    request_id="test_attack",
                    character_ids=["player1"],
                    type="attack",
                    dice_formula="1d20+5",
                    reason="Sword attack roll",
                    dc=12
                )
            ]
        )
        ai_service.get_response = Mock(return_value=ai_response)
        
        # Trigger player action
        game_event_manager.handle_player_action({
            "action_type": "attack",
            "value": "I attack the goblin!"
        })
        
        # Get all events that should share the same correlation ID
        backend_processing_events = event_recorder.find_all_events_with_data("backend_processing")
        narrative_events = event_recorder.find_all_events_with_data("narrative_added")
        dice_request_events = event_recorder.find_all_events_with_data("player_dice_request_added")
        
        # Should have at least these events
        assert len(backend_processing_events) >= 2  # start + end
        assert len(narrative_events) >= 2  # user + AI
        assert len(dice_request_events) >= 1  # dice request
        
        # All events should have the same correlation ID
        correlation_id = backend_processing_events[0].correlation_id
        assert correlation_id is not None, "Correlation ID should be set"
        
        # Check that all BackendProcessingEvents have the same correlation ID
        for event in backend_processing_events:
            assert event.correlation_id == correlation_id, f"BackendProcessingEvent should have correlation ID {correlation_id}"
        
        # Check that all NarrativeAddedEvents from this action have the same correlation ID
        ai_narratives = [e for e in narrative_events if e.role == "assistant"]
        for event in ai_narratives:
            assert event.correlation_id == correlation_id, f"NarrativeAddedEvent should have correlation ID {correlation_id}"
        
        # Check that all PlayerDiceRequestAddedEvents have the same correlation ID
        for event in dice_request_events:
            assert event.correlation_id == correlation_id, f"PlayerDiceRequestAddedEvent should have correlation ID {correlation_id}"
    
    def test_hp_change_correlation_id(self, event_recorder):
        """Test that HP change events get correlation IDs."""
        # Setup scenario
        game_state = self.setup_combat_scenario()
        game_event_manager = self.container.get_game_event_manager()
        ai_service = self.app.config.get('AI_SERVICE')
        
        event_recorder.clear()
        
        # Mock AI response that applies damage
        ai_response = AIResponse(
            narrative="The goblin takes 5 damage!",
            reasoning="Applying damage",
            game_state_updates=[
                HPChangeUpdate(
                    type="hp_change",
                    character_id="goblin1",
                    value=-5,
                    details={"source": "player1"}
                )
            ]
        )
        ai_service.get_response = Mock(return_value=ai_response)
        
        # Trigger player action that causes HP change
        game_event_manager.handle_player_action({
            "action_type": "spell",
            "value": "I cast Magic Missile at the goblin!"
        })
        
        # Get correlation ID from backend processing events
        backend_events = event_recorder.find_all_events_with_data("backend_processing")
        assert len(backend_events) >= 1
        correlation_id = backend_events[0].correlation_id
        assert correlation_id is not None
        
        # Get HP change event
        hp_events = event_recorder.find_all_events_with_data("combatant_hp_changed")
        assert len(hp_events) == 1
        
        hp_event = hp_events[0]
        assert hp_event.correlation_id == correlation_id, f"HP change event should have correlation ID {correlation_id}"
        assert hp_event.combatant_id == "goblin1"
        assert hp_event.change_amount == -5
    
    def test_npc_action_correlation_id(self, event_recorder):
        """Test that NPC actions get their own correlation IDs."""
        # Setup scenario with NPC turn
        game_state = self.setup_combat_scenario()
        game_state.combat.current_turn_index = 1  # Goblin's turn
        
        game_event_manager = self.container.get_game_event_manager()
        ai_service = self.app.config.get('AI_SERVICE')
        
        event_recorder.clear()
        
        # Mock AI response sequence for NPC turn
        attack_response = AIResponse(
            narrative="The goblin attacks the hero!",
            reasoning="NPC attack",
            dice_requests=[
                DiceRequest(
                    request_id="npc_attack",
                    character_ids=["goblin1"],
                    type="attack",
                    dice_formula="1d20+4",
                    reason="Scimitar attack"
                )
            ],
            end_turn=False  # Don't end turn yet, wait for roll results
        )
        
        final_response = AIResponse(
            narrative="The goblin's attack misses!",
            reasoning="Attack result narration",
            end_turn=True  # Now end the turn
        )
        
        # Use side_effect to return different responses for each AI call
        ai_service.get_response = Mock(side_effect=[attack_response, final_response])
        
        # Trigger NPC turn
        game_event_manager.handle_next_step_trigger()
        
        # Get correlation ID from backend processing events
        backend_events = event_recorder.find_all_events_with_data("backend_processing")
        assert len(backend_events) >= 1
        correlation_id = backend_events[0].correlation_id
        assert correlation_id is not None
        
        # Check that NPC dice events have the correlation ID
        npc_dice_events = event_recorder.find_all_events_with_data("npc_dice_roll_processed")
        for event in npc_dice_events:
            assert event.correlation_id == correlation_id, f"NPC dice event should have correlation ID {correlation_id}"
    
    def test_multiple_actions_different_correlation_ids(self, event_recorder):
        """Test that different actions get different correlation IDs."""
        # Setup scenario
        game_state = self.setup_combat_scenario()
        game_event_manager = self.container.get_game_event_manager()
        ai_service = self.app.config.get('AI_SERVICE')
        
        event_recorder.clear()
        
        # First action
        ai_response1 = AIResponse(
            narrative="First action narrative",
            reasoning="First action"
        )
        ai_service.get_response = Mock(return_value=ai_response1)
        
        game_event_manager.handle_player_action({
            "action_type": "spell",
            "value": "First action"
        })
        
        # Get correlation ID from first action
        backend_events_1 = [e for e in event_recorder.events if e.event_type == "backend_processing"]
        correlation_id_1 = backend_events_1[0].correlation_id if backend_events_1 else None
        
        # Second action
        ai_response2 = AIResponse(
            narrative="Second action narrative", 
            reasoning="Second action"
        )
        ai_service.get_response = Mock(return_value=ai_response2)
        
        game_event_manager.handle_player_action({
            "action_type": "spell",
            "value": "Second action"
        })
        
        # Get correlation ID from second action
        backend_events_2 = [e for e in event_recorder.events if e.event_type == "backend_processing"]
        # Filter to get only events from the second action (after the first action completed)
        second_action_events = [e for e in backend_events_2 if e.correlation_id != correlation_id_1]
        correlation_id_2 = second_action_events[0].correlation_id if second_action_events else None
        
        # Correlation IDs should be different for different actions
        assert correlation_id_1 is not None
        assert correlation_id_2 is not None
        assert correlation_id_1 != correlation_id_2, "Different actions should have different correlation IDs"
    
    def test_correlation_id_propagation_basic(self):
        """Test basic correlation ID propagation (simplified version)."""
        # This is a simpler version of the old test_correlation_id_propagation
        # to demonstrate the concept without the complex combat setup
        
        correlation_id = "test-correlation-001"
        
        # Create related events with same correlation ID
        event1 = NarrativeAddedEvent(
            role="assistant",
            content="Starting a sequence",
            correlation_id=correlation_id
        )
        self.event_queue.put_event(event1)
        
        event2 = PlayerDiceRequestAddedEvent(
            character_id="hero",
            character_name="Hero",
            request_id="req-001",
            roll_type="initiative",
            dice_formula="1d20",
            purpose="Roll for initiative",
            correlation_id=correlation_id
        )
        self.event_queue.put_event(event2)
        
        event3 = BackendProcessingEvent(
            is_processing=False,
            needs_backend_trigger=False,
            correlation_id=correlation_id
        )
        self.event_queue.put_event(event3)
        
        # Collect events
        events = self.collect_events()
        
        # All events should have the same correlation ID
        assert len(events) == 3
        for event in events:
            assert event.correlation_id == correlation_id