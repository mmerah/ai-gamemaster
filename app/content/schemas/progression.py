"""Character progression models for D&D 5e.

This module contains models for character level progression including
class features and level-specific data.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field

from app.content.schemas.base import APIReference


class Prerequisite(BaseModel):
    """Represents a prerequisite for a feature."""

    type: str = Field(..., description="Type of prerequisite (level, feature, etc.)")
    level: Optional[int] = Field(None, description="Required level")
    feature: Optional[str] = Field(None, description="Required feature")


class D5eFeature(BaseModel):
    """Represents a class or subclass feature in D&D 5e.

    Note: This corresponds to the 5e-SRD-Features.json file which contains
    thousands of features across all classes and levels.
    """

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    level: int = Field(..., description="Level when feature is gained")
    class_: APIReference = Field(
        ..., alias="class", description="Class that grants this feature"
    )
    subclass: Optional[APIReference] = Field(None, description="Subclass if applicable")
    desc: List[str] = Field(..., description="Description paragraphs")
    prerequisites: List[Prerequisite] = Field(
        default_factory=list, description="Prerequisites for this feature"
    )
    parent: Optional[APIReference] = Field(
        None, description="Parent feature (for sub-features)"
    )
    reference: Optional[str] = Field(
        None, description="Reference to spell or other content"
    )
    feature_specific: Optional[Dict[str, Any]] = Field(
        None, description="Feature-specific data"
    )
    url: str = Field(..., description="API endpoint URL")


class SpellSlotInfo(BaseModel):
    """Represents spell slot information at a specific level."""

    spell_slots_level_1: Optional[int] = Field(None, description="1st level slots")
    spell_slots_level_2: Optional[int] = Field(None, description="2nd level slots")
    spell_slots_level_3: Optional[int] = Field(None, description="3rd level slots")
    spell_slots_level_4: Optional[int] = Field(None, description="4th level slots")
    spell_slots_level_5: Optional[int] = Field(None, description="5th level slots")
    spell_slots_level_6: Optional[int] = Field(None, description="6th level slots")
    spell_slots_level_7: Optional[int] = Field(None, description="7th level slots")
    spell_slots_level_8: Optional[int] = Field(None, description="8th level slots")
    spell_slots_level_9: Optional[int] = Field(None, description="9th level slots")


class D5eLevel(BaseModel):
    """Represents level progression data for a specific class.

    Note: This corresponds to the 5e-SRD-Levels.json file which contains
    level progression tables for all classes.
    """

    level: int = Field(..., description="Character level")
    ability_score_bonuses: Optional[int] = Field(
        None, description="Total ability score improvements"
    )
    prof_bonus: Optional[int] = Field(None, description="Proficiency bonus")
    features: List[APIReference] = Field(
        default_factory=list, description="Features gained at this level"
    )
    spellcasting: Optional[SpellSlotInfo] = Field(
        None, description="Spell slots for spellcasting classes"
    )
    class_specific: Optional[Dict[str, Any]] = Field(
        None, description="Class-specific progression data"
    )
    index: str = Field(..., description="Unique identifier (class-level)")
    class_: Optional[APIReference] = Field(None, alias="class", description="The class")
    subclass: Optional[APIReference] = Field(
        None, description="The subclass (for subclass levels)"
    )
    url: str = Field(..., description="API endpoint URL")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name(self) -> str:
        """Generate name from index."""
        # Convert index like "barbarian-1" to "Barbarian 1"
        parts = self.index.split("-")
        if len(parts) >= 2 and parts[-1].isdigit():
            class_name = "-".join(parts[:-1]).title()
            return f"{class_name} {parts[-1]}"
        return self.index.title()


class D5eClassLevel(BaseModel):
    """Represents the complete level progression for a class.

    This is the container that holds all levels for a specific class.
    """

    class_: str = Field(..., alias="class", description="Class name")
    levels: List[D5eLevel] = Field(..., description="Level progression from 1-20")
