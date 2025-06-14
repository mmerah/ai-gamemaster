"""
RAG (Retrieval-Augmented Generation) services using LangChain for semantic search.
"""

import os

# Always export NoOpRAGService as it has no dependencies
from .no_op_rag_service import NoOpRAGService

# Only import heavy RAG services if RAG is enabled to avoid loading PyTorch/transformers
if os.environ.get("RAG_ENABLED", "true").lower() != "false":
    from app.rag.d5e_db_knowledge_base_manager import D5eDbKnowledgeBaseManager
    from app.rag.db_knowledge_base_manager import DbKnowledgeBaseManager
    from app.rag.knowledge_base import KnowledgeBaseManager
    from app.rag.query_engine import RAGQueryEngineImpl
    from app.rag.service import RAGServiceImpl

    __all__ = [
        "KnowledgeBaseManager",
        "DbKnowledgeBaseManager",
        "D5eDbKnowledgeBaseManager",
        "NoOpRAGService",
        "RAGQueryEngineImpl",
        "RAGServiceImpl",
    ]
else:
    # When RAG is disabled, don't import the heavy services
    # Type checkers will handle the conditional imports properly
    __all__ = ["NoOpRAGService"]
