"""
JSON-based knowledge base implementations for the RAG system.
"""
import json
import os
import logging
from typing import Any, Dict, List, Optional
from app.core.rag_interfaces import KnowledgeBase, KnowledgeResult

logger = logging.getLogger(__name__)


class JSONKnowledgeBase(KnowledgeBase):
    """
    Base class for JSON file-based knowledge bases.
    Provides common functionality for loading and querying JSON data.
    """
    
    def __init__(self, knowledge_type: str, file_path: str):
        self.knowledge_type = knowledge_type
        self.file_path = file_path
        self.data = {}
        self.last_modified = 0
        self.reload()
    
    def get_knowledge_type(self) -> str:
        return self.knowledge_type
    
    def reload(self) -> bool:
        """Reload the knowledge base from the JSON file."""
        try:
            if not os.path.exists(self.file_path):
                logger.warning(f"Knowledge base file not found: {self.file_path}")
                self.data = {}
                return False
            
            # Check if file was modified
            current_modified = os.path.getmtime(self.file_path)
            if current_modified <= self.last_modified and self.data:
                return True  # No need to reload
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.last_modified = current_modified
            logger.info(f"Loaded knowledge base '{self.knowledge_type}' from {self.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading knowledge base '{self.knowledge_type}' from {self.file_path}: {e}")
            self.data = {}
            return False
    
    def query(self, query: str, context: Dict[str, Any] = None) -> List[KnowledgeResult]:
        """Enhanced query implementation with relevance threshold and global ranking."""
        if not self.data:
            return []
        
        results = []
        query_terms = query.lower().split()
        
        # Search through all knowledge items
        for key, value in self.data.items():
            relevance_score = self._calculate_relevance(key, value, query_terms, context)
            # Apply relevance threshold - only include results with meaningful relevance
            if relevance_score >= 0.5:
                content = self._format_knowledge_item(key, value)
                results.append(KnowledgeResult(
                    content=content,
                    source=self.knowledge_type,
                    relevance_score=relevance_score,
                    metadata={"key": key, "type": type(value).__name__}
                ))
        
        # Sort by relevance and return top results
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:3]  # Return top 3 results to avoid overwhelming the prompt
    
    def _calculate_relevance(self, key: str, value: Any, query_terms: List[str], context: Dict[str, Any] = None) -> float:
        """Enhanced relevance calculation with weighted scoring."""
        score = 0.0
        
        # Convert value to searchable text
        searchable_text = self._get_searchable_text(key, value).lower()
        key_lower = key.lower()
        
        # Enhanced term matching with different weights
        for term in query_terms:
            term_lower = term.lower()
            
            # Exact key match (highest priority)
            if term_lower == key_lower:
                score += 10.0
            # Key contains term (high priority)
            elif term_lower in key_lower:
                score += 5.0
            # Key starts with term
            elif key_lower.startswith(term_lower):
                score += 4.0
            
            # Content matching with lower weights
            if term_lower in searchable_text:
                # Count occurrences for frequency boost
                occurrences = searchable_text.count(term_lower)
                score += min(occurrences * 0.5, 2.0)  # Cap at 2.0 for frequency
        
        # Semantic matching for related terms
        score += self._semantic_relevance_boost(key_lower, searchable_text, query_terms)
        
        # Context-based scoring
        if context:
            context_boost = self._context_relevance_boost(key, value, context)
            score += context_boost
        
        # Length penalty for very long content (prefer concise, relevant info)
        if len(searchable_text) > 500:
            score *= 0.9
        
        return score
    
    def _semantic_relevance_boost(self, key_lower: str, searchable_text: str, query_terms: List[str]) -> float:
        """Add semantic relevance for related terms."""
        boost = 0.0
        
        # Define semantic relationships for D&D terms
        semantic_mappings = {
            'damage': ['harm', 'hurt', 'injury', 'wound', 'attack', 'strike'],
            'heal': ['cure', 'restore', 'recovery', 'mend', 'fix'],
            'spell': ['magic', 'incantation', 'cantrip', 'enchantment'],
            'attack': ['hit', 'strike', 'assault', 'combat', 'fight'],
            'defense': ['protect', 'shield', 'guard', 'block', 'armor'],
            'cold': ['ice', 'frost', 'freeze', 'chill'],
            'fire': ['flame', 'burn', 'heat', 'ignite'],
            'force': ['push', 'energy', 'power', 'strength']
        }
        
        for term in query_terms:
            term_lower = term.lower()
            for base_term, related_terms in semantic_mappings.items():
                if term_lower == base_term:
                    # Boost if related terms found in content
                    for related in related_terms:
                        if related in searchable_text or related in key_lower:
                            boost += 0.3
                elif term_lower in related_terms:
                    # Boost if base term found in content
                    if base_term in searchable_text or base_term in key_lower:
                        boost += 0.3
        
        return min(boost, 2.0)  # Cap semantic boost
    
    def _get_searchable_text(self, key: str, value: Any) -> str:
        """Convert a knowledge item to searchable text."""
        if isinstance(value, str):
            return f"{key} {value}"
        elif isinstance(value, dict):
            # Flatten dictionary to searchable text
            text_parts = [key]
            for k, v in value.items():
                if isinstance(v, (str, int, float)):
                    text_parts.append(f"{k} {v}")
                elif isinstance(v, list):
                    text_parts.extend([str(item) for item in v if isinstance(item, (str, int, float))])
            return " ".join(text_parts)
        elif isinstance(value, list):
            text_parts = [key]
            text_parts.extend([str(item) for item in value if isinstance(item, (str, int, float))])
            return " ".join(text_parts)
        else:
            return f"{key} {str(value)}"
    
    def _format_knowledge_item(self, key: str, value: Any) -> str:
        """Enhanced formatting for better readability in prompts."""
        if isinstance(value, str):
            return f"{key}: {value}"
        elif isinstance(value, dict):
            # Prioritize important fields for spells and monsters
            important_fields = ['name', 'level', 'damage', 'range', 'duration', 'description', 
                              'armor_class', 'hit_points', 'challenge', 'abilities']
            
            formatted_parts = []
            # Add important fields first
            for field in important_fields:
                if field in value:
                    formatted_parts.append(f"{field}={value[field]}")
            
            # Add remaining fields
            for k, v in value.items():
                if k not in important_fields:
                    if isinstance(v, (str, int, float, bool)):
                        formatted_parts.append(f"{k}={v}")
                    elif isinstance(v, list) and len(v) <= 3:  # Only short lists
                        formatted_parts.append(f"{k}=[{', '.join([str(item) for item in v])}]")
            
            return f"{key}: {', '.join(formatted_parts[:8])}"  # Limit length
        elif isinstance(value, list):
            return f"{key}: {', '.join([str(item) for item in value[:5]])}"  # Limit to 5 items
        else:
            return f"{key}: {str(value)}"
    
    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format a dictionary for display."""
        parts = []
        for k, v in data.items():
            if isinstance(v, (str, int, float)):
                parts.append(f"{k}={v}")
            elif isinstance(v, list):
                parts.append(f"{k}=[{', '.join([str(item) for item in v])}]")
        return f"{{{', '.join(parts)}}}"
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Calculate additional relevance based on context. Override in subclasses."""
        return 0.0


