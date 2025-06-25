"""Unit tests for character routes."""

from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.character.template import (
    CharacterTemplateModel,
    CharacterTemplateUpdateModel,
)
from app.models.utils import BaseStatsModel, ProficienciesModel
from tests.conftest import get_test_settings


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    from app import create_app

    settings = get_test_settings()
    app = create_app(settings)
    return TestClient(app)


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
    client: TestClient, mock_character_template: CharacterTemplateModel
) -> None:
    """Test updating character template with no data."""
    mock_repo = MagicMock()
    mock_repo.get.return_value = mock_character_template
    mock_repo.save.return_value = True

    # Override the dependency at the app level
    from fastapi import FastAPI

    from app.api.dependencies import get_character_template_repository

    app = cast(FastAPI, client.app)
    app.dependency_overrides[get_character_template_repository] = lambda: mock_repo

    try:
        # Use an empty update model - this is valid and should succeed
        empty_update = CharacterTemplateUpdateModel()
        response = client.put(
            "/api/character_templates/test-template-1",
            json=empty_update.model_dump(exclude_unset=True, mode="json"),
        )

        # Empty updates are valid and should return the unchanged template
        assert response.status_code == 200
        data = response.json()

        # Validate response using typed model
        updated_template = CharacterTemplateModel.model_validate(data)
        assert updated_template.id == mock_character_template.id
        assert updated_template.name == mock_character_template.name
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


def test_update_character_template_invalid_body(client: TestClient) -> None:
    """Test updating character template with invalid body (None)."""
    # FastAPI requires content-type for PUT requests with body
    response = client.put(
        "/api/character_templates/test-template-1",
        content="null",  # Send literal null
        headers={"Content-Type": "application/json"},
    )

    # FastAPI returns 422 for validation errors
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
