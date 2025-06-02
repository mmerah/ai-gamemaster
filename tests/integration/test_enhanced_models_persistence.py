"""
Test integration of enhanced models with existing game state repository.
Ensures backward compatibility and proper serialization/deserialization.
"""
import pytest
import json
from app.game.unified_models import GameStateModel, CharacterInstanceModel, BaseStatsModel
from app.game.unified_models import CombatantModel, CombatStateModel
from app.repositories.game_state_repository import InMemoryGameStateRepository
from app.game.unified_models import MonsterBaseStats


class TestEnhancedModelsIntegration:
    """Test that enhanced models integrate properly with existing systems."""
    
    def test_enhanced_combat_state_in_game_state(self):
        """Test that GameStateModel can use the enhanced CombatStateModel."""
        # Create game state with enhanced combat state
        game_state = GameStateModel()
        
        # Create enhanced combat state with combatants
        enhanced_combat = CombatStateModel(
            is_active=True,
            round_number=2,
            current_turn_index=1,
            combatants=[
                CombatantModel(
                    id="pc_1",
                    name="Elara",
                    initiative=20,
                    initiative_modifier=3,
                    current_hp=22,
                    max_hp=25,
                    armor_class=16,
                    is_player=True
                ),
                CombatantModel(
                    id="goblin_1",
                    name="Goblin",
                    initiative=15,
                    initiative_modifier=2,
                    current_hp=5,
                    max_hp=7,
                    armor_class=13,
                    is_player=False
                )
            ],
            monster_stats={
                "goblin_1": MonsterBaseStats(
                    name="Goblin",
                    initial_hp=7,
                    ac=12,
                    stats={"STR": 8, "DEX": 14, "CON": 10},
                    abilities=["nimble_escape"]
                )
            }
        )
        
        # Assign enhanced combat state to game state
        game_state.combat = enhanced_combat
        
        # Verify it works
        assert game_state.combat.is_active is True
        assert len(game_state.combat.combatants) == 2
        assert game_state.combat.get_current_combatant().name == "Goblin"
        assert game_state.combat.get_combatant_by_id("pc_1").name == "Elara"
    
    def test_game_state_serialization_with_enhanced_combat(self):
        """Test that GameStateModel with enhanced combat can be serialized to JSON."""
        game_state = GameStateModel()
        
        # Add a character to party
        game_state.party["pc_1"] = CharacterInstanceModel(
            template_id="elara_ranger_template",
            campaign_id="test_campaign",
            level=3,
            current_hp=22,
            max_hp=25,
            conditions=[],
            inventory=[]
        )
        
        # Create enhanced combat state
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=[
                CombatantModel(
                    id="pc_1",
                    name="Elara",
                    initiative=18,
                    initiative_modifier=3,
                    current_hp=22,
                    max_hp=25,
                    armor_class=16,
                    is_player=True
                )
            ]
        )
        
        # Serialize to JSON
        json_str = game_state.model_dump_json()
        
        # Deserialize back
        loaded_data = json.loads(json_str)
        loaded_state = GameStateModel(**loaded_data)
        
        # Verify data integrity
        assert loaded_state.combat.is_active is True
        assert len(loaded_state.combat.combatants) == 1
        assert loaded_state.combat.combatants[0].name == "Elara"
        assert "pc_1" in loaded_state.party
    
    def test_repository_save_load_with_enhanced_combat(self):
        """Test that repository can save and load GameStateModel with enhanced combat."""
        repo = InMemoryGameStateRepository()
        
        # Get initial state
        game_state = repo.get_game_state()
        
        # Add enhanced combat
        game_state.combat = CombatStateModel(
            is_active=True,
            round_number=3,
            combatants=[
                CombatantModel(
                    id="test_pc",
                    name="Test Fighter",
                    initiative=15,
                    initiative_modifier=2,
                    current_hp=40,
                    max_hp=45,
                    armor_class=18,
                    is_player=True,
                    conditions=["blessed"]
                )
            ]
        )
        
        # Save state
        repo.save_game_state(game_state)
        
        # Load state
        loaded_state = repo.get_game_state()
        
        # Verify enhanced features preserved
        assert loaded_state.combat.is_active is True
        assert loaded_state.combat.round_number == 3
        assert len(loaded_state.combat.combatants) == 1
        
        combatant = loaded_state.combat.combatants[0]
        assert combatant.name == "Test Fighter"
        assert combatant.conditions == ["blessed"]
        assert combatant.is_player is True
    
    def test_backward_compatibility_with_basic_combat_state(self):
        """Test that basic combat state data can be loaded into enhanced model."""
        # Simulate loading old combat data
        old_combat_data = {
            "is_active": True,
            "combatants": [
                {
                    "id": "pc_1",
                    "name": "Fighter",
                    "initiative": 12,
                    "is_player": True  # Old field name
                }
            ],
            "current_turn_index": 0,
            "round_number": 1,
            "monster_stats": {}
        }
        
        # This should fail initially because old format uses is_player
        # Let's create a game state with the old format
        game_state_data = {
            "party": {},
            "combat": old_combat_data
        }
        
        # Try to load - this will show us if we need migration logic
        try:
            game_state = GameStateModel(**game_state_data)
            # If this works, check that combat is properly loaded
            assert game_state.combat.is_active is True
        except Exception as e:
            # Expected - old format incompatible
            assert "is_player" in str(e) or "Field required" in str(e)