"""
Game event handler - DEPRECATED

This file has been refactored into a modular structure:
- app/services/game_events/game_event_manager.py - Main coordinator
- app/services/game_events/handlers/ - Individual event handlers
- app/utils/validation/action_validators.py - Validation logic

All functionality has been preserved and migrated to the new structure.
The container now uses GameEventManager instead of GameEventHandlerImpl.
"""

# This file is kept for backwards compatibility but should not be used.
# All imports should use the new structure.

import warnings

def __getattr__(name):
    if name == 'GameEventHandlerImpl':
        warnings.warn(
            "GameEventHandlerImpl has been refactored. Use GameEventManager from "
            "app.services.game_events.game_event_manager instead.",
            DeprecationWarning,
            stacklevel=2
        )
        from app.services.game_events.game_event_manager import GameEventManager
        return GameEventManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
