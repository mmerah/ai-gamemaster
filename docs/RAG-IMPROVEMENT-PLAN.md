Enforce architecture principles from @CLAUDE.md

## RAG System Enhancement Plan

This document outlines a phased plan to refactor and enhance the Retrieval-Augmented Generation (RAG) system. The primary goals are to improve search relevance, increase modularity, expand data coverage, and establish a robust testing framework.

### Guiding Principles

All development will adhere to the principles outlined in `CLAUDE.md`:

-   **SOLID Principles**: Especially Dependency Inversion. We will use interfaces (`IQueryEngine`, `IReranker`) and dependency injection via the `ServiceContainer`.
-   **KISS & YAGNI**: We will start with simple, effective implementations (e.g., `SimpleExactMatchReranker`) and avoid over-engineering.
-   **Strong Typing**: All new components will be strictly typed and validated with `mypy`. Real type-hints must be enforced, `Any` must be avoided at all cost.
-   **Test-Driven Development (TDD)**: We will create a "golden set" of test cases to validate RAG performance before and after changes. It probably will fail at first.

---

## Phase 1: Cleanup & Simplification

**Objective**: Remove the outdated in-memory knowledge base system and dummy implementations to simplify the codebase and enforce proper dependency management.

-   [x] **Identify Obsolete Files**:
    -   `app/content/rag/knowledge_base.py`: The base in-memory manager.
    -   `app/content/rag/d5e_knowledge_base_manager.py`: The D&D 5e-specific in-memory manager that extends the base.
    -   `app/content/rag/dummy_sentence_transformer.py`: The dummy embeddings implementation (found inside db_knowledge_base_manager.py).

-   [x] **Update RAG Service Imports**:
    -   In `app/content/rag/rag_service.py`, removed import of `KnowledgeBaseManager` from `knowledge_base.py`.
    -   Updated the RAGService constructor to accept the `IKnowledgeBase` interface as a parameter.
    -   Added property getter/setter for proper error handling when kb_manager is not set.

-   [x] **Update Sentence Transformer Loading**:
    -   In `app/content/rag/db_knowledge_base_manager.py`, modified the `_get_sentence_transformer` method.
    -   Removed the try/except fallback to `DummySentenceTransformer`.
    -   Now catches `ImportError` and raises explicit error: "The 'sentence-transformers' and 'torch' packages are required for RAG. Please install them or set RAG_ENABLED=false in your .env file."
    -   Removed the `DummySentenceTransformer` class entirely.

-   [x] **Update `ServiceContainer`**:
    -   Verified `_create_rag_service` method in `app/core/container.py`.
    -   Container already exclusively uses database-backed implementations (`D5eDbKnowledgeBaseManager` or `DbKnowledgeBaseManager`).
    -   Updated to pass kb_manager as constructor parameter instead of setting it after creation.

-   [x] **Delete Obsolete Files**:
    -   Deleted `app/content/rag/knowledge_base.py`.
    -   Deleted `app/content/rag/d5e_knowledge_base_manager.py`.

-   [x] **Update Tests**:
    -   Removed tests for obsolete classes: `test_knowledge_base_manager.py` and `test_d5e_knowledge_base_manager.py`.
    -   Updated `test_rag_content_pack_priority.py` to remove patch of non-existent import.
    -   Updated `test_rag_service.py` to remove `DummySentenceTransformer` import and tests.
    -   Updated `test_d5e_rag_integration.py` to remove `DummySentenceTransformer` references.
    -   Updated mocking in `test_rag_service.py` to patch `sentence_transformers.SentenceTransformer` instead.

-   [x] **Run Tests**:
    -   Executed the full test suite (`python tests/run_all_tests.py --with-rag`) - all RAG tests are passing.

---

## Phase 2: Foundational Improvements (Modularity & Configuration)

**Objective**: Make the RAG system more configurable and modular, starting with the embedding model and its dimensions.

-   [x] **Update Embedding Model Configuration**:
    -   In `.env.example`, change `RAG_EMBEDDINGS_MODEL` from `all-MiniLM-L6-v2` to `intfloat/multilingual-e5-small`.
    -   Add a new setting `RAG_EMBEDDING_DIMENSION=384` to `.env.example`.

