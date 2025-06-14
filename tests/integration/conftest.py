"""
Shared fixtures for integration tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.core.container import ServiceContainer, get_container, reset_container
from app.models.character import CharacterInstanceModel
from app.models.game_state import GameStateModel
from app.models.utils import LocationModel
from app.utils.event_sequence import reset_sequence_counter
from tests.test_helpers import EventRecorder


@pytest.fixture(autouse=True)
def reset_container_before_each_test(
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    """Automatically reset the container before each test to ensure isolation."""
    # Skip container reset if the test has the no_auto_reset_container marker
    if "no_auto_reset_container" in request.keywords:
        yield
        return

    reset_container()
    yield
    # Reset after test as well
    reset_container()


# Import centralized fixtures from root conftest


@pytest.fixture
def temp_saves_dir() -> Generator[str, None, None]:
    """Create a temporary directory for saves during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def event_recorder(app: Flask) -> EventRecorder:
    """Create an event recorder."""
    # Reset the global sequence counter to ensure tests start from 1
    reset_sequence_counter()

    container = get_container()
    event_queue = container.get_event_queue()

    recorder = EventRecorder()
    recorder.attach_to_queue(event_queue)
    return recorder


@pytest.fixture
def container(app: Flask) -> ServiceContainer:
    """Get the service container."""
    return get_container()


@pytest.fixture
def basic_party(container: ServiceContainer) -> GameStateModel:
    """Create a basic 2-character party."""
    game_state_repo = container.get_game_state_repository()

    game_state = GameStateModel()
    game_state.party = {
        "fighter": CharacterInstanceModel(
            template_id="test_fighter_template",
            campaign_id="test_campaign",
            current_hp=28,
            max_hp=28,
            level=3,
            conditions=[],
            inventory=[],
        ),
        "wizard": CharacterInstanceModel(
            template_id="test_wizard_template",
            campaign_id="test_campaign",
            current_hp=18,
            max_hp=18,
            level=3,
            conditions=[],
            inventory=[],
        ),
    }

    game_state.current_location = LocationModel(
        name="Cave Entrance", description="A dark, foreboding cave"
    )
    game_state.campaign_goal = "Test the combat system"

    game_state_repo.save_game_state(game_state)

    return game_state


# Import test database fixtures
from tests.integration.fixtures.test_database import (
    test_content_db_path,
    test_db_manager,
    test_db_session,
)
from tests.integration.fixtures.test_database_manager import (
    empty_test_database,
    isolated_test_database,
    shared_test_database,
)


@pytest.fixture
def test_database_url(test_content_db_path: Path) -> str:
    """Provide the test database URL."""
    return f"sqlite:///{test_content_db_path}"
