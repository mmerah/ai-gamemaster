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

This phase streamlines the application's control flow by removing an unnecessary abstraction layer and implementing improvements based on architecture review.

### Task 3.1: Remove the `orchestration` Sub-package ✅ COMPLETED

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

### Task 3.2: Extract Shared State Management ✅ COMPLETED

**Objective:** Create a dedicated class to manage shared state with proper concurrency controls, replacing the current instance variables on GameOrchestrator. Since this is a single-player application, we use a single global state instead of session-based state management.

**Context for Junior Engineers:**
- Shared state on a singleton can cause race conditions between concurrent requests
- A dedicated state manager with proper locking ensures thread safety
- Clear API boundaries make the code easier to test and reason about
- This is a single-player game, so we maintain one global state rather than per-session states

**Implementation Steps:**

1. **Create SharedStateManager Class**
   ```python
   # app/services/shared_state_manager.py
   import threading
   import time
   from typing import Dict, List, Optional
   from app.models.game_state import AIRequestContextModel
   from app.models.utils import SharedHandlerStateModel
   
   class SharedStateManager:
       """Manages shared state for the single-user game application with thread-safe operations."""
       
       def __init__(self):
           # Single global state
           self.lock = threading.Lock()
           self.ai_processing = False
           self.needs_backend_trigger = False
           self.last_ai_request_context: Optional[AIRequestContextModel] = None
           self.last_ai_request_timestamp: Optional[float] = None
       
       def set_ai_processing(self, processing: bool) -> None:
           """Thread-safe setter for AI processing flag."""
           with self.lock:
               self.ai_processing = processing
       
       def is_ai_processing(self) -> bool:
           """Thread-safe getter for AI processing flag."""
           with self.lock:
               return self.ai_processing
       
       def try_begin_ai_processing(self) -> bool:
           """Atomically checks if AI is processing and sets the flag if it's not."""
           with self.lock:
               if self.ai_processing:
                   return False
               self.ai_processing = True
               return True
       
       def store_ai_request_context(
           self, 
           messages: List[Dict[str, str]], 
           initial_instruction: Optional[str] = None
       ) -> None:
           """Store AI request context for retry."""
           with self.lock:
               self.last_ai_request_context = AIRequestContextModel(
                   messages=messages.copy(),
                   initial_instruction=initial_instruction
               )
               self.last_ai_request_timestamp = time.time()
       
       def can_retry_last_request(self, max_age_seconds: int = 300) -> bool:
           """Check if retry is possible."""
           with self.lock:
               if not self.last_ai_request_context or not self.last_ai_request_timestamp:
                   return False
               return (time.time() - self.last_ai_request_timestamp) <= max_age_seconds
       
       def reset_state(self) -> None:
           """Reset all state to initial values. Useful for testing."""
           with self.lock:
               self.ai_processing = False
               self.needs_backend_trigger = False
               self.last_ai_request_context = None
               self.last_ai_request_timestamp = None
   ```

2. **Update GameOrchestrator to Use SharedStateManager**
   - Remove instance variables: `_shared_ai_request_context`, `_shared_ai_request_timestamp`, `_shared_state`
   - Add `shared_state_manager: SharedStateManager` to constructor
   - Update all methods to use the shared state manager directly (no session_id needed)

3. **Update Handler Context Setup**
   - Modify `_setup_shared_context` to share the state manager with all handlers
   - Each handler gets a reference to the shared state manager
   - No session_id parameter needed since it's single-player

**Testing / Validation:**
1. Create unit tests for SharedStateManager with concurrent access scenarios
2. Test reset functionality for test isolation
3. Verify no shared state remains on GameOrchestrator
4. Run integration tests to ensure proper state management

### Task 3.3: Implement Dependency Injection for Handlers ✅ **COMPLETE** (2025-06-18)

**Objective:** Refactor GameOrchestrator to receive handlers via dependency injection instead of creating them.

**Context for Junior Engineers:**
- Creating dependencies violates the Dependency Inversion Principle
- Injection makes testing easier - you can pass mock handlers
- The ServiceContainer should be responsible for creating all dependencies

**Implementation Steps:**