-   [x] **Update Settings Model**:
    -   In `app/settings.py`, add `embedding_dimension: int = Field(384, ..., alias="RAG_EMBEDDING_DIMENSION")` to `RAGSettings`.
    -   Update the default value for `embeddings_model` in `RAGSettings` to `"intfloat/multilingual-e5-small"`.

-   [x] **Make `VECTOR` Type Dimension-Aware**:
    -   In `app/content/models.py`, modify the `VECTOR` type decorator. It already accepts a `dim` argument. The key is to remove hardcoded `VECTOR(384)` from the model definitions.
    -   In `app/content/types.py`, update `DEFAULT_VECTOR_DIMENSION` to `384` (which it already is, but confirm). This file will serve as the source of truth for the default dimension, which can be overridden by settings.

-   [x] **Verify Alembic Migration**:
    -   In `app/content/alembic/versions/2032c7f301f0_add_vector_embedding_columns.py`, confirm that `VECTOR(384)` uses the type class.
    -   The `VECTOR` type stores data as `BLOB` in SQLite, with dimension validation happening in Python. The current implementation is already flexible.

-   [x] **Update Indexing Script for Dimension Safety**:
    -   In `app/content/scripts/index_for_rag.py`, modify the `main` function.
    -   After loading the `SentenceTransformer` model, get its embedding dimension (`model.get_sentence_embedding_dimension()`).
    -   Compare this with the `RAG_EMBEDDING_DIMENSION` from settings.
    -   If they do not match, log a critical error and exit, instructing the user to align their model and dimension settings. This prevents data corruption.

### Additional Fixes Implemented:

-   [x] **Fixed Torch Reimport Issues**:
    -   Added global caching for SentenceTransformer models to prevent "function '_has_torch_function' already has a docstring" errors
    -   Modified `_get_sentence_transformer()` to reuse cached instances across test runs
    -   Added `clear_sentence_transformer_cache()` function for test cleanup

-   [x] **Updated Test Runner for Isolation**:
    -   Modified `tests/run_all_tests.py` to run RAG integration tests in isolation
    -   RAG integration tests now run separately to avoid torch/numpy module conflicts
    -   Ensures all RAG tests pass when running the full test suite

-   [x] **Regenerated Test Database Embeddings**:
    -   Ran `python -m app.content.scripts.index_for_rag "sqlite:///data/test_content.db"`
    -   Ensured test database embeddings are compatible with `intfloat/multilingual-e5-small` model

---

## Phase 3: RAG Core Logic Enhancement

**Objective**: Extract existing reranking functionality into a modular interface and make the query engine more modular.

-   [x] **Create a Re-ranker Interface**:
    -   Create a new file `app/content/rag/interfaces.py`.
    -   Define an abstract base class `IReranker` with a method `rerank(self, query: str, results: List[KnowledgeResult]) -> List[KnowledgeResult]`.

-   [x] **Extract Existing Re-ranker**:
    -   Create a new file `app/content/rag/rerankers.py`.
    -   Extract the existing exact match boosting logic from `rag_service.py` (lines 156-169) into `ExactMatchReranker(IReranker)`.
    -   The `rerank` method should:
        -   Check if the query text appears exactly (case-insensitive) within the `content` of each `KnowledgeResult`.
        -   Boost the `relevance_score` of exact matches by a configurable amount (default `+0.2`).
        -   Return the list of results, re-sorted by the new scores.

-   [x] **Refactor RAGService**:
    -   In `app/content/rag/rag_service.py`, remove the inline reranking logic.
    -   Modify the `RAGService` constructor to accept an `IReranker` dependency.
    -   In the `get_relevant_knowledge` method, after the initial search and before returning the final results, pass the `all_results` list to the re-ranker.
    -   Update the `ServiceContainer` in `app/core/container.py` to create and inject the `ExactMatchReranker`.

-   [x] **Create Query Engine Interface**:
    -   In `app/content/rag/interfaces.py`, define an `IQueryEngine` interface with a method `analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]`.

-   [x] **Refactor `SimpleQueryEngine`**:
    -   In `app/content/rag/query_engine.py`, make `SimpleQueryEngine` implement the `IQueryEngine` interface.

-   [x] **Update `RAGService` Dependencies**:
    -   Modify `RAGService` to depend on `IQueryEngine` instead of the concrete `SimpleQueryEngine`.
    -   Update the `ServiceContainer` to inject `SimpleQueryEngine` as the `IQueryEngine` implementation.

