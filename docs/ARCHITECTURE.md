# AI Game Master Architecture

This document provides the comprehensive technical architecture for the AI Game Master project, consolidating concepts, design decisions, type system guidelines, and the unified models architecture.

> **Note**: This is a living document reflecting ongoing development. Architecture and features are subject to change as the project evolves.

## 1. Project Vision

Create an open-source web application that acts as an AI-powered Game Master for D&D 5e, providing an immersive single-player or group experience with intelligent storytelling, combat management, and character progression. This is just a "for fun" project, at least for now.

## 2. Introduction

The AI Game Master application architecture is built around **unified data models** organized by domain in `app/models/` that serve as the single source of truth for all data structures, ensuring consistency, type safety, and seamless integration across backend, frontend, data persistence, and AI services.

## 3. Core Architecture Overview

### Backend (Python Flask)
- **Service-oriented architecture** with dependency injection container
- **Event-driven system** using Server-Sent Events (SSE) for real-time updates
- **Repository pattern** for data access abstraction
- **Pydantic models** for all data structures
- **JSON file persistence** for simplicity and portability
- **Modular AI providers** supporting both local and cloud models
- **Optional RAG** for enhanced D&D 5e knowledge context

### Frontend (Vue.js 3)
- **Component-based architecture** for reusability
- **Pinia state management** with separate stores for different concerns
- **Event-driven updates** via SSE subscription
- **Automatic reconnection** with state reconciliation
- **Tailwind CSS** with responsive design

### AI Integration
- **Structured JSON responses** with schema validation
- **Provider abstraction** allowing easy switching between AI services
- **Error recovery** with retry mechanisms and user feedback
- **Rate limiting handling** for cloud providers

## 4. Core Principles: Single Source of Truth

### 4.1 Unified Models Foundation
- **`app/models/`**: Domain-organized Pydantic models
  - `base.py`: Base classes and serializers
  - `character.py`: Character templates, instances, and combined models
  - `campaign.py`: Campaign templates and instances
  - `combat.py`: Combat state, combatants, and related models
  - `dice.py`: Dice requests, results, and submissions
  - `game_state.py`: Core game state and action models
  - `config.py`: Service configuration model
  - `utils.py`: Basic structures and utility models
  - `rag.py`: RAG and knowledge base models
  - `events.py`: Event models for state changes
  - `updates.py`: Game state update models (flattened structure)
- **Pydantic-First Architecture**:
  - Services and repositories work directly with Pydantic model instances
  - No intermediate dict conversions unless necessary for external APIs
  - Strong type safety with mypy --strict validation
  - Automatic validation at runtime via Pydantic
- **Automatic TypeScript Generation**: `scripts/generate_typescript.py` converts models to TypeScript
- **JSON Persistence**: Direct serialization of Pydantic models
- **Event Sequence Management**: Centralized via `app/utils/event_sequence.py`

### 4.2 Template vs Instance Architecture
- **Templates**: Reusable, static definitions (CampaignTemplateModel, CharacterTemplateModel)
- **Instances**: Active, dynamic state (CampaignInstanceModel, CharacterInstanceModel, GameStateModel)
- **Clear Separation**: Templates contain no runtime state; instances contain no static definitions

## 5. Type System Architecture (Pydantic-First)

This project follows a **Pydantic-First Architecture** where all data models are defined as Pydantic models. This provides strong type safety, automatic validation, and seamless serialization/deserialization throughout the application.

### Architecture Principles

1. **Pydantic Models Everywhere**
   - All core data structures are Pydantic models (in `app/models/`)
   - Services and repositories work directly with Pydantic model instances
   - No intermediate dict conversions unless necessary for external APIs

2. **Model Organization**
   ```
   app/models/
   ├── base.py        # Shared base models
   ├── character.py   # Character templates, instances, combined models
   ├── campaign.py    # Campaign templates, instances models
   ├── combat.py      # Combat state. combatants, and related models
   ├── dice.py        # Dice requests, results, and submissions
   ├── game_state.py  # Core game state and action models
   ├── config.py      # Service configuration model
   ├── utils.py       # Basic structures and utility models
   ├── updates.py     # Validated game state updates
   ├── events.py      # Event system models
   └── rag.py         # RAG system models
   ```

3. **Type Safety Benefits**
   - **Compile-time checking**: mypy --strict validates all type annotations
   - **Runtime validation**: Pydantic validates data at runtime
   - **Auto-serialization**: Models convert to/from JSON automatically
   - **Schema generation**: TypeScript types auto-generated from Pydantic models

