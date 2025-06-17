"""
Combat models.

This module contains all combat-related models.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.validators.content_validator import (
        ContentValidationError,
        ContentValidator,
    )


class AttackModel(BaseModel):
    """Model for creature/NPC attacks."""

    name: str = Field(..., description="Attack name (e.g., 'scimitar', 'bite')")
    description: str = Field(..., description="Full attack description with mechanics")
    # Optional parsed fields for future use
    attack_type: Optional[Literal["melee", "ranged"]] = Field(
        None, description="Type of attack"
    )
    to_hit_bonus: Optional[int] = Field(None, description="Attack roll bonus")
    reach: Optional[str] = Field(None, description="Melee reach (e.g., '5 ft')")
    range: Optional[str] = Field(
        None, description="Ranged distance (e.g., '80/320 ft')"
    )
    damage_formula: Optional[str] = Field(
        None, description="Damage dice (e.g., '1d6+2')"
    )
    damage_type: Optional[str] = Field(
        None, description="Damage type (e.g., 'slashing', 'piercing')"
    )

    model_config = ConfigDict(extra="forbid")

    def validate_content(
        self,
        validator: "ContentValidator",
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List["ContentValidationError"]]:
        """Validate D&D 5e content references in this attack.

        Args:
            validator: The content validator to use
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List["ContentValidationError"] = []

        # Validate damage type if present
        if self.damage_type:
            invalid_damage_types = validator._validate_list_content(
                [self.damage_type],
                "damage-types",
                content_pack_priority=content_pack_priority,
            )
            if invalid_damage_types:
                from app.domain.validators.content_validator import (
                    ContentValidationError,
                )

                errors.append(
                    ContentValidationError(
                        "damage_type",
                        self.damage_type,
                        f"Invalid damage type: {self.damage_type}",
                    )
                )

        return (len(errors) == 0, errors)


class NextCombatantInfoModel(BaseModel):
    """Information about the next combatant in turn order."""

    combatant_id: str = Field(..., description="ID of the next combatant")
    combatant_name: str = Field(..., description="Name of the next combatant")
    is_player: bool = Field(
        ..., description="Whether the combatant is a player character"
    )
    round_number: int = Field(..., description="Current or new round number")
    is_new_round: bool = Field(..., description="Whether this starts a new round")
    should_end_combat: Optional[bool] = Field(
        None, description="Whether combat should end"
    )
    new_index: Optional[int] = Field(None, description="New turn index")

    model_config = ConfigDict(extra="forbid")


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


class CombatStateModel(BaseModel):
    """Enhanced combat state model with helper methods."""

    is_active: bool = False
    combatants: List[CombatantModel] = Field(default_factory=list)
    current_turn_index: int = -1  # -1 when no initiative set
    round_number: int = 1
    # Removed monster_stats - all data now stored in combatants with merged fields
    current_turn_instruction_given: bool = Field(
        default=False, description="Whether NPC turn instruction was given this turn"
    )

    # Private field for internal state tracking (not persisted)
    _combat_just_started_flag: bool = False

    def get_current_combatant(self) -> Optional[CombatantModel]:
        """Get the combatant whose turn it is."""
        if (
            not self.is_active
            or not self.combatants
            or not (0 <= self.current_turn_index < len(self.combatants))
        ):
            return None
        return self.combatants[self.current_turn_index]

    def get_combatant_by_id(self, combatant_id: str) -> Optional[CombatantModel]:
        """Find a combatant by ID."""
        for combatant in self.combatants:
            if combatant.id == combatant_id:
                return combatant
        return None

    def get_initiative_order(self) -> List[CombatantModel]:
        """Get combatants sorted by initiative (highest first), with DEX tie-breaker."""
        return sorted(
            self.combatants,
            key=lambda c: (c.initiative, c.initiative_modifier),
            reverse=True,
        )

    def get_next_active_combatant_index(self) -> tuple[int, int]:
        """
        Get the index of the next active (non-incapacitated) combatant.
        Returns (next_index, new_round_number).
        """
        if not self.combatants:
            return -1, self.round_number

        start_index = self.current_turn_index
        new_round_number = self.round_number
        wrapped = False

        # Try each combatant in turn order
        for i in range(1, len(self.combatants) + 1):
            next_index = (start_index + i) % len(self.combatants)

            # Check if we wrapped around the list
            if next_index <= start_index and not wrapped:
                wrapped = True
                new_round_number = self.round_number + 1

            combatant = self.combatants[next_index]
            if not combatant.is_incapacitated:
                return next_index, new_round_number

        # All combatants are incapacitated
        return -1, self.round_number

    @property
    def is_players_turn(self) -> bool:
        """Check if it's currently a player's turn."""
        current = self.get_current_combatant()
        return current is not None and current.is_player

    model_config = ConfigDict(extra="forbid")


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


class CombatInfoResponseModel(BaseModel):
    """Combat information response model for frontend display."""

    is_active: bool = Field(..., description="Whether combat is currently active")
    round_number: int = Field(default=0, description="Current combat round")
    current_combatant_id: Optional[str] = Field(
        None, description="ID of current combatant"
    )
    current_combatant_name: Optional[str] = Field(
        None, description="Name of current combatant"
    )
    combatants: List[CombatantModel] = Field(
        default_factory=list, description="List of combatants"
    )
    turn_order: List[str] = Field(
        default_factory=list, description="Turn order by combatant ID"
    )

    model_config = ConfigDict(extra="forbid")
