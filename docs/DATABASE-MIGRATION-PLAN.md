Excellent. This is a very well-structured and detailed specification. It provides a clear vision for the database migration. Based on your analysis and preferences, I will now construct the detailed implementation plan.

### Database Choice Justification

I agree with your assessment. The hybrid approach using **SQLite with the `sqlite-vec` extension** is the optimal choice for this project's current and foreseeable needs.

*   **Simplicity & Self-Hosting:** SQLite is a serverless, file-based database that requires zero configuration for the end-user. This perfectly aligns with the project's single-user, self-hosted model, providing total user control without the overhead of managing a separate database server process.
*   **Performance:** The primary performance bottleneck is the startup-time JSON parsing, which SQLite completely eliminates. For a single-user application, its read/write performance is more than sufficient.
*   **Integration:** As a built-in Python library, integration is seamless. SQLAlchemy provides a robust ORM that allows for easy future migration to a more powerful database like PostgreSQL if the project's needs evolve.
*   **Vector Search:** The `sqlite-vec` extension provides high-performance vector search capabilities directly within the SQLite database file. This simplifies the RAG architecture significantly by removing the need for a separate vector database like ChromaDB, reducing complexity and dependencies.
*   **Cost:** Both SQLite and `sqlite-vec` are open-source and free, aligning with the project's open-source nature.

This stack delivers the performance benefits of a database and the power of vector search while maintaining the simplicity and portability of a file-based system.

---
## 9. Migration Implementation Plan

This plan follows a Test-Driven Development (TDD) methodology, ensuring that each change is covered by tests and that the system remains stable throughout the migration. Each task concludes with the requirement that all existing tests pass (`python tests/run_all_tests.py --with-rag`), guaranteeing no regressions.

### Phase 1: Database Foundation & Core Setup (Week 1)

**Objective:** Establish the database connection, define the initial schema, and create a script to migrate existing JSON data.

---

#### **Task 1.1: Integrate SQLite and SQLAlchemy**

*   **Objective:** Set up the fundamental database connection and session management.
*   **Implementation Steps:**
    1.  Add `sqlalchemy`, `alembic`, and `sqlite-vec` to `requirements.txt`.
    2.  Create a new module `app/content/connection.py` to house a `DatabaseManager` class responsible for creating the SQLAlchemy engine and managing sessions. This will be configured via `app.config.py` to use a SQLite database file (e.g., `data/content.db`).
    3.  Update `app/core/container.py` to initialize and provide the `DatabaseManager` instance.
*   **Testing / Validation:**
    1.  Write a new unit test in `tests/unit/content/database/test_connection.py` to verify that `DatabaseManager` can successfully connect to an in-memory SQLite database.
    2.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 1.2: Define Core Database Models & Schema Migration**

*   **Objective:** Define the database schema using SQLAlchemy models and set up `Alembic` for managing schema migrations.
*   **Implementation Steps:**
    1.  Create `app/content/models.py` to define the SQLAlchemy ORM models corresponding to the tables in the specification (e.g., `ContentPack`, `Spell`, `Monster`). Use `JSONB`/`JSON` for flexible data fields and `VECTOR(768)` for embedding columns (conditionally based on DB dialect).
    2.  Initialize Alembic for database migrations: `alembic init app/content/alembic`.
    3.  Configure `app/content/alembic/env.py` to recognize the new SQLAlchemy models.
    4.  Generate the initial migration script: `alembic revision --autogenerate -m "Initial D&D content schema"`.
    5.  Review the generated migration script for accuracy.
*   **Testing / Validation:**
    1.  Write a new unit test that uses the `DatabaseManager` to create the full schema on a temporary SQLite database and then uses SQLAlchemy's `inspect` to verify that all tables and columns were created correctly.
    2.  Apply the migration to a test database: `alembic upgrade head`.
    3.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 1.3: Implement the Data Migration Script**

*   **Objective:** Create a standalone script to read data from the 25 `5e-database` JSON files and populate the newly defined database tables.
*   **Implementation Steps:**
    1.  Create `app/content/scripts/migrate_content.py`.
    2.  The script will accept a database URL as a command-line argument.
    3.  It will first create a "D&D 5e SRD" entry in the `content_packs` table.
    4.  It will then iterate through the JSON files, read their contents, and for each item:
        a. Validate the item against its corresponding Pydantic model (`D5eSpell`, `D5eMonster`, etc.).
        b. Create an instance of the SQLAlchemy model (`Spell`, `Monster`).
        c. Add the instance to a database session.
    5.  Commit the session to write all data to the database in a single transaction.
*   **Testing / Validation:**
    1.  Write a new integration test in `tests/integration/content/database/test_migration.py`. This test will:
        a. Create a fresh, temporary SQLite database.
        b. Run the migration script against it using a small subset of sample JSON data.
        c. Query the database to verify that the expected number of records were created and that a few specific records contain the correct data.
    2.  Ensure `python tests/run_all_tests.py --with-rag` passes.

### Phase 2: Repository Layer Refactoring (Week 2)

**Objective:** Refactor the existing D5e repositories to fetch data from the database instead of the JSON-based `IndexBuilder`, ensuring the service layer remains unaware of the underlying data source change.

---

#### **Task 2.1: Implement a DB-Aware Base Repository**

*   **Objective:** Create a new abstract base repository for database operations that supports content pack filtering.
*   **Implementation Steps:**
    1.  Create `app/content/repositories/db_base_repository.py`.
    2.  Define an abstract `BaseD5eDbRepository` that takes a `DatabaseManager` instance.
    3.  Implement common methods like `find_by_id` and a generic `_find_by_name` that incorporates content pack priority logic.
*   **Testing / Validation:**
    1.  Write unit tests for this new base repository using a mock database session and a simple test model to validate its generic logic.
    2.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 2.2: Refactor `SpellRepository`**

*   **Objective:** Modify the existing `SpellRepository` to inherit from the new DB base repository and use SQLAlchemy for data retrieval.
*   **Implementation Steps:**
    1.  Modify `app/content/repositories/spell_repository.py`.
    2.  Change its superclass to `BaseD5eDbRepository`.
    3.  Rewrite methods like `get_by_level`, `get_by_school`, and `get_by_class` to use SQLAlchemy queries against the `spells` table instead of the `IndexBuilder`.
    4.  The method signatures must remain identical to the old ones to avoid breaking the `ContentService`.
*   **Testing / Validation:**
    1.  **Adapt, do not delete,** the existing tests in `tests/unit/content/repositories/test_spell_repository.py`.
    2.  Modify the test setup to use a pre-populated test database instead of mocking the `IndexBuilder`.
    3.  Run the tests to ensure the new DB-backed implementation produces the exact same results as the old JSON-backed one. This validates the refactoring.
    4.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 2.3: Refactor All Other D5e Repositories**

*   **Objective:** Systematically refactor `MonsterRepository`, `EquipmentRepository`, `ClassRepository`, and all other generic repositories.
*   **Implementation Steps:**
    1.  For each repository, repeat the process from Task 2.2:
        a. Change the superclass.
        b. Replace `IndexBuilder` calls with SQLAlchemy queries.
        c. Ensure method signatures are unchanged.
*   **Testing / Validation:**
    1.  For each repository, adapt its existing unit tests to use a database fixture.
    2.  After refactoring each repository, run `python tests/run_all_tests.py --with-rag` to ensure no regressions have been introduced.

### Phase 3: Service & Container Integration (Week 3)

**Objective:** Update the application's service layer and dependency injection container to use the new database-backed repositories.

---

#### **Task 3.1: Update the DI Container**

*   **Objective:** Modify `app/core/container.py` to remove the old data loaders and provide the new `DatabaseManager` and DB-backed repositories.
*   **Implementation Steps:**
    1.  In `container.py`, remove the initialization of `D5eDataLoader`, `D5eIndexBuilder`, and `D5eReferenceResolver`.
    2.  Add initialization for the `DatabaseManager`.
    3.  Update the creation methods for the repositories (e.g., `_create_spell_repository`) to inject the `DatabaseManager` instead of the old dependencies.
*   **Testing / Validation:**
    1.  Update tests that rely on the container setup (e.g., `tests/unit/test_container.py`).
    2.  Write a new test to verify that `get_container().get_d5e_data_service()` now returns a service that uses a database session.
    3.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 3.2: Update the `ContentService`**

*   **Objective:** Ensure the `ContentService` works seamlessly with the new repositories.
*   **Implementation Steps:**
    1.  Review `app/content/service.py`. Due to the careful refactoring in Phase 2, minimal changes should be needed.
    2.  The primary change will be in its `__init__` method, which will now receive the DB-backed `D5eRepositoryHub`.
    3.  Remove any logic related to the old data loading system.
*   **Testing / Validation:**
    1.  Adapt existing tests for `ContentService` to use a database fixture. The service's public API should not have changed, so the tests should require minimal modification beyond the setup.
    2.  This is a critical integration point. A full pass of `python tests/run_all_tests.py --with-rag` is essential to confirm the application core is functioning correctly with the new data backend.

