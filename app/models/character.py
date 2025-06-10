"""
Character models.

This module contains all character-related models including templates and instances.
"""

from datetime import datetime
from typing import Dict, List, NamedTuple, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.game.calculators.dice_mechanics import get_ability_modifier

from .base import BaseModelWithDatetimeSerializer
from .utils import (
    BaseStatsModel,
    ClassFeatureModel,
    ItemModel,
    ProficienciesModel,
    TraitModel,
)


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


class CharacterTemplateModel(BaseModelWithDatetimeSerializer):
    """Complete character template matching JSON structure"""

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
    starting_equipment: List["ItemModel"] = Field(default_factory=list)
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

    model_config = ConfigDict(extra="forbid")


class CharacterInstanceModel(BaseModelWithDatetimeSerializer):
    """Character state within a specific campaign"""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Link to template
    template_id: str
    campaign_id: str

    # Current state
    current_hp: int
    max_hp: int
    temp_hp: int = 0

    # Experience
    experience_points: int = 0
    level: int = Field(ge=1, le=20)

    # Resources
    spell_slots_used: Dict[int, int] = Field(
        default_factory=dict
    )  # level -> used slots
    hit_dice_used: int = 0
    death_saves: Dict[str, int] = Field(
        default_factory=lambda: {"successes": 0, "failures": 0}
    )

    # Inventory (extends starting equipment)
    inventory: List[ItemModel] = Field(default_factory=list)
    gold: int = 0

    # Conditions & Effects
    conditions: List[str] = Field(default_factory=list)
    exhaustion_level: int = Field(ge=0, le=6, default=0)

    # Campaign-specific data
    notes: str = ""
    achievements: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(
        default_factory=dict
    )  # NPC ID -> relationship

    # Last activity
    last_played: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(extra="forbid")


class CombinedCharacterModel(BaseModel):
    """Combined character model for frontend consumption.

    This model merges CharacterTemplateModel and CharacterInstanceModel data
    to provide a complete view of a character for the frontend.
    """

    # From instance
    id: str = Field(..., description="Character ID (from instance)")
    template_id: str = Field(..., description="Reference to character template")
    campaign_id: str = Field(..., description="Campaign this instance belongs to")

    # From template - identity
    name: str = Field(..., description="Character name")
    race: str = Field(..., description="Character race")
    subrace: Optional[str] = Field(None, description="Character subrace")
    char_class: str = Field(..., description="Character class", alias="class")
    subclass: Optional[str] = Field(None, description="Character subclass")
    background: str = Field(..., description="Character background")
    alignment: str = Field(..., description="Character alignment")

    # From instance - current state
    current_hp: int = Field(..., description="Current hit points")
    max_hp: int = Field(..., description="Maximum hit points")
    temp_hp: int = Field(0, description="Temporary hit points")
    level: int = Field(..., description="Current level")
    experience_points: int = Field(
        0, description="Experience points", alias="experience"
    )

    # From template - base stats
    base_stats: BaseStatsModel = Field(..., description="Base ability scores")
    armor_class: int = Field(..., description="Armor class", alias="ac")

    # From instance - conditions and resources
    conditions: List[str] = Field(default_factory=list, description="Active conditions")
    spell_slots_used: Dict[int, int] = Field(
        default_factory=dict, description="Used spell slots by level"
    )
    hit_dice_used: int = Field(0, description="Number of hit dice used")
    death_saves: Dict[str, int] = Field(
        default_factory=lambda: {"successes": 0, "failures": 0}
    )
    exhaustion_level: int = Field(0, description="Exhaustion level (0-6)")

    # From instance - inventory
    inventory: List["ItemModel"] = Field(
        default_factory=list, description="Current inventory"
    )
    gold: int = Field(0, description="Current gold pieces")

    # From template - proficiencies and features
    proficiencies: ProficienciesModel = Field(
        ..., description="Character proficiencies"
    )
    languages: List[str] = Field(default_factory=list, description="Known languages")
    racial_traits: List[TraitModel] = Field(
        default_factory=list, description="Racial traits"
    )
    class_features: List[ClassFeatureModel] = Field(
        default_factory=list, description="Class features"
    )
    feats: List[TraitModel] = Field(default_factory=list, description="Character feats")

    # From template - spells
    spells_known: List[str] = Field(default_factory=list, description="Known spells")
    cantrips_known: List[str] = Field(
        default_factory=list, description="Known cantrips"
    )

    # From template - appearance
    portrait_path: Optional[str] = Field(None, description="Path to character portrait")

    # Computed/derived fields for frontend compatibility
    hp: int = Field(..., description="Alias for current_hp")
    maximum_hp: int = Field(..., description="Alias for max_hp")

    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on level."""
        from app.game.calculators.dice_mechanics import get_proficiency_bonus

        return get_proficiency_bonus(self.level)

    @classmethod
    def from_template_and_instance(
        cls,
        template: "CharacterTemplateModel",
        instance: "CharacterInstanceModel",
        character_id: str,
    ) -> "CombinedCharacterModel":
        """Create a combined model from template and instance data."""
        # Calculate derived stats
        dex_mod = get_ability_modifier(template.base_stats.DEX)
        base_ac = 10 + dex_mod  # Simplified AC calculation

        return cls(
            # Identity
            id=character_id,
            template_id=instance.template_id,
            campaign_id=instance.campaign_id,
            # From template
            name=template.name,
            race=template.race,
            subrace=template.subrace,
            char_class=template.char_class,
            subclass=template.subclass,
            background=template.background,
            alignment=template.alignment,
            base_stats=template.base_stats,
            armor_class=base_ac,
            proficiencies=template.proficiencies,
            languages=template.languages,
            racial_traits=template.racial_traits,
            class_features=template.class_features,
            feats=template.feats,
            spells_known=template.spells_known,
            cantrips_known=template.cantrips_known,
            portrait_path=template.portrait_path,
            # From instance
            current_hp=instance.current_hp,
            max_hp=instance.max_hp,
            temp_hp=instance.temp_hp,
            level=instance.level,
            experience_points=instance.experience_points,
            conditions=instance.conditions,
            spell_slots_used=instance.spell_slots_used,
            hit_dice_used=instance.hit_dice_used,
            death_saves=instance.death_saves,
            exhaustion_level=instance.exhaustion_level,
            inventory=instance.inventory,
            gold=instance.gold,
            # Aliases for frontend compatibility
            hp=instance.current_hp,
            maximum_hp=instance.max_hp,
        )

    model_config = ConfigDict(populate_by_name=True)


class CharacterData(NamedTuple):
    """Combined character data from template and instance."""

    template: CharacterTemplateModel
    instance: CharacterInstanceModel
    character_id: str
