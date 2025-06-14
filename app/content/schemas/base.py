"""Base models for D&D 5e data.

This module contains the fundamental models used across all D&D 5e data types,
including the APIReference model for cross-references and common structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class APIReference(BaseModel):
    """Represents a reference to another entity in the 5e database.

    This is the most fundamental model, used throughout the data to link
    related entities together. References always have exactly these three fields.
    """

    index: str = Field(..., description="Unique identifier for the referenced item")
    name: str = Field(..., description="Display name of the referenced item")
    url: str = Field(..., description="API endpoint URL for the full item data")

    model_config = ConfigDict(frozen=True)  # References should be immutable


class Cost(BaseModel):
    """Represents the cost of an item or service."""

    quantity: int = Field(..., description="Amount of currency")
    unit: str = Field(..., description="Currency type (cp, sp, ep, gp, pp)")


class DC(BaseModel):
    """Represents a difficulty class for saving throws or ability checks."""

    dc_type: APIReference = Field(..., description="Type of save (ability score)")
    dc_value: Optional[int] = Field(None, description="Fixed DC value")
    success_type: Optional[str] = Field(
        None, description="Effect on successful save (none, half)"
    )


class Damage(BaseModel):
    """Represents damage dealt by a spell, attack, or effect."""

    damage_type: Optional[APIReference] = Field(
        None, description="Type of damage dealt"
    )
    damage_dice: Optional[str] = Field(None, description="Dice expression (e.g., 2d6)")


class DamageAtLevel(BaseModel):
    """Represents damage that scales with spell slot or character level."""

    damage_type: Optional[APIReference] = Field(
        None, description="Type of damage dealt"
    )
    damage_at_slot_level: Optional[Dict[str, str]] = Field(
        None, description="Damage by spell slot level"
    )
    damage_at_character_level: Optional[Dict[str, str]] = Field(
        None, description="Damage by character level (cantrips)"
    )


class Usage(BaseModel):
    """Represents how often an ability can be used."""

    type: str = Field(..., description="Recharge type (per day, recharge, etc.)")
    dice: Optional[str] = Field(None, description="Dice to roll for recharge")
    min_value: Optional[int] = Field(
        None, description="Minimum value needed to recharge"
    )
    times: Optional[int] = Field(None, description="Number of uses")
    rest_types: Optional[List[str]] = Field(
        None, description="Types of rest that restore uses"
    )


class OptionSet(BaseModel):
    """Represents a set of options for equipment or features.

    This is used in the 'from' field of choices to define complex option sets.
    """

    option_set_type: str = Field(..., description="Type of options")
    options: Optional[List[Any]] = Field(None, description="List of available options")
    equipment_category: Optional[APIReference] = Field(
        None, description="Category for equipment options"
    )
    resource_list_url: Optional[str] = Field(
        None, description="URL to full list of options"
    )


class ChoiceOption(BaseModel):
    """Represents a single option in a choice."""

    option_type: str = Field(..., description="Type of option")
    item: Optional[APIReference] = Field(None, description="Reference to chosen item")
    choice: Optional["Choice"] = Field(None, description="Nested choice")
    string: Optional[str] = Field(None, description="String option")
    desc: Optional[str] = Field(None, description="Description of option")
    alignments: Optional[List[APIReference]] = Field(
        None, description="Alignment options"
    )
    count: Optional[int] = Field(None, description="Number to choose")
    of: Optional[APIReference] = Field(None, description="Item to count")
    ability_score: Optional[APIReference] = Field(
        None, description="Ability score option"
    )
    minimum: Optional[int] = Field(None, description="Minimum value")
    maximum: Optional[int] = Field(None, description="Maximum value")
    bonus: Optional[int] = Field(None, description="Bonus value")


class Choice(BaseModel):
    """Represents a choice to be made (skills, equipment, etc.)."""

    desc: Optional[str] = Field(None, description="Description of the choice")
    choose: int = Field(..., description="Number of options to choose")
    type: str = Field(..., description="Type of choice")
    from_: Optional[OptionSet] = Field(
        None, alias="from", description="Options to choose from"
    )

    @model_validator(mode="before")
    @classmethod
    def handle_from_field_variants(cls, data: Any) -> Any:
        """Handle different forms of 'from' field in choice data.

        The JSON data sometimes has 'from' directly, sometimes 'from_'.
        Since the field has alias="from", we should let Pydantic handle the alias naturally.
        """
        if isinstance(data, dict):
            # The field has alias="from", so Pydantic will handle "from" -> "from_" automatically
            # We only need to handle the case where we have "from_" but not "from"
            if "from_" in data and "from" not in data:
                # Move from_ to from so the alias can pick it up
                data["from"] = data.pop("from_")
        return data


# Update forward references
ChoiceOption.model_rebuild()
