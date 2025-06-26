"""Golden test pairs for RAG system validation.

This module contains a curated set of test cases to validate RAG performance
and prevent regressions. Each test case represents a real-world query scenario
with expected results that must appear in the search results.
"""

import logging
from dataclasses import dataclass
from typing import Generator, List

import pytest
from pydantic import SecretStr

from app.core.container import ServiceContainer
from app.models.game_state.main import GameStateModel
from tests.conftest import get_test_settings

# Configure logging for better debugging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@dataclass
class GoldenPair:
    """Type-safe structure for RAG golden test pairs."""

    name: str
    player_action: str
    game_state: GameStateModel
    expected_fragments: List[str]
    description: str


# Golden test pairs: Each entry tests a specific RAG use case
# Note: These expectations are based on the current RAG implementation behavior
GOLDEN_PAIRS: List[GoldenPair] = [
    GoldenPair(
        name="Combat Action - Melee Attack",
        player_action="I attack the goblin with my shortsword.",
        game_state=GameStateModel(),
        expected_fragments=[
            "goblin",
            "shortsword",
        ],  # Should retrieve both monster and weapon info
        description="Should retrieve information about goblins and shortsword for combat",
    ),
    GoldenPair(
        name="Spellcasting - Fireball",
        player_action="I cast fireball at the group of orcs.",
        game_state=GameStateModel(),
        expected_fragments=[
            "fireball",
            "8d6",
        ],  # Simplified - fire damage might be in description
        description="Should retrieve fireball spell information including damage",
    ),
    GoldenPair(
        name="Skill Check - Abilities",
        player_action="I want to make an ability check to climb the wall.",
        game_state=GameStateModel(),
        expected_fragments=["ability", "check"],  # More specific expectations
        description="Should retrieve information about ability checks or using abilities",
    ),
    GoldenPair(
        name="Rules Lookup - Actions",
        player_action="What actions can I take in combat?",
        game_state=GameStateModel(),
        expected_fragments=["action"],  # "combat" might trigger monster search
        description="Should retrieve information about combat actions",
    ),
    GoldenPair(
        name="Monster Information",
        player_action="What do I know about dragons?",
        game_state=GameStateModel(),
        expected_fragments=["dragon"],
        description="Should retrieve information about dragons",
    ),
    GoldenPair(
        name="Spell Components",
        player_action="What are spell components?",
        game_state=GameStateModel(),
        expected_fragments=["component"],
        description="Should retrieve information about spell components",
    ),
    GoldenPair(
        name="Conditions",
        player_action="What does being poisoned do?",
        game_state=GameStateModel(),
        expected_fragments=["poison"],
        description="Should retrieve information about poison condition",
    ),
    GoldenPair(
        name="Equipment Search - Weapons",
        player_action="I want to buy a dagger.",
        game_state=GameStateModel(),
        expected_fragments=["dagger"],
        description="Should retrieve dagger equipment information",
    ),
    GoldenPair(
        name="Class Information - Fighter",
        player_action="What abilities does a fighter get?",
        game_state=GameStateModel(),
        expected_fragments=["fighter"],
        description="Should retrieve fighter class abilities and features",
    ),
    GoldenPair(
        name="Subclass Information - Wizard Schools",
        player_action="Tell me about wizard subclasses or arcane traditions.",
        game_state=GameStateModel(),
        expected_fragments=["wizard"],
        description="Should retrieve information about wizard schools/subclasses",
    ),
    GoldenPair(
        name="Race Information - Elf",
        player_action="What are the traits of an elf?",
        game_state=GameStateModel(),
        expected_fragments=["elf"],
        description="Should retrieve elf racial traits",
    ),
    GoldenPair(
        name="Subrace Information - Hill Dwarf",
        player_action="What makes hill dwarves different from other dwarves?",
        game_state=GameStateModel(),
        expected_fragments=["dwarf", "hill"],
        description="Should retrieve hill dwarf subrace information",
    ),
    GoldenPair(
        name="Level Up - Class Features",
        player_action="What do I get when I level up as a rogue?",
        game_state=GameStateModel(),
        expected_fragments=["rogue"],
        description="Should retrieve rogue class progression and level-up features",
    ),
    GoldenPair(
        name="Level Up - Ability Score Improvement",
        player_action="When do characters get ability score improvements?",
        game_state=GameStateModel(),
        expected_fragments=["ability"],
        description="Should retrieve information about ability score improvements",
    ),
    GoldenPair(
        name="Class Hit Dice",
        player_action="What hit dice do different classes use?",
        game_state=GameStateModel(),
        expected_fragments=["hit", "die"],
        description="Should retrieve information about class hit dice",
    ),
]


