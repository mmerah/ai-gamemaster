# Database Guide

This guide covers all database operations for the AI Game Master application.

## Overview

The AI Game Master uses SQLite to store D&D 5e content. The database (`data/content.db`) is tracked in git for a zero-setup experience - users can clone and play immediately without running migrations.

## Quick Reference

| Task | Command | When to Use |
|------|---------|-------------|
| Verify database | `python scripts/verify_migration.py` | After cloning or updates |
| Full regeneration | `python scripts/migrate_json_to_db.py` | Schema changes, major updates |
| Incremental update | `python scripts/update_srd_content.py` | Submodule updates (Phase 5) |

## Database Schema

The database contains 26 tables for D&D 5e content:

- **Content Management**: `content_packs` (metadata for content collections)
- **Character Options**: `character_classes`, `subclasses`, `races`, `subraces`, `backgrounds`, `feats`
- **Progression**: `levels`, `features`, `traits`
- **Equipment**: `equipment`, `magic_items`, `equipment_categories`, `weapon_properties`
- **Magic**: `spells`, `magic_schools`
- **Creatures**: `monsters`
- **Game Mechanics**: `ability_scores`, `skills`, `proficiencies`, `languages`, `alignments`, `conditions`, `damage_types`

All content tables have:
- Foreign key to `content_packs` table
- Unique constraint on `(index, content_pack_id)` for multi-pack support
- JSON columns for complex nested data
- Optional `embedding` column (VECTOR(768)) for semantic search

## Operations

### Initial Setup

The database is included with the repository. No setup needed!

If you need to regenerate from scratch:

```bash
# 1. Remove existing database
rm data/content.db

# 2. Ensure submodule is initialized
git submodule update --init --recursive

# 3. Run migration
python scripts/migrate_json_to_db.py

# 4. Verify success
python scripts/verify_migration.py
```

### Updating Content

#### When to Update

- **After updating 5e-database submodule** - New content or fixes
- **After modifying Pydantic models** - Data structure changes
- **After modifying SQLAlchemy models** - Schema changes
- **To add custom content packs** - Phase 5 feature

#### Method 1: Full Regeneration (Recommended)

Best for development and when schema changes:

```bash
# Update submodule to latest
git submodule update --remote knowledge/5e-database

# Regenerate database
rm data/content.db
python scripts/migrate_json_to_db.py

# Verify and commit
python scripts/verify_migration.py
git add data/content.db
git commit -m "chore: Update D&D 5e content database"
```

#### Method 2: Incremental Update (Future - Phase 5)

Preserves custom content packs:

```bash
# Update only SRD content
python scripts/update_srd_content.py
```

### Verification

Always verify after database operations:

```bash
python scripts/verify_migration.py
```

Expected output:
```
Content Pack: D&D 5e SRD (v1.0.0)

Record counts:
  Spells: 319
  Monsters: 334
  Equipment: 237
  Classes: 12
  Levels: 290
  Features: 407

Migration verified successfully!
```

## Troubleshooting

### Migration Fails

```bash
# Check error details
python scripts/migrate_json_to_db.py 2>&1 | tee migration.log

# Common fixes:
# 1. Pydantic validation errors - Update models in app/models/d5e/
# 2. Missing fields - Check JSON structure vs model definitions
# 3. Type mismatches - Update field types or add validators
```

### Database Corruption

```bash
# Restore from git
git checkout data/content.db

# Or regenerate
rm data/content.db
python scripts/migrate_json_to_db.py
```

### Git Conflicts on content.db

```bash
# Binary file conflicts - choose one version
git checkout --theirs data/content.db  # Use remote version
# OR
git checkout --ours data/content.db    # Keep local version
# OR
rm data/content.db && python scripts/migrate_json_to_db.py  # Regenerate
```

## Development Workflow

### Adding New D5e Content Types

1. Add Pydantic model in `app/models/d5e/`
2. Add SQLAlchemy model in `app/database/models.py`
3. Update migration script mapping in `migrate_json_to_db.py`
4. Regenerate database
5. Update TypeScript types: `python scripts/generate_typescript.py`

