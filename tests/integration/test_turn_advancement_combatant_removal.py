"""
Test to verify turn advancement event is emitted when combatant is removed.

This test ensures that when a combatant is defeated and removed from combat,
the TurnAdvancedEvent is properly emitted to notify the frontend.
"""
from unittest.mock import patch
import uuid
from app.ai_services.schemas import (
    AIResponse, 
    CombatStartUpdate,
    HPChangeUpdate,
    CombatantRemoveUpdate,
    DiceRequest,
    InitialCombatantData
)
from app.events.game_update_events import (
    CombatStartedEvent,
    TurnAdvancedEvent,
    CombatantRemovedEvent,
    CombatantHpChangedEvent
)
from tests.integration.comprehensive_backend.conftest import (
    setup_mock_ai_service_patching,
    verify_event_system_integrity,
    temp_saves_dir,
    app,
    client,
    mock_ai_service,
    event_recorder,
    container,
    basic_party
)


def test_turn_advancement_with_combatant_removal(app, client, mock_ai_service, event_recorder, container, basic_party):
    """Test that TurnAdvancedEvent is emitted when turn advances after combatant removal."""
    
    # Set up the mock AI service
    app.config['AI_SERVICE'] = mock_ai_service
    
    # Patch the _get_ai_service method on all event handlers
    ai_service_patchers = setup_mock_ai_service_patching(container, mock_ai_service)
    
    # Clear any initial events
    event_recorder.clear()
    
    try:
        # ========== PHASE 1: Combat Start ==========
        
        # Player action triggers combat with 2 goblins
        mock_ai_service.add_response(AIResponse(
            narrative="Two goblins jump out to attack! Roll for initiative!",
            reasoning="Starting combat with goblins",
            game_state_updates=[
                CombatStartUpdate(
                    combatants=[
                        InitialCombatantData(id="gob_A", name="Goblin A", hp=10, ac=12),
                        InitialCombatantData(id="gob_B", name="Goblin B", hp=10, ac=12)
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
                    "gob_A": {"total_result": 8, "result_summary": "Initiative: 8"},
                    "gob_B": {"total_result": 5, "result_summary": "Initiative: 5"}
                }
                
                if character_id in rolls:
                    return {
                        "character_id": character_id,
                        "roll_type": "initiative",
                        **rolls[character_id]
                    }
                return {"error": f"Unknown character {character_id}"}
            
            mock_dice.side_effect = initiative_side_effect
            
            # Send player action to trigger combat
            response = client.post("/api/player_action", json={
                "action_type": "free_text",
                "value": "Attack the goblins!"
            })
            assert response.status_code == 200
        
        # Verify combat started
        combat_events = event_recorder.get_events_of_type(CombatStartedEvent)
        assert len(combat_events) == 1
        assert len(combat_events[0].combatants) == 4  # 2 party + 2 goblins
        
        # ========== PHASE 2: Initiative Submission ==========
        
        # AI processes initiative and starts first turn
        mock_ai_service.add_response(AIResponse(
            narrative="Battle begins! Torvin acts first!",
            reasoning="Initiative order determined",
            end_turn=False,
            next_turn={"combatant_id": "fighter"}
        ))
        
        # Submit player initiative rolls
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "wizard",
            "roll_type": "initiative",
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 10)],
            "total": 10
        }, {
            "character_id": "fighter",
            "roll_type": "initiative", 
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 18)],
            "total": 18  # Fighter has highest initiative
        }])
        assert response.status_code == 200
        
        # ========== PHASE 3: Fighter Attack - Kill Goblin B ==========
        
        # Fighter declares attack
        mock_ai_service.add_response(AIResponse(
            narrative="Torvin swings his sword at Goblin B!",
            reasoning="Fighter attacks Goblin B",
            dice_requests=[
                DiceRequest(
                    request_id=str(uuid.uuid4()),
                    character_ids=["fighter"],
                    type="attack",
                    dice_formula="1d20+5",
                    reason="Sword attack",
                    dc=12  # Goblin AC
                )
            ]
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "I attack Goblin B!"
        })
        assert response.status_code == 200
        
        # AI requests damage roll
        mock_ai_service.add_response(AIResponse(
            narrative="Hit! Roll for damage!",
            reasoning="Attack hit, rolling damage",
            dice_requests=[
                DiceRequest(
                    request_id=str(uuid.uuid4()),
                    character_ids=["fighter"],
                    type="damage",
                    dice_formula="1d8+3",
                    reason="Sword damage"
                )
            ]
        ))
        
        # Submit attack roll (hit)
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "fighter",
            "roll_type": "attack",
            "dice_formula": "1d20+5",
            "dice_notation": "1d20+5",
            "dice_results": [(20, 15)],
            "total": 20  # Hit!
        }])
        assert response.status_code == 200
        
        # AI applies damage, removes combatant, and advances turn
        mock_ai_service.add_response(AIResponse(
            narrative="The attack strikes true, felling the goblin! Elara, you're up!",
            reasoning="Goblin B defeated, removing from combat and advancing turn",
            game_state_updates=[
                HPChangeUpdate(
                    character_id="gob_B",
                    value=-12,
                    details={"source": "Fighter's attack"}
                ),
                CombatantRemoveUpdate(
                    character_id="gob_B",
                    details={"reason": "Defeated in combat"}
                )
            ],
            end_turn=True,  # AI signals turn should end
            next_turn={"combatant_id": "wizard"}  # Next in initiative order
        ))
        
        # Submit damage roll
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "fighter",
            "roll_type": "damage",
            "dice_formula": "1d8+3",
            "dice_notation": "1d8+3",
            "dice_results": [(8, 7)],
            "total": 10
        }])
        assert response.status_code == 200
        
        # ========== VERIFY EVENTS ==========
        
        # Verify event system integrity
        event_stats = verify_event_system_integrity(event_recorder)
        
        # Get all events for analysis
        all_events = event_recorder.get_all_events()
        
        # Check for combatant removal event
        removal_events = event_recorder.get_events_of_type(CombatantRemovedEvent)
        assert len(removal_events) == 1, f"Expected 1 combatant_removed event, got {len(removal_events)}"
        assert removal_events[0].combatant_id == 'gob_B'
        assert removal_events[0].reason == 'Defeated in combat'
        
        # Check for turn advancement event
        turn_advanced_events = event_recorder.get_events_of_type(TurnAdvancedEvent)
        assert len(turn_advanced_events) >= 1, f"Expected at least 1 turn_advanced event, got {len(turn_advanced_events)}"
        
        # Find the turn advancement that happened after the removal
        # It should be one of the last events
        last_turn_event = turn_advanced_events[-1]
        assert hasattr(last_turn_event, 'new_combatant_id')
        assert hasattr(last_turn_event, 'new_combatant_name')
        assert hasattr(last_turn_event, 'round_number')
        assert hasattr(last_turn_event, 'is_new_round')
        assert hasattr(last_turn_event, 'is_player_controlled')
        
        # Verify the turn advanced to wizard (next in order after fighter)
        assert last_turn_event.new_combatant_id == 'wizard'
        assert last_turn_event.new_combatant_name == 'Elara'
        
        # Verify HP change event
        hp_events = event_recorder.get_events_of_type(CombatantHpChangedEvent)
        hp_change_for_gob_b = [e for e in hp_events if e.combatant_id == 'gob_B']
        assert len(hp_change_for_gob_b) >= 1, "Expected HP change event for defeated goblin"
        assert hp_change_for_gob_b[-1].new_hp == 0, "Goblin should be at 0 HP"
        
        print(f"✅ TURN ADVANCEMENT WITH REMOVAL TEST COMPLETE")
        print(f"   📊 Total Events: {event_stats['total_events']}")
        print(f"   ❌ Removal Events: {len(removal_events)}")
        print(f"   🔄 Turn Advanced Events: {len(turn_advanced_events)}")
        print(f"   💔 HP Change Events: {len(hp_events)}")
        print(f"   📝 Event Types: {sorted(event_stats['event_types'])}")
        
    finally:
        # Stop all AI service patchers
        for patcher in ai_service_patchers:
            patcher.stop()


