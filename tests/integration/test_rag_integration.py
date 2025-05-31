"""
Integration tests for the LangChain-based RAG system.
Tests end-to-end functionality with multiple scenarios including
spell casting, combat, exploration, and social interactions.
"""
import pytest
import sys
import os
from typing import Any
from unittest.mock import Mock

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Skip entire module if RAG is disabled
if os.environ.get('RAG_ENABLED', 'true').lower() == 'false':
    pytest.skip("RAG is disabled", allow_module_level=True)

from app.services.rag.rag_service import RAGServiceImpl
from app.core.rag_interfaces import QueryType, RAGResults

# Create a module-level RAG service instance to avoid reinitializing embeddings
_module_rag_service = None

def get_module_rag_service():
    """Get or create the module-level RAG service instance."""
    global _module_rag_service
    if _module_rag_service is None:
        _module_rag_service = RAGServiceImpl()
    return _module_rag_service


class MockGameState:
    """Mock game state for testing."""
    
    def __init__(self, **kwargs):
        self.campaign_id = kwargs.get('campaign_id', 'test_campaign')
        self.combat = Mock()
        self.combat.is_active = kwargs.get('in_combat', False)
        self.current_location = kwargs.get('current_location', {'name': 'Forest Clearing'})
        self.event_summary = kwargs.get('event_summary', [])
        self.active_lore_id = kwargs.get('active_lore_id', None)
        # Add support for RAG context persistence
        self._last_rag_context = kwargs.get('_last_rag_context', None)


@pytest.fixture(scope="module")
def rag_service():
    """Get the module-level RAG service instance for testing."""
    return get_module_rag_service()


@pytest.fixture
def mock_game_state():
    """Create a mock game state."""
    return MockGameState()


class TestRAGSpellCasting:
    """Test RAG retrieval for spell casting scenarios."""
    
    def test_ice_knife_on_goblin(self, rag_service, mock_game_state):
        """Test the primary scenario: Cast Ice Knife on Goblin."""
        action = "Cast Ice Knife on Goblin"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        # Verify results are returned
        assert results.has_results(), "Should return results for ice knife + goblin"
        assert len(results.results) >= 2, "Should return both spell and creature info"
        
        # Check for Ice Knife spell information
        spell_results = [r for r in results.results if r.source == "spells" and "ice knife" in r.content.lower()]
        assert len(spell_results) >= 1, "Should return Ice Knife spell information"
        
        # Check for Goblin creature information
        creature_results = [r for r in results.results if r.source == "monsters" and "goblin" in r.content.lower()]
        assert len(creature_results) >= 1, "Should return Goblin creature information"
        
        # Verify no duplicates
        unique_content = set(r.content[:100] for r in results.results)
        assert len(unique_content) == len(results.results), "Should not return duplicate results"
    
    def test_fireball_spell(self, rag_service, mock_game_state):
        """Test fireball spell casting."""
        action = "I cast fireball at the group of enemies"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert results.has_results(), "Should return results for fireball"
        
        # Check for spell information
        spell_results = [r for r in results.results if r.source == "spells" and "fireball" in r.content.lower()]
        assert len(spell_results) >= 1, "Should return Fireball spell information"
    
    def test_healing_word_spell(self, rag_service, mock_game_state):
        """Test healing spell casting."""
        action = "Use healing word on the injured party member"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert results.has_results(), "Should return results for healing word"
        
        # Check for healing spell information
        spell_results = [r for r in results.results if r.source == "spells" and 
                        ("healing word" in r.content.lower() or "heal" in r.content.lower())]
        assert len(spell_results) >= 1, "Should return healing spell information"
    
    def test_unknown_spell(self, rag_service, mock_game_state):
        """Test behavior with unknown spell."""
        action = "Cast Super Ultra Mega Blast"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        # Should still return some spellcasting-related information
        assert results.total_queries > 0, "Should generate queries even for unknown spells"


class TestRAGCombat:
    """Test RAG retrieval for combat scenarios."""
    
    def test_attack_orc(self, rag_service):
        """Test attacking an orc."""
        mock_game_state = MockGameState(in_combat=True)
        action = "Attack the orc with my sword"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert results.has_results(), "Should return results for combat action"
        
        # Check for creature information
        creature_results = [r for r in results.results if r.source == "monsters" and "orc" in r.content.lower()]
        assert len(creature_results) >= 1, "Should return Orc creature information"
        
        # Check for combat rules
        rules_results = [r for r in results.results if r.source == "rules" and 
                        ("attack" in r.content.lower() or "combat" in r.content.lower())]
        assert len(rules_results) >= 1, "Should return combat rules information"
    
    def test_grapple_dragon(self, rag_service):
        """Test grappling a large creature."""
        mock_game_state = MockGameState(in_combat=True)
        action = "Attempt to grapple the dragon"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert results.has_results(), "Should return results for grapple + dragon"
        
        # Check for dragon information
        creature_results = [r for r in results.results if r.source == "monsters" and "dragon" in r.content.lower()]
        assert len(creature_results) >= 1, "Should return Dragon creature information"


