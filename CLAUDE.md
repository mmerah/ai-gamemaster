# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered Dungeons & Dragons 5e game master web application that uses LLMs for storytelling, manages turn-based combat, characters, and campaigns.

## Essential Commands

### Quick Start
```bash
# Windows
launch.bat

# Linux/macOS
./launch.sh
```

### Development Commands

**Backend (Flask) with Virtual Environment**
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Note: sqlite-vec is included in requirements.txt for native vector search performance
# The application will work without it but will use a slower fallback implementation

# Run server
python run.py                       # Backend server (http://127.0.0.1:5000)
python launch_server.py qwen_14b_q6 # Start local LLM server
```

**Frontend (Vue.js)**
```bash
npm --prefix frontend install       # Install dependencies
npm --prefix frontend run dev       # Dev server (http://localhost:5173)
npm --prefix frontend run build     # Production build
```

**Database Migration**
```bash
# Initial migration (one-time setup)
python scripts/migrate_json_to_db.py sqlite:///data/content.db

# Check migration status without making changes
python scripts/migrate_json_to_db.py sqlite:///data/content.db --check-only

# Rollback last migration if needed
python scripts/migrate_json_to_db.py sqlite:///data/content.db --rollback

# Verify migration
python scripts/verify_migration.py sqlite:///data/content.db

