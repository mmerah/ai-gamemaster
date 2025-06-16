# Backend Model Architecture

## Overview

This document explains the organization and purpose of models in the AI Gamemaster backend. The architecture follows a clear separation between runtime models (dynamic game state) and content schemas (static D&D 5e data).

## Model Categories

### Runtime Models (`app/models/`)

These models represent the dynamic state of the game and are stored/managed during gameplay:

#### Character Models (`character.py`)
- **CharacterTemplateModel**: Defines character blueprints with base stats, equipment, and traits
- **CharacterInstanceModel**: Active character state including HP, conditions, inventory changes
- **CombinedCharacterModel**: DTO that merges template and instance data for frontend consumption
- **CharacterModifierDataModel**: Transient data for calculating modifiers during rolls

#### Campaign Models (`campaign.py`)
- **CampaignTemplateModel**: Campaign blueprint with settings and initial configuration
- **CampaignInstanceModel**: Active campaign state including current location and session data
- **CombinedCampaignModel**: DTO merging template and instance for complete campaign info

#### Combat Models (`combat.py`)
- **CombatStateModel**: Current combat state including turn order and round tracking
- **CombatantModel**: Individual combatant data with initiative and status
- **CombatActionModel**: Actions taken during combat
- **CombatTurnModel**: Single turn information including actions and results

#### Game State Models (`game_state.py`)
- **GameStateModel**: Core game state including location, NPCs, quests, and narrative
- **GameActionModel**: Player actions and their context
- **LocationModel**: Current location details and description
- **NPCModel**: Non-player character information
- **QuestModel**: Active quest tracking

#### Event Models (`events.py`)
- Real-time event models for SSE (Server-Sent Events) updates
- Includes game state updates, chat messages, dice rolls, and combat events

#### Other Models
- **dice.py**: Dice roll requests, results, and submissions
- **config.py**: Service configuration models
- **utils.py**: Basic structures (items, traits, proficiencies) and utility models
- **rag.py**: RAG system and knowledge base models
- **updates.py**: Flattened update models for efficient frontend updates

### Content Schemas (`app/content/schemas/`)

These models represent static D&D 5e game content loaded from the database:

#### Character Creation Options
- **classes.py**: Character classes (Fighter, Wizard, etc.)
- **races.py**: Character races (Human, Elf, etc.)
- **backgrounds.py**: Character backgrounds (Soldier, Scholar, etc.)
- **alignments.py**: Alignment options (Lawful Good, Chaotic Neutral, etc.)
- **subclasses.py**: Class specializations
- **subraces.py**: Race variants

#### Game Mechanics
- **spells.py**: Spell definitions and properties
- **equipment.py**: Weapons, armor, and gear
- **conditions.py**: Status conditions (Poisoned, Stunned, etc.)
- **abilities.py**: Ability scores and modifiers
- **skills.py**: Skill definitions and associations
- **proficiencies.py**: Proficiency types and categories

#### Rules and References
- **rules.py**: Game rules and mechanics
- **traits.py**: Racial and class traits
- **features.py**: Class features by level
- **languages.py**: Available languages
- **damage_types.py**: Damage type definitions

## Key Principles

### 1. Separation of Concerns
- **Runtime state** (what changes during play) is separate from **game content** (D&D 5e rules and data)
- Runtime models live in `app/models/`
- Content schemas live in `app/content/schemas/`

### 2. Single Source of Truth
- All D&D 5e data comes from the ContentService
- No hardcoded game data in runtime models
- Content can be extended via content packs

### 3. Content Pack Support
- User-created content can override or extend base D&D 5e content
- Content pack priority determines which version of content is used
- All content access respects the campaign's content pack configuration

### 4. Type Safety
- All models use Pydantic for validation and serialization
- No use of TypedDict or Dict[str, Any] for domain models
- TypeScript interfaces are generated from Pydantic models

## DTO Pattern

### CombinedCharacterModel

This DTO (Data Transfer Object) provides a convenient, denormalized view for the frontend by merging:
- Static template data (from CharacterTemplateModel)
- Dynamic instance data (from CharacterInstanceModel)  
- Computed values (AC, proficiency bonus, spell slots, etc.)

Example usage:
```python
# Backend creates the DTO
template = character_template_repo.get(template_id)
instance = character_instance_repo.get(instance_id)
combined = create_combined_character(template, instance)

# Frontend receives complete character data
# No need to merge template/instance on client side
```

### CombinedCampaignModel

Similar pattern for campaigns, merging:
- Campaign template configuration
- Campaign instance state
- Runtime settings and overrides

## Model Relationships

```
CampaignTemplate
    ├── CharacterTemplates[]
    └── Settings

CampaignInstance
    ├── CharacterInstances[]
    ├── GameState
    └── ContentPackPriority[]

CharacterTemplate (references content by name/ID)
    ├── Class (from ContentService)
    ├── Race (from ContentService)
    ├── Background (from ContentService)
    └── Equipment[] (from ContentService)

CharacterInstance
    ├── Current HP/Conditions
    ├── Inventory Changes
    └── Experience/Level Ups
```

## Best Practices

### Creating New Models

1. **Determine the category**: Is it runtime state or static content?
2. **Choose the right location**: `app/models/` or `app/content/schemas/`
3. **Use Pydantic BaseModel**: Inherit from appropriate base class
4. **Add validation**: Use Pydantic validators for business rules
5. **Generate TypeScript**: Run `python scripts/dev/generate_ts.py`

### Naming Conventions

- Models end with `Model` suffix (e.g., `CharacterTemplateModel`)
- Schemas use D5e prefix (e.g., `D5eClass`, `D5eSpell`)
- DTOs explicitly state their purpose (e.g., `CombinedCharacterModel`)

### Version Management

When updating models that affect the API:
1. Consider backward compatibility
2. Use Optional fields for new additions
3. Provide defaults for new required fields
4. Document breaking changes in migration notes

## Examples

### Accessing D&D 5e Content

```python
# WRONG - Don't hardcode content
hit_die = 10  # Fighter hit die

# CORRECT - Use ContentService
class_data = content_service.get_class_by_name(
    "Fighter", 
    content_pack_priority=campaign.content_pack_priority
)
hit_die = class_data.hit_die if class_data else 8
```

### Creating Runtime Models

```python
# Character instance for active game
character = CharacterInstanceModel(
    id=generate_id(),
    template_id=template.id,
    campaign_id=campaign.id,
    hit_points=calculated_hp,
    max_hit_points=calculated_hp,
    # ... other runtime state
)
```

### Working with Content Packs

```python
# Respect content pack priority
spell = content_service.get_spell_by_name(
    "Fireball",
    content_pack_priority=["my-homebrew", "dnd_5e_srd"]
)
# Will return homebrew version if it exists, otherwise SRD version
```