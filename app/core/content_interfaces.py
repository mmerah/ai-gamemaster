"""Content management interfaces for the AI Game Master.

This module defines interfaces for D&D 5e content management,
content packs, and indexing services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

from app.content.schemas import (
    D5eAbilityScore,
    D5eAlignment,
    D5eBackground,
    D5eClass,
    D5eLanguage,
    D5eRace,
    D5eSkill,
)
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentPackWithStats,
    ContentUploadResult,
    D5eContentPack,
)
from app.content.schemas.content_types import ContentTypeInfo
from app.content.schemas.types import (
    ClassAtLevelInfo,
    D5eEntity,
    SearchResults,
    StartingEquipmentInfo,
)


class IContentService(ABC):
    """Interface for D&D 5e content management service."""

    @abstractmethod
    def get_content_filtered(
        self,
        content_type: str,
        filters: Dict[str, Any],
        content_pack_ids: Optional[List[str]] = None,
    ) -> List[D5eEntity]:
        """Get filtered content of a specific type.

        Args:
            content_type: Type of content (e.g., 'spells', 'monsters')
            filters: Optional filters to apply
            content_pack_priority: Content pack priority list

        Returns:
            List of filtered content items
        """
        pass

    @abstractmethod
    def get_content_by_id(
        self,
        content_type: str,
        item_id: str,
        content_pack_ids: Optional[List[str]] = None,
    ) -> Optional[D5eEntity]:
        """Get a specific content item by ID.

        Args:
            content_type: Type of content
            item_id: ID of the item
            content_pack_priority: Content pack priority list

        Returns:
            Content item or None
        """
        pass

    @abstractmethod
    def search_all_content(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        content_pack_priority: Optional[List[str]] = None,
    ) -> SearchResults:
        """Search across all content types.

        Args:
            query: Search query
            types: Optional list of types to search
            content_pack_priority: Content pack priority list

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def get_languages(self, language_type: Optional[str] = None) -> List[D5eLanguage]:
        """Get all available languages.

        Args:
            content_pack_priority: Content pack priority list

        Returns:
            List of languages
        """
        pass

    @abstractmethod
    def get_class_at_level(
        self,
        class_name: str,
        level: int,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Optional[ClassAtLevelInfo]:
        """Get class information at a specific level.

        Args:
            class_name: Name of the class
            level: Character level
            content_pack_priority: Content pack priority list

        Returns:
            Class information at the specified level
        """
        pass

    @abstractmethod
    def get_rule_section(self, section: str) -> List[str]:
        """Get a specific rule section.

        Args:
            section: Rule section name
            content_pack_priority: Content pack priority list

        Returns:
            Rule section content
        """
        pass

    @abstractmethod
    def get_starting_equipment(
        self, class_name: str, background_name: str
    ) -> StartingEquipmentInfo:
        """Get starting equipment for a class.

        Args:
            class_name: Name of the class
            content_pack_priority: Content pack priority list

        Returns:
            Starting equipment information
        """
        pass

    @abstractmethod
    def get_encounter_xp_budget(
        self, party_levels: List[int], difficulty: str = "medium"
    ) -> int:
        """Calculate encounter XP budget.

        Args:
            party_levels: List of party member levels
            difficulty: Encounter difficulty

        Returns:
            XP budget
        """
        pass

    @abstractmethod
    def get_content_statistics(self) -> Dict[str, int]:
        """Get statistics about available content.

        Returns:
            Dictionary with content counts by type
        """
        pass

    @abstractmethod
    def get_races(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eRace]:
        """Get all available races filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of races
        """
        pass

    @abstractmethod
    def get_classes(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eClass]:
        """Get all available classes filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of classes
        """
        pass

    @abstractmethod
    def get_backgrounds(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eBackground]:
        """Get all available backgrounds filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of backgrounds
        """
        pass

    @abstractmethod
    def get_alignments(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eAlignment]:
        """Get all available alignments filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of alignments
        """
        pass

    @abstractmethod
    def get_skills(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eSkill]:
        """Get all available skills filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of skills
        """
        pass

    @abstractmethod
    def get_ability_scores(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eAbilityScore]:
        """Get all available ability scores filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of ability scores
        """
        pass

    @abstractmethod
    def get_equipment_by_name(
        self, name: str, content_pack_priority: Optional[List[str]] = None
    ) -> Optional[Any]:
        """Get equipment by name.

        Args:
            name: Equipment name
            content_pack_priority: Optional content pack priority list

        Returns:
            Equipment data or None
        """
        pass

    @abstractmethod
    def get_class_by_name(
        self, name: str, content_pack_priority: Optional[List[str]] = None
    ) -> Optional[D5eClass]:
        """Get class by name.

        Args:
            name: Class name
            content_pack_priority: Optional content pack priority list

        Returns:
            Class data or None
        """
        pass


class IContentPackService(ABC):
    """Interface for content pack management operations."""

    @abstractmethod
    def get_content_pack(self, pack_id: str) -> Optional[D5eContentPack]:
        """Get a content pack by ID."""
        pass

    @abstractmethod
    def list_content_packs(self, active_only: bool = False) -> List[D5eContentPack]:
        """List all content packs."""
        pass

    @abstractmethod
    def create_content_pack(self, pack_data: ContentPackCreate) -> D5eContentPack:
        """Create a new content pack."""
        pass

    @abstractmethod
    def update_content_pack(
        self, pack_id: str, pack_data: ContentPackUpdate
    ) -> D5eContentPack:
        """Update an existing content pack."""
        pass

    @abstractmethod
    def activate_content_pack(self, pack_id: str) -> D5eContentPack:
        """Activate a content pack."""
        pass

    @abstractmethod
    def deactivate_content_pack(self, pack_id: str) -> D5eContentPack:
        """Deactivate a content pack."""
        pass

    @abstractmethod
    def delete_content_pack(self, pack_id: str) -> bool:
        """Delete a content pack and all its content."""
        pass

    @abstractmethod
    def get_content_pack_statistics(self, pack_id: str) -> ContentPackWithStats:
        """Get a content pack with statistics about its contents."""
        pass

    @abstractmethod
    def validate_content(
        self,
        content_type: str,
        content_data: Union[List[Dict[str, Any]], Dict[str, Any]],
    ) -> ContentUploadResult:
        """Validate content data against the appropriate schema.

        Returns:
            ContentUploadResult with validation details
        """
        pass

    @abstractmethod
    def upload_content(
        self,
        pack_id: str,
        content_type: str,
        content_data: Union[List[Dict[str, Any]], Dict[str, Any]],
    ) -> ContentUploadResult:
        """Upload and save content to a content pack."""
        pass

    @abstractmethod
    def get_supported_content_types(self) -> List[ContentTypeInfo]:
        """Get a list of supported content types for upload."""
        pass

    @abstractmethod
    def get_content_pack_items(
        self,
        pack_id: str,
        content_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get content items from a content pack.

        Returns:
            Dictionary with 'items' list and pagination info
        """
        pass


class IIndexingService(ABC):
    """Interface for content indexing operations."""

    @abstractmethod
    def index_content_pack(self, content_pack_id: str) -> Dict[str, int]:
        """Generate embeddings for all content in a content pack."""
        pass

    @abstractmethod
    def index_content_type(
        self, content_type: str, content_pack_id: Optional[str] = None
    ) -> int:
        """Generate embeddings for all content of a specific type."""
        pass

    @abstractmethod
    def update_entity_embedding(
        self, entity_class: Type[Any], entity_index: str
    ) -> bool:
        """Update the embedding for a single entity."""
        pass
