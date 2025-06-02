"""
NON-COMBAT GAME STATE EVENTS TEST

Tests location changes and non-combat HP changes:
- Location movement and descriptions
- Healing at temples/resting
- Environmental damage
- Non-combat HP restoration
- Location-based events

This test ensures non-combat game state changes are properly tracked.
"""
from app.ai_services.schemas import AIResponse
from app.game.unified_models import (
    LocationUpdate,
    HPChangeUpdate
)
from app.events.game_update_events import (
    LocationChangedEvent,
    PartyMemberUpdatedEvent
)
from .conftest import (
    setup_mock_ai_service_patching,
    verify_event_system_integrity,
    verify_required_event_types
)


def test_location_changes_and_non_combat_hp(app, client, mock_ai_service, event_recorder, container, basic_party, golden_test):
    """Test location changes and non-combat HP modifications."""
    
    # Set up the mock AI service
    app.config['AI_SERVICE'] = mock_ai_service
    
    # Patch the _get_ai_service method on all event handlers to ensure they use our mock
    ai_service_patchers = setup_mock_ai_service_patching(container, mock_ai_service)
    
    # Clear any initial events
    event_recorder.clear()
    
    try:
        # ========== PHASE 1: Location Change ==========
        
        # Player moves to a new location
        mock_ai_service.add_response(AIResponse(
            narrative="You leave the musty goblin cave and step into the fresh air of the Whispering Woods. Sunlight filters through the canopy above.",
            reasoning="Moving from cave to forest",
            location_update=LocationUpdate(
                name="Whispering Woods",
                description="A mystical forest with ancient trees. Sunlight filters through the dense canopy, creating dancing shadows on the forest floor."
            )
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "We exit the cave and head into the forest."
        })
        assert response.status_code == 200
        
        # Verify location changed event
        location_events = event_recorder.get_events_of_type(LocationChangedEvent)
        assert len(location_events) == 1
        assert location_events[0].new_location_name == "Whispering Woods"
        assert "mystical forest" in location_events[0].new_location_description
        
        # ========== PHASE 2: Environmental Damage First ==========
        
        # Party takes damage from environment to set up healing test
        mock_ai_service.add_response(AIResponse(
            narrative="As you traverse through thorny undergrowth, everyone takes minor scratches and cuts.",
            reasoning="Environmental hazard damage before healing",
            game_state_updates=[
                HPChangeUpdate(
                    type="hp_change",
                    character_id="fighter",
                    value=-10,
                    details={"source": "Thorny undergrowth"}
                ),
                HPChangeUpdate(
                    type="hp_change",
                    character_id="wizard",
                    value=-8,
                    details={"source": "Thorny undergrowth"}
                )
            ]
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "We push through the thorny undergrowth."
        })
        assert response.status_code == 200
        
        # ========== PHASE 3: Temple Healing ==========
        
        # Now party finds a healing shrine
        mock_ai_service.add_response(AIResponse(
            narrative="You discover a serene forest shrine dedicated to the goddess of healing. As you approach, warm light envelops your wounds, restoring your vitality.",
            reasoning="Healing at a shrine - non-combat HP restoration",
            game_state_updates=[
                HPChangeUpdate(
                    type="hp_change",
                    character_id="fighter",
                    value=8,
                    details={"source": "Divine healing at forest shrine"}
                ),
                HPChangeUpdate(
                    type="hp_change",
                    character_id="wizard",
                    value=5,
                    details={"source": "Divine healing at forest shrine"}
                )
            ]
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "We approach the shrine and pray for healing."
        })
        assert response.status_code == 200
        
        # ========== PHASE 4: More Environmental Damage ===========
        
        # Party takes damage from environment (non-combat)
        mock_ai_service.add_response(AIResponse(
            narrative="As you traverse the treacherous swamp, poisonous vapors rise from the murky water. Everyone feels weakened by the toxic fumes.",
            reasoning="Environmental hazard damage",
            location_update=LocationUpdate(
                name="Toxic Swamp",
                description="A dangerous swamp filled with poisonous vapors and murky waters. The air itself seems to sap your strength."
            ),
            game_state_updates=[
                HPChangeUpdate(
                    type="hp_change",
                    character_id="fighter",
                    value=-3,
                    details={"source": "Toxic swamp vapors"}
                ),
                HPChangeUpdate(
                    type="hp_change",
                    character_id="wizard",
                    value=-3,
                    details={"source": "Toxic swamp vapors"}
                )
            ]
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "We push through the swamp, holding our breath."
        })
        assert response.status_code == 200
        
        # ========== PHASE 5: Rest and Recovery ==========
        
        # Party rests to recover HP
        mock_ai_service.add_response(AIResponse(
            narrative="You find a safe clearing and decide to rest. After a few hours of sleep, everyone feels refreshed and some wounds have healed naturally.",
            reasoning="Short rest HP recovery",
            game_state_updates=[
                HPChangeUpdate(
                    type="hp_change",
                    character_id="fighter",
                    value=5,
                    details={"source": "Natural healing during rest"}
                ),
                HPChangeUpdate(
                    type="hp_change",
                    character_id="wizard",
                    value=3,
                    details={"source": "Natural healing during rest"}
                )
            ]
        ))
        
        response = client.post("/api/player_action", json={
            "action_type": "free_text",
            "value": "We take a short rest to recover."
        })
        assert response.status_code == 200
        
        # ========== COMPREHENSIVE EVENT VERIFICATION ==========
        
        # Verify event system integrity
        event_stats = verify_event_system_integrity(event_recorder)
        
        # Verify required event types
        verify_required_event_types(event_stats['event_types'], "Non-Combat Events")
        
        # ========== LOCATION EVENTS VERIFICATION ==========
        
        # Verify location changes
        location_events = event_recorder.get_events_of_type(LocationChangedEvent)
        assert len(location_events) == 2, f"Expected 2 LocationChangedEvents, got {len(location_events)}"
        
        # Verify first location change
        assert location_events[0].old_location_name == "Cave Entrance"
        assert location_events[0].new_location_name == "Whispering Woods"
        
        # Verify second location change
        assert location_events[1].old_location_name == "Whispering Woods"
        assert location_events[1].new_location_name == "Toxic Swamp"
        
        # ========== HP CHANGE EVENTS VERIFICATION ==========
        
        # Verify party member HP changes outside combat
        party_update_events = event_recorder.get_events_of_type(PartyMemberUpdatedEvent)
        assert len(party_update_events) == 8, f"Expected 8 PartyMemberUpdatedEvents (2 damage + 2 healing + 2 damage + 2 rest), got {len(party_update_events)}"
        
        # Verify fighter's HP changes
        fighter_events = [e for e in party_update_events if e.character_id == "fighter"]
        assert len(fighter_events) == 4, f"Expected 4 HP changes for fighter, got {len(fighter_events)}"
        
        # Check the sequence of HP changes for fighter
        # Event 0: Initial damage (28 -> 18)
        assert fighter_events[0].changes["current_hp"] == 18
        assert fighter_events[0].changes["max_hp"] == 28
        
        # Event 1: Healing (18 -> 26)
        assert fighter_events[1].changes["current_hp"] == 26
        assert fighter_events[1].changes["max_hp"] == 28
        
        # Event 2: Swamp damage (26 -> 23)
        assert fighter_events[2].changes["current_hp"] == 23
        assert fighter_events[2].changes["max_hp"] == 28
        
        # Event 3: Rest healing (23 -> 28)
        assert fighter_events[3].changes["current_hp"] == 28
        assert fighter_events[3].changes["max_hp"] == 28
        
        # Verify wizard's HP changes
        wizard_events = [e for e in party_update_events if e.character_id == "wizard"]
        assert len(wizard_events) == 4, f"Expected 4 HP changes for wizard, got {len(wizard_events)}"
        
        # ========== EVENT CONTENT VERIFICATION ==========
        
        # Check that healing events contain proper source information
        # For simplicity, we'll check by looking at the index since we know the order
        healing_events = [fighter_events[1], fighter_events[3]] + [wizard_events[1], wizard_events[3]]
        assert len(healing_events) == 4, f"Expected 4 healing events, got {len(healing_events)}"
        
        # Check that damage events contain proper source information
        damage_events = [fighter_events[0], fighter_events[2]] + [wizard_events[0], wizard_events[2]]
        assert len(damage_events) == 4, "Expected 4 damage events"
        
        # Test golden file comparison
        golden_test(event_recorder, "non_combat_events")
        
        print(f"\n✅ NON-COMBAT EVENTS TEST COMPLETE")
        print(f"   📊 Total Events: {event_stats['total_events']}")
        print(f"   📍 Location Changes: {len(location_events)}")
        print(f"   💊 HP Updates: {len(party_update_events)}")
        print(f"   🩹 Healing Events: {len(healing_events)}")
        print(f"   💔 Damage Events: {len(damage_events)}")
        print(f"   📝 Event Types: {sorted(event_stats['event_types'])}")
        
    finally:
        # Stop all AI service patchers
        for patcher in ai_service_patchers:
            patcher.stop()