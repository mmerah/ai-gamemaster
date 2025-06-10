# Comprehensive Backend Integration Tests

This directory contains the gold standard integration tests for the D&D AI system backend. These tests ensure that all major game mechanics work correctly together.

## Test Organization

The tests are split into focused modules:

- **test_comprehensive_combat.py** - Complex 4v5 combat with all D&D mechanics
- **test_exploration.py** - Non-combat gameplay including skill checks and trap detection
- **test_quest_inventory.py** - Quest progression and inventory management

## Golden Event Logs

These tests support golden file testing to ensure event sequences remain consistent across changes.

### Using Golden Files

By default, tests will compare event logs against golden files:

```bash
# Run tests and verify against golden files
pytest tests/integration/comprehensive_backend/
```

### Updating Golden Files

To update golden files after intentional changes:

```bash
# Update golden files
UPDATE_GOLDEN=1 pytest tests/integration/comprehensive_backend/
```

### Golden File Location

Golden files are stored in `tests/integration/comprehensive_backend/golden/` with names like:
- `comprehensive_combat_golden.json`
- `exploration_golden.json`
- `quest_inventory_golden.json`

## Event Log Sanitization

Golden files have the following fields sanitized for comparison:
- Timestamps (removed)
- UUIDs (replaced with placeholders)
- Request IDs (normalized)
- Character/Combatant IDs that are UUIDs (normalized)

This ensures tests remain deterministic while preserving the structure and sequence of events.

## Running Individual Tests

```bash
# Run specific test
pytest tests/integration/comprehensive_backend/test_basic_combat.py -v

# Run with golden file update
UPDATE_GOLDEN=1 pytest tests/integration/comprehensive_backend/test_basic_combat.py
```

## Test Coverage

These tests provide comprehensive coverage of:
- Combat initiation and initiative
- Attack rolls and damage application
- HP tracking and defeat conditions
- Turn advancement and NPC automation
- Skill checks and DC mechanics
- Area of effect spells and saving throws
- Quest progression and completion
- Inventory management and item distribution
- Event system integrity and ordering

## Debugging Failed Tests

If a test fails due to event mismatch:

1. Check the diff file in `golden/[test_name]_diff.json`
2. Review the changes to determine if they're intentional
3. If intentional, update the golden file with `UPDATE_GOLDEN=1`
4. If unintentional, fix the code that caused the event change
