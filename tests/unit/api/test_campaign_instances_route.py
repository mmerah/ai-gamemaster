"""Tests for campaign instances API endpoint."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Generator, List, cast
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import create_app
from app.models.campaign.instance import CampaignInstanceModel
from tests.conftest import get_test_settings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    settings = get_test_settings()
    app = create_app(settings)
    yield TestClient(app)


@pytest.fixture
def mock_instance_repo() -> Mock:
    """Create a mock campaign instance repository."""
    return Mock()


@pytest.fixture
def sample_instances() -> List[CampaignInstanceModel]:
    """Create sample campaign instances for testing."""
    return [
        CampaignInstanceModel(
            id="goblin_cave_adventure",
            name="Goblin Cave Adventure",
            template_id="goblin_cave_template",
            character_ids=["torvin_stonebeard", "elara_meadowlight", "zaltar_mystic"],
            current_location="Goblin Cave Entrance",
            session_count=2,
            in_combat=False,
            event_summary=["Party entered the cave", "Defeated two goblins"],
            event_log_path="saves/campaigns/goblin_cave_adventure/event_log.json",
            created_date=datetime(2025, 5, 23, 17, 2, 0, tzinfo=timezone.utc),
            last_played=datetime(2025, 5, 24, 19, 30, 0, tzinfo=timezone.utc),
        ),
        CampaignInstanceModel(
            id="dragon_heist_campaign",
            name="Dragon Heist Campaign",
            template_id="dragon_heist_template",
            character_ids=["wizard_1", "rogue_1"],
            current_location="Waterdeep Tavern",
            session_count=5,
            in_combat=True,
            event_summary=["Started in Waterdeep", "Met the quest giver"],
            event_log_path="saves/campaigns/dragon_heist_campaign/event_log.json",
            created_date=datetime(2025, 5, 20, 10, 0, 0, tzinfo=timezone.utc),
            last_played=datetime(2025, 5, 25, 20, 15, 0, tzinfo=timezone.utc),
        ),
    ]


class TestCampaignInstancesRoute:
    """Test campaign instances API endpoint."""

    def test_get_campaign_instances_success(
        self,
        client: TestClient,
        mock_instance_repo: Mock,
        sample_instances: List[CampaignInstanceModel],
    ) -> None:
        """Test getting all campaign instances successfully."""
        mock_instance_repo.list.return_value = sample_instances

        # Override the dependency at the app level
        from app.api.dependencies import get_campaign_instance_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_instance_repository] = (
            lambda: mock_instance_repo
        )

        try:
            response = client.get("/api/campaign-instances")

            assert response.status_code == 200
            data = response.json()

            # Validate response using typed models
            assert isinstance(data, list)
            campaign_instances = [
                CampaignInstanceModel.model_validate(item) for item in data
            ]
            assert len(campaign_instances) == 2

            # Check first instance
            first = campaign_instances[0]
            assert first.id == "goblin_cave_adventure"
            assert first.name == "Goblin Cave Adventure"
            assert first.template_id == "goblin_cave_template"
            assert len(first.character_ids) == 3
            assert first.current_location == "Goblin Cave Entrance"
            assert first.session_count == 2
            assert first.in_combat is False
            # Datetime objects are properly parsed by Pydantic
            assert first.created_date == datetime(
                2025, 5, 23, 17, 2, 0, tzinfo=timezone.utc
            )
            assert first.last_played == datetime(
                2025, 5, 24, 19, 30, 0, tzinfo=timezone.utc
            )

            # Check second instance
            second = campaign_instances[1]
            assert second.id == "dragon_heist_campaign"
            assert len(second.character_ids) == 2
            assert second.in_combat is True
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_campaign_instances_empty(
        self, client: TestClient, mock_instance_repo: Mock
    ) -> None:
        """Test getting campaign instances when none exist."""
        mock_instance_repo.list.return_value = []

        # Override the dependency at the app level
        from app.api.dependencies import get_campaign_instance_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_instance_repository] = (
            lambda: mock_instance_repo
        )

        try:
            response = client.get("/api/campaign-instances")

            assert response.status_code == 200
            data = response.json()

            # Validate empty list response
            assert isinstance(data, list)
            campaign_instances = [
                CampaignInstanceModel.model_validate(item) for item in data
            ]
            assert campaign_instances == []
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_campaign_instances_error(
        self, client: TestClient, mock_instance_repo: Mock
    ) -> None:
        """Test error handling when getting campaign instances fails."""
        mock_instance_repo.list.side_effect = Exception("Database error")

        # Override the dependency at the app level
        from app.api.dependencies import get_campaign_instance_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_instance_repository] = (
            lambda: mock_instance_repo
        )

        try:
            response = client.get("/api/campaign-instances")

            assert response.status_code == 500
            data = response.json()
            # Custom exception handler converts detail to error format
            assert "error" in data
            assert data["error"] == "Failed to retrieve campaign instances"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_get_campaign_instances_datetime_handling(
        self, client: TestClient, mock_instance_repo: Mock
    ) -> None:
        """Test that instances with datetime values are handled correctly."""
        # CampaignInstanceModel no longer accepts None for datetime fields
        # Test with actual datetime values instead
        test_created = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        test_played = datetime(2025, 1, 2, 14, 30, 0, tzinfo=timezone.utc)

        instance_with_dates = CampaignInstanceModel(
            id="test_instance",
            name="Test Instance",
            template_id="test_template",
            character_ids=[],
            current_location="Test Location",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path="test/path",
            created_date=test_created,
            last_played=test_played,
        )

        mock_instance_repo.list.return_value = [instance_with_dates]

        # Override the dependency at the app level
        from app.api.dependencies import get_campaign_instance_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_campaign_instance_repository] = (
            lambda: mock_instance_repo
        )

        try:
            response = client.get("/api/campaign-instances")

            assert response.status_code == 200
            data = response.json()

            # Validate response with datetime handling
            assert isinstance(data, list)
            campaign_instances = [
                CampaignInstanceModel.model_validate(item) for item in data
            ]
            assert len(campaign_instances) == 1

            instance = campaign_instances[0]
            assert instance.created_date == test_created
            assert instance.last_played == test_played
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
