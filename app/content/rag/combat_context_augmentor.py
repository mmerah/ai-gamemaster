"""
Combat context augmentor for RAG queries.
Automatically adds queries for active combatants when in combat.
"""

import logging
from typing import List, Set

from app.models.game_state import GameStateModel
from app.models.rag import QueryType, RAGQuery

logger = logging.getLogger(__name__)


class CombatContextAugmentor:
    """Augments RAG queries with combat context when applicable."""

    # Known creature types to extract from combatant names
    KNOWN_CREATURES = [
        "goblin",
        "orc",
        "dragon",
        "kobold",
        "skeleton",
        "zombie",
        "wolf",
        "bear",
        "giant",
        "troll",
        "ogre",
        "spider",
        "rat",
        "bandit",
        "guard",
        "knight",
        "cultist",
        "mage",
        "wizard",
        "elemental",
        "demon",
        "devil",
        "undead",
        "beast",
        "aberration",
    ]

    def augment_queries_with_combat_context(
        self, queries: List[RAGQuery], game_state: GameStateModel
    ) -> List[RAGQuery]:
        """
        Augment queries with combat context if in active combat.

        Args:
            queries: Existing queries to augment
            game_state: Current game state

        Returns:
            Augmented list of queries including combat context queries
        """
        if not self._is_in_combat(game_state):
            return queries

        # Get unique creature types from active combatants
        creature_types = self._extract_combatant_creatures(game_state)

        if not creature_types:
            return queries

        # Generate combat context queries
        combat_queries = self._generate_combat_context_queries(creature_types)

        # Prepend combat queries for higher priority
        return combat_queries + queries

    def _is_in_combat(self, game_state: GameStateModel) -> bool:
        """Check if the game is currently in combat."""
        return (
            hasattr(game_state, "combat")
            and game_state.combat is not None
            and game_state.combat.is_active
        )

    def _extract_combatant_creatures(self, game_state: GameStateModel) -> Set[str]:
        """Extract unique creature types from active combatants."""
        if not hasattr(game_state, "combat") or not game_state.combat:
            return set()

        creature_types = set()

        for combatant in game_state.combat.combatants:
            # Skip player characters
            if combatant.is_player:
                continue

            # Extract creature type from name
            name_lower = combatant.name.lower()
            for creature in self.KNOWN_CREATURES:
                if creature in name_lower:
                    creature_types.add(creature)
                    break

        return creature_types

    def _generate_combat_context_queries(
        self, creature_types: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for combat context."""
        queries = []

        for creature in creature_types:
            # High-priority combat tactics query
            queries.append(
                RAGQuery(
                    query_text=f"{creature} combat tactics abilities attacks damage resistances immunities",
                    query_type=QueryType.COMBAT,
                    knowledge_base_types=["monsters"],
                    context={
                        "creature": creature,
                        "combat_active": True,
                        "priority": "high",
                    },
                )
            )

        logger.debug(
            f"Generated {len(queries)} combat context queries for creatures: {creature_types}"
        )
        return queries
