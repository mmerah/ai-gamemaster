"""
Core interfaces and abstract base classes for the application.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeVar

from langchain_core.documents import Document
from pydantic import BaseModel

from app.models.character import CharacterData
from app.models.combat import InitialCombatantData
from app.models.dice import DiceRequestModel, DiceRollResultResponseModel
from app.models.game_state import ChatMessageModel, GameStateModel
from app.models.rag import LoreDataModel
from app.models.utils import VoiceInfoModel
from app.providers.ai.schemas import AIResponse

# Generic TypeVar for repository models
TModel = TypeVar("TModel", bound=BaseModel)


# --- Data Access and Persistence ---


class GameStateRepository(ABC):
    """Interface for game state persistence and retrieval."""

    @abstractmethod
    def get_game_state(self) -> GameStateModel:
        """Retrieve the current game state."""
        pass

    @abstractmethod
    def save_game_state(self, state: GameStateModel) -> None:
        """Save the game state."""
        pass

    @abstractmethod
    def load_campaign_state(self, campaign_id: str) -> Optional[GameStateModel]:
        """Load a specific campaign's game state."""
        pass


class D5eRepositoryProtocol(Protocol[TModel]):
    """Protocol for D&D 5e data repositories.

    This defines the interface that all D5e repositories must implement,
    providing a consistent API for data access across different entity types.
    """

    def get_by_index(self, index: str) -> Optional[TModel]:
        """Get an entity by its index.

        Args:
            index: The unique index of the entity.

        Returns:
            The entity model if found, None otherwise.
        """
        ...

    def get_by_name(self, name: str) -> Optional[TModel]:
        """Get an entity by its name (case-insensitive).

        Args:
            name: The name of the entity.

        Returns:
            The entity model if found, None otherwise.
        """
        ...

    def list_all(self) -> List[TModel]:
        """List all entities in this repository.

        Returns:
            List of all entity models.
        """
        ...

    def search(self, query: str) -> List[TModel]:
        """Search entities by partial name match.

        Args:
            query: The search query (partial name).

        Returns:
            List of matching entity models.
        """
        ...

    def filter_by(self, **criteria: Any) -> List[TModel]:
        """Filter entities by specific criteria.

        Args:
            **criteria: Field-value pairs to filter by.

        Returns:
            List of matching entity models.
        """
        ...


# --- Domain Services ---


class CharacterService(ABC):
    """Interface for character-related operations."""

    @abstractmethod
    def get_character(self, character_id: str) -> Optional[CharacterData]:
        """Get a character by ID, returning combined character data."""
        pass

    @abstractmethod
    def find_character_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Find character ID by name or direct ID match."""
        pass

    @abstractmethod
    def get_character_name(self, character_id: str) -> str:
        """Get display name for a character."""
        pass


class DiceRollingService(ABC):
    """Interface for dice rolling operations."""

    @abstractmethod
    def perform_roll(
        self,
        character_id: str,
        roll_type: str,
        dice_formula: str,
        skill: Optional[str] = None,
        ability: Optional[str] = None,
        dc: Optional[int] = None,
        reason: str = "",
        original_request_id: Optional[str] = None,
    ) -> DiceRollResultResponseModel:
        """Perform a dice roll and return the result."""
        pass


class CombatService(ABC):
    """Interface for combat-related operations."""

    @abstractmethod
    def start_combat(self, combatants: List[InitialCombatantData]) -> None:
        """Start a new combat encounter."""
        pass

    @abstractmethod
    def end_combat(self) -> None:
        """End the current combat encounter."""
        pass

    @abstractmethod
    def advance_turn(self) -> None:
        """Advance to the next turn in combat."""
        pass

    @abstractmethod
    def determine_initiative_order(
        self, roll_results: List[DiceRollResultResponseModel]
    ) -> None:
        """Determine and set initiative order based on roll results."""
        pass


class ChatService(ABC):
    """Interface for chat/message operations."""

    @abstractmethod
    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to chat history."""
        pass

    @abstractmethod
    def get_chat_history(self) -> list[ChatMessageModel]:
        """Get the current chat history."""
        pass


