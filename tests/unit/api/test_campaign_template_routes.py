"""Unit tests for campaign template API routes."""

import json
from typing import Generator, cast
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import create_app
from app.models.api.requests import CreateCampaignFromTemplateRequest
from app.models.api.responses import CreateCampaignFromTemplateResponse
from app.models.campaign.instance import CampaignInstanceModel
from app.models.campaign.template import (
    CampaignTemplateModel,
    CampaignTemplateUpdateModel,
)
from tests.conftest import get_test_settings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    settings = get_test_settings()
    app = create_app(settings)
    yield TestClient(app)


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
        self, client: TestClient, mock_template_repo: Mock
    ) -> None:
        """Test creating a new template."""
        # Use the proper model
        template = CampaignTemplateModel(
            id="test-create-id",
            name="New Template",
            description="A new template",
            campaign_goal="Test creation",
            starting_location={"name": "Start", "description": "Starting point"},
            opening_narrative="The adventure begins...",
            starting_level=1,
            difficulty="normal",
        )

        # Set mock to return success
        mock_template_repo.save.return_value = True

        # Override the dependency at the app level
        from app.api.dependencies import get_campaign_template_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_template_repository] = (
            lambda: mock_template_repo
        )

        try:
            response = client.post(
                "/api/campaign_templates",
                json=template.model_dump(mode="json"),
            )

            assert response.status_code == 201
            data = response.json()

            # Validate response using typed model
            created_template = CampaignTemplateModel.model_validate(data)
            assert created_template.name == "New Template"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_create_template_no_data(self, client: TestClient) -> None:
        """Test creating a template with no data."""
        response = client.post("/api/campaign_templates", json={})

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        # Custom exception handler converts to error format
        assert "error" in data
        assert "validation_errors" in data

    def test_create_template_invalid_data(self, client: TestClient) -> None:
        """Test creating a template with invalid data."""
        # Create a dict with missing required fields to test validation
        # Note: We intentionally use a raw dict here to test validation errors
        incomplete_data = {
            "name": "Invalid Template"
            # Missing required fields like description, campaign_goal, etc.
        }

        response = client.post(
            "/api/campaign_templates",
            json=incomplete_data,
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        # Custom exception handler converts to error format
        assert "error" in data
        assert "validation_errors" in data

    def test_update_template_no_data(
        self,
        client: TestClient,
        mock_template_repo: Mock,
        sample_template: CampaignTemplateModel,
    ) -> None:
        """Test updating template with no data."""
        mock_template_repo.get.return_value = sample_template
        mock_template_repo.save.return_value = True

        # Override the dependency at the app level
        from app.api.dependencies import get_campaign_template_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_template_repository] = (
            lambda: mock_template_repo
        )

        try:
            # Use an empty update model
            empty_update = CampaignTemplateUpdateModel()
            response = client.put(
                "/api/campaign_templates/test_template_id",
                json=empty_update.model_dump(exclude_unset=True, mode="json"),
            )

            # Empty updates are valid in FastAPI with exclude_unset=True
            # Template is returned unchanged
            assert response.status_code == 200
            data = response.json()

            # Validate response using typed model
            updated_template = CampaignTemplateModel.model_validate(data)
            assert updated_template.id == sample_template.id
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_create_campaign_from_template(
        self,
        client: TestClient,
        mock_template_repo: Mock,
        sample_template: CampaignTemplateModel,
    ) -> None:
        """Test creating a campaign from a template."""
        mock_template_repo.get.return_value = sample_template

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

        # Use the proper request model
        request = CreateCampaignFromTemplateRequest(
            campaign_name="New Campaign",
            character_ids=[
                "char1",
                "char2",
            ],  # Note: API expects character_ids, not character_template_ids
        )

        # Override the dependencies at the app level
        from app.api.dependencies import (
            get_campaign_instance_repository,
            get_campaign_service,
            get_campaign_template_repository,
        )

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_template_repository] = (
            lambda: mock_template_repo
        )
        app.dependency_overrides[get_campaign_service] = lambda: mock_campaign_service
        app.dependency_overrides[get_campaign_instance_repository] = lambda: Mock()

        try:
            response = client.post(
                "/api/campaign_templates/test_template_id/create_campaign",
                json=request.model_dump(mode="json"),
            )

            if response.status_code != 201:
                print(f"Response data: {response.text}")
            assert response.status_code == 201
            data = response.json()

            # Validate response using typed model
            response_model = CreateCampaignFromTemplateResponse.model_validate(data)
            assert response_model.success is True
            assert response_model.campaign.name == "New Campaign"
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_create_campaign_from_template_not_found(
        self, client: TestClient, mock_template_repo: Mock
    ) -> None:
        """Test creating campaign from non-existent template."""
        mock_template_repo.get.return_value = None

        # Override the dependency at the app level
        from app.api.dependencies import get_campaign_template_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_template_repository] = (
            lambda: mock_template_repo
        )

        try:
            # Use the proper request model
            request = CreateCampaignFromTemplateRequest(campaign_name="Test")
            response = client.post(
                "/api/campaign_templates/nonexistent/create_campaign",
                json=request.model_dump(mode="json"),
            )

            assert response.status_code == 404
            data = response.json()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
            assert "error" in data
