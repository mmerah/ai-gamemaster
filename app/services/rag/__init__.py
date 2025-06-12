"""
RAG (Retrieval-Augmented Generation) services using LangChain for semantic search.
"""

import os

# Always export NoOpRAGService as it has no dependencies
from .no_op_rag_service import NoOpRAGService

# Only import heavy RAG services if RAG is enabled to avoid loading PyTorch/transformers
if os.environ.get("RAG_ENABLED", "true").lower() != "false":
    from .d5e_db_knowledge_base_manager import D5eDbKnowledgeBaseManager
    from .db_knowledge_base_manager import DbKnowledgeBaseManager
    from .knowledge_bases import KnowledgeBaseManager
    from .query_engine import RAGQueryEngineImpl
    from .rag_service import RAGServiceImpl

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
