"""
Integration tests for correlation ID functionality.
Tests that related events share the same correlation ID.
"""
import pytest
from unittest.mock import Mock, patch
from app.core.container import get_container
from app.ai_services.schemas import AIResponse, DiceRequest, HPChangeUpdate
from app.game.models import GameState, CombatState, CharacterInstance
from app.game.models import Combatant
from tests.test_helpers import EventRecorder


class TestCorrelationIDs:
    """Test correlation ID functionality for related events."""
    
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
    
    @pytest.fixture
    def event_recorder(self, container):
        """Set up EventRecorder to capture all events."""
        recorder = EventRecorder()
        
        event_queue = container.get_event_queue()
        original_put_event = event_queue.put_event
        
        def record_and_emit(event):
            recorder.record_event(event)
            return original_put_event(event)
        
        patcher = patch.object(event_queue, 'put_event', side_effect=record_and_emit)
        patcher.start()
        
        yield recorder
        
        patcher.stop()
    
    def setup_combat_scenario(self, container):
        """Setup a combat scenario for testing."""
        game_state_repo = container.get_game_state_repository()
        game_state = game_state_repo.get_game_state()
        
        # Setup party
        game_state.party = {
            "player1": CharacterInstance(
                id="player1",
                name="Test Hero",
                race="Human",
                char_class="Fighter",
                level=3,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                ability_scores={"STR": 16, "DEX": 12, "CON": 14, "INT": 10, "WIS": 13, "CHA": 12}
            )
        }
        
        # Setup combat
        game_state.combat = CombatState(
            is_active=True,
            combatants=[
                Combatant(id="player1", name="Test Hero", initiative=15, current_hp=20, max_hp=20, armor_class=15, is_player=True),
                Combatant(id="goblin1", name="Test Goblin", initiative=10, current_hp=8, max_hp=8, armor_class=12, is_player=False)
            ],
            current_turn_index=0,  # Player's turn
            round_number=1
        )
        
        # Add goblin to monster_stats
        from app.ai_services.schemas import MonsterBaseStats
        game_state.combat.monster_stats = {
            "goblin1": MonsterBaseStats(
                name="Test Goblin",
                initial_hp=8,
                ac=12,
                stats={"STR": 8, "DEX": 14, "CON": 12, "INT": 7, "WIS": 9, "CHA": 8}
            )
        }
        
        return game_state
    
    def test_player_action_correlation_id(self, container, app, event_recorder):
        """Test that events from a single player action share the same correlation ID."""
        with app.app_context():
            # Setup scenario
            game_state = self.setup_combat_scenario(container)
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
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
    
    def test_hp_change_correlation_id(self, container, app, event_recorder):
        """Test that HP change events get correlation IDs."""
        with app.app_context():
            # Setup scenario
            game_state = self.setup_combat_scenario(container)
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
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
    
    def test_npc_action_correlation_id(self, container, app, event_recorder):
        """Test that NPC actions get their own correlation IDs."""
        with app.app_context():
            # Setup scenario with NPC turn
            game_state = self.setup_combat_scenario(container)
            game_state.combat.current_turn_index = 1  # Goblin's turn
            
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
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
    
    def test_multiple_actions_different_correlation_ids(self, container, app, event_recorder):
        """Test that different actions get different correlation IDs."""
        with app.app_context():
            # Setup scenario
            game_state = self.setup_combat_scenario(container)
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
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