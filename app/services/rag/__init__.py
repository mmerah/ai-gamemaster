"""
RAG (Retrieval-Augmented Generation) services using LangChain for semantic search.
"""
import os

# Always export NoOpRAGService as it has no dependencies
from .no_op_rag_service import NoOpRAGService

# Only import heavy RAG services if RAG is enabled to avoid loading PyTorch/transformers
if os.environ.get('RAG_ENABLED', 'true').lower() != 'false':
    from .rag_service import RAGServiceImpl
    from .query_engine import RAGQueryEngineImpl
    from .knowledge_bases import KnowledgeBaseManager
    __all__ = ['RAGServiceImpl', 'RAGQueryEngineImpl', 'KnowledgeBaseManager', 'NoOpRAGService']
else:
    # Provide dummy classes for type checking when RAG is disabled
    RAGServiceImpl = None
    RAGQueryEngineImpl = None
    KnowledgeBaseManager = None
    __all__ = ['NoOpRAGService']
