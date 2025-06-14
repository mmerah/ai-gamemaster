Of course. The current project structure has grown organically, and a well-defined domain-driven structure will significantly improve maintainability, testability, and developer experience. The goal is to group related logic together, making it intuitive to find and modify code related to a specific feature area like the database, AI interactions, or game mechanics.

Here is a detailed implementation plan to reorganize the `ai-gamemaster` repository into a clean, domain-driven architecture.

---

# Implementation Plan: Domain-Driven Repository Reorganization

## 1. Vision & Guiding Principles

The primary goal is to refactor the repository structure to align with clean architecture and domain-driven design principles. This will enable developers to work on specific parts of the application (e.g., RAG, Database, API) in greater isolation.

### Guiding Principles:
- **No Functional Changes**: This is a pure refactoring and reorganization effort. All tests should pass before and after the changes.
- **Domain-Driven Structure**: Code should be grouped by its business domain (e.g., `database`, `rag`, `api`) rather than by its technical type (e.g., a single `services` folder).
- **Mirrored Test Structure**: The `tests/` directory will be reorganized to exactly mirror the new `app/` structure, ensuring tests are easy to locate.
- **Clear Separation of Concerns**: Each module and package will have a single, well-defined responsibility.
- **Maintain Type Safety**: All changes must continue to pass `mypy --strict`.

## 2. Proposed "To-Be" Directory Structure

This is the target structure we will work towards.

```
ai-gamemaster/
├── alembic/                 # Database migrations (unchanged)
├── app/
│   ├── api/                   # NEW: All Flask routes and blueprints
│   │   ├── __init__.py
│   │   ├── campaign_routes.py
│   │   ├── character_routes.py
│   │   └── ... (all other route files)
│   ├── core/                  # Core components, interfaces, and DI container
│   │   ├── __init__.py
│   │   ├── container.py
│   │   ├── event_queue.py
│   │   └── interfaces.py      # All abstract protocols (ABC)
│   ├── database/              # Database models, connection, and custom types
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── types.py
│   ├── domain/                # NEW: Core business logic
│   │   ├── __init__.py
│   │   ├── campaigns/         # NEW: Campaign management logic
│   │   │   └── services.py    # (Previously CampaignService)
│   │   ├── characters/        # NEW: Character management logic
│   │   │   ├── factories.py
│   │   │   └── services.py    # (Previously CharacterService)
│   │   ├── combat/            # NEW: Combat logic
│   │   │   └── services.py    # (Previously CombatService)
│   │   └── game_model/        # NEW: The core GameStateModel and its direct modifiers
│   │       ├── game_state.py
│   │       └── state_processors.py
│   ├── events/                # Event definitions (mostly unchanged)
│   │   ├── __init__.py
│   │   └── definitions.py     # (Previously game_update_events.py)
│   ├── models/                # Pydantic data models (single source of truth)
│   │   ├── __init__.py
│   │   ├── campaign.py
│   │   ├── character.py
│   │   └── ... (all other Pydantic models)
│   ├── providers/             # NEW: External service integrations
│   │   ├── __init__.py
│   │   ├── ai/                  # NEW: AI provider clients
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── manager.py
│   │   │   └── openai_service.py
│   │   └── tts/               # NEW: TTS provider clients
│   │       ├── __init__.py
│   │       ├── manager.py
│   │       └── kokoro_service.py
│   ├── rag/                   # NEW: Retrieval-Augmented Generation system
│   │   ├── __init__.py
│   │   ├── context_builder.py
│   │   ├── knowledge_base.py  # Abstraction for KB
│   │   ├── query_engine.py
│   │   └── service.py
│   ├── repositories/          # Data access layer
│   │   ├── __init__.py
│   │   ├── d5e/               # D5e database repositories
│   │   └── game/              # Game save repositories
│   ├── services/              # NEW: High-level application services
│   │   ├── __init__.py
│   │   ├── game_orchestrator.py # (Previously GameEventManager)
│   │   └── response_processor.py # (Previously AIResponseProcessorImpl)
│   ├── utils/                 # General-purpose utilities
│   │   ├── __init__.py
│   │   └── ... (json parser, token monitor, etc.)
│   ├── __init__.py            # Flask app factory
│   └── settings.py            # Pydantic settings configuration
├── docs/                      # (Unchanged)
├── knowledge/                 # (Unchanged)
├── scripts/
│   ├── db/                    # NEW: Database-related scripts
│   │   ├── __init__.py
│   │   ├── migrate_content.py # (Previously migrate_json_to_db.py)
│   │   ├── verify_db.py       # (Previously verify_migration.py)
│   │   └── index_for_rag.py   # (Previously index_content_for_rag.py)
│   └── dev/                   # NEW: Development utility scripts
│       └── generate_ts.py     # (Previously generate_typescript.py)
├── static/
├── templates/
├── tests/
│   ├── integration/
│   │   ├── api/
│   │   ├── database/
│   │   └── ... (mirrors app structure)
│   ├── unit/
│   │   ├── domain/
│   │   ├── providers/
│   │   └── ... (mirrors app structure)
│   └── conftest.py
├── .env.example
├── README.md
└── ... (root config files)
```