### Schema Changes

1. Modify SQLAlchemy models
2. Create Alembic migration: `alembic revision -m "Description"`
3. Regenerate database from JSON
4. Test thoroughly
5. Commit both migration and updated database

## Script Reference

### migrate_json_to_db.py
Full migration from 5e-database JSON files to SQLite.
- Creates content pack "D&D 5e SRD"
- Validates all data against Pydantic models
- Populates all 26 tables
- Handles model/JSON mismatches gracefully

### verify_migration.py
Verifies database integrity and content.
- Checks content pack exists
- Counts records in key tables
- Samples specific content (Fireball, Goblin, Fighter)
- Reports any issues

### update_srd_content.py
Incremental update for SRD content (Phase 5 feature).
- Preserves custom content packs
- Updates only SRD content
- Reports changes (added/updated/deleted)
- Safer for production use

### index_content_for_rag.py
Generates vector embeddings for semantic search.
- Uses sentence-transformers/all-MiniLM-L6-v2 model
- Creates 384-dimensional embeddings
- Only indexes tables used for RAG search
- Run after migration or content updates

## Vector Embeddings for RAG

### Overview

The database uses vector embeddings to enable semantic search through the RAG system. Not all tables have embeddings - only those that are semantically searched.

### Tables WITH Embeddings (75.7% coverage)

These tables are indexed for semantic search:
- **Core Game Content**: spells, monsters, equipment, magic_items, classes, features, backgrounds, races, feats, traits, conditions, skills
- **To Be Migrated**: rules, rule_sections (currently in JSON)

### Tables WITHOUT Embeddings (NULL)

These tables use direct lookups and don't need embeddings:
- **Reference Data**: ability_scores, alignments, damage_types, languages, magic_schools, proficiencies, weapon_properties
- **Hierarchical Data**: equipment_categories, levels, subclasses, subraces
- **System**: content_packs

### Rationale

1. **Performance**: Only indexing searchable content reduces vector search space
2. **Relevance**: Users search for "fire damage spells" not "what is STR?"
3. **Storage**: Saves ~1.7MB by not indexing reference tables
4. **Speed**: Faster indexing and search operations

### Indexing Process

```bash
# After migration, generate embeddings
python scripts/index_content_for_rag.py
```

## Performance Optimization

### Database Indexes

The database includes optimized indexes for common query patterns:

```bash
# Create performance indexes (one-time setup)
python scripts/optimize_database_indexes.py

# Show current index statistics
python scripts/optimize_database_indexes.py --stats

# Preview changes without applying
python scripts/optimize_database_indexes.py --dry-run
```

### Key Indexes

1. **Name Searches**: Case-insensitive name lookups
2. **Content Pack Filtering**: Active content pack joins
3. **Type-Specific Queries**:
   - Spells: level, school, concentration, ritual
   - Monsters: CR, size, type
   - Equipment: weapon/armor category, range
   - Classes: hit die
   - Features: level, class, subclass

### Performance Impact

- Name searches: 10-100x faster with indexes
- Level/CR filtering: Direct column indexes provide major speedup
- JSON field searches: Improved but consider PostgreSQL for better JSON support
- Content pack joins: Significantly faster with active status index

For detailed analysis, see [Database Index Analysis](DATABASE-INDEXES-ANALYSIS.md).

## Important Notes

- **File Size**: ~3.8MB - acceptable for git
- **Binary File**: Each version stored separately in git history
- **Performance**: Database queries are much faster than JSON parsing
- **Backup**: Original JSON files remain in submodule
- **Embeddings**: Only 75.7% of entries need embeddings for optimal performance

## Related Documentation

- [Database Migration Plan](DATABASE-MIGRATION-PLAN.md) - Technical implementation details
- [Database Migration Progress](DATABASE-MIGRATION-PROGRESS.md) - Project status
- [Architecture](ARCHITECTURE.md) - System design overview