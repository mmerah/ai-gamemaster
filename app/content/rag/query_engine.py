"""
Simple query engine for RAG that analyzes player actions without LLM dependencies.
"""

import logging
import re
from typing import List, Set

from app.models.game_state.main import GameStateModel
from app.models.rag import QueryType, RAGQuery

from .interfaces import IQueryEngine
from .patterns import (
    CLASS_PATTERNS,
    COMBAT_PATTERNS,
    CREATURE_PATTERNS,
    EQUIPMENT_PATTERNS,
    EXPLORATION_PATTERNS,
    LOCATION_PATTERNS,
    RACE_PATTERNS,
    SKILL_PATTERNS,
    SOCIAL_PATTERNS,
    SPELL_PATTERNS,
)

logger = logging.getLogger(__name__)


class SimpleQueryEngine(IQueryEngine):
    """
    Analyzes player actions and generates RAG queries using simple pattern matching
    and keyword extraction. No LLM required.
    """

    def __init__(self) -> None:
        """Initialize the query engine with patterns from the patterns module."""
        # Import patterns from the patterns module
        self.spell_patterns = SPELL_PATTERNS
        self.skill_patterns = SKILL_PATTERNS
        self.combat_patterns = COMBAT_PATTERNS
        self.equipment_patterns = EQUIPMENT_PATTERNS
        self.social_patterns = SOCIAL_PATTERNS
        self.exploration_patterns = EXPLORATION_PATTERNS
        self.location_patterns = LOCATION_PATTERNS
        self.creature_keywords = CREATURE_PATTERNS
        self.class_patterns = CLASS_PATTERNS
        self.race_patterns = RACE_PATTERNS

    def analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]:
        """
        Analyze a player action and generate relevant RAG queries.

        Args:
            action: The player's action text
            game_state: Current game state

        Returns:
            List of RAGQuery objects
        """
        if not action or not isinstance(action, str):
            return []

        action_lower = action.lower()
        queries: List[RAGQuery] = []

        # Extract entities and keywords
        extracted_entities = self._extract_entities(action)

        # Determine query types based on patterns
        query_types = self._determine_query_types(action_lower, game_state)

        # Generate queries based on extracted information
        for query_type in query_types:
            if query_type == QueryType.SPELL_CASTING:
                queries.extend(
                    self._generate_spell_queries(action_lower, extracted_entities)
                )
            elif query_type == QueryType.COMBAT:
                queries.extend(
                    self._generate_combat_queries(
                        action_lower, game_state, extracted_entities
                    )
                )
            elif query_type == QueryType.SKILL_CHECK:
                queries.extend(
                    self._generate_skill_queries(action_lower, extracted_entities)
                )
            elif query_type == QueryType.SOCIAL_INTERACTION:
                queries.extend(
                    self._generate_social_queries(action_lower, extracted_entities)
                )
            elif query_type == QueryType.EXPLORATION:
                queries.extend(
                    self._generate_exploration_queries(
                        action_lower, game_state, extracted_entities
                    )
                )
            elif query_type == QueryType.EQUIPMENT:
                queries.extend(
                    self._generate_equipment_queries(action_lower, extracted_entities)
                )
            elif query_type == QueryType.CHARACTER_INFO:
                queries.extend(
                    self._generate_character_queries(action_lower, extracted_entities)
                )

        # Always add a general query with the full action
        # Determine knowledge bases based on content
        kb_types = ["lore", "rules"]

        # Add specific knowledge bases based on detected patterns
        if any(cls in action_lower for cls in self.class_patterns) or any(
            race in action_lower for race in self.race_patterns
        ):
            kb_types.append("character_options")

        if any(item in action_lower for item in self.equipment_patterns):
            kb_types.append("equipment")

        if any(creature in action_lower for creature in self.creature_keywords):
            kb_types.append("monsters")

        if any(spell in action_lower for spell in self.spell_patterns):
            kb_types.append("spells")

        queries.append(
            RAGQuery(
                query_text=action,
                query_type=QueryType.GENERAL,
                knowledge_base_types=kb_types,
                context={"action": action},
            )
        )

        # Deduplicate queries
        seen_texts = set()
        unique_queries = []
        for query in queries:
            if query.query_text not in seen_texts:
                seen_texts.add(query.query_text)
                unique_queries.append(query)

        logger.debug(
            f"Generated {len(unique_queries)} queries for action: {action[:50]}..."
        )
        return unique_queries

    def _extract_entities(self, action: str) -> Set[str]:
        """Extract notable entities from the action text."""
        entities = set()

        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"', action)
        entities.update(quoted)

        # Extract capitalized words (likely proper nouns)
        # Keep the original capitalization for proper nouns
        words = re.findall(r"\b[A-Z][a-z]+\b", action)
        entities.update(words)

        # Extract numbers with context (e.g., "10 feet", "3rd level")
        numbers_with_context = re.findall(r"\b\d+\s*\w+\b", action)
        entities.update(numbers_with_context)

        return entities

    def _determine_query_types(
        self, action_lower: str, game_state: GameStateModel
    ) -> List[QueryType]:
        """Determine what types of queries to generate based on the action."""
        query_types = []

        # Check for specific spell names first (highest priority)
        for spell in self.spell_patterns:
            if spell in action_lower and spell not in {
                "cast",
                "casting",
                "spell",
                "cantrip",
                "ritual",
            }:
                return [QueryType.SPELL_CASTING]

        # Check for skills before combat - skills are more specific than general combat
        if any(skill in action_lower for skill in self.skill_patterns):
            query_types.append(QueryType.SKILL_CHECK)

        # Check for social interaction
        if any(social in action_lower for social in self.social_patterns):
            query_types.append(QueryType.SOCIAL_INTERACTION)

        # Check for combat (including creature names)
        has_creature = any(
            creature in action_lower for creature in self.creature_keywords
        )
        has_combat_action = any(
            combat in action_lower for combat in self.combat_patterns
        )

        # Only add combat if it's not already covered by a skill check or social interaction
        if (
            game_state.in_combat or has_combat_action or has_creature
        ) and not query_types:
            query_types.append(QueryType.COMBAT)

        # Check for exploration
        if any(explore in action_lower for explore in self.exploration_patterns):
            query_types.append(QueryType.EXPLORATION)

        # Check for location queries
        if any(loc in action_lower for loc in self.location_patterns):
            if QueryType.EXPLORATION not in query_types:
                query_types.append(QueryType.EXPLORATION)

        # Check for spell casting keywords if no specific spell was found
        if any(
            spell in action_lower
            for spell in {"cast", "casting", "spell", "cantrip", "ritual"}
        ):
            if QueryType.SPELL_CASTING not in query_types:
                query_types.append(QueryType.SPELL_CASTING)

        # Check for class-related queries
        if any(cls in action_lower for cls in self.class_patterns):
            query_types.append(QueryType.CHARACTER_INFO)

        # Check for race-related queries
        if any(race in action_lower for race in self.race_patterns):
            query_types.append(QueryType.CHARACTER_INFO)

        # Check for equipment/items
        if any(item in action_lower for item in self.equipment_patterns):
            query_types.append(QueryType.EQUIPMENT)

        # Default to general if no specific type found
        if not query_types:
            query_types.append(QueryType.GENERAL)

        return query_types

    def _generate_spell_queries(
        self, action_lower: str, _entities: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for spell casting actions."""
        queries = []

        # Look for spell names
        spell_name = None
        for word in action_lower.split():
            if word in self.spell_patterns and word not in {
                "cast",
                "casting",
                "spell",
                "cantrip",
                "ritual",
            }:
                spell_name = word
                break

        # If no specific spell found, look for "cast X" pattern
        if not spell_name:
            match = re.search(r"cast(?:ing)?\s+(\w+)", action_lower)
            if match:
                spell_name = match.group(1)

        if spell_name:
            # Check if there's a creature target mentioned
            creature_target = None
            for creature in self.creature_keywords:
                if creature in action_lower:
                    creature_target = creature
                    break

            context = {"spell_name": spell_name}
            if creature_target:
                context["creature"] = creature_target

            queries.append(
                RAGQuery(
                    query_text=spell_name,
                    query_type=QueryType.SPELL_CASTING,
                    knowledge_base_types=["spells"],
                    context=context,
                )
            )

        # Also search for general spell casting rules
        queries.append(
            RAGQuery(
                query_text="spell casting rules components",
                query_type=QueryType.SPELL_CASTING,
                knowledge_base_types=["rules"],
                context={},
            )
        )

        return queries

    def _generate_combat_queries(
        self, action_lower: str, _game_state: GameStateModel, _entities: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for combat actions."""
        queries = []

        # Look for specific actions first
        defensive_actions = {"dodge", "parry", "block", "evade", "defend"}
        for action in defensive_actions:
            if action in action_lower:
                queries.append(
                    RAGQuery(
                        query_text=f"{action} action rules",
                        query_type=QueryType.COMBAT,
                        knowledge_base_types=["rules"],
                        context={"action": action},
                    )
                )

        # Look for weapon or attack type
        if (
            "melee" in action_lower
            or "sword" in action_lower
            or "axe" in action_lower
            or "attack" in action_lower
            or "strike" in action_lower
        ):
            queries.append(
                RAGQuery(
                    query_text="melee attack rules",
                    query_type=QueryType.COMBAT,
                    knowledge_base_types=["rules"],
                    context={},
                )
            )
        elif (
            "ranged" in action_lower or "bow" in action_lower or "shoot" in action_lower
        ):
            queries.append(
                RAGQuery(
                    query_text="ranged attack rules",
                    query_type=QueryType.COMBAT,
                    knowledge_base_types=["rules"],
                    context={},
                )
            )

        # Look for specific creatures mentioned
        for creature in self.creature_keywords:
            if creature in action_lower:
                queries.append(
                    RAGQuery(
                        query_text=creature,
                        query_type=QueryType.COMBAT,
                        knowledge_base_types=["monsters"],
                        context={"creature": creature},
                    )
                )

        return queries

    def _generate_skill_queries(
        self, action_lower: str, _entities: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for skill check actions."""
        queries = []

        # Find which skill is being used
        for skill in self.skill_patterns:
            if skill in action_lower:
                queries.append(
                    RAGQuery(
                        query_text=f"{skill} skill check",
                        query_type=QueryType.SKILL_CHECK,
                        knowledge_base_types=["rules"],
                        context={"skill": skill},
                    )
                )
                break

        return queries

    def _generate_social_queries(
        self, _action_lower: str, entities: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for social interaction actions."""
        queries = []

        # Add social interaction rules
        queries.append(
            RAGQuery(
                query_text="social interaction persuasion deception",
                query_type=QueryType.SOCIAL_INTERACTION,
                knowledge_base_types=["rules"],
                context={},
            )
        )

        # If location is mentioned, search lore
        if entities:
            for entity in entities:
                if len(entity) > 2:  # Skip very short entities
                    queries.append(
                        RAGQuery(
                            query_text=entity,
                            query_type=QueryType.SOCIAL_INTERACTION,
                            knowledge_base_types=["lore"],
                            context={"entity": entity},
                        )
                    )

        return queries

    def _generate_exploration_queries(
        self, action_lower: str, game_state: GameStateModel, entities: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for exploration actions."""
        queries = []

        # For location queries like "Where is X", extract the location name
        if "where" in action_lower:
            # Try to extract location after "where is"
            match = re.search(r"where\s+is\s+(\w+(?:\s+\w+)*)", action_lower)
            if match:
                location_name = match.group(1).strip()
                queries.append(
                    RAGQuery(
                        query_text=location_name,
                        query_type=QueryType.EXPLORATION,
                        knowledge_base_types=["lore"],
                        context={"location": location_name},
                    )
                )

        # Also search for any capitalized words that might be locations
        for entity in entities:
            if entity and len(entity) > 2:  # Skip very short entities
                queries.append(
                    RAGQuery(
                        query_text=entity,
                        query_type=QueryType.EXPLORATION,
                        knowledge_base_types=["lore"],
                        context={"entity": entity},
                    )
                )

        # Search for current location info
        if game_state.current_location:
            queries.append(
                RAGQuery(
                    query_text=game_state.current_location.name,
                    query_type=QueryType.EXPLORATION,
                    knowledge_base_types=["lore"],
                    context={"location": game_state.current_location.name},
                )
            )

        # Search for exploration rules
        if any(word in action_lower for word in ["trap", "secret", "hidden"]):
            queries.append(
                RAGQuery(
                    query_text="traps secret doors detection",
                    query_type=QueryType.EXPLORATION,
                    knowledge_base_types=["rules"],
                    context={},
                )
            )

        return queries

    def _generate_equipment_queries(
        self, action_lower: str, _entities: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for equipment and item-related actions."""
        queries = []

        # Find specific equipment mentioned
        mentioned_items: List[str] = []
        for item in self.equipment_patterns:
            if item in action_lower:
                # Skip generic terms when specific items are mentioned
                if (
                    item
                    in {
                        "item",
                        "items",
                        "equipment",
                        "gear",
                        "weapon",
                        "weapons",
                        "armor",
                        "armour",
                    }
                    and mentioned_items
                ):
                    continue
                mentioned_items.append(item)

        # Generate queries for specific items - prioritize them
        for item in mentioned_items:
            # Skip generic terms like "buy" from being treated as items
            if item not in {
                "buy",
                "purchase",
                "shop",
                "store",
                "merchant",
                "cost",
                "price",
                "gold",
                "silver",
                "copper",
            }:
                queries.append(
                    RAGQuery(
                        query_text=item,
                        query_type=QueryType.EQUIPMENT,
                        knowledge_base_types=["equipment"],
                        context={"item": item},
                    )
                )

        return queries

    def _generate_character_queries(
        self, action_lower: str, _entities: Set[str]
    ) -> List[RAGQuery]:
        """Generate queries for character-related actions (classes, races, etc.)."""
        queries = []

        # Find mentioned classes
        mentioned_classes: List[str] = []
        for class_kw in self.class_patterns:
            if class_kw in action_lower:
                # Skip generic terms when specific classes are mentioned
                if (
                    class_kw
                    in {
                        "class",
                        "classes",
                        "subclass",
                        "subclasses",
                        "level",
                        "levels",
                        "feature",
                        "features",
                    }
                    and mentioned_classes
                ):
                    continue
                mentioned_classes.append(class_kw)

        # Generate queries for specific classes
        for class_name in mentioned_classes:
            if class_name not in {
                "class",
                "classes",
                "subclass",
                "subclasses",
                "level",
                "levels",
                "multiclass",
                "multiclassing",
            }:
                queries.append(
                    RAGQuery(
                        query_text=class_name,
                        query_type=QueryType.CHARACTER_INFO,
                        knowledge_base_types=["character_options", "rules"],
                        context={"class": class_name},
                    )
                )

        # Find mentioned races
        mentioned_races: List[str] = []
        for race_kw in self.race_patterns:
            if race_kw in action_lower:
                # Skip generic terms when specific races are mentioned
                if (
                    race_kw
                    in {"race", "races", "subrace", "subraces", "traits", "racial"}
                    and mentioned_races
                ):
                    continue
                mentioned_races.append(race_kw)

        # Generate queries for specific races
        for race_name in mentioned_races:
            if race_name not in {
                "race",
                "races",
                "subrace",
                "subraces",
                "traits",
                "racial",
            }:
                queries.append(
                    RAGQuery(
                        query_text=race_name,
                        query_type=QueryType.CHARACTER_INFO,
                        knowledge_base_types=["character_options", "rules"],
                        context={"race": race_name},
                    )
                )

        return queries
