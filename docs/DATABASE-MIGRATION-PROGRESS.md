# Database Migration Progress

## Current Status: Phase 6.3 Complete | Service & API Cleanup

### Phase 5: Content Manager Implementation - COMPLETE ✅

#### Phase 5.5: Content Management UI/UX - COMPLETE ✅ (2025-06-16)

Successfully implemented dual database architecture and comprehensive content creation system:
- **Dual Database Architecture**: System DB (read-only SRD) + User DB (custom content)
- **Content Creation**: 100% coverage for all 25 D&D 5e content types with JSON upload and form creation
- **Frontend Improvements**: Full content management UI with pack detail views
- **Security & Quality**: Input validation, SQL injection prevention, 876 tests passing

### Phase 5.6: Type System Refactoring & State Management Cleanup - COMPLETE ✅ (2025-06-17)

Successfully completed comprehensive refactoring:
- **Content Service Integration**: All D&D 5e data now accessed through ContentService
- **Model Cleanup**: Removed duplicate models and JSON loading code
- **Frontend Integration**: Character creation now uses content packs with filtering
- **State Management**: Removed duplicate state from gameStore, clean separation of concerns
- **Type Safety**: Enhanced TypeScript generation with content constants
- **Testing**: 878 tests passing with full type safety (0 mypy errors)


### Phase 6: Architecture Consistency & Clean Code (Revised)

#### Phase 6.1: Core Refactoring (Week 1) ✅ **COMPLETE**

1. **Repository Pattern Standardization** ✅ **COMPLETE** (2025-06-17) ✅ **VERIFIED** (2025-06-17)
   - Created ABC interfaces for all repositories in `app/core/repository_interfaces.py`
   - Unified repository method naming:
     - `get_template/get_instance` → `get`
     - `save_template/save_instance` → `save`
     - `delete_template/delete_instance` → `delete`
     - `list_templates/list_all_instances` → `list`
     - `list_instances_for_template` → `list_by_template`
     - `list_templates_for_campaign` → `list_by_campaign`
   - Updated all repositories with new method names (backward compatibility maintained)
   - Updated all API routes and services to use new method names
   - Fixed CharacterInstanceModel validation errors by adding required id/name fields
   - Fixed test directory creation issues by removing file I/O from CampaignService
   - All unit tests now passing with unified interface

2. **CampaignFactory Creation** ✅ **COMPLETE** (2025-06-17) ✅ **VERIFIED WITH FIXES** (2025-06-17)
   - Created `app/domain/campaigns/factories.py` with CampaignFactory class
   - Extracted campaign instance creation logic from CampaignService
   - Implemented methods:
     - `create_campaign_instance` - Creates campaign instance from template
     - `create_initial_game_state` - Creates initial game state for new campaign
     - `create_game_state_from_instance` - Creates game state from existing instance
     - `create_template_preview_state` - Creates preview state for templates
     - `_merge_content_packs` - Handles content pack priority merging
   - Updated CampaignService to use factory for all creation logic
   - Updated ServiceContainer to provide both CharacterFactory and CampaignFactory
   - Created comprehensive unit tests for CampaignFactory
   - Updated existing CampaignService tests to work with factory pattern
   - Fixed factory coupling issue: CampaignService now takes CharacterFactory directly
   - All tests passing (878 passed, 1 skipped)

3. **Service Layer Splitting** ✅ **COMPLETE** (2025-06-17) ✅ **VERIFIED WITH FIXES** (2025-06-17)
   - Split GameOrchestrator into focused services:
     - `CombatOrchestrationService` - Handles all combat-specific orchestration
     - `NarrativeOrchestrationService` - Manages narrative and chat flow
     - `EventRoutingService` - Routes events and manages shared concerns
   - GameOrchestrator now acts as a thin coordination layer
   - All handlers properly encapsulated within their respective services
   - **YAGNI Cleanup**: Removed 10 unused methods from orchestration services:
     - CombatOrchestrationService: `validate_player_turn`, `get_npc_turn_instructions`, `advance_combat_turn`, `is_combat_active`
     - NarrativeOrchestrationService: `get_rag_context`, `format_scene_description`, `build_narrative_context`, `should_add_narrative_flourish`
     - EventRoutingService: `set_ai_processing`, `set_needs_backend_trigger` (only used in tests)
   - **Type Safety**: Improved shared context implementation
   - **Naming Consistency**: All orchestration services follow consistent naming pattern
   - **Integration Test Fix**: Fixed shared retry context to work across all handlers in Flask integration tests
   - Fixed all mypy type errors (0 errors)
   - All tests passing (879 passed, 1 skipped)

