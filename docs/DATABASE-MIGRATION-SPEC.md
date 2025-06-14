# Database Migration Implementation Specification

## Document Information
- **Version**: 1.0
- **Date**: January 2025
- **Project**: AI Game Master - Database Migration
- **Scope**: Migration from JSON-based data storage to hybrid database architecture

## 1. Executive Summary

### 1.1 Migration Overview
This specification details the migration from the current JSON file-based data storage to a hybrid database architecture. The migration targets **ruleset data only** (D&D 5e content, custom user content, lore), while preserving the existing JSON-based save system for game states, characters, and campaigns.

### 1.2 Key Objectives
- **Performance**: Eliminate 30-60 second startup times caused by loading 25 large JSON files
- **Scalability**: Enable efficient querying and indexing of D&D content
- **Modularity**: Maintain flexible "content pack" system for custom rulesets
- **Type Safety**: Preserve existing Pydantic model architecture
- **RAG Enhancement**: Optimize semantic search for AI game master context

### 1.3 Scope Boundaries
**IN SCOPE:**
- Migration of 25 5e-database JSON files to database
- Custom user content management system
- Lore system database integration
- RAG system optimization with vector database
- Content pack management architecture

**OUT OF SCOPE:**
- Game save system (remains JSON-based)
- Character/campaign template storage (remains JSON-based)
- Frontend UI changes (except Content Manager)
- Authentication/user management system

## 2. Current Architecture Analysis

### 2.1 Data Sources Overview
```
Current Data Flow:
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   5e-database/      │    │   knowledge/lore/   │    │   saves/            │
│   (25 JSON files)   │────│   (lore content)    │────│   (game states)     │
│   45,653+ lines     │    │   lores.json index  │    │   JSON persistence  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Python Backend Services                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Character Svc   │  │ RAG Service     │  │ Game State Repository       │  │
│  │ (uses D5e data) │  │ (semantic srch) │  │ (JSON read/write)           │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Performance Issues
- **Startup Time**: 30-60 seconds loading and parsing 25 JSON files
- **Memory Usage**: 45,000+ items loaded into RAM per application instance
- **Test Suite**: Execution time increased from 30s to 1 minute
- **RAG System**: Inefficient text search across large JSON structures

### 2.3 Current File Structure
```
knowledge/
├── 5e-database/src/2014/
│   ├── 5e-SRD-Spells.json (45,653+ lines)
│   ├── 5e-SRD-Monsters.json
│   ├── 5e-SRD-Equipment.json
│   └── ... (22 more files)
├── lore/
│   ├── generic_fantasy_lore.json
│   └── custom_lore.json
└── lores.json (index file)

saves/ (UNCHANGED - remains JSON)
├── campaign_templates/
├── campaigns/
└── character_templates/
```

## 3. Target Architecture

### 3.1 Hybrid Database Architecture
```
Target Architecture:
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Primary Database  │    │   Vector Database   │    │   JSON Files        │
│   (PostgreSQL)      │    │   (ChromaDB)        │    │   (saves/)          │
│   - Structured data │────│   - Embeddings     │    │   - Game states     │
│   - Source tracking │    │   - Semantic search │    │   - Campaigns       │
│   - Relationships   │    │   - RAG queries     │    │   - Characters      │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Enhanced Repository Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ D5eRepository   │  │ RAGRepository   │  │ SaveRepository              │  │
│  │ (SQL queries)   │  │ (vector search) │  │ (JSON files - unchanged)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Content Pack System
```
Content Pack Hierarchy:
Campaign Instance
    ├── active_content_packs: ["user_homebrew_123", "dnd_5e_srd"]
    ├── Spell "Fireball" lookup:
    │   ├── 1. Check user_homebrew_123 → Found custom version
    │   └── 2. Return custom "Fireball" (skip SRD version)
    │
    └── Spell "Magic Missile" lookup:
        ├── 1. Check user_homebrew_123 → Not found
        └── 2. Check dnd_5e_srd → Found SRD version
```

## 4. Database Options Analysis

### 4.1 Primary Database Options

#### 4.1.1 PostgreSQL + pgvector (RECOMMENDED FOR PRODUCTION)
```yaml
Technology: PostgreSQL 15+ with pgvector extension
Python Library: psycopg2-binary, SQLAlchemy
```

**Pros:**
- Full ACID compliance for data integrity
- JSONB support for complex D&D data structures (spell components, monster actions)
- Built-in vector support via pgvector extension
- Excellent performance with proper indexing
- Mature ecosystem and tooling
- Horizontal scaling capabilities

**Cons:**
- Requires separate server process
- More complex setup than SQLite
- Overkill for single-user deployments

**Use Cases:**
- Production deployments
- Multi-user scenarios
- High-performance requirements
- Future horizontal scaling

**Implementation Requirements:**
```python
# requirements.txt additions
psycopg2-binary==2.9.7
sqlalchemy==2.0.20
alembic==1.12.0
pgvector==0.2.3
```

#### 4.1.2 SQLite (RECOMMENDED FOR DEVELOPMENT)
```yaml
Technology: SQLite 3.38+
Python Library: sqlite3 (built-in), SQLAlchemy
```

**Pros:**
- Zero configuration required
- File-based (portable, easy backup)
- Built into Python standard library
- Perfect for development and testing
- Can migrate to PostgreSQL later with minimal code changes

**Cons:**
- Limited concurrent write performance
- No built-in vector support
- Fewer advanced features than PostgreSQL

**Use Cases:**
- Development environment
- Single-user deployments
- Proof of concept
- Local testing

**Implementation Requirements:**
```python
# No additional dependencies needed
# Uses Python built-in sqlite3 module
```

#### 4.1.3 MongoDB (ALTERNATIVE OPTION)
```yaml
Technology: MongoDB 6.0+
Python Library: pymongo, motor (async)
```

**Pros:**
- Schema-less design fits D&D's varied data structures
- Direct mapping from Pydantic models to documents
- Excellent performance for document-based queries
- Built-in text search capabilities

**Cons:**
- NoSQL queries less powerful for relational data
- Transactions more complex than SQL
- Additional infrastructure complexity

**Use Cases:**
- Highly irregular data structures
- Need for extreme schema flexibility
- Document-oriented query patterns

**Implementation Requirements:**
```python
# requirements.txt additions
pymongo==4.5.0
motor==3.3.1  # For async operations
```

### 4.2 Vector Database Options (For RAG System)

#### 4.2.1 ChromaDB (RECOMMENDED)
```yaml
Technology: ChromaDB 0.4+
Python Library: chromadb
```

**Pros:**
- Python-native implementation
- Can run in-memory or as standalone server
- Excellent integration with LangChain
- Simple API for embeddings management
- Open source with active development

**Cons:**
- Newer technology (less mature than alternatives)
- Smaller ecosystem compared to established solutions

**Implementation Requirements:**
```python
# requirements.txt additions
chromadb==0.4.15
sentence-transformers==2.2.2
```

#### 4.2.2 Weaviate (ALTERNATIVE)
```yaml
Technology: Weaviate 1.20+
Python Library: weaviate-client
```

**Pros:**
- Production-ready with enterprise features
- Excellent GraphQL API
- Built-in ML model support
- Strong consistency guarantees

**Cons:**
- More complex setup and configuration
- Requires Docker or cloud deployment
- Steeper learning curve

**Implementation Requirements:**
```python
# requirements.txt additions
weaviate-client==3.24.2
```

#### 4.2.3 Pinecone (CLOUD OPTION)
```yaml
Technology: Pinecone Cloud Service
Python Library: pinecone-client
```

**Pros:**
- Fully managed service (no infrastructure)
- Excellent performance and scalability
- Professional support available

**Cons:**
- Cloud dependency
- Recurring costs
- Less control over data

**Implementation Requirements:**
```python
# requirements.txt additions
pinecone-client==2.2.4
```

### 4.3 Recommended Database Stack

#### 4.3.1 Development Stack
```yaml
Primary Database: SQLite 3.38+
Vector Database: ChromaDB (in-memory mode)
ORM: SQLAlchemy 2.0+
Migration Tool: Alembic
```

#### 4.3.2 Production Stack
```yaml
Primary Database: PostgreSQL 15+ with pgvector
Vector Database: ChromaDB (server mode)
ORM: SQLAlchemy 2.0+
Migration Tool: Alembic
Caching: Redis (optional)
```

## 5. Database Schema Design

### 5.1 Content Management Tables

#### 5.1.1 Content Packs Table
```sql
CREATE TABLE content_packs (
    id VARCHAR(50) PRIMARY KEY,           -- e.g., 'dnd_5e_srd', 'user_homebrew_123'
    display_name VARCHAR(100) NOT NULL,   -- e.g., 'D&D 5e SRD', 'John's Homebrew'
    description TEXT,                     -- Content pack description
    author VARCHAR(100),                  -- Content creator
    version VARCHAR(20) DEFAULT '1.0.0', -- Semantic versioning
    is_active BOOLEAN DEFAULT true,       -- Enable/disable pack
    is_system BOOLEAN DEFAULT false,      -- System vs user content
    user_id INTEGER,                      -- Owner (NULL for system content)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB                        -- Additional pack metadata
);

-- Indexes
CREATE INDEX idx_content_packs_user_id ON content_packs(user_id);
CREATE INDEX idx_content_packs_active ON content_packs(is_active);
```

#### 5.1.2 Content Dependencies Table
```sql
CREATE TABLE content_dependencies (
    id SERIAL PRIMARY KEY,
    pack_id VARCHAR(50) REFERENCES content_packs(id) ON DELETE CASCADE,
    depends_on_pack_id VARCHAR(50) REFERENCES content_packs(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) NOT NULL, -- 'required', 'optional', 'conflicts'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(pack_id, depends_on_pack_id)
);
```

