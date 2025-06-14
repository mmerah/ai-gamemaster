"""
Shared fixtures and utilities for comprehensive backend tests.

Contains common test infrastructure including:
- Mock AI service setup
- Event recording and verification
- Golden event log comparison
- Test data fixtures (party, game state)
"""

import json
import os
import tempfile
from typing import Any, Dict, Generator, List, Optional, Set
from unittest.mock import MagicMock

import pytest

from app.core.interfaces import GameStateRepository
from app.models.character import CharacterInstanceModel, CharacterTemplateModel
from app.models.game_state import GameStateModel
from app.models.utils import (
    BaseStatsModel,
    LocationModel,
    ProficienciesModel,
    QuestModel,
)
from tests.test_helpers import EventRecorder


def verify_event_system_integrity(event_recorder: EventRecorder) -> Dict[str, Any]:
    """
    Comprehensive verification of the event system integrity.

    This function ensures all events are properly recorded, ordered, and contain
    the expected data structures for frontend consumption.
    """
    all_events = event_recorder.get_all_events()

    # Verify basic event structure
    for i, event in enumerate(all_events):
        assert hasattr(event, "event_type"), f"Event {i} missing event_type"
        assert hasattr(event, "timestamp"), f"Event {i} missing timestamp"
        assert hasattr(event, "sequence_number"), f"Event {i} missing sequence_number"
        assert event.sequence_number >= 0, f"Event {i} has invalid sequence_number"

        # Verify timestamp order (should be increasing)
        if i > 0:
            assert event.timestamp >= all_events[i - 1].timestamp, (
                f"Event {i} timestamp out of order"
            )
            assert event.sequence_number > all_events[i - 1].sequence_number, (
                f"Event {i} sequence out of order"
            )

    # Verify no gaps in sequence numbers
    assert not event_recorder.has_gaps(), "Event recorder detected sequence gaps"

    # Enhanced verification: Check event payload integrity
    _verify_event_payload_integrity(all_events)

    return {
        "total_events": len(all_events),
        "event_types": set(type(e).__name__ for e in all_events),
        "first_timestamp": all_events[0].timestamp if all_events else None,
        "last_timestamp": all_events[-1].timestamp if all_events else None,
        "sequence_range": (
            all_events[0].sequence_number,
            all_events[-1].sequence_number,
        )
        if all_events
        else (0, 0),
    }


def verify_required_event_types(event_types: Set[str], test_name: str) -> bool:
    """
    Verify that required event types are present based on test type.
    """
    # Core events that should be in every test
    core_events = {"BackendProcessingEvent", "NarrativeAddedEvent"}

    for event_type in core_events:
        assert event_type in event_types, (
            f"{test_name}: Missing required event type {event_type}"
        )

    return True


