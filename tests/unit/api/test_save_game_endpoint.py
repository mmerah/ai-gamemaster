"""Unit tests for the save game state endpoint."""

import tempfile
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.api.responses import SaveGameResponse
from app.models.campaign import CampaignInstanceModel, CampaignTemplateModel
from app.models.character.template import CharacterTemplateModel
from app.models.utils import BaseStatsModel, ProficienciesModel
from tests.conftest import get_test_settings


class TestSaveGameEndpoint:
    """Test the save game state API endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        from app import create_app

        settings = get_test_settings()
        app = create_app(settings)
        return TestClient(app)

    def test_save_game_state_success(self, client: TestClient) -> None:
        """Test successfully saving game state with default campaign."""
        response = client.post("/api/game_state/save")

        assert response.status_code == 200
        data = response.json()
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

        # Create a campaign template with required fields
        template = CampaignTemplateModel(
            id="test-campaign-template",
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

        # Create a test character template
        char_template = CharacterTemplateModel(
            id="test-char",
            name="Test Hero",
            race="human",
            char_class="fighter",
            background="soldier",
            level=1,
            alignment="neutral",
            base_stats=BaseStatsModel(STR=16, DEX=14, CON=14, INT=10, WIS=12, CHA=10),
            proficiencies=ProficienciesModel(
                skills=["athletics", "intimidation"],
                armor=["all"],
                weapons=["simple", "martial"],
                tools=[],
                saving_throws=["STR", "CON"],
            ),
        )

        # Create a campaign instance with the character
        instance = CampaignInstanceModel(
            id="test-campaign-instance",
            name="Test Adventure",
            template_id="test-campaign-template",
            character_ids=["test-char"],
            current_location="Test Town",
            event_log_path="events/test-campaign-instance.json",
        )

        # Manually save template, character, and instance
        container = get_container()
        container.get_campaign_template_repository().save(template)
        container.get_character_template_repository().save(char_template)
        container.get_campaign_instance_repository().save(instance)

        # Start the campaign instance (not the template)
        response = client.post("/api/campaigns/test-campaign-instance/start")
        assert response.status_code == 200

        # Now save the game state
        response = client.post("/api/game_state/save")
        assert response.status_code == 200
        data = response.json()
        response_model = SaveGameResponse.model_validate(data)

        assert response_model.success is True
        assert response_model.campaign_id is not None
        assert "test-campaign-instance" in response_model.campaign_id

    def test_save_game_state_file_creation(self) -> None:
        """Test save game state creates actual file."""
        from app import create_app

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create app with file repository
            settings = get_test_settings()
            settings.storage.game_state_repo_type = "file"
            settings.storage.saves_dir = tmpdir

            app = create_app(settings)
            client = TestClient(app)

            response = client.post("/api/game_state/save")

            assert response.status_code == 200
            data = response.json()
            response_model = SaveGameResponse.model_validate(data)

            assert response_model.success is True
            assert response_model.message == "Game state saved successfully"

            # Check if file was created
            import os

            files = os.listdir(tmpdir)
            assert len(files) > 0  # At least one save file created
