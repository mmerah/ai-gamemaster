"""
Snapshot tests for event payloads.
These tests capture the JSON representation of events to detect unintended changes.
"""
import pytest
from unittest.mock import Mock, patch
from app.core.container import get_container
from app.ai_services.schemas import AIResponse, DiceRequest, HPChangeUpdate
from app.game.models import GameState, CombatState, CharacterInstance
from app.game.models import Combatant
from tests.test_helpers import EventRecorder


class TestEventSnapshots:
    """Snapshot tests for event payloads."""
    
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
    
    def normalize_event_for_snapshot(self, event_data):
        """Normalize event data for stable snapshots by removing dynamic fields."""
        normalized = event_data.copy()
        
        # Remove dynamic fields that change every test run
        normalized.pop('event_id', None)
        normalized.pop('timestamp', None)
        normalized.pop('sequence_number', None)
        normalized.pop('correlation_id', None)  # These are UUIDs and change every run
        normalized.pop('message_id', None)  # Message IDs contain timestamps and random numbers
        
        return normalized
    
    def test_backend_processing_event_snapshot(self, container, app, event_recorder, snapshot):
        """Test BackendProcessingEvent payload snapshot."""
        with app.app_context():
            # Setup scenario
            game_state = self.setup_combat_scenario(container)
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
            event_recorder.clear()
            
            # Mock simple AI response
            ai_response = AIResponse(
                narrative="Simple response",
                reasoning="Test action"
            )
            ai_service.get_response = Mock(return_value=ai_response)
            
            # Trigger action to generate BackendProcessingEvent
            game_event_manager.handle_player_action({
                "action_type": "misc",
                "value": "test action"
            })
            
            # Get BackendProcessingEvent
            backend_events = event_recorder.find_all_events_with_data("backend_processing")
            assert len(backend_events) >= 1
            
            # Take the first backend processing event (start)
            backend_event = backend_events[0]
            normalized_event = self.normalize_event_for_snapshot(backend_event.model_dump())
            
            # Convert to JSON string for snapshot
            import json
            event_json = json.dumps(normalized_event, indent=2, sort_keys=True)
            
            # Assert snapshot
            snapshot.assert_match(event_json, "backend_processing_event.json")
    
    def test_player_dice_request_added_event_snapshot(self, container, app, event_recorder, snapshot):
        """Test PlayerDiceRequestAddedEvent payload snapshot."""
        with app.app_context():
            # Setup scenario
            game_state = self.setup_combat_scenario(container)
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
            event_recorder.clear()
            
            # Mock AI response with dice request
            ai_response = AIResponse(
                narrative="Roll for attack!",
                reasoning="Player attack",
                dice_requests=[
                    DiceRequest(
                        request_id="test_attack",
                        character_ids=["player1"],
                        type="attack",
                        dice_formula="1d20+5",
                        reason="Sword attack roll",
                        dc=15,
                        skill=None,
                        ability=None
                    )
                ]
            )
            ai_service.get_response = Mock(return_value=ai_response)
            
            # Trigger action
            game_event_manager.handle_player_action({
                "action_type": "attack",
                "value": "I attack!"
            })
            
            # Get PlayerDiceRequestAddedEvent
            dice_events = event_recorder.find_all_events_with_data("player_dice_request_added")
            assert len(dice_events) >= 1
            
            dice_event = dice_events[0]
            normalized_event = self.normalize_event_for_snapshot(dice_event.model_dump())
            
            # Convert to JSON string for snapshot
            import json
            event_json = json.dumps(normalized_event, indent=2, sort_keys=True)
            
            # Assert snapshot
            snapshot.assert_match(event_json, "player_dice_request_added_event.json")
    
    def test_combatant_hp_changed_event_snapshot(self, container, app, event_recorder, snapshot):
        """Test CombatantHpChangedEvent payload snapshot."""
        with app.app_context():
            # Setup scenario
            game_state = self.setup_combat_scenario(container)
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
            event_recorder.clear()
            
            # Mock AI response with HP change
            ai_response = AIResponse(
                narrative="The goblin takes damage!",
                reasoning="Applying damage",
                game_state_updates=[
                    HPChangeUpdate(
                        type="hp_change",
                        character_id="goblin1",
                        value=-3,
                        details={"source": "player1", "weapon": "sword"}
                    )
                ]
            )
            ai_service.get_response = Mock(return_value=ai_response)
            
            # Trigger action
            game_event_manager.handle_player_action({
                "action_type": "damage",
                "value": "Damage the goblin"
            })
            
            # Get CombatantHpChangedEvent
            hp_events = event_recorder.find_all_events_with_data("combatant_hp_changed")
            assert len(hp_events) >= 1
            
            hp_event = hp_events[0]
            normalized_event = self.normalize_event_for_snapshot(hp_event.model_dump())
            
            # Convert to JSON string for snapshot
            import json
            event_json = json.dumps(normalized_event, indent=2, sort_keys=True)
            
            # Assert snapshot
            snapshot.assert_match(event_json, "combatant_hp_changed_event.json")
    
    def test_narrative_added_event_snapshot(self, container, app, event_recorder, snapshot):
        """Test NarrativeAddedEvent payload snapshot."""
        with app.app_context():
            # Setup scenario
            game_state = self.setup_combat_scenario(container)
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
            event_recorder.clear()
            
            # Mock AI response
            ai_response = AIResponse(
                narrative="This is a test narrative from the AI.",
                reasoning="Test narrative generation"
            )
            ai_service.get_response = Mock(return_value=ai_response)
            
            # Trigger action
            game_event_manager.handle_player_action({
                "action_type": "speak",
                "value": "Hello there!"
            })
            
            # Get NarrativeAddedEvent (look for AI response)
            narrative_events = event_recorder.find_all_events_with_data("narrative_added", role="assistant")
            assert len(narrative_events) >= 1
            
            narrative_event = narrative_events[0]
            normalized_event = self.normalize_event_for_snapshot(narrative_event.model_dump())
            
            # Convert to JSON string for snapshot
            import json
            event_json = json.dumps(normalized_event, indent=2, sort_keys=True)
            
            # Assert snapshot
            snapshot.assert_match(event_json, "narrative_added_event.json")
    
    def test_npc_dice_roll_processed_event_snapshot(self, container, app, event_recorder, snapshot):
        """Test NpcDiceRollProcessedEvent payload snapshot."""
        with app.app_context():
            # Setup scenario with NPC turn
            game_state = self.setup_combat_scenario(container)
            game_state.combat.current_turn_index = 1  # Goblin's turn
            
            game_event_manager = container.get_game_event_manager()
            ai_service = app.config.get('AI_SERVICE')
            
            event_recorder.clear()
            
            # Mock AI response with NPC dice request
            ai_response = AIResponse(
                narrative="The goblin attacks!",
                reasoning="NPC attack",
                dice_requests=[
                    DiceRequest(
                        request_id="npc_attack",
                        character_ids=["goblin1"],
                        type="attack",
                        dice_formula="1d20+4",
                        reason="Scimitar attack",
                        dc=15
                    )
                ]
            )
            ai_service.get_response = Mock(return_value=ai_response)
            
            # Mock dice service to return consistent result
            with patch.object(container.get_dice_service(), 'perform_roll') as mock_dice:
                mock_dice.return_value = {
                    "character_id": "goblin1",
                    "total_result": 14,
                    "result_summary": "Goblin Attack: 14",
                    "result_message": "Goblin rolls Attack: 1d20+4 -> [10]+4 = 14",
                    "success": False
                }
                
                # Trigger NPC turn
                game_event_manager.handle_next_step_trigger()
            
            # Get NpcDiceRollProcessedEvent
            npc_dice_events = event_recorder.find_all_events_with_data("npc_dice_roll_processed")
            assert len(npc_dice_events) >= 1
            
            npc_dice_event = npc_dice_events[0]
            normalized_event = self.normalize_event_for_snapshot(npc_dice_event.model_dump())
            
            # Convert to JSON string for snapshot
            import json
            event_json = json.dumps(normalized_event, indent=2, sort_keys=True)
            
            # Assert snapshot
            snapshot.assert_match(event_json, "npc_dice_roll_processed_event.json")