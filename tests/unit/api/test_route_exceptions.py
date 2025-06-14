"""Tests for exception handling in API routes."""

from unittest.mock import Mock, patch

import pytest
from flask import Flask, Response
from flask.testing import FlaskClient

from app.api import initialize_routes
from app.exceptions import (
    BadRequestError,
    DatabaseError,
    EntityNotFoundError,
    InternalServerError,
    NotFoundError,
    ValidationError,
)


class TestRouteExceptionHandling:
    """Test exception handling in routes."""

    @pytest.fixture
    def app(self) -> Flask:
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True

        # Initialize routes with error handlers
        initialize_routes(app)

        return app

    @pytest.fixture
    def client(self, app: Flask) -> FlaskClient:
        """Create a test client."""
        return app.test_client()

    def test_global_http_exception_handler(
        self, app: Flask, client: FlaskClient
    ) -> None:
        """Test global HTTPException handler."""

        # Create a test route directly on the app to test error handling
        @app.route("/test-http-error")
        def test_http_error() -> Response:
            raise NotFoundError("Test resource not found", resource_type="TestResource")

        response = client.get("/test-http-error")
        assert response.status_code == 404

        data = response.get_json()
        assert data["error"] == "Test resource not found"
        assert data["code"] == "NOT_FOUND"
        assert data["details"]["resource_type"] == "TestResource"

    def test_global_generic_exception_handler(
        self, app: Flask, client: FlaskClient
    ) -> None:
        """Test global generic exception handler."""

        # Create a test route directly on the app to test error handling
        @app.route("/test-generic-error")
        def test_generic_error() -> Response:
            raise ValueError("Unexpected error")

        response = client.get("/test-generic-error")
        assert response.status_code == 500

        data = response.get_json()
        assert data["error"] == "Unexpected error"
        assert data["code"] == "INTERNAL_SERVER_ERROR"

    def test_d5e_route_entity_not_found(self, client: FlaskClient) -> None:
        """Test D5E route handling EntityNotFoundError."""
        with patch("app.api.d5e_routes.get_d5e_service") as mock_get_service:
            mock_service = Mock()
            mock_service._hub.ability_scores.get_by_index.return_value = None
            mock_get_service.return_value = mock_service

            response = client.get("/api/d5e/ability-scores/invalid")
            assert response.status_code == 404

            data = response.get_json()
            assert "Ability score 'invalid' not found" in data["error"]
            assert data["code"] == "NOT_FOUND"

    def test_d5e_route_database_error(self, client: FlaskClient) -> None:
        """Test D5E route handling DatabaseError."""
        with patch("app.api.d5e_routes.get_d5e_service") as mock_get_service:
            mock_service = Mock()
            mock_service._hub.ability_scores.list_all.side_effect = DatabaseError(
                "Connection lost", details={"db": "test"}
            )
            mock_get_service.return_value = mock_service

            response = client.get("/api/d5e/ability-scores")
            assert response.status_code == 500

            data = response.get_json()
            assert data["error"] == "Connection lost"
            assert data["code"] == "DATABASE_ERROR"
            assert data["details"]["db"] == "test"

    def test_game_route_validation_error(self, client: FlaskClient) -> None:
        """Test game route handling ValidationError."""
        with patch("app.api.game_routes.get_container"):
            # Send invalid JSON data
            response = client.post(
                "/api/player_action",
                json={"invalid": "data"},  # Missing required fields
            )

            # The route should raise ValidationError which maps to 422
            assert response.status_code == 422

    def test_game_route_internal_error(self, client: FlaskClient) -> None:
        """Test game route handling internal errors."""
        with patch("app.api.game_routes.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_game_orchestrator.side_effect = Exception(
                "Service initialization failed"
            )
            mock_get_container.return_value = mock_container

            response = client.get("/api/game_state")
            assert response.status_code == 500

            data = response.get_json()
            assert data["error"] == "Failed to get game state"
            assert data["code"] == "INTERNAL_SERVER_ERROR"


class TestExceptionMappingInRoutes:
    """Test exception mapping in route handlers."""

    @pytest.fixture
    def app(self) -> Flask:
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    def test_entity_not_found_maps_to_404(self, app: Flask) -> None:
        """Test EntityNotFoundError maps to 404."""
        from app.api.d5e_routes import _handle_service_error

        with app.app_context():
            error = EntityNotFoundError("Spell", "fireball", "index")
            response, status_code = _handle_service_error("test operation", error)

            assert status_code == 404
            data = response.get_json()
            assert data["code"] == "NOT_FOUND"
            assert data["details"]["resource_type"] == "Spell"

    def test_validation_error_maps_to_422(self, app: Flask) -> None:
        """Test ValidationError maps to 422."""
        from app.api.d5e_routes import _handle_service_error

        with app.app_context():
            error = ValidationError("Invalid level", field="level", value=-1)
            response, status_code = _handle_service_error("test operation", error)

            assert status_code == 422
            data = response.get_json()
            assert data["code"] == "UNPROCESSABLE_ENTITY"
            assert data["details"]["validation_errors"]["field"] == "level"

    def test_database_error_maps_to_500(self, app: Flask) -> None:
        """Test DatabaseError maps to 500."""
        from app.api.d5e_routes import _handle_service_error

        with app.app_context():
            error = DatabaseError("Connection failed")
            response, status_code = _handle_service_error("test operation", error)

            assert status_code == 500
            data = response.get_json()
            assert data["code"] == "DATABASE_ERROR"

    def test_generic_exception_maps_to_500(self, app: Flask) -> None:
        """Test generic Exception maps to 500."""
        from app.api.d5e_routes import _handle_service_error

        with app.app_context():
            error = RuntimeError("Unexpected error")
            response, status_code = _handle_service_error("test operation", error)

            assert status_code == 500
            data = response.get_json()
            assert data["error"] == "Unexpected error"
