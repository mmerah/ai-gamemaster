"""
Integration tests for game state events not covered by comprehensive tests.
Tests LocationChangedEvent and PartyMemberUpdatedEvent (non-combat HP changes).
"""
import pytest
from unittest.mock import Mock
from app.core.container import get_container
from app.events.game_update_events import (
    LocationChangedEvent,
    PartyMemberUpdatedEvent
)
from app.game.models import GameState, CharacterInstance
from app.ai_services.schemas import AIResponse, LocationUpdate


class TestGameStateEvents:
    """Test game state event emission."""
    
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
    def container(self, app):
        """Get service container within app context."""
        with app.app_context():
            yield get_container()
    
    def test_location_changed_event(self, container):
        """Test that changing location emits LocationChangedEvent."""
        # Get services
        game_state_repo = container.get_game_state_repository()
        event_queue = container.get_event_queue()
        ai_response_processor = container.get_ai_response_processor()
        
        # Set up initial location
        game_state = GameState()
        game_state.current_location = {
            "name": "Tavern",
            "description": "A cozy tavern with a warm fireplace."
        }
        game_state_repo._active_game_state = game_state
        
        # Clear event queue
        event_queue.clear()
        
        # Create AI response that changes location
        ai_response = AIResponse(
            narrative="You step out of the tavern into the bustling market square.",
            reasoning="Moving to market",
            location_update=LocationUpdate(
                name="Market Square",
                description="A busy marketplace filled with vendors and shoppers."
            )
        )
        
        # Process the AI response
        ai_response_processor.process_response(ai_response)
        
        # Collect events
        events = []
        while not event_queue.is_empty():
            event = event_queue.get_event(block=False)
            events.append(event)
        
        # Should have narrative and location changed events
        event_types = [e.event_type for e in events]
        assert "narrative_added" in event_types
        assert "location_changed" in event_types
        
        # Verify location changed event
        location_event = next(e for e in events if e.event_type == "location_changed")
        assert location_event.old_location_name == "Tavern"
        assert location_event.new_location_name == "Market Square"
        assert location_event.new_location_description == "A busy marketplace filled with vendors and shoppers."
        
        # Verify location was actually updated
        updated_state = game_state_repo.get_game_state()
        assert updated_state.current_location["name"] == "Market Square"
    
    def test_party_member_updated_event_hp_change(self, container):
        """Test that changing party member stats emits PartyMemberUpdatedEvent."""
        # Get services
        game_state_repo = container.get_game_state_repository()
        event_queue = container.get_event_queue()
        ai_response_processor = container.get_ai_response_processor()
        
        # Set up party member
        game_state = GameState()
        game_state.party = {
            "hero1": CharacterInstance(
                id="hero1",
                name="Brave Hero",
                race="Human",
                char_class="Fighter",
                level=3,
                current_hp=20,
                max_hp=25,
                armor_class=15
            )
        }
        game_state_repo._active_game_state = game_state
        
        # Clear event queue
        event_queue.clear()
        
        # Create AI response that heals the hero (outside combat)
        ai_response = AIResponse(
            narrative="The priest's healing magic washes over you, restoring your vitality.",
            reasoning="Healing at temple",
            game_state_updates=[
                {
                    "type": "hp_change",
                    "character_id": "hero1",
                    "value": 5
                }
            ]
        )
        
        # Process the AI response
        ai_response_processor.process_response(ai_response)
        
        # Collect events
        events = []
        while not event_queue.is_empty():
            event = event_queue.get_event(block=False)
            events.append(event)
        
        # Should have narrative and party member updated events
        event_types = [e.event_type for e in events]
        assert "narrative_added" in event_types
        assert "party_member_updated" in event_types
        
        # Verify party member updated event
        party_event = next(e for e in events if e.event_type == "party_member_updated")
        assert party_event.character_id == "hero1"
        assert party_event.character_name == "Brave Hero"
        assert party_event.changes == {"current_hp": 25, "max_hp": 25}
        
        # Verify HP was actually updated
        updated_state = game_state_repo.get_game_state()
        assert updated_state.party["hero1"].current_hp == 25
    