### Common Patterns

```python
# Creating models
character = CharacterTemplateModel(
    id="wizard_1",
    name="Gandalf",
    race="Human",
    character_class="Wizard",
    level=20,
    stats=BaseStatsModel(STR=10, DEX=14, CON=12, INT=20, WIS=18, CHA=16)
)

# Accessing fields (type-safe)
name = character.name  # str
level = character.level  # int

# Serialization
json_data = character.model_dump()  # Convert to dict
json_str = character.model_dump_json()  # Convert to JSON string

# Deserialization
loaded = CharacterTemplateModel.model_validate(json_data)
```

### Best Practices

1. **Always use model classes** - Don't pass raw dicts between services
2. **Validate early** - Use Pydantic validation at API boundaries
3. **Avoid dict conversions** - Only use `model_dump()` when necessary
4. **Leverage type hints** - Use Optional, List, Dict with proper types
5. **Handle validation errors** - Catch `ValidationError` at API endpoints

### TypeScript Integration

Python models are automatically converted to TypeScript interfaces:

```bash
python scripts/generate_typescript.py
```

This ensures frontend type safety matches backend models exactly.

## 6. AI Integration Strategy

### Structured Output Approach
Instead of parsing natural language, the AI responds with structured JSON:

```json
{
  "narrative": "The door creaks open revealing a dimly lit chamber...",
  "dice_requests": [
    {
      "character_ids": ["player_1"],
      "type": "skill_check",
      "skill": "Perception",
      "dc": 13,
      "reason": "Spotting hidden dangers"
    }
  ],
  "location_update": {
    "name": "Ancient Chamber",
    "description": "Stone walls covered in mysterious runes",
    "features": ["altar", "shadows", "runes"]
  },
  "game_state_updates": [
    {
      "type": "condition_add",
      "character_id": "player_1",
      "condition": "Investigating"
    }
  ]
}
```

### AI Provider Abstraction
```python
class AIProvider:
    def generate_response(self, context: GameContext) -> GMResponse:
        """Generate structured GM response"""
        pass

    def validate_response(self, response: str) -> bool:
        """Validate response format"""
        pass
```

### Supported Providers
- **Local**: llamacpp HTTP server with various models
- **Cloud**: OpenRouter API (GPT, Claude, Gemini, etc.)

## 7. Game Mechanics

### Dice Rolling System
- **Player-initiated rolls**: Manual or simulated dice
- **GM-requested rolls**: Automatic skill checks, saves, attacks
- **Advantage/Disadvantage**: Full 5e support
- **Modifiers**: Automatic calculation from character stats

### Combat System
- **Initiative tracking**: Automatic turn order
- **Action economy**: Proper action/bonus action/reaction handling
- **Status effects**: Conditions, buffs, debuffs
- **HP management**: Damage tracking, healing

### Persistence Strategy
- **JSON files** for simplicity and human readability
- **Atomic saves** to prevent corruption
- **Backup system** for important game states
- **Export/Import** for sharing campaigns

## 8. System Architecture

### 8.1 System Architecture Diagram

```
                               +---------------------------+
                               | Frontend (Vue.js)         |
                               | - TypeScript unified.ts   |
                               | - Pinia Stores (typed)    |
                               | - Components (typed)      |
                               | - API Client              |
                               +-------------^-------------+
                                             | (HTTP API / SSE)
                                             v
+--------------------------------------------+------------------------------------------------+
| Backend (Flask)                                                                             |
|                                                                                             |
|  +---------------------+      +--------------------------+      +------------------------+  |
|  | API Routes          |<---->| Services                 |<---->| Repositories           |  |
|  | - CharacterTemplateM|      | - CampaignService        |      | - CharacterTemplateRepo|  |
|  | - CampaignTemplateM |      | - CharacterService       |      | - CampaignTemplateRepo |  |
|  | - GameStateModel    |      | - CombatService          |      | - GameStateRepository  |  |
|  +---------------------+      +------------^-------------+      +------------^-----------+  |
|                                            |                                |               |
|  +---------------------+                   |                                |               |
|  | Event Queue / SSE   |                   | (BaseGameEvent & subclasses)   |               |
|  | - NarrativeAddedE   |<------------------+                                |               |
|  | - CombatStartedE    |      +--------------------------+                  |               |
|  | - TurnAdvancedE     |      | GameEventManager         |                  |               |
|  | - PlayerDiceRequestE|      | - PlayerActionHandler    |                  |               |
|  +---------------------+      | - NextStepHandler        |                  |               |
|                               | - DiceSubmissionHandler  |                  |               |
|  +---------------------+      +--------------------------+                  |               |
|  | AI Service          |<---->| AIResponseProcessor      |                  |               |
|  | - OpenAIService     |      | - Processes AIResponse   |                  |               |
|  | - Receives context  |      | - Updates GameStateModel |                  |               |
|  | - Returns AIResponse|      | - Emits typed events     |                  |               |
|  +---------------------+      +--------------------------+                  |               |
|        ^       |                                                            |               |
|        |       | (Knowledge)                                                v               |
|  +---------------------+                                         +------------------------+ |
|  | RAG Service         |                                         | Data Persistence       | |
|  | - KnowledgeBase     |                                         | - CharacterTemplateM   | |
|  | - QueryEngine       |                                         | - CampaignTemplateM    | |
|  | - RAGContextBuilder |                                         | - GameStateModel       | |
|  +---------------------+                                         | - JSON Serialization   | |
|                                                                  |------------------------+ |
|  +--------------------------------------------------------------+                           |
|  | Core: app/models/*.py (Single Source of Truth)               |                           |
|  | - All Pydantic Models - CharacterTemplateModel               |                           |
|  | - Type Safety         - CampaignTemplateModel                |                           |
|  | - Auto TypeScript Gen - GameStateModel                       |                           |
|  | - Event Models        - CombatantModel, CombatStateModel     |                           |
|  +--------------------------------------------------------------+                           |
+---------------------------------------------------------------------------------------------+
```