### Phase 3 Implementation Notes:

-   [x] **Created Two Re-ranker Implementations**:
    -   `ExactMatchReranker`: As specified in the plan, checks for case-insensitive exact matches of the query in content
    -   `EntityMatchReranker`: Extracted the existing entity-based boosting logic to preserve current functionality
    -   Both implementations follow the `IReranker` interface and support configurable boost amounts

-   [x] **Enhanced Query Context Preservation**:
    -   Modified `RAGService` to add query context to result metadata
    -   This allows re-rankers to access entity information (spell names, creature names) for more sophisticated reranking

-   [x] **Dependency Injection Setup**:
    -   `ServiceContainer` now creates and injects `SimpleQueryEngine` and `EntityMatchReranker`
    -   Used `EntityMatchReranker` to maintain backward compatibility with existing behavior
    -   All dependencies follow the Dependency Inversion Principle from SOLID

-   [x] **Fixed Import Issues**:
    -   Fixed incorrect import in `interfaces.py` (GameStateModel location)
    -   Updated test mocking to accommodate new architecture
    -   All tests pass with strict mypy type checking

---

## Phase 4: Expanding RAG Data Coverage

**Objective**: Ensure all relevant content tables are indexed with vector embeddings to provide comprehensive search results.

-   [x] **Audit Content Tables for Indexing**:
    -   Review all models in `app/content/models.py`.
    -   Cross-reference with the `RAG_ENABLED_TABLES` dictionary in `app/content/scripts/index_for_rag.py`.
    -   Identify any content-bearing tables that are missing.
        -   **Missing tables identified**: `EquipmentCategory`, `Level`, `MagicSchool`, `WeaponProperty`.

-   [x] **Update `RAG_ENABLED_TABLES`**:
    -   In `app/content/scripts/index_for_rag.py`, add the missing models and their table names to the `RAG_ENABLED_TABLES` dictionary:
        -   `EquipmentCategory`: "equipment_categories"
        -   `Level`: "levels"
        -   `MagicSchool`: "magic_schools"
        -   `WeaponProperty`: "weapon_properties"

-   [x] **Enhance `create_content_text` Function**:
    -   In `app/content/scripts/index_for_rag.py`, update the `create_content_text` function.
    -   Add missing handlers for existing indexed tables:
        -   `backgrounds`, `feats`, `magic_items`, `traits`
        -   `conditions`, `skills`, `proficiencies`
        -   `damage_types`, `languages`, `alignments`, `ability_scores`
    -   Add handlers for newly indexed tables:
        -   For `EquipmentCategory`, include the category name and description.
        -   For `Level`, include class name, level number, and features.
        -   For `MagicSchool`, include school name and description.
        -   For `WeaponProperty`, include property name and description.

-   [x] **Update Documentation**:
    -   In `app/content/README.md`, update the list of indexed content to reflect the expanded coverage.

-   [x] **Re-run Indexing Script**:
    -   After implementing the changes, run `python -m app.content.scripts.index_for_rag` to populate the new embeddings.
    -   Update the project's main `README.md` to note that reindexing is required when changing embedding models or dimensions.

### Phase 4 Implementation Notes:

-   [x] **Successfully expanded RAG coverage to all content tables**:
    -   Added 4 new tables: `EquipmentCategory`, `Level`, `MagicSchool`, `WeaponProperty`
    -   Enhanced content text generation for existing tables: backgrounds, feats, magic_items, traits
    -   Improved content extraction with specific handlers for conditions and skills
    -   Added content handlers for all new entity types with appropriate field extraction
    -   All new handlers passed type checking with `mypy --strict`
    -   Test runs confirmed successful indexing of new tables

-   [x] **Fixed Query Engine Logic Issue**:
    -   Fixed `_determine_query_types` method to properly handle actions containing both creature keywords and skill keywords
    -   "I try to persuade the guard" now correctly generates a SKILL_CHECK query type
    -   Combat detection no longer overrides skill check detection when both patterns are present
    -   All RAG tests passing at 100%

---

## Phase 5: Testing & Validation

**Objective**: Create a "golden set" of test cases to validate RAG performance and prevent regressions.

-   [ ] **Create Test File**:
    -   Create `tests/integration/rag/test_rag_golden_pairs.py`.

