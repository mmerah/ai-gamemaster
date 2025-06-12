# Database Migration Progress

This document tracks the implementation progress of migrating from JSON-based data storage to SQLite with sqlite-vec extension.

> 📖 **For migration instructions, see [DATABASE-MIGRATION-GUIDE.md](DATABASE-MIGRATION-GUIDE.md)**

## Current Status: Phase 1 Complete ✅

### Migration Overview
- **Approach**: SQLite with sqlite-vec extension for vector search
- **Scope**: Migrate D&D 5e ruleset data only (game saves remain JSON)
- **Timeline**: 7 weeks estimated
- **Methodology**: Test-Driven Development (TDD)

### Prerequisites Complete ✅
The 5e-database JSON integration (Phases 1-7) has been completed, providing:
- Comprehensive Pydantic models for all 25 data types
- Repository pattern implementation
- Service layer abstraction
- Full API exposure
- RAG system integration

This foundation will make the database migration smoother as all data models and interfaces are already defined.

## Implementation Phases

### Phase 1: Database Foundation & Core Setup (Week 1)
**Status**: ✅ Complete

#### Task 1.1: Integrate SQLite and SQLAlchemy ✅ COMPLETE
- [x] Add `sqlalchemy`, `alembic`, and `sqlite-vec` to `requirements.txt` (already present)
- [x] Create `app/database/connection.py` with `DatabaseManager` class
- [x] Configure SQLite database file location in `app/config.py`
- [x] Update `app/core/container.py` to initialize `DatabaseManager`
- [x] Write unit tests for database connection (13 tests passing)

#### Task 1.2: Define Core Database Models & Schema Migration ✅ COMPLETE
- [x] Create `app/database/models.py` with SQLAlchemy ORM models
- [x] Define tables: content_packs, spells, monsters, equipment, etc.
- [x] Initialize Alembic for migrations: `alembic init alembic`
- [x] Configure `alembic/env.py` for model recognition
- [x] Generate initial migration script
- [x] Write tests for schema creation

#### Task 1.3: Implement the Data Migration Script ✅ COMPLETE
- [x] Create `scripts/migrate_json_to_db.py`
- [x] Load data from 25 5e-database JSON files
- [x] Validate against existing Pydantic models
- [x] Populate database tables with "D&D 5e SRD" content pack
- [x] Write integration tests for migration process
- [x] Fix model mismatches between Pydantic models and JSON data:
  - Updated D5eBackground to use Choice instead of PersonalityChoice
  - Made SpellcastingInfo.count optional and added desc field
  - Added optional fields to D5eLevel for subclass levels
  - Added name computed field to D5eLevel
  - Made D5eMonster.desc handle both string and list formats
  - Updated D5eSubclass.spells to handle both string URLs and spell lists
- [x] Successfully migrated 2,317 items to the database

### Phase 2: Repository Layer Refactoring (Week 2)
**Status**: ⏳ Not Started

#### Task 2.1: Implement a DB-Aware Base Repository
- [ ] Create `app/repositories/d5e/db_base_repository.py`
- [ ] Implement content pack filtering logic
- [ ] Add common CRUD operations
- [ ] Write unit tests for base repository

#### Task 2.2: Refactor SpellRepository
- [ ] Modify to use SQLAlchemy queries instead of IndexBuilder
- [ ] Maintain existing method signatures for compatibility
- [ ] Adapt existing tests to use test database
- [ ] Ensure all tests pass

#### Task 2.3: Refactor All Other D5e Repositories
- [ ] MonsterRepository - CR filtering, type queries
- [ ] EquipmentRepository - category and property filtering
- [ ] ClassRepository - level progression queries
- [ ] All 25 generic repositories
- [ ] Update all repository tests

### Phase 3: Service & Container Integration (Week 3)
**Status**: ⏳ Not Started

#### Task 3.1: Update the DI Container
- [ ] Remove D5eDataLoader, D5eIndexBuilder, D5eReferenceResolver
- [ ] Add DatabaseManager initialization
- [ ] Update repository creation to use DatabaseManager
- [ ] Update container tests

