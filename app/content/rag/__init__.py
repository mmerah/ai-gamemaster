"""
RAG (Retrieval-Augmented Generation) services using LangChain for semantic search.
"""

import os

# Always export NoOpRAGService as it has no dependencies
from .no_op_rag_service import NoOpRAGService

# Only import heavy RAG services if RAG is enabled to avoid loading PyTorch/transformers
if os.environ.get("RAG_ENABLED", "true").lower() != "false":
    from app.content.rag.d5e_db_knowledge_base_manager import D5eDbKnowledgeBaseManager
    from app.content.rag.db_knowledge_base_manager import DbKnowledgeBaseManager
    from app.content.rag.knowledge_base import KnowledgeBaseManager
    from app.content.rag.query_engine import SimpleQueryEngine
    from app.content.rag.rag_service import RAGService

    __all__ = [
        "KnowledgeBaseManager",
        "DbKnowledgeBaseManager",
        "D5eDbKnowledgeBaseManager",
        "NoOpRAGService",
        "SimpleQueryEngine",
        "RAGService",
    ]
else:
    # When RAG is disabled, don't import the heavy services
    # Type checkers will handle the conditional imports properly
    __all__ = ["NoOpRAGService"]
