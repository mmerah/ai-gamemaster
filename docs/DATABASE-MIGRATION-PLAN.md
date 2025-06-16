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

*   **Objective:** Modify the `RAGService` to perform vector similarity searches against the database instead of using an in-memory `InMemoryVectorStore`.
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

### Phase 5.6: D&D 5e Type System Refactoring (Week 7)

**Objective:** Standardize and strengthen the D&D 5e type system across frontend and backend, eliminating naming inconsistencies and improving type safety.

---

#### **Task 5.6.1: Standardize Content Type Naming Convention**

*   **Objective:** Replace all underscore-based content types in frontend with hyphenated format to match backend.
*   **Implementation Steps:**
    1.  Update `frontend/src/types/content.ts`:
        a. Change the `ContentType` union to use hyphenated names (e.g., `'ability-scores'` instead of `'ability_scores'`).
        b. Update all type exports and interfaces to use the hyphenated convention.
    2.  Update content type conversions in `frontend/src/services/contentApi.ts`:
        a. Remove all `replace(/_/g, '-')` conversions since frontend will now use hyphens natively.
        b. Update method signatures to expect hyphenated content types.
    3.  Update `frontend/src/views/ContentPackDetailView.vue`:
        a. Remove line 388 that converts hyphens to underscores: `const frontendType = contentType.replace(/-/g, '_')`.
        b. Use the original hyphenated format from the backend: `_content_type: contentType`.
    4.  Update all frontend components that reference content types:
        a. `ContentCreationForm.vue` - update v-if conditions to use hyphenated names.
        b. `UploadContentModal.vue` - update dropdown options to use hyphenated names.
        c. Any other components that use content type strings.
    5.  Create a shared constant file `frontend/src/constants/contentTypes.ts`:
        ```typescript
        export const CONTENT_TYPES = {
          ABILITY_SCORES: 'ability-scores',
          ALIGNMENTS: 'alignments',
          BACKGROUNDS: 'backgrounds',
          // ... etc
        } as const;
        
        export type ContentType = typeof CONTENT_TYPES[keyof typeof CONTENT_TYPES];
        ```
*   **Testing / Validation:**
    1.  Write unit tests to verify content type consistency across the application.
    2.  Test all content management UI features to ensure they work with hyphenated names.
    3.  Verify that content upload, viewing, and filtering still function correctly.
    4.  Run `npm run type-check` in frontend to ensure no type errors.

---

#### **Task 5.6.2: Strengthen Frontend Type Safety for D5e Data**

*   **Objective:** Replace generic `any` types with proper D5e interfaces throughout the frontend.
*   **Implementation Steps:**
    1.  Update `frontend/src/stores/campaignStore.ts`:
        a. Import specific D5e types from `types/unified.ts`:
           ```typescript
           import type { D5eRace, D5eClass, D5eBackground } from '@/types/unified';
           ```
        b. Replace generic interfaces with proper types:
           ```typescript
           const d5eRaces = ref<D5eRace[]>([]);
           const d5eClasses = ref<D5eClass[]>([]);
           const d5eBackgrounds = ref<D5eBackground[]>([]);
           ```
        c. Update method return types to use specific D5e interfaces.
    2.  Update `frontend/src/composables/useD5eData.ts`:
        a. Import all necessary D5e types.
        b. Add proper type parameters to functions:
           ```typescript
           export function useD5eData() {
             const findRaceByIndex = (index: string): D5eRace | undefined => {
               return campaignStore.d5eRaces.find(r => r.index === index);
             };
             
             const findClassByIndex = (index: string): D5eClass | undefined => {
               return campaignStore.d5eClasses.find(c => c.index === index);
             };
             // ... etc
           }
           ```
    3.  Update `frontend/src/services/campaignApi.ts`:
        a. Import D5e types and use them in return type annotations:
           ```typescript
           export async function getD5eRaces(): Promise<D5eRace[]> {
             const response = await apiClient.get<D5eRace[]>('/api/d5e/races');
             return response.data;
           }
           ```
    4.  Update components that use D5e data to expect proper types instead of `any`.
*   **Testing / Validation:**
    1.  Run `npm run type-check` to ensure all type changes are valid.
    2.  Write type tests using TypeScript's type assertion capabilities.
    3.  Verify autocomplete and IntelliSense work properly in VS Code.
    4.  Test that all D5e data displays correctly in the UI.

---

#### **Task 5.6.3: Create Type-Safe Content Service Layer**

*   **Objective:** Create a unified content service in the frontend that provides type-safe access to all D5e content.
*   **Implementation Steps:**
    1.  Create `frontend/src/services/d5eContentService.ts`:
        ```typescript
        import type { 
          D5eSpell, D5eMonster, D5eEquipment, D5eClass, 
          D5eRace, D5eBackground, D5eFeat, D5eTrait 
        } from '@/types/unified';
        import { CONTENT_TYPES } from '@/constants/contentTypes';
        
        export class D5eContentService {
          async getSpells(): Promise<D5eSpell[]> { /* ... */ }
          async getMonsters(): Promise<D5eMonster[]> { /* ... */ }
          async getSpellByIndex(index: string): Promise<D5eSpell | null> { /* ... */ }
          // ... methods for all content types
          
          async getContentByType<T>(contentType: ContentType): Promise<T[]> {
            // Generic method with type parameter
          }
        }
        
        export const d5eContentService = new D5eContentService();
        ```
    2.  Create type guards for runtime validation:
        ```typescript
        export function isD5eSpell(obj: unknown): obj is D5eSpell {
          return typeof obj === 'object' && obj !== null && 'level' in obj && 'school' in obj;
        }
        ```
    3.  Update stores to use the new service instead of direct API calls.
    4.  Add caching layer to reduce API calls for frequently accessed content.
