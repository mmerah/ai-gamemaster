"""
Interfaces for the RAG (Retrieval-Augmented Generation) system components.

This module defines abstract base classes that establish contracts for modular
components in the RAG system, following the Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import numpy.typing as npt
from langchain_core.documents import Document

from app.models.game_state.main import GameStateModel
from app.models.rag import KnowledgeResult, RAGQuery


class IReranker(ABC):
    """
    Interface for re-ranking search results based on additional criteria.

    Re-rankers can apply various strategies to adjust relevance scores
    and reorder results to improve search quality.
    """

    @abstractmethod
    def rerank(
        self, query: str, results: List[KnowledgeResult]
    ) -> List[KnowledgeResult]:
        """
        Re-rank a list of knowledge results based on the query.

        Args:
            query: The original search query text
            results: List of knowledge results to re-rank

        Returns:
            A new list of KnowledgeResult objects, potentially with updated
            relevance scores and in a new order
        """
        pass


class IQueryEngine(ABC):
    """
    Interface for analyzing player actions and generating RAG queries.

    Query engines interpret player actions in the context of the game state
    and produce structured queries for the knowledge retrieval system.
    """

    @abstractmethod
    def analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]:
        """
        Analyze a player action and generate relevant RAG queries.

        Args:
            action: The player's action text
            game_state: Current game state for context

        Returns:
            List of RAGQuery objects to execute against the knowledge base
        """
        pass


class IChunker(ABC):
    """
    Interface for chunking documents into smaller, searchable pieces.

    Chunkers break down large documents (e.g., lore, rules) into smaller
    chunks suitable for embedding and retrieval, preserving context and
    structure information in metadata.
    """

    @abstractmethod
    def chunk(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[Document]:
        """
        Split content into chunks suitable for embedding and search.

        Args:
            content: The text content to chunk
            metadata: Base metadata to include with each chunk
            chunk_size: Target size for each chunk (in characters or tokens)
            chunk_overlap: Amount of overlap between chunks

        Returns:
            List of Document objects, each containing a chunk of the content
            with appropriate metadata
        """
        pass


class IHybridSearch(ABC):
    """
    Interface for hybrid search combining vector and keyword-based search.

    Hybrid search leverages both semantic similarity (vector search) and
    exact/partial matches (keyword search) to improve retrieval quality.
    The interface supports individual search methods and a combined approach
    with configurable weighting.
    """

    @abstractmethod
    def search_vector(
        self, query_embedding: npt.NDArray[Any], limit: int
    ) -> List[Tuple[str, float]]:
        """
        Perform vector similarity search using embeddings.

        Args:
            query_embedding: The query vector (numpy array)
            limit: Maximum number of results to return

        Returns:
            List of tuples containing (entity_id, similarity_score)
            ordered by descending similarity
        """
        pass

    @abstractmethod
    def search_keyword(self, query: str, limit: int) -> List[Tuple[str, float]]:
        """
        Perform keyword-based search using BM25 or similar algorithm.

        Args:
            query: The text query
            limit: Maximum number of results to return

        Returns:
            List of tuples containing (entity_id, relevance_score)
            ordered by descending relevance
        """
        pass

    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        query_embedding: npt.NDArray[Any],
        limit: int,
        alpha: float = 0.7,
    ) -> List[Tuple[str, float]]:
        """
        Perform hybrid search combining vector and keyword search results.

        Uses Reciprocal Rank Fusion (RRF) or similar algorithm to merge
        the rankings from both search methods.

        Args:
            query: The text query
            query_embedding: The query vector
            limit: Maximum number of results to return
            alpha: Weight for vector search (0.0 = keyword only, 1.0 = vector only)

        Returns:
            List of tuples containing (entity_id, combined_score)
            ordered by descending combined score
        """
        pass