#### Phase 6.2: Model & Event Improvements (Week 2) - IN PROGRESS

1. **Model Reorganization** ✅ **COMPLETE** (2025-06-17) ✅ **VERIFIED** (2025-06-17)
   - Split large model files into logical sub-packages:
     - **character.py** (372 lines) → `character/` sub-package:
       - `template.py`: CharacterTemplateModel (static data)
       - `instance.py`: CharacterInstanceModel (dynamic state)
       - `combined.py`: CombinedCharacterModel (DTO)
       - `utils.py`: CharacterModifierDataModel, CharacterData
     - **events.py** (306 lines) → `events/` sub-package:
       - `base.py`: BaseGameEvent
       - `narrative.py`: Narrative events
       - `combat.py`: Combat and combatant events
       - `dice.py`: Dice roll events
       - `game_state.py`: Location, party, quest events
       - `system.py`: System events (processing, errors, snapshots)
       - `utils.py`: Utility models
     - **combat.py** (300 lines) → `combat/` sub-package:
       - `attack.py`: AttackModel
       - `combatant.py`: CombatantModel, InitialCombatantData
       - `state.py`: CombatStateModel, NextCombatantInfoModel
       - `response.py`: CombatInfoResponseModel (DTO)
   - Maintained backward compatibility with deprecation warnings
   - All imports re-exported through package __init__.py files
   - Type checking passes (mypy --strict: 0 errors)
   - All tests passing (882 passed, 1 skipped)
   - Verified 2025-06-17: All changes working correctly, original files reduced from ~300-370 lines to ~25-28 lines (deprecation warnings only)

2. **Event System Refactoring** ❌ **ABANDONED** (2025-06-17)
    - Started implementing EventBus pattern but determined it added complexity without value
    - Current event system works adequately for the application's needs
    - Better to focus on actual business logic improvements

3. **Additional Factories** ✅ **COMPLETE** (2025-06-17) ✅ **VERIFIED WITH INTEGRATION** (2025-06-17)
   - `CombatFactory` - Creates combat states and combatants
   - `QuestFactory` - Creates quests and objectives  
   - `NPCFactory` - Creates NPCs with consistent structure
   - Created comprehensive unit tests for all factories
   - Type-safe implementation with mypy --strict compliance
   - Integrated into ServiceContainer
   - **Integration Status**:
     - CombatFactory: Successfully integrated into ICombatService
       - Moved all combatant creation logic from ICombatService to factory
       - ICombatService.start_combat reduced from ~50 lines to ~10 lines
       - Factory handles both PC and NPC combatant creation with proper initiative
       - Made factory helper methods private for clean public interface
     - QuestFactory: Created but not integrated (quests managed via AI responses)
     - NPCFactory: Created but not integrated (NPCs managed via AI responses)
   - **Code Quality**: Fixed private method usage based on Gemini review
   - **Note**: AC calculation simplified (10 + DEX modifier) - proper equipment-based calculation would require ContentService integration
   - All tests passing (915 passed, 1 skipped)

#### Phase 6.3: Service & API Cleanup (Week 3) - IN PROGRESS

1. **State Processor Decomposition** ✅ **COMPLETE** (2025-06-17) ✅ **VERIFIED WITH CLEANUP** (2025-06-17)
   - **NOTE**: Processors have been relocated to `app/services/state_updaters/` as part of reorganization
   - Split `app/domain/game_model/state_processors.py` (1093 lines) into focused updaters:
     - `CombatStateUpdater` (269 lines) - Core combat state management (start, end, remove)
     - `CombatHPUpdater` (180 lines) - HP change handling
     - `CombatConditionUpdater` (198 lines) - Condition add/remove handling
     - `CombatHelpers` (176 lines) - Combat setup helper functions
     - `InventoryUpdater` (243 lines) - Inventory and gold management
     - `QuestUpdater` (85 lines) - Quest update handling
     - `utils.py` (41 lines) - Shared utilities (get_correlation_id, get_target_ids_for_update)
   - **Backward Compatibility Cleanup** (2025-06-17):
     - Removed backward compatibility wrapper (`state_processors.py`)
     - Updated `ai_response_processor.py` to import directly from updaters
     - Fixed test imports in `test_state_processors_combat_end.py`
   - **Architecture Benefits**:
     - All files under 300 lines as required
     - Clear separation of concerns
     - No backward compatibility debt
     - All 915 tests passing
     - Type safety maintained (mypy --strict: 0 errors)
   - **Gemini Review (2025-06-17)**:
     - "This is a model refactoring. Well done."
     - Excellent adherence to KISS, YAGNI, DRY, and SOLID principles
     - Massive improvement in Single Responsibility Principle (SRP)
     - Future consideration: Move from static methods to dependency injection

