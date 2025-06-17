"""Repository interface definitions for the AI Game Master.

This module defines abstract base classes for all repository interfaces,
providing consistent patterns across the codebase and enabling better
testability through dependency injection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.campaign import CampaignInstanceModel, CampaignTemplateModel
from app.models.character import CharacterInstanceModel, CharacterTemplateModel


class CampaignTemplateRepository(ABC):
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


class CampaignInstanceRepository(ABC):
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
    def list_by_template(self, template_id: str) -> List[CampaignInstanceModel]:
        """List all campaign instances for a given template.

        Args:
            template_id: The template ID to filter by

        Returns:
            List of campaign instances for the template
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


class CharacterTemplateRepository(ABC):
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


class CharacterInstanceRepository(ABC):
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
    def list_by_template(self, template_id: str) -> List[CharacterInstanceModel]:
        """List all character instances for a given template.

        Args:
            template_id: The template ID to filter by

        Returns:
            List of character instances for the template
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