#### Task 3.2: Update the D5eDataService
- [ ] Minimal changes needed (repository interfaces unchanged)
- [ ] Update initialization to receive DB-backed repositories
- [ ] Adapt service tests to use database fixture
- [ ] Full test suite validation

### Phase 4: RAG System Migration & Vector Search (Week 4)
**Status**: ⏳ Not Started

#### Task 4.1: Integrate sqlite-vec and Update Schema
- [ ] Update DatabaseManager to load sqlite-vec extension
- [ ] Add VECTOR(768) columns to content tables
- [ ] Create Alembic migration for vector columns
- [ ] Write tests for vector search functionality

#### Task 4.2: Implement Vector Indexing Script
- [ ] Create `scripts/index_content_for_rag.py`
- [ ] Generate embeddings using sentence-transformers
- [ ] Populate embedding columns for all content
- [ ] Write integration tests for indexing

#### Task 4.3: Refactor RAG Service for Vector Search
- [ ] Remove InMemoryVectorStore usage
- [ ] Implement direct SQL vector search queries
- [ ] Update search methods to use sqlite-vec
- [ ] Validate with existing RAG integration tests

### Phase 5: Content Manager & Custom Content API (Week 5-6)
**Status**: ⏳ Not Started

#### Task 5.1: Backend - Content Pack Management API
- [ ] Create `app/services/content_pack_service.py`
- [ ] Create `app/routes/content_routes.py` with endpoints:
  - GET /api/content/packs
  - POST /api/content/packs
  - POST /api/content/packs/{pack_id}/activate
  - POST /api/content/packs/{pack_id}/deactivate
  - POST /api/content/packs/{pack_id}/upload/{content_type}
- [ ] Create `app/services/indexing_service.py` for background tasks
- [ ] Write comprehensive API tests

#### Task 5.2: Backend - Integrate Content Pack Priority
- [ ] Update CampaignInstanceModel with content_pack_priority field
- [ ] Modify repositories to accept content pack priority
- [ ] Implement priority-based entity resolution
- [ ] Update D5eDataService to pass priority lists
- [ ] Write tests for priority system

#### Task 5.3: Frontend - Content Manager UI Components
- [ ] Create `ContentManagerView.vue`
- [ ] Create `ContentPackCard.vue`
- [ ] Create `CreatePackModal.vue`
- [ ] Create `UploadContentModal.vue`
- [ ] Manual UI testing

#### Task 5.4: Frontend - API Integration and State Management
- [ ] Create `contentApi.ts` service
- [ ] Create `contentStore.ts` Pinia store
- [ ] Wire up UI components to API
- [ ] End-to-end testing of content management flow

### Phase 6: Cleanup and Finalization (Week 7)
**Status**: ⏳ Not Started

#### Task 6.1: Code and Dependency Cleanup
- [ ] Delete old JSON loading code
- [ ] Remove 5e-database submodule reference
- [ ] Remove static JSON files from knowledge/
- [ ] Ensure all tests pass

#### Task 6.2: Documentation Update
- [ ] Update ARCHITECTURE.md with database diagram
- [ ] Update README.md with migration steps
- [ ] Update RAG-SYSTEM.md with vector search details
- [ ] Fresh install testing

## Testing Strategy

### Test Requirements
- All existing tests must continue to pass
- Each phase must maintain 100% backward compatibility
- Performance benchmarks for startup time improvement
- Load testing for concurrent database access

### Test Execution
```bash
# Run after each task completion
python tests/run_all_tests.py --with-rag

# Type checking
mypy app --strict

# Linting
ruff check .
ruff format .
```

## Risk Mitigation

| Risk | Mitigation Strategy | Status |
|------|-------------------|---------|
| Data loss during migration | Backup JSON files, test migration script thoroughly | Planned |
| Performance regression | Benchmark before/after, optimize queries | Planned |
| Breaking API changes | Maintain exact method signatures in repositories | Planned |
| Vector search accuracy | Compare results with current RAG system | Planned |

## Performance Targets

- **Startup Time**: < 1 second (from 30-60 seconds)
- **Memory Usage**: < 100MB (from ~1GB with all JSON loaded)
- **API Response**: < 50ms for cached queries
- **Vector Search**: < 100ms for semantic queries

