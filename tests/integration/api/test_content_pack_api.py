"""Integration tests for content pack API endpoints."""

import json
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.api.content_routes import content_bp
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentPackWithStats,
    ContentUploadResult,
    D5eContentPack,
)
from app.content.services.content_pack_service import ContentPackService
from app.content.services.indexing_service import IndexingService
from app.core.container import ServiceContainer
from app.exceptions import (
    ContentPackNotFoundError,
    DuplicateEntityError,
    ValidationError,
)


@pytest.fixture
def app() -> Flask:
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.register_blueprint(content_bp)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def mock_container() -> Mock:
    """Create a mock service container."""
    return Mock(spec=ServiceContainer)


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

    @patch("app.api.content_routes.get_container")
    def test_get_all_content_packs(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test GET /api/content/packs endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.list_content_packs.return_value = [
            sample_content_pack
        ]

        # Execute
        response = client.get("/api/content/packs")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "packs" in data
        assert len(data["packs"]) == 1
        assert data["packs"][0]["id"] == "test-pack"

    @patch("app.api.content_routes.get_container")
    def test_get_active_content_packs_only(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test GET /api/content/packs?active_only=true."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.list_content_packs.return_value = [
            sample_content_pack
        ]

        # Execute
        response = client.get("/api/content/packs?active_only=true")

        # Verify
        assert response.status_code == 200
        mock_content_pack_service.list_content_packs.assert_called_once_with(
            active_only=True
        )

    @patch("app.api.content_routes.get_container")
    def test_get_content_pack_by_id(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test GET /api/content/packs/{id} endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.get_content_pack.return_value = sample_content_pack

        # Execute
        response = client.get("/api/content/packs/test-pack")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == "test-pack"
        assert data["name"] == "Test Pack"

    @patch("app.api.content_routes.get_container")
    def test_get_content_pack_not_found(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
    ) -> None:
        """Test GET /api/content/packs/{id} when pack not found."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.get_content_pack.return_value = None

        # Execute
        response = client.get("/api/content/packs/non-existent")

        # Verify
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    @patch("app.api.content_routes.get_container")
    def test_get_content_pack_statistics(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test GET /api/content/packs/{id}/statistics endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service

        stats = {"spells": 10, "monsters": 5}
        pack_with_stats = ContentPackWithStats(
            **sample_content_pack.model_dump(),
            statistics=stats,
        )
        mock_content_pack_service.get_content_pack_statistics.return_value = (
            pack_with_stats
        )

        # Execute
        response = client.get("/api/content/packs/test-pack/statistics")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["statistics"]["spells"] == 10
        assert data["statistics"]["monsters"] == 5

    @patch("app.api.content_routes.get_container")
    def test_create_content_pack(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.create_content_pack.return_value = sample_content_pack

        request_data = {
            "id": "test-pack",
            "name": "Test Pack",
            "description": "A test content pack",
            "version": "1.0.0",
            "author": "Test Author",
        }

        # Execute
        response = client.post(
            "/api/content/packs",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["id"] == "test-pack"

    @patch("app.api.content_routes.get_container")
    def test_create_duplicate_content_pack(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
    ) -> None:
        """Test creating a duplicate content pack."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.create_content_pack.side_effect = (
            DuplicateEntityError(entity_type="ContentPack", identifier="test-pack")
        )

        request_data = {"id": "test-pack", "name": "Test Pack", "version": "1.0.0"}

        # Execute
        response = client.post(
            "/api/content/packs",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 409
        data = json.loads(response.data)
        assert "error" in data

    @patch("app.api.content_routes.get_container")
    def test_update_content_pack(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test PUT /api/content/packs/{id} endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service

        updated_pack = sample_content_pack.model_copy()
        updated_pack.name = "Updated Pack"
        mock_content_pack_service.update_content_pack.return_value = updated_pack

        request_data = {"name": "Updated Pack"}

        # Execute
        response = client.put(
            "/api/content/packs/test-pack",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Pack"

    @patch("app.api.content_routes.get_container")
    def test_activate_content_pack(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs/{id}/activate endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.activate_content_pack.return_value = (
            sample_content_pack
        )

        # Execute
        response = client.post("/api/content/packs/test-pack/activate")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["is_active"] is True

    @patch("app.api.content_routes.get_container")
    def test_deactivate_content_pack(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs/{id}/deactivate endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service

        deactivated_pack = sample_content_pack.model_copy()
        deactivated_pack.is_active = False
        mock_content_pack_service.deactivate_content_pack.return_value = (
            deactivated_pack
        )

        # Execute
        response = client.post("/api/content/packs/test-pack/deactivate")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["is_active"] is False

    @patch("app.api.content_routes.get_container")
    def test_delete_content_pack(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
    ) -> None:
        """Test DELETE /api/content/packs/{id} endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.delete_content_pack.return_value = True

        # Execute
        response = client.delete("/api/content/packs/test-pack")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data

    @patch("app.api.content_routes.get_container")
    def test_upload_content(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
        mock_indexing_service: Mock,
        sample_content_pack: D5eContentPack,
    ) -> None:
        """Test POST /api/content/packs/{id}/upload/{type} endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_container.get_indexing_service.return_value = mock_indexing_service

        mock_content_pack_service.get_content_pack.return_value = sample_content_pack
        mock_content_pack_service.get_supported_content_types.return_value = [
            "spells",
            "monsters",
            "equipment",
            "classes",
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

        spell_data = {
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
        }

        # Execute
        response = client.post(
            "/api/content/packs/test-pack/upload/spells",
            data=json.dumps(spell_data),
            content_type="application/json",
        )

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["total_items"] == 1
        assert data["successful_items"] == 1
        assert data["failed_items"] == 0

    @patch("app.api.content_routes.get_container")
    def test_get_supported_content_types(
        self,
        mock_get_container: Mock,
        client: FlaskClient,
        mock_container: Mock,
        mock_content_pack_service: Mock,
    ) -> None:
        """Test GET /api/content/supported-types endpoint."""
        # Setup
        mock_get_container.return_value = mock_container
        mock_container.get_content_pack_service.return_value = mock_content_pack_service
        mock_content_pack_service.get_supported_content_types.return_value = [
            "spells",
            "monsters",
            "equipment",
        ]

        # Execute
        response = client.get("/api/content/supported-types")

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "types" in data
        assert "spells" in data["types"]
        assert "monsters" in data["types"]
