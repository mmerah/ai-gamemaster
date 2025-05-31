"""
BASIC COMBAT FLOW TEST

Tests a basic combat scenario with 2 characters vs 2 goblins, including:
- Combat initiation
- Initiative rolling and ordering
- Attack and damage rolls
- HP tracking and defeat conditions
- Turn advancement
- Event system verification

This is the foundational combat test that ensures core mechanics work correctly.
"""
import pytest
from unittest.mock import patch
import uuid
from app.ai_services.schemas import (
    AIResponse, 
    CombatStartUpdate,
    HPChangeUpdate,
    ConditionUpdate,
    DiceRequest,
    InitialCombatantData
)
from app.events.game_update_events import (
    CombatStartedEvent,
    PlayerDiceRequestAddedEvent,
    TurnAdvancedEvent
)
from .conftest import (
    setup_mock_ai_service_patching,
    verify_event_system_integrity,
    verify_required_event_types,
    verify_initiative_sequence
)


def test_basic_combat_flow(app, client, mock_ai_service, event_recorder, container, basic_party, golden_test):
    """Test a basic combat flow with 2 characters vs 2 goblins."""
    
    # Set up the mock AI service
    app.config['AI_SERVICE'] = mock_ai_service
    
    # Patch the _get_ai_service method on all event handlers to ensure they use our mock
    ai_service_patchers = setup_mock_ai_service_patching(container, mock_ai_service)
    
    # Clear any initial events
    event_recorder.clear()
    
    try:
        # ========== PHASE 1: Combat Start ==========
        
        # Player action triggers combat
        mock_ai_service.add_response(AIResponse(
            narrative="Two goblins jump out from the shadows! Roll for initiative!",
            reasoning="Starting combat",
            game_state_updates=[
                CombatStartUpdate(
                    combatants=[
                        InitialCombatantData(id="goblin1", name="Goblin Scout", hp=7, ac=15),
                        InitialCombatantData(id="goblin2", name="Goblin Warrior", hp=9, ac=13)
                    ]
                )
            ],
            dice_requests=[
                DiceRequest(
                    request_id=str(uuid.uuid4()),
                    character_ids=["all"],
                    type="initiative",
                    dice_formula="1d20",
                    reason="Roll for initiative!"
                )
            ]
        ))

        # Mock NPC initiative rolls
        with patch.object(container.get_dice_service(), 'perform_roll') as mock_dice:
            def initiative_side_effect(character_id, roll_type, **kwargs):
                if roll_type != "initiative":
                    return {"error": "Unexpected roll type"}
                    
                rolls = {
                    "goblin1": {"total_result": 14, "result_summary": "Initiative: 14"},
                    "goblin2": {"total_result": 10, "result_summary": "Initiative: 10"}
                }
                
                if character_id in rolls:
                    return {
                        "character_id": character_id,
                        "roll_type": "initiative",
                        **rolls[character_id]
                    }
                return {"error": f"Unknown character {character_id}"}
            
            mock_dice.side_effect = initiative_side_effect
            
            # Send player action
            response = client.post("/api/player_action", json={
                "action_type": "free_text",
                "value": "We explore the cave cautiously."
            })
            assert response.status_code == 200
        
        # Verify combat started
        combat_events = event_recorder.get_events_of_type(CombatStartedEvent)
        assert len(combat_events) == 1
        assert len(combat_events[0].combatants) == 4  # 2 party + 2 enemies
        
        # Verify dice requests were created
        dice_requests = event_recorder.get_events_of_type(PlayerDiceRequestAddedEvent)
        assert len(dice_requests) == 2  # One for each party member
        
        # ========== PHASE 2: Initiative Submission ==========
        
        # AI processes initiative and starts first turn (add BEFORE submitting rolls)
        mock_ai_service.add_response(AIResponse(
            narrative="Initiative determined! The fighter acts first!",
            reasoning="Setting turn order",
            end_turn=False,
            next_turn={"combatant_id": "fighter"}
        ))
        
        # Submit all player initiative rolls in a single call
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "wizard",
            "roll_type": "initiative",
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 12)],
            "total": 12
        }, {
            "character_id": "fighter",
            "roll_type": "initiative",
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 15)],
            "total": 15
        }])
        assert response.status_code == 200
        
        # ========== PHASE 3: Fighter Attack ==========
        
        # Fighter attacks
        mock_ai_service.add_response(AIResponse(
            narrative="Torvin swings his longsword at the goblin scout!",
            reasoning="Fighter attacks",
            dice_requests=[
                DiceRequest(
                    request_id=str(uuid.uuid4()),
                    character_ids=["fighter"],
                    type="attack",
                    dice_formula="1d20+5",
                    reason="Longsword attack",
                    dc=15  # Goblin AC
                )
            ]
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "I attack the goblin scout with my longsword!"
        })
        assert response.status_code == 200
        
        # AI requests damage (add BEFORE submitting attack roll)
        mock_ai_service.add_response(AIResponse(
            narrative="The sword strikes true! Roll for damage!",
            reasoning="Attack hit, rolling damage",
            dice_requests=[
                DiceRequest(
                    request_id=str(uuid.uuid4()),
                    character_ids=["fighter"],
                    type="damage",
                    dice_formula="1d8+3",
                    reason="Longsword damage"
                )
            ]
        ))
        
        # Submit attack roll (hit)
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "fighter",
            "roll_type": "attack",
            "dice_formula": "1d20+5",
            "dice_notation": "1d20+5",
            "dice_results": [(20, 13)],
            "total": 18  # Hit!
        }])
        assert response.status_code == 200
        
        # AI applies damage (add BEFORE submitting damage roll)
        mock_ai_service.add_response(AIResponse(
            narrative="The goblin scout takes 8 damage and falls!",
            reasoning="Apply damage, goblin defeated",
            game_state_updates=[
                HPChangeUpdate(
                    character_id="goblin1",
                    value=-8,
                    details={"source": "Fighter's longsword", "damage_type": "slashing"}
                ),
                ConditionUpdate(
                    type="condition_add",
                    character_id="goblin1",
                    value="defeated"
                )
            ],
            end_turn=True,
            next_turn={"combatant_id": "goblin2"}
        ))
        
        # Submit damage roll
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "fighter",
            "roll_type": "damage",
            "dice_formula": "1d8+3",
            "dice_notation": "1d8+3",
            "dice_results": [(8, 5)],
            "total": 8
        }])
        assert response.status_code == 200
        
        # ========== COMPREHENSIVE EVENT VERIFICATION ==========
        
        # Verify event system integrity
        event_stats = verify_event_system_integrity(event_recorder)
        
        # Verify required event types for combat
        verify_required_event_types(event_stats['event_types'], "Basic Combat")
        
        # Combat-specific event verification
        assert "CombatStartedEvent" in event_stats['event_types'], "Missing CombatStartedEvent"
        assert "PlayerDiceRequestAddedEvent" in event_stats['event_types'], "Missing PlayerDiceRequestAddedEvent"
        assert "TurnAdvancedEvent" in event_stats['event_types'], "Missing TurnAdvancedEvent"
        
        # Verify initiative processing occurred
        has_initiative = ("InitiativeOrderDeterminedEvent" in event_stats['event_types'] or 
                        "CombatantInitiativeSetEvent" in event_stats['event_types'])
        assert has_initiative, "No initiative processing events found"
        
        # Verify specific event counts and content
        combat_events = event_recorder.get_events_of_type(CombatStartedEvent)
        assert len(combat_events) == 1, f"Expected 1 CombatStartedEvent, got {len(combat_events)}"
        assert len(combat_events[0].combatants) == 4, f"Expected 4 combatants, got {len(combat_events[0].combatants)}"
        
        dice_requests = event_recorder.get_events_of_type(PlayerDiceRequestAddedEvent)
        assert len(dice_requests) >= 2, f"Expected at least 2 dice requests, got {len(dice_requests)}"
        
        # Enhanced verification: Initiative sequence verification
        all_events = event_recorder.get_all_events()
        verify_initiative_sequence(all_events, expected_combatant_count=4)
        
        # Verify all dice requests have required fields
        for dice_req in dice_requests:
            assert hasattr(dice_req, 'character_id'), "Dice request missing character_id"
            assert hasattr(dice_req, 'roll_type'), "Dice request missing roll_type"
            assert hasattr(dice_req, 'dice_formula'), "Dice request missing dice_formula"
        
        # Test golden file comparison
        golden_test(event_recorder, "basic_combat")
        
        print(f"✅ BASIC COMBAT TEST COMPLETE")
        print(f"   📊 Total Events: {event_stats['total_events']}")
        print(f"   🎲 Dice Requests: {len(dice_requests)}")
        print(f"   ⚔️  Combat Events: {len(combat_events)}")
        print(f"   📝 Event Types: {sorted(event_stats['event_types'])}")
        print(f"   ⏱️  Duration: {event_stats['last_timestamp'] - event_stats['first_timestamp'] if event_stats['first_timestamp'] else 0}ms")
    finally:
        # Stop all AI service patchers
        for patcher in ai_service_patchers:
            patcher.stop()