### Phase 4: RAG System Migration & Vector Search (Week 4)

**Objective:** Migrate the RAG system to use vector search capabilities within the SQLite database, improving search relevance and performance.

---

#### **Task 4.1: Integrate `sqlite-vec` and Update Schema**

*   **Objective:** Enable vector search in the SQLite database and add embedding columns to the content tables.
*   **Implementation Steps:**
    1.  Update `app/content/connection.py` to load the `sqlite-vec` extension when creating the SQLite engine.
    2.  In `app/content/models.py`, add `Column(VECTOR(768))` to the `spells`, `monsters`, and `equipment` tables. The number `768` corresponds to the dimension of the `all-MiniLM-L6-v2` embedding model.
    3.  Create a new Alembic migration to add these columns: `alembic revision --autogenerate -m "Add vector embedding columns"`.
*   **Testing / Validation:**
    1.  Write a new unit test in `tests/unit/content/database/test_connection.py` that:
        a. Creates a test table with a VECTOR column.
        b. Inserts two sample vectors.
        c. Performs a `vec_search` query and asserts that the correct nearest neighbor is returned.
    2.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 4.2: Implement Vector Indexing Script**

*   **Objective:** Create a script that populates the new vector embedding columns for all content.
*   **Implementation Steps:**
    1.  Create `app/content/scripts/index_for_rag.py`.
    2.  The script will connect to the database.
    3.  It will iterate through each row in the `spells`, `monsters`, etc., tables.
    4.  For each row, it will format the relevant text fields into a single string.
    5.  It will use `sentence-transformers` to generate an embedding for that string.
    6.  It will update the row, saving the generated vector into the `_embedding` column.
*   **Testing / Validation:**
    1.  Write an integration test that runs the indexing script on a small, populated test database.
    2.  Verify that the `_embedding` columns are populated and not NULL after the script runs.
    3.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 4.3: Refactor RAG Service for Vector Search**

*   **Objective:** Modify the `IRAGService` to perform vector similarity searches against the database instead of using an in-memory `InMemoryVectorStore`.
*   **Implementation Steps:**
    1.  Modify `app/content/rag/knowledge_base.py` and `app/content/rag/service.py`.
    2.  Remove all logic related to `InMemoryVectorStore` and `HuggingFaceEmbeddings` instantiation.
    3.  Rewrite the `search` method to execute a direct SQL query on the appropriate table using `vec_search` from `sqlite-vec`. The query will look like: `SELECT *, vec_distance_l2(embedding_column, :query_vector) AS distance FROM table ORDER BY distance LIMIT :k`.
*   **Testing / Validation:**
    1.  This is a critical step. The existing RAG integration tests (`tests/integration/content/rag/test_rag_enabled_integration.py`) must be run.
    2.  The tests will now implicitly use the new DB-backed RAG service. Their success will validate that the new system provides relevant context correctly.
    3.  Run `python tests/run_all_tests.py --with-rag` and ensure 100% pass rate.

Of course. This is an excellent and necessary addition. A content management system is crucial for expanding the application beyond the base SRD data and empowering users. Adding a new phase for this feature after the core database migration is the correct approach.

Here is the detailed specification for the new **Phase 5**, with the previous final phase renumbered to **Phase 6**.

---

### Phase 4.5: Production Readiness & Security Hardening (Week 5)

**Objective:** Address critical security, performance, and reliability issues identified in the migration review before proceeding with new features.

---

#### **Task 4.5.1: SQLite Concurrency and WAL Configuration**

*   **Objective:** Configure SQLite for optimal concurrent access and prevent database locking issues.
*   **Implementation Steps:**
    1.  Modify `app/content/connection.py` in the `_load_sqlite_vec_extension` method:
        a. After the `load_extension` event listener, add another event listener for SQLite pragma configuration.
        b. Execute `PRAGMA journal_mode=WAL` to enable Write-Ahead Logging mode.
        c. Execute `PRAGMA busy_timeout=5000` to set a 5-second timeout for lock acquisition.
        d. Execute `PRAGMA synchronous=NORMAL` for better performance while maintaining durability.
        e. Add logging to confirm pragma settings were applied.
    2.  Create a new method `_configure_sqlite_pragmas(self, engine: Engine) -> None` to encapsulate all SQLite-specific optimizations.
    3.  Update the `get_engine` method to call this new configuration method after engine creation.
    4.  Add a configuration option `SQLITE_BUSY_TIMEOUT` to make the timeout configurable via environment variables.
*   **Testing / Validation:**
    1.  Write a new test in `tests/unit/test_database_connection.py` that verifies:
        a. WAL mode is enabled on SQLite connections.
        b. Busy timeout is set correctly.
        c. Multiple concurrent readers can access the database.
    2.  Create an integration test that simulates concurrent writes and verifies no "database is locked" errors occur within the timeout period.
    3.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 4.5.2: Vector Search SQL Injection Prevention**

*   **Objective:** Secure all vector search queries against SQL injection attacks.
*   **Implementation Steps:**
    1.  In `app/content/rag/db_knowledge_base_manager.py`:
        a. Replace all string formatting in SQL queries with parameterized queries using SQLAlchemy's `text()` and `bindparams()`.
        b. In the `_vector_search_with_sqlite_vec` method, change the query construction to:
           ```python
           stmt = text("""
               SELECT *, vec_distance_l2(embedding, :query_vector) as distance
               FROM :table_name
               WHERE embedding IS NOT NULL
               ORDER BY distance
               LIMIT :limit
           """).bindparams(
               query_vector=query_embedding.tobytes(),
               table_name=table_name,
               limit=k
           )
           ```
        c. Create a helper method `_sanitize_table_name(self, table_name: str) -> str` that validates table names against a whitelist.
        d. Never use f-strings or string concatenation for any SQL query construction.
    2.  In `app/content/rag/d5e_db_knowledge_base_manager.py`:
        a. Apply the same parameterization to all queries.
        b. Use the same `_sanitize_table_name` method for table name validation.
    3.  Create a security audit script `app/content/scripts/audit_sql_queries.py` that uses regex to find potential SQL injection vulnerabilities.
*   **Testing / Validation:**
    1.  Write security tests in `tests/unit/test_rag_security.py` that attempt SQL injection with:
        a. Malicious query vectors containing SQL commands.
        b. Table names with SQL injection attempts.
        c. Limit parameters with non-numeric values.
    2.  All injection attempts should either raise exceptions or return empty results, never execute injected SQL.
    3.  Run the security audit script and ensure no vulnerabilities are found.

---

#### **Task 4.5.3: Database Performance Indexes**

*   **Objective:** Add missing indexes to optimize query performance.
*   **Implementation Steps:**
    1.  Create a new Alembic migration: `alembic revision --autogenerate -m "Add performance indexes"`
    2.  In the migration file, add the following indexes:
        ```python
        def upgrade():
            # Content pack foreign key indexes (for all 25 tables)
            for table in ['spells', 'monsters', 'equipment', 'classes', 'features', 
                         'backgrounds', 'races', 'feats', 'magic_items', ...]:
                op.create_index(f'idx_{table}_content_pack_id', table, ['content_pack_id'])
            
            # Spell-specific indexes
            op.create_index('idx_spells_level', 'spells', ['level'])
            op.create_index('idx_spells_school', 'spells', ['school'])
            op.create_index('idx_spells_ritual', 'spells', ['ritual'])
            op.create_index('idx_spells_concentration', 'spells', ['concentration'])
            
            # Monster-specific indexes
            op.create_index('idx_monsters_challenge_rating', 'monsters', ['challenge_rating'])
            op.create_index('idx_monsters_type', 'monsters', ['type'])
            op.create_index('idx_monsters_size', 'monsters', ['size'])
            
            # Equipment-specific indexes
            op.create_index('idx_equipment_equipment_category', 'equipment', ['equipment_category'])
            op.create_index('idx_equipment_weapon_category', 'equipment', ['weapon_category'])
            op.create_index('idx_equipment_armor_category', 'equipment', ['armor_category'])
            
            # Class-specific indexes
            op.create_index('idx_classes_hit_die', 'classes', ['hit_die'])
            
            # Feature-specific indexes
            op.create_index('idx_features_level', 'features', ['level'])
            op.create_index('idx_features_class_ref', 'features', ['class_ref'])
            
            # Name search indexes (for all tables with name column)
            for table in ['spells', 'monsters', 'equipment', ...]:
                op.create_index(f'idx_{table}_name_lower', table, [func.lower(column('name'))])
        ```
    3.  Apply the migration to the database.
    4.  Update `app/content/scripts/migrate_content.py` to create these indexes after initial data load.
*   **Testing / Validation:**
    1.  Create performance benchmarks in `tests/performance/test_query_performance.py`:
        a. Measure query time for common operations before and after indexes.
        b. Assert that indexed queries complete in under 50ms.
    2.  Use `EXPLAIN QUERY PLAN` to verify indexes are being used.
    3.  Ensure no performance regression in existing tests.