1. **Create Handler Interfaces**
   ```python
   # app/core/interfaces.py (add to existing file)
   from typing import Protocol
   from app.models.game_state import GameEventResponseModel, PlayerActionEventModel
   from app.models.dice import DiceRollSubmissionModel, DiceRollResultResponseModel
   
   class IPlayerActionHandler(Protocol):
       """Interface for player action handler."""
       def handle(self, action_data: PlayerActionEventModel, session_id: str) -> GameEventResponseModel: ...
   
   class IDiceSubmissionHandler(Protocol):
       """Interface for dice submission handler."""
       def handle(self, rolls: List[DiceRollSubmissionModel], session_id: str) -> GameEventResponseModel: ...
       def handle_completed_rolls(self, results: List[DiceRollResultResponseModel], session_id: str) -> GameEventResponseModel: ...
   
   class INextStepHandler(Protocol):
       """Interface for next step handler."""
       def handle(self, session_id: str) -> GameEventResponseModel: ...
   
   class IRetryHandler(Protocol):
       """Interface for retry handler."""
       def handle(self, session_id: str) -> GameEventResponseModel: ...
   ```

2. **Update GameOrchestrator Constructor**
   ```python
   class GameOrchestrator:
       def __init__(
           self,
           # Remove all service dependencies except what GameOrchestrator directly uses
           game_state_repo: IGameStateRepository,
           character_service: ICharacterService,
           shared_state_manager: SharedStateManager,
           # Add handler dependencies
           player_action_handler: IPlayerActionHandler,
           dice_submission_handler: IDiceSubmissionHandler,
           next_step_handler: INextStepHandler,
           retry_handler: IRetryHandler,
       ) -> None:
           # Just store references, don't create
           self.game_state_repo = game_state_repo
           self.character_service = character_service
           self.shared_state_manager = shared_state_manager
           self.player_action_handler = player_action_handler
           self.dice_submission_handler = dice_submission_handler
           self.next_step_handler = next_step_handler
           self.retry_handler = retry_handler
           
           # Event handlers dict
           self.event_handlers: Dict[str, Callable[[Any, str], GameEventResponseModel]] = {}
           self._register_event_handlers()
   ```

3. **Update ServiceContainer**
   ```python
   # app/core/container.py
   def _create_player_action_handler(self) -> PlayerActionHandler:
       """Create player action handler with all dependencies."""
       return PlayerActionHandler(
           game_state_repo=self.get_game_state_repository(),
           character_service=self.get_character_service(),
           dice_service=self.get_dice_service(),
           combat_service=self.get_combat_service(),
           chat_service=self.get_chat_service(),
           ai_response_processor=self.get_ai_response_processor(),
           campaign_service=self.get_campaign_service(),
           rag_service=self.get_rag_service() if self._is_rag_enabled() else None,
       )
   
   # Similar methods for other handlers...
   
   def _create_game_orchestrator(self) -> GameOrchestrator:
       """Create game orchestrator with injected handlers."""
       return GameOrchestrator(
           game_state_repo=self.get_game_state_repository(),
           character_service=self.get_character_service(),
           shared_state_manager=self.get_shared_state_manager(),
           player_action_handler=self._create_player_action_handler(),
           dice_submission_handler=self._create_dice_submission_handler(),
           next_step_handler=self._create_next_step_handler(),
           retry_handler=self._create_retry_handler(),
       )
   ```

**Testing / Validation:**
1. Update GameOrchestrator unit tests to pass mock handlers
2. Verify ServiceContainer creates all dependencies correctly
3. Test that handlers can be easily mocked for testing
4. Ensure all integration tests still pass

### Task 3.4: Standardize Event Types with Enums

**Objective:** Replace magic strings for event types with a type-safe Enum.

**Context for Junior Engineers:**
- Magic strings are error-prone (typos, no autocomplete)
- Enums provide type safety and make all options visible
- Inheriting from `str` makes enums JSON-serializable

**Implementation Steps:**

1. **Create GameEventType Enum**
   ```python
   # app/models/events/event_types.py
   from enum import Enum
   
   class GameEventType(str, Enum):
       """All possible game event types."""
       # Player actions
       PLAYER_ACTION = "player_action"
       
       # Dice events
       DICE_SUBMISSION = "dice_submission"
       COMPLETED_ROLL_SUBMISSION = "completed_roll_submission"
       
       # Game flow events
       NEXT_STEP = "next_step"
       RETRY = "retry"
       
       # Add other event types as needed
       GAME_STATE_REQUEST = "game_state_request"
       SAVE_GAME = "save_game"
   ```

