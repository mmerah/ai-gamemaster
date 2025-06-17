Of course. Here is a detailed implementation plan for refactoring your project structure, renaming files, and standardizing interface and implementation names.

---

# Refactoring and Reorganization Plan

This document outlines a detailed plan to refactor the `ai-gamemaster` project for a cleaner, more intuitive structure. The plan is divided into three main phases:

1.  **Folder and File Reorganization**: Restructure directories and rename files for clarity and consistency.
2.  **Interface and Implementation Renaming**: Standardize the naming convention for interfaces (e.g., `ICharacterService`) and their concrete implementations (e.g., `CharacterService`).
3.  **Service Layer Simplification**: Flatten the service layer by removing the `orchestration` sub-package, making the architecture more direct.

## Proposed Project Structure (Key Changes)

This is the target structure for the most impacted directories.

```diff
ai-gamemaster/
└── app/
    ├── api/
    ├── content/
    ├── core/
    │   ├── container.py
    │   ├── event_queue.py
    │   ├── interfaces.py
    │   └── repository_interfaces.py
    ├── domain/
    │   ├── campaigns/
    │   │   ├── campaign_factory.py     # Renamed
    │   │   └── campaign_service.py     # Renamed
    │   ├── characters/
    │   │   ├── character_factory.py    # Renamed
    │   │   └── character_service.py    # Renamed
    │   ├── combat/
    │   │   ├── combat_factory.py       # Renamed
    │   │   └── combat_service.py
    │   ├── npcs/
    │   │   └── npc_factory.py          # Renamed
    │   └── quests/
    │       └── quest_factory.py        # Renamed
    ├── models/
    ├── providers/
    │   ├── ai/
-   │   │   ├── prompt_builder.py
-   │   │   └── system_prompt.py
    │   └── tts/
    ├── repositories/
    │   └── game/
    │       └── game_state_repository.py # Renamed
    ├── services/
-   │   ├── game_orchestrator.py
-   │   ├── ai_response_processor.py      # Renamed
-   │   ├── chat_service.py
-   │   ├── dice_service.py
-   │   ├── tts_integration_service.py
+   │   ├── action_handlers/                # New: Was services/game_events/handlers
+   │   │   ├── __init__.py
+   │   │   ├── base_handler.py
+   │   │   ├── dice_submission_handler.py
+   │   │   ├── next_step_handler.py
+   │   │   ├── player_action_handler.py
+   │   │   └── retry_handler.py
+   │   ├── state_updaters/                 # New: Was domain/game_model/processors
+   │   │   ├── __init__.py
+   │   │   ├── combat_hp_updater.py        # Renamed
+   │   │   ├── combat_state_updater.py     # Renamed
+   │   │   ├── inventory_updater.py        # Renamed
+   │   │   └── quest_updater.py            # Renamed
-   │   ├── game_events/
-   │   │   └── handlers/
-   │   ├── orchestration/
-   │   └── response_processors/
    └── utils/
```

## Phase 1: File & Folder Reorganization

This phase focuses on moving and renaming files to create a more logical structure. It should be done first as it provides the foundation for subsequent code changes.

### Task 1.1: Relocate `game_model/processors`

The state processors are part of the application logic, not the domain model.

- **Action**: Move the directory `app/domain/game_model/processors/` to `app/services/state_updaters/`.
- **Action**: Rename the files within the new `state_updaters` directory for clarity.
  - `combat_hp_processor.py` -> `combat_hp_updater.py`
  - `combat_state_processor.py` -> `combat_state_updater.py`
  - `inventory_state_processor.py` -> `inventory_updater.py`
  - `quest_state_processor.py` -> `quest_updater.py`
  - `combat_condition_processor.py` -> `combat_condition_updater.py`
- **Impact**:
  - Update imports in `app/services/response_processor.py` (which will be renamed to `ai_response_processor.py`).
  - Update `__init__.py` files if they exist in the affected directories.

### Task 1.2: Relocate `app/game` Contents

The `app/game` directory contains loosely related files. Let's move them to more appropriate locations.

- **Action**: Move `app/game/prompt_builder.py` to `app/providers/ai/prompt_builder.py`.
- **Action**: Move `app/game/initial_data.py` to `app/providers/ai/system_prompt.py`.
- **Impact**:
  - Update imports in `app/services/game_events/handlers/base_handler.py` and any other files that use `build_ai_prompt_context` or `SYSTEM_PROMPT`.
- **Action**: Delete the now-empty `app/game/` directory.

### Task 1.3: Consolidate Service Handlers

The `game_events/handlers` are a core part of the service layer. Let's elevate them.

- **Action**: Move the directory `app/services/game_events/handlers/` to `app/services/action_handlers/`.
- **Action**: Delete the now-empty `app/services/game_events/` directory.
- **Impact**: Update imports in `app/services/orchestration/*` and `app/services/game_orchestrator.py`.

### Task 1.4: Rename Generic `factories.py` and `service.py` Files

Generic names hide the purpose of the files.

- **Action**: Rename the following files:
  - `app/domain/campaigns/factories.py` -> `app/domain/campaigns/campaign_factory.py`
  - `app/domain/campaigns/service.py` -> `app/domain/campaigns/campaign_service.py`
  - `app/domain/characters/factories.py` -> `app/domain/characters/character_factory.py`
  - `app/domain/characters/service.py` -> `app/domain/characters/character_service.py`
  - `app/domain/combat/factories.py` -> `app/domain/combat/combat_factory.py`
  - `app/domain/npcs/factories.py` -> `app/domain/npcs/npc_factory.py`
  - `app/domain/quests/factories.py` -> `app/domain/quests/quest_factory.py`
  - `app/content/rag/service.py` -> `app/content/rag/rag_service.py`
  - `app/repositories/game/game_state.py` -> `app/repositories/game/game_state_repository.py`
  - `app/services/response_processor.py` -> `app/services/ai_response_processor.py`
