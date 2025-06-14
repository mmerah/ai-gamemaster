# Testing Guide

This guide covers how to run tests for the AI Game Master project.

## Quick Start

The project uses pytest for testing with optimized configuration to avoid slow startup times.

### Using the Test Runner (Recommended)

```bash
# Run all tests (fast mode with RAG disabled)
python tests/run_all_tests.py

# Run only unit tests
python tests/run_all_tests.py unit

# Run only integration tests
python tests/run_all_tests.py integration

# Run with coverage report
python tests/run_all_tests.py coverage

# Run tests with RAG enabled (slower, for testing RAG functionality)
python tests/run_all_tests.py --with-rag
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_combat_service.py

# Run specific test method
pytest tests/unit/test_combat_service.py::TestCombatService::test_start_combat

# Run tests matching a pattern
pytest tests/ -k "combat"
```

## Performance Optimization

By default, tests run with RAG (Retrieval-Augmented Generation) disabled for much faster execution:

```bash
# Fast mode (RAG disabled) - ~1 minute for all tests
RAG_ENABLED=false pytest tests/

# Full mode (RAG enabled) - ~10+ minutes due to embeddings loading
RAG_ENABLED=true pytest tests/
```

The test runner script automatically sets `RAG_ENABLED=false` unless you use the `--with-rag` flag.

## Test Coverage

Generate coverage reports to see which code is tested:

```bash
# Using the test runner
python tests/run_all_tests.py coverage

# Or manually with pytest
coverage run -m pytest tests/
coverage report -m
coverage html  # Creates htmlcov/index.html
```

## Test Organization

```
tests/
├── conftest.py              # Shared test configuration
├── run_all_tests.py         # Test runner with optimized config
├── pytest_plugins.py        # Custom pytest fixtures and settings
├── test_helpers.py          # Shared test utilities
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_combat_service.py
│   ├── test_dice_mechanics.py
│   ├── test_event_queue.py
│   ├── test_game_orchestrator.py
│   └── ...
├── integration/             # Integration tests (slower, test multiple components)
│   ├── test_campaign_flow.py
│   ├── test_event_snapshots.py
│   ├── test_sse_endpoint.py
│   ├── comprehensive_backend/   # Golden file tests
│   │   ├── test_basic_combat.py
│   │   ├── test_comprehensive_combat.py
│   │   └── golden/         # Expected output files
│   └── ...
└── performance/             # Performance tests
    └── test_event_throughput.py
```

## Writing Tests

### Test Configuration

All tests should use the optimized configuration from `conftest.py`:

```python
from app.core.container import ServiceContainer, reset_container
from tests.conftest import get_test_config

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        reset_container()
        self.container = ServiceContainer(get_test_config())
        self.container.initialize()
```

### Testing with RAG

If your test specifically needs to test RAG functionality:

```python
def setUp(self):
    reset_container()
    config = get_test_config()
    config['RAG_ENABLED'] = True  # Enable RAG for this test
    self.container = ServiceContainer(config)
    self.container.initialize()
```

## Continuous Integration

For CI/CD pipelines, use environment variables:

```yaml
# Example GitHub Actions
env:
  RAG_ENABLED: false
  TTS_PROVIDER: disabled
  GAME_STATE_REPO_TYPE: memory

steps:
  - name: Run tests
    run: pytest tests/ -v
```

## Troubleshooting

### Tests are running slowly

Make sure RAG is disabled:
- Use `python tests/run_all_tests.py` instead of pytest directly
- Or set `RAG_ENABLED=false` in your environment

### Import errors

The test runner adds the project root to Python path automatically. If running pytest directly from the project root, imports should work fine.

### Coverage not found

Install coverage:
```bash
pip install coverage
```

## AI Mocking Patterns for Integration Tests

This section describes best practices for mocking AI services in integration tests, particularly for multi-stage scenarios where AI responses need to be carefully orchestrated.

### Key Principles

1. **Update AI mock before each stage** that triggers an AI call
2. **Use specific responses** that match the expected context and game state
3. **For auto-continuation tests**, use `side_effect` with a list of sequential responses
4. **For multi-step tests**, update `mock.return_value` before each step

### Pattern 1: Multi-Stage Precise Mocking

When testing multi-stage interactions (e.g., player action → dice roll → damage application), update the AI mock before each stage:

```python
def test_multi_stage_interaction(self, container, app, event_recorder):
    """Test a multi-stage combat interaction with precise mocking."""
    with app.app_context():
        ai_service = app.config.get('AI_SERVICE')
        game_event_manager = container.get_game_event_handler()

        # Stage 1: Player declares attack
        attack_response = AIResponse(
            narrative="You swing your sword at the orc!",
            reasoning="Player attacking",
            dice_requests=[
                DiceRequest(
                    request_id="attack_001",
                    character_ids=["fighter1"],
                    type="attack",
                    dice_formula="1d20+5",
                    reason="Attack roll"
                )
            ]
        )
        ai_service.get_response = Mock(return_value=attack_response)

        game_event_manager.handle_player_action({
            "action_type": "attack",
            "value": "I attack the orc!"
        })

        # Stage 2: Process attack roll result
        damage_response = AIResponse(
            narrative="Your sword strikes true!",
            reasoning="Attack hit, rolling damage",
            dice_requests=[
                DiceRequest(
                    request_id="damage_001",
                    character_ids=["fighter1"],
                    type="damage",
                    dice_formula="1d8+3",
                    reason="Sword damage"
                )
            ]
        )
        ai_service.get_response = Mock(return_value=damage_response)

        game_event_manager.handle_dice_submission([{
            "request_id": "attack_001",
            "character_id": "fighter1",
            "roll_type": "attack",
            "total": 18
        }])

        # Stage 3: Apply damage
        final_response = AIResponse(
            narrative="The orc staggers from your blow!",
            reasoning="Applied damage",
            game_state_updates=[
                HPChangeUpdate(
                    combatant_id="orc1",
                    new_hp=8,
                    damage_dealt=7
                )
            ]
        )
        ai_service.get_response = Mock(return_value=final_response)

        game_event_manager.handle_dice_submission([{
            "request_id": "damage_001",
            "character_id": "fighter1",
            "roll_type": "damage",
            "total": 7
        }])
```

