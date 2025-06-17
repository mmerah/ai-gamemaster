"""
Game state event models.

This module contains events related to game state changes like location,
party members, quests, and items.
"""

from typing import Literal, Optional

from app.models.events.base import BaseGameEvent
from app.models.events.utils import CharacterChangesModel


class LocationChangedEvent(BaseGameEvent):
    event_type: Literal["location_changed"] = "location_changed"
    new_location_name: str
    new_location_description: str
    old_location_name: Optional[str] = None


class PartyMemberUpdatedEvent(BaseGameEvent):
    event_type: Literal["party_member_updated"] = "party_member_updated"
    character_id: str
    character_name: str
    changes: CharacterChangesModel
    gold_source: Optional[str] = None  # Source of gold change if applicable


class QuestUpdatedEvent(BaseGameEvent):
    """Event emitted when a quest status changes."""

    event_type: Literal["quest_updated"] = "quest_updated"

    quest_id: str
    quest_title: str
    new_status: str  # "active", "completed", "failed"
    old_status: Optional[str] = None
    description_update: Optional[str] = None


class ItemAddedEvent(BaseGameEvent):
    """Event emitted when item is added to inventory."""

    event_type: Literal["item_added"] = "item_added"

    character_id: str
    character_name: str
    item_name: str
    quantity: int = 1
    item_description: Optional[str] = None
    item_value: Optional[int] = None  # Value in gold pieces
    item_rarity: Optional[str] = None  # common, uncommon, rare, etc.
