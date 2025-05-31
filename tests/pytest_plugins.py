"""
Pytest plugins for proper test isolation.
"""
import os
import sys
import pytest


def pytest_configure(config):
    """Configure pytest with proper test environment."""
    # Set environment variables early
    if 'RAG_ENABLED' not in os.environ:
        os.environ['RAG_ENABLED'] = 'false'
    if 'TTS_PROVIDER' not in os.environ:
        os.environ['TTS_PROVIDER'] = 'disabled'
    if 'GAME_STATE_REPO_TYPE' not in os.environ:
        os.environ['GAME_STATE_REPO_TYPE'] = 'memory'


@pytest.fixture(autouse=True, scope='function')
def reset_modules_between_tests():
    """
    Reset problematic modules between tests to avoid the _has_torch_function error.
    This fixture runs automatically before each test.
    """
    # Ensure container is reset before each test
    from app.core.container import reset_container
    reset_container()
    
    yield
    
    # Note: We no longer try to remove torch/numpy modules as this causes more problems
    # The global RAG service cache in container.py handles the reimport issue instead