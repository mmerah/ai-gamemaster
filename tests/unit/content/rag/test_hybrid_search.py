"""
Unit tests for hybrid search functionality.

Tests the BM25Search and HybridSearch implementations, including
FTS5 table creation, keyword search, and Reciprocal Rank Fusion.
"""

import unittest
from contextlib import contextmanager
from typing import Any, Iterator, List, Tuple
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import numpy as np
import numpy.typing as npt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.content.protocols import DatabaseManagerProtocol
from app.content.rag.bm25_search import BM25Search
from app.content.rag.hybrid_search import HybridSearch, MultiTableHybridSearch


class TestBM25Search(unittest.TestCase):
    """Test cases for BM25Search functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.db_manager = Mock(spec=DatabaseManagerProtocol)

        # Create a real session for testing
        self.session = Session(self.engine)
        # Make get_session return a proper context manager
        from contextlib import contextmanager

        @contextmanager
        def mock_get_session(_source: str = "system") -> Iterator[Session]:
            yield self.session

        self.db_manager.get_session = mock_get_session

        # Create test table
        self.session.execute(
            text("""
            CREATE TABLE test_table (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT
            )
        """)
        )

        # Insert test data
        test_data = [
            ("1", "Fire Bolt", "A mote of fire streaks toward a creature"),
            ("2", "Lightning Bolt", "A stroke of lightning forming a line"),
            ("3", "Healing Word", "A creature of your choice regains hit points"),
            ("4", "Fireball", "A bright streak flashes to a point you choose"),
        ]

        for id_, name, desc in test_data:
            self.session.execute(
                text(
                    "INSERT INTO test_table (id, name, description) VALUES (:id, :name, :desc)"
                ),
                {"id": id_, "name": name, "desc": desc},
            )
        self.session.commit()

        self.bm25_search = BM25Search(self.db_manager)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.session.close()
        self.engine.dispose()

    def test_sanitize_table_name(self) -> None:
        """Test table name sanitization."""
        # Valid table names
        self.assertEqual(
            self.bm25_search._sanitize_table_name("test_table"), "test_table"
        )
        self.assertEqual(self.bm25_search._sanitize_table_name("Table123"), "Table123")

        # Invalid table names
        with self.assertRaises(ValueError):
            self.bm25_search._sanitize_table_name("test-table")

        with self.assertRaises(ValueError):
            self.bm25_search._sanitize_table_name("test table")

        with self.assertRaises(ValueError):
            self.bm25_search._sanitize_table_name("test;drop table users")

    def test_escape_fts_query(self) -> None:
        """Test FTS query escaping for natural language queries."""
        # Test that it converts to FTS5-compatible OR queries
        self.assertEqual(
            self.bm25_search._escape_fts_query('test "quoted"'), "test OR quoted"
        )
        self.assertEqual(
            self.bm25_search._escape_fts_query("test's query"), "tests OR query"
        )
        self.assertEqual(self.bm25_search._escape_fts_query("test:query"), "testquery")
        # Test stopword removal
        self.assertEqual(self.bm25_search._escape_fts_query("what is the test"), "test")
        # Test empty result
        self.assertEqual(self.bm25_search._escape_fts_query("???"), '""')

    def test_create_fts_table(self) -> None:
        """Test FTS5 table creation."""
        # Create FTS table - first column should be the primary key
        self.bm25_search.create_fts_table("test_table", ["id", "name", "description"])

        # Verify FTS table exists
        result = self.session.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table_fts'"
            )
        ).fetchone()
        self.assertIsNotNone(result)

        # Verify data was populated
        count = self.session.execute(
            text("SELECT COUNT(*) FROM test_table_fts")
        ).scalar()
        self.assertEqual(count, 4)

    def test_search_table(self) -> None:
        """Test searching a table with FTS5."""
        # Create FTS table first - first column should be the primary key
        self.bm25_search.create_fts_table("test_table", ["id", "name", "description"])
        self.bm25_search._fts_tables.add("test_table_fts")

        # Search for "fire"
        results = self.bm25_search.search_table("test_table", "fire", limit=3)

        # Should find at least one result (Fire Bolt or Fireball)
        self.assertGreaterEqual(len(results), 1)
        entity_ids = [r[0] for r in results]

        # At least one of these should be found
        fire_items = ["1", "4"]  # Fire Bolt, Fireball
        found_fire_item = any(item in entity_ids for item in fire_items)
        self.assertTrue(
            found_fire_item,
            f"Expected to find at least one of {fire_items} in {entity_ids}",
        )

        # Verify scores are normalized
        for _, score in results:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_search_multiple_tables(self) -> None:
        """Test searching multiple tables."""
        # Create another test table
        self.session.execute(
            text("""
            CREATE TABLE test_table2 (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT
            )
        """)
        )
        self.session.execute(
            text(
                "INSERT INTO test_table2 (id, name, description) VALUES ('5', 'Fire Shield', 'Flames surround your body')"
            )
        )
        self.session.commit()

        # Create FTS tables - first column should be the primary key
        self.bm25_search.create_fts_table("test_table", ["id", "name", "description"])
        self.bm25_search.create_fts_table("test_table2", ["id", "name", "description"])
        self.bm25_search._fts_tables.add("test_table_fts")
        self.bm25_search._fts_tables.add("test_table2_fts")

        # Mock the search results since FTS5 might not work properly in test environment
        with patch.object(self.bm25_search, "search_table") as mock_search:
            # Set up different return values for each table
            def search_side_effect(
                table_name: str, _query: str, _limit: int
            ) -> List[Tuple[str, float]]:
                if table_name == "test_table":
                    return [("1", 1.0), ("4", 0.8)]  # Fire Bolt, Fireball
                elif table_name == "test_table2":
                    return [("5", 0.9)]  # Fire Shield
                return []

            mock_search.side_effect = search_side_effect

            # Search both tables
            results = self.bm25_search.search_multiple_tables(
                ["test_table", "test_table2"], "fire", limit_per_table=2
            )

            # Should have results from both tables
            self.assertIn("test_table", results)
            self.assertIn("test_table2", results)
            self.assertEqual(len(results["test_table"]), 2)
            self.assertEqual(len(results["test_table2"]), 1)


class TestHybridSearch(unittest.TestCase):
    """Test cases for HybridSearch functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_manager = Mock(spec=DatabaseManagerProtocol)
        self.session = Mock(spec=Session)

        # Make get_session return a proper context manager
        @contextmanager
        def mock_get_session(_source: str = "system") -> Iterator[Session]:
            yield self.session

        self.db_manager.get_session = mock_get_session

        self.hybrid_search = HybridSearch(
            db_manager=self.db_manager,
            table_name="test_table",
            embedding_model=None,
            rrf_k=60,
        )

        # Mock BM25Search
        self.hybrid_search.bm25_search = Mock(spec=BM25Search)

    def test_vector_search(self) -> None:
        """Test vector similarity search."""
        # Create test embedding
        query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        # Mock database results
        self.session.execute.return_value.fetchall.return_value = [
            ("entity1", 0.5),
            ("entity2", 1.0),
            ("entity3", 1.5),
        ]

        # Perform search
        results = self.hybrid_search.search_vector(query_embedding, limit=3)

        # Verify results
        self.assertEqual(len(results), 3)
        # Check similarity scores (inverse of distance)
        self.assertEqual(results[0][0], "entity1")
        self.assertAlmostEqual(results[0][1], 1.0 / (1.0 + 0.5), places=4)
        self.assertEqual(results[1][0], "entity2")
        self.assertAlmostEqual(results[1][1], 1.0 / (1.0 + 1.0), places=4)

    def test_keyword_search(self) -> None:
        """Test keyword search delegation to BM25Search."""
        # Mock BM25 results
        expected_results = [("entity1", 0.9), ("entity2", 0.7)]
        # Use patch.object to mock the method properly
        with patch.object(
            self.hybrid_search.bm25_search,
            "search_table",
            return_value=expected_results,
        ) as mock_search:
            # Perform search
            results = self.hybrid_search.search_keyword("test query", limit=5)

            # Verify delegation
            mock_search.assert_called_once_with("test_table", "test query", 5)
            self.assertEqual(results, expected_results)

    @patch.object(HybridSearch, "search_keyword")
    @patch.object(HybridSearch, "search_vector")
    def test_hybrid_search_rrf(
        self, mock_search_vector: Mock, mock_search_keyword: Mock
    ) -> None:
        """Test hybrid search with Reciprocal Rank Fusion."""
        # Create test embedding
        query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        # Mock vector search results
        mock_search_vector.return_value = [
            ("entity1", 0.9),
            ("entity2", 0.8),
            ("entity3", 0.7),
        ]

        # Mock keyword search results
        mock_search_keyword.return_value = [
            ("entity2", 0.95),
            ("entity4", 0.85),
            ("entity1", 0.75),
        ]

        # Perform hybrid search
        results = self.hybrid_search.hybrid_search(
            "test query", query_embedding, limit=3, alpha=0.5
        )

        # Verify results
        self.assertEqual(len(results), 3)

        # entity2 should rank highest (appears first in keyword, second in vector)
        # entity1 should be present (appears first in vector, third in keyword)
        # entity3 or entity4 should be present
        entity_ids = [r[0] for r in results]
        self.assertEqual(entity_ids[0], "entity2")
        # entity1 and entity4 have similar combined scores, order may vary
        self.assertIn("entity1", entity_ids)
        self.assertTrue(any(e in entity_ids for e in ["entity3", "entity4"]))

        # Verify scores are normalized
        self.assertEqual(results[0][1], 1.0)  # First result normalized to 1.0
        for _, score in results:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    @patch.object(HybridSearch, "search_keyword")
    @patch.object(HybridSearch, "search_vector")
    def test_hybrid_search_extreme_alpha(
        self, mock_search_vector: Mock, mock_search_keyword: Mock
    ) -> None:
        """Test hybrid search with extreme alpha values."""
        query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        # Mock search results
        vector_results = [("v1", 0.9), ("v2", 0.8)]
        keyword_results = [("k1", 0.95), ("k2", 0.85)]

        mock_search_vector.return_value = vector_results
        mock_search_keyword.return_value = keyword_results

        # Test alpha = 1.0 (vector only)
        results = self.hybrid_search.hybrid_search(
            "test", query_embedding, limit=2, alpha=1.0
        )
        self.assertEqual(results, vector_results[:2])

        # Test alpha = 0.0 (keyword only)
        results = self.hybrid_search.hybrid_search(
            "test", query_embedding, limit=2, alpha=0.0
        )
        self.assertEqual(results, keyword_results[:2])


