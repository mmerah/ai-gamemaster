# Content Module

The `app/content/` module is a comprehensive, domain-driven subsystem that encapsulates all D&D 5e content management functionality for the AI Game Master application. This module provides a clean, isolated interface for accessing, managing, and searching D&D 5e game content.

## Overview

This module consolidates all content-related functionality that was previously scattered across the codebase:
- Database models and connections
- Content repositories (spells, monsters, equipment, etc.)
- RAG (Retrieval-Augmented Generation) system for semantic search
- Database migration scripts
- Content indexing and vector search capabilities

## Architecture

```
app/content/
├── __init__.py              # Module exports
├── service.py               # ContentService - main facade/interface
├── connection.py            # DatabaseManager for SQLite connections
├── models.py               # SQLAlchemy ORM models
├── types.py                # Type definitions (Vector types, etc.)
│
├── alembic/                # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/           # Migration scripts
│
├── data/                   # Static data files
│   ├── 5e-database/        # Git submodule with D&D 5e SRD data
│   └── knowledge/          # Additional knowledge bases
│       └── lore/
│
├── rag/                    # RAG system for semantic search
│   ├── __init__.py
│   ├── rag_service.py      # RAGService
│   ├── knowledge_base.py   # In-memory vector store manager
│   ├── db_knowledge_base_manager.py  # Database-backed knowledge base
│   ├── d5e_knowledge_base_manager.py # D5e-specific knowledge manager
│   ├── d5e_document_converters.py    # Convert D5e data to documents
│   └── query_engine.py     # Query analysis and generation
│
├── repositories/           # Data access layer
│   ├── __init__.py
│   ├── base_repository.py  # Abstract base repository
│   ├── db_base_repository.py # Database-aware base repository
│   ├── spell_repository.py
│   ├── monster_repository.py
│   ├── equipment_repository.py
│   ├── class_repository.py
│   ├── generic_repository.py
│   └── hub.py             # Repository hub/factory
│
├── schemas/               # Pydantic models for D&D 5e data
│   ├── __init__.py
│   ├── spell.py          # D5eSpell model
│   ├── monster.py        # D5eMonster model
│   ├── equipment.py      # D5eEquipment model
│   ├── character_class.py # D5eClass model
│   └── ... (20+ schema files)
│
└── scripts/              # Database management scripts
    ├── __init__.py
    ├── migrate_content.py     # Migrate JSON data to SQLite
    ├── migrate_content_v2.py  # Enhanced migration with robustness
    ├── verify_db.py          # Verify database integrity
    ├── index_for_rag.py      # Generate vector embeddings
    ├── update_srd_content.py # Update from 5e-database submodule
    ├── setup_test_database.py # Create test databases
    └── audit_sql_queries.py  # Security audit script
```

## Key Components

### ContentService (`service.py`)
The main facade that provides high-level operations for D&D 5e content:
- Character creation from templates
- Spell lookup and filtering
- Monster queries
- Equipment management
- Combat setup utilities
- Rules and mechanics lookup

### DatabaseManager (`connection.py`)
Manages SQLite database connections with:
- Connection pooling
- SQLite-vec extension for vector search
- WAL (Write-Ahead Logging) mode for concurrency
- Automatic pragma configuration

### Repository Pattern (`repositories/`)
Provides a clean abstraction over data access:
- Type-safe query methods
- Content pack support (for future custom content)
- Efficient caching of field mappings
- Pure domain model returns (no SQLAlchemy leakage)

### RAG System (`rag/`)
Implements semantic search capabilities:
- Comprehensive content indexing across all D&D 5e tables
- Vector similarity search using SQLite-vec
- Query understanding and intent analysis
- Campaign-specific knowledge support

Indexed content includes:
- **Core Content**: Spells, Monsters, Equipment, Classes, Races, Backgrounds
- **Character Features**: Features, Feats, Traits, Subclasses, Subraces, Levels
- **Game Mechanics**: Rules, Rule Sections, Conditions, Skills, Proficiencies
- **Reference Data**: Damage Types, Languages, Alignments, Ability Scores
- **Item Categories**: Equipment Categories, Magic Items, Magic Schools, Weapon Properties

### Database Migrations (`alembic/`)
Manages schema evolution:
- Automated migration generation
- Version tracking
- Rollback support
- Performance indexes

## Usage

### Basic Usage

```python
from app.core.container import get_container

# Get the ContentService
content_service = get_container().get_content_service()

# Look up a spell
fireball = content_service.get_spell_by_name("fireball")

# Get all spells of a specific level
level_3_spells = content_service.get_spells_by_level(3)

# Search for monsters by CR
cr_5_monsters = content_service.get_monsters_by_cr_range(5.0, 5.0)

# Create a character from a template
character = content_service.create_character_from_template(
    "fighter",
    name="Aragorn",
    level=5
)
```

### Database Migration

To populate the database with D&D 5e content:

```bash
# Run the migration script
python -m app.content.scripts.migrate_content

# Verify the migration
python -m app.content.scripts.verify_db

# Generate vector embeddings for RAG
python -m app.content.scripts.index_for_rag
```

### RAG Integration

The RAG system provides semantic search across all content:

```python
from app.core.container import get_container

rag_service = get_container().get_rag_service()
game_state = get_container().get_game_state_repo().get_game_state()

# Get relevant knowledge for a player action
results = rag_service.get_relevant_knowledge(
    "I cast fireball at the group of goblins",
    game_state
)

# Access the formatted context
context = results.format_for_prompt()
```

## Testing

The module includes comprehensive test coverage:

```bash
# Unit tests
pytest tests/unit/content/

# Integration tests
pytest tests/integration/content/

# Run with RAG enabled
python tests/run_all_tests.py --with-rag
```

## Configuration

Configuration is managed through environment variables and settings:

```python
# Database settings
DATABASE_URL = "sqlite:///data/content.db"
DATABASE_ECHO = False
SQLITE_BUSY_TIMEOUT = 5000

# RAG settings
RAG_ENABLED = True
RAG_EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RAG_CHUNK_SIZE = 1000
```

## Future Enhancements

The module is designed to support future features:
- **Content Packs**: User-created content that can override or extend base content
- **Multi-source Content**: Support for multiple game systems beyond D&D 5e
- **Advanced Search**: Natural language queries across all content
- **Content Versioning**: Track changes and allow rollbacks
- **Export/Import**: Share custom content between users

## Architecture Principles

This module follows key architectural principles:
- **Domain-Driven Design**: Organized around business concepts, not technical layers
- **Clean Architecture**: Clear boundaries and dependencies flow inward
- **Repository Pattern**: Abstraction over data access
- **Facade Pattern**: ContentService provides a simple interface to complex subsystems
- **Type Safety**: Full type annotations and mypy --strict compliance
- **Test-Driven Development**: Comprehensive test coverage

## Performance

The module is optimized for performance:
- Database indexes on commonly queried fields
- Vector embeddings pre-computed and stored
- Efficient SQL queries with proper parameterization
- Connection pooling and reuse
- WAL mode for concurrent access

## Security

Security is built-in:
- SQL injection prevention through parameterized queries
- Input validation using Pydantic models
- Whitelist-based table name validation
- No direct database access from external code