---

#### **Task 4.5.4: Migration Script Robustness**

*   **Objective:** Make the migration script fully transactional and idempotent.
*   **Implementation Steps:**
    1.  Modify `app/content/scripts/migrate_content.py`:
        a. Add a `--check-only` flag that reports migration status without making changes.
        b. Implement idempotency by checking existing records before insertion:
           ```python
           def migrate_file(self, filename: str, pydantic_class: Type[T], 
                          sqlalchemy_class: Type[S]) -> MigrationResult:
               # Check if already migrated
               existing_count = self.session.query(sqlalchemy_class).filter_by(
                   content_pack_id=self.content_pack_id
               ).count()
               
               if existing_count > 0:
                   return MigrationResult(
                       filename=filename,
                       status="skipped",
                       message=f"Already has {existing_count} records"
                   )
               
               # Load and validate data
               items = self.load_json_file(filename)
               validated_items = []
               errors = []
               
               for item in items:
                   try:
                       validated = pydantic_class(**item)
                       validated_items.append(validated)
                   except ValidationError as e:
                       errors.append(f"{item.get('index', 'unknown')}: {e}")
               
               # Single transaction for entire file
               try:
                   with self.session.begin_nested():  # Savepoint
                       for validated in validated_items:
                           entity = self.convert_to_entity(validated, sqlalchemy_class)
                           self.session.add(entity)
                       self.session.flush()  # Trigger any DB constraints
                       
                   return MigrationResult(
                       filename=filename,
                       status="success",
                       records_created=len(validated_items),
                       errors=errors
                   )
               except Exception as e:
                   return MigrationResult(
                       filename=filename,
                       status="failed",
                       message=str(e),
                       errors=errors
                   )
           ```
        c. Add comprehensive logging with structured output.
        d. Implement a `--rollback` option that removes all data for a content pack.
        e. Add progress bars using `tqdm` for better user experience.
    2.  Create a migration status table to track migration history:
        ```python
        class MigrationHistory(Base):
            __tablename__ = "migration_history"
            
            id = Column(Integer, primary_key=True)
            filename = Column(String(100), nullable=False)
            content_pack_id = Column(String(50), ForeignKey("content_packs.id"))
            status = Column(String(20), nullable=False)  # success, failed, partial
            records_count = Column(Integer)
            error_count = Column(Integer)
            started_at = Column(DateTime, nullable=False)
            completed_at = Column(DateTime)
            error_details = Column(JSON)
        ```
    3.  Implement automatic backup before migration starts.
*   **Testing / Validation:**
    1.  Write tests for idempotency:
        a. Run migration twice, verify no duplicates.
        b. Partially fail a migration, re-run, verify completion.
    2.  Test transaction rollback on various failure scenarios.
    3.  Verify migration history is accurately recorded.

---

#### **Task 4.5.5: Type Safety Enhancements**

*   **Objective:** Improve type annotations for vector operations and custom types.
*   **Implementation Steps:**
    1.  Create `app/content/types.py` with domain-specific type aliases:
        ```python
        from typing import TypeAlias
        from numpy.typing import NDArray
        import numpy as np
        
        # Vector types
        Vector: TypeAlias = NDArray[np.float32]
        OptionalVector: TypeAlias = Optional[Vector]
        
        # Dimension-specific vectors
        Vector384: TypeAlias = Annotated[Vector, Literal[384]]  # all-MiniLM-L6-v2
        Vector768: TypeAlias = Annotated[Vector, Literal[768]]  # sentence-transformers/all-mpnet-base-v2
        
        # Repository return types
        EntityResult: TypeAlias = Optional[TModel]
        EntityList: TypeAlias = List[TModel]
        EntityPage: TypeAlias = Tuple[List[TModel], int]  # (items, total_count)
        ```
    2.  Update all vector-related type hints throughout the codebase:
        a. Replace `Optional[NDArray[np.float32]]` with `OptionalVector`.
        b. Replace `List[float]` for embeddings with `Vector`.
    3.  Update the VECTOR TypeDecorator in `app/content/models.py`:
        a. Add runtime dimension validation in `process_bind_param`.
        b. Improve error messages with expected vs actual dimensions.
    4.  Create custom mypy plugin for vector dimension checking (optional but recommended).
*   **Testing / Validation:**
    1.  Run `mypy app --strict` and ensure 0 errors.
    2.  Write type tests using `typing_extensions.assert_type`.
    3.  Verify vector dimension mismatches raise clear errors.

---

#### **Task 4.5.6: Configuration Management Refactor**

*   **Objective:** Replace dict/object hybrid configuration with Pydantic settings.
*   **Implementation Steps:**
    1.  Create `app/settings.py` using pydantic-settings:
        ```python
        from pydantic_settings import BaseSettings, SettingsConfigDict
        
        class DatabaseSettings(BaseSettings):
            model_config = SettingsConfigDict(env_prefix="DATABASE_")
            
            url: str = "sqlite:///data/content.db"
            echo: bool = False
            pool_size: int = 5
            pool_timeout: int = 30
            pool_recycle: int = 3600
            enable_sqlite_vec: bool = True
            sqlite_busy_timeout: int = 5000
            vector_dimension: int = 384
            
        class RAGSettings(BaseSettings):
            model_config = SettingsConfigDict(env_prefix="RAG_")
            
            enabled: bool = True
            embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
            chunk_size: int = 1000
            chunk_overlap: int = 200
            top_k: int = 5
            
        class Settings(BaseSettings):
            database: DatabaseSettings = DatabaseSettings()
            rag: RAGSettings = RAGSettings()
            # ... other settings groups
        ```
    2.  Update `app/config.py` to use the new settings:
        a. Create a singleton settings instance.
        b. Provide backward-compatible access methods.
    3.  Update ServiceContainer to use Settings instead of dict/ServiceConfigModel.
    4.  Update all configuration access throughout the codebase.
*   **Testing / Validation:**
    1.  Write tests that verify environment variable loading.
    2.  Test configuration validation and error messages.
    3.  Ensure backward compatibility with existing config usage.

---

#### **Task 4.5.7: Error Handling and Custom Exceptions**

*   **Objective:** Implement specific exception types for better error handling.
*   **Implementation Steps:**
    1.  Create `app/exceptions.py` with domain-specific exceptions:
        ```python
        class AIGameMasterError(Exception):
            """Base exception for all application errors."""
            
        class DatabaseError(AIGameMasterError):
            """Base class for database-related errors."""
            
        class ContentPackNotFoundError(DatabaseError):
            """Raised when a content pack doesn't exist."""
            def __init__(self, pack_id: str):
                super().__init__(f"Content pack '{pack_id}' not found")
                self.pack_id = pack_id
                
        class VectorSearchError(DatabaseError):
            """Raised when vector search fails."""
            
        class VectorDimensionError(VectorSearchError):
            """Raised when vector dimensions don't match."""
            def __init__(self, expected: int, actual: int):
                super().__init__(
                    f"Vector dimension mismatch: expected {expected}, got {actual}"
                )
                self.expected = expected
                self.actual = actual
                
        class MigrationError(DatabaseError):
            """Base class for migration errors."""
            
        class RepositoryError(AIGameMasterError):
            """Base class for repository errors."""
        ```
    2.  Update all repository methods to raise specific exceptions.
    3.  Update error handling in routes to return appropriate HTTP status codes.
    4.  Add exception logging with structured data.
*   **Testing / Validation:**
    1.  Write tests for each exception type.
    2.  Verify error messages are user-friendly.
    3.  Test API error responses have correct status codes.

---

#### **Task 4.5.8: Repository Pattern Purity**

*   **Objective:** Ensure repositories return domain models, not SQLAlchemy entities.
*   **Implementation Steps:**
    1.  Audit all repository return types:
        a. Verify they return Pydantic models (D5eSpell, etc.) not SQLAlchemy models.
        b. Update any methods that leak SQLAlchemy models.
    2.  Enhance `_entity_to_model` method in BaseD5eDbRepository:
        a. Add caching for field mappings to improve performance.
        b. Handle lazy-loaded relationships explicitly.
        c. Add option to include/exclude related entities.
    3.  Create integration tests that verify no SQLAlchemy objects escape repositories.
    4.  Update repository interfaces to use explicit return types.
*   **Testing / Validation:**
    1.  Write tests that verify return types are Pydantic models.
    2.  Test that accessing repository results outside session context works.
    3.  Verify no lazy loading exceptions occur.

### Phase 5: Content Manager & Custom Content API (Week 6-7)

**Note on Model Design Decision (Phase 5.6)**: After careful consideration, we've decided to maintain string references for D&D 5e content in our models rather than switching to ID-based references. This approach:
- Maintains backward compatibility with existing saves
- Avoids complex data migrations
- Simplifies the codebase by avoiding duplicate DTOs
- Still provides type safety through validation and TypeScript enums

Instead of changing the storage format, we'll add comprehensive validation to ensure all string references point to valid D&D 5e content. This pragmatic approach balances type safety with maintainability.