### 5.2 D&D Content Tables

#### 5.2.1 Spells Table
```sql
CREATE TABLE spells (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    
    -- Core spell data
    name VARCHAR(100) NOT NULL,
    level INTEGER NOT NULL CHECK (level >= 0 AND level <= 9),
    school VARCHAR(50) NOT NULL,
    casting_time VARCHAR(100) NOT NULL,
    range_value VARCHAR(100) NOT NULL,
    components VARCHAR(100) NOT NULL,
    duration VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    higher_level TEXT,
    
    -- Classification
    is_ritual BOOLEAN DEFAULT false,
    is_concentration BOOLEAN DEFAULT false,
    
    -- Classes that can cast this spell
    classes JSONB DEFAULT '[]',           -- ["Wizard", "Sorcerer"]
    
    -- RAG embeddings
    description_embedding VECTOR(768),    -- For semantic search
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_source VARCHAR(100),         -- Original book/source
    
    -- Ensure unique names within same content pack
    UNIQUE(source, name)
);

-- Indexes for performance
CREATE INDEX idx_spells_source ON spells(source);
CREATE INDEX idx_spells_level ON spells(level);
CREATE INDEX idx_spells_school ON spells(school);
CREATE INDEX idx_spells_name ON spells(name);
CREATE INDEX idx_spells_classes ON spells USING GIN(classes);
CREATE INDEX idx_spells_embedding ON spells USING hnsw (description_embedding vector_l2_ops);
```

#### 5.2.2 Monsters Table
```sql
CREATE TABLE monsters (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    size VARCHAR(20) NOT NULL,
    type VARCHAR(50) NOT NULL,
    subtype VARCHAR(50),
    alignment VARCHAR(50) NOT NULL,
    
    -- Combat stats
    armor_class INTEGER NOT NULL,
    hit_points INTEGER NOT NULL,
    hit_dice VARCHAR(20) NOT NULL,
    speed JSONB NOT NULL DEFAULT '{}',    -- {"walk": 30, "fly": 60}
    
    -- Ability scores
    strength INTEGER NOT NULL CHECK (strength > 0),
    dexterity INTEGER NOT NULL CHECK (dexterity > 0),
    constitution INTEGER NOT NULL CHECK (constitution > 0),
    intelligence INTEGER NOT NULL CHECK (intelligence > 0),
    wisdom INTEGER NOT NULL CHECK (wisdom > 0),
    charisma INTEGER NOT NULL CHECK (charisma > 0),
    
    -- Challenge and XP
    challenge_rating VARCHAR(10) NOT NULL,
    experience_points INTEGER NOT NULL,
    proficiency_bonus INTEGER NOT NULL,
    
    -- Proficiencies and resistances
    saving_throws JSONB DEFAULT '{}',     -- {"dex": 5, "wis": 3}
    skills JSONB DEFAULT '{}',            -- {"perception": 4, "stealth": 6}
    damage_vulnerabilities TEXT,
    damage_resistances TEXT,
    damage_immunities TEXT,
    condition_immunities TEXT,
    
    -- Senses and languages
    senses JSONB DEFAULT '{}',            -- {"darkvision": 60, "passive_perception": 14}
    languages TEXT,
    
    -- Abilities and actions
    special_abilities JSONB DEFAULT '[]', -- [{"name": "Pack Tactics", "desc": "..."}]
    actions JSONB DEFAULT '[]',           -- [{"name": "Bite", "desc": "...", "attack_bonus": 5}]
    legendary_actions JSONB DEFAULT '[]',
    reactions JSONB DEFAULT '[]',
    
    -- RAG embeddings
    full_text_embedding VECTOR(768),     -- Combined description for search
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_source VARCHAR(100),
    
    UNIQUE(source, name)
);

-- Indexes
CREATE INDEX idx_monsters_source ON monsters(source);
CREATE INDEX idx_monsters_challenge_rating ON monsters(challenge_rating);
CREATE INDEX idx_monsters_type ON monsters(type);
CREATE INDEX idx_monsters_name ON monsters(name);
CREATE INDEX idx_monsters_embedding ON monsters USING hnsw (full_text_embedding vector_l2_ops);
```

#### 5.2.3 Equipment Table
```sql
CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    equipment_category VARCHAR(50) NOT NULL, -- "Weapon", "Armor", "Adventuring Gear"
    description TEXT NOT NULL,
    
    -- Cost and weight
    cost_quantity INTEGER,
    cost_unit VARCHAR(10),                -- "gp", "sp", "cp"
    weight DECIMAL(5,2),
    
    -- Weapon properties
    weapon_category VARCHAR(50),          -- "Simple", "Martial"
    weapon_range VARCHAR(20),             -- "Melee", "Ranged"
    damage JSONB,                         -- {"damage_dice": "1d8", "damage_type": "slashing"}
    properties JSONB DEFAULT '[]',        -- ["finesse", "light"]
    
    -- Armor properties
    armor_category VARCHAR(20),           -- "Light", "Medium", "Heavy", "Shield"
    armor_class JSONB,                    -- {"base": 11, "dex_bonus": true, "max_bonus": 2}
    strength_requirement INTEGER,
    stealth_disadvantage BOOLEAN DEFAULT false,
    
    -- Magic item properties
    is_magic_item BOOLEAN DEFAULT false,
    rarity VARCHAR(20),                   -- "common", "uncommon", "rare", "very rare", "legendary"
    requires_attunement BOOLEAN DEFAULT false,
    magic_properties JSONB DEFAULT '[]',
    
    -- RAG embeddings
    description_embedding VECTOR(768),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_source VARCHAR(100),
    
    UNIQUE(source, name)
);

-- Indexes
CREATE INDEX idx_equipment_source ON equipment(source);
CREATE INDEX idx_equipment_category ON equipment(equipment_category);
CREATE INDEX idx_equipment_magic ON equipment(is_magic_item);
CREATE INDEX idx_equipment_name ON equipment(name);
CREATE INDEX idx_equipment_embedding ON equipment USING hnsw (description_embedding vector_l2_ops);
```

### 5.3 Character Creation Tables

#### 5.3.1 Races Table
```sql
CREATE TABLE races (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Mechanical benefits
    ability_score_increases JSONB NOT NULL DEFAULT '{}', -- {"str": 2, "con": 1}
    size VARCHAR(20) NOT NULL,
    speed INTEGER NOT NULL DEFAULT 30,
    languages JSONB DEFAULT '[]',         -- ["Common", "Elvish"]
    proficiencies JSONB DEFAULT '{}',     -- {"skills": ["Perception"], "weapons": ["Longsword"]}
    
    -- Racial traits
    traits JSONB DEFAULT '[]',            -- [{"name": "Darkvision", "description": "..."}]
    
    -- Subraces
    has_subraces BOOLEAN DEFAULT false,
    
    -- RAG embeddings
    description_embedding VECTOR(768),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_source VARCHAR(100),
    
    UNIQUE(source, name)
);

-- Subraces table
CREATE TABLE subraces (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    race_id INTEGER NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Additional benefits beyond base race
    additional_ability_score_increases JSONB DEFAULT '{}',
    additional_proficiencies JSONB DEFAULT '{}',
    additional_traits JSONB DEFAULT '[]',
    additional_spells JSONB DEFAULT '[]',
    
    -- RAG embeddings
    description_embedding VECTOR(768),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source, race_id, name)
);
```

#### 5.3.2 Classes Table
```sql
CREATE TABLE classes (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    hit_die INTEGER NOT NULL,
    
    -- Proficiencies
    primary_abilities JSONB NOT NULL DEFAULT '[]', -- ["Strength", "Dexterity"]
    saving_throw_proficiencies JSONB NOT NULL DEFAULT '[]',
    skill_proficiencies JSONB DEFAULT '{}',       -- {"choose": 2, "from": ["Acrobatics", "Athletics"]}
    armor_proficiencies JSONB DEFAULT '[]',
    weapon_proficiencies JSONB DEFAULT '[]',
    tool_proficiencies JSONB DEFAULT '[]',
    
    -- Equipment
    starting_equipment JSONB DEFAULT '[]',
    equipment_options JSONB DEFAULT '[]',
    
    -- Spellcasting
    is_spellcaster BOOLEAN DEFAULT false,
    spellcasting_ability VARCHAR(20),             -- "Intelligence", "Wisdom", "Charisma"
    spell_list JSONB DEFAULT '[]',                -- Available spells by level
    
    -- Class features by level
    class_features JSONB DEFAULT '{}',            -- {"1": [...], "2": [...]}
    
    -- RAG embeddings
    description_embedding VECTOR(768),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_source VARCHAR(100),
    
    UNIQUE(source, name)
);

-- Subclasses table
CREATE TABLE subclasses (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    subclass_flavor TEXT,                         -- e.g., "Otherworldly Patron" for Warlock
    
    -- Level when subclass is chosen
    subclass_level INTEGER NOT NULL DEFAULT 1,
    
    -- Additional features
    subclass_features JSONB DEFAULT '{}',         -- Features by level
    additional_spells JSONB DEFAULT '{}',         -- Expanded spell list
    
    -- RAG embeddings
    description_embedding VECTOR(768),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source, class_id, name)
);
```

### 5.4 Lore and Knowledge Tables

