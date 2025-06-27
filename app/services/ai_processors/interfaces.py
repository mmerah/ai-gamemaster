"""
Interfaces for AI response processors.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from app.models.combat.state import NextCombatantInfoModel
from app.models.dice import DiceRequestModel
from app.providers.ai.schemas import AIResponse


class INarrativeProcessor(ABC):
    """Interface for processing narrative and location updates."""

    @abstractmethod
    def process_narrative_and_location(
        self, ai_response: AIResponse, correlation_id: Optional[str] = None
    ) -> None:
        """Process narrative and location updates from AI response."""
        pass


class IStateUpdateProcessor(ABC):
    """Interface for processing game state updates."""

    @abstractmethod
    def process_game_state_updates(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> bool:
        """Process game state updates from AI response.

        Returns:
            bool: True if combat was started, False otherwise.
        """
        pass


class IRagProcessor(ABC):
    """Interface for processing RAG event logging."""

    @abstractmethod
    def process_rag_event_logging(self, ai_response: AIResponse) -> None:
        """Update RAG event log with AI response narrative."""
        pass


class IDiceRequestProcessor(ABC):
    """Interface for processing dice requests from AI responses."""

    @abstractmethod
    def process_dice_requests(
        self, ai_response: AIResponse, combat_just_started: bool
    ) -> Tuple[List[DiceRequestModel], bool, bool]:
        """Process dice requests from AI response.

        Returns:
            Tuple containing:
            - List of pending player dice requests
            - Whether NPC rolls were performed
            - Whether AI rerun is needed after NPC rolls
        """
        pass


class ITurnAdvancementProcessor(ABC):
    """Interface for processing turn advancement from AI responses."""

    @abstractmethod
    def handle_turn_advancement(
        self,
        ai_response: AIResponse,
        needs_ai_rerun: bool,
        player_requests_pending: bool,
        next_combatant_info: Optional[NextCombatantInfoModel] = None,
    ) -> None:
        """Handle turn advancement based on AI signal and current state.

        Args:
            ai_response: The AI response containing potential end_turn signal
            needs_ai_rerun: Whether AI needs to be called again
            player_requests_pending: Whether there are pending player dice requests
            next_combatant_info: Pre-calculated info about the next combatant
        """
        pass
