"""
Integration tests for ChatService and SSE event streaming.
Consolidated from test_chat_service_events_integration.py, test_sse_chat_events.py, 
and test_phase3_e2e_verification.py.
"""
import pytest
import time
import json
from app.core.container import ServiceContainer, get_container
from app.events.game_update_events import NarrativeAddedEvent
from app.game.unified_models import GameStateModel


class TestChatAndSSEIntegration:
    """Test ChatService event emission and SSE streaming integration."""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app with proper configuration."""
        from run import create_app
        app = create_app({
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False,
            'TESTING': True
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @pytest.fixture
    def container(self):
        """Create a standalone service container for testing."""
        config = {
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False
        }
        container = ServiceContainer(config)
        container.initialize()
        return container
    
    def test_chat_service_emits_to_event_queue(self, container):
        """Test that ChatService emits events to the real event queue."""
        chat_service = container.get_chat_service()
        event_queue = container.get_event_queue()
        
        # Clear any existing events
        event_queue.clear()
        
        # Add a message
        chat_service.add_message("assistant", "The goblin strikes!")
        
        # Check event was added to queue
        assert event_queue.qsize() == 1
        
        # Get and verify the event
        event = event_queue.get_event(block=False)
        assert isinstance(event, NarrativeAddedEvent)
        assert event.role == "assistant"
        assert event.content == "The goblin strikes!"
    
    def test_multiple_messages_emit_multiple_events(self, container):
        """Test that multiple messages emit multiple events in order."""
        chat_service = container.get_chat_service()
        event_queue = container.get_event_queue()
        
        # Clear any existing events
        event_queue.clear()
        
        # Add multiple messages
        messages = [
            ("user", "I attack the goblin!"),
            ("assistant", "You swing your sword at the goblin."),
            ("system", "Roll for attack.")
        ]
        
        for role, content in messages:
            chat_service.add_message(role, content)
        
        # Verify all events were emitted
        assert event_queue.qsize() == 3
        
        # Verify events are in order
        for role, content in messages:
            event = event_queue.get_event(block=False)
            assert event.role == role
            assert event.content == content
    
    def test_event_sequence_numbers_increment(self, container):
        """Test that event sequence numbers increment properly."""
        chat_service = container.get_chat_service()
        event_queue = container.get_event_queue()
        
        # Clear any existing events
        event_queue.clear()
        
        # Add messages
        chat_service.add_message("user", "First message")
        chat_service.add_message("assistant", "Second message")
        
        # Get events
        event1 = event_queue.get_event(block=False)
        event2 = event_queue.get_event(block=False)
        
        # Verify sequence numbers increment
        assert event2.sequence_number > event1.sequence_number
    
    def test_chat_message_emits_sse_event(self, app, client):
        """Test that adding a chat message emits an SSE event."""
        with app.app_context():
            # Get services
            container = get_container()
            chat_service = container.get_chat_service()
            event_queue = container.get_event_queue()
            
            # Clear any existing events
            event_queue.clear()
            
            # Connect to SSE endpoint with test mode
            sse_response = client.get('/api/game_event_stream?test_mode=true', 
                                     headers={'Accept': 'text/event-stream'})
            
            # Add a chat message
            chat_service.add_message("assistant", "Welcome to the dungeon!", 
                                   gm_thought="Setting the scene")
            
            # Give a moment for event to propagate
            time.sleep(0.1)
            
            # Read SSE data
            data = sse_response.get_data(as_text=True)
            
            # Parse SSE events
            events = []
            for line in data.strip().split('\n'):
                if line.startswith('data: '):
                    event_data = line[6:]  # Remove 'data: ' prefix
                    if event_data and event_data != '{"status": "connected"}':
                        # Parse the JSON event data
                        parsed = json.loads(event_data)
                        events.append(parsed)
            
            # Verify we got a narrative event
            assert len(events) >= 1
            narrative_event = None
            for event in events:
                if event.get('event_type') == 'narrative_added':
                    narrative_event = event
                    break
            
            assert narrative_event is not None
            assert narrative_event['role'] == 'assistant'
            assert narrative_event['content'] == "Welcome to the dungeon!"
            assert narrative_event['gm_thought'] == "Setting the scene"
            assert narrative_event['message_id'] is not None
            assert narrative_event['sequence_number'] > 0
    
    def test_complete_chat_sse_flow(self, app, client):
        """Test the complete flow: add message -> emit event -> receive via SSE."""
        with app.app_context():
            container = get_container()
            chat_service = container.get_chat_service()
            event_queue = container.get_event_queue()
            game_state_repo = container.get_game_state_repository()
            
            # Reset game state to clear any initial messages
            game_state_repo._game_state = GameStateModel()
            
            # Clear any existing events
            event_queue.clear()
            
            # Add multiple messages in sequence
            test_messages = [
                ("user", "I enter the dark cave", None),
                ("assistant", "You step into the damp cave. Water drips from stalactites above.", "Rolling perception check"),
                ("system", "Roll for perception (DC 15)", None),
                ("assistant", "You notice movement in the shadows!", "Goblin ambush incoming")
            ]
            
            for role, content, thought in test_messages:
                kwargs = {"gm_thought": thought} if thought else {}
                chat_service.add_message(role, content, **kwargs)
            
            # Verify events were queued
            assert event_queue.qsize() == 4
            
            # Get SSE response
            response = client.get('/api/game_event_stream?test_mode=true&test_timeout=1',
                                headers={'Accept': 'text/event-stream'})
            
            # Parse SSE data
            data = response.get_data(as_text=True)
            sse_events = []
            
            for line in data.strip().split('\n'):
                if line.startswith('data: '):
                    event_data = line[6:]
                    if event_data and event_data != '{"status": "connected"}':
                        try:
                            parsed = json.loads(event_data)
                            sse_events.append(parsed)
                        except json.JSONDecodeError:
                            pass
            
            # Verify we received all events via SSE
            assert len(sse_events) == 4, f"Expected 4 events, got {len(sse_events)}"
            
            # Verify event order and content
            for i, (role, content, thought) in enumerate(test_messages):
                event = sse_events[i]
                assert event['event_type'] == 'narrative_added'
                assert event['role'] == role
                assert event['content'] == content
                if thought:
                    assert event['gm_thought'] == thought
                assert event['message_id'] is not None
                assert event['sequence_number'] > 0
                
                # Verify sequence numbers increment
                if i > 0:
                    assert event['sequence_number'] > sse_events[i-1]['sequence_number']
    
    def test_sse_connection_health(self, app, client):
        """Test basic SSE connection health and status messages."""
        # Connect to SSE endpoint
        response = client.get('/api/game_event_stream?test_mode=true&test_timeout=0.1',
                            headers={'Accept': 'text/event-stream'})
        
        # Verify response
        assert response.status_code == 200
        assert response.content_type.startswith('text/event-stream')
        
        # Check for connection message
        data = response.get_data(as_text=True)
        assert 'data: {"status": "connected"}' in data