def _verify_event_payload_integrity(all_events: List[Any]) -> None:
    """
    Enhanced event payload verification.

    Verifies that critical event fields contain correct values and that
    event sequences follow expected patterns.
    """
    # Group events by type for specific verification
    events_by_type: Dict[str, List[Any]] = {}
    for event in all_events:
        event_type = type(event).__name__
        if event_type not in events_by_type:
            events_by_type[event_type] = []
        events_by_type[event_type].append(event)

    # Verify HP Change Events
    if "CombatantHpChangedEvent" in events_by_type:
        for hp_event in events_by_type["CombatantHpChangedEvent"]:
            assert hasattr(hp_event, "combatant_id"), "HP event missing combatant_id"
            assert hasattr(hp_event, "change_amount"), "HP event missing change_amount"
            assert hasattr(hp_event, "new_hp"), "HP event missing new_hp"
            assert hasattr(hp_event, "old_hp"), "HP event missing old_hp"
            assert hasattr(hp_event, "max_hp"), "HP event missing max_hp"

            # Verify HP math consistency (with proper clamping to 0)
            if (
                hasattr(hp_event, "old_hp")
                and hasattr(hp_event, "new_hp")
                and hasattr(hp_event, "change_amount")
            ):
                expected_new_hp = max(
                    0, hp_event.old_hp + hp_event.change_amount
                )  # HP cannot go below 0
                assert hp_event.new_hp == expected_new_hp, (
                    f"HP math inconsistent: max(0, {hp_event.old_hp} + {hp_event.change_amount}) = {expected_new_hp} != {hp_event.new_hp}"
                )

    # Verify Condition Change Events
    if "CombatantStatusChangedEvent" in events_by_type:
        for condition_event in events_by_type["CombatantStatusChangedEvent"]:
            assert hasattr(condition_event, "combatant_id"), (
                "Condition event missing combatant_id"
            )
            assert hasattr(condition_event, "added_conditions") or hasattr(
                condition_event, "removed_conditions"
            ), "Condition event missing condition changes"

    # Verify Turn Advancement Events
    if "TurnAdvancedEvent" in events_by_type:
        for turn_event in events_by_type["TurnAdvancedEvent"]:
            assert hasattr(turn_event, "new_combatant_id"), (
                "Turn event missing new_combatant_id"
            )
            assert hasattr(turn_event, "new_combatant_name"), (
                "Turn event missing new_combatant_name"
            )
            assert hasattr(turn_event, "round_number"), (
                "Turn event missing round_number"
            )
            assert turn_event.round_number >= 1, "Invalid round number"

    # Verify Initiative Events Sequence
    if "CombatStartedEvent" in events_by_type:
        combat_started_events = events_by_type["CombatStartedEvent"]

        for combat_event in combat_started_events:
            assert hasattr(combat_event, "combatants"), (
                "Combat started event missing combatants"
            )
            assert len(combat_event.combatants) > 0, "Combat started with no combatants"

            # Each combatant should have required fields
            for combatant in combat_event.combatants:
                # Handle both dict and CombatantModel objects
                if hasattr(combatant, "id"):
                    # It's a CombatantModel object
                    assert combatant.id is not None, "CombatantModel missing id"
                    assert combatant.name is not None, "CombatantModel missing name"
                    assert combatant.current_hp is not None, (
                        "CombatantModel missing current_hp"
                    )
                else:
                    # It's a dict (legacy)
                    assert "id" in combatant, "CombatantModel missing id"
                    assert "name" in combatant, "CombatantModel missing name"
                    assert "current_hp" in combatant or "hp" in combatant, (
                        "CombatantModel missing current_hp/hp"
                    )
                    assert "max_hp" in combatant, "CombatantModel missing max_hp"

    # Verify Dice Request Events
    if "PlayerDiceRequestAddedEvent" in events_by_type:
        for dice_event in events_by_type["PlayerDiceRequestAddedEvent"]:
            assert hasattr(dice_event, "character_id"), (
                "Dice request missing character_id"
            )
            assert hasattr(dice_event, "roll_type"), "Dice request missing roll_type"
            assert hasattr(dice_event, "dice_formula"), (
                "Dice request missing dice_formula"
            )
            assert hasattr(dice_event, "purpose"), "Dice request missing purpose"

            # Verify dice formula format
            assert dice_event.dice_formula, "Empty dice formula"
            # Basic format check (should contain 'd' for dice)
            if "d" not in dice_event.dice_formula.lower():
                assert False, f"Invalid dice formula format: {dice_event.dice_formula}"

    # Verify Backend Processing Events come in pairs
    if "BackendProcessingEvent" in events_by_type:
        processing_events = events_by_type["BackendProcessingEvent"]

        # Should have both start (is_processing=True) and end (is_processing=False) events
        start_events = [
            e for e in processing_events if getattr(e, "is_processing", False)
        ]
        end_events = [
            e for e in processing_events if not getattr(e, "is_processing", True)
        ]

        # We should have at least one of each type
        assert len(start_events) > 0, "No backend processing start events found"
        assert len(end_events) > 0, "No backend processing end events found"


