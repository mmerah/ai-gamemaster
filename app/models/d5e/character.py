"""Character option models for D&D 5e.

This module contains models for character creation options including classes,
subclasses, races, subraces, backgrounds, feats, and traits.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.models.d5e.base import APIReference, Choice


class StartingEquipmentOption(BaseModel):
    """Represents an equipment choice during character creation."""

    desc: Optional[str] = Field(None, description="Description of the choice")
    choose: int = Field(..., description="Number of options to choose")
    type: str = Field(..., description="Type of choice")
    from_: Dict[str, Any] = Field(
        ..., alias="from", description="Options to choose from"
    )


class StartingEquipment(BaseModel):
    """Represents guaranteed starting equipment."""

    equipment: APIReference = Field(..., description="The equipment item")
    quantity: int = Field(..., description="Number of items")


class AbilityBonus(BaseModel):
    """Represents an ability score bonus from race."""

    ability_score: APIReference = Field(..., description="The ability score")
    bonus: int = Field(..., description="Bonus amount")


class SpellcastingInfo(BaseModel):
    """Represents spellcasting information for a spell slot."""

    name: str = Field(..., description="Type of spell (e.g., Cantrips Known)")
    desc: List[str] = Field(default_factory=list, description="Description paragraphs")
    count: Optional[int] = Field(None, description="Number of spells/slots")
    level: Optional[int] = Field(None, description="Spell level")


class Spellcasting(BaseModel):
    """Represents spellcasting details for a class."""

    level: int = Field(..., description="Level when spellcasting is gained")
    spellcasting_ability: APIReference = Field(
        ..., description="Ability used for spellcasting"
    )
    info: List[SpellcastingInfo] = Field(
        default_factory=list, description="Spell slot and known spell info"
    )


class MultiClassingPrereq(BaseModel):
    """Represents multiclassing prerequisites."""

    ability_score: APIReference = Field(..., description="Required ability score")
    minimum_score: int = Field(..., description="Minimum score needed")


class MultiClassingProficiency(BaseModel):
    """Represents proficiencies gained from multiclassing."""

    proficiencies: List[APIReference] = Field(
        default_factory=list, description="Proficiencies gained"
    )
    proficiency_choices: Optional[Choice] = Field(
        None, description="Proficiency choices"
    )


class MultiClassing(BaseModel):
    """Represents multiclassing rules for a class."""

    prerequisites: Optional[List[MultiClassingPrereq]] = Field(
        None, description="Ability score prerequisites"
    )
    prerequisite_options: Optional[Choice] = Field(
        None, description="Alternative prerequisites"
    )
    proficiencies: Optional[List[APIReference]] = Field(
        None, description="Proficiencies gained"
    )
    proficiency_choices: Optional[List[Choice]] = Field(
        None, description="Proficiency choices"
    )


class D5eClass(BaseModel):
    """Represents a character class in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    hit_die: int = Field(..., description="Hit die size")
    proficiency_choices: List[Choice] = Field(
        default_factory=list, description="Skill/tool proficiency choices"
    )
    proficiencies: List[APIReference] = Field(
        default_factory=list, description="Starting proficiencies"
    )
    saving_throws: List[APIReference] = Field(
        default_factory=list, description="Proficient saving throws"
    )
    starting_equipment: List[StartingEquipment] = Field(
        default_factory=list, description="Guaranteed starting equipment"
    )
    starting_equipment_options: List[StartingEquipmentOption] = Field(
        default_factory=list, description="Equipment choices"
    )
    class_levels: str = Field(..., description="URL to class level progression")
    multi_classing: Optional[MultiClassing] = Field(
        None, description="Multiclassing rules"
    )
    subclasses: List[APIReference] = Field(
        default_factory=list, description="Available subclasses"
    )
    spellcasting: Optional[Spellcasting] = Field(
        None, description="Spellcasting details"
    )
    spells: Optional[str] = Field(None, description="URL to class spell list")
    url: str = Field(..., description="API endpoint URL")


