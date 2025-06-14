"""
QUEST AND INVENTORY MANAGEMENT TEST

Tests quest progression and inventory management:
- Quest initiation and progression
- Quest completion with rewards
- Individual character inventory updates
- Party-wide item distribution
- Magical item properties
- Quest status tracking
- Multiple inventory updates in one action

This test ensures quest and inventory systems work correctly.
"""

from typing import Any

from app.models.events import ItemAddedEvent, QuestUpdatedEvent
from app.models.updates import InventoryAddUpdateModel, QuestUpdateModel
from app.providers.ai.schemas import AIResponse

from .conftest import verify_event_system_integrity, verify_required_event_types


def test_quest_and_inventory_management(
    app: Any,
    client: Any,
    mock_ai_service: Any,
    event_recorder: Any,
    container: Any,
    full_party: Any,
    golden_test: Any,
) -> None:
    """Test dedicated quest progression and inventory management functionality."""

    # Clear any initial events
    event_recorder.clear()

    # ========== PHASE 1: Quest Initiation ==========

    # AI provides quest information
    mock_ai_service.add_response(
        AIResponse(
            narrative="You discover an ancient tome detailing the dragon's weaknesses! Your quest advances.",
            reasoning="Quest progression with new information",
            quest_updates=[
                QuestUpdateModel(
                    quest_id="dragon_lair",
                    objectives_completed=2,
                    objectives_total=5,
                    rewards_experience=0,
                    rewards_gold=0,
                    rewards_items=[],
                    description="Discovered ancient tome with dragon weaknesses",
                )
            ],
        )
    )

    # User input which will result in the AIResponse with QuestUpdate
    response = client.post(
        "/api/player_action",
        json={
            "action_type": "free_text",
            "value": "We examine the ancient tome carefully.",
        },
    )
    assert response.status_code == 200

    # ========== PHASE 2: Treasure Discovery ==========

    # AI provides multiple items to different characters
    mock_ai_service.add_response(
        AIResponse(
            narrative="Hidden in the tome's binding, you find magical items and treasures!",
            reasoning="Treasure discovery with multiple items",
            inventory_adds=[
                InventoryAddUpdateModel(
                    character_id="wizard",
                    value="Ancient Spellbook of Dragon Lore",
                    quantity=1,
                    item_value=5000,
                    rarity="rare",
                    description="Grants +2 to spell attack rolls against dragons",
                ),
                InventoryAddUpdateModel(
                    character_id="fighter",
                    value="Dragonbane Sword",
                    quantity=1,
                    item_value=10000,
                    rarity="very rare",
                    description="A sword specifically forged to harm dragons",
                ),
                InventoryAddUpdateModel(
                    character_id="rogue",
                    value="Cloak of Draconic Resistance",
                    quantity=1,
                    item_value=4500,
                    rarity="rare",
                    description="Provides resistance to fire, cold, acid, lightning, and poison damage",
                ),
                InventoryAddUpdateModel(
                    character_id="cleric",
                    value="Blessed Amulet of Dragon Protection",
                    quantity=1,
                    item_value=2000,
                    rarity="uncommon",
                    description="Grants advantage on saving throws against dragon abilities",
                ),
            ],
        )
    )

    # User input which will result in the AIResponse with InventoryUpdate
    response = client.post(
        "/api/player_action",
        json={
            "action_type": "free_text",
            "value": "We search for any hidden compartments or treasures.",
        },
    )
    assert response.status_code == 200

    # ========== PHASE 3: Quest Completion ==========

    # AI completes the quest
    mock_ai_service.add_response(
        AIResponse(
            narrative="With the ancient knowledge and magical items, you feel ready to face the dragon! Your quest objective is complete.",
            reasoning="Quest completion",
            quest_updates=[
                QuestUpdateModel(
                    quest_id="dragon_lair",
                    status="completed",
                    objectives_completed=5,
                    objectives_total=5,
                    rewards_experience=2000,
                    rewards_gold=500,
                    rewards_items=["Map to Dragon's Heart Chamber"],
                    description="Quest completed - Knowledge of dragon's weakness gained",
                )
            ],
            inventory_adds=[
                InventoryAddUpdateModel(
                    character_id="party",
                    value="Map to Dragon's Heart Chamber",
                    quantity=1,
                    item_value=0,
                    rarity="quest item",
                    description="Detailed map showing the path to the dragon's most vulnerable location",
                )
            ],
        )
    )

    # User input which will result in the AIResponse with QuestUpdate/InventoryUpdate for quest completion
    response = client.post(
        "/api/player_action",
        json={"action_type": "free_text", "value": "We study the tome's final pages."},
    )
    assert response.status_code == 200

    # ========== COMPREHENSIVE EVENT VERIFICATION ==========

    # Verify event system integrity
    event_stats = verify_event_system_integrity(event_recorder)
    verify_required_event_types(event_stats["event_types"], "Quest & Inventory")

    # ========== QUEST SYSTEM VERIFICATION ==========

    quest_events = event_recorder.get_events_of_type(QuestUpdatedEvent)
    assert len(quest_events) >= 1, (
        f"Expected at least 1 quest event, got {len(quest_events)}"
    )

    # Verify quest progression
    quest_ids = set(event.quest_id for event in quest_events)
    assert "dragon_lair" in quest_ids, "Expected dragon_lair quest to be updated"

    # Verify quest event structure
    for quest_event in quest_events:
        assert hasattr(quest_event, "quest_id"), "Quest event missing quest_id"
        assert hasattr(quest_event, "quest_title"), "Quest event missing quest_title"
        assert hasattr(quest_event, "new_status"), "Quest event missing new_status"
        print(
            f"      ✅ Quest '{quest_event.quest_id}' ({quest_event.quest_title}) updated to status: {quest_event.new_status}"
        )

    # ========== INVENTORY SYSTEM VERIFICATION ==========

    item_events = event_recorder.get_events_of_type(ItemAddedEvent)
    assert len(item_events) >= 5, (
        f"Expected at least 5 item events, got {len(item_events)}"
    )

    # Verify items were distributed to different characters
    characters_with_items = set(event.character_id for event in item_events)
    expected_characters = {"wizard", "fighter", "rogue", "cleric"}
    assert expected_characters.issubset(characters_with_items), (
        f"Missing items for characters: {expected_characters - characters_with_items}"
    )

    # Verify that party items were distributed to all party members
    party_items = [
        e for e in item_events if "Map to Dragon's Heart Chamber" in e.item_name
    ]
    assert len(party_items) == 4, (
        f"Expected 4 copies of party item (one per character), got {len(party_items)}"
    )

    # Verify item event structure
    for item_event in item_events:
        assert hasattr(item_event, "character_id"), "Item event missing character_id"
        assert hasattr(item_event, "character_name"), (
            "Item event missing character_name"
        )
        assert hasattr(item_event, "item_name"), "Item event missing item_name"
        assert hasattr(item_event, "quantity"), "Item event missing quantity"

        print(
            f"      ✅ {item_event.character_name} received '{item_event.item_name}' (x{item_event.quantity})"
        )

    # Count items by type
    magical_items = len(
        [
            e
            for e in item_events
            if "Dragon" in e.item_name
            or "Blessed" in e.item_name
            or "Ancient" in e.item_name
        ]
    )
    rare_items = len(
        [
            e
            for e in item_events
            if "Dragonbane" in e.item_name
            or "Cloak" in e.item_name
            or "Spellbook" in e.item_name
        ]
    )

    print(f"      🔮 Magical Items: {magical_items}")
    print(f"      💎 Rare Items: {rare_items}")

    # ========== SYSTEM INTEGRATION VERIFICATION ==========

    # Verify all core events occurred
    assert "QuestUpdatedEvent" in event_stats["event_types"], (
        "Missing QuestUpdatedEvent"
    )
    assert "ItemAddedEvent" in event_stats["event_types"], "Missing ItemAddedEvent"
    assert "NarrativeAddedEvent" in event_stats["event_types"], (
        "Missing NarrativeAddedEvent"
    )

    # Test golden file comparison
    golden_test(event_recorder, "quest_inventory")

    print("\n✅ QUEST & INVENTORY TEST COMPLETE")
    print(f"   📊 Total Events: {event_stats['total_events']}")
    print(f"   📜 Quest Updates: {len(quest_events)}")
    print(f"   🎒 Items Added: {len(item_events)}")
    print(f"   👥 Characters with Items: {len(characters_with_items)}")
    print(f"   🔮 Magical Items: {magical_items}")
    print(f"   💎 Rare Items: {rare_items}")
    print(f"   📝 Event Types: {sorted(event_stats['event_types'])}")