#### 5.4.1 Lore Collections Table
```sql
CREATE TABLE lore_collections (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL REFERENCES content_packs(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,               -- "world", "history", "religion", "custom"
    
    -- Organization
    is_system_lore BOOLEAN DEFAULT false,        -- vs user-created
    parent_collection_id INTEGER REFERENCES lore_collections(id),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source, name)
);

CREATE TABLE lore_entries (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES lore_collections(id) ON DELETE CASCADE,
    
    -- Content
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    tags JSONB DEFAULT '[]',                     -- ["gods", "creation", "mythology"]
    
    -- Organization
    entry_order INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT true,
    
    -- RAG embeddings
    content_embedding VECTOR(768),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.5 Database Constraints and Relationships

#### 5.5.1 Foreign Key Constraints
```sql
-- Ensure referential integrity
ALTER TABLE spells ADD CONSTRAINT fk_spells_source 
    FOREIGN KEY (source) REFERENCES content_packs(id) ON DELETE CASCADE;

ALTER TABLE monsters ADD CONSTRAINT fk_monsters_source 
    FOREIGN KEY (source) REFERENCES content_packs(id) ON DELETE CASCADE;

-- Add similar constraints for all content tables
```

#### 5.5.2 Check Constraints
```sql
-- Validate ability scores (1-30 range)
ALTER TABLE monsters ADD CONSTRAINT chk_ability_scores 
    CHECK (strength BETWEEN 1 AND 30 AND 
           dexterity BETWEEN 1 AND 30 AND 
           constitution BETWEEN 1 AND 30 AND 
           intelligence BETWEEN 1 AND 30 AND 
           wisdom BETWEEN 1 AND 30 AND 
           charisma BETWEEN 1 AND 30);

-- Validate spell levels
ALTER TABLE spells ADD CONSTRAINT chk_spell_level 
    CHECK (level BETWEEN 0 AND 9);

-- Validate challenge ratings
ALTER TABLE monsters ADD CONSTRAINT chk_challenge_rating 
    CHECK (challenge_rating IN ('0', '1/8', '1/4', '1/2', '1', '2', '3', '4', '5', 
                                '6', '7', '8', '9', '10', '11', '12', '13', '14', 
                                '15', '16', '17', '18', '19', '20', '21', '22', 
                                '23', '24', '25', '26', '27', '28', '29', '30'));
```

## 6. Repository Layer Implementation

### 6.1 Base Repository Pattern

#### 6.1.1 Abstract Base Repository
```python
# app/repositories/d5e/base_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Type
from sqlalchemy.orm import Session
from app.core.interfaces import DatabaseProtocol

T = TypeVar('T')

class BaseD5eRepository(Generic[T], ABC):
    """Abstract base repository for D5e content with content pack support."""
    
    def __init__(self, db: DatabaseProtocol, model_class: Type[T]):
        self.db = db
        self.model_class = model_class
    
    @abstractmethod
    def find_by_name(self, name: str, content_pack_priority: List[str]) -> Optional[T]:
        """Find entity by name using content pack precedence."""
        pass
    
    @abstractmethod
    def find_all(self, content_pack_priority: List[str], filters: dict = None) -> List[T]:
        """Find all entities with content pack filtering."""
        pass
    
    @abstractmethod
    def create(self, entity: T, source: str) -> T:
        """Create new entity in specified content pack."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID."""
        pass
    
    def get_available_sources(self, active_only: bool = True) -> List[str]:
        """Get list of available content pack sources."""
        query = self.db.session.query(ContentPack.id)
        if active_only:
            query = query.filter(ContentPack.is_active == True)
        return [row.id for row in query.all()]
```

#### 6.1.2 Spell Repository Implementation
```python
# app/repositories/d5e/spell_repository.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.repositories.d5e.base_repository import BaseD5eRepository
from app.models.d5e.spells import SpellModel
from app.database.models import Spell, ContentPack

class SpellRepository(BaseD5eRepository[SpellModel]):
    """Repository for spell data with content pack support."""
    
    def __init__(self, db: DatabaseProtocol):
        super().__init__(db, SpellModel)
    
    def find_by_name(self, name: str, content_pack_priority: List[str]) -> Optional[SpellModel]:
        """Find spell by name using content pack precedence."""
        session = self.db.session
        
        # Try each content pack in priority order
        for source in content_pack_priority:
            spell = session.query(Spell).filter(
                and_(Spell.name == name, Spell.source == source)
            ).first()
            
            if spell:
                return self._to_pydantic_model(spell)
        
        return None
    
    def find_by_level(self, level: int, content_pack_priority: List[str]) -> List[SpellModel]:
        """Find spells by level across active content packs."""
        session = self.db.session
        
        spells = session.query(Spell).filter(
            and_(
                Spell.level == level,
                Spell.source.in_(content_pack_priority)
            )
        ).order_by(Spell.source.desc(), Spell.name).all()
        
        # Remove duplicates, keeping highest priority version
        seen_names = set()
        unique_spells = []
        
        for spell in spells:
            if spell.name not in seen_names:
                seen_names.add(spell.name)
                unique_spells.append(self._to_pydantic_model(spell))
        
        return unique_spells
    
    def find_by_class(self, class_name: str, content_pack_priority: List[str]) -> List[SpellModel]:
        """Find spells available to a specific class."""
        session = self.db.session
        
        spells = session.query(Spell).filter(
            and_(
                Spell.classes.contains([class_name]),  # JSONB contains
                Spell.source.in_(content_pack_priority)
            )
        ).order_by(Spell.level, Spell.name).all()
        
        return [self._to_pydantic_model(spell) for spell in spells]
    
    def search_by_text(self, query: str, content_pack_priority: List[str]) -> List[SpellModel]:
        """Full-text search across spell names and descriptions."""
        session = self.db.session
        
        # PostgreSQL full-text search
        spells = session.query(Spell).filter(
            and_(
                or_(
                    Spell.name.ilike(f'%{query}%'),
                    Spell.description.ilike(f'%{query}%')
                ),
                Spell.source.in_(content_pack_priority)
            )
        ).limit(50).all()
        
        return [self._to_pydantic_model(spell) for spell in spells]
    
    def create(self, spell_data: SpellModel, source: str) -> SpellModel:
        """Create new spell in specified content pack."""
        session = self.db.session
        
        # Check if content pack exists
        content_pack = session.query(ContentPack).filter(
            ContentPack.id == source
        ).first()
        
        if not content_pack:
            raise ValueError(f"Content pack '{source}' not found")
        
        # Check for duplicate names within same source
        existing = session.query(Spell).filter(
            and_(Spell.name == spell_data.name, Spell.source == source)
        ).first()
        
        if existing:
            raise ValueError(f"Spell '{spell_data.name}' already exists in source '{source}'")
        
        # Create database entity
        db_spell = Spell(
            source=source,
            name=spell_data.name,
            level=spell_data.level,
            school=spell_data.school,
            casting_time=spell_data.casting_time,
            range_value=spell_data.range,
            components=spell_data.components,
            duration=spell_data.duration,
            description=spell_data.description,
            higher_level=spell_data.higher_level,
            is_ritual=spell_data.is_ritual,
            is_concentration=spell_data.is_concentration,
            classes=spell_data.classes,
            original_source=spell_data.original_source
        )
        
        session.add(db_spell)
        session.commit()
        session.refresh(db_spell)
        
        return self._to_pydantic_model(db_spell)
    
    def _to_pydantic_model(self, db_spell: Spell) -> SpellModel:
        """Convert database model to Pydantic model."""
        return SpellModel(
            id=str(db_spell.id),
            name=db_spell.name,
            level=db_spell.level,
            school=db_spell.school,
            casting_time=db_spell.casting_time,
            range=db_spell.range_value,
            components=db_spell.components,
            duration=db_spell.duration,
            description=db_spell.description,
            higher_level=db_spell.higher_level,
            is_ritual=db_spell.is_ritual,
            is_concentration=db_spell.is_concentration,
            classes=db_spell.classes or [],
            source=db_spell.source,
            original_source=db_spell.original_source
        )
```

### 6.2 Repository Factory Pattern
```python
# app/repositories/d5e/repository_factory.py
from typing import Dict, Type
from app.core.interfaces import DatabaseProtocol
from app.repositories.d5e.base_repository import BaseD5eRepository
from app.repositories.d5e.spell_repository import SpellRepository
from app.repositories.d5e.monster_repository import MonsterRepository
from app.repositories.d5e.equipment_repository import EquipmentRepository
from app.repositories.d5e.race_repository import RaceRepository
from app.repositories.d5e.class_repository import ClassRepository

class D5eRepositoryFactory:
    """Factory for creating D5e repositories."""
    
    _repositories: Dict[str, Type[BaseD5eRepository]] = {
        'spells': SpellRepository,
        'monsters': MonsterRepository,
        'equipment': EquipmentRepository,
        'races': RaceRepository,
        'classes': ClassRepository,
    }
    
    def __init__(self, db: DatabaseProtocol):
        self.db = db
        self._instances: Dict[str, BaseD5eRepository] = {}
    
    def get_repository(self, repository_type: str) -> BaseD5eRepository:
        """Get repository instance by type."""
        if repository_type not in self._repositories:
            raise ValueError(f"Unknown repository type: {repository_type}")
        
        if repository_type not in self._instances:
            repo_class = self._repositories[repository_type]
            self._instances[repository_type] = repo_class(self.db)
        
        return self._instances[repository_type]
    
    @property
    def spells(self) -> SpellRepository:
        return self.get_repository('spells')
    
    @property
    def monsters(self) -> MonsterRepository:
        return self.get_repository('monsters')
    
    @property
    def equipment(self) -> EquipmentRepository:
        return self.get_repository('equipment')
    
    @property
    def races(self) -> RaceRepository:
        return self.get_repository('races')
    
    @property
    def classes(self) -> ClassRepository:
        return self.get_repository('classes')
```

## 7. Content Pack Management System

### 7.1 Content Pack Service
```python
# app/services/content_pack_service.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ValidationError
import json
import uuid
from datetime import datetime