## Daily Progress Log

### 2025-01-11
#### Task 1.1: SQLite and SQLAlchemy Integration ✅
#### Task 1.1: SQLite and SQLAlchemy Integration ✅
- Created `DatabaseManager` class following TDD approach
  - Handles SQLite and PostgreSQL connections
  - Lazy loading of engine and session factory
  - Context manager for automatic session management
  - Support for sqlite-vec extension loading
  - Thread-safe session creation
- Added database configuration to `Config` class and `ServiceConfigModel`
  - DATABASE_URL, DATABASE_ECHO, pool settings, ENABLE_SQLITE_VEC
- Integrated `DatabaseManager` into `ServiceContainer`
  - Added `get_database_manager()` method
  - Added `cleanup()` method for proper resource disposal
  - Handles both dict and ServiceConfigModel configurations
- Comprehensive test coverage:
  - 13 tests for DatabaseManager functionality
  - 7 tests for ServiceContainer integration
  - All tests passing with 100% type safety
- Quality checks passed:
  - mypy --strict: 0 errors
  - ruff: 0 errors
  - All code properly formatted

#### Environment Variable Documentation ✅
- Verified all environment variables from `app/config.py` are documented in `.env.example`
- Database configuration section properly documented with examples
- All RAG, TTS, and other service configurations present

#### Task 1.2: Define Core Database Models & Schema Migration ✅
- Created comprehensive SQLAlchemy models for all 25 D5e data types
  - Base content model with common fields (index, name, url, content_pack_id)
  - ContentPack model for managing content collections (SRD, homebrew, etc.)
  - All models use JSON columns for complex nested data structures
  - Proper foreign key relationships to content_packs table
  - Unique constraints on (index, content_pack_id) for multi-pack support
- Set up Alembic for database migrations
  - Configured to use DATABASE_URL environment variable
  - Generated initial migration with all 26 tables
  - env.py properly imports models and handles SQLite/PostgreSQL
- Comprehensive test coverage:
  - 7 tests for model creation and relationships
  - 4 tests for schema validation and migrations
  - All tests passing with proper type safety
- Fixed all SQLAlchemy 2.0 deprecation warnings
  - Using DeclarativeBase instead of declarative_base()
  - Using datetime.now(UTC) instead of datetime.utcnow()

#### Task 1.3: Implement the Data Migration Script ✅
- Created comprehensive migration script `scripts/migrate_json_to_db.py`
  - Supports all 25 D5e JSON file types
  - Maps Pydantic models to SQLAlchemy models
  - Handles field filtering for SQLAlchemy compatibility
  - Creates "D&D 5e SRD" content pack
- Fixed multiple Pydantic model mismatches with actual JSON data:
  - D5eBackground: Changed personality traits/ideals/bonds/flaws from PersonalityChoice to Choice
  - SpellcastingInfo: Made count optional, added desc field
  - D5eLevel: Made several fields optional for subclass levels, added computed name field
  - D5eMonster: Added field_validator to normalize desc field (string or list)
  - D5eSubclass: Made spells field accept both string URLs and spell lists
- Created comprehensive integration tests:
  - Test migration of individual file types
  - Test full migration process
  - Test schema integrity
  - All tests passing with proper type safety
- Successfully migrated all D5e data:
  - 319 Spells
  - 334 Monsters  
  - 237 Equipment items
  - 12 Classes
  - 290 Levels (class and subclass)
  - 407 Features
  - Plus all other content types
  - Total: 2,317 items migrated
- Created verification script to validate migration success
- All existing tests passing (588 passed, 1 fixed)

### Next Steps
- Phase 2: Repository Layer Refactoring
  - Implement DB-aware base repository
  - Refactor all D5e repositories to use database
  - Maintain backward compatibility

## Documentation

- **Database Guide**: See [DATABASE-GUIDE.md](DATABASE-GUIDE.md) for all database operations
- **Migration Plan**: See [DATABASE-MIGRATION-PLAN.md](DATABASE-MIGRATION-PLAN.md) for technical details

---

*This document will be updated daily during the implementation phase*