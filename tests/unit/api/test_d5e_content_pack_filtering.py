"""Tests for D5e API endpoints with content pack filtering."""

from typing import Any, Dict, cast
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.content.schemas import D5eBackground, D5eClass, D5eRace
from tests.conftest import get_test_settings


class TestD5eContentPackFiltering:
    """Test D5e API endpoints with content pack filtering."""

    @pytest.fixture
    def client(self, mock_d5e_service: Mock) -> TestClient:
        """Create test client."""
        from app.core.container import get_container
        from app.factory import create_fastapi_app

        settings = get_test_settings()
        app = create_fastapi_app(settings)

        # Override the content service in the container
        container = get_container()
        container._content_service = mock_d5e_service

        return TestClient(app)

    @pytest.fixture
    def mock_d5e_service(self) -> Mock:
        """Mock D5e service."""
        mock_service = Mock()
        mock_service._hub = Mock()
        return mock_service

    def test_get_races_with_content_pack_filtering(
        self, client: TestClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=races endpoint with content pack filtering."""
        # Create proper D5eRace instances instead of mocks
        race1 = D5eRace(
            index="elf",
            name="Elf",
            speed=30,
            alignment="Chaotic good",
            age="Adult at 100",
            size="Medium",
            size_description="4-6 feet tall",
            language_desc="Common and Elvish",
            url="/api/races/elf",
        )

        # Mock get_content_filtered to return filtered races
        mock_d5e_service.get_content_filtered.return_value = [race1]

        response = client.get(
            "/api/d5e/content?type=races&content_pack_ids=custom-pack,homebrew"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Elf"
        # content_pack_id is not exposed in the API response

        # Verify get_content_filtered was called with correct parameters
        mock_d5e_service.get_content_filtered.assert_called_once_with(
            "races",
            {},  # content_pack_ids is removed from filters
            ["custom-pack", "homebrew"],
        )

    def test_get_races_without_content_pack_filtering(
        self, client: TestClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=races endpoint without content pack filtering."""
        # Create proper D5eRace instances
        race1 = D5eRace(
            index="elf",
            name="Elf",
            speed=30,
            alignment="Chaotic good",
            age="Adult at 100",
            size="Medium",
            size_description="4-6 feet tall",
            language_desc="Common and Elvish",
            url="/api/races/elf",
        )
        race2 = D5eRace(
            index="dwarf",
            name="Dwarf",
            speed=25,
            alignment="Lawful good",
            age="Adult at 50",
            size="Medium",
            size_description="4-5 feet tall",
            language_desc="Common and Dwarvish",
            url="/api/races/dwarf",
        )

        # Mock get_content_filtered to return all races
        mock_d5e_service.get_content_filtered.return_value = [race1, race2]

        response = client.get("/api/d5e/content?type=races")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify get_content_filtered was called without content_pack_ids
        mock_d5e_service.get_content_filtered.assert_called_once_with("races", {}, None)

    def test_get_classes_with_content_pack_filtering(
        self, client: TestClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=classes endpoint with content pack filtering."""
        # Create proper D5eClass instances
        class1 = D5eClass(
            index="wizard",
            name="Wizard",
            hit_die=6,
            class_levels="/api/classes/wizard/levels",
            url="/api/classes/wizard",
        )

        # Mock get_content_filtered to return filtered classes
        mock_d5e_service.get_content_filtered.return_value = [class1]

        response = client.get(
            "/api/d5e/content?type=classes&content_pack_ids=custom-pack"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Wizard"
        # content_pack_id is not exposed in the API response

        # Verify get_content_filtered was called with correct parameters
        mock_d5e_service.get_content_filtered.assert_called_once_with(
            "classes", {}, ["custom-pack"]
        )

    def test_get_backgrounds_with_content_pack_filtering(
        self, client: TestClient, mock_d5e_service: Mock
    ) -> None:
        """Test /api/d5e/content?type=backgrounds endpoint with content pack filtering."""
        # Create proper D5eBackground instances
        bg1 = D5eBackground(
            index="noble",
            name="Noble",
            feature={"name": "Position of Privilege", "desc": ["Nobility respect"]},
            personality_traits={
                "choose": 2,
                "type": "personality_traits",
                "from": {
                    "option_set_type": "personality_traits",
                    "options": ["Trait 1", "Trait 2"],
                },
            },
            ideals={
                "choose": 1,
                "type": "ideals",
                "from": {"option_set_type": "ideals", "options": ["Ideal 1"]},
            },
            bonds={
                "choose": 1,
                "type": "bonds",
                "from": {"option_set_type": "bonds", "options": ["Bond 1"]},
            },
            flaws={
                "choose": 1,
                "type": "flaws",
                "from": {"option_set_type": "flaws", "options": ["Flaw 1"]},
            },
            url="/api/backgrounds/noble",
        )

        # Mock get_content_filtered to return filtered backgrounds
        mock_d5e_service.get_content_filtered.return_value = [bg1]

        response = client.get(
            "/api/d5e/content?type=backgrounds&content_pack_ids=custom-pack"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Noble"
        # content_pack_id is not exposed in the API response

        # Verify get_content_filtered was called with correct parameters
        mock_d5e_service.get_content_filtered.assert_called_once_with(
            "backgrounds", {}, ["custom-pack"]
        )

    def test_content_pack_filtering_with_empty_parameter(
        self, client: TestClient, mock_d5e_service: Mock
    ) -> None:
        """Test that empty content_pack_ids parameter is handled correctly."""
        # Mock get_content_filtered to return empty list
        mock_d5e_service.get_content_filtered.return_value = []

        # Empty parameter should still call get_content_filtered with None
        response = client.get("/api/d5e/content?type=races&content_pack_ids=")
        assert response.status_code == 200

        # Verify get_content_filtered was called with None for content_pack_ids
        mock_d5e_service.get_content_filtered.assert_called_once_with("races", {}, None)

    def test_content_pack_filtering_with_whitespace(
        self, client: TestClient, mock_d5e_service: Mock
    ) -> None:
        """Test that whitespace in content_pack_ids is handled correctly."""
        # Create proper D5eRace instance
        race = D5eRace(
            index="elf",
            name="Elf",
            speed=30,
            alignment="Chaotic good",
            age="Adult at 100",
            size="Medium",
            size_description="4-6 feet tall",
            language_desc="Common and Elvish",
            url="/api/races/elf",
        )

        # Mock get_content_filtered to return filtered race
        mock_d5e_service.get_content_filtered.return_value = [race]

        # Test with spaces around commas
        response = client.get(
            "/api/d5e/content?type=races&content_pack_ids=custom-pack , homebrew"
        )
        assert response.status_code == 200

        # Verify get_content_filtered was called with trimmed pack IDs
        mock_d5e_service.get_content_filtered.assert_called_once_with(
            "races",
            {},
            ["custom-pack", "homebrew"],
        )
