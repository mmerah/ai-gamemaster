"""
Shared fixtures for integration tests.
"""
import pytest
import tempfile
from app.core.container import reset_container, get_container
from app.utils.event_sequence import reset_sequence_counter
from tests.test_helpers import EventRecorder


@pytest.fixture(autouse=True)
def reset_container_before_each_test(request):
    """Automatically reset the container before each test to ensure isolation."""
    # Skip container reset if the test has the no_auto_reset_container marker
    if 'no_auto_reset_container' in request.keywords:
        yield
        return
    
    reset_container()
    yield
    # Reset after test as well
    reset_container()


@pytest.fixture
def test_app():
    """Create a test Flask app with consistent configuration."""
    from run import create_app
    
    app = create_app({
        'GAME_STATE_REPO_TYPE': 'memory',
        'TTS_PROVIDER': 'disabled',
        'RAG_ENABLED': False,
        'TESTING': True
    })
    
    with app.app_context():
        yield app


@pytest.fixture
def temp_saves_dir():
    """Create a temporary directory for saves during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def app(temp_saves_dir):
    """Create a Flask app with test configuration."""
    reset_container()
    
    from run import create_app
    app = create_app({
        'GAME_STATE_REPO_TYPE': 'memory',
        'TTS_PROVIDER': 'disabled',
        'RAG_ENABLED': False,
        'TESTING': True,
        'CAMPAIGNS_DIR': f'{temp_saves_dir}/campaigns',
        'CHARACTER_TEMPLATES_DIR': f'{temp_saves_dir}/templates'
    })
    
    with app.app_context():
        yield app
        reset_container()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    from tests.integration.comprehensive_backend.conftest import MockAIService
    return MockAIService()


@pytest.fixture
def event_recorder(app):
    """Create an event recorder."""
    # Reset the global sequence counter to ensure tests start from 1
    reset_sequence_counter()
    
    container = get_container()
    event_queue = container.get_event_queue()
    
    recorder = EventRecorder()
    recorder.attach_to_queue(event_queue)
    return recorder


@pytest.fixture
def container(app):
    """Get the service container."""
    return get_container()


@pytest.fixture
def basic_party(container):
    """Create a basic 2-character party."""
    from app.game.unified_models import GameStateModel, CharacterInstanceModel, LocationModel
    
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
            inventory=[]
        ),
        "wizard": CharacterInstanceModel(
            template_id="test_wizard_template",
            campaign_id="test_campaign",
            current_hp=18,
            max_hp=18,
            level=3,
            conditions=[],
            inventory=[]
        )
    }
    
    game_state.current_location = LocationModel(name="Cave Entrance", description="A dark, foreboding cave")
    game_state.campaign_goal = "Test the combat system"
    
    game_state_repo.save_game_state(game_state)
    
    return game_state