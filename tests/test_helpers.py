"""
Test helper utilities to ensure proper test isolation.
"""
import os
import sys
from typing import List, Set
from unittest import mock


def ensure_clean_imports():
    """
    Ensure clean imports by removing potentially problematic modules.
    This helps avoid the '_has_torch_function' error when tests reload modules.
    """
    # Modules that can cause issues when reloaded
    problematic_modules = [
        'torch',
        'numpy',
        'transformers',
        'sentence_transformers',
        'kokoro',
        'app.services.rag.knowledge_bases',
        'app.tts_services.kokoro_service',
    ]
    
    # Get current module names to avoid modifying dict during iteration
    current_modules = list(sys.modules.keys())
    
    for module in current_modules:
        # Remove problematic modules and their submodules
        for prob_module in problematic_modules:
            if module == prob_module or module.startswith(prob_module + '.'):
                sys.modules.pop(module, None)


def setup_test_environment():
    """
    Set up a clean test environment with proper configuration.
    """
    # Set environment variables before any imports
    os.environ['RAG_ENABLED'] = 'false'
    os.environ['TTS_PROVIDER'] = 'disabled'
    
    # Clean up any previously imported modules
    ensure_clean_imports()


class IsolatedTestCase:
    """
    Mixin for test cases that need proper isolation from ML dependencies.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level test isolation."""
        setup_test_environment()
        super().setUpClass()
    
    def setUp(self):
        """Set up test-level isolation."""
        # Ensure environment is clean for each test
        os.environ['RAG_ENABLED'] = 'false'
        os.environ['TTS_PROVIDER'] = 'disabled'
        super().setUp()