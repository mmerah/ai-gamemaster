"""
RAG processor for AI response processing.
"""

import logging
import re
from typing import List, Optional

from app.core.ai_interfaces import IRAGService
from app.core.repository_interfaces import IGameStateRepository
from app.providers.ai.schemas import AIResponse
from app.services.ai_processors.interfaces import IRagProcessor

logger = logging.getLogger(__name__)


class RagProcessor(IRagProcessor):
    """Handles RAG event logging from AI responses."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        rag_service: Optional[IRAGService] = None,
    ):
        self.game_state_repo = game_state_repo
        self.rag_service = rag_service
        self._stopwords = {
            "the",
            "and",
            "a",
            "an",
            "to",
            "of",
            "in",
            "on",
            "at",
            "for",
            "with",
            "by",
            "is",
            "it",
            "as",
            "from",
            "that",
            "this",
            "was",
            "are",
            "be",
            "or",
            "but",
            "if",
            "then",
            "so",
            "do",
            "did",
            "has",
            "have",
            "had",
        }

    def process_rag_event_logging(self, ai_response: AIResponse) -> None:
        """Update RAG event log with AI response narrative."""
        try:
            # Only attempt to update event log if we have a narrative
            if not ai_response.narrative:
                return

            game_state = self.game_state_repo.get_game_state()

            # Only update if we have a campaign ID
            if not game_state.campaign_id:
                return

            # Generate event summary from narrative
            summary = ai_response.narrative.strip()[:300]

            # Simple keyword extraction
            keywords = self._extract_keywords(summary)

            # Use the injected RAG service if available
            if self.rag_service and hasattr(self.rag_service, "add_event"):
                self.rag_service.add_event(
                    campaign_id=game_state.campaign_id,
                    event_summary=summary,
                    keywords=keywords,
                )
                logger.debug("Event log updated with new event from AI response.")
            else:
                logger.debug(
                    "RAG service not available or does not support event logging"
                )
        except Exception as e:
            # Log error but don't fail the response processing
            logger.warning(f"Failed to update event log after AI response: {e}")

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for RAG indexing."""
        words = re.findall(r"\b\w+\b", text.lower())
        keywords = list({w for w in words if len(w) > 3 and w not in self._stopwords})[
            :8
        ]
        return keywords
