"""
Re-ranking implementations for the RAG system.

This module provides concrete implementations of the IReranker interface,
offering various strategies to improve search result relevance.
"""

from typing import List

from app.content.rag.interfaces import IReranker
from app.models.rag import KnowledgeResult


class ExactMatchReranker(IReranker):
    """
    Re-ranker that boosts scores for results containing exact query matches.

    This implementation checks for case-insensitive exact matches of the query
    text within the content and applies a configurable score boost.
    """

    def __init__(self, boost_amount: float = 0.2):
        """
        Initialize the ExactMatchReranker.

        Args:
            boost_amount: Amount to add to relevance scores for exact matches.
                         Defaults to 0.2.
        """
        self.boost_amount = boost_amount

    def rerank(
        self, query: str, results: List[KnowledgeResult]
    ) -> List[KnowledgeResult]:
        """
        Re-rank results by boosting scores for exact query matches.

        Args:
            query: The original search query text
            results: List of knowledge results to re-rank

        Returns:
            A new list of KnowledgeResult objects with updated scores,
            sorted by relevance in descending order
        """
        if not results:
            return results

        # Create a copy of results to avoid modifying the original list
        reranked_results = []
        query_lower = query.lower()

        for result in results:
            # Create a copy of the result to avoid modifying the original
            new_result = result.model_copy()

            # Check for case-insensitive exact match
            if query_lower in result.content.lower():
                new_result.relevance_score += self.boost_amount

            reranked_results.append(new_result)

        # Sort by relevance score in descending order
        reranked_results.sort(key=lambda r: r.relevance_score, reverse=True)

        return reranked_results


class EntityMatchReranker(IReranker):
    """
    Re-ranker that boosts scores based on entity matches from query context.

    This implementation extracts the entity-based boosting logic from the
    original RAGService implementation, checking for specific entity types
    (spells, creatures) in the query context.
    """

    def __init__(self, boost_amount: float = 0.5):
        """
        Initialize the EntityMatchReranker.

        Args:
            boost_amount: Amount to add to relevance scores for entity matches.
                         Defaults to 0.5 (matching original implementation).
        """
        self.boost_amount = boost_amount

    def rerank(
        self, query: str, results: List[KnowledgeResult]
    ) -> List[KnowledgeResult]:
        """
        Re-rank results by boosting scores for entity matches.

        Note: This reranker requires RAGQuery context to be available in the
        KnowledgeResult metadata under the 'query_context' key.

        Args:
            query: The original search query text (not used in this implementation)
            results: List of knowledge results to re-rank

        Returns:
            A new list of KnowledgeResult objects with updated scores,
            sorted by relevance in descending order
        """
        if not results:
            return results

        # Create a copy of results to avoid modifying the original list
        reranked_results = []

        for result in results:
            # Create a copy of the result to avoid modifying the original
            new_result = result.model_copy()

            # Extract query context from metadata if available
            query_context = result.metadata.get("query_context", {})

            # Check for spell matches
            if (
                query_context.get("spell_name")
                and result.source == "spells"
                and query_context["spell_name"].lower() in result.content.lower()
            ):
                new_result.relevance_score += self.boost_amount

            # Check for creature matches
            elif (
                query_context.get("creature")
                and result.source == "monsters"
                and query_context["creature"].lower() in result.content.lower()
            ):
                new_result.relevance_score += self.boost_amount

            # Check for class matches
            elif (
                query_context.get("class")
                and result.source in ["classes", "subclasses", "levels"]
                and query_context["class"].lower() in result.content.lower()
            ):
                new_result.relevance_score += self.boost_amount

            # Check for race matches
            elif (
                query_context.get("race")
                and result.source in ["races", "subraces", "traits"]
                and query_context["race"].lower() in result.content.lower()
            ):
                new_result.relevance_score += self.boost_amount

            # Check for equipment matches
            elif (
                query_context.get("item")
                and result.source in ["equipment", "magic_items"]
                and query_context["item"].lower() in result.content.lower()
            ):
                new_result.relevance_score += self.boost_amount

            # Deprioritize ability scores unless they're explicitly mentioned
            elif (
                result.source == "ability_scores"
                and "ability" not in query.lower()
                and "score" not in query.lower()
            ):
                # Reduce score for ability scores in general queries
                new_result.relevance_score *= 0.5

            reranked_results.append(new_result)

        # Sort by relevance score in descending order
        reranked_results.sort(key=lambda r: r.relevance_score, reverse=True)

        return reranked_results
