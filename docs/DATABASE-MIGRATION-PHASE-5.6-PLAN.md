# Phase 5.6: Type System Refactoring & Content Service Integration

## Revised Analysis Summary

After starting implementation, we discovered a more fundamental issue: the entire character and campaign system should use ContentService for ALL D&D 5e data access, not just maintain separate simplified models. This represents a major architectural improvement.

### Key Discoveries

1. **Duplicate Models Are Symptoms**: The `D5EClassModel` and `ArmorModel` in `app/models/utils.py` are symptoms of a larger problem - the system is loading D&D 5e data from JSON files instead of using the content database.

2. **Content Service Is Underutilized**: We have a fully functional ContentService with database-backed D&D 5e data, but character creation still uses JSON files.

3. **Content Packs Can't Work Properly**: Without using ContentService, user-created content packs can't influence character creation options.

## Revised Implementation Plan

### Task 5.6.1: Remove Duplicate D&D 5e Models ✅ COMPLETE

**What we did:**
- Removed `D5EClassModel` and `ArmorModel` from `app/models/utils.py`
- These were simplified models that duplicated functionality from `app/content/schemas`

### Task 5.6.2: Refactor CampaignService ✅ COMPLETE

**What we did:**
- Updated CampaignService to accept ContentService as a dependency
- Removed `_load_d5e_data()` and `_load_basic_armor_data()` methods
- Updated ServiceContainer to inject ContentService into CampaignService

### Task 5.6.3: Update CharacterFactory ✅ COMPLETE

**What we did:**
- Refactored CharacterFactory to use ContentService for all D&D 5e data
- Added content_pack_priority support throughout
- Updated armor and hit point calculations to use content from database

### Task 5.6.4: Fix Test Failures (NEW - In Progress)

**What needs to be done:**
- Update test files that import the removed models
- Mock ContentService in unit tests
- Ensure all tests pass with the new architecture

### Task 5.6.5: Expand Content Service Integration

**What needs to be done:**

1. **Update Character Templates**
   - Change character templates to store content IDs instead of names
   - Add methods to ContentService for looking up content by ID
   - Ensure backward compatibility or provide migration

2. **Add Missing ContentService Methods**
   ```python
   # Methods needed in ContentService:
   def get_race_by_id(self, race_id: str, content_pack_priority: List[str]) -> Optional[D5eRace]
   def get_subrace_by_id(self, subrace_id: str, content_pack_priority: List[str]) -> Optional[D5eSubrace]
   def get_background_by_id(self, background_id: str, content_pack_priority: List[str]) -> Optional[D5eBackground]
   def get_alignment_by_id(self, alignment_id: str, content_pack_priority: List[str]) -> Optional[D5eAlignment]
   def get_subclass_by_id(self, subclass_id: str, content_pack_priority: List[str]) -> Optional[D5eSubclass]
   ```

3. **Update Character Creation Flow**
   - Modify character creation APIs to accept content IDs
   - Update frontend to fetch available options from content packs
   - Ensure content pack priority is respected

### Task 5.6.6: Document Backend Architecture

**What needs to be done:**

Create `app/models/README.md`:
```markdown
# Backend Model Architecture

## Model Categories

### Runtime Models (`app/models/`)
These models represent the dynamic state of the game:
- **Character Models**: Templates and instances for player characters
- **Campaign Models**: Campaign configuration and runtime state
- **Combat Models**: Combat state and turn management
- **Game State**: Overall game state including location, quests, NPCs
- **Events**: Real-time event models for SSE updates

### Content Schemas (`app/content/schemas/`)
These models represent static D&D 5e game content:
- **Character Options**: Classes, races, backgrounds, etc.
- **Game Mechanics**: Spells, equipment, conditions, etc.
- **Rules**: Ability scores, skills, proficiencies, etc.

## Key Principles

1. **Separation of Concerns**: Runtime state is separate from game content
2. **Single Source of Truth**: All D&D 5e data comes from ContentService
3. **Content Pack Support**: User content can override or extend base content
4. **Type Safety**: Use Pydantic models throughout, no TypedDict

## DTO Pattern

`CombinedCharacterModel` is a DTO (Data Transfer Object) that merges:
- Static template data (from CharacterTemplateModel)
- Dynamic instance data (from CharacterInstanceModel)
- Computed values (AC, proficiency bonus, etc.)

This provides a convenient, denormalized view for the frontend.
```

### Task 5.6.6: Add D&D 5e Content Validation (NEW - Critical)

**Revised Approach**: Instead of changing models to use IDs, we'll keep string references but add comprehensive validation to ensure all D&D 5e content references are valid.

**What needs to be done:**

