"""
Shared fixtures for integration tests.
"""
import pytest
from app.core.container import reset_container


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