### Service Layer Simplification (Phase 3) ✅ **COMPLETE** (2025-06-18)

#### Task 3.1: Remove Orchestration Sub-package ✅ **COMPLETE** (2025-06-18)

Successfully simplified the service layer by removing the orchestration sub-package:

1. **Removed Orchestration Layer**: 
   - Deleted `app/services/orchestration/` directory containing:
     - `CombatOrchestrationService` - Was just a wrapper around DiceSubmissionHandler
     - `NarrativeOrchestrationService` - Was just a wrapper around PlayerActionHandler
     - `EventRoutingService` - Logic integrated directly into GameOrchestrator
   
2. **GameOrchestrator Refactoring**:
   - Now directly instantiates and manages action handlers
   - Integrated event routing logic from EventRoutingService
   - Manages shared context and retry functionality directly
   - Cleaner, flatter architecture that's easier to trace
   
3. **Test Updates**:
   - Fixed `test_game_orchestrator.py` to use direct handler references
   - All 737 unit tests passing
   - No functionality lost during refactoring
   
4. **Architecture Benefits**:
   - Removed unnecessary abstraction layer
   - Reduced indirection and complexity
   - GameOrchestrator is now the single coordinator for all handlers
   - Easier to understand control flow

#### Task 3.2: Extract Shared State Management ✅ **COMPLETE** (2025-06-18)

Successfully implemented thread-safe session state management:

1. **Created SharedStateManager**: 
   - New class in `app/services/shared_state_manager.py`
   - Thread-safe per-session state management
   - Handles AI processing flags, backend triggers, and retry context
   - Session cleanup for expired sessions
   
2. **Updated GameOrchestrator**:
   - Removed shared state instance variables
   - Now uses SharedStateManager for all state management
   - All handler methods updated to accept session_id parameter
   
3. **Updated All Action Handlers**:
   - Added session_id parameter to all handler methods
   - State accessed through SharedStateManager
   - Thread-safe operation for concurrent requests
   
4. **API Routes Updated**:
   - Added session ID generation in `game_routes.py`
   - All endpoints now pass session_id to handlers
   - Uses Flask sessions for consistent session management
   
5. **Test Updates**:
   - All tests updated to use SharedStateManager
   - Fixed test setup to provide session IDs
   - All 901 tests passing (5 skipped)
   
**Architecture Benefits**:
- Thread-safe concurrent request handling
- Proper session isolation
- Clear state management boundaries
- No more shared mutable state on singletons

#### Task 3.4: Standardize Event Types with Enums ✅ **COMPLETE** (2025-06-18)

Successfully replaced magic strings for event types with a type-safe Enum:

1. **Created GameEventType Enum**: 
   - New enum in `app/models/events/event_types.py`
   - Includes all event types: PLAYER_ACTION, DICE_SUBMISSION, NEXT_STEP, RETRY, etc.
   - Inherits from `str` for JSON serialization compatibility
   
2. **Updated GameEventModel**:
   - Changed `type` field from `Literal` to `GameEventType` enum
   - Ensures type safety and autocomplete for event types
   
3. **Updated GameOrchestrator**:
   - All event type comparisons use enum values
   - Better error handling for unknown event types
   
4. **Fixed Circular Imports**:
   - Used `TYPE_CHECKING` imports in event_utils.py and system.py
   - Resolved import cycles between game_state.py and events modules
   
5. **Test Updates**:
   - Updated all test files to use GameEventType enum
   - All 726 unit tests passing
   
**Architecture Benefits**:
- Type safety for event types (no more typos)
- IDE autocomplete for available event types
- Single source of truth for all event types
- JSON serialization works correctly (enum serializes to string value)

