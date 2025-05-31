"""
Core interfaces for the RAG (Retrieval-Augmented Generation) system.
Simplified using LangChain abstractions.
"""
from typing import Any, Dict, List
from pydantic import BaseModel
from enum import Enum
from langchain_core.documents import Document


class QueryType(Enum):
    """Types of RAG queries based on player actions."""
    COMBAT = "combat"
    SPELL_CASTING = "spell_casting" 
    SKILL_CHECK = "skill_check"
    SOCIAL_INTERACTION = "social_interaction"
    EXPLORATION = "exploration"
    RULES_LOOKUP = "rules_lookup"
    GENERAL = "general"


class KnowledgeResult(BaseModel):
    """Single piece of retrieved knowledge."""
    content: str
    source: str  # Which knowledge base this came from
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = {}
    
    @classmethod
    def from_document(cls, doc: Document, source: str, score: float = 1.0) -> 'KnowledgeResult':
        """Create from LangChain Document."""
        return cls(
            content=doc.page_content,
            source=source,
            relevance_score=score,
            metadata=doc.metadata
        )


class RAGQuery(BaseModel):
    """A query to be executed against knowledge bases."""
    query_text: str
    query_type: QueryType
    context: Dict[str, Any] = {}
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
        current_items = []
        
        # Group by source
        for result in self.results:
            if result.source != current_source:
                if current_items:
                    formatted_sections.append(f"{current_source}:\n" + "\n".join(f"- {item}" for item in current_items))
                current_source = result.source
                current_items = [result.content]
            else:
                current_items.append(result.content)
        
        # Add the last group
        if current_items:
            formatted_sections.append(f"{current_source}:\n" + "\n".join(f"- {item}" for item in current_items))
        
        return "\n\n".join(formatted_sections)
    
    def debug_format(self) -> str:
        """Format results for debug logging."""
        if not self.results:
            return "No RAG results retrieved."
        
        lines = [f"RAG Retrieved {len(self.results)} results in {self.execution_time_ms:.1f}ms:"]
        for result in self.results:
            lines.append(f"  [{result.source}] {result.content[:100]}{'...' if len(result.content) > 100 else ''}")
        return "\n".join(lines)


class RAGService:
    """Main RAG service interface - simplified with LangChain."""
    
    def get_relevant_knowledge(self, action: str, game_state: Any) -> RAGResults:
        """Get relevant knowledge for a player action."""
        raise NotImplementedError
    
    def analyze_action(self, action: str, game_state: Any) -> List[RAGQuery]:
        """Analyze a player action and generate relevant RAG queries."""
        raise NotImplementedError
