"""
Hybrid search implementation combining vector and keyword-based search.

This module implements the IHybridSearch interface, providing a unified search
approach that leverages both semantic similarity (vector search) and exact/partial
matches (keyword search) to improve retrieval quality.
"""

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

import numpy.typing as npt
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.content.protocols import DatabaseManagerProtocol
from app.content.rag.bm25_search import BM25Search
from app.content.rag.interfaces import IHybridSearch

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class HybridSearch(IHybridSearch):
    """
    Implements hybrid search combining vector similarity and BM25 keyword search.

    Uses Reciprocal Rank Fusion (RRF) to merge rankings from both search methods,
    providing improved retrieval quality by capturing both semantic meaning and
    exact keyword matches.
    """

    def __init__(
        self,
        db_manager: DatabaseManagerProtocol,
        table_name: str,
        embedding_model: Optional["SentenceTransformer"] = None,
        rrf_k: int = 60,
    ):
        """
        Initialize hybrid search for a specific table.

        Args:
            db_manager: Database manager for accessing SQLite
            table_name: Name of the table to search
            embedding_model: Optional sentence transformer for vector search
            rrf_k: Reciprocal Rank Fusion constant (default: 60)
        """
        self.db_manager = db_manager
        self.table_name = table_name
        self.embedding_model = embedding_model
        self.rrf_k = rrf_k

        # Initialize BM25 search component
        self.bm25_search = BM25Search(db_manager)

        # Verify vector search support
        self._has_vector_support = self._check_vector_support()

    def _check_vector_support(self) -> bool:
        """Check if sqlite-vec extension is available for vector search."""
        with self.db_manager.get_session() as session:
            try:
                # Test vec_distance_l2 function
                session.execute(text("SELECT vec_distance_l2('[1,2]', '[3,4]')"))
                return True
            except Exception:
                logger.warning(
                    "sqlite-vec extension not available. "
                    "Vector search will be disabled in hybrid search."
                )
                return False

    def search_vector(
        self, query_embedding: npt.NDArray[Any], limit: int
    ) -> List[Tuple[str, float]]:
        """
        Perform vector similarity search using embeddings.

        Args:
            query_embedding: The query vector
            limit: Maximum number of results

        Returns:
            List of (entity_id, similarity_score) tuples
        """
        if not self._has_vector_support:
            return []

        with self.db_manager.get_session() as session:
            try:
                # Convert embedding to serialized format expected by sqlite-vec
                embedding_bytes = query_embedding.astype("float32").tobytes()

                # Perform vector search using L2 distance
                search_sql = f"""
                    SELECT 
                        "index" as entity_id,
                        vec_distance_l2(embedding, :query_embedding) as distance
                    FROM {self.table_name}
                    WHERE embedding IS NOT NULL
                    ORDER BY distance ASC
                    LIMIT :limit
                """

                results = session.execute(
                    text(search_sql),
                    {"query_embedding": embedding_bytes, "limit": limit},
                ).fetchall()

                # Convert L2 distance to similarity score
                vector_results = []
                for entity_id, distance in results:
                    # Convert distance to similarity (inverse relationship)
                    similarity = 1.0 / (1.0 + float(distance))
                    vector_results.append((entity_id, similarity))

                return vector_results

            except Exception as e:
                logger.error(f"Vector search error: {e}")
                return []

    def search_keyword(self, query: str, limit: int) -> List[Tuple[str, float]]:
        """
        Perform keyword-based search using BM25.

        Args:
            query: The text query
            limit: Maximum number of results

        Returns:
            List of (entity_id, relevance_score) tuples
        """
        return self.bm25_search.search_table(self.table_name, query, limit)

    def hybrid_search(
        self,
        query: str,
        query_embedding: npt.NDArray[Any],
        limit: int,
        alpha: float = 0.7,
    ) -> List[Tuple[str, float]]:
        """
        Perform hybrid search combining vector and keyword search.

        Uses Reciprocal Rank Fusion (RRF) to merge rankings from both methods.

        Args:
            query: The text query
            query_embedding: The query vector
            limit: Maximum number of results
            alpha: Weight for vector search (0.0 = keyword only, 1.0 = vector only)

        Returns:
            List of (entity_id, combined_score) tuples
        """
        # Get results from both search methods
        vector_results = self.search_vector(query_embedding, limit * 2)
        keyword_results = self.search_keyword(query, limit * 2)

        # If one method fails or alpha is at extremes, return single method results
        if alpha >= 0.99 or not keyword_results:
            return vector_results[:limit]
        elif alpha <= 0.01 or not vector_results:
            return keyword_results[:limit]

        # Apply Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = defaultdict(float)

        # Process vector search results
        for rank, (entity_id, _) in enumerate(vector_results):
            rrf_scores[entity_id] += alpha * (1.0 / (self.rrf_k + rank + 1))

        # Process keyword search results
        for rank, (entity_id, _) in enumerate(keyword_results):
            rrf_scores[entity_id] += (1 - alpha) * (1.0 / (self.rrf_k + rank + 1))

        # Sort by combined RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]

        # Normalize scores to 0-1 range
        if sorted_results:
            max_score = sorted_results[0][1]
            normalized_results = [
                (entity_id, score / max_score) for entity_id, score in sorted_results
            ]
            return normalized_results

        return []

    def get_entity_scores(self, entity_ids: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get detailed scores for specific entities from both search methods.

        Useful for debugging and understanding why certain results were ranked higher.

        Args:
            entity_ids: List of entity IDs to get scores for

        Returns:
            Dictionary mapping entity IDs to their vector and keyword scores
        """
        scores: Dict[str, Dict[str, float]] = {}

        # This is a utility method for debugging - not part of the interface
        # Would need to store results from last search to implement properly
        logger.debug(f"Score details requested for entities: {entity_ids}")

        return scores


class MultiTableHybridSearch:
    """
    Manages hybrid search across multiple tables.

    This class coordinates hybrid search instances for different content tables,
    allowing unified search across all game content.
    """

    def __init__(
        self,
        db_manager: DatabaseManagerProtocol,
        embedding_model: Optional["SentenceTransformer"] = None,
        rrf_k: int = 60,
    ):
        """
        Initialize multi-table hybrid search coordinator.

        Args:
            db_manager: Database manager for accessing SQLite
            embedding_model: Optional sentence transformer for vector search
            rrf_k: Reciprocal Rank Fusion constant
        """
        self.db_manager = db_manager
        self.embedding_model = embedding_model
        self.rrf_k = rrf_k
        self._search_instances: Dict[str, HybridSearch] = {}

    def get_search_instance(self, table_name: str) -> HybridSearch:
        """
        Get or create a hybrid search instance for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            HybridSearch instance for the table
        """
        if table_name not in self._search_instances:
            self._search_instances[table_name] = HybridSearch(
                self.db_manager, table_name, self.embedding_model, self.rrf_k
            )

        return self._search_instances[table_name]

    def search_tables(
        self,
        tables: List[str],
        query: str,
        query_embedding: npt.NDArray[Any],
        limit_per_table: int = 5,
        alpha: float = 0.7,
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Perform hybrid search across multiple tables.

        Args:
            tables: List of table names to search
            query: The text query
            query_embedding: The query vector
            limit_per_table: Maximum results per table
            alpha: Weight for vector search

        Returns:
            Dictionary mapping table names to their search results
        """
        results = {}

        for table in tables:
            search_instance = self.get_search_instance(table)
            table_results = search_instance.hybrid_search(
                query, query_embedding, limit_per_table, alpha
            )

            if table_results:
                results[table] = table_results

        return results
