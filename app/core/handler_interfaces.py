"""Handler interfaces for the AI Game Master.

This module defines interfaces for game event handlers
that process various types of player and system actions.
"""

from abc import ABC, abstractmethod
from typing import List

from app.models.dice import DiceRollResultResponseModel, DiceRollSubmissionModel
from app.models.events.game_events import GameEventResponseModel, PlayerActionEventModel


class IPlayerActionHandler(ABC):
    """Interface for handling player actions."""

    @abstractmethod
    def handle(self, action_data: PlayerActionEventModel) -> GameEventResponseModel:
        """Handle a player action event.

        Args:
            action_data: Player action event data

        Returns:
            Game event response
        """
        pass


class IDiceSubmissionHandler(ABC):
    """Interface for handling dice submissions."""

    @abstractmethod
    def handle(self, rolls: List[DiceRollSubmissionModel]) -> GameEventResponseModel:
        """Handle dice roll submissions.

        Args:
            rolls: List of dice roll submissions

        Returns:
            Game event response
        """
        pass

    @abstractmethod
    def handle_completed_rolls(
        self, results: List[DiceRollResultResponseModel]
    ) -> GameEventResponseModel:
        """Handle already-completed dice roll results.

        Args:
            results: List of completed dice roll results

        Returns:
            Game event response
        """
        pass


class INextStepHandler(ABC):
    """Interface for handling next step triggers."""

    @abstractmethod
    def handle(self) -> GameEventResponseModel:
        """Handle next step trigger.

        Returns:
            Game event response
        """
        pass


class IRetryHandler(ABC):
    """Interface for handling retry requests."""

    @abstractmethod
    def handle(self) -> GameEventResponseModel:
        """Handle retry request.

        Returns:
            Game event response
        """
        pass