## 9. Complete Unified Data Model Catalog

### 9.1 Base Types and Shared Models
- **ItemModel**: Equipment/inventory structure (id: str, name: str, description: str, quantity: int)
- **NPCModel**: Non-Player Character structure (id: str, name: str, description: str, last_location: str)
- **QuestModel**: Quest structure (id: str, title: str, description: str, status: str)
- **LocationModel**: Game location structure (name: str, description: str)
- **HouseRulesModel**: Campaign rule configuration (critical_hit_tables: bool, flanking_rules: bool, milestone_leveling: bool, death_saves_public: bool)
- **GoldRangeModel**: Min/max gold range for starting equipment (min: int, max: int)
- **BaseStatsModel**: D&D ability scores (STR: int, DEX: int, CON: int, INT: int, WIS: int, CHA: int) with Field(ge=1, le=30)
- **ProficienciesModel**: Categorized proficiency lists (armor: List[str], weapons: List[str], tools: List[str], saving_throws: List[str], skills: List[str])
- **TraitModel**: Generic trait structure for racial traits and feats (name: str, description: str)
- **ClassFeatureModel**: Class feature with level acquisition (name: str, description: str, level_acquired: int)

### 9.2 Character Models
- **CharacterTemplateModel**: Complete static character definition including:
  - Identity fields (id: str, name: str, race: str, subrace: Optional[str], char_class: str, subclass: Optional[str], level: int, background: str, alignment: str)
  - Stats and mechanics (base_stats: BaseStatsModel, proficiencies: ProficienciesModel, languages: List[str])
  - Traits and features (racial_traits: List[TraitModel], class_features: List[ClassFeatureModel], feats: List[TraitModel])
  - Spellcasting (spells_known: List[str], cantrips_known: List[str])
  - Equipment (starting_equipment: List[ItemModel], starting_gold: int)
  - Character details (portrait_path: Optional[str], personality_traits: List[str], ideals: List[str], bonds: List[str], flaws: List[str], appearance: Optional[str], backstory: Optional[str])
  - Metadata (created_date: Optional[datetime], last_modified: Optional[datetime])

- **CharacterInstanceModel**: Dynamic character state within campaigns including:
  - Template linking (template_id: str, campaign_id: str)
  - Current state (current_hp: int, max_hp: int, temp_hp: int)
  - Experience (experience_points: int, level: int)
  - Resources (spell_slots_used: Dict[int, int], hit_dice_used: int, death_saves: Dict[str, int])
  - Inventory (inventory: List[ItemModel], gold: int)
  - Conditions and effects (conditions: List[str], exhaustion_level: int)
  - Campaign-specific data (notes: str, achievements: List[str], relationships: Dict[str, str])
  - Activity tracking (last_played: datetime)

