"""
Chat-related shared models.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageModel(BaseModel):
    """Core game model for chat history messages."""

    id: str = Field(..., description="Unique message identifier")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    is_dice_result: Optional[bool] = Field(
        False, description="Whether message represents dice roll results"
    )
    gm_thought: Optional[str] = Field(
        None, description="GM's internal thought or reasoning"
    )
    ai_response_json: Optional[str] = Field(
        None, description="Full AI response in JSON format"
    )
    detailed_content: Optional[str] = Field(
        None, description="Detailed content for expandable messages"
    )
    audio_path: Optional[str] = Field(None, description="Path to audio file for TTS")

    model_config = ConfigDict(extra="forbid")
