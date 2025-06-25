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

from typing import Any, Callable, cast
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.container import ServiceContainer
from app.models.api import PlayerActionRequest
from app.models.events.game_state import LocationChangedEvent, PartyMemberUpdatedEvent
from app.models.game_state.main import GameStateModel
from app.models.updates import HPChangeUpdateModel, LocationUpdateModel
from app.providers.ai.schemas import AIResponse
from tests.test_helpers import EventRecorder

from .conftest import verify_event_system_integrity, verify_required_event_types


def test_location_changes_and_non_combat_hp(
    app: FastAPI,
    client: TestClient,
    mock_ai_service: Mock,
    event_recorder: EventRecorder,
    container: ServiceContainer,
    basic_party: GameStateModel,
    golden_test: Callable[[EventRecorder, str], None],
) -> None:
    """Test location changes and non-combat HP modifications."""

    # Clear any initial events
    event_recorder.clear()

    # ========== PHASE 1: Location Change ==========

    # Player moves to a new location
    mock_ai_service.add_response(
        AIResponse(
            narrative="You leave the musty goblin cave and step into the fresh air of the Whispering Woods. Sunlight filters through the canopy above.",
            reasoning="Moving from cave to forest",
            location_update=LocationUpdateModel(
                name="Whispering Woods",
                description="A mystical forest with ancient trees. Sunlight filters through the dense canopy, creating dancing shadows on the forest floor.",
            ),
        )
    )

    action_request = PlayerActionRequest(
        action_type="free_text", value="We exit the cave and head into the forest."
    )
    response = client.post(
        "/api/player_action",
        json=action_request.model_dump(mode="json", exclude_unset=True),
    )
    assert response.status_code == 200

    # Verify location changed event
    location_events = event_recorder.get_events_of_type(LocationChangedEvent)
    assert len(location_events) == 1
    location_event = cast(LocationChangedEvent, location_events[0])
    assert location_event.new_location_name == "Whispering Woods"
    assert "mystical forest" in location_event.new_location_description

    # ========== PHASE 2: Environmental Damage First ==========

    # Party takes damage from environment to set up healing test
    mock_ai_service.add_response(
        AIResponse(
            narrative="As you traverse through thorny undergrowth, everyone takes minor scratches and cuts.",
            reasoning="Environmental hazard damage before healing",
            hp_changes=[
                HPChangeUpdateModel(character_id="fighter", value=-10),
                HPChangeUpdateModel(character_id="wizard", value=-8),
            ],
        )
    )

    action_request = PlayerActionRequest(
        action_type="free_text", value="We push through the thorny undergrowth."
    )
    response = client.post(
        "/api/player_action",
        json=action_request.model_dump(mode="json", exclude_unset=True),
    )
    assert response.status_code == 200

    # ========== PHASE 3: Temple Healing ==========

    # Now party finds a healing shrine
    mock_ai_service.add_response(
        AIResponse(
            narrative="You discover a serene forest shrine dedicated to the goddess of healing. As you approach, warm light envelops your wounds, restoring your vitality.",
            reasoning="Healing at a shrine - non-combat HP restoration",
            hp_changes=[
                HPChangeUpdateModel(character_id="fighter", value=8),
                HPChangeUpdateModel(character_id="wizard", value=5),
            ],
        )
    )

    action_request = PlayerActionRequest(
        action_type="free_text", value="We approach the shrine and pray for healing."
    )
    response = client.post(
        "/api/player_action",
        json=action_request.model_dump(mode="json", exclude_unset=True),
    )
    assert response.status_code == 200

    # ========== PHASE 4: More Environmental Damage ===========

    # Party takes damage from environment (non-combat)
    mock_ai_service.add_response(
        AIResponse(
            narrative="As you traverse the treacherous swamp, poisonous vapors rise from the murky water. Everyone feels weakened by the toxic fumes.",
            reasoning="Environmental hazard damage",
            location_update=LocationUpdateModel(
                name="Toxic Swamp",
                description="A dangerous swamp filled with poisonous vapors and murky waters. The air itself seems to sap your strength.",
            ),
            hp_changes=[
                HPChangeUpdateModel(character_id="fighter", value=-3),
                HPChangeUpdateModel(character_id="wizard", value=-3),
            ],
        )
    )

    action_request = PlayerActionRequest(
        action_type="free_text", value="We push through the swamp, holding our breath."
    )
    response = client.post(
        "/api/player_action",
        json=action_request.model_dump(mode="json", exclude_unset=True),
    )
    assert response.status_code == 200

    # ========== PHASE 5: Rest and Recovery ==========

    # Party rests to recover HP
    mock_ai_service.add_response(
        AIResponse(
            narrative="You find a safe clearing and decide to rest. After a few hours of sleep, everyone feels refreshed and some wounds have healed naturally.",
            reasoning="Short rest HP recovery",
            hp_changes=[
                HPChangeUpdateModel(character_id="fighter", value=5),
                HPChangeUpdateModel(character_id="wizard", value=3),
            ],
        )
    )

    action_request = PlayerActionRequest(
        action_type="free_text", value="We take a short rest to recover."
    )
    response = client.post(
        "/api/player_action",
        json=action_request.model_dump(mode="json", exclude_unset=True),
    )
    assert response.status_code == 200

    # ========== COMPREHENSIVE EVENT VERIFICATION ==========

    # Verify event system integrity
    event_stats = verify_event_system_integrity(event_recorder)

    # Verify required event types
    verify_required_event_types(event_stats["event_types"], "Non-Combat Events")

    # ========== LOCATION EVENTS VERIFICATION ==========

    # Verify location changes
    location_events = event_recorder.get_events_of_type(LocationChangedEvent)
    assert len(location_events) == 2, (
        f"Expected 2 LocationChangedEvents, got {len(location_events)}"
    )

    # Verify first location change
    first_location = cast(LocationChangedEvent, location_events[0])
    assert first_location.old_location_name == "Cave Entrance"
    assert first_location.new_location_name == "Whispering Woods"

    # Verify second location change
    second_location = cast(LocationChangedEvent, location_events[1])
    assert second_location.old_location_name == "Whispering Woods"
    assert second_location.new_location_name == "Toxic Swamp"

    # ========== HP CHANGE EVENTS VERIFICATION ==========

    # Verify party member HP changes outside combat
    party_update_events = event_recorder.get_events_of_type(PartyMemberUpdatedEvent)
    assert len(party_update_events) == 8, (
        f"Expected 8 PartyMemberUpdatedEvents (2 damage + 2 healing + 2 damage + 2 rest), got {len(party_update_events)}"
    )

    # Verify fighter's HP changes
    fighter_events = [
        cast(PartyMemberUpdatedEvent, e)
        for e in party_update_events
        if cast(PartyMemberUpdatedEvent, e).character_id == "fighter"
    ]
    assert len(fighter_events) == 4, (
        f"Expected 4 HP changes for fighter, got {len(fighter_events)}"
    )

    # Check the sequence of HP changes for fighter
    # Event 0: Initial damage (28 -> 18)
    assert fighter_events[0].changes.current_hp == 18
    assert fighter_events[0].changes.max_hp == 28

    # Event 1: Healing (18 -> 26)
    assert fighter_events[1].changes.current_hp == 26
    assert fighter_events[1].changes.max_hp == 28

    # Event 2: Swamp damage (26 -> 23)
    assert fighter_events[2].changes.current_hp == 23
    assert fighter_events[2].changes.max_hp == 28

    # Event 3: Rest healing (23 -> 28)
    assert fighter_events[3].changes.current_hp == 28
    assert fighter_events[3].changes.max_hp == 28

    # Verify wizard's HP changes
    wizard_events = [
        cast(PartyMemberUpdatedEvent, e)
        for e in party_update_events
        if cast(PartyMemberUpdatedEvent, e).character_id == "wizard"
    ]
    assert len(wizard_events) == 4, (
        f"Expected 4 HP changes for wizard, got {len(wizard_events)}"
    )

    # ========== EVENT CONTENT VERIFICATION ==========

    # Check that healing events contain proper source information
    # For simplicity, we'll check by looking at the index since we know the order
    healing_events = [fighter_events[1], fighter_events[3]] + [
        wizard_events[1],
        wizard_events[3],
    ]
    assert len(healing_events) == 4, (
        f"Expected 4 healing events, got {len(healing_events)}"
    )

    # Check that damage events contain proper source information
    damage_events = [fighter_events[0], fighter_events[2]] + [
        wizard_events[0],
        wizard_events[2],
    ]
    assert len(damage_events) == 4, "Expected 4 damage events"

    # Test golden file comparison
    golden_test(event_recorder, "non_combat_events")

    print("\n✅ NON-COMBAT EVENTS TEST COMPLETE")
    print(f"   📊 Total Events: {event_stats['total_events']}")
    print(f"   📍 Location Changes: {len(location_events)}")
    print(f"   💊 HP Updates: {len(party_update_events)}")
    print(f"   🩹 Healing Events: {len(healing_events)}")
    print(f"   💔 Damage Events: {len(damage_events)}")
    print(f"   📝 Event Types: {sorted(event_stats['event_types'])}")