class RulesKnowledgeBase(JSONKnowledgeBase):
    """Knowledge base for D&D 5e rules and mechanics."""
    
    def __init__(self, file_path: str = "knowledge/rules.json"):
        super().__init__("rules", file_path)
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Enhanced context boost for rules based on specific contexts."""
        boost = 0.0
        
        # Boost spell-related rules when casting spells
        if context.get("spell_name"):
            spell_keywords = ["spell", "magic", "concentration", "component", "casting", "verbal", "somatic", "material"]
            if any(word in key.lower() for word in spell_keywords):
                boost += 2.0
        
        # Boost combat rules during combat
        if context.get("creature"):
            combat_keywords = ["combat", "attack", "damage", "armor", "hit", "initiative", "turn", "action"]
            if any(word in key.lower() for word in combat_keywords):
                boost += 2.0
        
        # Boost skill rules for skill checks
        if context.get("skill"):
            skill_keywords = ["skill", "check", "ability", "proficiency", "advantage", "disadvantage"]
            if any(word in key.lower() for word in skill_keywords):
                boost += 2.0
        
        return boost


class LoreKnowledgeBase(JSONKnowledgeBase):
    """Knowledge base for campaign-specific world lore."""
    
    def __init__(self, campaign_id: str = None, file_path: str = None):
        if not file_path:
            if campaign_id:
                file_path = f"knowledge/lore_{campaign_id}.json"
            else:
                file_path = "knowledge/lore.json"
        super().__init__("lore", file_path)
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Enhanced context boost for lore based on location and NPCs."""
        boost = 0.0
        
        # Boost location-related lore
        if context.get("location"):
            location = context["location"].lower()
            searchable = self._get_searchable_text(key, value).lower()
            if location in key.lower():
                boost += 5.0  # Exact location match
            elif location in searchable:
                boost += 3.0  # Location mentioned in content
        
        # Boost NPC-related lore
        if context.get("npc_name"):
            npc_name = context["npc_name"].lower()
            searchable = self._get_searchable_text(key, value).lower()
            if npc_name in key.lower():
                boost += 5.0  # Exact NPC match
            elif npc_name in searchable:
                boost += 3.0  # NPC mentioned in content
        
        return boost