**Objective:** Build the backend API and frontend UI for managing content packs. This will allow users to view system content, create their own content packs, and upload custom data (spells, monsters, etc.) in JSON format. This phase builds upon the new database architecture.

---

#### **Task 5.1: Backend - Content Pack Management API**

*   **Objective:** Create API endpoints for creating, listing, activating/deactivating, and uploading content to content packs.
*   **Implementation Steps:**
    1.  Create `app/services/content_pack_service.py` to handle the business logic for managing `ContentPack` entities in the database.
    2.  Create `app/api/content_routes.py` and define the following endpoints:
        *   `GET /api/content/packs`: Lists all available content packs, distinguishing between system packs (e.g., 'dnd_5e_srd') and user-created packs.
        *   `POST /api/content/packs`: Creates a new, empty content pack for a user. Request body will contain `display_name`, `description`, etc.
        *   `POST /api/content/packs/<pack_id>/activate`: Sets the `is_active` flag for a content pack to `true`.
        *   `POST /api/content/packs/<pack_id>/deactivate`: Sets `is_active` to `false`. System packs cannot be deactivated.
        *   `POST /api/content/packs/<pack_id>/upload/<content_type>`: This is the core upload endpoint.
            *   It will accept a JSON payload.
            *   The `content_type` URL parameter will specify the type of content (e.g., 'spells', 'monsters').
            *   The service will parse the JSON, validate each item against the corresponding Pydantic model (`D5eSpell`, `D5eMonster`, etc.), and insert valid items into the database, linking them to the `pack_id`.
            *   It will return a summary of the upload (e.g., items succeeded, items failed with validation errors).
    3.  Create `app/services/indexing_service.py` to handle background tasks. Upon successful content upload, this service will be triggered to generate and save vector embeddings for the new content.
*   **Testing / Validation:**
    1.  Create `tests/integration/test_content_api.py`.
    2.  Write tests for each new endpoint:
        *   Test creating a content pack and verifying it appears in the `GET /api/content/packs` list.
        *   Test uploading a valid `spells.json` file to the new pack and verifying the spells are in the database with the correct `source`.
        *   Test uploading a JSON file with invalid spell data and assert that the API returns a `422 Unprocessable Entity` error with detailed validation messages.
        *   Test activating and deactivating a user-created pack.
    3.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 5.2: Backend - Integrate Content Pack Priority**

*   **Objective:** Modify the repository layer and services to respect the new content pack system, allowing user content to override system content.
*   **Implementation Steps:**
    1.  Update the `CampaignInstanceModel` in `app/models/campaign.py` to include a new field: `content_pack_priority: List[str]`. This list will store the IDs of the content packs active for that specific campaign, in order of precedence.
    2.  Modify the `BaseD5eDbRepository` and its concrete implementations (e.g., `SpellRepository`). Update methods like `find_by_name` and `find_all` to accept a `content_pack_priority: List[str]` argument.
    3.  The `find_by_name` implementation must now iterate through the `content_pack_priority` list and return the *first* match found. This ensures that a user's custom "Fireball" spell is found before the SRD "Fireball" if the user's pack has higher priority.
    4.  Update the `ContentService` methods to accept and pass down the `content_pack_priority` list to the repositories.
    5.  The `GameOrchestrator` will be responsible for retrieving the priority list from the active `CampaignInstanceModel` and passing it to the `ContentService`.
*   **Testing / Validation:**
    1.  In `tests/unit/content/repositories/test_spell_repository.py`, create a test scenario with a test database containing two versions of "Fireball": one from `dnd_5e_srd` and one from a `user_homebrew` pack.
    2.  Assert that `find_by_name('Fireball', ['user_homebrew', 'dnd_5e_srd'])` returns the homebrew version.
    3.  Assert that `find_by_name('Fireball', ['dnd_5e_srd'])` returns the SRD version.
    4.  Assert that `find_by_name('Magic Missile', ['user_homebrew', 'dnd_5e_srd'])` (where Magic Missile only exists in SRD) successfully falls back and returns the SRD version.
    5.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

#### **Task 5.3: Frontend - Content Manager UI Components**

*   **Objective:** Create the Vue components for the Content Manager UI.
*   **Implementation Steps:**
    1.  Create a new view component: `frontend/src/views/ContentManagerView.vue`. This will be the main page for content management.
    2.  Create a `frontend/src/components/content/` directory.
    3.  Inside, create `ContentPackCard.vue` to display information for a single content pack, including its name, description, status (active/inactive), and action buttons (Activate, Upload, Delete).
    4.  Create `CreatePackModal.vue`: A modal form with fields for `display_name`, `description`, and `author`.
    5.  Create `UploadContentModal.vue`: A modal that allows the user to select a `content_type` (Spells, Monsters, etc.) from a dropdown and provides a file input for JSON files. Include a textarea as a fallback for pasting JSON content directly. Add clear instructions and a link to a data format example.
*   **Testing / Validation:**
    1.  Manual testing: Navigate to the new `/content` route. Verify all components render correctly with mock data.
    2.  Verify that modals open and close as expected and that forms have basic validation (e.g., required fields).

---

#### **Task 5.4: Frontend - API Integration and State Management**

*   **Objective:** Connect the new UI components to the backend API via a new Pinia store.
*   **Implementation Steps:**
    1.  Create `frontend/src/services/contentApi.ts` to encapsulate all API calls to the new `/api/content/*` endpoints.
    2.  Create `frontend/src/stores/contentStore.ts`. This store will manage the state of content packs, handle loading, creating, and updating them by calling the `contentApi`.
    3.  In `ContentManagerView.vue`, use the `contentStore` to fetch and display the list of content packs.
    4.  Connect the buttons on `ContentPackCard.vue` to actions in the `contentStore` (e.g., `activatePack(packId)`).
    5.  Wire up the `CreatePackModal.vue` and `UploadContentModal.vue` to call the appropriate `contentApi` methods and update the store upon success.
*   **Testing / Validation:**
    1.  **End-to-End Test:**
        a. Navigate to the Content Manager.
        b. Create a new content pack. Verify it appears in the list.
        c. Upload a valid JSON file of custom spells to the new pack. Verify a success message is shown.
        d. Activate the pack.
        e. Start a new campaign instance, ensuring this new content pack is selected with high priority.
        f. In the game, ask the AI about one of the custom spells and verify it provides the correct, custom description, not the SRD one.
    2.  Ensure `python tests/run_all_tests.py --with-rag` passes.

---

### Phase 5.6: Type System Refactoring & State Management Cleanup (Week 7)

**Objective:** Consolidate duplicate D&D 5e models, improve frontend type safety by consistently using generated types, and simplify frontend state management by removing duplicated responsibilities from gameStore.

---

#### **Task 5.6.1: Consolidate Duplicate D&D 5e Models**

*   **Objective:** Remove duplicate D&D 5e entity models from `app/models/utils.py` and ensure all D&D 5e schemas are contained within `app/content/schemas/`.
*   **Implementation Steps:**
    1.  Review duplicate models in `app/models/utils.py`:
        a. `D5EClassModel` (lines 100-118) - This duplicates `D5eClass` from content schemas
        b. `ArmorModel` (lines 120-140) - This should be part of equipment schemas
    2.  Update any references to these models:
        a. Search for all usages of `D5EClassModel` and `ArmorModel` in the codebase
        b. Replace them with the canonical versions from `app/content/schemas/`
        c. If they're not used, simply delete them
    3.  Evaluate game-specific models that have D&D 5e aspects:
        a. Keep `BaseStatsModel`, `ProficienciesModel`, `TraitModel`, `ClassFeatureModel` in `app/models/utils.py` as they represent runtime character state
        b. Document that these are runtime models, not static D&D 5e definitions
    4.  Verify content module independence:
        a. Run `grep -r "from app.models" app/content/` to ensure only appropriate imports exist
        b. The only allowed imports should be for RAG-related models and `GameStateModel`
*   **Testing / Validation:**
    1.  Run `mypy app --strict` to ensure no type errors after removal
    2.  Run `python tests/run_all_tests.py --with-rag` to verify no functionality is broken
    3.  Verify that the TypeScript generation still works correctly

---

#### **Task 5.6.2: Improve Frontend Type Safety**

*   **Objective:** Consistently use generated TypeScript types from `unified.ts` throughout the frontend, replacing any remaining `any` types or custom type definitions.
*   **Implementation Steps:**
    1.  Audit frontend stores for type safety gaps:
        a. Search for `any` type usage: `grep -r ": any" frontend/src/`
        b. Identify where generated types from `unified.ts` should be used instead
        c. Focus on stores that handle backend data: `campaignStore`, `contentStore`, `partyStore`
    2.  Update stores to use proper types:
        a. Import specific types from `@/types/unified` instead of using `any`
        b. Ensure all API responses are properly typed with generated interfaces
        c. Update method signatures to return specific types, not generic objects
    3.  Update API service files:
        a. Review all files in `frontend/src/services/`
        b. Ensure all API methods have proper return types using generated interfaces
        c. Remove any type assertions or casts that bypass type safety
    4.  Create type guards for runtime validation:
        ```typescript
        // frontend/src/utils/typeGuards.ts
        export function isD5eSpell(obj: unknown): obj is D5eSpell {
          return typeof obj === 'object' && obj !== null && 
                 'level' in obj && 'school' in obj;
        }
        ```
