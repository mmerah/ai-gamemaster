"""
RAG (Retrieval-Augmented Generation) related type definitions.

This module contains all RAG-related model definitions.
"""

from typing import Dict, List, Optional

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


class EventMetadataModel(BaseModel):
    """Metadata for RAG events."""

    timestamp: str = Field(..., description="ISO timestamp of the event")
    location: Optional[str] = Field(None, description="Location where event occurred")
    participants: Optional[List[str]] = Field(
        None, description="List of participants in the event"
    )
    combat_active: Optional[bool] = Field(
        None, description="Whether combat was active during event"
    )

    model_config = ConfigDict(extra="forbid")


class LoreDataModel(BaseModel):
    """Structure for lore entries."""

    id: str = Field(..., description="Lore entry ID")
    name: str = Field(..., description="Lore entry name")
    description: str = Field(..., description="Brief description")
    content: str = Field(..., description="Full lore content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(None, description="Lore category")

    model_config = ConfigDict(extra="forbid")


class RulesetDataModel(BaseModel):
    """Structure for ruleset entries."""

    id: str = Field(..., description="Ruleset ID")
    name: str = Field(..., description="Ruleset name")
    description: str = Field(..., description="Ruleset description")
    rules: Dict[str, str] = Field(..., description="Map of rule names to descriptions")
    version: str = Field(..., description="Ruleset version")
    category: Optional[str] = Field(None, description="Ruleset category")

    model_config = ConfigDict(extra="forbid")
