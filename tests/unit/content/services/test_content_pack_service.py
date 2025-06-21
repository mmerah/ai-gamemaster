"""Tests for the ContentPackService."""

from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from app.content.repositories.content_pack_repository import ContentPackRepository
from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentPackWithStats,
    ContentUploadResult,
    D5eContentPack,
)
from app.content.services.content_pack_service import ContentPackService
from app.exceptions import (
    ContentPackNotFoundError,
    DatabaseError,
    DuplicateEntityError,
    ValidationError,
)


class TestContentPackService:
    """Test the ContentPackService class."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create a mock ContentPackRepository."""
        return Mock(spec=ContentPackRepository)

    @pytest.fixture
    def mock_repository_hub(self) -> Mock:
        """Create a mock D5eDbRepositoryHub."""
        return Mock(spec=D5eDbRepositoryHub)

    @pytest.fixture
    def service(
        self, mock_repository: Mock, mock_repository_hub: Mock
    ) -> ContentPackService:
        """Create a ContentPackService instance."""
        return ContentPackService(mock_repository, mock_repository_hub)

    @pytest.fixture
    def sample_content_pack(self) -> D5eContentPack:
        """Create a sample content pack."""
        return D5eContentPack(
            id="test-pack",
            name="Test Pack",
            description="A test content pack",
            version="1.0.0",
            author="Test Author",
            is_active=True,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

    def test_create_content_pack_success(
        self,
        service: ContentPackService,
        mock_repository: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test creating a content pack successfully."""
        # Setup
        create_data = ContentPackCreate(
            id="test-pack",
            name="Test Pack",
            description="A test content pack",
            version="1.0.0",
            author="Test Author",
        )
        mock_repository.create.return_value = sample_content_pack

        # Execute
        result = service.create_content_pack(create_data)

        # Verify
        assert result.id == "test-pack"
        mock_repository.create.assert_called_once_with(create_data)

    def test_create_content_pack_duplicate(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test creating a duplicate content pack."""
        # Setup
        create_data = ContentPackCreate(
            id="test-pack",
            name="Test Pack",
            version="1.0.0",
        )
        mock_repository.create.side_effect = DuplicateEntityError(
            entity_type="ContentPack", identifier="test-pack"
        )

        # Execute & Verify
        with pytest.raises(DuplicateEntityError):
            service.create_content_pack(create_data)

    def test_update_content_pack_success(
        self,
        service: ContentPackService,
        mock_repository: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test updating a content pack successfully."""
        # Setup
        update_data = ContentPackUpdate(
            name="Updated Pack",
            description="Updated description",
        )
        updated_pack = sample_content_pack.model_copy()
        updated_pack.name = "Updated Pack"
        updated_pack.description = "Updated description"
        mock_repository.update.return_value = updated_pack

        # Execute
        result = service.update_content_pack("test-pack", update_data)

        # Verify
        assert result.name == "Updated Pack"
        mock_repository.update.assert_called_once_with("test-pack", update_data)

    def test_update_content_pack_not_found(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test updating a non-existent content pack."""
        # Setup
        update_data = ContentPackUpdate(name="Updated Pack")
        mock_repository.update.side_effect = ContentPackNotFoundError(
            "Content pack not found"
        )

        # Execute & Verify
        with pytest.raises(ContentPackNotFoundError):
            service.update_content_pack("non-existent", update_data)

    def test_delete_content_pack_success(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test deleting a content pack successfully."""
        # Setup
        mock_repository.delete.return_value = True

        # Execute
        result = service.delete_content_pack("test-pack")

        # Verify
        assert result is True
        mock_repository.delete.assert_called_once_with("test-pack")

    def test_activate_content_pack(
        self,
        service: ContentPackService,
        mock_repository: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test activating a content pack."""
        # Setup
        inactive_pack = sample_content_pack.model_copy()
        inactive_pack.is_active = False
        activated_pack = sample_content_pack.model_copy()
        activated_pack.is_active = True

        mock_repository.activate.return_value = activated_pack

        # Execute
        result = service.activate_content_pack("test-pack")

        # Verify
        assert result.is_active is True
        mock_repository.activate.assert_called_once_with("test-pack")

    def test_deactivate_content_pack(
        self,
        service: ContentPackService,
        mock_repository: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test deactivating a content pack."""
        # Setup
        active_pack = sample_content_pack.model_copy()
        active_pack.is_active = True
        deactivated_pack = sample_content_pack.model_copy()
        deactivated_pack.is_active = False

        mock_repository.deactivate.return_value = deactivated_pack

        # Execute
        result = service.deactivate_content_pack("test-pack")

        # Verify
        assert result.is_active is False
        mock_repository.deactivate.assert_called_once_with("test-pack")

    def test_get_content_pack_statistics(
        self,
        service: ContentPackService,
        mock_repository: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test getting content pack statistics."""
        # Setup
        stats: Dict[str, int] = {
            "spells": 10,
            "monsters": 5,
            "equipment": 20,
            "classes": 2,
        }
        pack_with_stats = ContentPackWithStats(
            **sample_content_pack.model_dump(), statistics=stats
        )
        mock_repository.get_statistics.return_value = pack_with_stats

        # Execute
        result = service.get_content_pack_statistics("test-pack")

        # Verify
        assert isinstance(result, ContentPackWithStats)
        assert result.id == "test-pack"
        assert result.statistics == stats

    def test_get_content_pack_statistics_not_found(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test getting statistics for non-existent pack."""
        # Setup
        mock_repository.get_statistics.side_effect = ContentPackNotFoundError(
            "non-existent"
        )

        # Execute & Verify
        with pytest.raises(ContentPackNotFoundError):
            service.get_content_pack_statistics("non-existent")

    def test_validate_content_single_item(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test validating a single content item."""
        # Setup
        spell_data = {
            "index": "fireball",
            "name": "Fireball",
            "url": "/api/spells/fireball",
            "level": 3,
            "school": {
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
            "casting_time": "1 action",
            "range": "150 feet",
            "components": ["V", "S", "M"],
            "duration": "Instantaneous",
            "ritual": False,
            "concentration": False,
            "classes": [
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
            ],
            "desc": ["A bright streak flashes..."],
        }

        # Execute
        result = service.validate_content("spells", spell_data)

        # Verify
        assert isinstance(result, ContentUploadResult)
        assert result.content_type == "spells"
        assert result.total_items == 1
        assert result.successful_items == 1
        assert result.failed_items == 0

    def test_validate_content_multiple_items(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test validating multiple content items."""
        # Setup
        spell_data: List[Dict[str, Any]] = [
            {
                "index": "fireball",
                "name": "Fireball",
                "url": "/api/spells/fireball",
                "level": 3,
                "school": {
                    "index": "evocation",
                    "name": "Evocation",
                    "url": "/api/magic-schools/evocation",
                },
                "casting_time": "1 action",
                "range": "150 feet",
                "components": ["V", "S", "M"],
                "duration": "Instantaneous",
                "ritual": False,
                "concentration": False,
                "classes": [
                    {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
                ],
                "desc": ["A bright streak flashes..."],
            },
            {
                "index": "invalid-spell",
                "name": "Invalid Spell",
                # Missing required fields
            },
        ]

        # Execute
        result = service.validate_content("spells", spell_data)

        # Verify
        assert result.total_items == 2
        assert result.successful_items == 1
        assert result.failed_items == 1
        assert len(result.validation_errors) == 1

    def test_validate_content_unsupported_type(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test validating content with unsupported type."""
        # Execute & Verify
        with pytest.raises(ValidationError) as exc_info:
            service.validate_content("unsupported_type", {})
        assert "Unknown content type" in str(exc_info.value)

    def test_get_supported_content_types(
        self,
        service: ContentPackService,
        mock_repository: Mock,
    ) -> None:
        """Test getting supported content types."""
        # Execute
        result = service.get_supported_content_types()

        # Verify
        assert isinstance(result, list)
        assert len(result) == 25  # All supported types

        # Check that all items are ContentTypeInfo objects
        type_ids = [item.type_id for item in result]
        assert "spells" in type_ids
        assert "monsters" in type_ids
        assert "equipment" in type_ids
        assert "classes" in type_ids

        # Verify structure of first item
        first_item = result[0]
        assert hasattr(first_item, "type_id")
        assert hasattr(first_item, "display_name")
        assert hasattr(first_item, "description")

    def test_list_content_packs_all(
        self,
        service: ContentPackService,
        mock_repository: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test listing all content packs."""
        # Setup
        mock_repository.get_all.return_value = [sample_content_pack]

        # Execute
        result = service.list_content_packs()

        # Verify
        assert len(result) == 1
        assert result[0].id == "test-pack"
        mock_repository.get_all.assert_called_once_with(active_only=False)

    def test_list_content_packs_active_only(
        self,
        service: ContentPackService,
        mock_repository: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test listing only active content packs."""
        # Setup
        mock_repository.get_all.return_value = [sample_content_pack]

        # Execute
        result = service.list_content_packs(active_only=True)

        # Verify
        assert len(result) == 1
        mock_repository.get_all.assert_called_once_with(active_only=True)