-   [ ] **Define Golden Set Data Structure**:
    -   At the top of the new test file, define a list of dictionaries named `GOLDEN_PAIRS`. Each dictionary will contain:
        -   `name`: A descriptive name for the test case.
        -   `player_action`: The input action string.
        -   `game_state`: A simplified `GameStateModel` representing the context.
        -   `expected_fragments`: A list of strings that *must* appear in the top 3 search results' content.

-   [ ] **Implement Golden Pair Test**:
    -   Write a test function `test_rag_golden_pairs` that uses `@pytest.mark.parametrize("golden_pair", GOLDEN_PAIRS)`.
    -   Inside the test:
        1.  Get the `RAGService` from the test container.
        2.  Call `rag_service.get_relevant_knowledge()` with the action and game state from the golden pair.
        3.  Assert that results were returned.
        4.  Combine the content of the top 3 results into a single string.
        5.  Iterate through `expected_fragments` and assert that each fragment is present in the combined result content.

-   [ ] **Populate Golden Set**:
    -   Add at least 5-7 diverse test cases to `GOLDEN_PAIRS`:
        1.  **Combat Action**: `player_action`: "I attack the goblin with my shortsword.", `game_state`: in combat with a goblin. `expected_fragments`: ["goblin", "shortsword"].
        2.  **Spellcasting**: `player_action`: "I cast fireball at the group of orcs.", `game_state`: not in combat. `expected_fragments`: ["fireball", "dexterity saving throw", "8d6 fire damage"].
        3.  **Skill Check**: `player_action`: "I try to persuade the guard to let us pass.", `game_state`: at a city gate. `expected_fragments`: ["persuasion", "charisma", "social interaction"].
        4.  **Rules Lookup**: `player_action`: "How does grappling work?", `game_state`: any. `expected_fragments`: ["grappled", "escape", "athletics"].
        5.  **Lore Query**: `player_action`: "Tell me about the Celestial Empire of Solaria.", `game_state`: lore is "world_of_eldoria". `expected_fragments`: ["Lumengarde", "Sun Throne"].

-   [ ] **Integrate into Test Suite**:
    -   Ensure the new test file is picked up by `tests/run_all_tests.py` when run with the `--with-rag` flag.

---

## Phase 6: Hybrid Search Implementation

**Objective**: Implement hybrid search combining vector similarity search with keyword-based BM25 search for improved retrieval quality.

-   [ ] **Create Hybrid Search Interface**:
    -   In `app/content/rag/interfaces.py`, define an `IHybridSearch` interface with methods:
        -   `search_vector(query_embedding: np.ndarray, limit: int) -> List[Tuple[str, float]]`
        -   `search_keyword(query: str, limit: int) -> List[Tuple[str, float]]`
        -   `hybrid_search(query: str, query_embedding: np.ndarray, limit: int, alpha: float = 0.7) -> List[Tuple[str, float]]`

-   [ ] **Implement BM25 Search**:
    -   Create `app/content/rag/bm25_search.py`.
    -   Implement `BM25Search` class that:
        -   Uses SQLite's FTS5 (Full-Text Search) extension for efficient keyword search.
        -   Creates an FTS5 virtual table for each content type.
        -   Implements BM25 scoring algorithm.

-   [ ] **Create Hybrid Search Implementation**:
    -   Create `app/content/rag/hybrid_search.py`.
    -   Implement `HybridSearch(IHybridSearch)` that:
        -   Combines vector search results with BM25 keyword search results.
        -   Uses Reciprocal Rank Fusion (RRF) to merge rankings.
        -   Supports configurable weighting between vector and keyword search (alpha parameter).

-   [ ] **Update Database Schema**:
    -   Create a new Alembic migration to add FTS5 virtual tables for searchable content.
    -   Index the same text content used for embeddings.

-   [ ] **Integrate Hybrid Search**:
    -   Update `DbKnowledgeBaseManager` to use `IHybridSearch` instead of direct vector search.
    -   Add configuration for hybrid search alpha parameter in `RAGSettings`.
    -   Update `ServiceContainer` to inject the hybrid search implementation.

-   [ ] **Add Hybrid Search Tests**:
    -   Create tests comparing pure vector search, pure keyword search, and hybrid search.
    -   Validate that hybrid search improves recall for both exact matches and semantic queries.
    -   Test edge cases like empty queries, special characters, and multilingual content.