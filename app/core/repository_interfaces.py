"""Repository interface definitions for the AI Game Master.

This module defines abstract base classes for all repository interfaces,
providing consistent patterns across the codebase and enabling better
testability through dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol, TypeVar

from pydantic import BaseModel

from app.models.campaign import CampaignInstanceModel, CampaignTemplateModel
from app.models.character import CharacterInstanceModel, CharacterTemplateModel
from app.models.game_state import GameStateModel

# Generic TypeVar for repository models
TModel = TypeVar("TModel", bound=BaseModel)


class ICampaignTemplateRepository(ABC):
    """Abstract base class for campaign template data access."""

    @abstractmethod
    def get(self, template_id: str) -> Optional[CampaignTemplateModel]:
        """Get a campaign template by ID.

        Args:
            template_id: The unique identifier of the template

        Returns:
            The campaign template if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, template: CampaignTemplateModel) -> bool:
        """Save a campaign template.

        Args:
            template: The campaign template to save

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def list(self) -> List[CampaignTemplateModel]:
        """List all available campaign templates.

        Returns:
            List of all campaign templates
        """
        pass

    @abstractmethod
    def delete(self, template_id: str) -> bool:
        """Delete a campaign template by ID.

        Args:
            template_id: The unique identifier of the template

        Returns:
            True if deleted successfully, False otherwise
        """
        pass


class ICampaignInstanceRepository(ABC):
    """Abstract base class for campaign instance data access."""

    @abstractmethod
    def get(self, instance_id: str) -> Optional[CampaignInstanceModel]:
        """Get a campaign instance by ID.

        Args:
            instance_id: The unique identifier of the instance

        Returns:
            The campaign instance if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, instance: CampaignInstanceModel) -> bool:
        """Save a campaign instance.

        Args:
            instance: The campaign instance to save

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def list(self) -> List[CampaignInstanceModel]:
        """List all campaign instances.

        Returns:
            List of all campaign instances
        """
        pass

    @abstractmethod
    def delete(self, instance_id: str) -> bool:
        """Delete a campaign instance by ID.

        Args:
            instance_id: The unique identifier of the instance

        Returns:
            True if deleted successfully, False otherwise
        """
        pass


class ICharacterTemplateRepository(ABC):
    """Abstract base class for character template data access."""

    @abstractmethod
    def get(self, template_id: str) -> Optional[CharacterTemplateModel]:
        """Get a character template by ID.

        Args:
            template_id: The unique identifier of the template

        Returns:
            The character template if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, template: CharacterTemplateModel) -> bool:
        """Save a character template.

        Args:
            template: The character template to save

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def list(self) -> List[CharacterTemplateModel]:
        """List all character templates.

        Returns:
            List of all character templates
        """
        pass

    @abstractmethod
    def delete(self, template_id: str) -> bool:
        """Delete a character template by ID.

        Args:
            template_id: The unique identifier of the template

        Returns:
            True if deleted successfully, False otherwise
        """
        pass


class ICharacterInstanceRepository(ABC):
    """Abstract base class for character instance data access."""

    @abstractmethod
    def get(self, instance_id: str) -> Optional[CharacterInstanceModel]:
        """Get a character instance by ID.

        Args:
            instance_id: The unique identifier of the instance

        Returns:
            The character instance if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, instance: CharacterInstanceModel) -> bool:
        """Save a character instance.

        Args:
            instance: The character instance to save

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def list(self) -> List[CharacterInstanceModel]:
        """List all character instances.

        Returns:
            List of all character instances
        """
        pass

    @abstractmethod
    def delete(self, instance_id: str) -> bool:
        """Delete a character instance by ID.

        Args:
            instance_id: The unique identifier of the instance

        Returns:
            True if deleted successfully, False otherwise
        """
        pass


class IGameStateRepository(ABC):
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


class ID5eRepository(Protocol[TModel]):
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
