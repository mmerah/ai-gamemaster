"""
BM25 keyword-based search implementation using SQLite's FTS5 extension.

This module provides efficient full-text search capabilities for the RAG system,
complementing vector-based semantic search with exact and partial keyword matching.
"""

import logging
import re
import string
from typing import Dict, List, Set, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.content.protocols import DatabaseManagerProtocol

logger = logging.getLogger(__name__)


class BM25Search:
    """
    Implements BM25 ranking algorithm using SQLite FTS5 full-text search.

    This class manages FTS5 virtual tables for efficient keyword search across
    content tables, providing relevance-ranked results based on term frequency
    and document length normalization.
    """

    def __init__(self, db_manager: DatabaseManagerProtocol):
        """
        Initialize BM25 search with database connection.

        Args:
            db_manager: Database manager for accessing SQLite connection
        """
        self.db_manager = db_manager
        self._fts_tables: Set[str] = set()
        self._verify_fts5_support()
        self._discover_existing_fts_tables()

    def _verify_fts5_support(self) -> None:
        """Verify that SQLite FTS5 extension is available."""
        with self.db_manager.get_session() as session:
            try:
                # Test FTS5 availability
                result = session.execute(
                    text("SELECT sqlite_compileoption_used('ENABLE_FTS5')")
                ).scalar()

                if not result:
                    logger.warning(
                        "SQLite FTS5 extension not available. "
                        "Keyword search functionality will be limited."
                    )
            except Exception as e:
                logger.error(f"Error checking FTS5 support: {e}")

    def _discover_existing_fts_tables(self) -> None:
        """Discover existing FTS5 tables in the database."""
        with self.db_manager.get_session() as session:
            try:
                # Query for all FTS5 virtual tables
                result = session.execute(
                    text("""
                        SELECT name 
                        FROM sqlite_master 
                        WHERE type='table' 
                        AND name LIKE '%_fts' 
                        AND sql LIKE '%USING fts5%'
                    """)
                ).fetchall()

                # Add discovered tables to the set
                for row in result:
                    table_name = row[0]
                    self._fts_tables.add(table_name)
                    logger.debug(f"Discovered existing FTS5 table: {table_name}")

                if self._fts_tables:
                    logger.info(f"Found {len(self._fts_tables)} existing FTS5 tables")

            except Exception as e:
                logger.error(f"Error discovering FTS5 tables: {e}")

    def _sanitize_table_name(self, table_name: str) -> str:
        """
        Sanitize table name to prevent SQL injection.

        Args:
            table_name: Table name to sanitize

        Returns:
            Sanitized table name

        Raises:
            ValueError: If table name contains invalid characters
        """
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        return table_name

    def _escape_fts_query(self, query: str) -> str:
        """
        Convert natural language query to FTS5-compatible search terms.

        Args:
            query: Raw query string (e.g., "What makes hill dwarves different?")

        Returns:
            FTS5-compatible query (e.g., "hill dwarves different")
        """
        # Common stopwords to remove
        stopwords = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "he",
            "in",
            "is",
            "it",
            "its",
            "of",
            "on",
            "that",
            "the",
            "to",
            "was",
            "will",
            "with",
            "what",
            "when",
            "where",
            "who",
            "why",
            "how",
            "makes",
            "make",
            "does",
            "do",
            "did",
            "other",
            "than",
            "much",
            "many",
            "some",
            "any",
            "their",
            "them",
            "they",
        }

        # Remove punctuation and convert to lowercase
        translator = str.maketrans("", "", string.punctuation)
        clean_query = query.translate(translator).lower()

        # Split into words and filter out stopwords
        words = [word for word in clean_query.split() if word not in stopwords]

        # If we have no words after filtering, use original words (minus punctuation)
        if not words:
            words = clean_query.split()

        # Join words with OR operator for broader matching
        # This allows FTS5 to find documents containing any of the terms
        if words:
            fts_query = " OR ".join(words)
            logger.debug(f"FTS5 query: '{query}' -> '{fts_query}' (words: {words})")
            return fts_query
        else:
            # Fallback: return a safe empty query
            logger.debug(f"FTS5 query: '{query}' -> '\"\"' (no words after filtering)")
            return '""'

    def create_fts_table(self, table_name: str, columns: List[str]) -> None:
        """
        Create an FTS5 virtual table for a content table.

        Args:
            table_name: Name of the source table
            columns: List of column names to index for full-text search
        """
        table_name = self._sanitize_table_name(table_name)
        fts_table_name = f"{table_name}_fts"

        with self.db_manager.get_session() as session:
            try:
                # Drop existing FTS table if it exists
                session.execute(text(f"DROP TABLE IF EXISTS {fts_table_name}"))

                # Create FTS5 virtual table
                # Quote column names to handle reserved keywords
                quoted_columns = [f'"{col}"' for col in columns]
                columns_str = ", ".join(quoted_columns)
                create_sql = f"""
                    CREATE VIRTUAL TABLE {fts_table_name} 
                    USING fts5(
                        entity_id UNINDEXED,
                        {columns_str},
                        tokenize='porter unicode61'
                    )
                """
                session.execute(text(create_sql))

                # Populate FTS table from source table
                # Note: First column in columns list should be the primary key (usually 'index')
                insert_columns = ["entity_id"] + columns[
                    1:
                ]  # Skip primary key from insert columns

                # Special handling for classes table to convert hit_die to searchable text
                if table_name == "classes":
                    select_expressions = []
                    for col in columns:
                        if col == "hit_die":
                            # Convert numeric hit_die to searchable text like "Hit Die: d12"
                            select_expressions.append(
                                f'CASE WHEN "{col}" IS NOT NULL THEN \'Hit Die: d\' || "{col}" ELSE NULL END'
                            )
                        else:
                            select_expressions.append(f'"{col}"')
                else:
                    # For other tables, use columns as-is
                    select_expressions = [f'"{col}"' for col in columns]

                # Quote column names in INSERT statement
                quoted_insert_columns = [f'"{col}"' for col in insert_columns]
                where_conditions = " OR ".join(
                    f'"{col}" IS NOT NULL' for col in columns[1:]
                )

                insert_sql = f"""
                    INSERT INTO {fts_table_name} ({", ".join(quoted_insert_columns)})
                    SELECT {", ".join(select_expressions)}
                    FROM {table_name}
                    WHERE {where_conditions}
                """
                session.execute(text(insert_sql))

                session.commit()
                self._fts_tables.add(fts_table_name)

                logger.info(f"Created FTS5 table '{fts_table_name}' for '{table_name}'")

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to create FTS table for '{table_name}': {e}")
                raise

    def search_table(
        self, table_name: str, query: str, limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search a specific table using FTS5.

        Args:
            table_name: Name of the table to search
            query: Search query
            limit: Maximum number of results

        Returns:
            List of (entity_id, bm25_score) tuples
        """
        table_name = self._sanitize_table_name(table_name)
        fts_table_name = f"{table_name}_fts"

        if fts_table_name not in self._fts_tables:
            logger.warning(f"FTS table '{fts_table_name}' not found")
            return []

        escaped_query = self._escape_fts_query(query)

        with self.db_manager.get_session() as session:
            try:
                # Use FTS5 MATCH operator with BM25 ranking
                search_sql = f"""
                    SELECT 
                        entity_id,
                        -rank as bm25_score
                    FROM {fts_table_name}
                    WHERE {fts_table_name} MATCH :query
                    ORDER BY rank
                    LIMIT :limit
                """

                results = session.execute(
                    text(search_sql), {"query": escaped_query, "limit": limit}
                ).fetchall()

                # Normalize BM25 scores to 0-1 range
                if results:
                    max_score = max(score for _, score in results)
                    min_score = min(score for _, score in results)
                    score_range = max_score - min_score

                    if score_range > 0:
                        normalized_results = [
                            (entity_id, (score - min_score) / score_range)
                            for entity_id, score in results
                        ]
                    else:
                        # All scores are the same
                        normalized_results = [
                            (entity_id, 1.0) for entity_id, _ in results
                        ]

                    return normalized_results

                return []

            except Exception as e:
                logger.error(f"FTS5 search error for table '{table_name}': {e}")
                return []

    def search_multiple_tables(
        self, tables: List[str], query: str, limit_per_table: int = 5
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Search multiple tables and return results grouped by table.

        Args:
            tables: List of table names to search
            query: Search query
            limit_per_table: Maximum results per table

        Returns:
            Dictionary mapping table names to their search results
        """
        results = {}

        for table in tables:
            table_results = self.search_table(table, query, limit_per_table)
            if table_results:
                results[table] = table_results

        return results

    def update_fts_entry(
        self, table_name: str, entity_id: str, columns: Dict[str, str]
    ) -> None:
        """
        Update a single entry in the FTS index.

        Args:
            table_name: Name of the table
            entity_id: ID of the entity to update
            columns: Dictionary of column values to update
        """
        table_name = self._sanitize_table_name(table_name)
        fts_table_name = f"{table_name}_fts"

        if fts_table_name not in self._fts_tables:
            logger.warning(f"FTS table '{fts_table_name}' not found")
            return

        with self.db_manager.get_session() as session:
            try:
                # Delete existing entry
                session.execute(
                    text(f"DELETE FROM {fts_table_name} WHERE entity_id = :id"),
                    {"id": entity_id},
                )

                # Insert updated entry
                columns_with_id = {"entity_id": entity_id, **columns}
                column_names = ", ".join(columns_with_id.keys())
                placeholders = ", ".join(f":{key}" for key in columns_with_id.keys())

                insert_sql = f"""
                    INSERT INTO {fts_table_name} ({column_names})
                    VALUES ({placeholders})
                """
                session.execute(text(insert_sql), columns_with_id)

                session.commit()

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to update FTS entry: {e}")
                raise
