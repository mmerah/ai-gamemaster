"""Tests for campaign instances API endpoint."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Generator, List
from unittest.mock import Mock, patch

import pytest
from flask.testing import FlaskClient

from app.models.campaign import CampaignInstanceModel


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
        client: FlaskClient,
        mock_instance_repo: Mock,
        sample_instances: List[CampaignInstanceModel],
    ) -> None:
        """Test getting all campaign instances successfully."""
        mock_instance_repo.list.return_value = sample_instances

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_instance_repository.return_value = (
                mock_instance_repo
            )
            mock_get_container.return_value = mock_container

            response = client.get("/api/campaign-instances")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "campaigns" in data
            assert len(data["campaigns"]) == 2

            # Check first instance
            first = data["campaigns"][0]
            assert first["id"] == "goblin_cave_adventure"
            assert first["name"] == "Goblin Cave Adventure"
            assert first["template_id"] == "goblin_cave_template"
            assert first["party_size"] == 3
            assert first["current_location"] == "Goblin Cave Entrance"
            assert first["session_count"] == 2
            assert first["in_combat"] is False
            assert first["created_date"] == "2025-05-23T17:02:00+00:00"
            assert first["last_played"] == "2025-05-24T19:30:00+00:00"
            assert (
                first["created_at"] == "2025-05-23T17:02:00+00:00"
            )  # Frontend compatibility

            # Check second instance
            second = data["campaigns"][1]
            assert second["id"] == "dragon_heist_campaign"
            assert second["party_size"] == 2
            assert second["in_combat"] is True

    def test_get_campaign_instances_empty(
        self, client: FlaskClient, mock_instance_repo: Mock
    ) -> None:
        """Test getting campaign instances when none exist."""
        mock_instance_repo.list.return_value = []

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_instance_repository.return_value = (
                mock_instance_repo
            )
            mock_get_container.return_value = mock_container

            response = client.get("/api/campaign-instances")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "campaigns" in data
            assert data["campaigns"] == []

    def test_get_campaign_instances_error(
        self, client: FlaskClient, mock_instance_repo: Mock
    ) -> None:
        """Test error handling when getting campaign instances fails."""
        mock_instance_repo.list.side_effect = Exception("Database error")

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_instance_repository.return_value = (
                mock_instance_repo
            )
            mock_get_container.return_value = mock_container

            response = client.get("/api/campaign-instances")

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
            assert data["error"] == "Database error"

    def test_get_campaign_instances_datetime_handling(
        self, client: FlaskClient, mock_instance_repo: Mock
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

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_campaign_instance_repository.return_value = (
                mock_instance_repo
            )
            mock_get_container.return_value = mock_container

            response = client.get("/api/campaign-instances")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data["campaigns"]) == 1
            assert data["campaigns"][0]["created_date"] == "2025-01-01T12:00:00+00:00"
            assert data["campaigns"][0]["last_played"] == "2025-01-02T14:30:00+00:00"
            assert data["campaigns"][0]["created_at"] == "2025-01-01T12:00:00+00:00"
