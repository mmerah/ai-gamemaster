# AI Game Master - Technical Concept & Design

This document outlines the core concepts, architecture decisions, and technical implementation details for the AI Game Master project. Most things in this document are subject to changes. Most things are also work-in-progress.

## Project Vision

Create an open-source web application that acts as an AI-powered Game Master for D&D 5e, providing an immersive single-player or group experience with intelligent storytelling, combat management, and character progression. This is just a "for fun" project, at least for now.

## Core Architecture

### Backend (Python Flask)
- **Service-oriented architecture** with dependency injection
- **Pydantic models** for all data structures
- **JSON file persistence** for simplicity and portability
- **Modular AI providers** supporting both local and cloud models
- **RAG** for knowledge bases and intelligent context

### Frontend (Vue.js 3)
- **Component-based architecture** for reusability
- **Pinia state management** for reactive game state
- **Tailwind CSS** with custom D&D theming

### AI Integration
- **Structured JSON responses** using function calling or instructor library
- **Provider abstraction** allowing easy switching between AI services
- **Error recovery** with retry mechanisms for failed requests

## Game Interface Design

### Main Game Window Layout
```
┌─────────────────────────────────────────────────────────────┐
│                        AI Game Master                      │
├───────────────┬─────────────────────────┬───────────────────┤
│               │                         │                   │
│   Party       │      Chat History       │   Map/Visual      │
│   Panel       │   (GM + Player msgs)    │   (Placeholder)   │
│               │                         │                   │
│ • Character 1 │ GM: "You enter a dark..." │  [ASCII Map or   │
│ • Character 2 │ You: "I check for traps" │   AI-generated    │
│ • Character 3 │ GM: "Roll perception"    │   image]          │
│               │                         │                   │
├───────────────┴─────────────────────────┼───────────────────┤
│              Input Controls              │   Dice Requests   │
│  [Text Input] [Dice] [Quick Actions]     │   • Perception    │
└─────────────────────────────────────────┴───────────────────┘
```

### Campaign Management
- **Campaign Browser**: List existing campaigns, create new ones
- **Character Templates**: Pre-built characters with full D&D 5e stats
- **Party Selection**: Choose which characters to include
- **GM/Player Control**: Assign character control (AI vs player)

## Data Models

### Core Game State
```python
class GameState:
    campaign_id: str
    current_location: Location
    party: List[Character]
    chat_history: List[Message]
    combat_state: Optional[CombatState]
    game_flags: Dict[str, Any]
    timestamp: datetime
```

### Character Data
```python
class Character:
    # Basic Info
    name: str
    race: str
    character_class: str
    level: int
    
    # D&D 5e Stats
    ability_scores: AbilityScores
    skills: Dict[str, int]
    saving_throws: Dict[str, int]
    
    # Game State
    current_hp: int
    max_hp: int
    conditions: List[str]
    spell_slots: Dict[int, int]
    
    # Roleplay
    personality_traits: List[str]
    ideals: str
    bonds: str
    flaws: str
```

### AI Response Schema
```python
class GMResponse:
    narrative: str
    dice_requests: List[DiceRequest]
    location_update: Optional[LocationUpdate]
    game_state_updates: List[GameStateUpdate]
    gm_notes: Optional[str]  # Private notes for context
```

## AI Integration Strategy

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

## Game Mechanics

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

## Technical Implementation

### File Organization
```
saves/
├── campaigns/
│   ├── campaigns.json           # Campaign metadata
│   └── {campaign_id}/
│       ├── campaign.json        # Campaign definition
│       ├── game_state.json      # Current game state
│       └── chat_history.json    # Message history
├── character_templates/
│   ├── templates.json           # Template metadata  
│   └── {template_id}.json       # Individual templates
└── d5e_data/
    ├── races.json               # D&D 5e race data
    ├── classes.json             # D&D 5e class data
    └── spells.json              # Spell database
```

### Error Handling
- **AI Response Validation**: JSON schema validation
- **Retry Mechanisms**: Automatic retry for failed AI requests
- **Graceful Degradation**: Fallback to simpler responses
- **User Recovery**: Manual retry buttons, state restoration

### Performance Considerations
- **Lazy Loading**: Load character/campaign data as needed
- **Caching**: Cache frequently accessed D&D data
- **Streaming**: Real-time message updates
- **Optimization**: Minimize AI context window usage

## Development Workflow

### Local Development Setup
```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py

# Frontend  
cd frontend
npm install
npm run dev
```

### Testing Strategy
- **Unit Tests**: Core game logic, character calculations
- **Integration Tests**: AI response processing, data persistence
- **E2E Tests**: Full game scenarios with browser automation
- **AI Testing**: Validate responses against various models

### Deployment Options
- **Single Binary**: Package everything for easy distribution
- **Docker**: Containerized deployment
- **Cloud**: Deploy backend to cloud, serve frontend via CDN
- **Local**: Desktop application with embedded browser

## Future Enhancements

### Planned Features
- **Visual Maps**: AI-generated dungeon maps and battle grids
- **Voice Chat**: Real-time voice conversation with AI GM
- **Campaign Import**: Support for published adventures
- **Multiplayer**: Real-time collaboration for groups
- **Custom Rules**: Support for homebrew rules and content

### Technical Improvements
- **Database Migration**: Move from JSON to SQLite/PostgreSQL
- **Real-time Sync**: WebSocket integration for live updates
- **Mobile Support**: React Native or Progressive Web App
- **AI Fine-tuning**: Custom models trained specifically for D&D

## Design Decisions

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

---

*This document evolves with the project. Last updated: May 2025*
