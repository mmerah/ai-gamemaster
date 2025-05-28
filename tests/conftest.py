"""
Test configuration to reduce logging noise during testing.
"""
import logging
import os
import sys

def setup_test_logging():
    """Configure logging for tests to reduce noise."""
    # Set logging level to WARNING or higher to reduce noise
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )
    
    # Specifically silence verbose loggers
    verbose_loggers = [
        'app.services.rag',
        'app.ai_services',
        'app.services.game_events',
        'app.game.calculators',
        'app.repositories',
        'urllib3',
        'requests'
    ]
    
    for logger_name in verbose_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)

def get_test_config():
    """Get default configuration for tests."""
    return {
        'GAME_STATE_REPO_TYPE': 'memory',
        'TTS_PROVIDER': 'disabled',
        'RAG_ENABLED': False  # Disable RAG by default for faster tests
    }

# Automatically set up logging when this module is imported
if 'unittest' in sys.modules or 'pytest' in sys.modules or 'test' in sys.argv[0]:
    setup_test_logging()
