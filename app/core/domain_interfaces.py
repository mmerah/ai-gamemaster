"""Domain service interfaces for the AI Game Master.

This module defines interfaces for core game domain services like
character management, dice rolling, combat, chat, and campaign management.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.core.repository_interfaces import ICharacterTemplateRepository
from app.models.campaign.instance import CampaignInstanceModel
from app.models.character.utils import CharacterData
from app.models.combat.combatant import InitialCombatantData
from app.models.dice import DiceRollResultResponseModel
from app.models.game_state.main import GameStateModel
from app.models.shared import ChatMessageModel


class ICharacterService(ABC):
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


class IDiceRollingService(ABC):
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


class ICombatService(ABC):
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


class IChatService(ABC):
    """Interface for chat/message operations."""

    @abstractmethod
    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to chat history."""
        pass

    @abstractmethod
    def get_chat_history(self) -> list[ChatMessageModel]:
        """Get the current chat history."""
        pass


class ICampaignService(ABC):
    """Interface for campaign management service."""

    @abstractmethod
    def create_campaign_instance(
        self, template_id: str, instance_name: str, character_ids: List[str]
    ) -> Optional[CampaignInstanceModel]:
        """Create a new campaign instance from a template.

        Args:
            template_id: ID of the campaign template
            instance_name: Name for the campaign instance
            character_ids: List of character template IDs to include

        Returns:
            Created campaign instance or None on failure
        """
        pass

    @abstractmethod
    def start_campaign_from_template(
        self, template_id: str, instance_name: str, party_character_ids: List[str]
    ) -> Optional[GameStateModel]:
        """Create and start a new campaign instance from a template.

        Args:
            template_id: ID of the campaign template
            instance_name: Name for the campaign instance
            party_character_ids: List of character IDs for the party

        Returns:
            Game state for the new campaign or None on failure
        """
        pass

    @abstractmethod
    def start_campaign(
        self, campaign_id: str, party_character_ids: Optional[List[str]] = None
    ) -> Optional[GameStateModel]:
        """Start a campaign (backward compatibility method).

        This method handles both campaign instances and templates:
        - If campaign_id is an instance ID, loads that instance
        - If campaign_id is a template ID and party_character_ids provided, creates new instance
        - Otherwise treats as template view

        Args:
            campaign_id: Campaign ID (template or instance)
            party_character_ids: Optional list of character IDs

        Returns:
            Game state for the campaign or None
        """
        pass

    @abstractmethod
    def get_character_template_repository(self) -> ICharacterTemplateRepository:
        """Get the character template repository.

        Returns:
            Character template repository instance
        """
        pass