*   **Testing / Validation:**
    1.  Run `npm run type-check --prefix frontend` - must pass with 0 errors
    2.  Verify VS Code IntelliSense provides proper autocomplete
    3.  Test that type errors are caught at compile time, not runtime
    4.  Ensure all existing functionality continues to work

---

#### **Task 5.6.3: Simplify Frontend State Management**

*   **Objective:** Remove duplicate state from `gameStore` and ensure each store has a single, clear responsibility.
*   **Implementation Steps:**
    1.  Audit `gameStore.ts` for duplicate state:
        a. Identify state that exists in both `gameStore` and specialized stores
        b. List: `chatHistory` (duplicate of `chatStore`), `party` (duplicate of `partyStore`), 
           `combatState` (duplicate of `combatStore`), `diceRequests` (duplicate of `diceStore`)
    2.  Remove duplicate state from `gameStore`:
        a. Delete the duplicate state properties
        b. Update any methods that referenced the duplicate state to use the specialized stores
        c. Keep only campaign-specific state: `campaignId`, `campaignName`, `location`, `mapState`, `gameSettings`
    3.  Update components to use the correct stores:
        a. Search for all components using `gameStore.chatHistory` and update to use `chatStore.messages`
        b. Update party-related components to use `partyStore` directly
        c. Update combat components to use `combatStore` directly
        d. Update dice components to use `diceStore` directly
    4.  Ensure `eventRouter` remains the single point of SSE event handling:
        a. Verify all stores register their event handlers with `eventRouter`
        b. Remove any direct SSE handling from individual stores
        c. Document the event flow in comments
*   **Testing / Validation:**
    1.  Test all UI components to ensure they display data correctly
    2.  Verify SSE events update the correct stores
    3.  Check Vue DevTools to confirm no duplicate state exists
    4.  Run all frontend tests to ensure no regressions

---

#### **Task 5.6.4: Enhance TypeScript Generation Process**

*   **Objective:** Improve the TypeScript generation script to provide better developer experience and include helpful metadata.
*   **Implementation Steps:**
    1.  Enhance `scripts/dev/generate_ts.py`:
        a. The header already includes timestamp and warning - ensure it's prominent
        b. Add a comment block listing all included models by category
        c. Generate content type constants from backend:
           ```typescript
           // Generated from backend CONTENT_TYPE_TO_MODEL
           export const CONTENT_TYPES = {
             SPELLS: 'spells',
             MONSTERS: 'monsters',
             // ... etc
           } as const;
           ```
        d. Add JSDoc comments to complex interfaces explaining their purpose
    2.  Create a validation script:
        a. Create `scripts/dev/validate_types.py` that checks for:
           - Duplicate model names across different modules
           - Models referenced but not included in generation
           - Circular dependencies
        b. Run this as part of the generation process
    3.  Add type generation to pre-commit hooks:
        a. Create a git pre-commit hook that warns if Python models changed without regenerating TypeScript
        b. Document this in the developer guide
    4.  Update developer documentation:
        a. Add section to CLAUDE.md about type generation workflow
        b. Document when to run the generation script
*   **Testing / Validation:**
    1.  Run the enhanced generation script and verify output
    2.  Test that the validation script catches intentional errors
    3.  Verify pre-commit hook works correctly
    4.  Ensure generated types compile without errors

---

#### **Task 5.6.5: Create Backend Model Documentation**

*   **Objective:** Document the backend model architecture to clarify the distinction between runtime models and D&D 5e content schemas.
*   **Implementation Steps:**
    1.  Create `docs/BACKEND-MODELS.md`:
        a. Document the separation between `app/models/` (runtime) and `app/content/schemas/` (D&D 5e)
        b. Explain the purpose of each model file:
           - Runtime models: game state, characters, campaigns, combat
           - Content schemas: static D&D 5e definitions
        c. Document the model relationships and dependencies
        d. Include diagrams showing data flow
    2.  Add docstrings to key models:
        a. Add class-level docstrings explaining the purpose of each model
        b. Document important fields that might be confusing
        c. Explain the difference between Template and Instance models
    3.  Document the DTO pattern:
        a. Explain why `CombinedCharacterModel` exists as a DTO
        b. Document where DTOs are created (API layer)
        c. Show examples of proper DTO usage
    4.  Create model usage guidelines:
        a. When to create new models vs extending existing ones
        b. Naming conventions for models
        c. How to properly version models for API compatibility
*   **Testing / Validation:**
    1.  Technical review of documentation accuracy
    2.  Verify all models are documented
    3.  Test that examples in documentation work correctly
    4.  Ensure documentation helps new developers understand the architecture

---

#### **Task 5.6.6: Performance and Code Quality Improvements**

*   **Objective:** Optimize the type system and state management for better performance and maintainability.
*   **Implementation Steps:**
    1.  Optimize frontend store performance:
        a. Add computed properties to stores for derived state instead of recalculating
        b. Implement proper memoization for expensive operations
        c. Use `shallowRef` for large arrays of D&D 5e data that don't need deep reactivity
        d. Profile and optimize any performance bottlenecks
    2.  Improve error handling:
        a. Create typed error classes for different failure scenarios
        b. Ensure all API errors are properly typed and handled
        c. Add error boundaries in Vue components
        d. Implement proper error logging
    3.  Add development tools:
        a. Create a debug mode that logs all state changes
        b. Add store inspection tools for development
        c. Create performance monitoring for store updates
        d. Add automated checks for common issues
    4.  Code quality improvements:
        a. Remove any remaining `console.log` statements
        b. Ensure all promises have proper error handling
        c. Add missing type annotations where needed
        d. Remove dead code and unused imports
*   **Testing / Validation:**
    1.  Run performance profiling before and after optimizations
    2.  Verify error handling works correctly in various failure scenarios
    3.  Test development tools don't affect production build
    4.  Ensure all code quality metrics pass (linting, type checking)

---

### Phase 6: Architecture Consistency & Clean Code (Revised)

**Objective:** Improve architecture consistency by standardizing patterns, splitting large services, and organizing models for better maintainability and testability.

---

## Phase 6.1: Core Refactoring (Week 1)

### Task 6.1.1: Repository Pattern Standardization

**Objective:** Create consistent repository interfaces and standardize naming across all repositories.

**Context for Junior Engineers:**
- Repositories abstract data access logic from business logic
- Using protocols/interfaces allows easy mocking in tests
- Consistent naming makes the codebase more navigable

**Implementation Steps:**

1. **Create Repository Protocols**
   - Create `app/core/protocols/repositories.py`:
   ```python
   from typing import Protocol, Optional, List
   from app.models.campaign import CampaignTemplateModel, CampaignInstanceModel
   from app.models.character import CharacterTemplateModel, CharacterInstanceModel
   
   class CampaignTemplateRepositoryProtocol(Protocol):
       """Interface for campaign template data access"""
       def get_template(self, template_id: str) -> Optional[CampaignTemplateModel]: ...
       def save_template(self, template: CampaignTemplateModel) -> bool: ...
       def list_templates(self) -> List[CampaignTemplateModel]: ...
   
   class CampaignInstanceRepositoryProtocol(Protocol):
       """Interface for campaign instance data access"""
       def get_instance(self, instance_id: str) -> Optional[CampaignInstanceModel]: ...
       def save_instance(self, instance: CampaignInstanceModel) -> bool: ...
       def list_instances_for_template(self, template_id: str) -> List[CampaignInstanceModel]: ...
   
   class CharacterTemplateRepositoryProtocol(Protocol):
       """Interface for character template data access"""
       def get_template(self, template_id: str) -> Optional[CharacterTemplateModel]: ...
       def save_template(self, template: CharacterTemplateModel) -> bool: ...
       def list_templates_for_campaign(self, campaign_id: str) -> List[CharacterTemplateModel]: ...
   ```

2. **Standardize Repository Names**
   - Find all files with `repo` suffix: `grep -r "class.*Repo[^s]" app/`
   - Rename to use full `Repository` suffix:
     - `game_state_repo.py` → `game_state_repository.py`
     - Update all imports: `from app.repositories.game_state_repo` → `from app.repositories.game_state_repository`
   - Update class names to match file names

3. **Update Container to Use Protocols**
   - In `app/core/container.py`, update factory methods:
   ```python
   def _create_campaign_template_repository(self) -> CampaignTemplateRepositoryProtocol:
       # Implementation returns concrete class but typed as protocol
       return FileBasedCampaignTemplateRepository(self.config)
   ```

**Testing / Validation:**
1. Create unit tests that mock repositories using protocols
2. Run `mypy app --strict` to ensure all type annotations are correct
3. Run all tests to ensure no regressions
4. Use IDE "Find Usages" to verify all imports updated

