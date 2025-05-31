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
│   ├── test_game_event_manager.py
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