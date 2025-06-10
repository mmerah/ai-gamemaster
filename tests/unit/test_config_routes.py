"""Unit tests for configuration routes."""

from unittest.mock import patch

import pytest
from flask import Flask
from flask.testing import FlaskClient


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client using the centralized app fixture."""
    return app.test_client()


def test_get_configuration(client: FlaskClient) -> None:
    """Test getting safe configuration values."""
    # Mock Flask app config
    mock_config = {
        "AI_PROVIDER": "openrouter",
        "AI_RESPONSE_PARSING_MODE": "flexible",
        "AI_TEMPERATURE": 0.7,
        "FLASK_DEBUG": False,
        "GAME_STATE_REPO_TYPE": "memory",
        "RAG_ENABLED": True,
        "TTS_PROVIDER": "kokoro",
    }

    with patch("app.routes.config_routes.current_app") as mock_app:
        mock_app.config = mock_config

        response = client.get("/api/config")

    assert response.status_code == 200
    data = response.get_json()

    # Check response structure
    assert "success" in data
    assert data["success"] is True
    assert "config" in data

    # Check some expected config values
    config = data["config"]
    assert config["AI_PROVIDER"] == "openrouter"
    assert config["AI_RESPONSE_PARSING_MODE"] == "flexible"
    assert config["AI_TEMPERATURE"] == 0.7
    assert config["FLASK_DEBUG"] is False
    assert config["GAME_STATE_REPO_TYPE"] == "memory"
    assert config["RAG_ENABLED"] is True
    assert config["TTS_PROVIDER"] == "kokoro"

    # Check computed values
    assert "VERSION" in config
    assert config["VERSION"] == "1.0.0"
    assert "ENVIRONMENT" in config
    assert config["ENVIRONMENT"] == "production"  # Because FLASK_DEBUG is False


def test_get_configuration_with_env_vars(client: FlaskClient) -> None:
    """Test getting configuration values from environment variables."""
    mock_config = {
        "FLASK_DEBUG": True  # This should make ENVIRONMENT = 'development'
    }

    # Mock environment variables
    mock_env = {"AI_PROVIDER": "llamacpp_http", "RAG_ENABLED": "true"}

    with patch("app.routes.config_routes.current_app") as mock_app, patch(
        "app.routes.config_routes.os.environ", mock_env
    ):
        mock_app.config = mock_config

        response = client.get("/api/config")

    assert response.status_code == 200
    data = response.get_json()

    config = data["config"]

    # Values from environment variables
    assert config["AI_PROVIDER"] == "llamacpp_http"
    assert config["RAG_ENABLED"] == "true"

    # Computed value based on FLASK_DEBUG=True
    assert config["ENVIRONMENT"] == "development"


def test_get_configuration_handles_path_objects(client: FlaskClient) -> None:
    """Test that Path objects are converted to strings."""
    from pathlib import Path

    mock_config = {
        "CAMPAIGNS_DIR": Path("saves/campaigns"),
        "CHARACTER_TEMPLATES_DIR": Path("saves/character_templates"),
    }

    with patch("app.routes.config_routes.current_app") as mock_app:
        mock_app.config = mock_config

        response = client.get("/api/config")

    assert response.status_code == 200
    data = response.get_json()

    config = data["config"]

    # Path objects should be converted to strings
    assert config["CAMPAIGNS_DIR"] == "saves/campaigns"
    assert config["CHARACTER_TEMPLATES_DIR"] == "saves/character_templates"
    assert isinstance(config["CAMPAIGNS_DIR"], str)
    assert isinstance(config["CHARACTER_TEMPLATES_DIR"], str)
