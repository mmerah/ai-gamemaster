"""Common type-safe models to replace Dict[str, Any] usage."""

from pydantic import BaseModel, Field


class MessageDict(BaseModel):
    """Type-safe message for AI interactions."""

    role: str = Field(..., description="Message role (system/user/assistant)")
    content: str = Field(..., description="Message content")
