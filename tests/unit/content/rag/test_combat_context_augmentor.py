"""Tests for the combat context augmentor."""

import pytest

from app.content.rag.combat_context_augmentor import CombatContextAugmentor
from app.models.combat import CombatantModel, CombatStateModel
from app.models.game_state import GameStateModel
from app.models.rag import QueryType, RAGQuery


class TestCombatContextAugmentor:
    """Test suite for CombatContextAugmentor."""

    @pytest.fixture
    def augmentor(self) -> CombatContextAugmentor:
        """Create a combat context augmentor."""
        return CombatContextAugmentor()

    @pytest.fixture
    def game_state_no_combat(self) -> GameStateModel:
        """Create game state without combat."""
        return GameStateModel(campaign_id="test")

    @pytest.fixture
    def game_state_with_combat(self) -> GameStateModel:
        """Create game state with active combat including goblins."""
        return GameStateModel(
            campaign_id="test",
            combat=CombatStateModel(
                is_active=True,
                combatants=[
                    CombatantModel(
                        id="goblin1",
                        name="Goblin Raider",
                        initiative=10,
                        current_hp=7,
                        max_hp=7,
                        armor_class=15,
                        is_player=False,
                    ),
                    CombatantModel(
                        id="goblin2",
                        name="Goblin Shaman",
                        initiative=12,
                        current_hp=10,
                        max_hp=10,
                        armor_class=13,
                        is_player=False,
                    ),
                    CombatantModel(
                        id="player1",
                        name="Hero",
                        initiative=15,
                        current_hp=20,
                        max_hp=20,
                        armor_class=16,
                        is_player=True,
                    ),
                ],
            ),
        )

    def test_no_augmentation_without_combat(
        self, augmentor: CombatContextAugmentor, game_state_no_combat: GameStateModel
    ) -> None:
        """Test no queries added when not in combat."""
        original_queries = [
            RAGQuery(
                query_text="test query",
                query_type=QueryType.GENERAL,
                knowledge_base_types=["rules"],
            )
        ]

        result = augmentor.augment_queries_with_combat_context(
            original_queries, game_state_no_combat
        )

        assert len(result) == 1
        assert result[0].query_text == "test query"

    def test_augmentation_with_combat(
        self, augmentor: CombatContextAugmentor, game_state_with_combat: GameStateModel
    ) -> None:
        """Test queries are augmented with combat context."""
        original_queries = [
            RAGQuery(
                query_text="test query",
                query_type=QueryType.GENERAL,
                knowledge_base_types=["rules"],
            )
        ]

        result = augmentor.augment_queries_with_combat_context(
            original_queries, game_state_with_combat
        )

        # Should have combat queries prepended
        assert len(result) > 1

        # First query should be for goblin (only one query since both are goblins)
        combat_query = result[0]
        assert "goblin" in combat_query.query_text
        assert combat_query.query_type == QueryType.COMBAT
        assert combat_query.knowledge_base_types == ["monsters"]
        assert combat_query.context["combat_active"] is True
        assert combat_query.context["priority"] == "high"

        # Original query should still be there
        assert result[-1].query_text == "test query"

    def test_extract_multiple_creature_types(
        self, augmentor: CombatContextAugmentor
    ) -> None:
        """Test extraction of multiple creature types."""
        game_state = GameStateModel(
            campaign_id="test",
            combat=CombatStateModel(
                is_active=True,
                combatants=[
                    CombatantModel(
                        id="orc1",
                        name="Orc Warrior",
                        initiative=10,
                        current_hp=15,
                        max_hp=15,
                        armor_class=13,
                        is_player=False,
                    ),
                    CombatantModel(
                        id="wolf1",
                        name="Dire Wolf",
                        initiative=14,
                        current_hp=20,
                        max_hp=20,
                        armor_class=14,
                        is_player=False,
                    ),
                ],
            ),
        )

        result = augmentor.augment_queries_with_combat_context([], game_state)

        # Should have queries for both orc and wolf
        assert len(result) == 2
        query_texts = [q.query_text for q in result]
        assert any("orc" in text for text in query_texts)
        assert any("wolf" in text for text in query_texts)

    def test_skip_player_characters(
        self, augmentor: CombatContextAugmentor, game_state_with_combat: GameStateModel
    ) -> None:
        """Test that player characters are skipped."""
        result = augmentor.augment_queries_with_combat_context(
            [], game_state_with_combat
        )

        # Should not have queries for "Hero"
        query_texts = [q.query_text for q in result]
        assert not any("hero" in text.lower() for text in query_texts)

    def test_inactive_combat(self, augmentor: CombatContextAugmentor) -> None:
        """Test no augmentation when combat is inactive."""
        game_state = GameStateModel(
            campaign_id="test",
            combat=CombatStateModel(
                is_active=False,
                combatants=[
                    CombatantModel(
                        id="goblin1",
                        name="Goblin",
                        initiative=10,
                        current_hp=7,
                        max_hp=7,
                        armor_class=15,
                        is_player=False,
                    )
                ],
            ),
        )

        result = augmentor.augment_queries_with_combat_context([], game_state)
        assert len(result) == 0

    def test_empty_combatants(self, augmentor: CombatContextAugmentor) -> None:
        """Test no augmentation with empty combatants list."""
        game_state = GameStateModel(
            campaign_id="test", combat=CombatStateModel(is_active=True, combatants=[])
        )

        result = augmentor.augment_queries_with_combat_context([], game_state)
        assert len(result) == 0

    def test_unknown_creature_type(self, augmentor: CombatContextAugmentor) -> None:
        """Test handling of unknown creature types."""
        game_state = GameStateModel(
            campaign_id="test",
            combat=CombatStateModel(
                is_active=True,
                combatants=[
                    CombatantModel(
                        id="unknown1",
                        name="Strange Creature",
                        initiative=10,
                        current_hp=10,
                        max_hp=10,
                        armor_class=10,
                        is_player=False,
                    )
                ],
            ),
        )

        result = augmentor.augment_queries_with_combat_context([], game_state)
        # Should not generate queries for unknown creatures
        assert len(result) == 0
