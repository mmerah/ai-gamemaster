"""
RAG routes for testing and demonstration.
"""
import logging
from flask import Blueprint, request, jsonify
from app.core.container import get_container

logger = logging.getLogger(__name__)

rag_bp = Blueprint('rag', __name__, url_prefix='/api/rag')


@rag_bp.route('/test', methods=['POST'])
def test_rag():
    """Test RAG functionality with a query."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        
        # Get RAG service from container
        container = get_container()
        rag_service = container.get_rag_service()
        
        if not rag_service:
            return jsonify({'error': 'RAG service not available'}), 500
        
        # Perform RAG query
        results = rag_service.query(query)
        
        # Format results for response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'knowledge_base': result.source,
                'content': result.content,
                'score': result.relevance_score,
                'metadata': result.metadata
            })
        
        # Log the RAG context as requested
        if formatted_results:
            logger.info("=== RAG CONTEXT LOG ===")
            logger.info(f"Query: {query}")
            logger.info(f"Results ({len(formatted_results)} found):")
            for i, result in enumerate(formatted_results, 1):
                logger.info(f"  {i}. [{result['knowledge_base']}] {result['content']} (Score: {result['score']:.3f})")
            logger.info("=== END RAG CONTEXT ===")
        else:
            logger.info(f"=== RAG CONTEXT LOG === Query: {query} - No results found === END RAG CONTEXT ===")
        
        return jsonify({
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error in RAG test endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/status', methods=['GET'])
def rag_status():
    """Get RAG system status."""
    try:
        container = get_container()
        rag_service = container.get_rag_service()
        
        if not rag_service:
            return jsonify({
                'status': 'unavailable',
                'knowledge_bases': []
            })
        
        # Get knowledge base info
        kb_info = []
        for kb_name, kb in rag_service.knowledge_bases.items():
            kb_info.append({
                'name': kb_name,
                'type': type(kb).__name__,
                'loaded': True  # If it's in the dict, it's loaded
            })
        
        return jsonify({
            'status': 'available',
            'knowledge_bases': kb_info
        })
        
    except Exception as e:
        logger.error(f"Error in RAG status endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
