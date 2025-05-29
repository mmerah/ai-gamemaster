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


@pytest.fixture(autouse=True)
def reset_modules_between_tests():
    """
    Reset problematic modules between tests to avoid the _has_torch_function error.
    This fixture runs automatically before each test.
    """
    # Modules that can cause issues when reloaded
    problematic_patterns = [
        'torch',
        'numpy', 
        'transformers',
        'sentence_transformers',
        'kokoro',
        'app.services.rag.knowledge_bases',
        'app.tts_services.kokoro_service',
    ]
    
    # Store current modules
    original_modules = dict(sys.modules)
    
    yield
    
    # After test, remove any newly imported problematic modules
    modules_to_remove = []
    for module_name in sys.modules:
        if module_name not in original_modules:
            for pattern in problematic_patterns:
                if module_name == pattern or module_name.startswith(pattern + '.'):
                    modules_to_remove.append(module_name)
                    break
    
    for module_name in modules_to_remove:
        sys.modules.pop(module_name, None)