## 3. Implementation Plan

The reorganization will be executed in phases to ensure stability and continuous validation.

### Phase 1: Foundational Directory Restructuring

**Objective:** Create the new top-level directories inside `app/` and move existing files to their new homes. This phase focuses on moving files and updating imports.

1.  **Create New `app/` Directories:**
    -   `app/api`
    -   `app/core`
    -   `app/database`
    -   `app/domain` (with subdirectories: `campaigns`, `characters`, `combat`, `game_model`)
    -   `app/events`
    -   `app/providers` (with subdirectories: `ai`, `tts`)
    -   `app/rag`
    -   `app/repositories` (with subdirectories: `d5e`, `game`)
    -   `app/services`
    -   `app/utils`

2.  **Move Files into New `app/` Directories:**
    -   **API Routes (`app/api`):**
        -   Move `app/routes/*` to `app/api/`.
        -   Rename `app/routes/__init__.py` to `app/api/__init__.py` and update blueprint registrations.
    -   **Core Components (`app/core`):**
        -   Move `app/core/container.py` and `app/core/event_queue.py` to `app/core/`.
        -   Consolidate all `...Protocol` and `...Interface` classes from `app/core/*interfaces.py` into a single `app/core/interfaces.py`.
    -   **Database (`app/database`):**
        -   Move `app/database/*` to `app/database/`.
    -   **Domain Logic (`app/domain`):**
        -   Move `app/game/factories/*` to `app/domain/characters/`.
        -   Move `app/game/calculators/*` to `app/domain/shared/calculators/` (as it's used by multiple domains).
        -   Move `app/services/campaign_service.py` to `app/domain/campaigns/service.py`.
        -   Move `app/services/character_service.py` to `app/domain/characters/service.py`.
        -   Move `app/services/combat_service.py` and `combat_utilities.py` to `app/domain/combat/`.
        -   Move `app/game/state_processors.py` to `app/domain/game_model/`.
    -   **Events (`app/events`):**
        -   Move `app/events/game_update_events.py` to `app/events/definitions.py`.
    -   **Providers (`app/providers`):**
        -   Move `app/ai_services/*` to `app/providers/ai/`.
        -   Move `app/tts_services/*` to `app/providers/tts/`.
    -   **RAG System (`app/rag`):**
        -   Move `app/services/rag/*` to `app/rag/`.
        -   Rename files for clarity:
            -   `rag_service.py` -> `service.py`
            -   `knowledge_bases.py` -> `knowledge_base.py`
    -   **Repositories (`app/repositories`):**
        -   Move `app/repositories/d5e/*` to `app/repositories/d5e/`.
        -   Move other repositories (e.g., `GameStateRepository`) to `app/repositories/game/`.
    -   **Application Services (`app/services`):**
        -   Move `app/services/game_events/game_event_manager.py` to `app/services/game_orchestrator.py`.
        -   Move `app/services/response_processors/ai_response_processor_impl.py` to `app/services/response_processor.py`.
    -   **Utilities (`app/utils`):**
        -   Move files like `robust_json_parser.py`, `token_monitor.py` to `app/utils/`.

3.  **Update All Imports:**
    -   Perform a project-wide search and replace for all import paths. For example, `from app.routes.game_routes import game_bp` becomes `from app.api.game_routes import game_bp`.
    -   This is the most time-consuming part of this phase. Be meticulous.

4.  **Testing/Validation:**
    -   Run `mypy app --strict` to catch all import and type errors.
    -   Run `ruff check . --fix` to clean up the code.
    -   Run `python tests/run_all_tests.py --with-rag` to ensure all functionality is intact.

### Phase 2: Restructure Scripts and Tests

**Objective:** Reorganize the `scripts/` and `tests/` directories to match the new application structure.

1.  **Reorganize `scripts/` Directory:**
    -   Create `scripts/db/` and `scripts/dev/`.
    -   Move `migrate_json_to_db.py` to `scripts/db/migrate_content.py`.
    -   Move `verify_migration.py` to `scripts/db/verify_db.py`.
    -   Move `index_content_for_rag.py` to `scripts/db/index_for_rag.py`.
    -   Move `generate_typescript.py` to `scripts/dev/generate_ts.py`.
    -   Update any CI scripts or `pre-commit` hooks that reference these scripts.

2.  **Reorganize `tests/` Directory:**
    -   For every new directory in `app/`, create a corresponding directory in `tests/unit/` and `tests/integration/`.
        -   Example: `app/providers/ai/` will have `tests/unit/providers/ai/` and `tests/integration/providers/ai/`.
    -   Move every test file to its new, mirrored location.
        -   Example: `tests/unit/test_openai_service.py` moves to `tests/unit/providers/ai/test_openai_service.py`.
        -   Example: `tests/integration/test_d5e_rag_integration.py` moves to `tests/integration/rag/test_d5e_integration.py`.
    -   Update any relative imports within the tests.
    -   Update `tests/pytest_plugins.py` and `tests/run_all_tests.py` to reflect the new test file locations and ignore patterns if necessary.

3.  **Testing/Validation:**
    -   Run `mypy tests --strict`.
    -   Run `python tests/run_all_tests.py --with-rag`. All tests must be discovered and pass.

### Phase 3: Final Cleanup and Documentation

**Objective:** Update all documentation and configuration to reflect the new structure, and remove obsolete files.

1.  **Update Documentation:**
    -   **`README.md`**: Update all file paths in the quick start, setup, and architecture sections.
    -   **`docs/ARCHITECTURE.md`**: Update the architecture diagram and file paths to match the new structure.
    -   **`docs/DATABASE-GUIDE.md`**: Update paths to migration and verification scripts.
    -   **All other docs**: Review for outdated file paths.

2.  **Update Configuration Files:**
    -   **`alembic.ini`**: Verify `script_location` and `prepend_sys_path` are still correct.
    -   **`.pre-commit-config.yaml`**: Update paths for `mypy` and `pytest` hooks.

3.  **Remove Obsolete Files:**
    -   Delete empty directories from the old structure (e.g., `app/routes`, `app/services`).
    -   Remove any consolidated files (e.g., the old `*interfaces.py` files).

4.  **Final Verification:**
    -   Perform a full `git status` to ensure no unexpected files are left behind.
    -   Run all checks one last time: `pre-commit run --all-files`.

## Appendix: Detailed File Migration Map

| Current Path | New Path | Rationale |
| --- | --- | --- |
| **Routes** | **`app/api/`** | Centralizes all web-facing API endpoints. |
| `app/routes/__init__.py` | `app/api/__init__.py` | |
| `app/routes/campaign_routes.py` | `app/api/campaign_routes.py` | |
| ... | ... | |
| **AI Services** | **`app/providers/ai/`** | Groups external AI provider logic. |
| `app/ai_services/*` | `app/providers/ai/*` | |
| **TTS Services** | **`app/providers/tts/`** | Groups external TTS provider logic. |
| `app/tts_services/*` | `app/providers/tts/*` | |
| **RAG System** | **`app/rag/`** | Consolidates all RAG logic. |
| `app/services/rag/rag_service.py` | `app/rag/service.py` | |
| `app/services/rag/query_engine.py` | `app/rag/query_engine.py` | |
| `app/services/rag/knowledge_bases.py` | `app/rag/knowledge_base.py` | |
| ... | ... | |
| **Core Components** | **`app/core/`** | Foundational, cross-cutting concerns. |
| `app/core/container.py` | `app/core/container.py` | (Stays) |
| `app/core/event_queue.py` | `app/core/event_queue.py` | (Stays) |
| `app/core/*interfaces.py` | `app/core/interfaces.py` | (Consolidated) |
| **Domain Logic** | **`app/domain/`** | Encapsulates core business rules. |
| `app/game/calculators/*` | `app/domain/shared/calculators/` | Shared domain logic. |
| `app/services/character_service.py`| `app/domain/characters/service.py` | Character-specific logic. |
| `app.game.factories.*`| `app/domain/characters/factories.py`| |
| ... | ... | |
| **Repositories** | **`app/repositories/`** | Abstracts data sources. |
| `app/repositories/d5e/*` | `app/repositories/d5e/*` | (Stays, but within new `repositories` dir) |
| `app/repositories/game_state_repository.py` | `app/repositories/game/game_state.py` | Game save logic. |
| ... | ... | |
| **Scripts** | **`scripts/`** | Categorized operational scripts. |
| `scripts/migrate_json_to_db.py` | `scripts/db/migrate_content.py` | Database operation. |
| `scripts/verify_migration.py` | `scripts/db/verify_db.py` | Database operation. |
| `scripts/generate_typescript.py` | `scripts/dev/generate_ts.py` | Development utility. |
| **Tests** | **`tests/`** | Mirrors the new `app/` structure. |
| `tests/unit/test_openai_service.py` | `tests/unit/providers/ai/test_openai_service.py` | |
| `tests/integration/test_d5e_api_integration.py` | `tests/integration/api/test_d5e_api_integration.py` | |
| ... | ... | (All other test files similarly moved) |

---
This structured plan ensures a methodical and safe reorganization of the repository, validated at each step to prevent regressions and ultimately leading to a much cleaner and more maintainable codebase.