def verify_initiative_sequence(
    all_events: List[Any], expected_combatant_count: int
) -> None:
    """
    Verify that initiative sequence events follow the expected pattern.
    """
    initiative_set_events = [
        e for e in all_events if type(e).__name__ == "CombatantInitiativeSetEvent"
    ]
    initiative_order_events = [
        e for e in all_events if type(e).__name__ == "InitiativeOrderDeterminedEvent"
    ]
    turn_advanced_events = [
        e for e in all_events if type(e).__name__ == "TurnAdvancedEvent"
    ]

    # Should have initiative set events for each combatant (or at least some if NPCs auto-roll)
    if initiative_set_events:
        assert len(initiative_set_events) <= expected_combatant_count, (
            f"Too many initiative set events: {len(initiative_set_events)} > {expected_combatant_count}"
        )

    # Should have exactly one initiative order determination
    if initiative_order_events:
        assert len(initiative_order_events) == 1, (
            f"Expected 1 initiative order event, got {len(initiative_order_events)}"
        )

        order_event = initiative_order_events[0]
        assert hasattr(order_event, "ordered_combatants"), (
            "Initiative order event missing ordered_combatants"
        )

    # Should have at least one turn advancement (to first combatant)
    if turn_advanced_events:
        assert len(turn_advanced_events) >= 1, (
            f"Expected at least 1 turn advancement, got {len(turn_advanced_events)}"
        )

    # Verify sequence order: initiative sets should come before order determination, which should come before turn advancement
    if initiative_set_events and initiative_order_events:
        last_init_set = max(e.sequence_number for e in initiative_set_events)
        first_order = min(e.sequence_number for e in initiative_order_events)
        assert last_init_set < first_order, (
            "Initiative order determined before all initiatives set"
        )

    if initiative_order_events and turn_advanced_events:
        last_order = max(e.sequence_number for e in initiative_order_events)
        first_turn = min(e.sequence_number for e in turn_advanced_events)
        assert last_order < first_turn, (
            "Turn advanced before initiative order determined"
        )


