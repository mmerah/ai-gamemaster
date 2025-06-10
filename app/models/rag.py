"""
RAG (Retrieval-Augmented Generation) related type definitions.

This module contains all RAG-related model definitions.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# ===== Pydantic Models =====


class RAGContextDataModel(BaseModel):
    """Context data for RAG queries."""

    action: str = Field(..., description="The query action")
    location: Optional[str] = Field(None, description="Current location")
    spell_name: Optional[str] = Field(None, description="Spell name for queries")
    creature: Optional[str] = Field(None, description="Creature name for queries")
    skill: Optional[str] = Field(None, description="Skill name for queries")
    npc_name: Optional[str] = Field(None, description="NPC name for queries")
    recent_events: Optional[str] = Field(None, description="Recent game events")
    in_combat: Optional[str] = Field(None, description="Whether in combat")
    current_combatant: Optional[str] = Field(None, description="Current combatant name")

    model_config = ConfigDict(extra="forbid")
