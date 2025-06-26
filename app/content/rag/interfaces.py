"""
Interfaces for the RAG (Retrieval-Augmented Generation) system components.

This module defines abstract base classes that establish contracts for modular
components in the RAG system, following the Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

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
