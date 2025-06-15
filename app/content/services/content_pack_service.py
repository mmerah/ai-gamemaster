"""Service for managing content packs.

This module provides high-level business logic for content pack management,
including validation, content upload processing, and coordination with other services.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, ValidationError

from app.content.content_types import CONTENT_TYPE_TO_MODEL, get_supported_content_types
from app.content.repositories.content_pack_repository import ContentPackRepository
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentPackWithStats,
    ContentUploadResult,
    D5eContentPack,
)
from app.exceptions import ContentPackNotFoundError
from app.exceptions import ValidationError as AppValidationError

logger = logging.getLogger(__name__)


class ContentPackService:
    """Service for content pack management.

    Provides high-level operations for creating, updating, and managing content packs,
    as well as uploading content to them.
    """

    def __init__(self, content_pack_repository: ContentPackRepository) -> None:
        """Initialize the service with repository.

        Args:
            content_pack_repository: Repository for content pack data access
        """
        self._repository = content_pack_repository

    def get_content_pack(self, pack_id: str) -> Optional[D5eContentPack]:
        """Get a content pack by ID.

        Args:
            pack_id: The content pack ID

        Returns:
            The content pack if found, None otherwise
        """
        return self._repository.get_by_id(pack_id)

    def list_content_packs(self, active_only: bool = False) -> List[D5eContentPack]:
        """List all content packs.

        Args:
            active_only: If True, only return active packs

        Returns:
            List of content packs
        """
        return self._repository.get_all(active_only=active_only)

    def create_content_pack(self, pack_data: ContentPackCreate) -> D5eContentPack:
        """Create a new content pack.

        Args:
            pack_data: Data for creating the content pack

        Returns:
            The created content pack
        """
        # Validate pack data
        self._validate_pack_data(pack_data)

        # Create the pack
        return self._repository.create(pack_data)

    def update_content_pack(
        self, pack_id: str, pack_data: ContentPackUpdate
    ) -> D5eContentPack:
        """Update an existing content pack.

        Args:
            pack_id: The content pack ID
            pack_data: Data for updating the content pack

        Returns:
            The updated content pack
        """
        # Get existing pack to ensure it exists
        existing = self._repository.get_by_id(pack_id)
        if not existing:
            raise ContentPackNotFoundError(pack_id)

        # Update the pack
        return self._repository.update(pack_id, pack_data)

    def activate_content_pack(self, pack_id: str) -> D5eContentPack:
        """Activate a content pack.

        Args:
            pack_id: The content pack ID

        Returns:
            The activated content pack
        """
        return self._repository.activate(pack_id)

    def deactivate_content_pack(self, pack_id: str) -> D5eContentPack:
        """Deactivate a content pack.

        Args:
            pack_id: The content pack ID

        Returns:
            The deactivated content pack
        """
        return self._repository.deactivate(pack_id)

    def delete_content_pack(self, pack_id: str) -> bool:
        """Delete a content pack and all its content.

        Args:
            pack_id: The content pack ID

        Returns:
            True if deleted successfully
        """
        return self._repository.delete(pack_id)

    def get_content_pack_statistics(self, pack_id: str) -> ContentPackWithStats:
        """Get a content pack with statistics about its contents.

        Args:
            pack_id: The content pack ID

        Returns:
            Content pack with statistics
        """
        return self._repository.get_statistics(pack_id)

    def validate_content(
        self,
        content_type: str,
        content_data: Union[List[Dict[str, Any]], Dict[str, Any]],
    ) -> ContentUploadResult:
        """Validate content data against the appropriate schema.

        Args:
            content_type: The type of content (e.g., 'spells', 'monsters')
            content_data: The content data to validate (single item or list)

        Returns:
            Validation result with details about successes and failures
        """
        # Get the appropriate model
        model_class = CONTENT_TYPE_TO_MODEL.get(content_type)
        if not model_class:
            raise AppValidationError(f"Unknown content type: {content_type}")

        # Ensure data is a list
        if isinstance(content_data, dict):
            items = [content_data]
        else:
            items = content_data

        # Validate each item
        result = ContentUploadResult(
            content_type=content_type,
            total_items=len(items),
            successful_items=0,
            failed_items=0,
        )

        for idx, item in enumerate(items):
            try:
                # Try to get a meaningful identifier
                item_id = item.get("index", item.get("name", f"item_{idx}"))

                # Validate against the model
                model_class(**item)
                result.successful_items += 1
            except ValidationError as e:
                result.failed_items += 1
                # Store validation errors
                result.validation_errors[str(item_id)] = str(e)
            except Exception as e:
                result.failed_items += 1
                result.validation_errors[str(item_id)] = f"Unexpected error: {str(e)}"

        return result

    def get_supported_content_types(self) -> List[str]:
        """Get a list of supported content types for upload.

        Returns:
            List of content type names
        """
        return get_supported_content_types()

    def _validate_pack_data(self, pack_data: ContentPackCreate) -> None:
        """Validate content pack creation data.

        Args:
            pack_data: The pack data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate name
        if not pack_data.name or not pack_data.name.strip():
            raise AppValidationError("Content pack name cannot be empty")

        if len(pack_data.name) > 100:
            raise AppValidationError("Content pack name cannot exceed 100 characters")

        # Validate version format (simple check)
        if not pack_data.version or not any(c.isdigit() for c in pack_data.version):
            raise AppValidationError("Version must contain at least one digit")

        # Validate author if provided
        if pack_data.author and len(pack_data.author) > 100:
            raise AppValidationError("Author name cannot exceed 100 characters")