---

### Task 6.1.2: Create CampaignFactory

**Objective:** Extract campaign creation logic from CampaignService into a dedicated factory.

**Context for Junior Engineers:**
- Factories encapsulate complex object creation logic
- This matches the existing CharacterFactory pattern
- Makes testing easier by isolating creation logic

**Implementation Steps:**

1. **Create the Factory Class**
   - Create `app/domain/campaigns/factories.py`:
   ```python
   from typing import Optional
   from app.models.campaign import CampaignTemplateModel, CampaignInstanceModel
   from app.models.game_state import GameStateModel
   from app.content.service import ContentService
   from app.domain.characters.factories import CharacterFactory
   
   class CampaignFactory:
       """Factory for creating campaign instances and initial game states"""
       
       def __init__(self, content_service: ContentService, character_factory: CharacterFactory):
           self.content_service = content_service
           self.character_factory = character_factory
       
       def create_campaign_instance(
           self, 
           template: CampaignTemplateModel,
           instance_name: Optional[str] = None
       ) -> CampaignInstanceModel:
           """Create a campaign instance from a template"""
           # Move logic from CampaignService._template_to_campaign_instance()
           instance = CampaignInstanceModel(
               id=self._generate_id(),
               name=instance_name or f"{template.name} Campaign",
               template_id=template.id,
               created_at=datetime.now(timezone.utc),
               # Copy relevant fields from template
               content_pack_priority=template.content_pack_priority or ["dnd_5e_srd"],
               rules_summary=template.rules_summary,
               safety_tools=template.safety_tools,
               allowed_classes=template.allowed_classes,
               allowed_races=template.allowed_races
           )
           return instance
       
       def create_initial_game_state(
           self,
           campaign_instance: CampaignInstanceModel,
           party_size: int = 4
       ) -> GameStateModel:
           """Create initial game state for a new campaign"""
           # Move logic from CampaignService
           game_state = GameStateModel(
               id=self._generate_id(),
               campaign_id=campaign_instance.id,
               name=campaign_instance.name,
               location="The beginning of your adventure",
               quests=[],
               npcs=[],
               session_number=1,
               # Initialize other fields
           )
           return game_state
   ```

2. **Refactor CampaignService**
   - Remove creation methods from `app/services/campaign_service.py`
   - Add factory as dependency:
   ```python
   def __init__(self, campaign_factory: CampaignFactory, ...):
       self.campaign_factory = campaign_factory
   
   def create_campaign_instance(self, template_id: str, name: Optional[str] = None) -> CampaignInstanceModel:
       """Create a new campaign instance"""
       template = self.template_repo.get_template(template_id)
       if not template:
           raise CampaignNotFoundError(template_id)
       
       # Delegate to factory
       instance = self.campaign_factory.create_campaign_instance(template, name)
       self.instance_repo.save_instance(instance)
       return instance
   ```

3. **Update ServiceContainer**
   - Add factory creation in `app/core/container.py`:
   ```python
   def _create_campaign_factory(self) -> CampaignFactory:
       return CampaignFactory(
           content_service=self.get_content_service(),
           character_factory=self.get_character_factory()
       )
   
   def _create_campaign_service(self) -> CampaignService:
       return CampaignService(
           campaign_factory=self._create_campaign_factory(),
           template_repo=self._create_campaign_template_repository(),
           instance_repo=self._create_campaign_instance_repository(),
           # ... other dependencies
       )
   ```

**Testing / Validation:**
1. Create unit tests for CampaignFactory methods
2. Update CampaignService tests to mock the factory
3. Run integration tests to ensure campaign creation still works
4. Verify no logic remains in CampaignService for creation

---

### Task 6.1.3: Split GameOrchestrator Service

**Objective:** Break down the large GameOrchestrator into focused, single-responsibility services.

**Context for Junior Engineers:**
- Large classes violate Single Responsibility Principle
- Smaller, focused services are easier to test and maintain
- Each service should handle one aspect of game orchestration

**Implementation Steps:**

1. **Analyze Current Responsibilities**
   - Review `app/services/game_orchestrator.py`
   - List all methods and group by functionality:
     - Combat orchestration methods
     - Narrative/chat orchestration methods  
     - Event routing/coordination methods

2. **Create Focused Services**
   
   a. **CombatOrchestrationService** (`app/services/orchestration/combat_orchestration_service.py`):
   ```python
   class CombatOrchestrationService:
       """Handles combat-specific game flow orchestration"""
       
       def __init__(self, combat_service: ICombatService, dice_service: DiceService, ...):
           self.combat_service = combat_service
           self.dice_service = dice_service
       
       async def handle_combat_action(self, action: CombatAction) -> CombatResult:
           """Process combat actions like attacks, spells, etc."""
           # Move combat-specific logic here
       
       async def handle_initiative_roll(self, combatants: List[str]) -> InitiativeResult:
           """Handle initiative rolling for combat start"""
           # Move initiative logic here
   ```
   
   b. **NarrativeOrchestrationService** (`app/services/orchestration/narrative_orchestration_service.py`):
   ```python
   class NarrativeOrchestrationService:
       """Handles narrative and chat flow orchestration"""
       
       def __init__(self, ai_service: AIServiceProtocol, chat_service: IChatService, ...):
           self.ai_service = ai_service
           self.chat_service = chat_service
       
       async def handle_player_message(self, message: str, context: GameContext) -> NarrativeResponse:
           """Process player messages and generate AI responses"""
           # Move chat/narrative logic here
       
       async def handle_scene_description(self, scene_data: SceneData) -> str:
           """Generate scene descriptions using AI"""
           # Move scene description logic here
   ```
   
   c. **EventRoutingService** (`app/services/orchestration/event_routing_service.py`):
   ```python
   class EventRoutingService:
       """Routes game events to appropriate handlers"""
       
       def __init__(self, event_handlers: Dict[str, EventHandler]):
           self.event_handlers = event_handlers
       
       async def route_event(self, event: GameEvent) -> None:
           """Route events to appropriate handlers"""
           handler = self.event_handlers.get(event.type)
           if handler:
               await handler.handle(event)
   ```

3. **Update GameOrchestrator to Coordinate**
   - Keep GameOrchestrator as a thin coordination layer:
   ```python
   class GameOrchestrator:
       """Coordinates between specialized orchestration services"""
       
       def __init__(
           self,
           combat_orchestration: CombatOrchestrationService,
           narrative_orchestration: NarrativeOrchestrationService,
           event_routing: EventRoutingService
       ):
           self.combat = combat_orchestration
           self.narrative = narrative_orchestration
           self.events = event_routing
       
       async def handle_action(self, action: GameAction) -> GameResponse:
           """Route actions to appropriate orchestration service"""
           if action.type in COMBAT_ACTIONS:
               return await self.combat.handle_combat_action(action)
           elif action.type in NARRATIVE_ACTIONS:
               return await self.narrative.handle_player_message(action)
           # etc.
   ```

4. **Update Imports and Container**
   - Update all imports from `game_orchestrator` to specific services
   - Update ServiceContainer to create all new services
   - Ensure dependency injection works correctly

**Testing / Validation:**
1. Create unit tests for each new orchestration service
2. Verify GameOrchestrator tests still pass after refactoring
3. Run integration tests to ensure game flow works correctly
4. Check that each service has a focused set of responsibilities

---

## Phase 6.2: Model & Event Improvements (Week 2)

### Task 6.2.1: Model Reorganization

**Objective:** Split large model files into logical sub-packages for better organization.

**Context for Junior Engineers:**
- Large files are hard to navigate and maintain
- Logical grouping makes finding models easier
- Reduces import conflicts and circular dependencies

**Implementation Steps:**

1. **Create Sub-Package Structure**
   ```bash
   # Create new directory structure
   mkdir -p app/models/character
   mkdir -p app/models/combat
   mkdir -p app/models/campaign
   mkdir -p app/models/game
   
   # Add __init__.py files to make them packages
   touch app/models/character/__init__.py
   touch app/models/combat/__init__.py
   touch app/models/campaign/__init__.py
   touch app/models/game/__init__.py
   ```

2. **Split character.py**
   - Move models to separate files:
     - `app/models/character/template.py`: CharacterTemplateModel
     - `app/models/character/instance.py`: CharacterInstanceModel  
     - `app/models/character/combined.py`: CombinedCharacterModel (DTO)
     - `app/models/character/data.py`: CharacterData, InitialCharacterData
   
   - Update `app/models/character/__init__.py`:
   ```python
   """Character models for the AI Game Master"""
   from .template import CharacterTemplateModel
   from .instance import CharacterInstanceModel
   from .combined import CombinedCharacterModel
   from .data import CharacterData, InitialCharacterData
   
   __all__ = [
       "CharacterTemplateModel",
       "CharacterInstanceModel", 
       "CombinedCharacterModel",
       "CharacterData",
       "InitialCharacterData"
   ]
   ```

