"""
RAG query engine that analyzes player actions and generates relevant queries.
"""

import logging
import re
from typing import List

from app.content.rag.combat_context_augmentor import CombatContextAugmentor
from app.models.game_state import GameStateModel
from app.models.rag import QueryType, RAGQuery

logger = logging.getLogger(__name__)


class RAGQueryEngineImpl:
    """
    Analyzes player actions to generate relevant RAG queries.
    Uses enhanced pattern matching and fuzzy spell detection to determine what knowledge is needed.
    """

    def __init__(self) -> None:
        # Initialize combat context augmentor
        self.combat_augmentor = CombatContextAugmentor()

        # Enhanced spell patterns with better matching
        self.spell_patterns = [
            r"\b(?:cast|casting|use|uses|unleash|unleashes|channel|channels|invoke|invokes|fire|fires|launch|launches|throw|throws|activate|activates|trigger|triggers)\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\s+(?:spell|at|on|against))?",
            r"\b(fireball|ice knife|cure wounds|healing word|shield|magic missile|vicious mockery|thunder wave|eldritch blast)\b",
            r"\b([a-zA-Z\s]+?)\s+(?:spell|cantrip)\b",
        ]

        # Known spell names with common variations for fuzzy matching
        self.known_spells = {
            "fireball": ["fireball", "fire ball", "flame ball"],
            "ice_knife": [
                "ice knife",
                "iceknife",
                "ice shard",
                "frozen knife",
                "ice blade",
            ],
            "cure_wounds": [
                "cure wounds",
                "cure wound",
                "healing touch",
                "heal wounds",
                "mend wounds",
            ],
            "healing_word": [
                "healing word",
                "heal word",
                "word of healing",
                "healing phrase",
            ],
            "vicious_mockery": [
                "vicious mockery",
                "mockery",
                "insult",
                "verbal attack",
                "cutting words",
            ],
            "shield": ["shield", "magic shield", "barrier", "protection"],
            "magic_missile": [
                "magic missile",
                "missile",
                "force missile",
                "force dart",
            ],
            "thunder_wave": [
                "thunder wave",
                "thunderwave",
                "sonic boom",
                "thunder blast",
            ],
            "eldritch_blast": [
                "eldritch blast",
                "eldritch beam",
                "warlock blast",
                "eldritch ray",
            ],
        }

        # Enhanced combat action patterns
        self.combat_patterns = [
            r"\b(?:attack|attacks|hit|hits|strike|strikes|swing|swings)\b",
            r"\b(?:dodge|dodges|block|blocks|parry|parries)\b",
            r"\b(?:charge|charges|rush|rushes)\b",
            r"\b(?:shoot|shoots|fire|fires|arrow|arrows)\b",
            r"\b(?:stab|stabs|slash|slashes|thrust|thrusts)\b",
            r"\b(?:grapple|grapples|grab|grabs|wrestle|wrestles)\b",
            r"\b(?:turn|combat|fight|battle)\b",  # Add turn-based combat indicators
            r"(?:narrate|describe).*(?:action|attack|move)",  # For DM narration requests
        ]

        # Enhanced skill check patterns
        self.skill_patterns = [
            r"\b(?:perception|investigation|insight|persuasion|deception|intimidation|stealth|acrobatics|athletics|sleight of hand|survival|nature|history|arcana|religion|medicine|performance|animal handling)\b",
            r"\b(?:look|looks|search|searches|examine|examines|inspect|inspects|scan|scans)\b",
            r"\b(?:sneak|sneaks|hide|hides|creep|creeps|skulk|skulks)\b",
            r"\b(?:convince|persuade|lie|deceive|intimidate|threaten|bluff|bluffs)\b",
            r"\b(?:climb|climbs|jump|jumps|balance|balances|tumble|tumbles)\b",
        ]

        # Skill mapping for common action words to D&D skills
        self.skill_mapping = {
            "sneak": "stealth",
            "sneaks": "stealth",
            "hide": "stealth",
            "hides": "stealth",
            "creep": "stealth",
            "creeps": "stealth",
            "skulk": "stealth",
            "skulks": "stealth",
            "convince": "persuasion",
            "persuade": "persuasion",
            "talk": "persuasion",
            "lie": "deception",
            "deceive": "deception",
            "bluff": "deception",
            "bluffs": "deception",
            "threaten": "intimidation",
            "intimidate": "intimidation",
            "look": "perception",
            "looks": "perception",
            "watch": "perception",
            "listen": "perception",
            "search": "investigation",
            "searches": "investigation",
            "examine": "investigation",
            "climb": "athletics",
            "climbs": "athletics",
            "swim": "athletics",
            "jump": "athletics",
            "balance": "acrobatics",
            "tumble": "acrobatics",
            "dodge": "acrobatics",
        }

        # Social interaction patterns
        self.social_patterns = [
            r"\b(?:talk|talks|speak|speaks|say|says|tell|tells)\s+(?:to|with)\s+([a-zA-Z\s]+)",
            r"\b(?:negotiate|negotiates|bargain|bargains|converse|converses)\b",
            r"\b(?:greet|greets|approach|approaches|hail|hails)\s+([a-zA-Z\s]+)",
            r"\b(?:ask|asks|question|questions|inquire|inquires)\s+([a-zA-Z\s]+)",
        ]

        # Enhanced monster/creature name patterns
        self.creature_patterns = [
            r"\b(?:goblin|goblins|orc|orcs|dragon|dragons|kobold|kobolds|skeleton|skeletons|zombie|zombies|wolf|wolves|bear|bears|giant|giants)\b",
            r"\b(?:bandit|bandits|guard|guards|soldier|soldiers|knight|knights)\b",
            r"\b(?:troll|trolls|ogre|ogres|hobgoblin|hobgoblins|bugbear|bugbears)\b",
            r"\b(?:spider|spiders|rat|rats|bat|bats|hawk|hawks|eagle|eagles)\b",
        ]

        # Spell keywords that suggest spellcasting
        self.spell_keywords = [
            "spell",
            "magic",
            "incantation",
            "cantrip",
            "enchantment",
            "conjuration",
            "evocation",
            "abjuration",
            "divination",
            "illusion",
            "necromancy",
            "transmutation",
        ]

        logger.info("RAG Query Engine initialized with enhanced pattern matching")

    def analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]:
        """Analyze a player action and generate relevant RAG queries."""
        if not action or not isinstance(action, str):
            return []

        action_lower = action.lower()
        queries = []

        # Determine query type and generate specific queries
        query_type = self._determine_query_type(action_lower, game_state)

        # Generate queries based on action type
        if query_type == QueryType.SPELL_CASTING:
            queries.extend(self._generate_spell_queries(action_lower, game_state))

        elif query_type == QueryType.COMBAT:
            queries.extend(self._generate_combat_queries(action_lower, game_state))

        elif query_type == QueryType.SKILL_CHECK:
            queries.extend(self._generate_skill_queries(action_lower, game_state))

        elif query_type == QueryType.SOCIAL_INTERACTION:
            queries.extend(self._generate_social_queries(action_lower, game_state))

        elif query_type == QueryType.EXPLORATION:
            queries.extend(self._generate_exploration_queries(action_lower, game_state))

        # Always add general context queries
        queries.extend(self._generate_general_queries(action_lower, game_state))

        # Apply combat context augmentation if needed
        queries = self.combat_augmentor.augment_queries_with_combat_context(
            queries, game_state
        )

        logger.debug(
            f"Generated {len(queries)} RAG queries for action type: {query_type.value}"
        )
        return queries

    def _determine_query_type(
        self, action: str, game_state: GameStateModel
    ) -> QueryType:
        """Determine the primary type of action being performed."""
        # Enhanced spell detection - check for spell keywords first
        if self._contains_spell_indicators(action):
            return QueryType.SPELL_CASTING

        # Check for specific spell patterns
        for pattern in self.spell_patterns:
            if re.search(pattern, action, re.IGNORECASE):
                return QueryType.SPELL_CASTING

        # Check for combat actions
        for pattern in self.combat_patterns:
            if re.search(pattern, action, re.IGNORECASE):
                return QueryType.COMBAT

        # Check for skill-based actions
        for pattern in self.skill_patterns:
            if re.search(pattern, action, re.IGNORECASE):
                return QueryType.SKILL_CHECK

        # Check for social interactions
        for pattern in self.social_patterns:
            if re.search(pattern, action, re.IGNORECASE):
                return QueryType.SOCIAL_INTERACTION

        # Check for exploration keywords
        if any(
            word in action
            for word in [
                "move",
                "go",
                "walk",
                "travel",
                "explore",
                "enter",
                "exit",
                "door",
                "path",
            ]
        ):
            return QueryType.EXPLORATION

        return QueryType.GENERAL

    def _contains_spell_indicators(self, action: str) -> bool:
        """Check if action contains spell-related keywords or known spell names."""
        # Check for spell keywords
        for keyword in self.spell_keywords:
            if keyword in action:
                return True

        # Check for known spell names and variants
        for spell_id, variants in self.known_spells.items():
            for variant in variants:
                if variant in action:
                    return True

        return False

    def _generate_spell_queries(
        self, action: str, game_state: GameStateModel
    ) -> List[RAGQuery]:
        """Generate queries for spell casting actions."""
        queries = []

        # Extract spell name with enhanced matching
        spell_name = self._extract_spell_name_enhanced(action)
        if spell_name:
            # Query for specific spell mechanics
            queries.append(
                RAGQuery(
                    query_text=f"{spell_name} spell mechanics damage range saving throw components",
                    query_type=QueryType.SPELL_CASTING,
                    knowledge_base_types=["spells", "rules"],
                    context={"spell_name": spell_name},
                )
            )

            # Add semantic queries for spell effects
            if any(word in spell_name.lower() for word in ["damage", "harm", "attack"]):
                queries.append(
                    RAGQuery(
                        query_text="damage spells attack spells ranged spell attack",
                        query_type=QueryType.SPELL_CASTING,
                        knowledge_base_types=["spells", "rules"],
                    )
                )
            elif any(
                word in spell_name.lower() for word in ["heal", "cure", "restore"]
            ):
                queries.append(
                    RAGQuery(
                        query_text="healing spells restoration hit points recovery",
                        query_type=QueryType.SPELL_CASTING,
                        knowledge_base_types=["spells", "rules"],
                    )
                )

        # Check if there's a target creature mentioned
        creatures = self._extract_creatures(action)
        for creature in creatures:
            queries.append(
                RAGQuery(
                    query_text=f"{creature} stats armor class hit points abilities",
                    query_type=QueryType.SPELL_CASTING,  # Keep as spell casting context
                    knowledge_base_types=["monsters"],
                    context={
                        "creature": creature,
                        "spell_name": spell_name if spell_name else "",
                    },
                )
            )

        # General spellcasting rules
        queries.append(
            RAGQuery(
                query_text="spellcasting concentration spell slots verbal somatic material components",
                query_type=QueryType.SPELL_CASTING,
                knowledge_base_types=["rules"],
            )
        )

        return queries

    def _generate_combat_queries(
        self, action: str, game_state: GameStateModel
    ) -> List[RAGQuery]:
        """Generate queries for combat actions."""
        queries = []

        # Check for target creatures
        creatures = self._extract_creatures(action)
        for creature in creatures:
            queries.append(
                RAGQuery(
                    query_text=f"{creature} stats armor class hit points abilities resistances",
                    query_type=QueryType.COMBAT,
                    knowledge_base_types=["monsters", "rules"],
                    context={"creature": creature},
                )
            )

        # Combat mechanics based on action type
        if any(word in action for word in ["attack", "hit", "strike", "swing"]):
            queries.append(
                RAGQuery(
                    query_text="attack roll damage roll critical hit advantage disadvantage",
                    query_type=QueryType.COMBAT,
                    knowledge_base_types=["rules"],
                )
            )

        if any(word in action for word in ["dodge", "block", "parry"]):
            queries.append(
                RAGQuery(
                    query_text="dodge action armor class defensive combat",
                    query_type=QueryType.COMBAT,
                    knowledge_base_types=["rules"],
                )
            )

        # Check if in combat for turn order info
        if hasattr(game_state, "combat") and game_state.combat.is_active:
            queries.append(
                RAGQuery(
                    query_text="combat turn order initiative actions bonus actions movement",
                    query_type=QueryType.COMBAT,
                    knowledge_base_types=["rules"],
                )
            )

        return queries

    def _generate_skill_queries(
        self, action: str, game_state: GameStateModel
    ) -> List[RAGQuery]:
        """Generate queries for skill check actions."""
        queries = []

        # Extract and normalize skill name
        skill = self._extract_skill_name(action)
        if skill:
            # Map common actions to actual D&D skills
            normalized_skill = self.skill_mapping.get(skill, skill)

            # Generate specific skill queries
            queries.append(
                RAGQuery(
                    query_text=f"{normalized_skill} skill ability check proficiency",
                    query_type=QueryType.SKILL_CHECK,
                    knowledge_base_types=["rules"],
                    context={"skill": normalized_skill},
                )
            )

            # Add query for skill lists to find the actual skill definition
            queries.append(
                RAGQuery(
                    query_text=f"skills list {normalized_skill} dexterity charisma wisdom intelligence",
                    query_type=QueryType.SKILL_CHECK,
                    knowledge_base_types=["rules"],
                    context={"skill": normalized_skill},
                )
            )

            # Add specific queries based on skill type
            if normalized_skill in ["stealth", "sleight of hand", "acrobatics"]:
                queries.append(
                    RAGQuery(
                        query_text="dexterity skills stealth hiding sneaking",
                        query_type=QueryType.SKILL_CHECK,
                        knowledge_base_types=["rules"],
                    )
                )
            elif normalized_skill in [
                "persuasion",
                "deception",
                "intimidation",
                "performance",
            ]:
                queries.append(
                    RAGQuery(
                        query_text="charisma skills persuasion social interaction",
                        query_type=QueryType.SKILL_CHECK,
                        knowledge_base_types=["rules"],
                    )
                )

        return queries

    def _generate_social_queries(
        self, action: str, game_state: GameStateModel
    ) -> List[RAGQuery]:
        """Generate queries for social interaction actions."""
        queries = []

        # Extract NPC name
        npc_name = self._extract_npc_name(action)
        if npc_name:
            queries.append(
                RAGQuery(
                    query_text=f"{npc_name} personality motivations relationships attitude",
                    query_type=QueryType.SOCIAL_INTERACTION,
                    knowledge_base_types=["npcs", "lore", "adventure"],
                    context={"npc_name": npc_name},
                )
            )

        # Social mechanics
        queries.append(
            RAGQuery(
                query_text="persuasion deception intimidation insight social interaction",
                query_type=QueryType.SOCIAL_INTERACTION,
                knowledge_base_types=["rules"],
            )
        )

        return queries

    def _generate_exploration_queries(
        self, action: str, game_state: GameStateModel
    ) -> List[RAGQuery]:
        """Generate queries for exploration actions."""
        queries = []

        # Current location context
        if hasattr(game_state, "current_location"):
            location = game_state.current_location.name
            if location:
                queries.append(
                    RAGQuery(
                        query_text=f"{location} description exits secrets dangers",
                        query_type=QueryType.EXPLORATION,
                        knowledge_base_types=["lore", "adventure"],
                        context={"location": location},
                    )
                )

        return queries

    def _generate_general_queries(
        self, action: str, game_state: GameStateModel
    ) -> List[RAGQuery]:
        """Generate general context queries that might be relevant."""
        queries = []

        # ALWAYS check for creatures in any action
        creatures = self._extract_creatures(action)
        for creature in creatures:
            queries.append(
                RAGQuery(
                    query_text=f"{creature} stats armor class hit points abilities attacks damage resistances",
                    query_type=QueryType.GENERAL,
                    knowledge_base_types=["monsters"],
                    context={"creature": creature},
                )
            )

        # Current adventure context
        if hasattr(game_state, "event_summary") and game_state.event_summary:
            recent_events = " ".join(game_state.event_summary[-3:])  # Last 3 events
            queries.append(
                RAGQuery(
                    query_text=f"current adventure context {recent_events}",
                    query_type=QueryType.GENERAL,
                    knowledge_base_types=["adventure"],
                    context={"recent_events": recent_events},
                )
            )

        return queries

    def _extract_spell_name_enhanced(self, action: str) -> str:
        """Enhanced spell name extraction with fuzzy matching."""
        # First try exact pattern matching
        for pattern in self.spell_patterns:
            match = re.search(pattern, action, re.IGNORECASE)
            if match:
                spell_name = (
                    match.group(1).strip()
                    if match.lastindex and match.lastindex >= 1
                    else match.group(0).strip()
                )
                # Clean up common words
                spell_name = re.sub(
                    r"\b(?:spell|at|on|the|a|an|against|with|my|his|her|their)\b",
                    "",
                    spell_name,
                    flags=re.IGNORECASE,
                ).strip()
                if spell_name and len(spell_name) > 2:
                    # Try to match to known spells
                    normalized_spell = self._normalize_spell_name(spell_name)
                    if normalized_spell:
                        return normalized_spell
                    return spell_name

        # Try fuzzy matching against known spells
        for spell_id, variants in self.known_spells.items():
            for variant in variants:
                if variant in action.lower():
                    return spell_id.replace("_", " ")

        return ""

    def _normalize_spell_name(self, spell_name: str) -> str:
        """Normalize spell name to match known spells."""
        spell_lower = spell_name.lower().strip()

        # Direct match
        for spell_id, variants in self.known_spells.items():
            if spell_lower in [v.lower() for v in variants]:
                return spell_id.replace("_", " ")

        # Partial match
        for spell_id, variants in self.known_spells.items():
            for variant in variants:
                if variant.lower() in spell_lower or spell_lower in variant.lower():
                    return spell_id.replace("_", " ")

        return spell_name

    def _extract_creatures(self, action: str) -> List[str]:
        """Extract creature names from action text."""
        creatures = []

        # First check for known creature types
        action_lower = action.lower()
        for pattern in self.creature_patterns:
            matches = re.findall(pattern, action_lower)
            creatures.extend(matches)

        # Also check in the original case-sensitive text for proper nouns
        # This helps catch things like "Goblin Cook" → "Goblin"
        words = action.split()
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in [
                "goblin",
                "goblins",
                "orc",
                "orcs",
                "dragon",
                "dragons",
                "kobold",
                "kobolds",
                "skeleton",
                "skeletons",
                "zombie",
                "zombies",
                "troll",
                "trolls",
                "ogre",
                "ogres",
                "giant",
                "giants",
            ]:
                creatures.append(word_lower.rstrip("s"))  # Remove plural

        return list(set(creatures))  # Remove duplicates

    def _extract_skill_name(self, action: str) -> str:
        """Extract skill name from action text."""
        action_lower = action.lower()

        # First check for direct skill mappings
        for action_word, skill in self.skill_mapping.items():
            if action_word in action_lower:
                return skill

        # Then check for direct skill name matches
        for pattern in self.skill_patterns:
            match = re.search(pattern, action, re.IGNORECASE)
            if match:
                matched_skill = match.group(0).lower()
                # Map to actual skill if needed
                return self.skill_mapping.get(matched_skill, matched_skill)

        return ""

    def _extract_npc_name(self, action: str) -> str:
        """Extract NPC name from action text (simplified)."""
        # Look for patterns like "talk to [Name]" or "approach [Name]"
        patterns = [
            r"(?:talk|speak|say|tell|ask|greet|approach|negotiate)\s+(?:to|with)?\s+([A-Z][a-zA-Z\s]+)",
            r"([A-Z][a-zA-Z\s]+)(?:\s+(?:says|tells|speaks|responds))",
        ]

        for pattern in patterns:
            match = re.search(pattern, action)
            if match:
                npc_name = match.group(1).strip()
                # Filter out common false positives
                if npc_name.lower() not in [
                    "the",
                    "that",
                    "this",
                    "what",
                    "where",
                    "when",
                    "how",
                ]:
                    return npc_name

        return ""
