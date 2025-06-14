"""Equipment and item models for D&D 5e.

This module contains models for equipment, magic items, weapon properties,
and equipment categories.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.content.schemas.base import APIReference, Cost, Damage


class EquipmentRange(BaseModel):
    """Represents the range of a weapon."""

    normal: int = Field(..., description="Normal range in feet")
    long: Optional[int] = Field(None, description="Long range in feet")


class ArmorClass(BaseModel):
    """Represents armor class details for armor."""

    base: int = Field(..., description="Base AC provided")
    dex_bonus: bool = Field(..., description="Whether DEX modifier is added")
    max_bonus: Optional[int] = Field(None, description="Maximum DEX bonus allowed")


class D5eEquipment(BaseModel):
    """Represents a piece of equipment in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    equipment_category: APIReference = Field(..., description="Category of equipment")
    cost: Cost = Field(..., description="Purchase cost")
    weight: Optional[float] = Field(None, description="Weight in pounds")
    desc: Optional[List[str]] = Field(None, description="Description paragraphs")

    # Weapon-specific fields
    weapon_category: Optional[str] = Field(None, description="Simple or Martial")
    weapon_range: Optional[str] = Field(None, description="Melee or Ranged")
    category_range: Optional[str] = Field(
        None, description="Combined category (Simple Melee, etc.)"
    )
    damage: Optional[Damage] = Field(None, description="Weapon damage")
    two_handed_damage: Optional[Damage] = Field(
        None, description="Damage when used two-handed"
    )
    range: Optional[EquipmentRange] = Field(None, description="Weapon range")
    throw_range: Optional[EquipmentRange] = Field(None, description="Range when thrown")
    properties: Optional[List[APIReference]] = Field(
        None, description="Weapon properties"
    )

    # Armor-specific fields
    armor_category: Optional[str] = Field(None, description="Light, Medium, or Heavy")
    armor_class: Optional[ArmorClass] = Field(None, description="AC details")
    str_minimum: Optional[int] = Field(None, description="Minimum Strength requirement")
    stealth_disadvantage: Optional[bool] = Field(
        None, description="Imposes disadvantage on Stealth"
    )

    # Gear-specific fields
    gear_category: Optional[APIReference] = Field(
        None, description="Specific gear category"
    )
    quantity: Optional[int] = Field(None, description="Quantity in a set")
    contents: Optional[List[Dict[str, Any]]] = Field(
        None, description="Contents of a pack/kit"
    )

    # Tool-specific fields
    tool_category: Optional[str] = Field(None, description="Type of tool")

    # Vehicle-specific fields
    vehicle_category: Optional[str] = Field(None, description="Type of vehicle")
    speed: Optional[Dict[str, Any]] = Field(None, description="Vehicle speed")
    capacity: Optional[str] = Field(None, description="Cargo capacity")

    url: str = Field(..., description="API endpoint URL")


class D5eEquipmentCategory(BaseModel):
    """Represents a category of equipment."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    equipment: List[APIReference] = Field(
        default_factory=list, description="Equipment in this category"
    )
    url: str = Field(..., description="API endpoint URL")


class D5eMagicItem(BaseModel):
    """Represents a magic item in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    equipment_category: APIReference = Field(..., description="Category (magic item)")
    desc: List[str] = Field(..., description="Description paragraphs")
    rarity: Dict[str, str] = Field(..., description="Rarity information")
    variant: bool = Field(..., description="Whether this has variants")
    variants: Optional[List[APIReference]] = Field(None, description="Variant versions")
    url: str = Field(..., description="API endpoint URL")


class D5eWeaponProperty(BaseModel):
    """Represents a weapon property in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    desc: List[str] = Field(..., description="Description paragraphs")
    url: str = Field(..., description="API endpoint URL")


class D5eMagicSchool(BaseModel):
    """Represents a school of magic in D&D 5e."""

    index: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    desc: str = Field(..., description="Description")
    url: str = Field(..., description="API endpoint URL")