class TestRAGSkillChecks:
    """Test RAG retrieval for skill check scenarios."""
    
    def test_perception_check(self, rag_service, mock_game_state):
        """Test perception skill check."""
        action = "I look around for hidden doors"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert results.has_results(), "Should return results for perception check"
        
        # Check for skill rules
        rules_results = [r for r in results.results if r.source == "rules" and 
                        ("perception" in r.content.lower() or "skill" in r.content.lower())]
        assert len(rules_results) >= 1, "Should return skill check rules"
    
    def test_stealth_action(self, rag_service, mock_game_state):
        """Test stealth action."""
        action = "I try to sneak past the guards"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert results.has_results(), "Should return results for stealth action"
        
        # Check for stealth rules
        rules_results = [r for r in results.results if r.source == "rules" and 
                        "stealth" in r.content.lower()]
        assert len(rules_results) >= 1, "Should return stealth rules"


class TestRAGSocialInteraction:
    """Test RAG retrieval for social interaction scenarios."""
    
    def test_persuasion_attempt(self, rag_service, mock_game_state):
        """Test persuasion attempt."""
        action = "I try to convince the merchant to lower his prices"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert results.has_results(), "Should return results for persuasion"
        
        # Check for social interaction rules
        rules_results = [r for r in results.results if r.source == "rules" and 
                        ("persuasion" in r.content.lower() or "social" in r.content.lower())]
        assert len(rules_results) >= 1, "Should return social interaction rules"


class TestRAGExploration:
    """Test RAG retrieval for exploration scenarios."""
    
    def test_environment_exploration(self, rag_service, mock_game_state):
        """Test exploring the environment."""
        action = "I explore the ancient ruins"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        # May or may not return results depending on available lore
        assert results.total_queries > 0, "Should generate exploration queries"


class TestRAGQueryGeneration:
    """Test RAG query generation and analysis."""
    
    def test_spell_query_generation(self, rag_service, mock_game_state):
        """Test query generation for spells."""
        action = "Cast Ice Knife on Goblin Cook"
        
        queries = rag_service.analyze_action(action, mock_game_state)
        
        assert len(queries) > 0, "Should generate queries for spell action"
        
        # Check for spell casting query type
        spell_queries = [q for q in queries if q.query_type == QueryType.SPELL_CASTING]
        assert len(spell_queries) > 0, "Should generate spell casting queries"
        
        # Check for spell name in context
        spell_context_queries = [q for q in queries if q.context.get("spell_name")]
        assert len(spell_context_queries) > 0, "Should extract spell name"
        
        # Check for creature in context
        creature_context_queries = [q for q in queries if q.context.get("creature")]
        assert len(creature_context_queries) > 0, "Should extract creature name"
    
    def test_combat_query_generation(self, rag_service):
        """Test query generation for combat."""
        mock_game_state = MockGameState(in_combat=True)
        action = "Attack the orc with my battleaxe"
        
        queries = rag_service.analyze_action(action, mock_game_state)
        
        assert len(queries) > 0, "Should generate queries for combat action"
        
        # Check for combat query type
        combat_queries = [q for q in queries if q.query_type == QueryType.COMBAT]
        assert len(combat_queries) > 0, "Should generate combat queries"


class TestRAGPerformance:
    """Test RAG system performance and reliability."""
    
    def test_response_time(self, rag_service, mock_game_state):
        """Test that RAG responses are reasonably fast."""
        action = "Cast Fireball at the group of goblins"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        # Should complete in under 5 seconds (very generous for testing)
        assert results.execution_time_ms < 5000, f"RAG took too long: {results.execution_time_ms}ms"
    
    def test_empty_action(self, rag_service, mock_game_state):
        """Test behavior with empty or invalid actions."""
        results = rag_service.get_relevant_knowledge("", mock_game_state)
        assert isinstance(results, RAGResults), "Should return RAGResults for empty action"
        
        results = rag_service.get_relevant_knowledge(None, mock_game_state)
        assert isinstance(results, RAGResults), "Should handle None action gracefully"
    
    def test_very_long_action(self, rag_service, mock_game_state):
        """Test behavior with very long action text."""
        long_action = "I cast fireball " * 100 + " at the goblin"
        
        results = rag_service.get_relevant_knowledge(long_action, mock_game_state)
        
        assert isinstance(results, RAGResults), "Should handle long actions"
        assert results.execution_time_ms < 10000, "Should complete long actions in reasonable time"


