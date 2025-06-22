"""Tests for exception handling in API routes."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import (
    BadRequestError,
    DatabaseError,
    EntityNotFoundError,
    InternalServerError,
    NotFoundError,
    ValidationError,
    map_to_http_exception,
)


class TestRouteExceptionHandling:
    """Test exception handling in routes."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        from app.factory import create_fastapi_app
        from tests.conftest import get_test_settings

        settings = get_test_settings()
        app = create_fastapi_app(settings)
        return TestClient(app)

    @pytest.fixture
    def client_with_mock_repo(self) -> TestClient:
        """Create a test client with mocked repository."""
        from app.core.container import get_container
        from app.factory import create_fastapi_app
        from tests.conftest import get_test_settings

        settings = get_test_settings()
        app = create_fastapi_app(settings)

        # Get container and mock repository
        container = get_container()
        mock_repo = Mock()
        mock_repo.get.return_value = None  # Simulate not found
        # Properly mock the getter method
        container.get_character_template_repository = Mock(return_value=mock_repo)  # type: ignore[method-assign]

        return TestClient(app)

    @pytest.fixture
    def client_with_mock_service(self) -> TestClient:
        """Create a test client with mocked content service."""
        from app.core.container import get_container
        from app.factory import create_fastapi_app
        from tests.conftest import get_test_settings

        settings = get_test_settings()
        app = create_fastapi_app(settings)

        # Get container and mock service
        container = get_container()
        mock_service = Mock()
        mock_service.get_content_filtered.side_effect = DatabaseError(
            "Connection lost", details={"db": "test"}, code="DATABASE_ERROR"
        )
        container._content_service = mock_service

        return TestClient(app)

    def test_not_found_exception_handler(
        self, client_with_mock_repo: TestClient
    ) -> None:
        """Test 404 exception handler through existing API routes."""
        # Test with a non-existent character template
        response = client_with_mock_repo.get("/api/character_templates/non-existent-id")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    def test_d5e_route_database_error(
        self, client_with_mock_service: TestClient
    ) -> None:
        """Test D5E route handling DatabaseError."""
        response = client_with_mock_service.get("/api/d5e/content?type=ability-scores")
        assert response.status_code == 500

        data = response.json()
        assert data["error"] == "Connection lost"
        assert data["code"] == "DATABASE_ERROR"
        assert data["details"]["db"] == "test"

    def test_game_route_validation_error(self, client: TestClient) -> None:
        """Test game route handling ValidationError."""
        # No need to patch dependencies since they're not called for validation errors
        # Send invalid JSON data
        response = client.post(
            "/api/player_action",
            json={"invalid": "data"},  # Missing required fields
        )

        # The route should raise ValidationError which maps to 422
        assert response.status_code == 422


class TestExceptionMappingInRoutes:
    """Test exception mapping in route handlers."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a test FastAPI app."""
        from app.factory import create_fastapi_app
        from tests.conftest import get_test_settings

        settings = get_test_settings()
        return create_fastapi_app(settings)

    def test_entity_not_found_maps_to_404(self, app: FastAPI) -> None:
        """Test EntityNotFoundError maps to 404."""
        error = EntityNotFoundError("Spell", "fireball", "index")
        http_error = map_to_http_exception(error)

        assert http_error.status_code == 404
        error_dict = http_error.to_dict()
        assert error_dict["code"] == "NOT_FOUND"
        assert error_dict["details"]["resource_type"] == "Spell"

    def test_validation_error_maps_to_422(self, app: FastAPI) -> None:
        """Test ValidationError maps to 422."""
        error = ValidationError("Invalid level", field="level", value=-1)
        http_error = map_to_http_exception(error)

        assert http_error.status_code == 422
        error_dict = http_error.to_dict()
        assert error_dict["code"] == "UNPROCESSABLE_ENTITY"
        assert error_dict["details"]["validation_errors"]["field"] == "level"

    def test_database_error_maps_to_500(self, app: FastAPI) -> None:
        """Test DatabaseError maps to 500."""
        error = DatabaseError("Connection failed")
        http_error = map_to_http_exception(error)

        assert http_error.status_code == 500
        error_dict = http_error.to_dict()
        assert error_dict["code"] == "DATABASE_ERROR"

    def test_generic_exception_maps_to_500(self, app: FastAPI) -> None:
        """Test generic Exception maps to 500."""
        error = RuntimeError("Unexpected error")
        http_error = map_to_http_exception(error)

        assert http_error.status_code == 500
        error_dict = http_error.to_dict()
        assert error_dict["error"] == "Unexpected error"