class ContentServiceProtocol(Protocol):
    """Protocol for the main content service.

    This defines the high-level interface for accessing all D&D 5e content data.
    """

    # Character creation helpers
    def get_class_at_level(
        self, class_name: str, level: int
    ) -> Optional[Dict[str, Any]]:
        """Get complete class information at a specific level.

        Args:
            class_name: Name of the class.
            level: Character level (1-20).

        Returns:
            Dictionary with class features, spell slots, etc.
        """
        ...

    def calculate_ability_modifiers(self, scores: Dict[str, int]) -> Dict[str, int]:
        """Calculate ability modifiers from ability scores.

        Args:
            scores: Dictionary mapping ability names to scores.

        Returns:
            Dictionary mapping ability names to modifiers.
        """
        ...

    def get_proficiency_bonus(self, level: int) -> int:
        """Get proficiency bonus for a character level.

        Args:
            level: Character level (1-20).

        Returns:
            Proficiency bonus.
        """
        ...

    # Spell helpers
    def get_spells_for_class(
        self, class_name: str, level: Optional[int] = None
    ) -> List[BaseModel]:
        """Get all spells available to a class.

        Args:
            class_name: Name of the class.
            level: Optional spell level filter.

        Returns:
            List of spell models.
        """
        ...

    def get_spell_slots(self, class_name: str, level: int) -> Dict[int, int]:
        """Get spell slots by class and level.

        Args:
            class_name: Name of the spellcasting class.
            level: Character level.

        Returns:
            Dictionary mapping spell level to number of slots.
        """
        ...

    # Monster helpers
    def get_monsters_by_cr(self, min_cr: float, max_cr: float) -> List[BaseModel]:
        """Get monsters within a challenge rating range.

        Args:
            min_cr: Minimum challenge rating.
            max_cr: Maximum challenge rating.

        Returns:
            List of monster models.
        """
        ...

    # Equipment helpers
    def get_starting_equipment(
        self, class_name: str, background: str
    ) -> List[BaseModel]:
        """Get all starting equipment options.

        Args:
            class_name: Name of the class.
            background: Name of the background.

        Returns:
            List of equipment models.
        """
        ...

    # Rules helpers
    def get_rule_section(self, section: str) -> List[str]:
        """Get rules text for a specific section.

        Args:
            section: Name of the rule section.

        Returns:
            List of rule text paragraphs.
        """
        ...


# --- AI and RAG Systems ---


