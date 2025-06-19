"""Unit tests for the save game state endpoint."""

import json
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from flask.testing import FlaskClient


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create a test client."""
    from app import create_app
    from tests.test_config_helper import create_test_service_config

    config = create_test_service_config()
    app = create_app(config)

    with app.test_client() as client:
        with app.app_context():
            yield client


class TestSaveGameEndpoint:
    """Test the save game state API endpoint."""

    def test_save_game_state_success(self, client: FlaskClient) -> None:
        """Test successfully saving game state."""
        # Mock game state
        mock_game_state = Mock()
        mock_game_state.campaign_id = "test_campaign_123"

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_repo = Mock()
            mock_repo.get_game_state.return_value = mock_game_state
            mock_repo.save_game_state.return_value = None  # No exceptions

            mock_container.get_game_state_repository.return_value = mock_repo
            mock_get_container.return_value = mock_container

            response = client.post("/api/game_state/save")

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data["success"] is True
            assert data["message"] == "Game state saved successfully"
            assert data["campaign_id"] == "test_campaign_123"

            # Verify save was called with the game state
            mock_repo.save_game_state.assert_called_once_with(mock_game_state)

    def test_save_game_state_no_campaign(self, client: FlaskClient) -> None:
        """Test saving game state when no campaign is active."""
        # Mock game state with no campaign
        mock_game_state = Mock()
        mock_game_state.campaign_id = None

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_repo = Mock()
            mock_repo.get_game_state.return_value = mock_game_state
            mock_repo.save_game_state.return_value = None

            mock_container.get_game_state_repository.return_value = mock_repo
            mock_get_container.return_value = mock_container

            response = client.post("/api/game_state/save")

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data["success"] is True
            assert data["campaign_id"] is None

            # Save should still be called
            mock_repo.save_game_state.assert_called_once()

    def test_save_game_state_repository_error(self, client: FlaskClient) -> None:
        """Test save game state when repository throws an error."""
        mock_game_state = Mock()
        mock_game_state.campaign_id = "test_campaign"

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_repo = Mock()
            mock_repo.get_game_state.return_value = mock_game_state
            mock_repo.save_game_state.side_effect = Exception("Failed to write file")

            mock_container.get_game_state_repository.return_value = mock_repo
            mock_get_container.return_value = mock_container

            response = client.post("/api/game_state/save")

            assert response.status_code == 500
            data = json.loads(response.data)

            assert "error" in data
            assert "Failed to write file" in data["error"]

    def test_save_game_state_file_repository(self, client: FlaskClient) -> None:
        """Test save game state with file repository."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create app with file repository
            from app import create_app
            from tests.test_config_helper import create_test_service_config

            config = create_test_service_config(
                GAME_STATE_REPO_TYPE="file",
                SAVES_DIR=tmpdir,  # Use SAVES_DIR as the base for the repository
            )
            app = create_app(config)

            with app.test_client() as file_client:
                with app.app_context():
                    response = file_client.post("/api/game_state/save")

                    assert response.status_code == 200
                    data = json.loads(response.data)

                    assert data["success"] is True
                    assert data["message"] == "Game state saved successfully"

                    # The file creation depends on the implementation
                    # Just verify the endpoint executed successfully
