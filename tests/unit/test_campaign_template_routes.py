"""Unit tests for campaign template API routes."""

import json
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from flask.testing import FlaskClient

from app import create_app
from app.models import CampaignTemplateModel


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create a test client."""
    from tests.test_config_helper import create_test_service_config

    config = create_test_service_config()
    app = create_app(config)

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_template_repo() -> Mock:
    """Create a mock campaign template repository."""
    return Mock()


@pytest.fixture
def sample_template() -> CampaignTemplateModel:
    """Create a sample campaign template."""
    return CampaignTemplateModel(
        id="test_template_id",
        name="Test Campaign Template",
        description="A test campaign template",
        campaign_goal="Test the template system",
        starting_location={
            "name": "Test Village",
            "description": "A peaceful testing ground",
        },
        opening_narrative="Once upon a test...",
        starting_level=1,
        difficulty="normal",
        ruleset_id="dnd5e_standard",
        lore_id="generic_fantasy",
        theme_mood="Test Theme",
        tags=["test", "template"],
    )


class TestCampaignTemplateRoutes:
    """Test campaign template API routes."""

    def test_create_template(
        self, client: FlaskClient, mock_template_repo: Mock
    ) -> None:
        """Test creating a new template."""
        template_data = {
            "name": "New Template",
            "description": "A new template",
            "campaign_goal": "Test creation",
            "starting_location": {"name": "Start", "description": "Starting point"},
            "opening_narrative": "The adventure begins...",
            "starting_level": 1,
            "difficulty": "normal",
        }

        # The route will add the ID, so we need to simulate that
        created_template = CampaignTemplateModel(id="generated-id", **template_data)
        mock_template_repo.save_template.return_value = created_template

        with patch(
            "app.routes.campaign_template_routes.get_container"
        ) as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_template_repository.return_value = (
                mock_template_repo
            )
            mock_get_container.return_value = mock_container

            response = client.post(
                "/api/campaign_templates",
                data=json.dumps(template_data),
                content_type="application/json",
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            # Response is just the template data, not wrapped
            assert data["name"] == "New Template"

    def test_create_template_no_data(self, client: FlaskClient) -> None:
        """Test creating a template with no data."""
        with patch("app.routes.campaign_template_routes.get_container"):
            response = client.post(
                "/api/campaign_templates", data="", content_type="application/json"
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_create_template_invalid_data(self, client: FlaskClient) -> None:
        """Test creating a template with invalid data."""
        # Missing required fields
        template_data = {
            "name": "Invalid Template"
            # Missing required fields like description, campaign_goal, etc.
        }

        with patch("app.routes.campaign_template_routes.get_container"):
            response = client.post(
                "/api/campaign_templates",
                data=json.dumps(template_data),
                content_type="application/json",
            )

            assert response.status_code == 422  # Validation error
            data = json.loads(response.data)
            assert "error" in data

    def test_update_template_no_data(
        self,
        client: FlaskClient,
        mock_template_repo: Mock,
        sample_template: CampaignTemplateModel,
    ) -> None:
        """Test updating template with no data."""
        mock_template_repo.get_template.return_value = sample_template

        with patch(
            "app.routes.campaign_template_routes.get_container"
        ) as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_template_repository.return_value = (
                mock_template_repo
            )
            mock_get_container.return_value = mock_container

            response = client.put(
                "/api/campaign_templates/test_template_id",
                data="",
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_create_campaign_from_template(
        self,
        client: FlaskClient,
        mock_template_repo: Mock,
        sample_template: CampaignTemplateModel,
    ) -> None:
        """Test creating a campaign from a template."""
        from app.models import CampaignInstanceModel

        mock_template_repo.get_template.return_value = sample_template

        # Create a mock campaign instance that can be serialized
        mock_campaign_instance = CampaignInstanceModel(
            id="new_campaign_id",
            name="New Campaign",
            template_id="test_template_id",
            character_ids=["char1", "char2"],
            current_location="Test Village",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path="saves/campaigns/new_campaign_id/event_log.json",
        )

        mock_campaign_service = Mock()
        mock_campaign_service.create_campaign_instance.return_value = (
            mock_campaign_instance
        )

        request_data = {
            "campaign_name": "New Campaign",
            "character_template_ids": ["char1", "char2"],
        }

        with patch(
            "app.routes.campaign_template_routes.get_container"
        ) as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_template_repository.return_value = (
                mock_template_repo
            )
            mock_container.get_campaign_service.return_value = mock_campaign_service
            mock_get_container.return_value = mock_container

            response = client.post(
                "/api/campaign_templates/test_template_id/create_campaign",
                data=json.dumps(request_data),
                content_type="application/json",
            )

            if response.status_code != 201:
                print(f"Response data: {response.data}")
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["campaign"]["name"] == "New Campaign"

    def test_create_campaign_from_template_not_found(
        self, client: FlaskClient, mock_template_repo: Mock
    ) -> None:
        """Test creating campaign from non-existent template."""
        mock_template_repo.get_template.return_value = None

        with patch(
            "app.routes.campaign_template_routes.get_container"
        ) as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_template_repository.return_value = (
                mock_template_repo
            )
            mock_get_container.return_value = mock_container

            response = client.post(
                "/api/campaign_templates/nonexistent/create_campaign",
                data=json.dumps({"campaign_name": "Test"}),
                content_type="application/json",
            )

            assert response.status_code == 404
            data = json.loads(response.data)
            assert "error" in data
