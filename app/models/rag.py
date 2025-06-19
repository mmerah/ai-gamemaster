"""
RAG (Retrieval-Augmented Generation) related type definitions.

This module contains all RAG-related model definitions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field

# ===== Enums =====


class QueryType(Enum):
    """Types of RAG queries based on player actions."""

    COMBAT = "combat"
    SPELL_CASTING = "spell_casting"
    SKILL_CHECK = "skill_check"
    SOCIAL_INTERACTION = "social_interaction"
    EXPLORATION = "exploration"
    RULES_LOOKUP = "rules_lookup"
    GENERAL = "general"


# ===== Pydantic Models =====


class KnowledgeResult(BaseModel):
    """Single piece of retrieved knowledge."""

    content: str
    source: str  # Which knowledge base this came from
    relevance_score: float = 1.0
    metadata: Dict[
        str, Any
    ] = {}  # JUSTIFIED: LangChain document metadata can contain arbitrary fields

    @classmethod
    def from_document(
        cls, doc: Document, source: str, score: float = 1.0
    ) -> "KnowledgeResult":
        """Create from LangChain Document."""
        return cls(
            content=doc.page_content,
            source=source,
            relevance_score=score,
            metadata=doc.metadata,
        )


class RAGQuery(BaseModel):
    """A query to be executed against knowledge bases."""

    query_text: str
    query_type: QueryType
    context: Dict[
        str, Any
    ] = {}  # JUSTIFIED: RAG query context varies by query type and knowledge domain
    knowledge_base_types: List[str] = []  # Which KBs to search, empty = all


class RAGResults(BaseModel):
    """Collection of results from RAG queries."""

    results: List[KnowledgeResult] = []
    total_queries: int = 0
    execution_time_ms: float = 0.0

    def has_results(self) -> bool:
        return len(self.results) > 0

    def format_for_prompt(self) -> str:
        """Format results for injection into AI prompt."""
        if not self.results:
            return ""

        formatted_sections = []
        current_source = None
        current_items: List[str] = []

        # Group by source
        for result in self.results:
            if result.source != current_source:
                if current_items:
                    formatted_sections.append(
                        f"{current_source}:\n"
                        + "\n".join(f"- {item}" for item in current_items)
                    )
                current_source = result.source
                current_items = [result.content]
            else:
                current_items.append(result.content)

        # Add the last group
        if current_items:
            formatted_sections.append(
                f"{current_source}:\n"
                + "\n".join(f"- {item}" for item in current_items)
            )

        return "RELEVANT KNOWLEDGE:\n" + "\n\n".join(formatted_sections)

    def debug_format(self) -> str:
        """Format results for debug logging."""
        if not self.results:
            return "No RAG results retrieved."

        lines = [
            f"RAG Retrieved {len(self.results)} results in {self.execution_time_ms:.1f}ms:"
        ]
        for result in self.results:
            lines.append(
                f"  [{result.source}] {result.content[:100]}{'...' if len(result.content) > 100 else ''}"
            )
        return "\n".join(lines)


class EventMetadataModel(BaseModel):
    """Metadata for RAG events."""

    timestamp: str = Field(..., description="ISO timestamp of the event")
    location: Optional[str] = Field(None, description="Location where event occurred")
    participants: Optional[List[str]] = Field(
        None, description="List of participants in the event"
    )
    combat_active: Optional[bool] = Field(
        None, description="Whether combat was active during event"
    )

    model_config = ConfigDict(extra="forbid")


class LoreDataModel(BaseModel):
    """Structure for lore entries."""

    id: str = Field(..., description="Lore entry ID")
    name: str = Field(..., description="Lore entry name")
    description: str = Field(..., description="Brief description")
    content: str = Field(..., description="Full lore content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(None, description="Lore category")

    model_config = ConfigDict(extra="forbid")