### Pattern 2: Auto-Continuation with side_effect

For scenarios where the system makes multiple sequential AI calls without user intervention (e.g., NPC turns), use `side_effect`:

```python
def test_auto_continuation_npc_turn(self, container, app, event_recorder):
    """Test NPC auto-continuation with side_effect."""
    with app.app_context():
        ai_service = app.config.get('AI_SERVICE')

        # Setup sequential responses for auto-continuation
        ai_service.get_response.side_effect = [
            # First call: NPC declares attack
            AIResponse(
                narrative="The orc swings its axe!",
                reasoning="NPC attacking",
                dice_requests=[
                    DiceRequest(
                        request_id="npc_attack_001",
                        character_ids=["orc1"],
                        type="attack",
                        dice_formula="1d20+4",
                        reason="Orc attack"
                    )
                ],
                npc_action_required=True
            ),
            # Second call: Process attack result
            AIResponse(
                narrative="The axe bites deep!",
                reasoning="Attack hit, rolling damage",
                dice_requests=[
                    DiceRequest(
                        request_id="npc_damage_001",
                        character_ids=["orc1"],
                        type="damage",
                        dice_formula="1d12+3",
                        reason="Greataxe damage"
                    )
                ],
                npc_action_required=True
            ),
            # Third call: Apply damage
            AIResponse(
                narrative="Sir Roland grimaces in pain!",
                reasoning="Applied damage to player",
                game_state_updates=[
                    HPChangeUpdate(
                        combatant_id="fighter1",
                        new_hp=15,
                        damage_dealt=10
                    )
                ],
                end_turn=True
            )
        ]

        # Trigger the auto-continuation sequence
        game_event_manager.handle_next_step_trigger()
```

### Common Mistakes to Avoid

#### Mistake 1: Setting Mock Once for Multiple Stages

**Wrong:**
```python
# DON'T DO THIS
initial_response = AIResponse(narrative="This will be stale!")
ai_service.get_response = Mock(return_value=initial_response)

# Action 1
game_event_manager.handle_player_action(action1)
# Action 2 - will get the same stale response!
game_event_manager.handle_player_action(action2)
```

**Correct:**
```python
# DO THIS
response1 = AIResponse(narrative="Context-specific response 1")
ai_service.get_response = Mock(return_value=response1)
game_event_manager.handle_player_action(action1)

response2 = AIResponse(narrative="Context-specific response 2")
ai_service.get_response = Mock(return_value=response2)
game_event_manager.handle_player_action(action2)
```

#### Mistake 2: Using side_effect for Non-Sequential Actions

**Wrong:**
```python
# DON'T use side_effect for separate user actions
ai_service.get_response.side_effect = [response1, response2]
game_event_manager.handle_player_action(action1)  # Gets response1
# ... user thinks, time passes ...
game_event_manager.handle_player_action(action2)  # Gets response2 - WRONG!
```

**Correct:**
```python
# Use side_effect ONLY for auto-continuation
# For separate actions, update the mock each time
```

#### Mistake 3: Not Mocking Dice Service

Always mock the dice service when testing AI interactions that involve dice rolls:

```python
dice_service = container.get_dice_service()
dice_service.perform_roll = Mock(return_value={
    "total": 15,
    "rolls": [12],
    "modifier": 3,
    "formula": "1d20+3",
    "details": "1d20+3: [12] + 3 = 15"
})
```

### Working Examples

For complete working examples of these patterns, see:

1. **Multi-stage mocking**: `tests/integration/test_event_sequences.py::test_player_action_to_damage_full_sequence`
   - Demonstrates updating AI mock before each dice submission
   - Shows proper sequence: attack request → damage request → damage application

2. **Complex scenarios**: `tests/integration/test_complex_scenario_events.py::test_multi_step_player_action_scenario`
   - Shows precise mocking for complex spell scenarios
   - Demonstrates proper event validation with EventRecorder

3. **Auto-continuation**: `tests/integration/test_auto_continuation.py::test_auto_continuation_npc_attack_to_damage`
   - Shows side_effect usage for auto-continuation scenarios
   - Demonstrates sequential AI calls in a single operation

### Best Practices Summary

1. **Be specific**: Each AI response should match the expected game state and context
2. **Update frequently**: Update mocks before each stage that triggers an AI call
3. **Use side_effect sparingly**: Only for true auto-continuation sequences
4. **Mock all dependencies**: Always mock dice service, TTS, and other external services
5. **Validate with EventRecorder**: Use EventRecorder to verify the correct sequence of events
