"""Orchestration service interfaces for the AI Game Master.

This module defines interfaces for high-level orchestration services
that coordinate between multiple domain services.
"""

from abc import ABC, abstractmethod

from app.models.events.game_events import GameEventModel, GameEventResponseModel


class IGameOrchestrator(ABC):
    """Interface for game orchestration service."""

    @abstractmethod
    async def handle_event(self, event: GameEventModel) -> GameEventResponseModel:
        """Handle a game event through the unified entry point.

        Args:
            event: Game event to process

        Returns:
            Game event response
        """
        pass

    @abstractmethod
    def get_game_state(self) -> GameEventResponseModel:
        """Get the current game state.

        Returns:
            Game state response
        """
        pass
