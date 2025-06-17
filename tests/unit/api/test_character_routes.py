"""Unit tests for character routes."""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from app.models.character import CharacterTemplateModel
from app.models.utils import BaseStatsModel, ProficienciesModel


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
def mock_character_template() -> CharacterTemplateModel:
    """Create a mock character template."""
    return CharacterTemplateModel(
        id="test-template-1",
        name="Test Character",
        race="Human",
        char_class="Fighter",
        level=1,
        alignment="Neutral Good",
        background="Soldier",
        base_stats=BaseStatsModel(STR=15, DEX=14, CON=13, INT=12, WIS=10, CHA=8),
        proficiencies=ProficienciesModel(
            skills=["Athletics", "Intimidation"],
            armor=["Light", "Medium", "Heavy", "Shields"],
            weapons=["Simple", "Martial"],
            tools=[],
            saving_throws=["Strength", "Constitution"],
        ),
        languages=["Common", "Orcish"],
        racial_traits=[],
        class_features=[],
        feats=[],
        spells_known=[],
        cantrips_known=[],
        starting_equipment=[],
        starting_gold=100,
        personality_traits=["I am always polite"],
        ideals=["Honor"],
        bonds=["My weapon is my life"],
        flaws=["I am too trusting"],
    )


def test_update_character_template_no_data(
    client: FlaskClient, mock_character_template: CharacterTemplateModel
) -> None:
    """Test updating character template with no data."""
    with patch("app.api.character_routes.get_container") as mock_get_container:
        mock_repo = MagicMock()
        mock_repo.get.return_value = mock_character_template

        mock_container = MagicMock()
        mock_container.get_character_template_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        response = client.put(
            "/api/character_templates/test-template-1",
            data="",
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "No template data provided" in data["error"]
