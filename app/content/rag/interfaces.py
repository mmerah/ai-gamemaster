"""
Interfaces for the RAG (Retrieval-Augmented Generation) system components.

This module defines abstract base classes that establish contracts for modular
components in the RAG system, following the Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import List

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