from app.core.interfaces import DatabaseProtocol
from app.models.d5e.base import ContentPackModel
from app.repositories.d5e.repository_factory import D5eRepositoryFactory
from app.database.models import ContentPack

class ContentPackService:
    """Service for managing content packs and user content."""
    
    def __init__(self, db: DatabaseProtocol, repo_factory: D5eRepositoryFactory):
        self.db = db
        self.repo_factory = repo_factory
    
    def create_content_pack(
        self, 
        display_name: str, 
        description: str = "",
        author: str = "",
        user_id: Optional[int] = None
    ) -> ContentPackModel:
        """Create a new content pack."""
        session = self.db.session
        
        # Generate unique ID
        pack_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}" if user_id else f"system_{uuid.uuid4().hex[:8]}"
        
        # Create database entity
        db_pack = ContentPack(
            id=pack_id,
            display_name=display_name,
            description=description,
            author=author,
            user_id=user_id,
            is_system=user_id is None,
            is_active=True
        )
        
        session.add(db_pack)
        session.commit()
        session.refresh(db_pack)
        
        return self._to_pydantic_model(db_pack)
    
    def upload_content_from_json(
        self, 
        content_pack_id: str, 
        content_type: str, 
        json_data: str
    ) -> Dict[str, Any]:
        """Upload and validate content from JSON data."""
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON: {str(e)}",
                "details": {}
            }
        
        # Validate content pack exists
        session = self.db.session
        content_pack = session.query(ContentPack).filter(
            ContentPack.id == content_pack_id
        ).first()
        
        if not content_pack:
            return {
                "success": False,
                "error": f"Content pack '{content_pack_id}' not found",
                "details": {}
            }
        
        # Get appropriate repository
        try:
            repository = self.repo_factory.get_repository(content_type)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "details": {}
            }
        
        # Process each item in the JSON data
        results = {
            "success": True,
            "total_items": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "errors": []
        }
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and content_type in data:
            items = data[content_type]
        else:
            return {
                "success": False,
                "error": f"Expected list or object with '{content_type}' key",
                "details": {}
            }
        
        results["total_items"] = len(items)
        
        for i, item_data in enumerate(items):
            try:
                # Validate against Pydantic model
                if content_type == 'spells':
                    from app.models.d5e.spells import SpellModel
                    validated_item = SpellModel.model_validate(item_data)
                elif content_type == 'monsters':
                    from app.models.d5e.monsters import MonsterModel
                    validated_item = MonsterModel.model_validate(item_data)
                # Add other content types...
                else:
                    raise ValueError(f"Unsupported content type: {content_type}")
                
                # Create in database
                repository.create(validated_item, content_pack_id)
                results["successful_imports"] += 1
                
            except ValidationError as e:
                results["failed_imports"] += 1
                results["errors"].append({
                    "item_index": i,
                    "item_name": item_data.get("name", f"Item {i}"),
                    "error": "Validation failed",
                    "details": e.errors()
                })
            except Exception as e:
                results["failed_imports"] += 1
                results["errors"].append({
                    "item_index": i,
                    "item_name": item_data.get("name", f"Item {i}"),
                    "error": str(e),
                    "details": {}
                })
        
        return results
    
    def get_user_content_packs(self, user_id: int) -> List[ContentPackModel]:
        """Get all content packs owned by a user."""
        session = self.db.session
        
        packs = session.query(ContentPack).filter(
            ContentPack.user_id == user_id
        ).order_by(ContentPack.display_name).all()
        
        return [self._to_pydantic_model(pack) for pack in packs]
    
    def get_system_content_packs(self) -> List[ContentPackModel]:
        """Get all system (official) content packs."""
        session = self.db.session
        
        packs = session.query(ContentPack).filter(
            ContentPack.is_system == True
        ).order_by(ContentPack.display_name).all()
        
        return [self._to_pydantic_model(pack) for pack in packs]
    
    def activate_content_pack(self, pack_id: str, user_id: Optional[int] = None) -> bool:
        """Activate a content pack for use."""
        session = self.db.session
        
        pack = session.query(ContentPack).filter(
            ContentPack.id == pack_id
        ).first()
        
        if not pack:
            return False
        
        # Check permissions
        if pack.user_id is not None and pack.user_id != user_id:
            return False  # User can't activate another user's content
        
        pack.is_active = True
        session.commit()
        return True
    
    def deactivate_content_pack(self, pack_id: str, user_id: Optional[int] = None) -> bool:
        """Deactivate a content pack."""
        session = self.db.session
        
        pack = session.query(ContentPack).filter(
            ContentPack.id == pack_id
        ).first()
        
        if not pack:
            return False
        
        # Check permissions
        if pack.user_id is not None and pack.user_id != user_id:
            return False
        
        # Don't allow deactivating system packs
        if pack.is_system:
            return False
        
        pack.is_active = False
        session.commit()
        return True
    
    def _to_pydantic_model(self, db_pack: ContentPack) -> ContentPackModel:
        """Convert database model to Pydantic model."""
        return ContentPackModel(
            id=db_pack.id,
            display_name=db_pack.display_name,
            description=db_pack.description or "",
            author=db_pack.author or "",
            version=db_pack.version,
            is_active=db_pack.is_active,
            is_system=db_pack.is_system,
            user_id=db_pack.user_id,
            created_at=db_pack.created_at,
            updated_at=db_pack.updated_at,
            metadata=db_pack.metadata or {}
        )
```

## 8. RAG System Integration

### 8.1 Vector Database Implementation

#### 8.1.1 ChromaDB Integration
```python
# app/services/rag/chroma_vector_store.py
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
from sentence_transformers import SentenceTransformer

from app.core.rag_interfaces import VectorStoreProtocol, KnowledgeResult