- **Impact**: This will cause many import errors. Use your IDE's "Find and Replace in Files" feature to update all imports across the project.
  - Search for `from app.domain.campaigns.factories` and replace with `from app.domain.campaigns.campaign_factory`.
  - Repeat for all renamed files.

### Task 1.5: Deprecate `app/events/definitions.py`

This file re-exports models from `app/models/events`. It's now redundant.

- **Action**: Delete the file `app/events/definitions.py`.
- **Impact**: Update all imports that use `app.events.definitions` to import directly from `app/models/events`.
  - For example, `from app.events.definitions import GameStateSnapshotEvent` becomes `from app.models.events import GameStateSnapshotEvent`.
- **Action**: Delete the `app/events/` directory.

## Phase 2: Interface and Implementation Renaming

This phase applies a standard `IInterface`/`Implementation` naming convention.

### Task 2.1: Rename Core Service Interfaces and Implementations

- **Action**: In `app/core/interfaces.py`, rename the following classes:
  - `CharacterService` -> `ICharacterService`
  - `DiceRollingService` -> `IDiceRollingService`
  - `CombatService` -> `ICombatService`
  - `ChatService` -> `IChatService`
  - `AIResponseProcessor` -> `IAIResponseProcessor`
  - `RAGService` -> `IRAGService`
  - `BaseTTSService` -> `ITTSService`
- **Action**: In their respective implementation files, rename the concrete classes:
  - `app/domain/characters/character_service.py`: `CharacterServiceImpl` -> `CharacterService`
  - `app/services/dice_service.py`: `DiceRollingServiceImpl` -> `DiceRollingService`
  - `app/domain/combat/combat_service.py`: `CombatServiceImpl` -> `CombatService`
  - `app/services/chat_service.py`: `ChatServiceImpl` -> `ChatService`
  - `app/services/ai_response_processor.py`: `AIResponseProcessorImpl` -> `AIResponseProcessor`
  - `app/content/rag/rag_service.py`: `RAGServiceImpl` -> `RAGService`
  - `app/content/rag/no_op_rag_service.py`: `NoOpRAGService` -> `NoOpRAGService` (already good)
  - `app/providers/tts/kokoro_service.py`: `KokoroTTSService` -> `KokoroTTSService` (already good)
- **Impact**: Update all type hints and imports across the project. This will be a significant change affecting the service container, handlers, and API routes.

### Task 2.2: Rename Core Repository Interfaces

- **Action**: In `app/core/interfaces.py`, rename `GameStateRepository` -> `IGameStateRepository`.
- **Action**: In `app/core/repository_interfaces.py`, rename:
  - `CampaignTemplateRepository` -> `ICampaignTemplateRepository`
  - `CampaignInstanceRepository` -> `ICampaignInstanceRepository`
  - `CharacterTemplateRepository` -> `ICharacterTemplateRepository`
  - `CharacterInstanceRepository` -> `ICharacterInstanceRepository`
- **Impact**:
  - The implementation class names in `app/repositories/game/` are already correct (e.g., `CampaignTemplateRepository`), so no changes are needed there.
  - Update type hints in the service container (`app/core/container.py`) and any other places these interfaces are used.

## Phase 3: Service Layer Simplification

This phase streamlines the application's control flow by removing an unnecessary abstraction layer.

### Task 3.1: Remove the `orchestration` Sub-package

The services in `app/services/orchestration` primarily act as simple wrappers around the action handlers. We can simplify this by having `GameOrchestrator` manage and call the handlers directly.

- **Action**: Delete the directory `app/services/orchestration/`.
- **Action**: Modify `app/services/game_orchestrator.py`:
  1.  Remove imports for `CombatOrchestrationService`, `NarrativeOrchestrationService`, and `EventRoutingService`.
  2.  Directly instantiate `PlayerActionHandler`, `DiceSubmissionHandler`, `NextStepHandler`, and `RetryHandler`.
  3.  Re-implement the logic from `EventRoutingService` for handling event types and managing the shared retry context directly within `GameOrchestrator`.
  4.  The `handle_player_action`, `handle_dice_submission`, etc., methods will now call the appropriate handler directly.
- **Impact**:
  - `app/services/game_orchestrator.py` will become slightly larger but the overall architecture will be flatter and easier to trace.
  - The service container initialization in `app/core/container.py` will be simplified, as it will no longer need to create the orchestration services.

## Post-Refactoring Checklist

- [ ] **Run all tests**: Execute `python tests/run_all_tests.py --with-rag` to ensure all functionality remains intact.
- [ ] **Update `__init__.py` files**: Check all `__init__.py` files to ensure they export the correct, renamed modules and classes.
- [ ] **Update `.pre-commit-config.yaml`**: The `mypy` entries may need their file paths updated if any top-level files were moved.
- [ ] **Review `README.md` and `docs/`**: Update any references to file paths or class names that have changed (e.g., in the Architecture section).
- [ ] **Review `run.py`**: Ensure the application entry point is still correct.
- [ ] **Perform a global search**: Search for old file and class names (`*Impl`, `*factories.py`, `orchestration`, etc.) to catch any remaining references.