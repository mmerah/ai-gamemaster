"""
Character template model.

This module contains the CharacterTemplateModel which defines the static,
unchanging aspects of a character (race, class, background, etc.).
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple

from pydantic import ConfigDict, Field

from app.models.base import BaseModelWithDatetimeSerializer
from app.models.utils import (
    BaseStatsModel,
    ClassFeatureModel,
    ItemModel,
    ProficienciesModel,
    TraitModel,
)

if TYPE_CHECKING:
    from app.domain.validators.content_validator import (
        ContentValidationError,
        ContentValidator,
    )


class CharacterTemplateModel(BaseModelWithDatetimeSerializer):
    """Character template that defines the base character attributes.

    This model represents the static, unchanging aspects of a character
    (race, class, background, etc.) that are defined during character creation.
    Templates are reusable across multiple campaign instances.
    """

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Identity
    id: str
    name: str
    race: str
    subrace: Optional[str] = None
    char_class: str
    subclass: Optional[str] = None
    level: int = Field(ge=1, le=20, default=1)
    background: str
    alignment: str

    # Stats & Mechanics
    base_stats: BaseStatsModel
    proficiencies: ProficienciesModel
    languages: List[str] = Field(default_factory=list)

    # Traits & Features
    racial_traits: List[TraitModel] = Field(default_factory=list)
    class_features: List[ClassFeatureModel] = Field(default_factory=list)
    feats: List[TraitModel] = Field(default_factory=list)

    # Spellcasting
    spells_known: List[str] = Field(default_factory=list)
    cantrips_known: List[str] = Field(default_factory=list)

    # Equipment
    starting_equipment: List[ItemModel] = Field(default_factory=list)
    starting_gold: int = Field(ge=0, default=0)

    # Character Details
    portrait_path: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list, max_length=2)
    ideals: List[str] = Field(default_factory=list)
    bonds: List[str] = Field(default_factory=list)
    flaws: List[str] = Field(default_factory=list)
    appearance: Optional[str] = None
    backstory: Optional[str] = None

    # Metadata
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None

    # Content Management
    content_pack_ids: List[str] = Field(
        default_factory=lambda: ["dnd_5e_srd"],
        description="Content pack IDs available for this character template",
    )

    model_config = ConfigDict(extra="forbid")

    def validate_content(
        self, validator: "ContentValidator"
    ) -> Tuple[bool, List["ContentValidationError"]]:
        """Validate all D&D 5e content references in this character template.

        Args:
            validator: The content validator to use

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return validator.validate_character_template(self, self.content_pack_ids)


class CharacterTemplateUpdateModel(BaseModelWithDatetimeSerializer):
    """Update model for character templates with all fields optional.

    This model is used for PATCH endpoints where only specific fields
    need to be updated. All fields are optional except for those that
    shouldn't be changed (like id, created_date).
    """

    # Identity - most can be updated
    name: Optional[str] = None
    race: Optional[str] = None
    subrace: Optional[str] = None
    char_class: Optional[str] = None
    subclass: Optional[str] = None
    level: Optional[int] = Field(None, ge=1, le=20)
    background: Optional[str] = None
    alignment: Optional[str] = None

    # Stats & Mechanics
    base_stats: Optional[BaseStatsModel] = None
    proficiencies: Optional[ProficienciesModel] = None
    languages: Optional[List[str]] = None

    # Traits & Features
    racial_traits: Optional[List[TraitModel]] = None
    class_features: Optional[List[ClassFeatureModel]] = None
    feats: Optional[List[TraitModel]] = None

    # Spellcasting
    spells_known: Optional[List[str]] = None
    cantrips_known: Optional[List[str]] = None

    # Equipment
    starting_equipment: Optional[List[ItemModel]] = None
    starting_gold: Optional[int] = Field(None, ge=0)

    # Character Details
    portrait_path: Optional[str] = None
    personality_traits: Optional[List[str]] = Field(None, max_length=2)
    ideals: Optional[List[str]] = None
    bonds: Optional[List[str]] = None
    flaws: Optional[List[str]] = None
    appearance: Optional[str] = None
    backstory: Optional[str] = None

    # Content Management
    content_pack_ids: Optional[List[str]] = None

    model_config = ConfigDict(extra="forbid")
