"""Unit tests for the character adventures endpoint."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Generator
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


class TestCharacterAdventuresRoute:
    """Test the character adventures API route."""

    def test_get_character_adventures_success(self, client: FlaskClient) -> None:
        """Test successfully getting character adventures."""
        # Mock template
        mock_template = Mock()
        mock_template.name = "Torvin Stonebeard"
        mock_template.level = 3
        mock_template.char_class = "Fighter"

        # Mock campaign instances
        instance1 = CampaignInstanceModel(
            id="instance_1",
            name="The Goblin Cave Adventure",
            template_id="campaign_1",
            character_ids=["char_template_1", "char_template_2"],
            current_location="Goblin Caves",
            session_count=5,
            in_combat=False,
            event_summary=["Started adventure", "Found clues"],
            event_log_path="saves/campaigns/instance_1/event_log.json",
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
        )

        instance2 = CampaignInstanceModel(
            id="instance_2",
            name="Dragon's Lair Quest",
            template_id="campaign_2",
            character_ids=[
                "char_template_2",
                "char_template_3",
            ],  # Not including char_template_1
            current_location="Mountain Pass",
            session_count=3,
            in_combat=True,
            event_summary=["Began journey", "Encountered bandits"],
            event_log_path="saves/campaigns/instance_2/event_log.json",
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
        )

        # Mock game state with character instance
        mock_game_state = Mock()
        mock_char_instance = Mock()
        mock_char_instance.template_id = "char_template_1"
        mock_char_instance.current_hp = 38
        mock_char_instance.max_hp = 42
        mock_char_instance.level = 4
        mock_char_instance.char_class = "Fighter"
        mock_char_instance.experience = 2700
        mock_game_state.party = {
            "torvin": mock_char_instance
        }  # party is a dict, not a list

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()

            mock_char_repo = Mock()
            mock_char_repo.get.return_value = mock_template

            mock_instance_repo = Mock()
            mock_instance_repo.list.return_value = [instance1, instance2]

            mock_game_state_repo = Mock()
            mock_game_state_repo.get_game_state.return_value = mock_game_state
            mock_game_state_repo.set_campaign.return_value = None

            mock_container.get_character_template_repository.return_value = (
                mock_char_repo
            )
            mock_container.get_campaign_instance_repository.return_value = (
                mock_instance_repo
            )
            mock_container.get_game_state_repository.return_value = mock_game_state_repo
            mock_get_container.return_value = mock_container

            response = client.get("/api/character_templates/char_template_1/adventures")

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data["character_name"] == "Torvin Stonebeard"
            assert len(data["adventures"]) == 1  # Only in instance_1

            adventure = data["adventures"][0]
            assert adventure["campaign_id"] == "instance_1"
            assert adventure["campaign_name"] == "The Goblin Cave Adventure"
            assert adventure["template_id"] == "campaign_1"
            assert adventure["current_location"] == "Goblin Caves"
            assert adventure["session_count"] == 5
            assert adventure["in_combat"] is False
            assert adventure["character_data"]["level"] == 4
            assert adventure["character_data"]["current_hp"] == 38
            assert adventure["character_data"]["max_hp"] == 42

    def test_get_character_adventures_not_found(self, client: FlaskClient) -> None:
        """Test getting adventures for non-existent character."""
        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_char_repo = Mock()
            mock_char_repo.get.return_value = None

            mock_container.get_character_template_repository.return_value = (
                mock_char_repo
            )
            mock_get_container.return_value = mock_container

            response = client.get("/api/character_templates/nonexistent/adventures")

            assert response.status_code == 404
            data = json.loads(response.data)
            assert "error" in data
            assert "not found" in data["error"]

    def test_get_character_adventures_no_campaigns(self, client: FlaskClient) -> None:
        """Test getting adventures when character is not in any campaigns."""
        mock_template = Mock()
        mock_template.name = "Elara Meadowlight"
        mock_template.level = 1
        mock_template.char_class = "Cleric"

        # Create instances that don't include this character
        instance1 = CampaignInstanceModel(
            id="instance_1",
            name="Some Adventure",
            template_id="campaign_1",
            character_ids=[
                "other_char_1",
                "other_char_2",
            ],  # Not including our character
            current_location="Town",
            session_count=1,
            in_combat=False,
            event_summary=[],
            event_log_path="saves/campaigns/instance_1/event_log.json",
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
        )

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_char_repo = Mock()
            mock_char_repo.get.return_value = mock_template

            mock_instance_repo = Mock()
            mock_instance_repo.list.return_value = [instance1]

            mock_game_state_repo = Mock()

            mock_container.get_character_template_repository.return_value = (
                mock_char_repo
            )
            mock_container.get_campaign_instance_repository.return_value = (
                mock_instance_repo
            )
            mock_container.get_game_state_repository.return_value = mock_game_state_repo
            mock_get_container.return_value = mock_container

            response = client.get("/api/character_templates/char_template_1/adventures")

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data["character_name"] == "Elara Meadowlight"
            assert len(data["adventures"]) == 0

    def test_get_character_adventures_with_no_game_state(
        self, client: FlaskClient
    ) -> None:
        """Test getting adventures when game state doesn't exist."""
        mock_template = Mock()
        mock_template.name = "Torvin Stonebeard"
        mock_template.level = 3
        mock_template.char_class = "Fighter"
        mock_template.base_stats = Mock(CON=10)  # Ensure CON is set for HP calculation

        instance1 = CampaignInstanceModel(
            id="instance_1",
            name="The Goblin Cave Adventure",
            template_id="campaign_1",
            character_ids=["char_template_1"],
            current_location="Goblin Caves",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path="saves/campaigns/instance_1/event_log.json",
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
        )

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_char_repo = Mock()
            mock_char_repo.get.return_value = mock_template

            mock_instance_repo = Mock()
            mock_instance_repo.list.return_value = [instance1]

            mock_game_state_repo = Mock()
            mock_game_state_repo.get_game_state.return_value = None  # No game state

            mock_container.get_character_template_repository.return_value = (
                mock_char_repo
            )
            mock_container.get_campaign_instance_repository.return_value = (
                mock_instance_repo
            )
            mock_container.get_game_state_repository.return_value = mock_game_state_repo

            # Mock ContentService for HP calculation
            mock_content_service = Mock()
            mock_class = Mock()
            mock_class.hit_die = 10  # Fighter hit die
            mock_content_service.get_class_by_name.return_value = mock_class
            mock_container.get_content_service.return_value = mock_content_service

            mock_get_container.return_value = mock_container

            response = client.get("/api/character_templates/char_template_1/adventures")

            assert response.status_code == 200
            data = json.loads(response.data)

            assert len(data["adventures"]) == 1
            adventure = data["adventures"][0]
            # Should use default character data
            assert adventure["character_data"]["level"] == 3
            assert adventure["character_data"]["class"] == "Fighter"
            # Fighter HP calculated by CharacterFactory
            # Level 3 Fighter with CON 10 (mod 0): 10 + 0 + 2*(5.5 + 0) = 21
            assert adventure["character_data"]["current_hp"] == 21
            assert adventure["character_data"]["max_hp"] == 21