def sanitize_event_for_golden(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize an event dictionary for golden file comparison.

    Removes or normalizes fields that change between test runs:
    - timestamps
    - UUIDs
    - request_ids
    - Any other non-deterministic fields
    """
    sanitized = event_dict.copy()

    # Remove timestamp
    sanitized.pop("timestamp", None)

    # Normalize event_id UUID
    if "event_id" in sanitized:
        sanitized["event_id"] = "EVENT_UUID"

    # Normalize message_id (timestamp-based)
    if "message_id" in sanitized:
        sanitized["message_id"] = "MESSAGE_ID"

    # Normalize UUIDs
    if "request_id" in sanitized:
        # Replace actual UUID with placeholder
        sanitized["request_id"] = "UUID_PLACEHOLDER"

    # Normalize correlation_id
    if "correlation_id" in sanitized:
        if sanitized["correlation_id"] is None:
            pass  # Keep None values
        else:
            sanitized["correlation_id"] = "CORRELATION_UUID"

    if (
        "character_id" in sanitized
        and isinstance(sanitized["character_id"], str)
        and len(sanitized["character_id"]) == 36
        and "-" in sanitized["character_id"]
    ):
        # This looks like a UUID, replace it
        sanitized["character_id"] = (
            f"CHARACTER_UUID_{sanitized.get('character_name', 'UNKNOWN')}"
        )

    if (
        "combatant_id" in sanitized
        and isinstance(sanitized["combatant_id"], str)
        and len(sanitized["combatant_id"]) == 36
        and "-" in sanitized["combatant_id"]
    ):
        # This looks like a UUID, replace it
        sanitized["combatant_id"] = (
            f"COMBATANT_UUID_{sanitized.get('combatant_name', 'UNKNOWN')}"
        )

    # Handle cleared_request_ids list
    if "cleared_request_ids" in sanitized and isinstance(
        sanitized["cleared_request_ids"], list
    ):
        sanitized["cleared_request_ids"] = [
            "CLEARED_UUID" for _ in sanitized["cleared_request_ids"]
        ]

    # Handle dice roll request IDs in dice_requests
    if "dice_requests" in sanitized and isinstance(sanitized["dice_requests"], list):
        for dice_req in sanitized["dice_requests"]:
            if isinstance(dice_req, dict) and "request_id" in dice_req:
                dice_req["request_id"] = "DICE_REQUEST_UUID"

    # Handle combatants in combat started events
    if "combatants" in sanitized and isinstance(sanitized["combatants"], list):
        for i, combatant in enumerate(sanitized["combatants"]):
            if isinstance(combatant, dict) and "id" in combatant:
                # Preserve known IDs, sanitize UUIDs
                if (
                    isinstance(combatant["id"], str)
                    and len(combatant["id"]) == 36
                    and "-" in combatant["id"]
                ):
                    combatant["id"] = (
                        f"COMBATANT_UUID_{combatant.get('name', f'INDEX_{i}')}"
                    )

    return sanitized


def save_golden_event_log(
    event_recorder: EventRecorder, test_name: str, golden_dir: Optional[str] = None
) -> str:
    """
    Save the current event log as a golden file.

    Args:
        event_recorder: The event recorder with captured events
        test_name: Name of the test (used for filename)
        golden_dir: Directory to save golden files (defaults to tests/integration/comprehensive_backend/golden)
    """
    if golden_dir is None:
        golden_dir = os.path.join(os.path.dirname(__file__), "golden")

    os.makedirs(golden_dir, exist_ok=True)

    # Get all events and convert to sanitized dictionaries
    all_events = event_recorder.get_all_events()
    sanitized_events = []

    for event in all_events:
        # Use Pydantic's model_dump method for BaseModel objects
        event_dict = event.model_dump()
        sanitized_dict = sanitize_event_for_golden(event_dict)
        sanitized_events.append(sanitized_dict)

    # Save to golden file
    golden_path = os.path.join(golden_dir, f"{test_name}_golden.json")
    with open(golden_path, "w") as f:
        json.dump(sanitized_events, f, indent=2, sort_keys=True)

    print(f"📁 Golden event log saved: {golden_path}")
    return golden_path


def compare_with_golden(
    event_recorder: EventRecorder, test_name: str, golden_dir: Optional[str] = None
) -> bool:
    """
    Compare current event log with golden file.

    Args:
        event_recorder: The event recorder with captured events
        test_name: Name of the test (used for filename)
        golden_dir: Directory containing golden files

    Returns:
        bool: True if events match golden file, False otherwise
    """
    if golden_dir is None:
        golden_dir = os.path.join(os.path.dirname(__file__), "golden")

    golden_path = os.path.join(golden_dir, f"{test_name}_golden.json")

    if not os.path.exists(golden_path):
        print(
            f"⚠️  No golden file found at {golden_path}. Run with UPDATE_GOLDEN=1 to create."
        )
        return False

    # Load golden events
    with open(golden_path) as f:
        golden_events = json.load(f)

    # Get current events and sanitize
    all_events = event_recorder.get_all_events()
    current_events = []

    for event in all_events:
        # Use Pydantic's model_dump method for BaseModel objects
        event_dict = event.model_dump()
        sanitized_dict = sanitize_event_for_golden(event_dict)
        current_events.append(sanitized_dict)

    # Compare
    if len(golden_events) != len(current_events):
        print(
            f"❌ Event count mismatch: golden={len(golden_events)}, current={len(current_events)}"
        )
        return False

    for i, (golden, current) in enumerate(zip(golden_events, current_events)):
        if golden != current:
            print(f"❌ Event {i} mismatch:")
            print(f"   Golden: {json.dumps(golden, sort_keys=True)}")
            print(f"   Current: {json.dumps(current, sort_keys=True)}")

            # Save diff file for debugging
            diff_path = os.path.join(golden_dir, f"{test_name}_diff.json")
            with open(diff_path, "w") as f:
                json.dump(
                    {
                        "event_index": i,
                        "golden": golden,
                        "current": current,
                        "all_golden": golden_events,
                        "all_current": current_events,
                    },
                    f,
                    indent=2,
                )
            print(f"   Diff saved to: {diff_path}")
            return False

    print(f"✅ Events match golden file: {test_name}")
    return True


# Common fixtures


@pytest.fixture
def temp_saves_dir() -> Generator[str, None, None]:
    """Create a temporary directory for saves during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# Re-export fixtures from central conftest


@pytest.fixture
def client(app: Any) -> Any:
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def event_recorder(app: Any) -> EventRecorder:
    """Create an event recorder."""
    from app.core.container import get_container
    from app.utils.event_sequence import reset_sequence_counter

    # Reset the global sequence counter to ensure tests start from 1
    reset_sequence_counter()

    container = get_container()
    event_queue = container.get_event_queue()

    recorder = EventRecorder()
    recorder.attach_to_queue(event_queue)
    return recorder


@pytest.fixture
def container(app: Any) -> Any:
    """Get the service container."""
    from app.core.container import get_container

    return get_container()


@pytest.fixture
def test_character_templates(container: Any) -> Generator[Dict[str, Any], None, None]:
    """Create test character templates for the party members."""
    # Mock the character template repository
    char_template_repo = MagicMock()

    # Create test templates
    fighter_template = CharacterTemplateModel(
        id="test_fighter_template",
        name="Test Fighter",
        race="Human",
        char_class="Fighter",
        level=3,
        background="Soldier",
        alignment="Lawful Good",
        base_stats=BaseStatsModel(STR=16, DEX=13, CON=15, INT=10, WIS=12, CHA=8),
        proficiencies=ProficienciesModel(
            armor=["light", "medium", "heavy", "shields"],
            weapons=["simple", "martial"],
            saving_throws=["STR", "CON"],
        ),
        languages=["Common"],
        starting_equipment=[],
        portrait_path="/static/images/portraits/fighter.png",
    )

    wizard_template = CharacterTemplateModel(
        id="test_wizard_template",
        name="Test Wizard",
        race="Elf",
        char_class="Wizard",
        level=3,
        background="Sage",
        alignment="Neutral Good",
        base_stats=BaseStatsModel(STR=8, DEX=14, CON=13, INT=16, WIS=12, CHA=10),
        proficiencies=ProficienciesModel(
            armor=[],
            weapons=["daggers", "darts", "slings", "quarterstaffs", "light crossbows"],
            saving_throws=["INT", "WIS"],
        ),
        languages=["Common", "Elvish"],
        starting_equipment=[],
        portrait_path="/static/images/portraits/wizard.png",
    )

    cleric_template = CharacterTemplateModel(
        id="test_cleric_template",
        name="Test Cleric",
        race="Dwarf",
        char_class="Cleric",
        level=5,
        background="Acolyte",
        alignment="Lawful Good",
        base_stats=BaseStatsModel(STR=14, DEX=10, CON=16, INT=11, WIS=16, CHA=13),
        proficiencies=ProficienciesModel(
            armor=["light", "medium", "shields"],
            weapons=["simple"],
            saving_throws=["WIS", "CHA"],
        ),
        languages=["Common", "Dwarvish"],
        starting_equipment=[],
        portrait_path="/static/images/portraits/cleric.png",
    )

    rogue_template = CharacterTemplateModel(
        id="test_rogue_template",
        name="Test Rogue",
        race="Halfling",
        char_class="Rogue",
        level=5,
        background="Criminal",
        alignment="Chaotic Neutral",
        base_stats=BaseStatsModel(STR=10, DEX=18, CON=14, INT=13, WIS=14, CHA=12),
        proficiencies=ProficienciesModel(
            armor=["light"],
            weapons=[
                "simple",
                "hand crossbows",
                "longswords",
                "rapiers",
                "shortswords",
            ],
            saving_throws=["DEX", "INT"],
            skills=["Stealth", "Thieves' Tools"],
        ),
        languages=["Common", "Halfling", "Thieves' Cant"],
        starting_equipment=[],
        portrait_path="/static/images/portraits/rogue.png",
    )

    # Set up mock returns
    char_template_repo.get_template.side_effect = lambda template_id: {
        "test_fighter_template": fighter_template,
        "test_wizard_template": wizard_template,
        "test_cleric_template": cleric_template,
        "test_rogue_template": rogue_template,
    }.get(template_id)

    # Replace the container's template repository with our mock
    original_get_char_template_repo = container.get_character_template_repository
    container.get_character_template_repository = lambda: char_template_repo

    # Also patch the CharacterService's repository
    char_service = container.get_character_service()
    if hasattr(char_service, "template_repo"):
        char_service.template_repo = char_template_repo

    yield char_template_repo

    # Restore original
    container.get_character_template_repository = original_get_char_template_repo


@pytest.fixture
def basic_party(container: Any, test_character_templates: Dict[str, Any]) -> Any:
    """Create a basic 2-character party."""
    game_state_repo: GameStateRepository = container.get_game_state_repository()

    game_state = GameStateModel()
    # Use OrderedDict or sort keys to ensure deterministic order
    game_state.party = {
        "fighter": CharacterInstanceModel(
            template_id="test_fighter_template",
            campaign_id="test_campaign",
            current_hp=28,
            max_hp=28,
            level=3,
            conditions=[],
            inventory=[],  # Simplified for test
        ),
        "wizard": CharacterInstanceModel(
            template_id="test_wizard_template",
            campaign_id="test_campaign",
            current_hp=18,
            max_hp=18,
            level=3,
            conditions=[],
            inventory=[],  # Simplified for test
        ),
    }

    game_state.current_location = LocationModel(
        name="Cave Entrance", description="A dark, foreboding cave"
    )
    game_state.campaign_goal = "Test the combat system"

    game_state_repo.save_game_state(game_state)

    return game_state


@pytest.fixture
def full_party(container: Any, test_character_templates: Dict[str, Any]) -> Any:
    """Create a full 4-character party for comprehensive testing."""

    game_state_repo: GameStateRepository = container.get_game_state_repository()

    game_state = GameStateModel()
    # Use alphabetical order for deterministic behavior
    game_state.party = {
        "cleric": CharacterInstanceModel(
            template_id="test_cleric_template",
            campaign_id="test_campaign",
            level=5,
            current_hp=38,
            max_hp=38,
            conditions=[],
            inventory=[],  # Simplified for test
            spell_slots_used={1: 0, 2: 0, 3: 0},  # All slots available
        ),
        "fighter": CharacterInstanceModel(
            template_id="test_fighter_template",
            campaign_id="test_campaign",
            level=5,
            current_hp=44,
            max_hp=44,
            conditions=[],
            inventory=[],  # Simplified for test
        ),
        "rogue": CharacterInstanceModel(
            template_id="test_rogue_template",
            campaign_id="test_campaign",
            level=5,
            current_hp=33,
            max_hp=33,
            conditions=[],
            inventory=[],  # Simplified for test
        ),
        "wizard": CharacterInstanceModel(
            template_id="test_wizard_template",
            campaign_id="test_campaign",
            level=5,
            current_hp=28,
            max_hp=28,
            conditions=[],
            inventory=[],  # Simplified for test
            spell_slots_used={1: 0, 2: 0, 3: 0},  # All slots available
        ),
    }

    game_state.current_location = LocationModel(
        name="Dragon's Lair Entrance",
        description="A massive cave entrance, scorched black by dragon fire",
    )
    game_state.campaign_goal = "Test comprehensive D&D mechanics"

    # Add a quest
    game_state.active_quests = {
        "dragon_lair": QuestModel(
            id="dragon_lair",
            title="The Dragon's Lair",
            description="Investigate the ancient dragon terrorizing the countryside",
            status="active",
        )
    }

    game_state_repo.save_game_state(game_state)

    return game_state


@pytest.fixture
def golden_test(request: Any) -> Any:
    """
    Fixture to handle golden file testing.

    Use UPDATE_GOLDEN=1 environment variable to update golden files.
    """

    def _golden_test(event_recorder: EventRecorder, test_name: str) -> None:
        if os.environ.get("UPDATE_GOLDEN") == "1":
            golden_path = save_golden_event_log(event_recorder, test_name)
            print(f"📝 Updated golden file: {golden_path}")
        else:
            assert compare_with_golden(event_recorder, test_name), (
                f"Events don't match golden file for {test_name}"
            )

    return _golden_test
