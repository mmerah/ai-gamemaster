"""Unit tests for the character adventures endpoint."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Generator, cast
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.factory import create_fastapi_app
from app.models.api.responses import CharacterAdventuresResponse
from app.models.campaign import CampaignInstanceModel
from tests.conftest import get_test_settings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    settings = get_test_settings()
    app = create_fastapi_app(settings)
    yield TestClient(app)


class TestCharacterAdventuresRoute:
    """Test the character adventures API route."""

    def test_get_character_adventures_success(self, client: TestClient) -> None:
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

        # Mock repositories
        mock_char_repo = Mock()
        mock_char_repo.get.return_value = mock_template

        mock_instance_repo = Mock()
        mock_instance_repo.list.return_value = [instance1, instance2]

        mock_game_state_repo = Mock()
        mock_game_state_repo.get_game_state.return_value = mock_game_state
        mock_game_state_repo.set_campaign.return_value = None

        mock_content_service = Mock()

        # Override the dependencies at the app level
        from app.api.dependencies_fastapi import (
            get_campaign_instance_repository,
            get_character_template_repository,
            get_content_service,
            get_game_state_repository,
        )

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_character_template_repository] = (
            lambda: mock_char_repo
        )
        app.dependency_overrides[get_campaign_instance_repository] = (
            lambda: mock_instance_repo
        )
        app.dependency_overrides[get_game_state_repository] = (
            lambda: mock_game_state_repo
        )
        app.dependency_overrides[get_content_service] = lambda: mock_content_service

        try:
            response = client.get("/api/character_templates/char_template_1/adventures")

            assert response.status_code == 200
            data = response.json()

            # Validate response using typed model
            response_model = CharacterAdventuresResponse.model_validate(data)

            assert response_model.character_name == "Torvin Stonebeard"
            assert len(response_model.adventures) == 1  # Only in instance_1

            adventure = response_model.adventures[0]
            assert adventure.campaign_id == "instance_1"
            assert adventure.campaign_name == "The Goblin Cave Adventure"
            assert adventure.template_id == "campaign_1"
            assert adventure.current_location == "Goblin Caves"
            assert adventure.session_count == 5
            assert adventure.in_combat is False
            assert adventure.character_data.level == 4
            assert adventure.character_data.current_hp == 38
            assert adventure.character_data.max_hp == 42
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_get_character_adventures_not_found(self, client: TestClient) -> None:
        """Test getting adventures for non-existent character."""
        mock_char_repo = Mock()
        mock_char_repo.get.return_value = None

        # Override the dependency at the app level
        from app.api.dependencies_fastapi import get_character_template_repository

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_character_template_repository] = (
            lambda: mock_char_repo
        )

        try:
            response = client.get("/api/character_templates/nonexistent/adventures")

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "not found" in data["error"].lower()
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_get_character_adventures_no_campaigns(self, client: TestClient) -> None:
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

        # Mock repositories
        mock_char_repo = Mock()
        mock_char_repo.get.return_value = mock_template

        mock_instance_repo = Mock()
        mock_instance_repo.list.return_value = [instance1]

        mock_game_state_repo = Mock()

        mock_content_service = Mock()

        # Override the dependencies at the app level
        from app.api.dependencies_fastapi import (
            get_campaign_instance_repository,
            get_character_template_repository,
            get_content_service,
            get_game_state_repository,
        )

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_character_template_repository] = (
            lambda: mock_char_repo
        )
        app.dependency_overrides[get_campaign_instance_repository] = (
            lambda: mock_instance_repo
        )
        app.dependency_overrides[get_game_state_repository] = (
            lambda: mock_game_state_repo
        )
        app.dependency_overrides[get_content_service] = lambda: mock_content_service

        try:
            response = client.get("/api/character_templates/char_template_1/adventures")

            assert response.status_code == 200
            data = response.json()

            # Validate response using typed model
            response_model = CharacterAdventuresResponse.model_validate(data)

            assert response_model.character_name == "Elara Meadowlight"
            assert len(response_model.adventures) == 0
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_get_character_adventures_with_no_game_state(
        self, client: TestClient
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

        # Mock repositories
        mock_char_repo = Mock()
        mock_char_repo.get.return_value = mock_template

        mock_instance_repo = Mock()
        mock_instance_repo.list.return_value = [instance1]

        mock_game_state_repo = Mock()
        mock_game_state_repo.get_game_state.return_value = None  # No game state

        # Mock ContentService for HP calculation
        mock_content_service = Mock()
        mock_class = Mock()
        mock_class.hit_die = 10  # Fighter hit die
        mock_content_service.get_class_by_name.return_value = mock_class

        # Override the dependencies at the app level
        from app.api.dependencies_fastapi import (
            get_campaign_instance_repository,
            get_character_template_repository,
            get_content_service,
            get_game_state_repository,
        )

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_character_template_repository] = (
            lambda: mock_char_repo
        )
        app.dependency_overrides[get_campaign_instance_repository] = (
            lambda: mock_instance_repo
        )
        app.dependency_overrides[get_game_state_repository] = (
            lambda: mock_game_state_repo
        )
        app.dependency_overrides[get_content_service] = lambda: mock_content_service

        try:
            response = client.get("/api/character_templates/char_template_1/adventures")

            assert response.status_code == 200
            data = response.json()

            # Validate response using typed model
            from app.models.api import CharacterAdventuresResponse

            response_model = CharacterAdventuresResponse.model_validate(data)

            assert len(response_model.adventures) == 1
            adventure = response_model.adventures[0]
            # Should use default character data
            assert adventure.character_data.level == 3
            assert adventure.character_data.class_name == "Fighter"
            # Fighter HP calculated by CharacterFactory
            # Level 3 Fighter with CON 10 (mod 0): 10 + 0 + 2*(5.5 + 0) = 21
            assert adventure.character_data.current_hp == 21
            assert adventure.character_data.max_hp == 21
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