#### Task 3.5: Simplify Public API to Single Entry Point ✅ **COMPLETE** (2025-06-18)

Successfully simplified GameOrchestrator to have a single public method for event processing:

1. **Made Handler Methods Private**: 
   - Renamed all public handler methods to private (prefix with _)
   - `handle_player_action` → `_handle_player_action`
   - `handle_dice_submission` → `_handle_dice_submission`
   - `handle_completed_roll_submission` → `_handle_completed_roll_submission`
   - `handle_next_step_trigger` → `_handle_next_step_trigger`
   - `handle_retry` → `_handle_retry`
   
2. **Updated handle_event Method**:
   - Now calls private methods internally
   - Added support for COMPLETED_ROLL_SUBMISSION event type
   - Enhanced documentation to clarify it's the only public entry point
   - Fixed data handling for events without data (use empty dict {} instead of None)
   
3. **Added Backward Compatibility**:
   - Created deprecated wrapper methods for smooth transition
   - Each wrapper shows clear deprecation warning with migration path
   - All wrappers create GameEventModel and call handle_event
   
4. **Test Results**:
   - All 13 unit tests passing
   - Deprecation warnings shown as expected
   - No functionality lost during refactoring
   
**Architecture Benefits**:
- Single, clear entry point for all game events
- Cleaner facade pattern implementation
- Easier to understand and maintain
- Backward compatible for gradual migration

## Phase 6.3 Remaining Tasks (Service & API Cleanup)

### Task 6.3.2: API Route Consolidation (YAGNI) ✅ **COMPLETE** (2025-06-18)
   - Created `d5e_routes.py` with ~10 flexible endpoints replacing 41 individual ones:
     - `GET /api/d5e/content?type={type}&{filters}` - Generic list with filtering
     - `GET /api/d5e/content/{type}/{id}` - Generic get by ID
     - Kept specialized endpoints: search, character-options, class-at-level, starting-equipment, encounter-budget
   - Enhanced ContentService with new methods:
     - `get_content_filtered()` - Generic filtering for any content type
     - `get_content_by_id()` - Generic item retrieval
     - `get_character_options()` - Consolidated character creation data
     - Type-specific filter methods (_filter_spells, _filter_monsters, etc.)
   - Moved all filtering logic to service layer (proper separation of concerns)
   - Created comprehensive test suite (15 tests, all passing)
   
   **Results:**
   - Reduced API surface from 41 to ~10 endpoints
   - Improved consistency across all content types
   - Proper handling of query parameters (strings, lists)
   - Backward compatibility maintained (old endpoints still work)
   
   **Issues Found During Verification (2025-06-18):**
   - **Type Alias Issue**: Line 646 in ContentService uses variable in type expression
   - **DRY Violation**: VALID_CONTENT_TYPES duplicates content module
   - **Test Duplication**: test_d5e_api_integration.py and test_d5e_api.py overlap
   - **Frontend Types**: Using any[] instead of proper D5e types
   - **Performance**: In-memory filtering (acceptable for single-player game, add TODO)
   
   **Fixes Applied (2025-06-18):**
   1. ✅ Fixed TypeAlias syntax in ContentService (line 645)
   2. ✅ Replaced VALID_CONTENT_TYPES with get_supported_content_types() from content module
   3. ✅ Unified test files - merged test_d5e_api_integration.py into test_d5e_api.py
   4. ✅ Updated frontend campaignApi.ts to use proper D5e types instead of any[]
   5. ✅ Added TODO comment for future database-level filtering in ContentService
   
   **Gemini Review Feedback (Future Improvements):**
   - Add allow-list for filters per content type (security)
   - Return 400 errors for invalid filters (not silent ignore)
   - Add pagination support (limit/offset)
   - Consider API versioning (/api/v1/d5e/)
   - Add discovery endpoint for available types/filters

### Task 6.3.3: DRY Service Getters ✅ **COMPLETE WITH FIXES** (2025-06-19) ✅ **VERIFIED** (2025-06-19)

**Summary**: Centralized dependency injection and cleaned up interfaces.

**Key Changes Made**:
1. **Interface reorganization**: Split 675-line service_interfaces.py into 5 focused files:
   - `system_interfaces.py` - Core system interfaces (IEventQueue, etc.)
   - `content_interfaces.py` - D&D 5e content management (IContentService, IContentPackService)
   - `domain_interfaces.py` - Domain services (ICampaignService, ICharacterService, ICombatService)
   - `orchestration_interfaces.py` - Orchestration layer (IGameOrchestrator)
   - `external_interfaces.py` - External services (ITTSService, ITTSIntegrationService)

