"""
Combat models - DEPRECATED.

This module has been reorganized into the app.models.combat package.
Please import from the specific submodules:
- app.models.combat.attack for AttackModel
- app.models.combat.combatant for CombatantModel and InitialCombatantData
- app.models.combat.state for CombatStateModel and NextCombatantInfoModel
- app.models.combat.response for CombatInfoResponseModel

This file is maintained for backward compatibility only.
"""

import warnings

warnings.warn(
    "Importing from app.models.combat is deprecated. "
    "Use app.models.combat.attack, app.models.combat.combatant, "
    "app.models.combat.state, or app.models.combat.response instead. "
    "This compatibility layer will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all models for backward compatibility
from app.models.combat import *  # noqa: F401, F403
