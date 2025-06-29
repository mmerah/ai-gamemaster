"""
Combined character model (DTO).

This module contains the CombinedCharacterModel which merges template
and instance data for frontend consumption.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.shared.calculators.dice_mechanics import get_ability_modifier

if TYPE_CHECKING:
    from app.models.character.instance import CharacterInstanceModel
    from app.models.character.template import CharacterTemplateModel
from app.models.utils import (
    BaseStatsModel,
    ClassFeatureModel,
    ItemModel,
    ProficienciesModel,
    TraitModel,
)


class CombinedCharacterModel(BaseModel):
    """Data Transfer Object that combines character template and instance data.

    This DTO is used at the API boundary to provide a unified view of character
    data to the frontend. It merges static template data (class, race, etc.)
    with dynamic instance data (HP, conditions, etc.).

    Used by:
    - GameOrchestrator._format_party_for_frontend()
    - Game event responses (GameEventResponseModel)
    - Character API endpoints

    This is intentionally a denormalized model for frontend convenience.
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
    inventory: List[ItemModel] = Field(
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
        from app.domain.shared.calculators.dice_mechanics import get_proficiency_bonus

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
            name=instance.name,  # Use instance name to support character renaming
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