3. **Split Other Large Files Similarly**
   - Apply same pattern to:
     - `combat.py` → `combat/` sub-package
     - `game_state.py` → `game/` sub-package
     - `campaign.py` → `campaign/` sub-package

4. **Update Imports Throughout Codebase**
   - Use IDE refactoring tools or:
   ```bash
   # Find all imports of old models
   grep -r "from app.models.character import" app/ tests/
   
   # Update to new structure
   # Old: from app.models.character import CharacterTemplateModel
   # New: from app.models.character.template import CharacterTemplateModel
   # Or:  from app.models.character import CharacterTemplateModel (if re-exported)
   ```

5. **Maintain Backward Compatibility**
   - Keep old model files temporarily with deprecation warnings:
   ```python
   # app/models/character.py
   import warnings
   warnings.warn(
       "Importing from app.models.character is deprecated. "
       "Use app.models.character.template, etc. instead",
       DeprecationWarning,
       stacklevel=2
   )
   from app.models.character import *  # Re-export for compatibility
   ```

**Testing / Validation:**
1. Run `mypy app --strict` to ensure all imports resolve
2. Run all tests to ensure no import errors
3. Use IDE to find any missed import updates
4. Verify models still generate TypeScript correctly

---

### Task 6.2.2: Event System Refactoring

**Objective:** Introduce EventBus pattern and improve event organization.

**Context for Junior Engineers:**
- EventBus decouples event producers from consumers
- Makes adding new event handlers easier
- Improves testability by centralizing event flow

**Implementation Steps:**

1. **Create EventBus Implementation**
   - Create `app/core/event_bus.py`:
   ```python
   from typing import Dict, List, Type, Callable, Any
   from app.models.events import BaseGameEvent
   import asyncio
   import logging
   
   logger = logging.getLogger(__name__)
   
   EventHandler = Callable[[BaseGameEvent], asyncio.Future[None]]
   
   class EventBus:
       """Central event bus for game events"""
       
       def __init__(self):
           self._handlers: Dict[Type[BaseGameEvent], List[EventHandler]] = {}
           self._middleware: List[Callable] = []
       
       def subscribe(
           self, 
           event_type: Type[BaseGameEvent], 
           handler: EventHandler
       ) -> None:
           """Subscribe a handler to an event type"""
           if event_type not in self._handlers:
               self._handlers[event_type] = []
           self._handlers[event_type].append(handler)
           logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")
       
       async def publish(self, event: BaseGameEvent) -> None:
           """Publish an event to all subscribed handlers"""
           event_type = type(event)
           handlers = self._handlers.get(event_type, [])
           
           # Apply middleware
           for middleware in self._middleware:
               event = await middleware(event)
           
           # Execute handlers
           tasks = []
           for handler in handlers:
               task = asyncio.create_task(self._execute_handler(handler, event))
               tasks.append(task)
           
           # Wait for all handlers to complete
           if tasks:
               await asyncio.gather(*tasks, return_exceptions=True)
       
       async def _execute_handler(self, handler: EventHandler, event: BaseGameEvent) -> None:
           """Execute a single handler with error handling"""
           try:
               await handler(event)
           except Exception as e:
               logger.error(f"Error in handler {handler.__name__}: {e}", exc_info=True)
               # Don't propagate - other handlers should still run
   ```

2. **Categorize Events**
   - Create event sub-packages:
   ```bash
   mkdir -p app/models/events/domain
   mkdir -p app/models/events/application  
   mkdir -p app/models/events/integration
   ```
   
   - Move events to appropriate categories:
     - `domain/`: Core game events (CombatStartedEvent, CharacterCreatedEvent)
     - `application/`: App-level events (GameStateUpdatedEvent)
     - `integration/`: External events (TtsGeneratedEvent, AIResponseEvent)

3. **Convert Handlers to Use Composition**
   - Instead of inheritance from BaseEventHandler:
   ```python
   # Old approach (inheritance)
   class CombatEventHandler(BaseEventHandler):
       def handle_combat_started(self, event): ...
   
   # New approach (composition)
   class CombatEventHandlers:
       """Combat-related event handlers"""
       
       def __init__(self, combat_service: ICombatService, event_bus: EventBus):
           self.combat_service = combat_service
           self.event_bus = event_bus
           self._register_handlers()
       
       def _register_handlers(self):
           self.event_bus.subscribe(CombatStartedEvent, self.handle_combat_started)
           self.event_bus.subscribe(AttackEvent, self.handle_attack)
       
       async def handle_combat_started(self, event: CombatStartedEvent) -> None:
           """Handle combat started event"""
           # Implementation
       
       async def handle_attack(self, event: AttackEvent) -> None:
           """Handle attack event"""
           # Implementation
   ```

4. **Update ServiceContainer**
   - Create and inject EventBus:
   ```python
   def _create_event_bus(self) -> EventBus:
       return EventBus()
   
   def _create_event_handlers(self) -> None:
       """Create and register all event handlers"""
       event_bus = self.get_event_bus()
       
       # Create handler instances (they self-register)
       CombatEventHandlers(self.get_combat_service(), event_bus)
       NarrativeEventHandlers(self.get_narrative_service(), event_bus)
       # ... etc
   ```

