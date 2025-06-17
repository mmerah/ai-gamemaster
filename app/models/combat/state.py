"""
Combat state models.

This module contains the CombatStateModel and NextCombatantInfoModel.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.combat.combatant import CombatantModel


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
