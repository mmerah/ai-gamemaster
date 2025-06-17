"""
Game event models - DEPRECATED.

This module has been reorganized into the app.models.events package.
Please import from the specific submodules:
- app.models.events.base for BaseGameEvent
- app.models.events.narrative for narrative events
- app.models.events.combat for combat events
- app.models.events.dice for dice events
- app.models.events.game_state for game state events
- app.models.events.system for system events
- app.models.events.utils for utility models

This file is maintained for backward compatibility only.
"""

import warnings

warnings.warn(
    "Importing from app.models.events is deprecated. "
    "Use app.models.events.base, app.models.events.narrative, "
    "app.models.events.combat, etc. instead. "
    "This compatibility layer will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all models for backward compatibility
from app.models.events import *  # noqa: F401, F403
