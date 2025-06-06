"""
Integration tests for edge cases and unique scenarios not covered by comprehensive backend tests.
Consolidated from various other test files to reduce redundancy.
"""
import pytest
from unittest.mock import Mock, patch
from app.game.unified_models import CombatStateModel, CombatantModel
from app.ai_services.schemas import AIResponse
from app.game.unified_models import CombatantRemoveUpdate, MonsterBaseStats


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from app import create_app
        app = create_app({
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False,
            'TESTING': True
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def container(self, app):
        """Get service container."""
        with app.app_context():
            from app.core.container import get_container
            yield get_container()
    
    def test_error_handling_and_recovery(self, client, container, monkeypatch, app):
        """Test that the system handles errors gracefully and emits error events."""
        # Set up mock AI service to fail
        mock_ai_service = Mock()
        mock_ai_service.get_structured_response.side_effect = Exception("API rate limit reached")
        mock_ai_service.get_response.side_effect = Exception("API rate limit reached")
        
        # Patch the AI service in Flask config
        original_ai_service = app.config.get('AI_SERVICE')
        app.config['AI_SERVICE'] = mock_ai_service
        
        try:
            # Set up event recording
            from tests.test_helpers import EventRecorder
            recorder = EventRecorder()
            event_queue = container.get_event_queue()
            original_put = event_queue.put_event
            
            def record_and_emit(event):
                recorder.record_event(event)
                return original_put(event)
            
            monkeypatch.setattr(event_queue, 'put_event', record_and_emit)
            
            # Send player action that will trigger AI error
            response = client.post('/api/player_action', json={
                'action_type': 'free_text',
                'value': 'I attack the goblin!'
            })
            
            # Should get response with 500 status code 
            # The error is handled within the handler and returns frontend data with status 500
            assert response.status_code == 500
            data = response.json
            # Check that the error was added to chat history
            assert any('Error processing AI step' in msg['content'] for msg in data['chat_history'])
            
            # Should emit error event
            error_events = recorder.get_events_by_type('game_error')
            assert len(error_events) > 0
            assert 'API rate limit' in error_events[0].error_message
            
            # Test retry functionality
            mock_ai_service.get_structured_response.side_effect = None
            mock_ai_service.get_response.side_effect = None
            mock_ai_service.get_structured_response.return_value = AIResponse(
                narrative="You swing your sword at the goblin!",
                game_state_updates=[]
            )
            mock_ai_service.get_response.return_value = AIResponse(
                narrative="You swing your sword at the goblin!",
                game_state_updates=[]
            )
            
            # Retry should work
            retry_response = client.post('/api/retry_last_ai_request')
            assert retry_response.status_code == 200
            # The response does not have a 'success' field, check for no error instead
            assert 'error' not in retry_response.json
            
            # Note: In this error scenario, no assistant message was created initially,
            # so there's no message to supersede. The superseded event only happens
            # when retrying after a successful AI response.
            
            # Should emit narrative after successful retry
            narrative_events = recorder.get_events_by_type('narrative_added')
            assert any('swing your sword' in e.content for e in narrative_events)
            
        finally:
            # Restore original AI service
            app.config['AI_SERVICE'] = original_ai_service
    
    def test_retry_supersedes_previous_message(self, client, container, monkeypatch, app):
        """Test that retrying a successful AI response marks the previous message as superseded."""
        # Set up event recording
        from tests.test_helpers import EventRecorder
        recorder = EventRecorder()
        event_queue = container.get_event_queue()
        original_put = event_queue.put_event
        
        def record_and_emit(event):
            recorder.record_event(event)
            return original_put(event)
        
        monkeypatch.setattr(event_queue, 'put_event', record_and_emit)
        
        # First, send a successful player action
        response = client.post('/api/player_action', json={
            'action_type': 'free_text',
            'value': 'I search the room'
        })
        
        assert response.status_code == 200
        
        # Find the AI response message
        narrative_events = recorder.get_events_by_type('narrative_added')
        ai_messages = [e for e in narrative_events if e.role == 'assistant']
        assert len(ai_messages) > 0, "Expected at least one AI message"
        original_message_id = ai_messages[-1].message_id
        
        # Now retry the action
        retry_response = client.post('/api/retry_last_ai_request')
        assert retry_response.status_code == 200
        
        # Should emit message_superseded event for the previous message
        superseded_events = recorder.get_events_by_type('message_superseded')
        assert len(superseded_events) > 0, "Expected at least one message_superseded event"
        assert superseded_events[0].message_id == original_message_id
        assert superseded_events[0].reason == "retry"
        
        # Should also have a new narrative message
        new_narrative_events = recorder.get_events_by_type('narrative_added')
        new_ai_messages = [e for e in new_narrative_events if e.role == 'assistant']
        assert len(new_ai_messages) > len(ai_messages), "Expected a new AI message after retry"

    def test_state_snapshot_for_reconnection(self, client, container):
        """Test that state snapshots are generated for client reconnection."""
        from tests.test_helpers import EventRecorder
        recorder = EventRecorder()
        event_queue = container.get_event_queue()
        
        original_put = event_queue.put_event
        def record_and_emit(event):
            recorder.record_event(event)
            return original_put(event)
        
        with patch.object(event_queue, 'put_event', side_effect=record_and_emit):
            # Request state snapshot
            response = client.get('/api/game_state?emit_snapshot=true')
            assert response.status_code == 200
            
            # Should emit snapshot event
            snapshot_events = recorder.get_events_by_type('game_state_snapshot')
            assert len(snapshot_events) == 1
            
            snapshot = snapshot_events[0]
            # Combat state can be None if no combat is active
            assert hasattr(snapshot, 'combat_state')
            assert snapshot.party_members is not None
            assert len(snapshot.party_members) > 0
            assert snapshot.location is not None
            assert snapshot.active_quests is not None


class TestCombatEdgeCases:
    """Test combat edge cases not covered by basic scenarios."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from app import create_app
        app = create_app({
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False,
            'TESTING': True
        })
        return app
    
    @pytest.fixture
    def container(self, app):
        """Get service container."""
        with app.app_context():
            from app.core.container import get_container
            yield get_container()
    
    def test_combatant_removed_event(self, container):
        """Test that combatants can be removed (flee/escape)."""
        from tests.test_helpers import EventRecorder
        recorder = EventRecorder()
        event_queue = container.get_event_queue()
        
        # Set up combat with some combatants
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=[
                CombatantModel(id="pc_1", name="Hero", initiative=20, current_hp=25,
                         max_hp=25, armor_class=16, is_player=True),
                CombatantModel(id="goblin_1", name="Goblin", initiative=15, current_hp=7,
                         max_hp=7, armor_class=13, is_player=False),
                CombatantModel(id="goblin_2", name="Fleeing Goblin", initiative=10, current_hp=5,
                         max_hp=7, armor_class=13, is_player=False)
            ],
            monster_stats={
                "goblin_1": MonsterBaseStats(name="Goblin", initial_hp=7, ac=13),
                "goblin_2": MonsterBaseStats(name="Fleeing Goblin", initial_hp=7, ac=13)
            }
        )
        game_state_repo.save_game_state(game_state)
        
        original_put = event_queue.put_event
        def record_and_emit(event):
            recorder.record_event(event)
            return original_put(event)
        
        with patch.object(event_queue, 'put_event', side_effect=record_and_emit):
            # Mock AI response with combatant removal
            ai_response_processor = container.get_ai_response_processor()
            mock_response = AIResponse(
                narrative="The wounded goblin flees in terror!",
                game_state_updates=[
                    CombatantRemoveUpdate(
                        type="combatant_remove",
                        character_id="goblin_2",
                        details={"reason": "fled"}
                    )
                ]
            )
            
            # Process the response
            ai_response_processor.process_response(mock_response, 'player_action')
            
            # Verify combatant removed event
            removed_events = recorder.get_events_by_type('combatant_removed')
            assert len(removed_events) == 1
            assert removed_events[0].combatant_id == "goblin_2"
            assert removed_events[0].reason == "fled"
            
            # Verify combatant actually removed from state
            updated_state = game_state_repo.get_game_state()
            assert len(updated_state.combat.combatants) == 2
            assert not any(c.id == "goblin_2" for c in updated_state.combat.combatants)

    def test_player_dice_requests_cleared_event(self, container):
        """Test that dice requests are properly cleared after submission."""
        from tests.test_helpers import EventRecorder
        recorder = EventRecorder()
        event_queue = container.get_event_queue()
        
        # Set up game state with pending dice requests
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()
        from app.ai_services.schemas import DiceRequest
        game_state.pending_player_dice_requests = [
            DiceRequest(
                request_id="req_1",
                character_ids=["pc_1"],
                type="attack",
                dice_formula="1d20+5",
                reason="Attack roll"
            )
        ]
        game_state_repo.save_game_state(game_state)
        
        original_put = event_queue.put_event
        def record_and_emit(event):
            recorder.record_event(event)
            return original_put(event)
        
        with patch.object(event_queue, 'put_event', side_effect=record_and_emit):
            # Submit dice roll results
            game_event_manager = container.get_game_event_manager()
            game_event_manager.handle_completed_roll_submission([{
                "request_id": "req_1",
                "character_id": "pc_1",
                "roll_type": "attack",
                "dice_formula": "1d20+5",
                "dice_breakdown": "18 + 5",
                "total": 23,
                "purpose": "Attack roll"
            }])
            
            # Verify dice requests cleared event
            cleared_events = recorder.get_events_by_type('player_dice_requests_cleared')
            assert len(cleared_events) == 1
            assert len(cleared_events[0].cleared_request_ids) == 1
            
            # Verify requests actually cleared
            updated_state = game_state_repo.get_game_state()
            assert len(updated_state.pending_player_dice_requests) == 0


class TestEventRecorderCapabilities:
    """Test the EventRecorder testing utility comprehensively."""
    
    def test_event_recorder_comprehensive_capabilities(self):
        """Test all EventRecorder methods for test utility validation."""
        from tests.test_helpers import EventRecorder
        from app.events.game_update_events import (
            NarrativeAddedEvent, CombatStartedEvent, 
            CombatantHpChangedEvent, BackendProcessingEvent
        )
        
        recorder = EventRecorder()
        
        # Test basic recording
        event1 = NarrativeAddedEvent(role="assistant", content="Combat begins!")
        event2 = CombatStartedEvent(combatants=[
            CombatantModel(id="pc_1", name="Hero", initiative=10, current_hp=25, max_hp=25, armor_class=16, is_player=True)
        ])
        event3 = CombatantHpChangedEvent(
            combatant_id="pc_1", combatant_name="Hero",
            old_hp=25, new_hp=20, max_hp=25, change_amount=-5,
            is_player_controlled=True, source="Goblin attack"
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
        assert narrative_events[0].content == "Combat begins!"
        
        # Test count_events
        assert recorder.count_events("narrative_added") == 1
        assert recorder.count_events("combat_started") == 1
        assert recorder.count_events("nonexistent") == 0
        
        # Test has_event_type
        assert recorder.has_event_type("narrative_added")
        assert recorder.has_event_type("combat_started")
        assert not recorder.has_event_type("nonexistent")
        
        # Test find_event_with_data
        hp_event = recorder.find_event_with_data("combatant_hp_changed", combatant_id="pc_1")
        assert hp_event is not None
        assert hp_event.change_amount == -5
        
        no_match = recorder.find_event_with_data("combatant_hp_changed", combatant_id="pc_2")
        assert no_match is None
        
        # Test find_all_events_with_data
        backend_events = recorder.find_all_events_with_data("backend_processing", is_processing=True)
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
        import tempfile
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            recorder.save_to_file(f.name)
            
            # Load and verify
            with open(f.name, 'r') as rf:
                data = json.load(rf)
                assert len(data) == 2
                assert data[0]['event_type'] == 'narrative_added'