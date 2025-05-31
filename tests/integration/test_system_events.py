"""
Integration tests for system events.
Tests GameErrorEvent and GameStateSnapshotEvent for error handling and state synchronization.
"""
import pytest
from unittest.mock import Mock, patch
from app.core.container import get_container
from app.events.game_update_events import GameErrorEvent, GameStateSnapshotEvent
from app.game.models import GameState, CharacterInstance, Quest
from app.game.models import CombatState, Combatant
from app.ai_services.schemas import AIResponse, CombatStartUpdate
from flask import current_app


class TestSystemEvents:
    """Test system event emission."""
    
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
    
    def test_game_error_event_on_ai_service_error(self, container):
        """Test that AI service errors emit GameErrorEvent."""
        # Get services
        game_state_repo = container.get_game_state_repository()
        event_queue = container.get_event_queue()
        game_event_manager = container.get_game_event_manager()
        
        # Set up game state
        game_state = GameState()
        game_state.campaign_id = "test_campaign"
        game_state_repo._active_game_state = game_state
        
        # Clear event queue
        event_queue.clear()
        
        # Mock AI service to raise an error
        with patch.object(current_app.config['AI_SERVICE'], 'get_response') as mock_ai:
            mock_ai.side_effect = Exception("AI service connection failed")
            
            # Try to trigger an AI call
            try:
                game_event_manager.handle_event({
                    "type": "next_step",
                    "data": {}
                }, "test_session")
            except Exception:
                pass  # We expect this to fail
        
        # Collect events
        events = []
        while not event_queue.is_empty():
            event = event_queue.get_event(block=False)
            events.append(event)
        
        # Should have a game error event
        error_events = [e for e in events if e.event_type == "game_error"]
        assert len(error_events) >= 1
        
        error_event = error_events[0]
        assert "AI service connection failed" in error_event.error_message
        assert error_event.error_type == "ai_service_error"
        assert error_event.severity == "error"
        assert error_event.recoverable is True
    
    def test_game_error_event_on_invalid_character_reference(self, container):
        """Test that invalid character references emit GameErrorEvent."""
        # Get services
        game_state_repo = container.get_game_state_repository()
        event_queue = container.get_event_queue()
        ai_response_processor = container.get_ai_response_processor()
        
        # Set up game state with a character
        game_state = GameState()
        game_state.party = {
            "hero1": CharacterInstance(
                id="hero1",
                name="Test Hero",
                race="Human",
                char_class="Fighter",
                level=1,
                current_hp=10,
                max_hp=10,
                armor_class=15
            )
        }
        game_state_repo._active_game_state = game_state
        
        # Clear event queue
        event_queue.clear()
        
        # Create AI response that references non-existent character
        ai_response = AIResponse(
            narrative="The mysterious stranger vanishes into thin air.",
            reasoning="Character not found",
            game_state_updates=[
                {
                    "type": "hp_change",
                    "character_id": "non_existent_character",
                    "value": -5
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
        
        # Should have a game error event
        error_events = [e for e in events if e.event_type == "game_error"]
        assert len(error_events) >= 1
        
        error_event = error_events[0]
        assert "non_existent_character" in error_event.error_message
        assert error_event.error_type == "invalid_reference"
        assert error_event.context == {"character_id": "non_existent_character", "update_type": "hp_change"}
    
    def test_game_state_snapshot_event_on_request(self, container):
        """Test that game state snapshot can be requested."""
        # Get services
        game_state_repo = container.get_game_state_repository()
        event_queue = container.get_event_queue()
        
        # Set up a comprehensive game state
        game_state = GameState()
        game_state.campaign_id = "test_campaign"
        game_state.current_location = {
            "name": "Tavern",
            "description": "A cozy tavern"
        }
        
        # Add party members
        game_state.party = {
            "hero1": CharacterInstance(
                id="hero1",
                name="Aragorn",
                race="Human",
                char_class="Ranger",
                level=5,
                current_hp=45,
                max_hp=50,
                armor_class=16,
                inventory=[{"id": "sword1", "name": "Longsword", "equipped": True}],
                conditions=["blessed"]
            ),
            "hero2": CharacterInstance(
                id="hero2",
                name="Gandalf",
                race="Human",
                char_class="Wizard",
                level=10,
                current_hp=35,
                max_hp=40,
                armor_class=13,
                inventory=[{"id": "staff1", "name": "Staff of Power"}],
                conditions=[]
            )
        }
        
        # Add active quest
        game_state.active_quests = {
            "main_quest": Quest(
                id="main_quest",
                title="Destroy the Ring",
                description="Cast the ring into Mount Doom",
                status="active"
            )
        }
        
        # Add active combat
        game_state.combat = CombatState(
            is_active=True,
            round_number=2,
            current_turn_index=1,
            combatants=[
                Combatant(id="hero1", name="Aragorn", initiative=18, is_player=True,
                         current_hp=45, max_hp=50, armor_class=16),
                Combatant(id="orc1", name="Orc Warrior", initiative=12, is_player=False,
                         current_hp=8, max_hp=15, armor_class=13),
                Combatant(id="hero2", name="Gandalf", initiative=20, is_player=True,
                         current_hp=35, max_hp=40, armor_class=13)
            ]
        )
        from app.ai_services.schemas import MonsterBaseStats
        game_state.combat.monster_stats = {
            "orc1": MonsterBaseStats(
                name="Orc Warrior",
                initial_hp=15,
                ac=13,
                stats={"STR": 16, "DEX": 12},
                abilities=[],
                attacks=[]
            )
        }
        
        # Add pending dice requests
        from app.ai_services.schemas import DiceRequest
        game_state.pending_player_dice_requests = [
            DiceRequest(
                request_id="save_1",
                character_ids=["hero1"],
                type="save",
                dice_formula="1d20",
                reason="Dexterity save vs fireball"
            )
        ]
        
        game_state_repo._active_game_state = game_state
        
        # Clear event queue
        event_queue.clear()
        
        # Request a snapshot (this would normally be triggered by reconnection logic)
        from app.events.game_update_events import GameStateSnapshotEvent
        snapshot_event = GameStateSnapshotEvent.from_game_state(game_state)
        event_queue.put_event(snapshot_event)
        
        # Get the event
        event = event_queue.get_event(block=False)
        assert event.event_type == "game_state_snapshot"
        
        # Verify comprehensive state capture
        assert event.campaign_id == "test_campaign"
        assert event.location["name"] == "Tavern"
        
        # Verify party data
        assert len(event.party_members) == 2
        aragorn = next(p for p in event.party_members if p["id"] == "hero1")
        assert aragorn["name"] == "Aragorn"
        assert aragorn["current_hp"] == 45
        assert aragorn["conditions"] == ["blessed"]
        assert len(aragorn["inventory"]) == 1
        
        # Verify quest data
        assert len(event.active_quests) == 1
        assert event.active_quests[0]["title"] == "Destroy the Ring"
        
        # Verify combat data
        assert event.combat_state["is_active"] is True
        assert event.combat_state["round_number"] == 2
        assert len(event.combat_state["combatants"]) == 3
        assert event.combat_state["current_turn_combatant_id"] == "orc1"  # Index 1
        
        # Verify NPC stats
        assert "orc1" in event.combat_state["monster_stats"]
        # Note: The snapshot event serializes MonsterBaseStats using model_dump()
        # Check the initial_hp field instead of hp (which is dynamic)
        assert event.combat_state["monster_stats"]["orc1"]["initial_hp"] == 15
        
        # Verify pending requests
        assert len(event.pending_dice_requests) == 1
        assert event.pending_dice_requests[0]["type"] == "save"
    
    def test_game_error_event_severity_levels(self, container):
        """Test that GameErrorEvent supports different severity levels."""
        event_queue = container.get_event_queue()
        event_queue.clear()
        
        # Test different severity levels
        from app.events.game_update_events import GameErrorEvent
        
        # Warning level
        warning_event = GameErrorEvent(
            error_message="Character inventory nearly full",
            error_type="inventory_warning",
            severity="warning",
            recoverable=True,
            context={"character_id": "hero1", "slots_remaining": 2}
        )
        event_queue.put_event(warning_event)
        
        # Error level
        error_event = GameErrorEvent(
            error_message="Failed to save game state",
            error_type="save_error",
            severity="error",
            recoverable=True,
            correlation_id="save_attempt_123"
        )
        event_queue.put_event(error_event)
        
        # Critical level
        critical_event = GameErrorEvent(
            error_message="Database connection lost",
            error_type="database_error", 
            severity="critical",
            recoverable=False
        )
        event_queue.put_event(critical_event)
        
        # Collect and verify events
        events = []
        while not event_queue.is_empty():
            events.append(event_queue.get_event(block=False))
        
        assert len(events) == 3
        assert events[0].severity == "warning"
        assert events[1].severity == "error"
        assert events[2].severity == "critical"
        assert events[2].recoverable is False