2. **Update GameEventModel**
   ```python
   # app/models/game_state.py
   from app.models.events.event_types import GameEventType
   
   class GameEventModel(BaseModel):
       """Model for game events."""
       type: GameEventType  # Changed from str
       data: Any
       session_id: str  # Make required, not optional
   ```

3. **Update GameOrchestrator**
   ```python
   # Update event_handlers type
   self.event_handlers: Dict[GameEventType, Callable[[Any, str], GameEventResponseModel]] = {}
   
   # In _register_event_handlers
   self.event_handlers[GameEventType.PLAYER_ACTION] = self._handle_player_action_wrapper
   self.event_handlers[GameEventType.DICE_SUBMISSION] = self._handle_dice_submission_wrapper
   self.event_handlers[GameEventType.NEXT_STEP] = lambda _, sid: self.next_step_handler.handle(sid)
   self.event_handlers[GameEventType.RETRY] = lambda _, sid: self.retry_handler.handle(sid)
   
   # In handle_event - simpler!
   def handle_event(self, event: GameEventModel) -> GameEventResponseModel:
       """Handle any game event."""
       handler = self.event_handlers.get(event.type)
       if not handler:
           raise ValueError(f"No handler for event type: {event.type.value}")
       return handler(event.data, event.session_id)
   ```

4. **Update All Event Creation**
   - Search for all places creating events with string types
   - Replace with enum values:
   ```python
   # Before
   event = GameEventModel(type="player_action", data=action_data)
   
   # After
   event = GameEventModel(
       type=GameEventType.PLAYER_ACTION, 
       data=action_data,
       session_id=session_id
   )
   ```

**Testing / Validation:**
1. Update all tests to use GameEventType enum
2. Test that invalid event types raise errors at creation time
3. Verify JSON serialization still works
4. Use IDE to find all string event type usages

### Task 3.5: Simplify Public API to Single Entry Point

**Objective:** Make `handle_event` the only public method for processing game events.

**Context for Junior Engineers:**
- Multiple entry points create confusion about which to use
- A single entry point creates a cleaner facade pattern
- Internal methods should be private (prefix with _)

**Implementation Steps:**

1. **Make Handler Methods Private**
   ```python
   # In GameOrchestrator, rename methods:
   def handle_player_action(...) -> ...      # Before
   def _handle_player_action(...) -> ...     # After (private)
   
   def handle_dice_submission(...) -> ...    # Before  
   def _handle_dice_submission(...) -> ...   # After (private)
   
   # Do this for all: handle_completed_roll_submission, handle_next_step_trigger, handle_retry
   ```

2. **Create Wrapper Methods for Event Handlers**
   ```python
   def _handle_player_action_wrapper(self, data: Any, session_id: str) -> GameEventResponseModel:
       """Wrapper to adapt event handler signature."""
       # Validate and convert data to proper type
       if not isinstance(data, PlayerActionEventModel):
           raise ValueError(f"Expected PlayerActionEventModel, got {type(data)}")
       return self.player_action_handler.handle(data, session_id)
   
   def _handle_dice_submission_wrapper(self, data: Any, session_id: str) -> GameEventResponseModel:
       """Wrapper to adapt event handler signature."""
       # Extract rolls from data
       if hasattr(data, 'rolls'):
           rolls = data.rolls
       elif isinstance(data, list):
           rolls = data
       else:
           raise ValueError(f"Invalid dice submission data: {type(data)}")
       return self.dice_submission_handler.handle(rolls, session_id)
   ```

3. **Update Public Interface Documentation**
   ```python
   class GameOrchestrator:
       """
       Main game orchestrator with a single public entry point.
       
       Usage:
           orchestrator = container.get_game_orchestrator()
           event = GameEventModel(
               type=GameEventType.PLAYER_ACTION,
               data=PlayerActionEventModel(value="I cast fireball"),
               session_id="session-123"
           )
           response = orchestrator.handle_event(event)
       """
       
       def handle_event(self, event: GameEventModel) -> GameEventResponseModel:
           """
           Process any game event.
           
           This is the ONLY public method for event processing.
           All game actions should be wrapped in a GameEventModel.
           
           Args:
               event: The game event to process
               
           Returns:
               Response containing game state updates
               
           Raises:
               ValueError: If event type is unknown or data is invalid
           """
   ```