class TestMultiTableHybridSearch(unittest.TestCase):
    """Test cases for MultiTableHybridSearch."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_manager = Mock(spec=DatabaseManagerProtocol)
        self.multi_search = MultiTableHybridSearch(
            db_manager=self.db_manager, embedding_model=None, rrf_k=60
        )

    @patch("app.content.rag.hybrid_search.HybridSearch")
    def test_get_search_instance(self, mock_hybrid_class: Mock) -> None:
        """Test getting search instances for tables."""
        # Mock HybridSearch to avoid database operations
        mock_instance = Mock(spec=HybridSearch)
        mock_instance.table_name = "table1"
        mock_hybrid_class.return_value = mock_instance

        # Get instance for a table
        instance1 = self.multi_search.get_search_instance("table1")
        self.assertIsInstance(instance1, Mock)  # It's a mocked instance
        mock_hybrid_class.assert_called_once_with(self.db_manager, "table1", None, 60)

        # Get same instance again (should be cached)
        instance2 = self.multi_search.get_search_instance("table1")
        self.assertIs(instance1, instance2)
        # Should not create a new instance
        mock_hybrid_class.assert_called_once()  # Still only called once

        # Reset mock for second table
        mock_hybrid_class.reset_mock()
        mock_instance2 = Mock(spec=HybridSearch)
        mock_instance2.table_name = "table2"
        mock_hybrid_class.return_value = mock_instance2

        # Get instance for different table
        instance3 = self.multi_search.get_search_instance("table2")
        self.assertIsNot(instance1, instance3)
        mock_hybrid_class.assert_called_once_with(self.db_manager, "table2", None, 60)

    @patch.object(MultiTableHybridSearch, "get_search_instance")
    def test_search_tables(self, mock_get_search_instance: Mock) -> None:
        """Test searching across multiple tables."""
        query_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        # Mock search instances
        mock_instance1 = Mock(spec=HybridSearch)
        mock_instance1.hybrid_search.return_value = [("t1_e1", 0.9), ("t1_e2", 0.8)]

        mock_instance2 = Mock(spec=HybridSearch)
        mock_instance2.hybrid_search.return_value = [("t2_e1", 0.85)]

        mock_get_search_instance.side_effect = lambda t: {
            "table1": mock_instance1,
            "table2": mock_instance2,
        }.get(t)

        # Search tables
        results = self.multi_search.search_tables(
            ["table1", "table2"],
            "test query",
            query_embedding,
            limit_per_table=2,
            alpha=0.7,
        )

        # Verify results
        self.assertIn("table1", results)
        self.assertIn("table2", results)
        self.assertEqual(len(results["table1"]), 2)
        self.assertEqual(len(results["table2"]), 1)

        # Verify method calls
        mock_instance1.hybrid_search.assert_called_once_with(
            "test query", query_embedding, 2, 0.7
        )
        mock_instance2.hybrid_search.assert_called_once_with(
            "test query", query_embedding, 2, 0.7
        )


if __name__ == "__main__":
    unittest.main()