2. **Fixed return types**: Changed IContentService methods from `List[Any]` to proper types:
   - `get_alignments()` → `List[D5eAlignment]`
   - `get_skills()` → `List[D5eSkill]`
   - `get_ability_scores()` → `List[D5eAbilityScore]`
   - `get_languages()` → `List[D5eLanguage]`
   - `get_races()` → `List[D5eRace]`
   - `get_classes()` → `List[D5eClass]`
   - `get_backgrounds()` → `List[D5eBackground]`

3. **Created centralized dependencies.py**:
   - All service getters in one place
   - Eliminated duplicate getter functions across API routes
   - Created `error_handlers.py` with `with_error_handling` decorator

4. **Removed unused code**:
   - Deleted unused `/character-options` route and tests
   - Removed unused `inject_service` and `inject` functions from dependencies.py
   - Removed 6 unused error handling functions (kept only `with_error_handling` and `handle_pydantic_validation_error`)

5. **Enhanced type safety**: All services now have proper ABC interfaces

**Results**: 
- ~250 lines of unused code removed
- Improved type safety (mypy --strict: 0 errors)
- Cleaner architecture with proper separation of concerns
- No more anti-patterns

### Task 6.3.4: Response Processor Refactoring ✅ **COMPLETE** (2025-06-19)
    
Successfully refactored AIResponseProcessor from monolithic 584-line class to focused processors:

**Implementation:**
- Created interface-based design with dependency injection pattern (like game_orchestrator)
- Split into focused processors:
  - `NarrativeProcessor` (75 lines) - Handles narrative and location updates
  - `StateUpdateProcessor` (382 lines) - Handles all game state updates
  - `RagProcessor` (102 lines) - Handles RAG event logging  
  - `AIResponseProcessor` (335 lines) - Thin coordinator
- Created interfaces: `INarrativeProcessor`, `IStateUpdateProcessor`, `IRagProcessor`
- Processors injected via constructor in ServiceContainer
- Full type safety with mypy --strict compliance

**Results:**
- Improved testability - each processor can be tested independently
- Clear separation of concerns following Single Responsibility Principle
- Maintained backward compatibility with existing API
- All tests passing (922 tests)
- Type checking clean (0 errors)

**Gemini Review Feedback:**
- Excellent architecture with proper Coordinator Pattern
- No circular dependencies found
- Suggested internal decomposition for StateUpdateProcessor
- Recommended fixing unused variables with underscore prefix
- Future improvements: transactional integrity, Command Pattern for updates

### Task 6.3.5: Large Processor Decomposition 🔜 **PENDING**
   - **StateUpdateProcessor** (382 lines) needs internal decomposition:
     - Extract combat updates to private helper class
     - Extract inventory updates to private helper class
     - Extract condition updates to private helper class
     - Keep single public interface `IStateUpdateProcessor`
   - **DiceRequestHandler** (439 lines) needs refactoring:
     - Extract NPC dice handling logic
     - Extract player dice request logic
     - Extract initiative handling logic
     - Create focused helper classes
   - Both should follow internal decomposition pattern (not new public interfaces)
   - Target: All processor files under 200 lines

## Phase 6.4: Dependency & Architecture Simplification 🔜 **PENDING**

### Task 6.4.1: Event System Simplification (YAGNI)
    - Evaluate which events truly need the full handler pattern
    - Convert simple event handlers to direct method calls where appropriate
    - Remove `SharedHandlerStateModel` if not providing clear value
    - Keep event system only for truly decoupled components
    
    **Analysis (2025-06-18):**
    - Current event system usage:
      - EventQueue used in 12 service files for emitting events
      - Events used primarily for SSE updates to frontend (which makes sense)
      - Some internal events could be direct method calls
    - SharedHandlerStateModel removed in recent refactor - replaced with SharedStateManager
    - Events that should remain:
      - Frontend updates (LocationChangedEvent, CombatStartedEvent, etc.) - needed for SSE
      - Cross-boundary events (errors, system events)
    - Events that could be direct calls:
      - Internal state updates within same service boundary
      - Synchronous operations that don't need decoupling
    - Recommendation: Current event usage is mostly appropriate, minimal changes needed