### 9.3 Campaign Models
- **CampaignTemplateModel**: Reusable campaign scenario definition including:
  - Identity (id: str, name: str, description: str)
  - Core campaign info (campaign_goal: str, starting_location: LocationModel, opening_narrative: str)
  - Mechanics (starting_level: int, difficulty: str, ruleset_id: str, lore_id: str)
  - Initial content (initial_npcs: Dict[str, NPCModel], initial_quests: Dict[str, QuestModel], world_lore: List[str])
  - Rules and restrictions (house_rules: HouseRulesModel, allowed_races: Optional[List[str]], allowed_classes: Optional[List[str]], starting_gold_range: Optional[GoldRangeModel])
  - Additional info (theme_mood: Optional[str], world_map_path: Optional[str], session_zero_notes: Optional[str], xp_system: str)
  - TTS settings (narration_enabled: bool, tts_voice: str)
  - Metadata (created_date: datetime, last_modified: datetime, tags: List[str])

- **CampaignInstanceModel**: Active campaign state tracking including:
  - Identity (id: str, name: str, template_id: Optional[str])
  - Party (character_ids: List[str])
  - Current state (current_location: str, session_count: int, in_combat: bool, event_summary: List[str])
  - Event tracking (event_log_path: str, last_event_id: Optional[str])
  - Metadata (created_date: datetime, last_played: datetime)

### 9.4 Combat Models
- **CombatantModel**: Individual combat participant including:
  - Identity (id: str, name: str, icon_path: Optional[str])
  - Combat stats (initiative: int, initiative_modifier: int, current_hp: int, max_hp: int, armor_class: int)
  - State (conditions: List[str], is_player: bool)
  - Computed properties (is_defeated: bool, is_incapacitated: bool, is_player_controlled: bool)
  - HP validation logic (model_post_init validation)

- **CombatStateModel**: Complete combat encounter state including:
  - Status (is_active: bool)
  - Participants (combatants: List[CombatantModel])
  - Turn management (current_turn_index: int, round_number: int, current_turn_instruction_given: bool)
  - Monster data (monster_stats: Dict[str, MonsterBaseStats])
  - Internal flags (_combat_just_started_flag: bool)
  - Helper methods (get_current_combatant, get_combatant_by_id, get_initiative_order, get_next_active_combatant_index)

### 9.5 Game State Model
- **GameStateModel**: Central runtime object containing:
  - Campaign identity (campaign_id: Optional[str], campaign_name: Optional[str])
  - Campaign context (active_ruleset_id: Optional[str], active_lore_id: Optional[str], event_log_path: Optional[str])
  - Party state (party: Dict[str, CharacterInstanceModel])
  - Location (current_location: LocationModel)
  - Communication (chat_history: List[ChatMessage], pending_player_dice_requests: List[DiceRequest])
  - Combat (combat: CombatStateModel)
  - Campaign context (campaign_goal: str, known_npcs: Dict[str, NPCModel], active_quests: Dict[str, QuestModel], world_lore: List[str], event_summary: List[str])
  - Session tracking (session_count: int, in_combat: bool, last_event_id: Optional[str])
  - Private fields (_pending_npc_roll_results: List[DiceRollResult], _last_rag_context: Optional[str])
  - Field validators for automatic type conversion

### 9.6 AI Integration Models (from app/ai_services/schemas.py)
- **ChatMessage**: Chat message structure (id: str, role: str, content: str, timestamp: str, gm_thought: Optional[str], audio_path: Optional[str])
- **DiceRequest**: Dice roll request (request_id: str, character_ids: List[str], dice_formula: str, roll_type: str, purpose: str, dc: Optional[int], skill: Optional[str], ability: Optional[str])
- **DiceRollResult**: Dice roll outcome (request_id: str, character_id: str, total: int, details: str, roll_type: str, purpose: str, success: Optional[bool])
- **MonsterBaseStats**: Monster statistics (name: str, initial_hp: int, ac: int, attack_bonus: Optional[int], damage_dice: Optional[str])
- **AIResponse**: LLM response structure (reasoning: str, narrative: str, dice_requests: List[DiceRequest], game_state_updates: List[GameStateUpdate], end_turn: bool)
- **GameStateUpdate**: State modification instruction (update_type: str, target_id: str, changes: Dict[str, Any])

### 9.7 RAG System Models (from app/core/rag_interfaces.py)
- **KnowledgeResult**: Search result from knowledge base (content: str, source: str, relevance_score: float, metadata: Dict[str, Any])
- **RAGResults**: Collection of knowledge results (results: List[KnowledgeResult], total_results: int, query: str)
- **QueryRequest**: RAG query structure (query: str, max_results: int, relevance_threshold: float, knowledge_types: List[str])

### 9.8 Event Models Hierarchy

#### Base Event Model
- **BaseGameEvent**: Parent class with common fields (event_id: str, timestamp: datetime, sequence_number: int, event_type: str, correlation_id: Optional[str])