class AdventureKnowledgeBase(JSONKnowledgeBase):
    """Knowledge base for current adventure progress and context."""
    
    def __init__(self, campaign_id: str = None, file_path: str = None):
        if not file_path:
            if campaign_id:
                file_path = f"knowledge/adventure_{campaign_id}.json"
            else:
                file_path = "knowledge/adventure.json"
        super().__init__("adventure", file_path)
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Enhanced context boost for adventure based on recent events."""
        boost = 0.0
        
        # Boost recent events
        if context.get("recent_events"):
            recent_text = context["recent_events"].lower()
            searchable = self._get_searchable_text(key, value).lower()
            
            # Check for overlapping keywords
            recent_words = set(recent_text.split())
            searchable_words = set(searchable.split())
            overlap = len(recent_words.intersection(searchable_words))
            
            if overlap > 0:
                boost += min(overlap * 1.0, 5.0)  # Cap at 5.0
        
        return boost


class MonstersKnowledgeBase(JSONKnowledgeBase):
    """Knowledge base for monster stats and abilities."""
    
    def __init__(self, file_path: str = "knowledge/monsters.json"):
        super().__init__("monsters", file_path)
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Enhanced context boost for monster data."""
        boost = 0.0
        
        # Boost specific creature matches
        if context.get("creature"):
            creature = context["creature"].lower()
            searchable = self._get_searchable_text(key, value).lower()
            
            if creature == key.lower():
                boost += 10.0  # Exact creature match
            elif creature in key.lower():
                boost += 7.0  # Partial key match
            elif creature in searchable:
                boost += 3.0  # Creature mentioned in content
        
        return boost


class NPCsKnowledgeBase(JSONKnowledgeBase):
    """Knowledge base for NPC personalities, backgrounds, and relationships."""
    
    def __init__(self, campaign_id: str = None, file_path: str = None):
        if not file_path:
            if campaign_id:
                file_path = f"knowledge/npcs_{campaign_id}.json"
            else:
                file_path = "knowledge/npcs.json"
        super().__init__("npcs", file_path)
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Enhanced context boost for NPC data."""
        boost = 0.0
        
        # Boost specific NPC matches
        if context.get("npc_name"):
            npc_name = context["npc_name"].lower()
            searchable = self._get_searchable_text(key, value).lower()
            
            if npc_name == key.lower():
                boost += 10.0  # Exact NPC match
            elif npc_name in key.lower():
                boost += 7.0  # Partial key match
            elif npc_name in searchable:
                boost += 3.0  # NPC mentioned in content
        
        return boost


class SpellsKnowledgeBase(JSONKnowledgeBase):
    """Knowledge base for spell descriptions and mechanics."""
    
    def __init__(self, file_path: str = "knowledge/spells.json"):
        super().__init__("spells", file_path)
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Enhanced context boost for spell data."""
        boost = 0.0
        
        # Boost specific spell matches
        if context.get("spell_name"):
            spell_name = context["spell_name"].lower().replace('_', ' ')
            key_normalized = key.lower().replace('_', ' ')
            searchable = self._get_searchable_text(key, value).lower()
            
            if spell_name == key_normalized:
                boost += 10.0  # Exact spell match
            elif spell_name in key_normalized or key_normalized in spell_name:
                boost += 7.0  # Partial spell name match
            elif spell_name in searchable:
                boost += 3.0  # Spell mentioned in content
        
        return boost


class EquipmentKnowledgeBase(JSONKnowledgeBase):
    """Knowledge base for weapons, armor, and equipment."""
    
    def __init__(self, file_path: str = "knowledge/equipment.json"):
        super().__init__("equipment", file_path)
    
    def _context_relevance_boost(self, key: str, value: Any, context: Dict[str, Any]) -> float:
        """Context boost for equipment based on usage context."""
        boost = 0.0
        
        # Boost weapon info during combat
        if context.get("creature") or any(word in context.get("action", "").lower() 
                                        for word in ["attack", "hit", "strike", "weapon"]):
            if any(word in key.lower() for word in ["weapon", "sword", "bow", "axe", "damage"]):
                boost += 2.0
        
        # Boost armor info when taking damage
        if any(word in context.get("action", "").lower() 
               for word in ["damage", "hit", "attack", "armor"]):
            if any(word in key.lower() for word in ["armor", "shield", "protection", "ac"]):
                boost += 2.0
        
        return boost