# Update after 5e-database submodule update
python scripts/update_srd_content.py sqlite:///data/content.db
```
See [Database Migration Guide](docs/DATABASE-MIGRATION-GUIDE.md) for detailed instructions.

**Testing**
```bash
python tests/run_all_tests.py              # All tests (RAG disabled)
python tests/run_all_tests.py unit         # Unit tests only
python tests/run_all_tests.py integration  # Integration tests only
python tests/run_all_tests.py --with-rag   # Enable RAG tests
```

**Type Checking**
```bash
mypy app --strict                          # Type check production code (0 errors expected)
mypy tests --strict                        # Type check test code (0 errors expected)
mypy . --strict                            # Type check entire project
```

**TypeScript Generation**
```bash
python scripts/generate_typescript.py      # Regenerate TypeScript definitions
```
This command regenerates the TypeScript interfaces in `frontend/src/types/unified.ts` from the Pydantic models in `app/models/` (all domain-specific .py files). Run this whenever you modify the Python models to keep the frontend types in sync.

**Database Maintenance**
```bash
python scripts/migrate_json_to_db.py       # Regenerate content.db from JSON files
python scripts/verify_migration.py         # Verify database integrity
```
The D&D 5e content database (`data/content.db`) is tracked in git for zero-setup experience. See `docs/DATABASE-GUIDE.md` for all database operations.

**Golden Reference Tests**
The tests in `tests/integration/comprehensive_backend/` are our golden reference tests for the main game loop. These tests:
- Must always pass - they validate core game functionality
- Use golden JSON files to ensure consistent behavior
- Any changes to their golden files must be reviewed thoroughly as they indicate changes to core game behavior

## Key Dependencies

**AI/ML Libraries**
- **LangChain**: Core framework for AI service integration
  - langchain, langchain-core, langchain-community
  - langchain-openai, langchain-huggingface
- **PyTorch**: Deep learning framework (torch, torchvision, torchaudio)
- **Transformers**: Hugging Face transformers library
- **RAG Components**: sentence-transformers, faiss-cpu

## Architecture

### Core Patterns
- **Event-Driven Architecture**: EventQueue in `app/core/event_queue.py` provides asynchronous event handling
- **Dependency Injection**: ServiceContainer in `app/core/container.py` manages all service dependencies
- **Repository Pattern**: Data access abstracted through repositories (campaign, character, game state)
- **Event System**: GameEventManager in `app/services/game_events/` handles game actions through specialized handlers
- **Service Layer**: Business logic in service classes under `app/services/`

### Key Services
- **AI Services**: `app/ai_services/` - LLM integration using LangChain framework with improved JSON parsing
- **Game Services**: Combat, dice rolling, character management in `app/services/`
- **Response Processors**: `app/services/response_processors/` - Direct typed list processing from AI responses
- **RAG System**: `app/services/rag/` - Optional semantic search for rules/lore context
- **Event Handlers**: `app/services/game_events/handlers/` - Specialized handlers for game actions

### Data Flow
1. Frontend (Vue) → API Routes → Services → Repositories → Storage
2. Game events → GameEventManager → Event Handlers → State Updates
3. AI requests → AI Service → Response Processors → Game State

### Model Organization
Models are organized in `app/models/` by domain for better maintainability:
- **base.py**: Shared base models and serializers
- **character.py**: Character templates, instances, and combined models
- **campaign.py**: Campaign templates and instances
- **combat.py**: Combat state, combatants, and related models
- **dice.py**: Dice requests, results, and submissions
- **game_state.py**: Core game state and action models
- **config.py**: Service configuration model
- **utils.py**: Basic structures and utility models (items, NPCs, quests, etc.)
- **rag.py**: RAG and knowledge base models
- **events.py**: Event models for the event-driven architecture
- **updates.py**: Game state update models (flattened structure)

All models use Pydantic for validation and are the single source of truth for TypeScript generation. The `__init__.py` re-exports all models for backward compatibility.

### TTS Settings Hierarchy
TTS (Text-to-Speech) settings follow a three-tier hierarchy:
1. **Campaign Template** - Default narration settings (narration_enabled, tts_voice)
2. **Campaign Instance** - Optional override for specific campaigns
3. **Game State** - Runtime override via Enable Narration toggle (highest priority)

When starting a game, settings cascade: Template → Instance → Game State

## Configuration

### Environment Variables (.env)
- `AI_PROVIDER`: llamacpp_http or openrouter
- `AI_RESPONSE_PARSING_MODE`: strict or flexible (JSON parsing mode)
- `RAG_ENABLED`: true/false (disable for faster startup)
- `GAME_STATE_REPO_TYPE`: memory or file
- `TTS_PROVIDER`: kokoro or disabled

### Model Configuration
- `models.yaml`: Llama.cpp server configurations
- Pre-configured models: Qwen, Phi, Mistral, Gemma, GLM

## Known Issues

### Rate Limiting
The application handles rate limiting from AI providers (e.g., Google Gemini) through:
- LangChain's built-in retry mechanisms
- Automatic retry with configurable delays
- Error handling in `app/ai_services/openai_service.py`

## Important Notes

- Game state stored in `saves/` directory
- Knowledge bases in `knowledge/` for rules and lore
- Frontend built artifacts go to `static/dist/`
- TTS cache in `static/tts_cache/`
- Character portraits in `static/images/portraits/`
- Don't maintain backward compatiblity for anything
- When adding replacing features, don't keep the old ones rather delete them

## Testing Best Practices

- All test files use `get_test_config()` from `tests/conftest.py` for consistent configuration
- Tests are 100% type-safe - use proper type annotations for all test methods
- Golden reference tests in `tests/integration/comprehensive_backend/` validate core game loop
- Use specific model types instead of `Dict[str, Any]` for better type safety
- Mock AI services should use Protocol types or proper type casting

## Code Quality Standards

### Pre-commit Hooks

The project uses pre-commit hooks to maintain code quality and type safety:
```bash
pip install pre-commit
pre-commit install
```

The hooks automatically run before each commit:
1. **Ruff** - Lints and formats code (combines black, isort, flake8)
2. **Mypy** - Type checks with `--strict` mode

### Configuration

All Python tooling is configured in `pyproject.toml`:

**Ruff** (linting & formatting):
- Line length: 88 characters (black standard)
- Import sorting with `app` and `tests` as first-party
- Enabled checks: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear
- Auto-fixes: import sorting, formatting, common issues

**Mypy** (type checking):
- Strict mode enabled (all strict flags)
- Pydantic plugin for model validation
- Per-module overrides for scripts

**Pytest** (testing):
- Test discovery in `tests/` directory
- Custom markers: slow, requires_rag, no_auto_reset_container
- Verbose output with short tracebacks

Run manually:
```bash
ruff check . --fix    # Lint and auto-fix
ruff format .         # Format code
mypy app --strict     # Type check (uses pyproject.toml)
pytest                # Run tests (uses pyproject.toml)
```

## Project Status

### Type Safety Achievements:
- **Production Code**: 100% type-safe (mypy app --strict: 0 errors)
- **Test Code**: 100% type-safe (mypy tests --strict: 0 errors)
