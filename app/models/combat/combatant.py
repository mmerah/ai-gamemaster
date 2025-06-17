"""
Combatant models.

This module contains the CombatantModel and InitialCombatantData models.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from app.models.combat.attack import AttackModel

if TYPE_CHECKING:
    from app.domain.validators.content_validator import (
        ContentValidationError,
        ContentValidator,
    )


class CombatantModel(BaseModel):
    """Enhanced combatant model with validation and helper properties."""

    id: str
    name: str
    initiative: int
    initiative_modifier: int = Field(0, description="DEX modifier for tie-breaking")
    current_hp: int = Field(ge=0, description="Current hit points (non-negative)")
    max_hp: int = Field(gt=0, description="Maximum hit points (positive)")
    armor_class: int = Field(gt=0, description="Armor class")
    conditions: List[str] = Field(default_factory=list, description="Active conditions")
    is_player: bool = Field(..., description="Flag to distinguish player chars")
    icon_path: Optional[str] = None

    # Mostly for monsters/NPCs (None for players)
    stats: Optional[Dict[str, int]] = Field(
        None, description="Ability scores (e.g., {'STR': 16, 'DEX': 14})"
    )
    abilities: Optional[List[str]] = Field(
        None, description="Special abilities or features"
    )
    attacks: Optional[List[AttackModel]] = Field(
        None, description="Available attacks and their properties"
    )
    conditions_immune: Optional[List[str]] = Field(
        None, description="Conditions the creature is immune to"
    )
    resistances: Optional[List[str]] = Field(
        None, description="Damage types the creature resists"
    )
    vulnerabilities: Optional[List[str]] = Field(
        None, description="Damage types the creature is vulnerable to"
    )

    @property
    def is_player_controlled(self) -> bool:
        """Alias for is_player to maintain compatibility."""
        return self.is_player

    @property
    def is_defeated(self) -> bool:
        """Check if combatant is defeated (0 HP)."""
        return self.current_hp <= 0

    @property
    def is_incapacitated(self) -> bool:
        """Check if combatant cannot take actions."""
        incapacitating_conditions = {
            "unconscious",
            "stunned",
            "paralyzed",
            "petrified",
            "incapacitated",
        }
        return self.is_defeated or any(
            cond.lower() in incapacitating_conditions for cond in self.conditions
        )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    def model_post_init(self, _: Optional[Any] = None) -> None:
        """Validate HP relationship after initialization."""
        if self.current_hp > self.max_hp:
            raise ValueError(
                f"current_hp ({self.current_hp}) cannot exceed max_hp ({self.max_hp})"
            )

    def validate_content(
        self,
        validator: "ContentValidator",
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List["ContentValidationError"]]:
        """Validate D&D 5e content references in this combatant.

        Args:
            validator: The content validator to use
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return validator.validate_combatant(self, content_pack_priority)


class InitialCombatantData(BaseModel):
    """Core game model for initial combatant data when starting combat."""

    id: str = Field(..., description="Unique identifier for the combatant")
    name: str = Field(..., description="Display name of the combatant")
    hp: int = Field(..., description="Starting hit points")
    ac: int = Field(..., description="Armor class")
    stats: Optional[Dict[str, int]] = Field(
        None, description="Ability scores (e.g., {'DEX': 14, 'STR': 12})"
    )
    abilities: Optional[List[str]] = Field(
        None, description="Special abilities or features"
    )
    attacks: Optional[List[AttackModel]] = Field(
        None, description="Available attacks and their properties"
    )
    icon_path: Optional[str] = Field(
        None, description="Path to character portrait/icon"
    )

    model_config = ConfigDict(extra="forbid")