#### Narrative Events
- **NarrativeAddedEvent**: Chat message addition (role: str, content: str, gm_thought: Optional[str], audio_path: Optional[str], message_id: Optional[str])
- **MessageSupersededEvent**: Message replacement/retry (message_id: str, reason: str)

#### Combat Events
- **CombatStartedEvent**: Combat initiation (combatants: List[Dict[str, Any]], round_number: int)
- **CombatEndedEvent**: Combat conclusion (reason: str, outcome_description: Optional[str])
- **TurnAdvancedEvent**: Turn progression (new_combatant_id: str, new_combatant_name: str, round_number: int, is_new_round: bool, is_player_controlled: bool)

#### Combatant State Events
- **CombatantHpChangedEvent**: Health point changes (combatant_id: str, combatant_name: str, old_hp: int, new_hp: int, max_hp: int, change_amount: int, is_player_controlled: bool, source: Optional[str])
- **CombatantStatusChangedEvent**: Condition changes (combatant_id: str, combatant_name: str, new_conditions: List[str], added_conditions: List[str], removed_conditions: List[str], is_defeated: bool)
- **CombatantAddedEvent**: Combatant joining (combatant_id: str, combatant_name: str, hp: int, max_hp: int, ac: int, is_player_controlled: bool, position_in_order: Optional[int])
- **CombatantRemovedEvent**: Combatant departure (combatant_id: str, combatant_name: str, reason: str)

#### Initiative Events
- **CombatantInitiativeSetEvent**: Initiative assignment (combatant_id: str, combatant_name: str, initiative_value: int, roll_details: Optional[str])
- **InitiativeOrderDeterminedEvent**: Turn order establishment (ordered_combatants: List[Dict[str, Any]])

#### Dice Roll Events
- **PlayerDiceRequestAddedEvent**: Player roll request (request_id: str, character_id: str, character_name: str, roll_type: str, dice_formula: str, purpose: str, dc: Optional[int], skill: Optional[str], ability: Optional[str])
- **PlayerDiceRequestsClearedEvent**: Request cleanup (cleared_request_ids: List[str])
- **NpcDiceRollProcessedEvent**: NPC roll execution (character_id: str, character_name: str, roll_type: str, dice_formula: str, total: int, details: str, success: Optional[bool], purpose: str)

#### Game State Events
- **LocationChangedEvent**: Location transitions (new_location_name: str, new_location_description: str, old_location_name: Optional[str])
- **PartyMemberUpdatedEvent**: Character state changes (character_id: str, character_name: str, changes: Dict[str, Any])

#### System Events
- **BackendProcessingEvent**: Processing status (is_processing: bool, needs_backend_trigger: bool, trigger_reason: Optional[str])
- **GameErrorEvent**: Error reporting (error_message: str, error_type: str, severity: Literal["warning", "error", "critical"], recoverable: bool, context: Optional[Dict[str, Any]], error_code: Optional[str])
- **GameStateSnapshotEvent**: Full state synchronization (campaign_id: Optional[str], session_id: Optional[str], location: Dict[str, Any], party_members: List[Dict[str, Any]], active_quests: List[Dict[str, Any]], combat_state: Optional[Dict[str, Any]], pending_dice_requests: List[Dict[str, Any]], chat_history: List[Dict[str, Any]], reason: str)

#### Quest and Story Events
- **QuestUpdatedEvent**: Quest status changes (quest_id: str, quest_title: str, new_status: str, old_status: Optional[str], description_update: Optional[str])
- **ItemAddedEvent**: Inventory additions (character_id: str, character_name: str, item_name: str, quantity: int, item_description: Optional[str])

## 10. Service Layer Architecture

### 10.1 Campaign Service Operations
**CampaignService** operates on both template and instance models with clear separation, working directly with Pydantic model instances:

#### Template Operations
- **create_campaign**: Creates and saves CampaignTemplateModel instances
- **get_campaign**: Returns CampaignTemplateModel (not dict)
- **update_campaign**: Modifies existing CampaignTemplateModel
- **delete_campaign**: Removes CampaignTemplateModel
- **get_campaign_summary**: Provides CampaignTemplateModel metadata

#### Instance Operations
- **create_campaign_instance**: Creates CampaignInstanceModel from CampaignTemplateModel
- **start_campaign_from_template**: Returns GameStateModel instance (not dict)
- **start_campaign**: Backward compatibility method returns dict for API compatibility