class ChromaVectorStore(VectorStoreProtocol):
    """ChromaDB implementation of vector store for RAG system."""
    
    def __init__(self, persist_directory: str = "data/chromadb"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create collections for different content types
        self.collections = {
            'spells': self._get_or_create_collection('d5e_spells'),
            'monsters': self._get_or_create_collection('d5e_monsters'),
            'equipment': self._get_or_create_collection('d5e_equipment'),
            'rules': self._get_or_create_collection('d5e_rules'),
            'lore': self._get_or_create_collection('game_lore'),
            'classes': self._get_or_create_collection('d5e_classes'),
            'races': self._get_or_create_collection('d5e_races')
        }
    
    def _get_or_create_collection(self, name: str):
        """Get existing collection or create new one."""
        try:
            return self.client.get_collection(name)
        except ValueError:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_document(
        self, 
        collection_name: str, 
        document_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """Add a document to the vector store."""
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        collection = self.collections[collection_name]
        
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()
        
        # Add to collection
        collection.add(
            ids=[document_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    
    def search(
        self, 
        collection_name: str, 
        query: str, 
        n_results: int = 10,
        content_pack_filter: Optional[List[str]] = None
    ) -> List[KnowledgeResult]:
        """Search for similar documents."""
        if collection_name not in self.collections:
            return []
        
        collection = self.collections[collection_name]
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Build where clause for content pack filtering
        where_clause = None
        if content_pack_filter:
            where_clause = {"source": {"$in": content_pack_filter}}
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )
        
        # Convert to KnowledgeResult objects
        knowledge_results = []
        
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0.0
                
                # Convert distance to similarity score (1 - cosine_distance)
                similarity = max(0.0, 1.0 - distance)
                
                knowledge_results.append(KnowledgeResult(
                    content=doc,
                    source=metadata.get('source', 'unknown'),
                    relevance_score=similarity,
                    metadata=metadata
                ))
        
        return knowledge_results
    
    def update_document(
        self, 
        collection_name: str, 
        document_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """Update an existing document."""
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        collection = self.collections[collection_name]
        
        # Generate new embedding
        embedding = self.embedding_model.encode(text).tolist()
        
        # Update in collection
        collection.update(
            ids=[document_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    
    def delete_document(self, collection_name: str, document_id: str) -> None:
        """Delete a document from the vector store."""
        if collection_name not in self.collections:
            return
        
        collection = self.collections[collection_name]
        collection.delete(ids=[document_id])
    
    def delete_by_source(self, collection_name: str, source: str) -> None:
        """Delete all documents from a specific source (content pack)."""
        if collection_name not in self.collections:
            return
        
        collection = self.collections[collection_name]
        
        # Get all documents from this source
        results = collection.get(where={"source": source})
        
        if results['ids']:
            collection.delete(ids=results['ids'])
```

#### 8.1.2 RAG Service Enhancement
```python
# app/services/rag/enhanced_rag_service.py
from typing import List, Optional, Dict, Any
from app.core.rag_interfaces import RAGServiceProtocol, KnowledgeResult, RAGResults, QueryRequest
from app.services.rag.chroma_vector_store import ChromaVectorStore
from app.repositories.d5e.repository_factory import D5eRepositoryFactory

class EnhancedRAGService(RAGServiceProtocol):
    """Enhanced RAG service with database and vector store integration."""
    
    def __init__(self, vector_store: ChromaVectorStore, repo_factory: D5eRepositoryFactory):
        self.vector_store = vector_store
        self.repo_factory = repo_factory
    
    def query_knowledge(self, request: QueryRequest) -> RAGResults:
        """Query knowledge across all relevant sources."""
        all_results = []
        
        # Determine which collections to search
        collections_to_search = self._determine_collections(request.knowledge_types)
        
        # Search each collection
        for collection in collections_to_search:
            results = self.vector_store.search(
                collection_name=collection,
                query=request.query,
                n_results=request.max_results // len(collections_to_search),
                content_pack_filter=getattr(request, 'content_pack_filter', None)
            )
            all_results.extend(results)
        
        # Sort by relevance score and apply threshold
        filtered_results = [
            result for result in all_results 
            if result.relevance_score >= request.relevance_threshold
        ]
        
        filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit to max_results
        final_results = filtered_results[:request.max_results]
        
        return RAGResults(
            results=final_results,
            total_results=len(all_results),
            query=request.query
        )
    
    def index_content_from_database(self, content_pack_id: str) -> Dict[str, int]:
        """Index all content from a specific content pack into vector store."""
        indexing_stats = {
            'spells': 0,
            'monsters': 0,
            'equipment': 0,
            'classes': 0,
            'races': 0
        }
        
        # Index spells
        spells = self.repo_factory.spells.find_all([content_pack_id])
        for spell in spells:
            text_content = self._format_spell_for_indexing(spell)
            self.vector_store.add_document(
                collection_name='spells',
                document_id=f"{content_pack_id}_{spell.id}",
                text=text_content,
                metadata={
                    'source': content_pack_id,
                    'content_type': 'spell',
                    'name': spell.name,
                    'level': spell.level,
                    'school': spell.school,
                    'id': spell.id
                }
            )
            indexing_stats['spells'] += 1
        
        # Index monsters
        monsters = self.repo_factory.monsters.find_all([content_pack_id])
        for monster in monsters:
            text_content = self._format_monster_for_indexing(monster)
            self.vector_store.add_document(
                collection_name='monsters',
                document_id=f"{content_pack_id}_{monster.id}",
                text=text_content,
                metadata={
                    'source': content_pack_id,
                    'content_type': 'monster',
                    'name': monster.name,
                    'challenge_rating': monster.challenge_rating,
                    'type': monster.type,
                    'id': monster.id
                }
            )
            indexing_stats['monsters'] += 1
        
        # Index equipment
        equipment = self.repo_factory.equipment.find_all([content_pack_id])
        for item in equipment:
            text_content = self._format_equipment_for_indexing(item)
            self.vector_store.add_document(
                collection_name='equipment',
                document_id=f"{content_pack_id}_{item.id}",
                text=text_content,
                metadata={
                    'source': content_pack_id,
                    'content_type': 'equipment',
                    'name': item.name,
                    'category': item.equipment_category,
                    'id': item.id
                }
            )
            indexing_stats['equipment'] += 1
        
        # Index classes and races similarly...
        
        return indexing_stats
    
    def remove_content_pack_from_index(self, content_pack_id: str) -> None:
        """Remove all content from a content pack from the vector store."""
        collections = ['spells', 'monsters', 'equipment', 'classes', 'races', 'lore']
        
        for collection in collections:
            self.vector_store.delete_by_source(collection, content_pack_id)
    
    def _determine_collections(self, knowledge_types: List[str]) -> List[str]:
        """Determine which vector collections to search based on knowledge types."""
        type_mapping = {
            'spells': ['spells'],
            'monsters': ['monsters'],
            'equipment': ['equipment'],
            'combat': ['spells', 'monsters', 'equipment'],
            'character_creation': ['classes', 'races', 'equipment'],
            'rules': ['rules'],
            'lore': ['lore'],
            'all': ['spells', 'monsters', 'equipment', 'classes', 'races', 'rules', 'lore']
        }
        
        collections = set()
        for knowledge_type in knowledge_types:
            if knowledge_type in type_mapping:
                collections.update(type_mapping[knowledge_type])
        
        return list(collections) if collections else ['spells', 'monsters', 'equipment']
    
    def _format_spell_for_indexing(self, spell) -> str:
        """Format spell data for text indexing."""
        text_parts = [
            f"Spell: {spell.name}",
            f"Level: {spell.level}",
            f"School: {spell.school}",
            f"Classes: {', '.join(spell.classes)}",
            f"Casting Time: {spell.casting_time}",
            f"Range: {spell.range}",
            f"Components: {spell.components}",
            f"Duration: {spell.duration}",
            f"Description: {spell.description}"
        ]
        
        if spell.higher_level:
            text_parts.append(f"At Higher Levels: {spell.higher_level}")
        
        return "\n".join(text_parts)
    
    def _format_monster_for_indexing(self, monster) -> str:
        """Format monster data for text indexing."""
        text_parts = [
            f"Monster: {monster.name}",
            f"Type: {monster.type}",
            f"Size: {monster.size}",
            f"Challenge Rating: {monster.challenge_rating}",
            f"Armor Class: {monster.armor_class}",
            f"Hit Points: {monster.hit_points}",
            f"Abilities: STR {monster.strength}, DEX {monster.dexterity}, CON {monster.constitution}, INT {monster.intelligence}, WIS {monster.wisdom}, CHA {monster.charisma}"
        ]
        
        # Add special abilities
        if monster.special_abilities:
            abilities_text = []
            for ability in monster.special_abilities:
                abilities_text.append(f"{ability['name']}: {ability['desc']}")
            text_parts.append(f"Special Abilities: {'; '.join(abilities_text)}")
        
        # Add actions
        if monster.actions:
            actions_text = []
            for action in monster.actions:
                actions_text.append(f"{action['name']}: {action['desc']}")
            text_parts.append(f"Actions: {'; '.join(actions_text)}")
        
        return "\n".join(text_parts)
    
    def _format_equipment_for_indexing(self, equipment) -> str:
        """Format equipment data for text indexing."""
        text_parts = [
            f"Equipment: {equipment.name}",
            f"Category: {equipment.equipment_category}",
            f"Description: {equipment.description}"
        ]
        
        if equipment.cost_quantity and equipment.cost_unit:
            text_parts.append(f"Cost: {equipment.cost_quantity} {equipment.cost_unit}")
        
        if equipment.weight:
            text_parts.append(f"Weight: {equipment.weight} lbs")
        
        # Add weapon-specific information
        if equipment.weapon_category:
            text_parts.append(f"Weapon Category: {equipment.weapon_category}")
            if equipment.damage:
                text_parts.append(f"Damage: {equipment.damage}")
            if equipment.properties:
                text_parts.append(f"Properties: {', '.join(equipment.properties)}")
        
        # Add armor-specific information
        if equipment.armor_category:
            text_parts.append(f"Armor Category: {equipment.armor_category}")
            if equipment.armor_class:
                text_parts.append(f"Armor Class: {equipment.armor_class}")
        
        return "\n".join(text_parts)
```

## 9. Migration Implementation Plan

### 9.1 Phase 1: Database Foundation (Week 1-2)

#### 9.1.1 Database Setup
```python
# app/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from typing import Generator

Base = declarative_base()

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = os.getenv(
                'DATABASE_URL', 
                'sqlite:///data/gamemaster.db'
            )
        
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            echo=os.getenv('SQL_DEBUG', 'false').lower() == 'true'
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )
    
    @contextmanager
    def get_session(self) -> Generator:
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (for testing)."""
        Base.metadata.drop_all(bind=self.engine)
```

#### 9.1.2 Database Models
```python
# app/database/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, DECIMAL, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, VECTOR
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from app.database.connection import Base
import os

# Use JSONB for PostgreSQL, JSON for SQLite
JsonType = JSONB if os.getenv('DATABASE_URL', '').startswith('postgresql') else JSON

class ContentPack(Base):
    __tablename__ = 'content_packs'
    
    id = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    author = Column(String(100))
    version = Column(String(20), default='1.0.0')
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    user_id = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    metadata = Column(JsonType)
    
    # Relationships
    spells = relationship("Spell", back_populates="content_pack", cascade="all, delete-orphan")
    monsters = relationship("Monster", back_populates="content_pack", cascade="all, delete-orphan")
    equipment = relationship("Equipment", back_populates="content_pack", cascade="all, delete-orphan")

class Spell(Base):
    __tablename__ = 'spells'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), ForeignKey('content_packs.id', ondelete='CASCADE'), nullable=False)
    
    # Core spell data
    name = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)
    school = Column(String(50), nullable=False)
    casting_time = Column(String(100), nullable=False)
    range_value = Column(String(100), nullable=False)
    components = Column(String(100), nullable=False)
    duration = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    higher_level = Column(Text)
    
    # Classification
    is_ritual = Column(Boolean, default=False)
    is_concentration = Column(Boolean, default=False)
    
    # Classes that can cast this spell
    classes = Column(JsonType, default=list)
    
    # Vector embedding for RAG (PostgreSQL only)
    if os.getenv('DATABASE_URL', '').startswith('postgresql'):
        description_embedding = Column(VECTOR(768))
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    original_source = Column(String(100))
    
    # Relationships
    content_pack = relationship("ContentPack", back_populates="spells")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('level >= 0 AND level <= 9', name='chk_spell_level'),
        CheckConstraint('length(name) > 0', name='chk_spell_name_not_empty'),
        # Unique constraint handled at database level
    )

# Add indexes after class definition
from sqlalchemy import Index

Index('idx_spells_source', Spell.source)
Index('idx_spells_level', Spell.level)
Index('idx_spells_school', Spell.school)
Index('idx_spells_name', Spell.name)
Index('idx_spells_classes', Spell.classes)

# Similar Monster and Equipment models...
```

#### 9.1.3 Migration Scripts
```python
# scripts/migrate_json_to_db.py
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from app.database.connection import DatabaseManager
from app.database.models import ContentPack, Spell, Monster, Equipment
from app.models.d5e.spells import SpellModel
from app.models.d5e.monsters import MonsterModel
from app.models.d5e.equipment import EquipmentModel

class JsonToDatabaseMigrator:
    """Migrates JSON files to database."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.stats = {
            'content_packs': 0,
            'spells': 0,
            'monsters': 0,
            'equipment': 0,
            'errors': []
        }
    
    def migrate_5e_database(self, json_directory: str = "knowledge/5e-database/src/2014/"):
        """Migrate all 5e SRD JSON files to database."""
        print(f"Starting migration from {json_directory}")
        
        # Create D&D 5e SRD content pack
        with self.db_manager.get_session() as session:
            srd_pack = ContentPack(
                id='dnd_5e_srd',
                display_name='D&D 5e SRD',
                description='System Reference Document for D&D 5th Edition',
                author='Wizards of the Coast',
                is_system=True,
                is_active=True
            )
            session.add(srd_pack)
            session.commit()
            self.stats['content_packs'] += 1
        
        # Migrate each JSON file
        json_files = {
            'spells': '5e-SRD-Spells.json',
            'monsters': '5e-SRD-Monsters.json',
            'equipment': '5e-SRD-Equipment.json',
            'classes': '5e-SRD-Classes.json',
            'races': '5e-SRD-Races.json',
            # Add other files...
        }
        
        for content_type, filename in json_files.items():
            file_path = Path(json_directory) / filename
            if file_path.exists():
                self._migrate_file(file_path, content_type, 'dnd_5e_srd')
            else:
                print(f"Warning: {file_path} not found")
        
        print(f"Migration complete. Stats: {self.stats}")
    
    def _migrate_file(self, file_path: Path, content_type: str, source: str):
        """Migrate a single JSON file."""
        print(f"Migrating {file_path} as {content_type}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = data if isinstance(data, list) else data.get(content_type, [])
            
            with self.db_manager.get_session() as session:
                for item_data in items:
                    try:
                        if content_type == 'spells':
                            self._migrate_spell(session, item_data, source)
                        elif content_type == 'monsters':
                            self._migrate_monster(session, item_data, source)
                        elif content_type == 'equipment':
                            self._migrate_equipment(session, item_data, source)
                        # Add other content types...
                        
                    except Exception as e:
                        error_msg = f"Error migrating {content_type} '{item_data.get('name', 'unknown')}': {str(e)}"
                        print(error_msg)
                        self.stats['errors'].append(error_msg)
                
                session.commit()
        
        except Exception as e:
            error_msg = f"Error reading {file_path}: {str(e)}"
            print(error_msg)
            self.stats['errors'].append(error_msg)
    
    def _migrate_spell(self, session, spell_data: Dict[str, Any], source: str):
        """Migrate a single spell to database."""
        # Validate with Pydantic model
        spell_model = SpellModel.model_validate(spell_data)
        
        # Create database entity
        db_spell = Spell(
            source=source,
            name=spell_model.name,
            level=spell_model.level,
            school=spell_model.school,
            casting_time=spell_model.casting_time,
            range_value=spell_model.range,
            components=spell_model.components,
            duration=spell_model.duration,
            description=spell_model.description,
            higher_level=spell_model.higher_level,
            is_ritual=spell_model.is_ritual,
            is_concentration=spell_model.is_concentration,
            classes=spell_model.classes,
            original_source=spell_data.get('index', spell_model.name)
        )
        
        session.add(db_spell)
        self.stats['spells'] += 1
    
    def _migrate_monster(self, session, monster_data: Dict[str, Any], source: str):
        """Migrate a single monster to database."""
        # Validate with Pydantic model
        monster_model = MonsterModel.model_validate(monster_data)
        
        # Create database entity
        db_monster = Monster(
            source=source,
            name=monster_model.name,
            size=monster_model.size,
            type=monster_model.type,
            subtype=monster_model.subtype,
            alignment=monster_model.alignment,
            armor_class=monster_model.armor_class,
            hit_points=monster_model.hit_points,
            hit_dice=monster_model.hit_dice,
            speed=monster_model.speed,
            strength=monster_model.strength,
            dexterity=monster_model.dexterity,
            constitution=monster_model.constitution,
            intelligence=monster_model.intelligence,
            wisdom=monster_model.wisdom,
            charisma=monster_model.charisma,
            challenge_rating=monster_model.challenge_rating,
            experience_points=monster_model.experience_points,
            proficiency_bonus=monster_model.proficiency_bonus,
            saving_throws=monster_model.saving_throws,
            skills=monster_model.skills,
            damage_vulnerabilities=monster_model.damage_vulnerabilities,
            damage_resistances=monster_model.damage_resistances,
            damage_immunities=monster_model.damage_immunities,
            condition_immunities=monster_model.condition_immunities,
            senses=monster_model.senses,
            languages=monster_model.languages,
            special_abilities=monster_model.special_abilities,
            actions=monster_model.actions,
            legendary_actions=monster_model.legendary_actions,
            reactions=monster_model.reactions,
            original_source=monster_data.get('index', monster_model.name)
        )
        
        session.add(db_monster)
        self.stats['monsters'] += 1
    
    def _migrate_equipment(self, session, equipment_data: Dict[str, Any], source: str):
        """Migrate a single equipment item to database."""
        # Similar implementation to spell and monster...
        pass

# Migration runner script
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate JSON files to database')
    parser.add_argument('--database-url', help='Database URL (default: SQLite)')
    parser.add_argument('--json-dir', default='knowledge/5e-database/src/2014/', 
                       help='Directory containing JSON files')
    
    args = parser.parse_args()
    
    # Set up database
    db_manager = DatabaseManager(args.database_url)
    db_manager.create_tables()
    
    # Run migration
    migrator = JsonToDatabaseMigrator(db_manager)
    migrator.migrate_5e_database(args.json_dir)
```

### 9.2 Phase 2: Repository Integration (Week 2-3)

#### 9.2.1 Service Layer Updates
```python
# app/services/d5e_data_service.py (Enhanced)
from typing import List, Optional, Dict, Any
from app.repositories.d5e.repository_factory import D5eRepositoryFactory
from app.models.d5e.spells import SpellModel
from app.models.d5e.monsters import MonsterModel
from app.models.game_state import GameStateModel

class EnhancedContentService:
    """Enhanced content service using database repositories."""
    
    def __init__(self, repo_factory: D5eRepositoryFactory):
        self.repo_factory = repo_factory
    
    def get_spells_for_character(
        self, 
        character_class: str, 
        level: int,
        content_pack_priority: List[str]
    ) -> List[SpellModel]:
        """Get all spells available to a character class up to a given level."""
        all_spells = []
        
        for spell_level in range(level + 1):  # 0 to character level
            spells = self.repo_factory.spells.find_by_level(
                spell_level, 
                content_pack_priority
            )
            
            # Filter by class
            class_spells = [
                spell for spell in spells 
                if character_class in spell.classes
            ]
            
            all_spells.extend(class_spells)
        
        return sorted(all_spells, key=lambda s: (s.level, s.name))
    
    def get_monsters_by_challenge_rating(
        self, 
        min_cr: str, 
        max_cr: str,
        content_pack_priority: List[str]
    ) -> List[MonsterModel]:
        """Get monsters within a challenge rating range."""
        return self.repo_factory.monsters.find_by_challenge_rating_range(
            min_cr, max_cr, content_pack_priority
        )
    
    def search_content(
        self, 
        query: str, 
        content_types: List[str],
        content_pack_priority: List[str]
    ) -> Dict[str, List]:
        """Search across multiple content types."""
        results = {}
        
        if 'spells' in content_types:
            results['spells'] = self.repo_factory.spells.search_by_text(
                query, content_pack_priority
            )
        
        if 'monsters' in content_types:
            results['monsters'] = self.repo_factory.monsters.search_by_text(
                query, content_pack_priority
            )
        
        if 'equipment' in content_types:
            results['equipment'] = self.repo_factory.equipment.search_by_text(
                query, content_pack_priority
            )
        
        return results
    
    def get_content_pack_priority_for_game_state(
        self, 
        game_state: GameStateModel
    ) -> List[str]:
        """Extract content pack priority from game state."""
        # This would be stored in the campaign instance JSON
        # For now, return default priority
        return ['dnd_5e_srd']  # Default to SRD only
```

### 9.3 Phase 3: RAG Integration (Week 3-4)

#### 9.3.1 Background Indexing Service
```python
# app/services/indexing_service.py
import asyncio
from typing import Optional
from app.services.rag.enhanced_rag_service import EnhancedRAGService
from app.repositories.d5e.repository_factory import D5eRepositoryFactory
from app.database.connection import DatabaseManager

class BackgroundIndexingService:
    """Service for background indexing of content into RAG system."""
    
    def __init__(
        self, 
        rag_service: EnhancedRAGService,
        repo_factory: D5eRepositoryFactory,
        db_manager: DatabaseManager
    ):
        self.rag_service = rag_service
        self.repo_factory = repo_factory
        self.db_manager = db_manager
        self._indexing_tasks = {}
    
    async def index_content_pack(self, content_pack_id: str) -> Dict[str, int]:
        """Index all content from a content pack into RAG system."""
        print(f"Starting indexing for content pack: {content_pack_id}")
        
        # Check if already indexing
        if content_pack_id in self._indexing_tasks:
            return {"error": "Already indexing this content pack"}
        
        try:
            # Create indexing task
            task = asyncio.create_task(
                self._do_indexing(content_pack_id)
            )
            self._indexing_tasks[content_pack_id] = task
            
            # Wait for completion
            result = await task
            
            print(f"Indexing complete for {content_pack_id}: {result}")
            return result
            
        finally:
            # Clean up task
            if content_pack_id in self._indexing_tasks:
                del self._indexing_tasks[content_pack_id]
    
    async def _do_indexing(self, content_pack_id: str) -> Dict[str, int]:
        """Perform the actual indexing work."""
        loop = asyncio.get_event_loop()
        
        # Run indexing in thread pool to avoid blocking
        return await loop.run_in_executor(
            None, 
            self.rag_service.index_content_from_database,
            content_pack_id
        )
    
    def is_indexing(self, content_pack_id: str) -> bool:
        """Check if a content pack is currently being indexed."""
        return content_pack_id in self._indexing_tasks
    
    def get_indexing_status(self) -> Dict[str, str]:
        """Get status of all indexing operations."""
        status = {}
        for content_pack_id, task in self._indexing_tasks.items():
            if task.done():
                if task.exception():
                    status[content_pack_id] = f"Error: {task.exception()}"
                else:
                    status[content_pack_id] = "Completed"
            else:
                status[content_pack_id] = "In Progress"
        
        return status
```

### 9.4 Phase 4: Content Manager UI (Week 4-5)

#### 9.4.1 Frontend API Routes
```python
# app/routes/content_routes.py
from flask import Blueprint, request, jsonify
from app.services.content_pack_service import ContentPackService
from app.services.indexing_service import BackgroundIndexingService
from app.core.container import get_service

content_bp = Blueprint('content', __name__, url_prefix='/api/content')

@content_bp.route('/packs', methods=['GET'])
def get_content_packs():
    """Get all available content packs."""
    content_service = get_service(ContentPackService)
    
    # Get system and user packs
    system_packs = content_service.get_system_content_packs()
    # user_packs = content_service.get_user_content_packs(user_id) # When auth is implemented
    
    return jsonify({
        'system_packs': [pack.model_dump() for pack in system_packs],
        'user_packs': []  # Empty for now
    })

@content_bp.route('/packs', methods=['POST'])
def create_content_pack():
    """Create a new content pack."""
    content_service = get_service(ContentPackService)
    
    data = request.get_json()
    
    try:
        pack = content_service.create_content_pack(
            display_name=data['display_name'],
            description=data.get('description', ''),
            author=data.get('author', ''),
            user_id=None  # Will be set when auth is implemented
        )
        
        return jsonify({
            'success': True,
            'content_pack': pack.model_dump()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@content_bp.route('/packs/<pack_id>/upload/<content_type>', methods=['POST'])
def upload_content():
    """Upload content to a content pack."""
    content_service = get_service(ContentPackService)
    indexing_service = get_service(BackgroundIndexingService)
    
    pack_id = request.view_args['pack_id']
    content_type = request.view_args['content_type']
    
    # Get JSON data from request
    if request.is_json:
        json_data = request.get_json()
        json_string = json.dumps(json_data)
    else:
        json_string = request.get_data(as_text=True)
    
    try:
        # Upload and validate content
        result = content_service.upload_content_from_json(
            pack_id, content_type, json_string
        )
        
        if result['success'] and result['successful_imports'] > 0:
            # Trigger background indexing
            asyncio.create_task(
                indexing_service.index_content_pack(pack_id)
            )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'details': {}
        }), 400

@content_bp.route('/packs/<pack_id>/activate', methods=['POST'])
def activate_content_pack():
    """Activate a content pack."""
    content_service = get_service(ContentPackService)
    pack_id = request.view_args['pack_id']
    
    success = content_service.activate_content_pack(pack_id)
    
    return jsonify({'success': success})

@content_bp.route('/search/<content_type>', methods=['GET'])
def search_content():
    """Search content across active packs."""
    content_service = get_service(EnhancedContentService)
    
    content_type = request.view_args['content_type']
    query = request.args.get('q', '')
    content_packs = request.args.getlist('packs') or ['dnd_5e_srd']
    
    try:
        results = d5e_service.search_content(
            query, [content_type], content_packs
        )
        
        return jsonify({
            'success': True,
            'results': results.get(content_type, []),
            'query': query
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

#### 9.4.2 Vue.js Content Manager Component
```vue
<!-- frontend/src/components/content/ContentManager.vue -->
<template>
  <div class="content-manager">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Content Manager</h1>
      <button 
        @click="showCreatePack = true"
        class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Create Content Pack
      </button>
    </div>

    <!-- Content Packs Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <ContentPackCard
        v-for="pack in contentPacks"
        :key="pack.id"
        :pack="pack"
        @activate="activatePack"
        @deactivate="deactivatePack"
        @upload="showUploadModal"
      />
    </div>

    <!-- Create Pack Modal -->
    <CreatePackModal
      v-if="showCreatePack"
      @close="showCreatePack = false"
      @created="handlePackCreated"
    />

    <!-- Upload Content Modal -->
    <UploadContentModal
      v-if="uploadModal.show"
      :pack-id="uploadModal.packId"
      :pack-name="uploadModal.packName"
      @close="uploadModal.show = false"
      @uploaded="handleContentUploaded"
    />

    <!-- Search Interface -->
    <ContentSearchInterface
      :available-packs="contentPacks.filter(p => p.is_active)"
      @search="handleSearch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ContentPackModel } from '@/types/unified'
import ContentPackCard from './ContentPackCard.vue'
import CreatePackModal from './CreatePackModal.vue'
import UploadContentModal from './UploadContentModal.vue'
import ContentSearchInterface from './ContentSearchInterface.vue'
import { contentApi } from '@/services/contentApi'

const contentPacks = ref<ContentPackModel[]>([])
const showCreatePack = ref(false)
const uploadModal = ref({
  show: false,
  packId: '',
  packName: ''
})

const loadContentPacks = async () => {
  try {
    const response = await contentApi.getContentPacks()
    contentPacks.value = [
      ...response.system_packs,
      ...response.user_packs
    ]
  } catch (error) {
    console.error('Failed to load content packs:', error)
  }
}

const activatePack = async (packId: string) => {
  try {
    await contentApi.activateContentPack(packId)
    await loadContentPacks() // Refresh
  } catch (error) {
    console.error('Failed to activate pack:', error)
  }
}

const deactivatePack = async (packId: string) => {
  try {
    await contentApi.deactivateContentPack(packId)
    await loadContentPacks() // Refresh
  } catch (error) {
    console.error('Failed to deactivate pack:', error)
  }
}

const showUploadModal = (pack: ContentPackModel) => {
  uploadModal.value = {
    show: true,
    packId: pack.id,
    packName: pack.display_name
  }
}

const handlePackCreated = (pack: ContentPackModel) => {
  contentPacks.value.push(pack)
  showCreatePack.value = false
}

const handleContentUploaded = (result: any) => {
  uploadModal.value.show = false
  // Show success/error message based on result
  console.log('Upload result:', result)
}

const handleSearch = async (searchParams: any) => {
  try {
    const results = await contentApi.searchContent(
      searchParams.contentType,
      searchParams.query,
      searchParams.activePacks
    )
    // Handle search results
    console.log('Search results:', results)
  } catch (error) {
    console.error('Search failed:', error)
  }
}

onMounted(() => {
  loadContentPacks()
})
</script>
```

## 10. Testing Strategy

### 10.1 Unit Tests for Repository Layer
```python
# tests/unit/test_spell_repository.py
import pytest
from unittest.mock import Mock, MagicMock
from app.repositories.d5e.spell_repository import SpellRepository
from app.models.d5e.spells import SpellModel
from app.database.models import Spell, ContentPack

class TestSpellRepository:
    
    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.session = Mock()
        return db
    
    @pytest.fixture
    def spell_repository(self, mock_db):
        return SpellRepository(mock_db)
    
    @pytest.fixture
    def sample_spell_data(self):
        return {
            'id': '1',
            'name': 'Fireball',
            'level': 3,
            'school': 'Evocation',
            'casting_time': '1 action',
            'range': '150 feet',
            'components': 'V, S, M',
            'duration': 'Instantaneous',
            'description': 'A bright streak flashes...',
            'classes': ['Wizard', 'Sorcerer'],
            'source': 'dnd_5e_srd'
        }
    
    def test_find_by_name_with_single_source(self, spell_repository, mock_db, sample_spell_data):
        # Arrange
        mock_spell = Mock(spec=Spell)
        for key, value in sample_spell_data.items():
            setattr(mock_spell, key, value)
        
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_spell
        
        # Act
        result = spell_repository.find_by_name('Fireball', ['dnd_5e_srd'])
        
        # Assert
        assert result is not None
        assert result.name == 'Fireball'
        assert result.level == 3
        assert 'Wizard' in result.classes
    
    def test_find_by_name_with_priority_order(self, spell_repository, mock_db):
        # Test that content pack priority is respected
        # First source has no result, second source has result
        mock_db.session.query.return_value.filter.return_value.first.side_effect = [None, Mock()]
        
        result = spell_repository.find_by_name('Fireball', ['user_pack', 'dnd_5e_srd'])
        
        # Should have been called twice (once for each source)
        assert mock_db.session.query.return_value.filter.call_count == 2
    
    def test_find_by_level(self, spell_repository, mock_db, sample_spell_data):
        # Test finding spells by level
        mock_spells = [Mock(spec=Spell) for _ in range(3)]
        for i, spell in enumerate(mock_spells):
            spell.name = f'Spell_{i}'
            spell.level = 3
            spell.source = 'dnd_5e_srd'
            # Set other required attributes...
        
        mock_db.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_spells
        
        results = spell_repository.find_by_level(3, ['dnd_5e_srd'])
        
        assert len(results) == 3
        for result in results:
            assert result.level == 3
    
    def test_create_spell_validation(self, spell_repository, mock_db, sample_spell_data):
        # Test creating a new spell
        spell_model = SpellModel.model_validate(sample_spell_data)
        
        # Mock content pack exists
        mock_content_pack = Mock(spec=ContentPack)
        mock_content_pack.id = 'user_pack'
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_content_pack
        
        # Mock no existing spell with same name
        mock_db.session.query.return_value.filter.return_value.first.side_effect = [mock_content_pack, None]
        
        result = spell_repository.create(spell_model, 'user_pack')
        
        # Verify session.add was called
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()
    
    def test_create_spell_duplicate_name_error(self, spell_repository, mock_db, sample_spell_data):
        # Test error when creating spell with duplicate name in same source
        spell_model = SpellModel.model_validate(sample_spell_data)
        
        # Mock content pack exists and spell with same name exists
        mock_content_pack = Mock(spec=ContentPack)
        mock_existing_spell = Mock(spec=Spell)
        mock_db.session.query.return_value.filter.return_value.first.side_effect = [mock_content_pack, mock_existing_spell]
        
        with pytest.raises(ValueError, match="already exists"):
            spell_repository.create(spell_model, 'user_pack')
```

### 10.2 Integration Tests
```python
# tests/integration/test_database_migration.py
import pytest
import tempfile
import json
from pathlib import Path
from app.database.connection import DatabaseManager
from scripts.migrate_json_to_db import JsonToDatabaseMigrator

class TestDatabaseMigration:
    
    @pytest.fixture
    def temp_db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_url = f'sqlite:///{f.name}'
        
        db_manager = DatabaseManager(db_url)
        db_manager.create_tables()
        
        yield db_manager
        
        # Cleanup
        db_manager.drop_tables()
    
    @pytest.fixture
    def sample_json_data(self):
        return {
            'spells': [
                {
                    'name': 'Test Spell',
                    'level': 1,
                    'school': 'Abjuration',
                    'casting_time': '1 action',
                    'range': '30 feet',
                    'components': 'V, S',
                    'duration': '1 minute',
                    'description': 'A test spell for unit testing.',
                    'classes': ['Wizard'],
                    'is_ritual': False,
                    'is_concentration': False
                }
            ]
        }
    
    @pytest.fixture
    def temp_json_file(self, sample_json_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_json_data, f, indent=2)
            temp_path = f.name
        
        yield Path(temp_path)
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_migration_creates_content_pack(self, temp_db, temp_json_file):
        migrator = JsonToDatabaseMigrator(temp_db)
        
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            json_dir = Path(temp_dir)
            spells_file = json_dir / '5e-SRD-Spells.json'
            
            # Copy our test file
            spells_file.write_text(temp_json_file.read_text())
            
            # Run migration
            migrator.migrate_5e_database(str(json_dir))
        
        # Verify content pack was created
        with temp_db.get_session() as session:
            from app.database.models import ContentPack
            content_pack = session.query(ContentPack).filter(
                ContentPack.id == 'dnd_5e_srd'
            ).first()
            
            assert content_pack is not None
            assert content_pack.display_name == 'D&D 5e SRD'
            assert content_pack.is_system is True
    
    def test_migration_creates_spells(self, temp_db, temp_json_file):
        migrator = JsonToDatabaseMigrator(temp_db)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            json_dir = Path(temp_dir)
            spells_file = json_dir / '5e-SRD-Spells.json'
            spells_file.write_text(temp_json_file.read_text())
            
            migrator.migrate_5e_database(str(json_dir))
        
        # Verify spells were created
        with temp_db.get_session() as session:
            from app.database.models import Spell
            spell = session.query(Spell).filter(
                Spell.name == 'Test Spell'
            ).first()
            
            assert spell is not None
            assert spell.level == 1
            assert spell.school == 'Abjuration'
            assert spell.source == 'dnd_5e_srd'
    
    def test_migration_stats_tracking(self, temp_db, temp_json_file):
        migrator = JsonToDatabaseMigrator(temp_db)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            json_dir = Path(temp_dir)
            spells_file = json_dir / '5e-SRD-Spells.json'
            spells_file.write_text(temp_json_file.read_text())
            
            migrator.migrate_5e_database(str(json_dir))
        
        # Check migration stats
        assert migrator.stats['content_packs'] == 1
        assert migrator.stats['spells'] == 1
        assert len(migrator.stats['errors']) == 0
```

### 10.3 Performance Tests
```python
# tests/performance/test_database_performance.py
import pytest
import time
from app.repositories.d5e.spell_repository import SpellRepository
from app.database.connection import DatabaseManager

class TestDatabasePerformance:
    
    @pytest.fixture(scope='session')
    def populated_db(self):
        # Create database with test data
        db_manager = DatabaseManager('sqlite:///:memory:')
        db_manager.create_tables()
        
        # Populate with test data (would use factory or fixtures)
        # ... population code ...
        
        return db_manager
    
    def test_spell_search_performance(self, populated_db):
        """Test that spell searches complete within reasonable time."""
        repo = SpellRepository(populated_db)
        
        start_time = time.time()
        
        # Perform search that would previously require loading all JSON files
        results = repo.find_by_level(3, ['dnd_5e_srd'])
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in well under 1 second
        assert duration < 1.0
        assert len(results) > 0
    
    def test_startup_time_improvement(self, populated_db):
        """Test that repository instantiation is fast."""
        start_time = time.time()
        
        # This should be fast - no JSON loading
        repo = SpellRepository(populated_db)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be nearly instantaneous
        assert duration < 0.1
```

## 11. Deployment Configuration

### 11.1 Environment Configuration
```bash
# .env.example
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/gamemaster
# DATABASE_URL=sqlite:///data/gamemaster.db  # Alternative for development

# RAG Configuration
CHROMADB_PERSIST_DIR=data/chromadb
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Debug Settings
SQL_DEBUG=false
CHROMADB_DEBUG=false

# Migration Settings
ENABLE_AUTO_MIGRATION=true
JSON_BACKUP_DIR=data/json_backup
```

### 11.2 Docker Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: gamemaster
      POSTGRES_USER: gamemaster
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    command: postgres -c shared_preload_libraries=vector

  app:
    build: .
    environment:
      DATABASE_URL: postgresql://gamemaster:password@postgres:5432/gamemaster
      CHROMADB_PERSIST_DIR: /app/data/chromadb
    volumes:
      - ./data:/app/data
      - ./saves:/app/saves  # Keep saves as files
    ports:
      - "5000:5000"
    depends_on:
      - postgres

  chromadb:
    image: chromadb/chroma:latest
    environment:
      CHROMA_SERVER_HOST: 0.0.0.0
    volumes:
      - chromadb_data:/chroma/chroma
    ports:
      - "8000:8000"

volumes:
  postgres_data:
  chromadb_data:
```

### 11.3 Production Deployment Script
```bash
#!/bin/bash
# deploy.sh

set -e

echo "Starting database migration deployment..."

# Backup existing JSON files
echo "Backing up existing JSON files..."
mkdir -p data/json_backup
cp -r knowledge/ data/json_backup/

# Set up database
echo "Setting up database..."
if [ "$DATABASE_URL" = "" ]; then
    export DATABASE_URL="sqlite:///data/gamemaster.db"
fi

# Run migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Migrate JSON data to database
echo "Migrating JSON data to database..."
python scripts/migrate_json_to_db.py

# Index content for RAG
echo "Indexing content for RAG system..."
python scripts/index_content_for_rag.py

# Run tests to verify migration
echo "Running migration verification tests..."
python -m pytest tests/integration/test_database_migration.py -v

echo "Migration deployment complete!"
echo "JSON backups stored in: data/json_backup/"
echo "Database ready at: $DATABASE_URL"
```

## 12. Rollback Strategy

### 12.1 Rollback Plan
```python
# scripts/rollback_to_json.py
"""
Rollback script to revert from database back to JSON files if needed.
"""

import json
from pathlib import Path
from app.database.connection import DatabaseManager
from app.repositories.d5e.repository_factory import D5eRepositoryFactory

class DatabaseToJsonRollback:
    """Rollback database content to JSON files."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repo_factory = D5eRepositoryFactory(db_manager)
    
    def rollback_to_json(self, output_dir: str = "knowledge_restored"):
        """Export all database content back to JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export each content type
        self._export_spells(output_path)
        self._export_monsters(output_path)
        self._export_equipment(output_path)
        # ... other content types
        
        print(f"Rollback complete. JSON files restored to: {output_path}")
    
    def _export_spells(self, output_path: Path):
        """Export spells to JSON file."""
        spells = self.repo_factory.spells.find_all(['dnd_5e_srd'])
        
        spells_data = []
        for spell in spells:
            spells_data.append(spell.model_dump())
        
        output_file = output_path / '5e-SRD-Spells.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(spells_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(spells_data)} spells to {output_file}")

if __name__ == "__main__":
    db_manager = DatabaseManager()
    rollback = DatabaseToJsonRollback(db_manager)
    rollback.rollback_to_json()
```

## 13. Success Criteria and Validation

### 13.1 Performance Benchmarks
- **Startup Time**: < 5 seconds (down from 30-60 seconds)
- **Test Suite**: < 30 seconds (down from 1 minute)
- **Query Response**: < 100ms for typical searches
- **Memory Usage**: < 50% of current usage

### 13.2 Functional Requirements
- ✅ All existing D&D content accessible via new system
- ✅ Content pack priority system working
- ✅ Custom content upload and validation
- ✅ RAG system performance improved
- ✅ Save system unchanged and working
- ✅ Type safety maintained (mypy --strict passes)

### 13.3 Validation Tests
```python
# tests/integration/test_migration_validation.py
def test_content_completeness():
    """Verify all JSON content was migrated successfully."""
    # Compare counts of items in JSON vs database
    pass

def test_content_accuracy():
    """Verify migrated content matches original JSON."""
    # Spot check specific items for accuracy
    pass

def test_performance_improvements():
    """Verify performance targets are met."""
    # Measure startup times, query times, etc.
    pass

def test_backward_compatibility():
    """Verify existing save files still work."""
    # Load existing game saves and verify they work
    pass
```

This comprehensive specification provides your contractor with all the details needed to implement the database migration successfully. The hybrid approach maintains the flexibility of your current system while gaining the performance and scalability benefits of a proper database architecture.