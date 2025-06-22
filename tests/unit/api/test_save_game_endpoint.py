"""Unit tests for the save game state endpoint."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import get_test_settings


class TestSaveGameEndpoint:
    """Test the save game state API endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        from app.factory import create_fastapi_app

        settings = get_test_settings()
        app = create_fastapi_app(settings)
        return TestClient(app)

    def test_save_game_state_success(self, client: TestClient) -> None:
        """Test successfully saving game state with default campaign."""
        response = client.post("/api/game_state/save")

        assert response.status_code == 200
        data = response.json()

        # Validate response using typed model
        from app.models.api import SaveGameResponse

        response_model = SaveGameResponse.model_validate(data)

        assert response_model.success is True
        assert response_model.message == "Game state saved successfully"
        # Default game state has no campaign
        assert response_model.campaign_id is None
        assert response_model.save_file == "campaign_None"

    def test_save_game_state_with_campaign(self, client: TestClient) -> None:
        """Test save game state after loading a campaign."""
        # First load a campaign to set campaign_id
        from app.core.container import get_container
        from app.models.campaign import CampaignTemplateModel
        from app.models.game_state import GameStateModel

        # Create a campaign template with required fields
        template = CampaignTemplateModel(
            id="test-campaign",
            name="Test Campaign",
            description="Test",
            version=1,
            campaign_goal="Test the save functionality",
            starting_location={
                "name": "Test Town",
                "description": "A place for testing",
            },
            opening_narrative="Welcome to the test campaign!",
        )

        # Manually save template and update game state
        container = get_container()
        container.get_campaign_template_repository().save(template)

        # Start the campaign
        response = client.post("/api/campaigns/test-campaign/start")
        assert response.status_code == 200

        # Now save the game state
        response = client.post("/api/game_state/save")
        assert response.status_code == 200
        data = response.json()

        # Validate response using typed model
        from app.models.api import SaveGameResponse

        response_model = SaveGameResponse.model_validate(data)

        assert response_model.success is True
        assert response_model.campaign_id is not None
        assert "test-campaign" in response_model.campaign_id

    def test_save_game_state_file_creation(self) -> None:
        """Test save game state creates actual file."""
        import tempfile

        from app.factory import create_fastapi_app

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create app with file repository
            settings = get_test_settings()
            settings.storage.game_state_repo_type = "file"
            settings.storage.saves_dir = tmpdir

            app = create_fastapi_app(settings)
            client = TestClient(app)

            response = client.post("/api/game_state/save")

            assert response.status_code == 200
            data = response.json()

            # Validate response using typed model
            from app.models.api import SaveGameResponse

            response_model = SaveGameResponse.model_validate(data)

            assert response_model.success is True
            assert response_model.message == "Game state saved successfully"

            # Check if file was created
            import os

            files = os.listdir(tmpdir)
            assert len(files) > 0  # At least one save file created