1. **Add Validators to All D&D Reference Fields**

   The following models and fields need validators:

   **CharacterTemplateModel** (`app/models/character.py`):
   - `race: str` → Validate against available races
   - `subrace: Optional[str]` → Validate against subraces for the chosen race
   - `char_class: str` → Validate against available classes
   - `subclass: Optional[str]` → Validate against subclasses for the chosen class
   - `background: str` → Validate against available backgrounds
   - `alignment: str` → Validate against available alignments
   - `languages: List[str]` → Validate each language exists
   - `spells_known: List[str]` → Validate each spell exists and is valid for class
   - `cantrips_known: List[str]` → Validate each cantrip exists and is valid for class

   **CharacterInstanceModel** (`app/models/character.py`):
   - `conditions: List[str]` → Validate against available conditions

   **CampaignTemplateModel** (`app/models/campaign.py`):
   - `allowed_races: Optional[List[str]]` → Validate each race exists
   - `allowed_classes: Optional[List[str]]` → Validate each class exists

   **ItemModel** (`app/models/utils.py`):
   - `name: str` → Optionally validate against equipment database

   **ProficienciesModel** (`app/models/utils.py`):
   - `armor: List[str]` → Validate against armor proficiency types
   - `weapons: List[str]` → Validate against weapon proficiency types
   - `tools: List[str]` → Validate against tool types
   - `skills: List[str]` → Validate against skill list

   **AttackModel** (`app/models/combat.py`):
   - `damage_type: Optional[str]` → Validate against damage types

   **CombatantModel** (`app/models/combat.py`):
   - `conditions: List[str]` → Validate against conditions
   - `conditions_immune: Optional[List[str]]` → Validate against conditions
   - `resistances: Optional[List[str]]` → Validate against damage types
   - `vulnerabilities: Optional[List[str]]` → Validate against damage types

2. **Create Validation Service**
   ```python
   # app/domain/validators/content_validator.py
   class ContentValidator:
       def __init__(self, content_service: ContentService):
           self.content_service = content_service
           self._cache_valid_values()
       
       def validate_race(self, race: str) -> str:
           """Validate and normalize race name"""
           # Check cache, normalize, return validated value
       
       def validate_class(self, class_name: str) -> str:
           """Validate and normalize class name"""
           # Similar for all other content types
   ```

3. **Add Helper Methods to Models**
   ```python
   class CharacterTemplateModel:
       def get_race_data(self, content_service: ContentService) -> Optional[D5eRace]:
           """Get full race data when needed"""
           return content_service.get_race_by_name(self.race)
       
       def get_class_data(self, content_service: ContentService) -> Optional[D5eClass]:
           """Get full class data when needed"""
           return content_service.get_class_by_name(self.char_class)
   ```

4. **Generate TypeScript Enums for Frontend**
   ```typescript
   // Generated from database
   export enum Race {
     DRAGONBORN = "Dragonborn",
     DWARF = "Dwarf",
     ELF = "Elf",
     // ... etc
   }
   
   export enum CharacterClass {
     BARBARIAN = "Barbarian",
     BARD = "Bard",
     CLERIC = "Cleric",
     // ... etc
   }
   ```

**Benefits of This Approach:**
- ✅ Maintains backward compatibility
- ✅ No complex migrations needed
- ✅ Simple, maintainable code
- ✅ Validation ensures data integrity
- ✅ Frontend gets type safety through enums
- ✅ Content packs still work naturally

### Task 5.6.7: Enhance TypeScript Generation (Previously 5.6.6)

**What needs to be done:**

1. **Add Content Type Constants**
   ```typescript
   // Generated from backend
   export const CONTENT_TYPES = {
     SPELLS: "spells",
     MONSTERS: "monsters",
     CLASSES: "classes",
     // ... etc
   } as const;
   ```

2. **Improve Organization**
   - Group runtime models separately from content schemas
   - Add section headers in generated file
   - Include generation metadata

### Task 5.6.8: Remove ALL JSON Loading (Previously 5.6.7)

**What needs to be done:**

1. **Find All JSON Loading Code**
   ```bash
   grep -r "json.load\|\.json" app/ --include="*.py"
   ```

2. **Remove or Refactor**
   - Remove any code that loads D&D 5e data from JSON
   - Update to use ContentService instead
   - Remove JSON data files after confirming they're not needed

### Task 5.6.9: Update Frontend for Content Integration (Previously 5.6.8)

**What needs to be done:**

1. **Character Creation UI**
   - Fetch available races, classes, etc. from content API
   - Respect content pack priority in option lists
   - Show which content pack each option comes from

2. **API Endpoints**
   - Add endpoints to fetch available character options
   - Include content pack filtering
   - Return both ID and display information

### Task 5.6.10: Frontend State Management Cleanup (Previously 5.6.9)

**What needs to be done:**

1. **Remove Duplicate State**
   - Remove chatHistory, party, combatState, diceRequests from gameStore
   - Update components to use specialized stores

2. **Document Store Responsibilities**
   - gameStore: Campaign-level state only
   - chatStore: Chat messages and history
   - combatStore: Combat state and turn management
   - partyStore: Party composition and character state
   - contentStore: Available content and content packs

## Benefits of This Approach

1. **Consistency**: All D&D 5e data comes from one source
2. **Extensibility**: User content automatically available everywhere
3. **Performance**: Database queries faster than JSON parsing
4. **Maintainability**: Single code path for all content access
5. **Type Safety**: Strong types throughout the system

## Migration Strategy

1. **Backward Compatibility**: Ensure existing saves continue to work
2. **Gradual Migration**: Can be done incrementally by system
3. **Testing**: Comprehensive tests at each step
4. **Documentation**: Update all docs to reflect new architecture

## Success Criteria

- [ ] All tests pass with 0 errors
- [ ] No JSON files loaded for D&D 5e data
- [ ] Character creation uses content packs
- [ ] Type safety maintained throughout
- [ ] Performance equal or better than before
- [ ] Clear separation between runtime and content models