#### Supporting Operations
- **get_all_campaigns**: Retrieves campaign metadata
- **_template_to_character_instance**: Converts CharacterTemplateModel to CharacterInstanceModel data

### 10.2 Complete Service Catalog

#### Core Game Services
- **CharacterService**: Character instance management, template combination, stat calculations
  - Methods: get_character_data, update_character_instance, combine_template_and_instance
  - Models: CharacterInstanceModel, CharacterTemplateModel
- **CombatService**: Combat state manipulation, turn management, combatant operations
  - Methods: start_combat, advance_turn, update_combatant_hp, add_combatant, remove_combatant
  - Models: CombatStateModel, CombatantModel
- **ChatService**: Message handling, history management
  - Methods: add_message, get_chat_history, clear_history
  - Models: ChatMessage, NarrativeAddedEvent
- **DiceService**: Roll processing, request management, result handling
  - Methods: process_dice_request, roll_dice, clear_requests
  - Models: DiceRequest, DiceRollResult
- **GameEventManager**: Event orchestration, handler coordination
  - Methods: handle_player_action, handle_dice_submission, handle_next_step
  - Models: BaseGameEvent and all event subclasses

#### Template Management Services
- **CharacterTemplateRepository**: CharacterTemplateModel persistence
  - Methods: save_template, get_template, get_all_templates, delete_template
  - Models: CharacterTemplateModel
- **CampaignTemplateRepository**: CampaignTemplateModel persistence
  - Methods: save_template, get_template, get_all_templates, delete_template
  - Models: CampaignTemplateModel

#### State Management Services
- **GameStateRepository**: GameStateModel persistence, migration logic, serialization handling
  - Methods: save_game_state, load_game_state, migrate_old_save_data
  - Models: GameStateModel
- **AIResponseProcessor**: AI output parsing, game state application, event generation
  - Methods: process_ai_response, apply_game_state_updates, handle_dice_requests
  - Models: AIResponse, GameStateUpdate, various event models

#### AI Integration Services
- **OpenAIService**: LLM communication, context preparation, response parsing
  - Methods: send_request, build_messages, parse_response
  - Models: AIResponse, ChatMessage
- **PromptBuilder**: Context construction from GameStateModel, template data integration
  - Methods: build_prompt, format_character_data, format_combat_state, format_location
  - Models: GameStateModel, CharacterInstanceModel, CharacterTemplateModel, CombatStateModel
- **AIServiceManager**: AI provider abstraction and configuration
  - Methods: get_ai_service, switch_provider, validate_response
  - Models: AIResponse

#### RAG System Services
- **RAGService**: Knowledge base querying, context enhancement
  - Methods: query_knowledge, build_context, search_rules
  - Models: RAGResults, KnowledgeResult, QueryRequest
- **KnowledgeBaseManager**: Knowledge base loading and indexing
  - Methods: load_knowledge_bases, build_indexes, update_embeddings
  - Models: KnowledgeResult
- **QueryEngine**: Query processing and retrieval
  - Methods: execute_query, rank_results, filter_by_relevance
  - Models: QueryRequest, RAGResults
- **RAGContextBuilder**: Context preparation for AI prompts
  - Methods: build_rag_context, format_knowledge_results
  - Models: RAGResults, KnowledgeResult

#### Support Services
- **TTS Integration**: Audio generation, voice synthesis
  - Methods: synthesize_speech, get_available_voices, cache_audio
  - Models: NarrativeAddedEvent (for audio_path)

## 11. Data Persistence Architecture

### 11.1 File Structure and Model Mapping
#### Character Templates (`saves/character_templates/`)
- **Individual files**: JSON serialization of CharacterTemplateModel instances
- **Index file**: Metadata collection with template discovery

#### Campaign Templates (`saves/campaign_templates/`)
- **Individual files**: JSON serialization of CampaignTemplateModel instances
- **Index file**: Metadata collection with template discovery

#### Active Campaigns (`saves/campaigns/{campaign_id}/`)
- **campaign.json**: CampaignInstanceModel serialization (high-level campaign state)
- **active_game_state.json**: GameStateModel serialization (complete runtime state)
- **event_log.json**: Event history for debugging and replay

#### Configuration Data (`saves/d5e_data/`)
- **classes.json**: D&D class definitions for character creation
- **races.json**: D&D race definitions for character creation

### 11.2 Repository Pattern Implementation
#### Responsibilities
- **Serialization**: model_dump() with proper datetime handling
- **Deserialization**: Model.model_validate(data) with validation
- **Migration**: Backward compatibility for existing save files
- **Indexing**: Metadata management for efficient discovery
- **Validation**: Data integrity checks during persistence operations
- **Type Safety**: All repository methods return Pydantic model instances, not dicts

