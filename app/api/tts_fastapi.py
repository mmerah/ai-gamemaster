"""
Text-to-Speech API routes - FastAPI version.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies_fastapi import get_tts_integration_service, get_tts_service
from app.core.external_interfaces import ITTSIntegrationService, ITTSService

logger = logging.getLogger(__name__)

# Create router for TTS API routes
router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.get("/voices")
async def get_tts_voices(
    tts_service: Optional[ITTSService] = Depends(get_tts_service),
) -> Dict[str, Any]:
    """Get available TTS voices."""
    if not tts_service:
        raise HTTPException(
            status_code=503,
            detail="TTS service not available",
        )

    try:
        # Assuming lang_code 'a' for English for now, or make it a query param
        voices = tts_service.get_available_voices(lang_code="a")
        # Convert models to dicts for JSON response
        voices_dicts = [voice.model_dump() for voice in voices]
        return {"voices": voices_dicts}
    except Exception as e:
        logger.error(f"Error getting TTS voices: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get TTS voices",
        )


@router.post("/narration/toggle")
async def toggle_narration(
    data: Dict[str, Any],
    tts_integration_service: ITTSIntegrationService = Depends(
        get_tts_integration_service
    ),
) -> Dict[str, Any]:
    """Toggle narration on/off for the current session."""
    if not data or "enabled" not in data:
        raise HTTPException(
            status_code=400,
            detail="No enabled flag provided",
        )

    try:
        enabled = bool(data.get("enabled"))
        success = tts_integration_service.set_narration_enabled(enabled)

        if success:
            return {
                "success": True,
                "narration_enabled": enabled,
                "message": f"Narration {'enabled' if enabled else 'disabled'}",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update narration setting",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling narration: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update narration setting",
        )


@router.get("/narration/status")
async def get_narration_status(
    tts_integration_service: ITTSIntegrationService = Depends(
        get_tts_integration_service
    ),
) -> Dict[str, bool]:
    """Get current narration status."""
    try:
        enabled = tts_integration_service.is_narration_enabled()
        return {"narration_enabled": enabled}
    except Exception as e:
        logger.error(f"Error getting narration status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get narration status",
        )


@router.post("/synthesize")
async def synthesize_speech(
    data: Dict[str, Any],
    tts_service: Optional[ITTSService] = Depends(get_tts_service),
) -> Dict[str, Any]:
    """Synthesize speech from text."""
    if not tts_service:
        raise HTTPException(
            status_code=503,
            detail="TTS service not available",
        )

    if not data:
        raise HTTPException(
            status_code=400,
            detail="No data provided",
        )

    text = data.get("text")
    voice_id = data.get("voice_id", "af_heart")  # Default voice

    if not text:
        raise HTTPException(
            status_code=400,
            detail="No text provided",
        )

    try:
        # Generate the audio file
        audio_path = tts_service.synthesize_speech(text, voice_id)
        if not audio_path:
            raise HTTPException(
                status_code=500,
                detail="Failed to synthesize speech",
            )

        # Construct proper URL for the audio file
        audio_url = f"/static/{audio_path}"

        # Return the URL to the audio file (frontend expects audio_url)
        return {"audio_url": audio_url, "voice_id": voice_id, "text": text}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to synthesize speech",
        )
