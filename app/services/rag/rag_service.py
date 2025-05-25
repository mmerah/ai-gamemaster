"""
Main RAG service implementation with smart filtering and relevance optimization.
"""
import time
import logging
from typing import Any, Dict, List, Set
from app.core.rag_interfaces import RAGService, RAGQuery, RAGResults, KnowledgeBase, KnowledgeResult
from .query_engine import RAGQueryEngineImpl

logger = logging.getLogger(__name__)


class RAGServiceImpl(RAGService):
    """
    Enhanced RAG service with smart filtering and relevance optimization.
    """
    
    def __init__(self):
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}
        self.query_engine = RAGQueryEngineImpl()
        # Configuration for smart filtering
        self.relevance_threshold = 2.0  # Minimum relevance score to include
        self.max_results_per_category = 2  # Max results per knowledge base type
        self.max_total_results = 5  # Maximum total results to include in prompt
        self.similarity_threshold = 0.7  # Threshold for deduplication
        logger.info("Enhanced RAG Service initialized with smart filtering")
    
    def register_knowledge_base(self, kb: KnowledgeBase) -> None:
        """Register a knowledge base with the RAG service."""
        kb_type = kb.get_knowledge_type()
        self.knowledge_bases[kb_type] = kb
        logger.info(f"Registered knowledge base: {kb_type}")
    
    def get_relevant_knowledge(self, action: str, game_state: Any) -> RAGResults:
        """Get relevant knowledge for a player action with smart filtering."""
        start_time = time.time()
        
        try:
            # Generate queries based on the action
            queries = self.query_engine.analyze_action(action, game_state)
            logger.debug(f"Generated {len(queries)} RAG queries for action: '{action[:50]}...'")
            
            # Execute queries with smart filtering
            results = self.execute_queries_with_filtering(queries, action)
            results.execution_time_ms = (time.time() - start_time) * 1000
            
            if results.has_results():
                logger.info(f"RAG retrieved {len(results.results)} filtered knowledge items in {results.execution_time_ms:.1f}ms")
                logger.debug(f"Knowledge sources: {self._get_source_summary(results.results)}")
            else:
                logger.debug("No RAG results found for action")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in RAG knowledge retrieval: {e}", exc_info=True)
            return RAGResults(execution_time_ms=(time.time() - start_time) * 1000)
    
    def execute_queries_with_filtering(self, queries: List[RAGQuery], original_action: str = "") -> RAGResults:
        """Execute queries with smart filtering and optimization."""
        all_results = []
        results_by_source = {}
        
        # Group queries by priority (spell casting has highest priority)
        prioritized_queries = self._prioritize_queries(queries)
        
        for query in prioritized_queries:
            # Determine which knowledge bases to search
            kb_types_to_search = query.knowledge_base_types if query.knowledge_base_types else list(self.knowledge_bases.keys())
            
            for kb_type in kb_types_to_search:
                if kb_type in self.knowledge_bases:
                    try:
                        kb_results = self.knowledge_bases[kb_type].query(query.query_text, query.context)
                        
                        # Filter results by relevance threshold
                        filtered_results = [r for r in kb_results if r.relevance_score >= self.relevance_threshold]
                        
                        if filtered_results:
                            if kb_type not in results_by_source:
                                results_by_source[kb_type] = []
                            results_by_source[kb_type].extend(filtered_results)
                            
                        logger.debug(f"KB '{kb_type}': {len(kb_results)} raw -> {len(filtered_results)} filtered results")
                        
                    except Exception as e:
                        logger.error(f"Error querying knowledge base '{kb_type}': {e}")
                else:
                    logger.warning(f"Requested knowledge base '{kb_type}' not found")
        
        # Apply smart filtering per knowledge base
        for kb_type, results in results_by_source.items():
            # Sort by relevance and limit per category
            results.sort(key=lambda r: r.relevance_score, reverse=True)
            limited_results = results[:self.max_results_per_category]
            all_results.extend(limited_results)
        
        # Global filtering and optimization
        final_results = self._apply_global_filtering(all_results, original_action)
        
        return RAGResults(
            results=final_results,
            total_queries=len(queries)
        )
    
    def _prioritize_queries(self, queries: List[RAGQuery]) -> List[RAGQuery]:
        """Prioritize queries to ensure most important information is retrieved first."""
        from app.core.rag_interfaces import QueryType
        
        priority_order = {
            QueryType.SPELL_CASTING: 1,
            QueryType.COMBAT: 2,
            QueryType.SKILL_CHECK: 3,
            QueryType.SOCIAL_INTERACTION: 4,
            QueryType.EXPLORATION: 5,
            QueryType.GENERAL: 6
        }
        
        return sorted(queries, key=lambda q: priority_order.get(q.query_type, 10))
    
    def _apply_global_filtering(self, results: List[KnowledgeResult], original_action: str) -> List[KnowledgeResult]:
        """Apply global filtering to optimize results for prompt inclusion."""
        if not results:
            return []
        
        # Sort all results by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        # Deduplicate similar results
        deduplicated = self._deduplicate_results(results)
        
        # Apply relevance boost for action-specific keywords
        if original_action:
            deduplicated = self._boost_action_relevance(deduplicated, original_action)
            deduplicated.sort(key=lambda r: r.relevance_score, reverse=True)
        
        # Limit to maximum total results
        final_results = deduplicated[:self.max_total_results]
        
        # Ensure we have the most relevant information
        if len(final_results) > 0:
            logger.debug(f"Final relevance scores: {[round(r.relevance_score, 2) for r in final_results]}")
        
        return final_results
    
    def _deduplicate_results(self, results: List[KnowledgeResult]) -> List[KnowledgeResult]:
        """Remove duplicate or very similar results."""
        if not results:
            return []
        
        deduplicated = []
        seen_content = set()
        
        for result in results:
            # Create a simplified version for comparison
            content_key = self._normalize_content_for_comparison(result.content)
            
            # Check if we've seen similar content
            is_duplicate = False
            for seen in seen_content:
                if self._are_contents_similar(content_key, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
                seen_content.add(content_key)
        
        return deduplicated
    
    def _normalize_content_for_comparison(self, content: str) -> str:
        """Normalize content for similarity comparison."""
        # Remove formatting and convert to lowercase
        normalized = content.lower()
        # Remove common prefixes and suffixes
        normalized = normalized.replace(":", "").replace("=", " ").replace(",", " ")
        # Extract key terms (first 10 words after the key)
        words = normalized.split()
        return " ".join(words[:15])
    
    def _are_contents_similar(self, content1: str, content2: str) -> bool:
        """Check if two content strings are similar enough to be considered duplicates."""
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= self.similarity_threshold
    
    def _boost_action_relevance(self, results: List[KnowledgeResult], action: str) -> List[KnowledgeResult]:
        """Apply additional relevance boost based on direct action keywords."""
        action_words = set(action.lower().split())
        
        for result in results:
            content_words = set(result.content.lower().split())
            # Count direct keyword matches
            direct_matches = len(action_words.intersection(content_words))
            
            if direct_matches > 0:
                # Boost relevance for direct action keyword matches
                boost = min(direct_matches * 0.5, 2.0)  # Cap boost at 2.0
                result.relevance_score += boost
        
        return results
    
    def _get_source_summary(self, results: List[KnowledgeResult]) -> str:
        """Get a summary of knowledge sources used."""
        sources = {}
        for result in results:
            source = result.source
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
        
        return ", ".join([f"{src}({count})" for src, count in sources.items()])
    
    def execute_queries(self, queries: List[RAGQuery]) -> RAGResults:
        """Execute a list of RAG queries (legacy method for backward compatibility)."""
        return self.execute_queries_with_filtering(queries)
    
    def query(self, query_text: str, context: Dict[str, Any] = None) -> List[Any]:
        """Simple query method for direct text queries."""
        from app.core.rag_interfaces import RAGQuery, QueryType
        
        # Create a simple RAG query
        rag_query = RAGQuery(
            query_text=query_text,
            query_type=QueryType.GENERAL,
            context=context or {},
            knowledge_base_types=[]  # Query all knowledge bases
        )
        
        # Execute the query with filtering
        results = self.execute_queries_with_filtering([rag_query], query_text)
        
        # Return the results list
        return results.results
    
    def retrieve_knowledge(self, query: str, context: Dict[str, Any] = None) -> str:
        """Retrieve relevant knowledge for a query and format it for prompt inclusion."""
        if not self.query_engine:
            logger.warning("Query engine not initialized")
            return ""
        
        # Generate RAG queries
        queries = self.query_engine.analyze_action(query, context)
        if not queries:
            logger.debug("No RAG queries generated for action")
            return ""
        
        # Execute queries with smart filtering
        results = self.execute_queries_with_filtering(queries, query)
        
        if not results.has_results():
            logger.debug("No knowledge results found")
            return ""
        
        # Format results for prompt inclusion
        return self._format_knowledge_for_prompt(results.results)
    
    def _format_knowledge_for_prompt(self, results: List[KnowledgeResult]) -> str:
        """Format knowledge results for inclusion in AI prompts."""
        if not results:
            return ""
        
        # Group results by source for better organization
        grouped_results = {}
        for result in results:
            source = result.source
            if source not in grouped_results:
                grouped_results[source] = []
            grouped_results[source].append(result)
        
        formatted_sections = []
        
        # Define source priority for ordering
        source_priority = {
            'spells': 1,
            'monsters': 2,
            'rules': 3,
            'equipment': 4,
            'lore': 5,
            'npcs': 6,
            'adventure': 7
        }
        
        # Sort sources by priority
        sorted_sources = sorted(grouped_results.keys(), key=lambda x: source_priority.get(x, 10))
        
        for source in sorted_sources:
            source_results = grouped_results[source]
            if source_results:
                # Capitalize source name for header
                source_header = source.replace('_', ' ').title()
                
                # Format results for this source
                result_lines = []
                for result in source_results[:2]:  # Limit per source
                    # Clean up the content formatting
                    content = result.content.strip()
                    if not content.endswith('.'):
                        content += '.'
                    result_lines.append(f"• {content}")
                
                if result_lines:
                    section = f"**{source_header}:**\n" + "\n".join(result_lines)
                    formatted_sections.append(section)
        
        if formatted_sections:
            return "**Relevant Information:**\n\n" + "\n\n".join(formatted_sections)
        
        return ""
    
    def reload_knowledge_bases(self) -> Dict[str, bool]:
        """Reload all knowledge bases. Returns status per KB."""
        results = {}
        for kb_type, kb in self.knowledge_bases.items():
            try:
                success = kb.reload()
                results[kb_type] = success
                logger.info(f"Knowledge base '{kb_type}' reload: {'success' if success else 'failed'}")
            except Exception as e:
                logger.error(f"Error reloading knowledge base '{kb_type}': {e}")
                results[kb_type] = False
        return results
    
    def configure_filtering(self, relevance_threshold: float = None, max_results: int = None, 
                          max_per_category: int = None) -> None:
        """Configure filtering parameters."""
        if relevance_threshold is not None:
            self.relevance_threshold = relevance_threshold
            logger.info(f"Set relevance threshold to {relevance_threshold}")
            
        if max_results is not None:
            self.max_total_results = max_results
            logger.info(f"Set max total results to {max_results}")
            
        if max_per_category is not None:
            self.max_results_per_category = max_per_category
            logger.info(f"Set max results per category to {max_per_category}")