def test_turn_advancement_multiple_removals(app, client, mock_ai_service, event_recorder, container, basic_party):
    """Test turn advancement when multiple combatants are removed in one action."""
    
    # Set up the mock AI service
    app.config['AI_SERVICE'] = mock_ai_service
    
    # Patch the _get_ai_service method on all event handlers
    ai_service_patchers = setup_mock_ai_service_patching(container, mock_ai_service)
    
    # Clear any initial events
    event_recorder.clear()
    
    try:
        # ========== PHASE 1: Combat Start with 3 Goblins ==========
        
        mock_ai_service.add_response(AIResponse(
            narrative="Three goblins attack! Roll for initiative!",
            reasoning="Starting combat",
            game_state_updates=[
                CombatStartUpdate(
                    combatants=[
                        InitialCombatantData(id="gob_A", name="Goblin A", hp=5, ac=12),
                        InitialCombatantData(id="gob_B", name="Goblin B", hp=5, ac=12),
                        InitialCombatantData(id="gob_C", name="Goblin C", hp=5, ac=12)
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
                    "gob_A": {"total_result": 7, "result_summary": "Initiative: 7"},
                    "gob_B": {"total_result": 5, "result_summary": "Initiative: 5"},
                    "gob_C": {"total_result": 3, "result_summary": "Initiative: 3"}
                }
                
                if character_id in rolls:
                    return {
                        "character_id": character_id,
                        "roll_type": "initiative",
                        **rolls[character_id]
                    }
                return {"error": f"Unknown character {character_id}"}
            
            mock_dice.side_effect = initiative_side_effect
            
            # Trigger combat
            response = client.post("/api/player_action", json={
                "action_type": "free_text",
                "value": "Attack!"
            })
            assert response.status_code == 200
        
        # ========== PHASE 2: Initiative and First Turn ==========
        
        mock_ai_service.add_response(AIResponse(
            narrative="The wizard acts first!",
            reasoning="Initiative determined",
            end_turn=False,
            next_turn={"combatant_id": "wizard"}
        ))
        
        # Submit player initiative
        response = client.post("/api/submit_rolls", json=[{
            "character_id": "wizard",
            "roll_type": "initiative",
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 15)],
            "total": 15  # Wizard has highest initiative
        }, {
            "character_id": "fighter",
            "roll_type": "initiative",
            "dice_formula": "1d20",
            "dice_notation": "1d20",
            "dice_results": [(20, 10)],
            "total": 10
        }])
        assert response.status_code == 200
        
        # ========== PHASE 3: Wizard Casts Fireball - Kills 2 Goblins ==========
        
        # Wizard casts area effect spell
        mock_ai_service.add_response(AIResponse(
            narrative="Elara casts Fireball! The explosion engulfs goblins A and B! Torvin, you're next!",
            reasoning="Area attack hits and defeats multiple enemies",
            game_state_updates=[
                HPChangeUpdate(
                    character_id="gob_A",
                    value=-10,
                    details={"source": "Fireball", "damage_type": "fire"}
                ),
                CombatantRemoveUpdate(
                    character_id="gob_A",
                    details={"reason": "Defeated"}
                ),
                HPChangeUpdate(
                    character_id="gob_B", 
                    value=-10,
                    details={"source": "Fireball", "damage_type": "fire"}
                ),
                CombatantRemoveUpdate(
                    character_id="gob_B",
                    details={"reason": "Defeated"}
                )
            ],
            end_turn=True,  # Wizard's turn ends
            next_turn={"combatant_id": "fighter"}  # Next in order
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "I cast fireball at the goblins!"
        })
        assert response.status_code == 200
        
        # ========== VERIFY EVENTS ==========
        
        # Get all events
        removal_events = event_recorder.get_events_of_type(CombatantRemovedEvent)
        turn_advanced_events = event_recorder.get_events_of_type(TurnAdvancedEvent)
        
        # Should have 2 removal events
        assert len(removal_events) == 2, f"Expected 2 removal events, got {len(removal_events)}"
        removed_ids = {e.combatant_id for e in removal_events}
        assert removed_ids == {'gob_A', 'gob_B'}, f"Wrong combatants removed: {removed_ids}"
        
        # Should have turn advancement event(s)
        assert len(turn_advanced_events) >= 1, f"Expected turn advancement, got {len(turn_advanced_events)}"
        
        # The last turn event should advance to fighter
        last_turn_event = turn_advanced_events[-1]
        assert last_turn_event.new_combatant_id == 'fighter'
        
        print(f"✅ MULTIPLE REMOVAL TEST COMPLETE")
        print(f"   ❌ Combatants Removed: {len(removal_events)}")
        print(f"   🔄 Turn Advanced to: {last_turn_event.new_combatant_name}")
        
    finally:
        # Stop all AI service patchers
        for patcher in ai_service_patchers:
            patcher.stop()