*   **Testing / Validation:**
    1.  Write comprehensive unit tests for the content service.
    2.  Test type guards with various input scenarios.
    3.  Verify caching behavior and performance improvements.
    4.  Ensure all existing functionality continues to work.

---

#### **Task 5.6.4: Consolidate and Remove Duplicate Type Definitions**

*   **Objective:** Remove all duplicate type definitions and establish single sources of truth.
*   **Implementation Steps:**
    1.  Audit and remove duplicates:
        a. Remove `D5EClassModel` from `app/models/utils.py` if unused.
        b. Ensure all D5e types come from `app/content/schemas/` in backend.
        c. Ensure all frontend D5e types come from generated `unified.ts`.
    2.  Update type generation script (`scripts/dev/generate_ts.py`):
        a. Add header comment warning against manual edits.
        b. Include generation timestamp.
        c. Add content type constants generation from backend `CONTENT_TYPE_TO_MODEL`.
    3.  Create migration guide for any breaking changes.
    4.  Update all imports to use the canonical sources.
*   **Testing / Validation:**
    1.  Run full test suite to catch any broken imports.
    2.  Verify type generation produces expected output.
    3.  Check that no duplicate type definitions remain using grep/search.

---

#### **Task 5.6.5: Add Comprehensive Content Creation Forms**

*   **Objective:** Implement the missing 16 content creation forms to achieve 100% coverage.
*   **Implementation Steps:**
    1.  Create form components for each missing content type in `ContentCreationForm.vue`:
        - `ability-scores`: Simple form with name, description, abbreviation, skills array
        - `alignments`: Name, description, abbreviation fields
        - `classes`: Complex form with hit_die, proficiencies, equipment, features
        - `damage-types`: Name and description fields
        - `equipment-categories`: Name and equipment array reference
        - `features`: Name, level, class reference, description
        - `languages`: Name, type (standard/exotic), script, speakers
        - `levels`: Level number, ability score improvement, prof bonus, features, spells
        - `magic-items`: Complex form with rarity, type, requires attunement, description
        - `magic-schools`: Name and description
        - `proficiencies`: Type, name, classes, races that grant it
        - `rules`: Name, description, subsections reference
        - `rule-sections`: Name, description, order
        - `subclasses`: Name, class reference, description, features
        - `subraces`: Name, race reference, ability bonuses, traits
        - `weapon-properties`: Name and description
    2.  For each form:
        a. Study the D5e schema in backend to understand required/optional fields.
        b. Create appropriate form controls (text, number, select, checkbox, arrays).
        c. Add client-side validation matching backend requirements.
        d. Include helpful placeholders and field descriptions.
    3.  Update the content type dropdown to show all 25 options.
    4.  Add form validation to prevent submission of invalid data.
*   **Testing / Validation:**
    1.  Test each form by creating sample content.
    2.  Verify backend accepts all form submissions.
    3.  Test validation shows appropriate error messages.
    4.  Ensure created content appears correctly in content pack view.

---

#### **Task 5.6.6: Type System Documentation and Developer Guide**

*   **Objective:** Document the D&D 5e type system for future developers.
*   **Implementation Steps:**
    1.  Create `docs/D5E-TYPE-SYSTEM.md`:
        a. Overview of the type system architecture.
        b. Backend type definitions and organization.
        c. Type generation process and workflow.
        d. Frontend type usage patterns and best practices.
        e. Content type naming conventions.
        f. How to add new content types.
    2.  Update `CLAUDE.md` with type system information:
        a. Add section on D5e type conventions.
        b. Document the type generation command.
        c. Note about hyphenated content type names.
    3.  Add JSDoc/TSDoc comments to key type definitions.
    4.  Create example code snippets for common type usage patterns.
*   **Testing / Validation:**
    1.  Technical review of documentation accuracy.
    2.  Test that a new developer can follow the guide to add a new content type.
    3.  Verify all code examples compile and run correctly.

---

### Phase 6: Cleanup and Finalization (Week 8)

**Objective:** Remove obsolete code and update all documentation to reflect the new architecture, including the content management system.

---

#### **Task 6.1: Code and Dependency Cleanup**

*   **Objective:** Remove all code related to the old JSON file loading system.
*   **Implementation Steps:**
    1.  Delete old JSON-based data loading code (no longer applicable after refactoring).
    2.  Remove the `app/content/data/5e-database` submodule or update documentation to state it's for one-time migration only.
    3.  Remove the static JSON files from `app/content/data/knowledge/lore/` as this data is now in the database.
*   **Testing / Validation:**
    1.  Run `python tests/run_all_tests.py --with-rag`. Any failure indicates a lingering dependency that must be removed.

---

#### **Task 6.2: Documentation Update**

*   **Objective:** Update all project documentation to reflect the final database and content management architecture.
*   **Implementation Steps:**
    1.  Update `docs/ARCHITECTURE.md`:
        *   Modify the diagram to show the SQLite/pgvector DB and the content pack system.
        *   Update the "Repository Layer" section to explain content pack priority.
    2.  Update `README.md`:
        *   Change "Quick Start" to include the one-time database migration step: `python -m app.content.scripts.migrate_content`.
        *   Add a new section describing the Content Manager and how users can add their own content.
    3.  Update `docs/RAG-SYSTEM.md`:
        *   Explain that the knowledge base is now stored in SQLite and indexed for vector search.
        *   Describe the new background indexing process.
*   **Testing / Validation:**
    1.  Peer-review all documentation for clarity and accuracy.
    2.  Perform a "fresh install" test by following the `README.md` instructions from scratch to ensure a new user can set up the project successfully.
