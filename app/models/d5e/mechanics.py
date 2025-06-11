"""Core game mechanics models for D&D 5e.

This module contains models for fundamental game mechanics like ability scores,
skills, proficiencies, conditions, damage types, languages, and alignments.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.d5e.base import APIReference


class D5eAbilityScore(BaseModel):
    """Represents one of the six ability scores in D&D 5e."""

    index: str = Field(..., description="Unique identifier (str, dex, con, etc.)")
    name: str = Field(..., description="Abbreviated name (STR, DEX, CON, etc.)")
    full_name: str = Field(..., description="Full name (Strength, Dexterity, etc.)")
    desc: List[str] = Field(..., description="Description paragraphs")
    skills: List[APIReference] = Field(
        default_factory=list, description="Skills based on this ability"
    )
    url: str = Field(..., description="API endpoint URL")


class D5eSkill(BaseModel):
    """Represents a skill in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    desc: List[str] = Field(..., description="Description paragraphs")
    ability_score: APIReference = Field(..., description="Associated ability score")
    url: str = Field(..., description="API endpoint URL")


class D5eProficiency(BaseModel):
    """Represents a proficiency (weapon, armor, tool, skill, etc.)."""

    index: str = Field(..., description="Unique identifier")
    type: str = Field(
        ...,
        description="Type of proficiency (Armor, Weapons, Tools, Skills, etc.)",
    )
    name: str = Field(..., description="Display name")
    classes: List[APIReference] = Field(
        default_factory=list, description="Classes that grant this proficiency"
    )
    races: List[APIReference] = Field(
        default_factory=list, description="Races that grant this proficiency"
    )
    url: str = Field(..., description="API endpoint URL")
    reference: Optional[APIReference] = Field(
        None, description="Reference to the actual item/skill"
    )


class D5eCondition(BaseModel):
    """Represents a status condition in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    desc: List[str] = Field(..., description="Description paragraphs")
    url: str = Field(..., description="API endpoint URL")


class D5eDamageType(BaseModel):
    """Represents a type of damage in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    desc: List[str] = Field(..., description="Description paragraphs")
    url: str = Field(..., description="API endpoint URL")


class D5eLanguage(BaseModel):
    """Represents a language in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    type: str = Field(..., description="Language type (Standard, Exotic, etc.)")
    typical_speakers: List[str] = Field(
        default_factory=list, description="Races/creatures that speak this language"
    )
    script: Optional[str] = Field(None, description="Writing system used")
    url: str = Field(..., description="API endpoint URL")


class D5eAlignment(BaseModel):
    """Represents an alignment in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    abbreviation: str = Field(..., description="Two-letter abbreviation")
    desc: str = Field(..., description="Description")
    url: str = Field(..., description="API endpoint URL")
