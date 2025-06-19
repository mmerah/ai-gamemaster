"""Tests for D5e API endpoints with content pack filtering."""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.api import initialize_routes
from app.content.schemas import D5eBackground, D5eClass, D5eRace


class TestD5eContentPackFiltering:
    """Test D5e API endpoints with content pack filtering."""

    @pytest.fixture
    def app(self) -> Flask:
        """Create Flask app for testing."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        initialize_routes(app)
        return app

    @pytest.fixture
    def client(self, app: Flask) -> FlaskClient:
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def mock_d5e_service(self) -> Mock:
        """Mock D5e service."""
        mock_service = Mock()
        mock_service._hub = Mock()
        return mock_service

    def test_get_races_with_content_pack_filtering(
        self, client: FlaskClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=races endpoint with content pack filtering."""
        # Setup mock races
        mock_race1 = Mock()
        mock_race1.model_dump.return_value = {
            "index": "elf",
            "name": "Elf",
            "content_pack_id": "custom-pack",
            "speed": 30,
            "size": "Medium",
        }

        # Mock get_content_filtered to return filtered races
        mock_d5e_service.get_content_filtered.return_value = [mock_race1]

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_content_service.return_value = mock_d5e_service
            mock_get_container.return_value = mock_container
            response = client.get(
                "/api/d5e/content?type=races&content_pack_ids=custom-pack,homebrew"
            )
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 1
            assert data[0]["name"] == "Elf"
            assert data[0]["content_pack_id"] == "custom-pack"

            # Verify get_content_filtered was called with correct parameters
            mock_d5e_service.get_content_filtered.assert_called_once_with(
                "races",
                {"content_pack_ids": "custom-pack,homebrew"},
                ["custom-pack", "homebrew"],
            )

    def test_get_races_without_content_pack_filtering(
        self, client: FlaskClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=races endpoint without content pack filtering."""
        # Setup mock races
        mock_race1 = Mock()
        mock_race1.model_dump.return_value = {
            "index": "elf",
            "name": "Elf",
            "content_pack_id": "dnd_5e_srd",
        }
        mock_race2 = Mock()
        mock_race2.model_dump.return_value = {
            "index": "dwarf",
            "name": "Dwarf",
            "content_pack_id": "dnd_5e_srd",
        }

        # Mock get_content_filtered to return all races
        mock_d5e_service.get_content_filtered.return_value = [mock_race1, mock_race2]

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_content_service.return_value = mock_d5e_service
            mock_get_container.return_value = mock_container
            response = client.get("/api/d5e/content?type=races")
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 2

            # Verify get_content_filtered was called without content_pack_ids
            mock_d5e_service.get_content_filtered.assert_called_once_with(
                "races", {}, None
            )

    def test_get_classes_with_content_pack_filtering(
        self, client: FlaskClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=classes endpoint with content pack filtering."""
        # Setup mock class
        mock_class = Mock()
        mock_class.model_dump.return_value = {
            "index": "sorcerer",
            "name": "Sorcerer",
            "content_pack_id": "custom-pack",
            "hit_die": 6,
        }

        # Mock get_content_filtered
        mock_d5e_service.get_content_filtered.return_value = [mock_class]

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_content_service.return_value = mock_d5e_service
            mock_get_container.return_value = mock_container
            response = client.get(
                "/api/d5e/content?type=classes&content_pack_ids=custom-pack,dnd_5e_srd"
            )
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 1
            assert data[0]["name"] == "Sorcerer"
            assert data[0]["content_pack_id"] == "custom-pack"

    def test_get_backgrounds_with_content_pack_filtering(
        self, client: FlaskClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=backgrounds endpoint with content pack filtering."""
        # Setup mock background
        mock_background = Mock()
        mock_background.model_dump.return_value = {
            "index": "soldier",
            "name": "Soldier",
            "content_pack_id": "custom-pack",
            "starting_proficiencies": [],
            "languages": [],
            "starting_equipment": [],
            "starting_equipment_options": [],
            "feature": {
                "name": "Military Rank",
                "desc": ["You have a military rank from your career as a soldier."],
            },
        }

        # Mock get_content_filtered
        mock_d5e_service.get_content_filtered.return_value = [mock_background]

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_content_service.return_value = mock_d5e_service
            mock_get_container.return_value = mock_container
            response = client.get(
                "/api/d5e/content?type=backgrounds&content_pack_ids=custom-pack,homebrew-pack"
            )
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 1
            assert data[0]["name"] == "Soldier"
            assert data[0]["content_pack_id"] == "custom-pack"

    def test_content_pack_filtering_with_empty_parameter(
        self, client: FlaskClient, mock_d5e_service: Mock
    ) -> None:
        """Test that empty content_pack_ids parameter is handled correctly."""
        # Mock get_content_filtered to return empty list
        mock_d5e_service.get_content_filtered.return_value = []

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_content_service.return_value = mock_d5e_service
            mock_get_container.return_value = mock_container
            # Empty parameter should still call get_content_filtered with None
            response = client.get("/api/d5e/content?type=races&content_pack_ids=")
            assert response.status_code == 200

            # Verify get_content_filtered was called with None for content_pack_ids
            mock_d5e_service.get_content_filtered.assert_called_once_with(
                "races", {"content_pack_ids": ""}, None
            )

    def test_content_pack_filtering_with_whitespace(
        self, client: FlaskClient, mock_d5e_service: Mock
    ) -> None:
        """Test that whitespace in content pack IDs is handled correctly."""
        mock_d5e_service.get_content_filtered.return_value = []

        with patch("app.api.dependencies.get_container") as mock_get_container:
            mock_container = Mock()
            mock_container.get_content_service.return_value = mock_d5e_service
            mock_get_container.return_value = mock_container
            # Parameter with spaces should be trimmed
            response = client.get(
                "/api/d5e/content?type=classes&content_pack_ids= custom-pack , homebrew "
            )
            assert response.status_code == 200

            # Verify get_content_filtered was called with trimmed values
            mock_d5e_service.get_content_filtered.assert_called_once_with(
                "classes",
                {"content_pack_ids": " custom-pack , homebrew "},
                ["custom-pack", "homebrew"],
            )