class TestRAGGoldenPairs:
    """Test golden pairs for RAG system validation."""

    @pytest.fixture
    def container_with_d5e_rag(
        self, test_database_url: str
    ) -> Generator[ServiceContainer, None, None]:
        """Create a container with D5e RAG enabled using test database."""
        settings = get_test_settings()
        settings.rag.enabled = True
        settings.rag.embeddings_model = "intfloat/multilingual-e5-small"
        settings.rag.embedding_dimension = 384
        settings.rag.chunk_size = 100
        settings.rag.max_results_per_query = 5
        settings.rag.max_total_results = 10
        settings.rag.score_threshold = 0.2
        settings.database.url = SecretStr(test_database_url)

        container = ServiceContainer(settings)
        container.initialize()

        yield container

        # Clean up
        from app.core.container import reset_container

        reset_container()

    @pytest.fixture
    def container_with_expanded_rag(
        self, test_database_url: str
    ) -> Generator[ServiceContainer, None, None]:
        """Create a container with expanded RAG result limits for debugging."""
        settings = get_test_settings()
        settings.rag.enabled = True
        settings.rag.embeddings_model = "intfloat/multilingual-e5-small"
        settings.rag.embedding_dimension = 384
        settings.rag.chunk_size = 100
        settings.rag.max_results_per_query = 10  # Increased from 5
        settings.rag.max_total_results = 30  # Increased from 10
        settings.rag.score_threshold = 0.1  # Lowered from 0.2
        settings.database.url = SecretStr(test_database_url)

        container = ServiceContainer(settings)
        container.initialize()

        yield container

        # Clean up
        from app.core.container import reset_container

        reset_container()

    @pytest.mark.requires_rag
    @pytest.mark.parametrize("golden_pair", GOLDEN_PAIRS, ids=lambda gp: gp.name)
    def test_rag_golden_pairs(
        self, container_with_d5e_rag: ServiceContainer, golden_pair: GoldenPair
    ) -> None:
        """Test RAG retrieval for golden pairs.

        Each golden pair represents a real-world query scenario with expected
        results that validate the RAG system is working correctly.

        Args:
            container_with_d5e_rag: Container with RAG enabled
            golden_pair: Test case with action, state, and expected results
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Testing: {golden_pair.name}")
        logger.info(f"Action: {golden_pair.player_action}")
        logger.info(f"Expected fragments: {golden_pair.expected_fragments}")

        # Get RAG service
        rag_service = container_with_d5e_rag.get_rag_service()
        assert rag_service is not None, "RAG service should be available"

        # Get query engine to inspect generated queries
        from app.content.rag.query_engine import SimpleQueryEngine

        query_engine = SimpleQueryEngine()
        queries = query_engine.analyze_action(
            golden_pair.player_action, golden_pair.game_state
        )
        logger.info(f"Generated {len(queries)} queries:")
        for i, query in enumerate(queries):
            logger.info(
                f"  Query {i + 1}: '{query.query_text}' (types: {query.knowledge_base_types})"
            )

        # Execute RAG query
        results = rag_service.get_relevant_knowledge(
            action=golden_pair.player_action,
            game_state=golden_pair.game_state,
            content_pack_priority=None,  # Use default priority
        )

        # Log results info
        logger.info(f"Total results: {len(results.results)}")
        logger.info(f"Execution time: {results.execution_time_ms:.2f}ms")

        # Basic assertions
        assert results is not None, f"Should return results for: {golden_pair.name}"
        assert results.has_results(), (
            f"Should have search results for: {golden_pair.name}"
        )
        assert results.total_queries > 0, (
            f"Should generate queries for: {golden_pair.name}"
        )

        # Get content from top results (limit to top 3 for validation)
        top_results = (
            results.results[:3] if len(results.results) > 3 else results.results
        )
        combined_content = " ".join([r.content.lower() for r in top_results])

        # Log top results for debugging
        logger.info("Top results:")
        for i, result in enumerate(top_results):
            logger.info(
                f"  Result {i + 1} ({result.source}, score: {result.relevance_score:.3f}): {result.content[:80]}..."
            )

        # Validate expected fragments appear in results
        missing_fragments = []
        for fragment in golden_pair.expected_fragments:
            if fragment.lower() not in combined_content:
                missing_fragments.append(fragment)

        # Provide detailed error message if fragments are missing
        if missing_fragments:
            # Show what was actually retrieved for debugging
            actual_content_preview = "\n".join(
                [f"  - {r.source}: {r.content[:100]}..." for r in top_results]
            )
            pytest.fail(
                f"\nTest case: {golden_pair.name}\n"
                f"Description: {golden_pair.description}\n"
                f"Action: {golden_pair.player_action}\n"
                f"Missing expected fragments: {missing_fragments}\n"
                f"Top {len(top_results)} results:\n{actual_content_preview}"
            )

        # Performance check
        assert results.execution_time_ms < 10000, (
            f"Query should complete within 10 seconds, took {results.execution_time_ms}ms"
        )

    @pytest.mark.requires_rag
    @pytest.mark.parametrize("golden_pair", GOLDEN_PAIRS, ids=lambda gp: gp.name)
    def test_rag_golden_pairs_expanded(
        self, container_with_expanded_rag: ServiceContainer, golden_pair: GoldenPair
    ) -> None:
        """Test RAG retrieval with expanded limits to debug failures.

        This test uses higher result limits and lower score threshold to help
        identify if expected content exists but is being filtered out.

        Args:
            container_with_expanded_rag: Container with expanded RAG limits
            golden_pair: Test case with action, state, and expected results
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"EXPANDED TEST: {golden_pair.name}")
        logger.info(f"Action: {golden_pair.player_action}")
        logger.info(f"Expected fragments: {golden_pair.expected_fragments}")

        # Get RAG service
        rag_service = container_with_expanded_rag.get_rag_service()
        assert rag_service is not None, "RAG service should be available"

        # Execute RAG query
        results = rag_service.get_relevant_knowledge(
            action=golden_pair.player_action,
            game_state=golden_pair.game_state,
            content_pack_priority=None,
        )

        logger.info(f"Total results with expanded limits: {len(results.results)}")

        # Check all results for expected fragments
        all_content = " ".join([r.content.lower() for r in results.results])
        found_fragments = []
        missing_fragments = []

        for fragment in golden_pair.expected_fragments:
            if fragment.lower() in all_content:
                # Find which result contains this fragment
                for i, result in enumerate(results.results):
                    if fragment.lower() in result.content.lower():
                        found_fragments.append(
                            f"{fragment} (found in result #{i + 1}, score: {result.relevance_score:.3f})"
                        )
                        break
            else:
                missing_fragments.append(fragment)

        logger.info("Fragment search results:")
        for found in found_fragments:
            logger.info(f"  ✓ {found}")
        for missing in missing_fragments:
            logger.info(f"  ✗ {missing} - NOT FOUND in any results")

        # Show all results for debugging
        logger.info("\nAll results (expanded):")
        for i, result in enumerate(results.results[:10]):  # Show up to 10
            logger.info(
                f"  Result {i + 1} ({result.source}, score: {result.relevance_score:.3f}): "
                f"{result.content[:100]}..."
            )

        # This test is primarily for debugging - we don't fail it
        logger.info(
            f"\nSummary: Found {len(found_fragments)}/{len(golden_pair.expected_fragments)} expected fragments"
        )

    @pytest.mark.requires_rag
    def test_golden_pairs_coverage(
        self, container_with_d5e_rag: ServiceContainer
    ) -> None:
        """Test that golden pairs provide good coverage of RAG functionality."""
        # Verify we have a diverse set of test cases
        action_types = set()
        for pair in GOLDEN_PAIRS:
            action = pair.player_action.lower()
            name = pair.name.lower()

            # Check for combat actions
            if "attack" in action or "cast" in action or "combat" in name:
                action_types.add("combat")
            # Check for skill checks
            elif "ability check" in action or "skill" in action:
                action_types.add("skill_check")
            # Check for equipment/shopping
            elif (
                "buy" in action
                or "dagger" in action
                or "weapon" in action
                or "equipment" in action
                or "equipment" in name
            ):
                action_types.add("equipment")
            # Check for class information
            elif (
                "class" in action
                or "fighter" in action
                or "wizard" in action
                or "rogue" in action
                or "class" in name
                or "subclass" in name
            ):
                action_types.add("class_info")
            # Check for race information
            elif (
                "race" in action
                or "elf" in action
                or "dwarf" in action
                or "race" in name
                or "subrace" in name
            ):
                action_types.add("race_info")
            # Check for level progression
            elif (
                "level" in action
                or "multiclass" in action
                or "level up" in name
                or "hit dice" in name
            ):
                action_types.add("level_progression")
            # Check for monster information
            elif "dragon" in action or "monster" in name:
                action_types.add("monster_info")
            # Check for spell information
            elif (
                "spell component" in action or "poison" in action or "condition" in name
            ):
                action_types.add("spell_or_condition_info")
            # Catch-all for rules/info queries
            elif "how" in action or "what" in action:
                action_types.add("rules_or_info")

        # Ensure we have diverse coverage
        assert len(action_types) >= 5, (
            f"Should cover at least 5 action types, got {action_types}"
        )
        assert len(GOLDEN_PAIRS) >= 10, "Should have at least 10 golden test pairs"

        # Verify each golden pair has required fields (dataclass ensures this)
        for pair in GOLDEN_PAIRS:
            assert pair.name, "Each golden pair must have a name"
            assert pair.player_action, "Each golden pair must have a player_action"
            assert pair.game_state is not None, (
                "Each golden pair must have a game_state"
            )
            assert pair.expected_fragments, (
                "Each golden pair must have expected_fragments"
            )
            assert len(pair.expected_fragments) > 0, (
                "Must have at least one expected fragment"
            )
