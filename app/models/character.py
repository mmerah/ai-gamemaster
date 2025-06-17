"""
Character models - DEPRECATED.

This module has been reorganized into the app.models.character package.
Please import from the specific submodules:
- app.models.character.template for CharacterTemplateModel
- app.models.character.instance for CharacterInstanceModel
- app.models.character.combined for CombinedCharacterModel
- app.models.character.utils for utility models

This file is maintained for backward compatibility only.
"""

import warnings

warnings.warn(
    "Importing from app.models.character is deprecated. "
    "Use app.models.character.template, app.models.character.instance, "
    "app.models.character.combined, or app.models.character.utils instead. "
    "This compatibility layer will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all models for backward compatibility
from app.models.character import *  # noqa: F401, F403
