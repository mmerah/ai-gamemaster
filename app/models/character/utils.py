"""
Character utility models.

This module contains utility models and data structures used by character models.
"""

from typing import TYPE_CHECKING, Dict, List, NamedTuple

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.models.character.instance import CharacterInstanceModel
    from app.models.character.template import CharacterTemplateModel


class CharacterModifierDataModel(BaseModel):
    """Data structure for calculating character modifiers."""

    stats: Dict[str, int] = Field(
        ..., description="Ability scores like {'STR': 14, 'DEX': 16, ...}"
    )
    proficiencies: Dict[str, List[str]] = Field(
        ..., description="Proficiencies like {'skills': [...], 'armor': [...]}"
    )
    level: int = Field(..., description="Character level")

    model_config = ConfigDict(extra="forbid")


class CharacterData(NamedTuple):
    """Combined character data from template and instance.

    This is a simple data container used internally when both template
    and instance data need to be passed together. Not exposed to API.
    """

    template: "CharacterTemplateModel"
    instance: "CharacterInstanceModel"
    character_id: str
