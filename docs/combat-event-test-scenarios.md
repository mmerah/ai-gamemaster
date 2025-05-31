# Combat Event System Test Scenarios

## Overview
This document defines test scenarios for the event-driven combat refactor, following Test-Driven Development (TDD) principles.

## Test Categories

### 1. Unit Tests (Pure Functions)

#### CombatState Tests
```python
# Test: Combat initialization
def test_combat_state_initialization():
    """Combat state initializes with correct defaults"""
    # Given: No combat
    # When: Combat starts with 2 PCs and 1 NPC
    # Then: 
    #   - is_active = True
    #   - combatants list has 3 entries
    #   - round_number = 1
    #   - current_turn_index = -1 (no initiative yet)

# Test: Initiative ordering
def test_initiative_order_with_ties():
    """Initiative correctly orders combatants, breaking ties with DEX"""
    # Given: Combatants with initiatives [20, 15, 15, 10]
    #        DEX modifiers [+2, +3, +1, +0]
    # When: set_initiative_order() called
    # Then: Order is [20(+2), 15(+3), 15(+1), 10(+0)]

# Test: Turn advancement
def test_advance_turn_skips_incapacitated():
    """Turn advancement skips incapacitated combatants"""
    # Given: 4 combatants, #2 at 0 HP
    # When: advance_turn() from combatant #1
    # Then: current_turn_index = 3 (skips #2)
```

#### CombatService Tests
```python
# Test: Damage application
def test_apply_damage_respects_minimum_zero():
    """Damage cannot reduce HP below 0"""
    # Given: Combatant with 5 HP
    # When: apply_damage(10)
    # Then: HP = 0, is_defeated = True

# Test: Healing application
def test_apply_healing_respects_maximum():
    """Healing cannot exceed max HP"""
    # Given: Combatant with 10/20 HP
    # When: apply_healing(15)
    # Then: HP = 20, actual_healed = 10
```

### 2. Integration Tests (Event Sequences)

#### Test Scenario: Basic NPC Attack
```python
def test_npc_attack_full_sequence():
    """Complete NPC attack sequence produces correct events"""
    
    # Setup
    event_recorder = EventRecorder()
    mock_ai_response = {
        "narrative": "The goblin archer nocks an arrow...",
        "dice_requests": [{
            "purpose": "attack",
            "dice_type": "1d20+4",
            "against_value": 15,
            "roller_name": "Goblin Archer"
        }]
    }
    
    # Execute
    handler.handle_next_step()
    
    # Assert event sequence
    events = event_recorder.get_events()
    assert events == [
        BackendProcessingEvent(is_processing=True),
        NarrativeAddedEvent(content="It's Goblin Archer's turn..."),
        NarrativeAddedEvent(content="The goblin archer nocks an arrow..."),
        NpcDiceRollProcessedEvent(
            roller_name="Goblin Archer",
            purpose="attack",
            total=18,
            details="1d20+4: [14] + 4 = 18"
        ),
        # ... continued based on hit/miss
    ]
```

#### Test Scenario: Player Character Death
```python
def test_player_character_defeat_sequence():
    """PC reaching 0 HP produces correct event sequence"""
    
    # Given: PC at 3 HP, incoming 5 damage
    # When: Damage applied
    # Then events:
    events = [
        CombatantHpChangedEvent(
            combatant_id="pc_1",
            old_hp=3,
            new_hp=0,
            max_hp=20,
            change_amount=-5,
            is_player_controlled=True
        ),
        CombatantStatusChangedEvent(
            combatant_id="pc_1",
            new_conditions=["unconscious"],
            is_defeated=True
        ),
        NarrativeAddedEvent(
            content="Elara falls unconscious!",
            is_system_message=True
        )
    ]
```

### 3. Contract Tests (Frontend-Backend Event Contract)

#### Event Schema Validation
```python
def test_all_events_have_required_fields():
    """All event types include base fields"""
    for event_class in get_all_event_classes():
        event = event_class()
        assert hasattr(event, 'event_id')
        assert hasattr(event, 'timestamp')
        assert hasattr(event, 'event_type')
```

#### Frontend Store Update Contract
```typescript
// Frontend test
describe('Combat Store Event Handling', () => {
  it('handles CombatantHpChangedEvent correctly', () => {
    // Given: Store with combatant at 20 HP
    const store = useCombatStore();
    store.combatants = [{ id: 'orc_1', current_hp: 20, max_hp: 20 }];
    
    // When: HP change event received
    const event = {
      type: 'CombatantHpChangedEvent',
      combatant_id: 'orc_1',
      old_hp: 20,
      new_hp: 15,
      change_amount: -5
    };
    store.handleHpChanged(event);
    
    // Then: Store updates correctly
    expect(store.combatants[0].current_hp).toBe(15);
  });
});
```

### 4. End-to-End Test Scenarios

#### Scenario: Complete Combat Round
```gherkin
Feature: Combat Round Execution
  
  Scenario: Mixed PC/NPC combat round
    Given a combat with 2 PCs and 2 NPCs
    And initiative order is [PC1(20), NPC1(15), PC2(10), NPC2(5)]
    
    When PC1 takes attack action
    Then BackendProcessingEvent(false) emitted
    And UI shows dice request for PC1
    
    When PC1 submits attack roll
    Then attack resolution events emitted
    And TurnAdvancedEvent(NPC1) emitted
    And BackendProcessingEvent(true) emitted
    
    When backend processes NPC1 turn
    Then NPC1 attack sequence events emitted
    And TurnAdvancedEvent(PC2) emitted
    And BackendProcessingEvent(false) emitted
```

### 5. Performance Tests

```python
def test_event_throughput():
    """System handles rapid event generation"""
    # Generate 1000 events in 1 second
    # Assert: All events delivered in order
    # Assert: No events dropped
    # Assert: Frontend remains responsive
```

### 6. Error Recovery Tests

```python
def test_frontend_reconnection_preserves_state():
    """Frontend can reconnect and reconcile state"""
    # Given: Active combat, SSE disconnects
    # When: Frontend reconnects
    # Then: StateReconciliationRequestEvent sent
    # And: GameStateSnapshotEvent received
    # And: Frontend state matches backend
```

## Test Execution Order (TDD)

1. **Phase 0**: Write all unit tests (red)
2. **Phase 1a**: Implement models to pass unit tests (green)
3. **Phase 1b**: Write integration tests for events (red)
4. **Phase 2**: Implement event system to pass integration tests (green)
5. **Phase 3**: Write E2E tests (red)
6. **Phase 4**: Implement full flow to pass E2E tests (green)
7. **Phase 5**: Refactor for performance and clarity

## Critical Test Patterns

### 1. Event Assertion Helper
```python
def assert_event_sequence(actual_events, expected_types):
    """Helper to assert event types in order"""
    actual_types = [e.__class__.__name__ for e in actual_events]
    assert actual_types == expected_types
```

### 2. Time-based Event Testing
```python
def test_event_timestamps_increase():
    """Events have monotonically increasing timestamps"""
    # Important for event ordering
```

### 3. Correlation Testing
```python
def test_related_events_share_correlation_id():
    """Related events (e.g., attack->damage) share correlation_id"""
    # Helps frontend group related updates
```