class D5eSubclass(BaseModel):
    """Represents a subclass/archetype in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    class_: APIReference = Field(
        ..., alias="class", description="Parent class"
    )  # 'class' is reserved
    name: str = Field(..., description="Display name")
    subclass_flavor: str = Field(..., description="Flavor text for subclass type")
    desc: List[str] = Field(..., description="Description paragraphs")
    subclass_levels: str = Field(..., description="URL to subclass level progression")
    spells: Optional[Union[str, List[Dict[str, Any]]]] = Field(
        None, description="URL to subclass spell list or list of spell objects"
    )
    url: str = Field(..., description="API endpoint URL")


class D5eRace(BaseModel):
    """Represents a character race in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    speed: int = Field(..., description="Base walking speed in feet")
    ability_bonuses: List[AbilityBonus] = Field(
        default_factory=list, description="Ability score improvements"
    )
    ability_bonus_options: Optional[Choice] = Field(
        None, description="Choice of ability bonuses"
    )
    alignment: str = Field(..., description="Typical alignment description")
    age: str = Field(..., description="Age description")
    size: str = Field(..., description="Size category")
    size_description: str = Field(..., description="Size details")
    starting_proficiencies: List[APIReference] = Field(
        default_factory=list, description="Racial proficiencies"
    )
    starting_proficiency_options: Optional[Choice] = Field(
        None, description="Proficiency choices"
    )
    languages: List[APIReference] = Field(
        default_factory=list, description="Languages known"
    )
    language_options: Optional[Choice] = Field(None, description="Language choices")
    language_desc: str = Field(..., description="Language description")
    traits: List[APIReference] = Field(
        default_factory=list, description="Racial traits"
    )
    subraces: List[APIReference] = Field(
        default_factory=list, description="Available subraces"
    )
    url: str = Field(..., description="API endpoint URL")


class D5eSubrace(BaseModel):
    """Represents a subrace in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    race: APIReference = Field(..., description="Parent race")
    desc: str = Field(..., description="Description")
    ability_bonuses: List[AbilityBonus] = Field(
        default_factory=list, description="Additional ability bonuses"
    )
    ability_bonus_options: Optional[Choice] = Field(
        None, description="Choice of ability bonuses"
    )
    starting_proficiencies: List[APIReference] = Field(
        default_factory=list, description="Additional proficiencies"
    )
    starting_proficiency_options: Optional[Choice] = Field(
        None, description="Proficiency choices"
    )
    languages: List[APIReference] = Field(
        default_factory=list, description="Additional languages"
    )
    language_options: Optional[Choice] = Field(None, description="Language choices")
    racial_traits: List[APIReference] = Field(
        default_factory=list, description="Subrace traits"
    )
    racial_trait_options: Optional[Choice] = Field(None, description="Trait choices")
    url: str = Field(..., description="API endpoint URL")


class PersonalityChoice(BaseModel):
    """Represents personality trait choices for backgrounds."""

    choose: int = Field(..., description="Number to choose")
    type: str = Field(..., description="Type of choice")
    from_: List[str] = Field(..., alias="from", description="Options")


class Feature(BaseModel):
    """Represents a background feature."""

    name: str = Field(..., description="Feature name")
    desc: List[str] = Field(..., description="Feature description")


class D5eBackground(BaseModel):
    """Represents a character background in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    starting_proficiencies: List[APIReference] = Field(
        default_factory=list, description="Skill proficiencies"
    )
    language_options: Optional[Choice] = Field(None, description="Language choices")
    starting_equipment: List[StartingEquipment] = Field(
        default_factory=list, description="Starting equipment"
    )
    starting_equipment_options: List[StartingEquipmentOption] = Field(
        default_factory=list, description="Equipment choices"
    )
    feature: Feature = Field(..., description="Background feature")
    personality_traits: Choice = Field(..., description="Personality trait options")
    ideals: Choice = Field(..., description="Ideal options")
    bonds: Choice = Field(..., description="Bond options")
    flaws: Choice = Field(..., description="Flaw options")
    url: str = Field(..., description="API endpoint URL")


class D5eFeat(BaseModel):
    """Represents a feat in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    prerequisites: List[Dict[str, Any]] = Field(
        default_factory=list, description="Prerequisites"
    )
    desc: List[str] = Field(..., description="Description paragraphs")
    url: str = Field(..., description="API endpoint URL")


class D5eTrait(BaseModel):
    """Represents a racial trait in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    races: List[APIReference] = Field(
        default_factory=list, description="Races with this trait"
    )
    subraces: List[APIReference] = Field(
        default_factory=list, description="Subraces with this trait"
    )
    name: str = Field(..., description="Display name")
    desc: List[str] = Field(..., description="Description paragraphs")
    proficiencies: List[APIReference] = Field(
        default_factory=list, description="Granted proficiencies"
    )
    proficiency_choices: Optional[Choice] = Field(
        None, description="Proficiency choices"
    )
    language_options: Optional[Choice] = Field(None, description="Language choices")
    trait_specific: Optional[Dict[str, Any]] = Field(
        None, description="Trait-specific data"
    )
    url: str = Field(..., description="API endpoint URL")