class AIResponseProcessor(ABC):
    """Interface for processing AI responses."""

    @abstractmethod
    def process_response(
        self, ai_response: AIResponse, correlation_id: Optional[str] = None
    ) -> Tuple[List[DiceRequestModel], bool]:
        """Process an AI response and return pending requests and rerun flag."""
        pass

    @property
    @abstractmethod
    def character_service(self) -> CharacterService:
        """Get the character service."""
        pass

    @property
    @abstractmethod
    def event_queue(self) -> Any:  # EventQueue
        """Get the event queue."""
        pass

    @abstractmethod
    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Find combatant ID by name or direct ID match."""
        pass


class QueryType(Enum):
    """Types of RAG queries based on player actions."""

    COMBAT = "combat"
    SPELL_CASTING = "spell_casting"
    SKILL_CHECK = "skill_check"
    SOCIAL_INTERACTION = "social_interaction"
    EXPLORATION = "exploration"
    RULES_LOOKUP = "rules_lookup"
    GENERAL = "general"


class KnowledgeResult(BaseModel):
    """Single piece of retrieved knowledge."""

    content: str
    source: str  # Which knowledge base this came from
    relevance_score: float = 1.0
    metadata: Dict[
        str, Any
    ] = {}  # JUSTIFIED: LangChain document metadata can contain arbitrary fields

    @classmethod
    def from_document(
        cls, doc: Document, source: str, score: float = 1.0
    ) -> "KnowledgeResult":
        """Create from LangChain Document."""
        return cls(
            content=doc.page_content,
            source=source,
            relevance_score=score,
            metadata=doc.metadata,
        )


class RAGQuery(BaseModel):
    """A query to be executed against knowledge bases."""

    query_text: str
    query_type: QueryType
    context: Dict[
        str, Any
    ] = {}  # JUSTIFIED: RAG query context varies by query type and knowledge domain
    knowledge_base_types: List[str] = []  # Which KBs to search, empty = all


class RAGResults(BaseModel):
    """Collection of results from RAG queries."""

    results: List[KnowledgeResult] = []
    total_queries: int = 0
    execution_time_ms: float = 0.0

    def has_results(self) -> bool:
        return len(self.results) > 0

    def format_for_prompt(self) -> str:
        """Format results for injection into AI prompt."""
        if not self.results:
            return ""

        formatted_sections = []
        current_source = None
        current_items: List[str] = []

        # Group by source
        for result in self.results:
            if result.source != current_source:
                if current_items:
                    formatted_sections.append(
                        f"{current_source}:\n"
                        + "\n".join(f"- {item}" for item in current_items)
                    )
                current_source = result.source
                current_items = [result.content]
            else:
                current_items.append(result.content)

        # Add the last group
        if current_items:
            formatted_sections.append(
                f"{current_source}:\n"
                + "\n".join(f"- {item}" for item in current_items)
            )

        return "RELEVANT KNOWLEDGE:\n" + "\n\n".join(formatted_sections)

    def debug_format(self) -> str:
        """Format results for debug logging."""
        if not self.results:
            return "No RAG results retrieved."

        lines = [
            f"RAG Retrieved {len(self.results)} results in {self.execution_time_ms:.1f}ms:"
        ]
        for result in self.results:
            lines.append(
                f"  [{result.source}] {result.content[:100]}{'...' if len(result.content) > 100 else ''}"
            )
        return "\n".join(lines)


class RAGService:
    """Main RAG service interface - simplified with LangChain."""

    def get_relevant_knowledge(
        self,
        action: str,
        game_state: GameStateModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> RAGResults:
        """Get relevant knowledge for a player action.

        Args:
            action: The player's action text
            game_state: Current game state
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            RAG results with relevant knowledge
        """
        raise NotImplementedError

    def analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]:
        """Analyze a player action and generate relevant RAG queries."""
        raise NotImplementedError


class KnowledgeBaseProtocol(Protocol):
    """Protocol for knowledge base managers."""

    def search(
        self,
        query: str,
        kb_types: Optional[List[str]] = None,
        k: int = 3,
        score_threshold: float = 0.3,
        content_pack_priority: Optional[List[str]] = None,
    ) -> RAGResults:
        """Search across knowledge bases.

        Args:
            query: Search query text
            kb_types: List of knowledge base types to search
            k: Number of results to return
            score_threshold: Minimum relevance score
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            RAG results with relevant knowledge
        """
        ...

    def add_campaign_lore(self, campaign_id: str, lore_data: LoreDataModel) -> None:
        """Add campaign-specific lore."""
        ...

    def add_event(
        self,
        campaign_id: str,
        event_summary: str,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an event to campaign event log."""
        ...


# --- External Service Integrations ---


class BaseTTSService(ABC):
    """Interface for Text-to-Speech services."""

    @abstractmethod
    def synthesize_speech(self, text: str, voice_id: str) -> Optional[str]:
        """
        Synthesizes speech from text using the given voice_id.
        Returns the relative path (from static folder root) to the audio file on success, None on failure.
        Example returned path: "tts_cache/unique_filename.wav"
        """
        pass

    @abstractmethod
    def get_available_voices(
        self, lang_code: Optional[str] = None
    ) -> List[VoiceInfoModel]:
        """
        Returns a list of available voices. Each voice is a VoiceInfoModel with id and name fields.
        Optionally filtered by language code. For now, only English voices are supported.
        """
        pass