## 12. Frontend Integration Architecture

### 12.1 TypeScript Type System
#### Auto-Generation Process
- **Source**: app/models/*.py Pydantic models
- **Generator**: scripts/generate_typescript.py conversion script
- **Output**: frontend/src/types/unified.ts TypeScript interfaces
- **Integration**: Direct import in Vue components and Pinia stores

#### Type Coverage
- **Complete Model Mirroring**: All backend models have TypeScript equivalents
- **Event Type Safety**: All event models typed for SSE handling
- **API Contract Enforcement**: Request/response type validation

### 12.2 Pinia Store Integration
#### Store Organization
- **gameStore**: GameStateModel state management
- **chatStore**: NarrativeAddedEvent collection management
- **combatStore**: CombatStateModel and event handling
- **diceStore**: DiceRequest and result management
- **partyStore**: CharacterInstanceModel collection
- **campaignStore**: CampaignTemplateModel and CampaignInstanceModel operations
- **configStore**: Application configuration
- **uiStore**: UI state management

#### Event Handling
- **eventRouter.js**: SSE event distribution to appropriate stores
- **Type-Safe Updates**: Unified event models ensure consistent state updates
- **Real-Time Synchronization**: Automatic UI updates via reactive store properties

### 12.3 Component Architecture
#### Type Safety Implementation
- **Script Setup**: `<script setup lang="ts">` for compile-time type checking
- **Props Typing**: Strong typing for component interfaces using unified types
- **Store Integration**: Typed store access with auto-completion
- **Event Emission**: Type-safe event handling

## 13. Comprehensive Data Flow Patterns

### 13.1 Campaign Management Flow
#### Template Creation
1. Frontend component validates CampaignTemplateModel fields
2. API route receives typed request body
3. CampaignService.create_campaign processes CampaignTemplateModel
4. CampaignRepository persists via model_dump()
5. Response returns serialized CampaignTemplateModel
6. Frontend store updates with typed campaign data

#### Instance Creation and Game Start
1. Frontend selects CampaignTemplateModel and character IDs
2. CampaignService.start_campaign_from_template called
3. CampaignService.create_campaign_instance creates CampaignInstanceModel
4. Character templates converted to CharacterInstanceModel data
5. GameStateModel initialized with all unified model components
6. GameStateRepository persists complete state
7. Initial events generated and queued
8. SSE streams typed events to frontend
9. Multiple stores update from typed event data

#### Save/Load Operations
1. GameStateRepository.save_game_state serializes GameStateModel
2. All nested unified models serialize via model_dump()
3. JSON persistence maintains complete type fidelity
4. Load operation deserializes with full validation
5. Migration logic handles backward compatibility
6. Restored state maintains all type relationships

### 13.2 Combat Management Flow
#### Combat Initiation
1. AI service requests combat start via structured response
2. AIResponseProcessor parses combat instruction
3. CombatService creates CombatantModel instances
4. CombatStateModel updated within GameStateModel
5. CombatStartedEvent generated with typed combatant data
6. Event queued and streamed via SSE
7. Frontend combatStore updates with typed combat state
8. UI components render combat interface

#### Turn Management
1. CombatService advances turn using CombatStateModel methods
2. TurnAdvancedEvent created with new combatant data
3. Event includes round progression and player status
4. Frontend receives typed event data
5. Combat UI updates automatically via reactive stores
6. Player/NPC-specific interfaces activated based on event data

### 13.3 Character Management Flow
#### Template to Instance Conversion
1. CharacterTemplateModel loaded from repository
2. Character factory calculates derived stats (HP, AC, etc.)
3. CharacterInstanceModel created with template_id reference
4. Instance added to GameStateModel.party
5. Services access full character data by combining instance + template
6. Character updates modify instance while preserving template

#### Character State Updates
1. Game events modify CharacterInstanceModel fields
2. PartyMemberUpdatedEvent generated with change details
3. GameStateRepository persists updated state
4. SSE streams typed update event
5. Frontend partyStore updates specific character
6. Character display components re-render automatically

### 13.4 Event System Flow
#### Event Generation
1. Service layer operations create typed event models
2. Events inherit from BaseGameEvent with automatic sequencing
3. Correlation IDs link related events
4. EventQueue stores typed event instances
5. SSE route serializes events for streaming

#### Event Processing
1. Frontend eventService receives SSE data
2. eventRouter.js distributes by event_type
3. Appropriate Pinia stores handle typed events
4. Store mutations update reactive state
5. UI components automatically re-render
6. Type safety maintained throughout flow

## 14. Integration Benefits

### 14.1 Development Benefits
- **Type Safety**: Compile-time error detection in both Python and TypeScript
- **Consistency**: Identical data structures across all system layers
- **Maintainability**: Single-source updates propagate systematically
- **Developer Experience**: IDE auto-completion and type checking
- **Testability**: Well-defined interfaces for comprehensive testing

### 14.2 Runtime Benefits
- **Data Integrity**: Pydantic validation ensures data consistency
- **Performance**: Efficient serialization with direct model mapping
- **Debugging**: Clear data flow with typed interfaces
- **Error Handling**: Structured error types with context
- **Scalability**: Clean separation enables component scaling

### 14.3 Operational Benefits
- **Migration Support**: Automatic data format upgrades
- **Backup Reliability**: Type-safe persistence guarantees
- **API Contracts**: Clear interfaces between system components
- **Event Replay**: Structured event logs for debugging
- **Configuration Validation**: Type-safe application configuration

## 15. Future Architecture Considerations

### 15.1 Database Integration
- **ORM Mapping**: Unified models can map to SQLAlchemy models
- **Migration Path**: JSON-to-database transition with preserved types
- **Query Optimization**: Type-safe database queries
- **Relationship Management**: Foreign key mapping from unified model relationships

### 15.2 API Evolution
- **OpenAPI Generation**: Automatic API documentation from Pydantic models
- **Version Management**: Structured API versioning with model evolution
- **Validation Middleware**: Automatic request/response validation
- **Contract Testing**: Type-based API contract verification

### 15.3 Configuration Management
- **Pydantic Configuration**: Type-safe application configuration
- **Environment Validation**: Structured environment variable handling
- **Feature Flags**: Type-safe feature toggle management
- **Deployment Configuration**: Structured deployment parameter validation

This unified architecture provides a robust, type-safe, and maintainable foundation that scales with application complexity while maintaining development velocity and operational reliability.

## 15. Design Decisions

### Why JSON Files?
- **Simplicity**: No database setup required
- **Portability**: Easy to backup, share, and version control
- **Debugging**: Human-readable for troubleshooting
- **Migration**: Easy to convert to database later

### Why Vue.js 3?
- **Modern**: Composition API for better code organization
- **Performance**: Reactivity system optimized for real-time updates
- **Ecosystem**: Rich component library and tooling
- **Learning Curve**: Approachable for new developers

### Why Structured AI Responses?
- **Reliability**: Eliminates parsing errors and ambiguity
- **Features**: Enables complex game mechanics
- **Debugging**: Easy to validate and troubleshoot
- **Flexibility**: Can add new response types without breaking changes

## 16. Future Enhancements

### Planned Features
- **Visual Maps**: AI-generated dungeon maps and battle grids
- **Voice Chat**: Voice conversation with AI GM
- **Campaign Import**: Support for published adventures
- **Multiplayer**: Real-time collaboration for groups
- **Custom Rules**: Support for homebrew rules and content

### Technical Improvements
- **Database Migration**: Move from JSON to SQLite/PostgreSQL
- **Real-time Sync**: WebSocket integration for live updates
- **Mobile Support**: React Native or Progressive Web App
- **AI Fine-tuning**: Custom models trained specifically for D&D

## 17. Implementation Status

### 17.1 Completed Components
- **Unified Models**: All Pydantic models defined in `app/models/*.py`
- **Repository Layer**: Character and campaign template repositories using unified models
- **Service Layer**: Campaign, character, and combat services updated for unified types
- **Event System**: All events migrated to typed BaseGameEvent hierarchy
- **TypeScript Generation**: Script generates frontend types from Pydantic models
- **API Routes**: Updated to use unified models for request/response
- **Data Persistence**: JSON serialization with backward compatibility

### 17.2 Testing Infrastructure
- **Unit Tests**: Coverage for all model validations and conversions
- **Integration Tests**: End-to-end flow from templates to gameplay
- **Test Isolation**: Temporary directories prevent test pollution
- **Golden Tests**: Reference tests ensure consistent behavior

### 17.3 Migration Support
- **Backward Compatibility**: Old save formats automatically migrated
- **Field Mapping**: Legacy field names mapped to new structure
- **Data Validation**: Migration includes validation and correction
- **Version Tracking**: Save files include version information

This implementation represents a complete transformation from the previous dictionary-based approach to a fully type-safe architecture across all system components.
