"""
TTS (Text-to-Speech) models.

This module contains all TTS-related models including voice information,
status, and synthesis requests/responses.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TTSVoice(BaseModel):
    """TTS voice option."""

    id: str
    name: str
    language: Optional[str] = None
    gender: Optional[str] = None


class TTSVoicesResponse(BaseModel):
    """Response for GET /tts/voices."""

    voices: List[TTSVoice]
    current_voice: Optional[str] = None


class TTSStatusResponse(BaseModel):
    """Response for GET /tts/narration/status."""

    narration_enabled: bool
    backend_auto_narration: bool
    voice: Optional[str] = None


class TTSSynthesizeResponse(BaseModel):
    """Response for POST /tts/synthesize."""

    success: bool
    audio_file: Optional[str] = None
    error: Optional[str] = None


class TTSToggleNarrationRequest(BaseModel):
    """Request for toggling narration on/off."""

    enable: bool = Field(..., description="Whether to enable or disable narration")


class TTSSynthesizeRequest(BaseModel):
    """Request for TTS synthesis."""

    text: str = Field(..., min_length=1, description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice ID to use")
    language: Optional[str] = Field(None, description="Language code")
