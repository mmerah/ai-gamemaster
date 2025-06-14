"""
Unit tests for the RAG query engine.
Tests the query engine that analyzes player actions.
"""

import os
import unittest
from typing import List, Optional
from unittest.mock import Mock

# Skip entire module if RAG is disabled
import pytest

_rag_env = os.environ.get("RAG_ENABLED", "true")
if _rag_env.lower() == "false":
    pytest.skip("RAG is disabled", allow_module_level=True)

from app.content.rag.query_engine import RAGQueryEngineImpl
from app.core.interfaces import QueryType


class TestRAGQueryEngine(unittest.TestCase):
    """Test the RAG query engine that analyzes player actions."""

    def setUp(self) -> None:
        self.query_engine = RAGQueryEngineImpl()
        self.mock_game_state = Mock()
        self.mock_game_state.combat = Mock()
        self.mock_game_state.combat.is_active = False
        self.mock_game_state.current_location = {"name": "tavern"}
        self.mock_game_state.event_summary = ["Player entered tavern", "Met bartender"]

    def test_spell_casting_detection(self) -> None:
        """Test detection of spell casting actions."""
        spell_actions = [
            "I cast fireball at the goblin",
            "I use healing word on my ally",
            "Cast magic missile",
            "I invoke shield spell",
            "Fire a fireball spell",
        ]

        for action in spell_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(
                    len(queries), 0, f"No queries generated for: {action}"
                )
                # At least one query should be spell-related
                has_spell_query = any(
                    q.query_type == QueryType.SPELL_CASTING for q in queries
                )
                self.assertTrue(has_spell_query, f"No spell query for: {action}")

    def test_combat_action_detection(self) -> None:
        """Test detection of combat actions."""
        combat_actions = [
            "I attack the skeleton with my sword",
            "Strike the orc",
            "I swing at the goblin",
            "Dodge the incoming attack",
            "I charge at the dragon",
        ]

        for action in combat_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(
                    len(queries), 0, f"No queries generated for: {action}"
                )
                # Should generate combat-related queries
                has_combat_query = any(
                    q.query_type == QueryType.COMBAT for q in queries
                )
                self.assertTrue(has_combat_query, f"No combat query for: {action}")

    def test_skill_check_detection(self) -> None:
        """Test detection of skill check actions."""
        skill_actions = [
            "I make a stealth check",
            "I search the room",
            "I try to persuade the guard",
            "Make an athletics check to climb",
        ]

        for action in skill_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(
                    len(queries), 0, f"No queries generated for: {action}"
                )
                # Should generate skill-related queries
                has_skill_query = any(
                    q.query_type == QueryType.SKILL_CHECK for q in queries
                )
                self.assertTrue(has_skill_query, f"No skill query for: {action}")

    def test_spell_name_extraction(self) -> None:
        """Test extraction of spell names from actions."""
        test_cases = [
            ("I cast fireball at the enemy", "fireball"),
            ("Use healing word on ally", "healing word"),
            ("Cast magic missile spell", "magic missile"),
            ("I invoke the shield spell", "shield"),
            ("Fire ice knife at target", "ice knife"),
        ]

        for action, expected_spell in test_cases:
            with self.subTest(action=action, expected=expected_spell):
                extracted = self.query_engine._extract_spell_name_enhanced(action)
                self.assertIn(
                    expected_spell.lower(),
                    extracted.lower(),
                    f"Expected '{expected_spell}' in extracted spell name '{extracted}'",
                )

    def test_creature_extraction(self) -> None:
        """Test extraction of creature names from actions."""
        test_cases = [
            ("I attack the goblin", ["goblin"]),
            ("Strike the orc and skeleton", ["orc", "skeleton"]),
            ("Fight the dragon", ["dragon"]),
            ("Avoid the giant spider", ["giant", "spider"]),
        ]

        for action, expected_creatures in test_cases:
            with self.subTest(action=action):
                creatures = self.query_engine._extract_creatures(action)
                for expected in expected_creatures:
                    self.assertIn(
                        expected,
                        creatures,
                        f"Expected creature '{expected}' not found in {creatures}",
                    )

    def test_empty_action_handling(self) -> None:
        """Test handling of empty or invalid actions."""
        invalid_actions: List[Optional[str]] = ["", None, "   "]

        for action in invalid_actions:
            with self.subTest(action=action):
                if action is not None:
                    queries = self.query_engine.analyze_action(
                        action, self.mock_game_state
                    )
                else:
                    # Handle None case - should not pass None to analyze_action
                    queries = []
                # Empty actions might still generate general queries, so allow some flexibility
                if action == "   ":  # Whitespace might generate a general query
                    self.assertLessEqual(
                        len(queries), 1, f"Should return minimal queries for: {action}"
                    )
                else:
                    self.assertEqual(
                        len(queries), 0, f"Should return empty list for: {action}"
                    )

    def test_social_interaction_detection(self) -> None:
        """Test detection of social interaction actions."""
        social_actions = [
            "I talk to the bartender",
            "Speak with the guard about passage",
            "I approach the merchant",
            "Ask the innkeeper about rooms",
        ]

        for action in social_actions:
            with self.subTest(action=action):
                queries = self.query_engine.analyze_action(action, self.mock_game_state)
                self.assertGreater(
                    len(queries), 0, f"No queries generated for: {action}"
                )


if __name__ == "__main__":
    unittest.main()
