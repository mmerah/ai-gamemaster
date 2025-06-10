"""
Base models and shared classes.

This module contains base classes used throughout the model hierarchy.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_serializer


class BaseModelWithDatetimeSerializer(BaseModel):
    """Base model with datetime serialization support for Pydantic v2."""

    @field_serializer(
        "created_date",
        "last_modified",
        "timestamp",
        when_used="json",
        check_fields=False,
    )
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return dt.isoformat() if dt else None
