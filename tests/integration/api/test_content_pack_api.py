"""Integration tests for content pack API endpoints."""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentUploadResult,
    D5eContentPack,
)
from app.content.schemas.content_types import ContentTypeInfo
from app.content.services.content_pack_service import ContentPackService
from app.content.services.indexing_service import IndexingService
from app.exceptions import DuplicateEntityError
from app.models.api.requests import ContentUploadItem, ContentUploadRequest
from app.models.api.responses import ContentUploadResponse, SuccessResponse


@pytest.fixture
def mock_content_pack_service() -> Mock:
    """Create a mock content pack service."""
    return Mock(spec=ContentPackService)


@pytest.fixture
def mock_indexing_service() -> Mock:
    """Create a mock indexing service."""
    return Mock(spec=IndexingService)


@pytest.fixture
def sample_content_pack() -> D5eContentPack:
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


class TestContentPackAPI:
    """Test content pack API endpoints."""

    def test_get_all_content_packs(
        self,
        client: TestClient,
    ) -> None:
        """Test GET /api/content/packs endpoint."""
        # Execute
        response = client.get("/api/content/packs")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # At least the system pack should exist
        assert len(data) >= 1
        # Check structure of first pack
        if data:
            pack = data[0]
            assert "id" in pack
            assert "name" in pack
            assert "version" in pack
            # Store the actual pack ID for use in other tests
            self.existing_pack_id = pack["id"]

    def test_get_active_content_packs_only(
        self,
        client: TestClient,
    ) -> None:
        """Test GET /api/content/packs?active_only=true."""
        # Execute
        response = client.get("/api/content/packs?active_only=true")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned packs should be active
        for pack in data:
            assert pack["is_active"] is True

    def test_get_content_pack_by_id(
        self,
        client: TestClient,
    ) -> None:
        """Test GET /api/content/packs/{id} endpoint."""
        # Use the system pack ID which should always exist
        pack_id = "dnd_5e_srd"

        # Execute
        response = client.get(f"/api/content/packs/{pack_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()

        # Validate response using typed model
        pack_model = D5eContentPack.model_validate(data)
        assert pack_model.id == pack_id
        assert pack_model.name is not None
        assert pack_model.version is not None
        assert pack_model.is_active is not None

    def test_get_content_pack_not_found(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
    ) -> None:
        """Test GET /api/content/packs/{id} when pack not found."""
        # Setup
        mock_content_pack_service.get_content_pack.return_value = None

        # Override dependency
        from app.api.dependencies_fastapi import get_content_pack_service

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )

        # Execute
        response = client.get("/api/content/packs/non-existent")

        # Verify
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_get_content_pack_statistics(
        self,
        client: TestClient,
    ) -> None:
        """Test GET /api/content/packs/{id}/statistics endpoint."""
        # Use the system pack ID which should always exist
        pack_id = "dnd_5e_srd"

        # Execute
        response = client.get(f"/api/content/packs/{pack_id}/statistics")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == pack_id
        assert "statistics" in data
        assert isinstance(data["statistics"], dict)
        # System pack should have content
        assert sum(data["statistics"].values()) > 0

    def test_create_content_pack(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs endpoint."""
        # Setup
        mock_content_pack_service.create_content_pack.return_value = sample_content_pack

        # Override dependency
        from app.api.dependencies_fastapi import get_content_pack_service

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )

        # Use typed model
        pack_create = ContentPackCreate(
            id="test-pack",
            name="Test Pack",
            description="A test content pack",
            version="1.0.0",
            author="Test Author",
        )

        # Execute
        response = client.post(
            "/api/content/packs",
            json=pack_create.model_dump(mode="json"),
        )

        # Verify
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-pack"

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_create_duplicate_content_pack(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
    ) -> None:
        """Test creating a duplicate content pack."""
        # Setup
        mock_content_pack_service.create_content_pack.side_effect = (
            DuplicateEntityError(entity_type="ContentPack", identifier="test-pack")
        )

        # Override dependency
        from app.api.dependencies_fastapi import get_content_pack_service

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )

        # Use typed model (intentionally missing description to test validation)
        pack_create = ContentPackCreate(
            id="test-pack",
            name="Test Pack",
            description="Duplicate test pack",  # Description is required
            version="1.0.0",
        )

        # Execute
        response = client.post(
            "/api/content/packs",
            json=pack_create.model_dump(mode="json"),
        )

        # Verify
        assert response.status_code == 409
        data = response.json()
        assert "error" in data

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_update_content_pack(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test PUT /api/content/packs/{id} endpoint."""
        # Setup
        from app.api.dependencies_fastapi import get_content_pack_service

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )

        updated_pack = sample_content_pack.model_copy()
        updated_pack.name = "Updated Pack"
        mock_content_pack_service.update_content_pack.return_value = updated_pack

        # Use typed model for update request
        update_request = ContentPackUpdate(name="Updated Pack")

        # Execute
        response = client.put(
            "/api/content/packs/test-pack",
            json=update_request.model_dump(mode="json", exclude_unset=True),
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Pack"

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_activate_content_pack(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs/{id}/activate endpoint."""
        # Setup
        from app.api.dependencies_fastapi import get_content_pack_service

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )
        mock_content_pack_service.activate_content_pack.return_value = (
            sample_content_pack
        )

        # Execute
        response = client.post("/api/content/packs/test-pack/activate")

        # Verify
        assert response.status_code == 200
        data = response.json()

        # Validate response using typed model
        response_model = SuccessResponse.model_validate(data)
        assert response_model.success is True
        assert "activated successfully" in response_model.message

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_deactivate_content_pack(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs/{id}/deactivate endpoint."""
        # Setup
        from app.api.dependencies_fastapi import get_content_pack_service

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )

        deactivated_pack = sample_content_pack.model_copy()
        deactivated_pack.is_active = False
        mock_content_pack_service.deactivate_content_pack.return_value = (
            deactivated_pack
        )

        # Execute
        response = client.post("/api/content/packs/test-pack/deactivate")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deactivated successfully" in data["message"]

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_delete_content_pack(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
    ) -> None:
        """Test DELETE /api/content/packs/{id} endpoint."""
        # Setup
        from app.api.dependencies_fastapi import get_content_pack_service

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )
        mock_content_pack_service.delete_content_pack.return_value = True

        # Execute
        response = client.delete("/api/content/packs/test-pack")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_upload_content(
        self,
        client: TestClient,
        app: FastAPI,
        mock_content_pack_service: Mock,
        mock_indexing_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs/{id}/upload/{type} endpoint."""
        # Setup
        from app.api.dependencies_fastapi import (
            get_content_pack_service,
            get_indexing_service,
        )

        app.dependency_overrides[get_content_pack_service] = (
            lambda: mock_content_pack_service
        )
        app.dependency_overrides[get_indexing_service] = lambda: mock_indexing_service

        mock_content_pack_service.get_content_pack.return_value = sample_content_pack
        mock_content_pack_service.get_supported_content_types.return_value = [
            ContentTypeInfo(
                type_id="spells", display_name="Spells", description="D&D 5e Spells"
            ),
            ContentTypeInfo(
                type_id="monsters",
                display_name="Monsters",
                description="D&D 5e Monsters",
            ),
            ContentTypeInfo(
                type_id="equipment",
                display_name="Equipment",
                description="D&D 5e Equipment",
            ),
            ContentTypeInfo(
                type_id="classes", display_name="Classes", description="D&D 5e Classes"
            ),
        ]

        upload_result = ContentUploadResult(
            content_type="spells",
            total_items=1,
            successful_items=1,
            failed_items=0,
            validation_errors={},
            warnings=["Successfully saved 1 items to the database"],
        )
        mock_content_pack_service.upload_content.return_value = upload_result
        mock_indexing_service.index_content_pack.return_value = {"spells": 1}

        # Create spell data using typed models
        spell_item = ContentUploadItem(
            id="test-spell",
            name="Test Spell",
            description="Test spell description",
            data={
                "index": "test-spell",
                "name": "Test Spell",
                "url": "/api/spells/test-spell",
                "level": 1,
                "school": {
                    "index": "evocation",
                    "name": "Evocation",
                    "url": "/api/magic-schools/evocation",
                },
                "casting_time": "1 action",
                "range": "30 feet",
                "components": ["V", "S"],
                "duration": "Instantaneous",
                "ritual": False,
                "concentration": False,
                "classes": [
                    {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
                ],
                "desc": ["Test spell description"],
            },
        )

        # Create upload request with typed model
        upload_request = ContentUploadRequest(items=spell_item)

        # Execute
        response = client.post(
            "/api/content/packs/test-pack/upload/spells",
            json=upload_request.model_dump(mode="json"),
        )

        # Verify
        assert response.status_code == 200
        data = response.json()

        # Validate response using typed model
        response_model = ContentUploadResponse.model_validate(data)
        assert response_model.success is True
        assert response_model.uploaded_count == 1
        assert response_model.failed_count == 0

        # Clean up dependency override
        app.dependency_overrides.clear()

    def test_get_supported_content_types(
        self,
        client: TestClient,
    ) -> None:
        """Test GET /api/content/supported-types endpoint."""
        # Execute
        response = client.get("/api/content/supported-types")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check structure of ContentTypeInfo objects
        for content_type in data:
            assert "type_id" in content_type
            assert "display_name" in content_type
        # Check for common types
        type_ids = [ct["type_id"] for ct in data]
        assert "spells" in type_ids
        assert "monsters" in type_ids