### Task 6.4.2: Base Handler Decomposition
    - Extract common logic from `base_handler.py` (559 lines) to utilities:
      - `handler_utils.py` - Common validation and error handling
      - `state_utils.py` - State manipulation helpers
      - `event_utils.py` - Event creation and publishing helpers
    - Keep base handler thin (under 100 lines)
    
    **Analysis (2025-06-18):**
    - Current base handler has 14 methods mixing different concerns:
      - AI service interaction (`_call_ai_and_process_step`, `_build_ai_prompt_context`)
      - Frontend formatting (`_format_party_for_frontend`, `_get_state_for_frontend`)
      - Error handling (`_create_error_response`)
      - State management (`_clear_pending_dice_requests`)
    - Proposed extraction:
      - `handler_utils.py`: Error response creation, retry logic
      - `ai_utils.py`: AI prompt building, continuation logic
      - `frontend_utils.py`: All frontend formatting methods
      - `state_query_utils.py`: Methods for querying game state
    - Keep in base: Abstract `handle` method, core initialization
    - Benefits: Each utility module ~100-150 lines, base handler reduced to ~50 lines


## Migration Timeline Summary

| Phase | Status | Description |
|-------|--------|-------------|
| 1-4 | ✅ Complete | Database foundation, repositories, services, RAG |
| 5 | ✅ Complete | Backend API and initial frontend |
| 5.5 | ✅ Complete | Dual DB architecture, 100% content creation coverage |
| 5.6 | ✅ Complete | Type system refactoring & content service integration |
| 6.1 | ✅ Complete | Core refactoring (3/3 tasks complete) |
| 6.2 | ✅ Complete | Model & event improvements (3/3 tasks complete) |
| 6.3 | 🔄 In Progress | Service & API cleanup - 4/5 tasks complete |
| 6.4 | 🔜 Pending | Dependency & architecture simplification (YAGNI, SOLID) |

## Current Focus: Phase 6.3 - Service & API Cleanup - IN PROGRESS

Progress today (2025-06-19):
- ✅ Completed DRY Service Getters (Task 6.3.3) - Fixed interfaces and cleaned up unused code
- ✅ Removed ~250 lines of unused code following YAGNI principle
- ✅ Completed Response Processor Refactoring (Task 6.3.4) - Split 584-line class into focused processors

Completed Phase 6.3 tasks:
- ✅ State Processor Decomposition (Task 6.3.1)
- ✅ API Route Consolidation (Task 6.3.2) - Reduced 41 endpoints to ~10
- ✅ DRY Service Getters (Task 6.3.3) - Fixed return types, removed unused functions
- ✅ Response Processor Refactoring (Task 6.3.4) - Interface-based design with DI
- 🔜 Large Processor Decomposition (Task 6.3.5) - Pending for StateUpdateProcessor and DiceRequestHandler

### Key Architecture Decisions

1. **Content Service as Single Source of Truth**
   - All D&D 5e data accessed through ContentService
   - No direct JSON file access in the application
   - Content packs control all game content availability

2. **Separation of Concerns**
   - `app/content/` - All D&D 5e content management
   - `app/models/` - Runtime game state models only
   - Clear boundary between static content and dynamic state

3. **Type Safety**
   - Use Pydantic models throughout (no TypedDict)
   - Generate TypeScript from Pydantic models
   - Maintain 100% type safety in both backend and frontend

### Phase 6.3 & 6.4 Task Validity Assessment (2025-06-18)

After thorough analysis and discussion, the remaining valid tasks are:

**High Priority (Most Value):**
- Task 6.3.2 (API Consolidation): Would reduce d5e_routes.py from 749 to ~200 lines
- Task 6.3.4 (Response Processor): Would improve testability and maintainability
- Task 6.4.2 (Base Handler): Would reduce base_handler.py from 559 to ~50 lines

**Medium Priority (Good Improvements):**
- Task 6.3.3 (DRY Service Getters): Would eliminate ~100 lines of duplicate code

**Lower Priority (Minimal Changes Needed):**
- Task 6.4.1 (Event System): Current implementation is appropriate for SSE needs

The codebase has already seen significant improvements from earlier phases. The remaining tasks would further polish the architecture following KISS, YAGNI, and DRY principles.