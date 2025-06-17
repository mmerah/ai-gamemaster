"""
Narrative event models.

This module contains events related to narrative and chat messages.
"""

from typing import Literal, Optional

from app.models.events.base import BaseGameEvent


class NarrativeAddedEvent(BaseGameEvent):
    event_type: Literal["narrative_added"] = "narrative_added"
    role: str  # "assistant", "user", "system"
    content: str
    gm_thought: Optional[str] = None
    audio_path: Optional[str] = None
    message_id: Optional[str] = None


class MessageSupersededEvent(BaseGameEvent):
    event_type: Literal["message_superseded"] = "message_superseded"
    message_id: str
    reason: str = "retry"
