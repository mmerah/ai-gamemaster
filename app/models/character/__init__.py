"""
Character models package.

This package contains all character-related models organized into logical modules:
- template.py: CharacterTemplateModel (static character data)
- instance.py: CharacterInstanceModel (dynamic character state)
- combined.py: CombinedCharacterModel (DTO for frontend)
- utils.py: Utility models and data structures
"""

from app.models.character.combined import CombinedCharacterModel
from app.models.character.instance import CharacterInstanceModel
from app.models.character.template import CharacterTemplateModel
from app.models.character.utils import CharacterData, CharacterModifierDataModel

__all__ = [
    "CharacterTemplateModel",
    "CharacterInstanceModel",
    "CombinedCharacterModel",
    "CharacterModifierDataModel",
    "CharacterData",
]