class TestRAGConfiguration:
    """Test RAG system configuration options."""
    
    def test_filtering_configuration(self, rag_service, mock_game_state):
        """Test configurable filtering options."""
        # Test with different max results
        rag_service.configure_filtering(max_results=2)
        
        action = "Cast Ice Knife on Goblin"
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert len(results.results) <= 2, "Should respect max_results configuration"
        
        # Test with different score threshold
        rag_service.configure_filtering(score_threshold=0.8)
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        # Should return fewer results with higher threshold
        for result in results.results:
            assert result.relevance_score >= 0.8, "Should respect score threshold"


class TestRAGEdgeCases:
    """Test edge cases and error handling."""
    
    def test_nonsense_action(self, rag_service, mock_game_state):
        """Test with nonsensical action text."""
        action = "Flibber jabberwocky quantum banana"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        # Should handle gracefully without crashing
        assert isinstance(results, RAGResults), "Should handle nonsense actions"
    
    def test_special_characters(self, rag_service, mock_game_state):
        """Test with special characters in action."""
        action = "Cast 'Ice Knife' @#$% on Goblin!!!"
        
        results = rag_service.get_relevant_knowledge(action, mock_game_state)
        
        assert isinstance(results, RAGResults), "Should handle special characters"
        # Should still extract meaningful information
        spell_results = [r for r in results.results if "ice knife" in r.content.lower()]
        assert len(spell_results) >= 1, "Should still extract spell despite special chars"


class TestRAGContextPersistence:
    """Test RAG context persistence across interactions."""
    
    def test_context_persistence_during_dice_submission(self):
        """Test that RAG context is preserved when submitting dice rolls."""
        from app.services.rag.rag_context_builder import rag_context_builder
        
        # Create a mock game state
        game_state = MockGameState()
        
        # Mock RAG service that returns some context
        mock_rag_service = Mock()
        mock_results = Mock()
        mock_results.has_results.return_value = True
        mock_results.format_for_prompt.return_value = "SPELL CONTEXT: Ice Knife spell details here..."
        mock_results.results = []  # Empty list for len() call
        mock_results.execution_time_ms = 100.0
        mock_rag_service.get_relevant_knowledge.return_value = mock_results
        
        # Mock chat history with initial spell action and dice submission
        chat_history = [
            {"role": "user", "content": "I cast Ice Knife on the goblin"},
            {"role": "assistant", "content": "Roll an attack roll"},
            {"role": "user", "content": "**Player Rolls Submitted:**\nAttack Roll: 15"}
        ]
        
        # First call: player casts spell (should generate new context)
        context1 = rag_context_builder.get_rag_context_for_prompt(
            game_state, mock_rag_service, "I cast Ice Knife on the goblin", chat_history, force_new_query=True
        )
        
        # Verify context was generated and stored
        assert context1 == "SPELL CONTEXT: Ice Knife spell details here..."
        assert game_state._last_rag_context == context1
        
        # Second call: dice submission (should reuse stored context)
        context2 = rag_context_builder.get_rag_context_for_prompt(
            game_state, mock_rag_service, None, chat_history, force_new_query=False
        )
        
        # Verify the same context was reused
        assert context2 == context1
        assert context2 == "SPELL CONTEXT: Ice Knife spell details here..."
        
        # RAG service should only be called once (for the initial query)
        assert mock_rag_service.get_relevant_knowledge.call_count == 1
    
    def test_context_clearing_on_new_action(self):
        """Test that RAG context is cleared when a new player action starts."""
        from app.services.rag.rag_context_builder import rag_context_builder
        
        game_state = MockGameState()
        game_state._last_rag_context = "Old context about Ice Knife"
        
        # Clear the stored context
        rag_context_builder.clear_stored_rag_context(game_state)
        
        # Verify context was cleared
        assert game_state._last_rag_context is None
    
    def test_context_clearing_on_combat_end(self):
        """Test that RAG context is cleared when combat ends."""
        from app.game.state_processors import end_combat
        from app.ai_services.schemas import CombatEndUpdate
        from app.game.models import GameState, CombatState
        
        # Create a game state with active combat and stored RAG context
        game_state = GameState()
        game_state.combat = CombatState(is_active=True)
        game_state._last_rag_context = "Combat spell context"
        
        # End combat (pass None for game_manager since we're not testing events)
        combat_end_update = CombatEndUpdate(details={"reason": "All enemies defeated"})
        end_combat(game_state, combat_end_update, game_manager=None)
        
        # Verify combat ended and RAG context was cleared
        assert not game_state.combat.is_active
        assert game_state._last_rag_context is None


if __name__ == "__main__":
    pytest.main([__file__])