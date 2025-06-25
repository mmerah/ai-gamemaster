"""Tests for campaign start validation to prevent empty party issues."""

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.core.container import get_container
from app.models.api import StartCampaignResponse
from app.models.campaign.instance import CampaignInstanceModel
from app.models.campaign.template import CampaignTemplateModel
from app.models.character.template import CharacterTemplateModel
from app.models.utils import BaseStatsModel, ProficienciesModel
from tests.conftest import get_test_settings


class TestCampaignStartValidation:
    """Test campaign start validation prevents empty party."""

    def test_start_campaign_template_without_party_fails(
        self, client: TestClient
    ) -> None:
        """Test that starting a campaign template without party members fails."""
        # Create a campaign template
        template = CampaignTemplateModel(
            id="test-campaign-template",
            name="Test Campaign",
            description="Test",
            version=1,
            campaign_goal="Test the validation",
            starting_location={
                "name": "Test Town",
                "description": "A place for testing",
            },
            opening_narrative="Welcome to the test campaign!",
        )

        # Save template
        container = get_container()
        container.get_campaign_template_repository().save(template)

        # Try to start the campaign template directly (without creating instance)
        response = client.post("/api/campaigns/test-campaign-template/start")

        # Should fail with 400 because no party members
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "without party members" in data["error"]
        assert (
            "Please create a campaign instance with selected characters"
            in data["error"]
        )

    def test_start_campaign_instance_with_party_succeeds(
        self, client: TestClient
    ) -> None:
        """Test that starting a campaign instance with party members succeeds."""
        # Create campaign template
        template = CampaignTemplateModel(
            id="test-campaign-template",
            name="Test Campaign",
            description="Test",
            version=1,
            campaign_goal="Test the validation",
            starting_location={
                "name": "Test Town",
                "description": "A place for testing",
            },
            opening_narrative="Welcome to the test campaign!",
        )

        # Create character template
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

        # Create campaign instance with character
        instance = CampaignInstanceModel(
            id="test-campaign-instance",
            name="Test Adventure",
            template_id="test-campaign-template",
            character_ids=["test-char"],
            current_location="Test Town",
            event_log_path="events/test-campaign-instance.json",
        )

        # Save all
        container = get_container()
        container.get_campaign_template_repository().save(template)
        container.get_character_template_repository().save(char_template)
        container.get_campaign_instance_repository().save(instance)

        # Start the campaign instance
        response = client.post("/api/campaigns/test-campaign-instance/start")

        # Should succeed with party members
        assert response.status_code == 200
        data = response.json()
        response_model = StartCampaignResponse.model_validate(data)

        assert response_model.message == "Campaign started successfully"
        assert response_model.initial_state is not None

        # Verify party is populated
        game_state = response_model.initial_state
        assert hasattr(game_state, "party")
        assert len(game_state.party) == 1
        assert "test-char" in game_state.party