**Testing / Validation:**
1. Create unit tests for EventBus functionality
2. Test event handler registration and execution
3. Verify all existing events still work
4. Test error isolation (one handler error doesn't affect others)

---

### Task 6.2.3: Create Additional Factories

**Objective:** Create factories for consistent object creation across domains.

**Context for Junior Engineers:**
- Factories centralize complex object creation
- Makes it easier to create valid test data
- Ensures consistent initialization logic

**Implementation Steps:**

1. **Create CombatFactory**
   - Create `app/domain/combat/factories.py`:
   ```python
   from typing import List, Optional
   from app.models.combat import CombatStateModel, CombatantModel, InitialCombatantData
   from app.models.character import CombinedCharacterModel
   from app.content.service import ContentService
   from app.services.dice_service import DiceService
   import uuid
   
   class CombatFactory:
       """Factory for creating combat-related objects"""
       
       def __init__(self, content_service: ContentService, dice_service: DiceService):
           self.content_service = content_service
           self.dice_service = dice_service
       
       def create_combat_state(
           self,
           combatants_data: List[InitialCombatantData],
           encounter_name: Optional[str] = None
       ) -> CombatStateModel:
           """Create a new combat state with combatants"""
           combatants = [
               self.create_combatant(data) for data in combatants_data
           ]
           
           return CombatStateModel(
               id=str(uuid.uuid4()),
               encounter_name=encounter_name or "Combat Encounter",
               combatants=combatants,
               current_turn=0,
               round_number=1,
               is_active=True
           )
       
       def create_combatant(self, data: InitialCombatantData) -> CombatantModel:
           """Create a combatant from initial data"""
           # Logic to create combatant with proper stats
           # Handle NPCs vs PCs differently
           # Roll initiative if not provided
           # Set up action economy
           pass
       
       def create_combatant_from_character(
           self, 
           character: CombinedCharacterModel
       ) -> CombatantModel:
           """Create a combatant from a character model"""
           # Convert character to combatant
           # Preserve all combat-relevant stats
           pass
   ```

2. **Create QuestFactory**
   - Create `app/domain/quests/factories.py`:
   ```python
   from typing import List, Optional
   from app.models.game_state import QuestModel, ObjectiveModel
   from datetime import datetime
   import uuid
   
   class QuestFactory:
       """Factory for creating quests and objectives"""
       
       def create_quest(
           self,
           name: str,
           description: str,
           quest_giver: Optional[str] = None,
           reward: Optional[str] = None,
           objectives: Optional[List[str]] = None
       ) -> QuestModel:
           """Create a new quest with objectives"""
           quest_objectives = []
           if objectives:
               quest_objectives = [
                   self.create_objective(obj_description)
                   for obj_description in objectives
               ]
           
           return QuestModel(
               id=str(uuid.uuid4()),
               name=name,
               description=description,
               quest_giver=quest_giver,
               status="active",
               objectives=quest_objectives,
               reward=reward,
               started_at=datetime.utcnow()
           )
       
       def create_objective(
           self,
           description: str,
           optional: bool = False
       ) -> ObjectiveModel:
           """Create a quest objective"""
           return ObjectiveModel(
               id=str(uuid.uuid4()),
               description=description,
               completed=False,
               optional=optional
           )
   ```

3. **Create NPCFactory**
   - Create `app/domain/npcs/factories.py`:
   ```python
   from typing import Optional, List, Dict
   from app.models.utils import NPCModel
   from app.content.service import ContentService
   import uuid
   
   class NPCFactory:
       """Factory for creating NPCs"""
       
       def __init__(self, content_service: ContentService):
           self.content_service = content_service
       
       def create_npc(
           self,
           name: str,
           race: str,
           role: str,
           description: Optional[str] = None,
           stat_block: Optional[str] = None,
           personality_traits: Optional[List[str]] = None,
           **kwargs
       ) -> NPCModel:
           """Create an NPC with consistent structure"""
           # Validate race exists in content
           if not self._validate_race(race):
               raise ValueError(f"Invalid race: {race}")
           
           return NPCModel(
               id=str(uuid.uuid4()),
               name=name,
               race=race,
               role=role,
               description=description or f"A {race} {role}",
               stat_block=stat_block,
               personality_traits=personality_traits or [],
               location="Unknown",
               relationship_to_party="neutral",
               **kwargs
           )
       
       def create_merchant(
           self,
           name: str,
           race: str,
           shop_type: str,
           inventory: List[str]
       ) -> NPCModel:
           """Create a merchant NPC"""
           return self.create_npc(
               name=name,
               race=race,
               role="merchant",
               description=f"A {race} {shop_type} merchant",
               shop_type=shop_type,
               inventory=inventory
           )
   ```

4. **Update ServiceContainer**
   - Add factory creation methods:
   ```python
   def _create_combat_factory(self) -> CombatFactory:
       return CombatFactory(
           content_service=self.get_content_service(),
           dice_service=self.get_dice_service()
       )
   
   def _create_quest_factory(self) -> QuestFactory:
       return QuestFactory()
   
   def _create_npc_factory(self) -> NPCFactory:
       return NPCFactory(
           content_service=self.get_content_service()
       )
   ```

**Testing / Validation:**
1. Create comprehensive unit tests for each factory
2. Test edge cases and validation logic
3. Verify factories create valid objects
4. Use factories in other tests for consistent test data

---

## Phase 6.3: Service & API Cleanup (Week 3)

### Task 6.3.1: State Processor Decomposition

**Objective:** Split the monolithic state processor into focused, single-responsibility processors.

**Context for Junior Engineers:**
- Large files violate KISS principle - harder to understand and maintain
- Each processor should handle one domain of state updates
- Common logic should be extracted to utilities

**Implementation Steps:**

1. **Analyze Current State Processor**
   - Review all 15 functions in `state_processors.py`
   - Group by responsibility (combat, inventory, quests, party)
   - Identify common patterns

2. **Create Domain-Specific Processors**
   ```python
   # app/domain/game_model/processors/combat_state_processor.py
   class CombatStateProcessor:
       """Handles combat-related state updates"""
       
       def process_combat_start(self, state: GameStateModel, update: CombatStartUpdateModel) -> None:
           # Move _add_combatants_to_state logic here
           pass
       
       def process_hp_change(self, state: GameStateModel, update: HPChangeUpdateModel) -> None:
           # Move apply_hp_change logic here
           pass
   ```

3. **Extract Common Utilities**
   - Create `app/domain/game_model/processors/utils.py`
   - Move shared functions like `_get_correlation_id`
   - Create helper functions for common patterns

**Testing / Validation:**
1. Ensure each processor has focused unit tests
2. Verify no functionality is lost during split
3. Check that each file is under 200 lines

---

### Task 6.3.2: API Route Consolidation (YAGNI)

**Objective:** Reduce the number of D&D 5e endpoints from 41 to ~10 flexible endpoints.

**Context for Junior Engineers:**
- Too many endpoints violate YAGNI - most aren't needed
- Query parameters provide flexibility without endpoint proliferation
- Reduces maintenance burden

**Implementation Steps:**

1. **Design Consolidated Endpoints**
   ```
   GET /api/d5e/content?type={type}&filter={filter}
   GET /api/d5e/content/{type}/{id}
   GET /api/d5e/search?q={query}&types={types}
   ```

2. **Move Filtering to Service Layer**
   - Add query parameter parsing to ContentService
   - Support flexible filtering without separate endpoints
   - Use a single endpoint with type parameter

3. **Deprecate Granular Endpoints**
   - Mark old endpoints as deprecated
   - Provide migration guide in API documentation
   - Remove after grace period

**Testing / Validation:**
1. Test all query parameter combinations
2. Ensure backward compatibility during transition
3. Verify performance isn't degraded

---

### Task 6.3.3: DRY Service Getters

**Objective:** Eliminate duplicate service getter functions across API routes.

**Context for Junior Engineers:**
- Copy-paste code violates DRY principle
- Centralized dependency injection is cleaner
- Reduces boilerplate in route files

**Implementation Steps:**

1. **Create Dependency Injection Decorator**
   ```python
   # app/api/dependencies.py
   from functools import wraps
   from typing import TypeVar, Type
   
   T = TypeVar('T')
   
   def inject_service(service_class: Type[T]):
       """Decorator to inject services into route handlers"""
       def decorator(func):
           @wraps(func)
           def wrapper(*args, **kwargs):
               container = get_container()
               service = container.get_service(service_class)
               return func(service, *args, **kwargs)
           return wrapper
       return decorator
   ```

2. **Update Route Handlers**
   ```python
   # Before
   def get_spells():
       service = get_d5e_service()
       return service.get_spells()
   
   # After
   @inject_service(ContentService)
   def get_spells(service: ContentService):
       return service.get_spells()
   ```

3. **Create Shared Error Handler**
   - Move `_handle_service_error` to `app/api/error_handlers.py`
   - Import and use in all route files
   - Remove duplicate implementations

**Testing / Validation:**
1. Test decorator with various service types
2. Ensure error handling works consistently
3. Verify no service getter functions remain

---

### Task 6.3.4: Response Processor Refactoring

**Objective:** Split the large response processor into focused processors.

**Context for Junior Engineers:**
- Single class handling multiple responsibilities violates SOLID
- Focused processors are easier to test and maintain
- Coordinator pattern keeps the flow clear

**Implementation Steps:**

1. **Extract Domain Processors**
   ```python
   # app/services/processors/narrative_processor.py
   class NarrativeProcessor:
       """Processes narrative and location updates"""
       def process_narrative(self, response: dict) -> NarrativeUpdate:
           pass
   
   # app/services/processors/combat_processor.py
   class CombatProcessor:
       """Processes combat-related responses"""
       def process_combat_action(self, response: dict) -> CombatUpdate:
           pass
   ```

2. **Keep Coordinator Thin**
   - Main processor only routes to sub-processors
   - No business logic in coordinator
   - Clear separation of concerns

**Testing / Validation:**
1. Unit test each processor independently
2. Integration test the coordinator flow
3. Verify all response types handled correctly

---

## Phase 6.4: Dependency & Architecture Simplification (Week 4)


### Task 6.4.1: Event System Simplification (YAGNI)

**Objective:** Remove unnecessary complexity from the event system.

**Context for Junior Engineers:**
- Not all events need complex handling
- Direct method calls are simpler for tightly coupled components
- Keep events only where decoupling adds value

**Implementation Steps:**

1. **Audit Event Usage**
   - List all events and their handlers
   - Identify which truly need decoupling
   - Mark candidates for simplification

2. **Convert to Direct Calls**
   - For tightly coupled components, use direct method calls
   - Remove unnecessary event classes
   - Keep events for cross-boundary communication

3. **Simplify Handler Pattern**
   - Remove `SharedHandlerStateModel` if not adding value
   - Use simple functions instead of classes where appropriate
   - Keep only essential abstraction

**Testing / Validation:**
1. Ensure all functionality preserved
2. Test that remaining events work correctly
3. Verify improved performance from direct calls

---

### Task 6.4.2: Base Handler Decomposition

**Objective:** Extract utilities from the large base handler class.

**Context for Junior Engineers:**
- Base classes shouldn't contain too much logic
- Utilities are more flexible than inheritance
- Composition over inheritance principle

**Implementation Steps:**

1. **Create Utility Modules**
   ```python
   # app/services/game_events/utils/handler_utils.py
   def validate_game_state(state: GameStateModel) -> None:
       """Common validation logic"""
       pass
   
   # app/services/game_events/utils/state_utils.py
   def update_character_hp(character: CharacterModel, change: int) -> None:
       """State manipulation helper"""
       pass
   ```

2. **Slim Down Base Handler**
   - Keep only abstract methods and minimal shared state
   - Move all logic to utilities
   - Use composition in concrete handlers

**Testing / Validation:**
1. Test utilities independently
2. Verify handlers still work correctly
3. Check base handler is under 100 lines

---


### Documentation for Junior Engineers

**Key Principles to Remember:**

1. **Single Responsibility**: Each class/service should do one thing well
2. **Dependency Injection**: Accept dependencies, don't create them
3. **Interface Segregation**: Depend on abstractions (protocols), not concrete classes
4. **Testability**: If it's hard to test, the design needs improvement
5. **Consistency**: Follow existing patterns in the codebase

**Common Pitfalls to Avoid:**

1. Don't put business logic in models - keep them as data structures
2. Don't create circular dependencies between services
3. Don't skip writing tests - they catch issues early
4. Don't ignore type hints - they prevent bugs

**Resources for Learning:**

1. Python Protocols: https://peps.python.org/pep-0544/
2. Factory Pattern: https://refactoring.guru/design-patterns/factory-method
3. Event-Driven Architecture: https://martinfowler.com/articles/201701-event-driven.html
4. SOLID Principles: https://realpython.com/solid-principles-python/