**Testing / Validation:**
1. Update all tests to use handle_event exclusively
2. Verify private methods are not accessible from outside
3. Test error handling for invalid event data
4. Update integration tests to use new API

### Task 3.6: Update API Routes to Use Unified Interface

**Objective:** Update all API route handlers to use the new single-entry-point GameOrchestrator interface.

**Context for Junior Engineers:**
- API routes currently call different GameOrchestrator methods
- They need to be updated to create GameEventModel objects
- This creates consistency across all endpoints

**Implementation Steps:**

1. **Update Player Action Route**
   ```python
   # app/api/game_routes.py
   @game_bp.route("/action", methods=["POST"])
   def player_action():
       """Submit a player action."""
       try:
           # Get request data
           data = request.get_json()
           session_id = request.headers.get("X-Session-ID", "default")
           
           # Create event model
           action_model = PlayerActionEventModel(**data)
           event = GameEventModel(
               type=GameEventType.PLAYER_ACTION,
               data=action_model,
               session_id=session_id
           )
           
           # Process through single entry point
           orchestrator = get_game_orchestrator()
           response = orchestrator.handle_event(event)
           
           return jsonify(response.model_dump())
       except ValueError as e:
           return jsonify({"error": str(e)}), 400
   ```

2. **Update Dice Submission Route**
   ```python
   @game_bp.route("/dice/submit", methods=["POST"])
   def submit_dice():
       """Submit dice roll results."""
       try:
           data = request.get_json()
           session_id = request.headers.get("X-Session-ID", "default")
           
           # Validate rolls
           rolls = [DiceRollSubmissionModel(**roll) for roll in data.get("rolls", [])]
           
           event = GameEventModel(
               type=GameEventType.DICE_SUBMISSION,
               data={"rolls": rolls},  # Note: wrapper object
               session_id=session_id
           )
           
           orchestrator = get_game_orchestrator()
           response = orchestrator.handle_event(event)
           
           return jsonify(response.model_dump())
       except ValueError as e:
           return jsonify({"error": str(e)}), 400
   ```

3. **Create Route Helper Function**
   ```python
   # app/api/helpers.py
   def process_game_event(
       event_type: GameEventType,
       data: Any,
       session_id: Optional[str] = None
   ) -> Tuple[Dict[str, Any], int]:
       """
       Helper to process game events consistently across routes.
       
       Returns:
           Tuple of (response_dict, http_status_code)
       """
       try:
           if not session_id:
               session_id = request.headers.get("X-Session-ID", "default")
               
           event = GameEventModel(
               type=event_type,
               data=data,
               session_id=session_id
           )
           
           orchestrator = get_game_orchestrator()
           response = orchestrator.handle_event(event)
           
           return response.model_dump(), 200
           
       except ValueError as e:
           logger.warning(f"Invalid request: {e}")
           return {"error": "Invalid request"}, 400
       except Exception as e:
           logger.error(f"Internal error: {e}")
           return {"error": "Internal server error"}, 500
   ```

4. **Update All Routes to Use Helper**
   ```python
   @game_bp.route("/action", methods=["POST"])
   def player_action():
       """Submit a player action."""
       data = request.get_json()
       action_model = PlayerActionEventModel(**data)
       response, status = process_game_event(
           GameEventType.PLAYER_ACTION, 
           action_model
       )
       return jsonify(response), status
   ```

**Testing / Validation:**
1. Test all API endpoints with the new structure
2. Verify session IDs are properly passed through
3. Test error handling for missing session IDs
4. Run API integration tests
5. Update API documentation/OpenAPI spec

## Post-Refactoring Checklist

- [ ] **Run all tests**: Execute `python tests/run_all_tests.py --with-rag` to ensure all functionality remains intact.
- [ ] **Update `__init__.py` files**: Check all `__init__.py` files to ensure they export the correct, renamed modules and classes.
- [ ] **Update `.pre-commit-config.yaml`**: The `mypy` entries may need their file paths updated if any top-level files were moved.
- [ ] **Review `README.md` and `docs/`**: Update any references to file paths or class names that have changed (e.g., in the Architecture section).
- [ ] **Review `run.py`**: Ensure the application entry point is still correct.
- [ ] **Perform a global search**: Search for old file and class names (`*Impl`, `*factories.py`, `orchestration`, etc.) to catch any remaining references.