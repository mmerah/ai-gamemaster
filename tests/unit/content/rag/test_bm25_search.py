"""
Tests for BM25 search functionality, including special character handling.
"""

from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.rag.bm25_search import BM25Search


class TestBM25Search:
    """Test BM25 search functionality."""

    @pytest.fixture
    def db_manager(self) -> DatabaseManager:
        """Create a mock database manager."""

        # Mock database manager for testing
        class MockDbManager:
            def __init__(self) -> None:
                pass

            def get_session(self, source: str = "system") -> Any:
                """Context manager that yields a mock session."""
                from contextlib import contextmanager

                @contextmanager
                def session_context() -> Any:
                    # For these tests, we don't need a real session
                    yield None

                return session_context()

        return MockDbManager()  # type: ignore[return-value]

    @pytest.fixture
    def bm25_search(self, db_manager: DatabaseManager) -> BM25Search:
        """Create a BM25Search instance."""
        # Mock the _verify_fts5_support and _discover_existing_fts_tables methods
        # to avoid database operations during initialization
        import unittest.mock

        with unittest.mock.patch.object(BM25Search, "_verify_fts5_support"):
            with unittest.mock.patch.object(
                BM25Search, "_discover_existing_fts_tables"
            ):
                return BM25Search(db_manager)

    def test_escape_fts_query_basic(self, bm25_search: BM25Search) -> None:
        """Test basic query escaping."""
        # Simple query
        result = bm25_search._escape_fts_query("hello world")
        assert result == "hello OR world"

        # Query with stopwords
        result = bm25_search._escape_fts_query("the quick brown fox")
        assert result == "quick OR brown OR fox"

    def test_escape_fts_query_special_characters(self, bm25_search: BM25Search) -> None:
        """Test escaping of queries with special characters."""
        # Question mark
        result = bm25_search._escape_fts_query(
            "What hit dice do different classes use?"
        )
        assert "?" not in result  # Question mark should be removed
        assert "hit" in result
        assert "dice" in result
        assert "different" in result
        assert "classes" in result

        # Apostrophes and quotes
        result = bm25_search._escape_fts_query("What's the fighter's hit die?")
        assert "'" not in result  # Apostrophes should be removed
        assert "fighters" in result or "fighter" in result
        assert "hit" in result
        assert "die" in result

        # Punctuation marks
        result = bm25_search._escape_fts_query("I attack the goblin!")
        assert "!" not in result
        assert "attack" in result
        assert "goblin" in result

        # Parentheses and special symbols
        result = bm25_search._escape_fts_query("Cast fireball (8d6 damage)")
        assert "(" not in result
        assert ")" not in result
        assert "cast" in result
        assert "fireball" in result
        assert "8d6" in result
        assert "damage" in result

    def test_escape_fts_query_edge_cases(self, bm25_search: BM25Search) -> None:
        """Test edge cases for query escaping."""
        # Empty query
        result = bm25_search._escape_fts_query("")
        assert result == '""'

        # Only stopwords
        result = bm25_search._escape_fts_query("the and or is")
        # Should fallback to original words when all are stopwords
        assert result != '""'

        # Only special characters
        result = bm25_search._escape_fts_query("???!!!")
        assert result == '""'

        # Mixed content
        result = bm25_search._escape_fts_query("D&D 5e: What's new?")
        assert "&" not in result
        assert ":" not in result
        assert "'" not in result
        assert "?" not in result
        assert "dd" in result.lower() or "5e" in result.lower()
        assert "new" in result

    def test_escape_fts_query_preserves_important_terms(
        self, bm25_search: BM25Search
    ) -> None:
        """Test that important game terms are preserved."""
        # Hit dice query
        result = bm25_search._escape_fts_query(
            "What hit dice do different classes use?"
        )
        terms = result.split(" OR ")
        assert "hit" in terms
        assert "dice" in terms
        assert "classes" in terms

        # Spell components
        result = bm25_search._escape_fts_query("What are the components for fireball?")
        terms = result.split(" OR ")
        assert "components" in terms
        assert "fireball" in terms

        # Character abilities
        result = bm25_search._escape_fts_query("How does sneak attack work?")
        terms = result.split(" OR ")
        assert "sneak" in terms
        assert "attack" in terms
        assert "work" in terms

    def test_sanitize_table_name(self, bm25_search: BM25Search) -> None:
        """Test table name sanitization."""
        # Valid table names
        assert bm25_search._sanitize_table_name("classes") == "classes"
        assert bm25_search._sanitize_table_name("magic_items") == "magic_items"
        assert bm25_search._sanitize_table_name("table123") == "table123"

        # Invalid table names should raise ValueError
        with pytest.raises(ValueError):
            bm25_search._sanitize_table_name("classes; DROP TABLE users")

        with pytest.raises(ValueError):
            bm25_search._sanitize_table_name("table-name")

        with pytest.raises(ValueError):
            bm25_search._sanitize_table_name("table name")
