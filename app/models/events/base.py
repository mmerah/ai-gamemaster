"""
Base event model.

This module contains the base class for all game events.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import ConfigDict, Field

from app.models.base import BaseModelWithDatetimeSerializer
from app.utils.event_sequence import get_next_sequence_number


class BaseGameEvent(BaseModelWithDatetimeSerializer):
    """Base class for all game events"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_number: int = Field(default_factory=get_next_sequence_number)
    event_type: str
    correlation_id: Optional[str] = None

    model_config = ConfigDict()
