"""Spell and monster models for D&D 5e.

This module contains models for spells and monsters, the two largest
data sets in the 5e database.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.content.schemas.base import DC, APIReference, Damage, DamageAtLevel, Usage


class D5eSpell(BaseModel):
    """Represents a spell in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    desc: List[str] = Field(..., description="Description paragraphs")
    higher_level: Optional[List[str]] = Field(
        None, description="Effects at higher levels"
    )
    range: str = Field(..., description="Spell range")
    components: List[str] = Field(..., description="Components required (V, S, M)")
    material: Optional[str] = Field(None, description="Material component details")
    ritual: bool = Field(..., description="Can be cast as ritual")
    duration: str = Field(..., description="Spell duration")
    concentration: bool = Field(..., description="Requires concentration")
    casting_time: str = Field(..., description="Time to cast")
    level: int = Field(..., description="Spell level (0 for cantrips)")
    attack_type: Optional[str] = Field(None, description="Melee or ranged")
    damage: Optional[DamageAtLevel] = Field(None, description="Damage dealt")
    heal_at_slot_level: Optional[Dict[str, str]] = Field(
        None, description="Healing by spell slot"
    )
    dc: Optional[DC] = Field(None, description="Saving throw info")
    area_of_effect: Optional[Dict[str, Any]] = Field(
        None, description="Area of effect details"
    )
    school: APIReference = Field(..., description="School of magic")
    classes: List[APIReference] = Field(
        default_factory=list, description="Classes that can cast"
    )
    subclasses: List[APIReference] = Field(
        default_factory=list, description="Subclasses that can cast"
    )
    url: str = Field(..., description="API endpoint URL")


class MonsterSpeed(BaseModel):
    """Represents movement speeds for a monster."""

    walk: Optional[str] = Field(None, description="Walking speed")
    swim: Optional[str] = Field(None, description="Swimming speed")
    fly: Optional[str] = Field(None, description="Flying speed")
    burrow: Optional[str] = Field(None, description="Burrowing speed")
    climb: Optional[str] = Field(None, description="Climbing speed")
    hover: Optional[bool] = Field(None, description="Can hover while flying")


class MonsterArmorClass(BaseModel):
    """Represents armor class for a monster."""

    type: str = Field(..., description="Type of AC (natural, armor, etc.)")
    value: int = Field(..., description="AC value")
    armor: Optional[List[APIReference]] = Field(None, description="Armor worn")
    spell: Optional[APIReference] = Field(None, description="Spell providing AC")
    condition: Optional[APIReference] = Field(None, description="Conditional AC")
    desc: Optional[str] = Field(None, description="AC description")


class MonsterProficiency(BaseModel):
    """Represents a proficiency for a monster."""

    value: int = Field(..., description="Proficiency bonus")
    proficiency: APIReference = Field(..., description="Skill or save")


class SpecialAbility(BaseModel):
    """Represents a special ability or trait for a monster."""

    name: str = Field(..., description="Ability name")
    desc: str = Field(..., description="Ability description")
    attack_bonus: Optional[int] = Field(None, description="Attack bonus")
    damage: Optional[List[Damage]] = Field(None, description="Damage dealt")
    dc: Optional[DC] = Field(None, description="Save DC")
    spellcasting: Optional[Dict[str, Any]] = Field(
        None, description="Spellcasting details"
    )
    usage: Optional[Usage] = Field(None, description="Usage limits")


class MonsterAction(BaseModel):
    """Represents an action a monster can take."""

    name: str = Field(..., description="Action name")
    multiattack_type: Optional[str] = Field(None, description="Type of multiattack")
    desc: str = Field(..., description="Action description")
    attack_bonus: Optional[int] = Field(None, description="Attack bonus")
    damage: Optional[List[Damage]] = Field(None, description="Damage dealt")
    dc: Optional[DC] = Field(None, description="Save DC")
    usage: Optional[Usage] = Field(None, description="Usage limits")
    options: Optional[Dict[str, Any]] = Field(None, description="Action options")
    actions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Sub-actions for multiattack"
    )


class D5eMonster(BaseModel):
    """Represents a monster in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    size: str = Field(..., description="Size category")
    type: str = Field(..., description="Creature type")
    subtype: Optional[str] = Field(None, description="Creature subtype")
    alignment: str = Field(..., description="Typical alignment")
    armor_class: List[MonsterArmorClass] = Field(..., description="AC details")
    hit_points: int = Field(..., description="Average hit points")
    hit_dice: str = Field(..., description="Hit dice")
    hit_points_roll: str = Field(..., description="HP roll formula")
    speed: MonsterSpeed = Field(..., description="Movement speeds")

    # Ability scores
    strength: int = Field(..., description="Strength score")
    dexterity: int = Field(..., description="Dexterity score")
    constitution: int = Field(..., description="Constitution score")
    intelligence: int = Field(..., description="Intelligence score")
    wisdom: int = Field(..., description="Wisdom score")
    charisma: int = Field(..., description="Charisma score")

    # Proficiencies and defenses
    proficiencies: List[MonsterProficiency] = Field(
        default_factory=list, description="Skill and save proficiencies"
    )
    damage_vulnerabilities: List[str] = Field(
        default_factory=list, description="Damage vulnerabilities"
    )
    damage_resistances: List[str] = Field(
        default_factory=list, description="Damage resistances"
    )
    damage_immunities: List[str] = Field(
        default_factory=list, description="Damage immunities"
    )
    condition_immunities: List[APIReference] = Field(
        default_factory=list, description="Condition immunities"
    )

    # Senses and communication
    senses: Dict[str, Any] = Field(..., description="Senses")
    languages: str = Field(..., description="Languages spoken")
    telepathy: Optional[str] = Field(None, description="Telepathy range")

    # Challenge and experience
    challenge_rating: float = Field(..., description="Challenge rating")
    proficiency_bonus: int = Field(..., description="Proficiency bonus")
    xp: int = Field(..., description="Experience points")

    # Abilities and actions
    special_abilities: Optional[List[SpecialAbility]] = Field(
        None, description="Special traits"
    )
    actions: Optional[List[MonsterAction]] = Field(
        None, description="Actions in combat"
    )
    legendary_actions: Optional[List[MonsterAction]] = Field(
        None, description="Legendary actions"
    )
    reactions: Optional[List[MonsterAction]] = Field(None, description="Reactions")

    # Additional info
    desc: Optional[Union[str, List[str]]] = Field(None, description="Description")
    image: Optional[str] = Field(None, description="Image URL")
    url: str = Field(..., description="API endpoint URL")

    @field_validator("desc", mode="before")
    @classmethod
    def normalize_desc(cls, v: Any) -> Optional[List[str]]:
        """Normalize desc to always be a list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        return None
