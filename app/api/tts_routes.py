"""
Text-to-Speech API routes - FastAPI version.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_tts_integration_service, get_tts_service
from app.core.external_interfaces import ITTSIntegrationService, ITTSService
from app.models.api import SuccessResponse
from app.models.tts import (
    TTSStatusResponse,
    TTSSynthesizeRequest,
    TTSSynthesizeResponse,
    TTSToggleNarrationRequest,
    TTSVoice,
    TTSVoicesResponse,
)

logger = logging.getLogger(__name__)

# Create router for TTS API routes
router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.get("/voices", response_model=TTSVoicesResponse)
async def get_tts_voices(
    tts_service: Optional[ITTSService] = Depends(get_tts_service),
) -> TTSVoicesResponse:
    """Get available TTS voices."""
    if not tts_service:
        raise HTTPException(
            status_code=503,
            detail="TTS service not available",
        )

    try:
        # Assuming lang_code 'a' for English for now, or make it a query param
        voices = tts_service.get_available_voices(lang_code="a")
        # Convert provider models to API models
        voice_models = [
            TTSVoice(
                id=voice.id,
                name=voice.name,
                language=voice.language if hasattr(voice, "language") else None,
                gender=voice.gender if hasattr(voice, "gender") else None,
            )
            for voice in voices
        ]
        return TTSVoicesResponse(voices=voice_models)
    except Exception as e:
        logger.error(f"Error getting TTS voices: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get TTS voices",
        )


@router.post("/narration/toggle", response_model=SuccessResponse)
async def toggle_narration(
    request: TTSToggleNarrationRequest,
    tts_integration_service: ITTSIntegrationService = Depends(
        get_tts_integration_service
    ),
) -> SuccessResponse:
    """Toggle narration on/off for the current session."""
    try:
        success = tts_integration_service.set_narration_enabled(request.enable)

        if success:
            return SuccessResponse(
                success=True,
                message=f"Narration {'enabled' if request.enable else 'disabled'}",
                data={"narration_enabled": request.enable},
            )
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


@router.get("/narration/status", response_model=TTSStatusResponse)
async def get_narration_status(
    tts_integration_service: ITTSIntegrationService = Depends(
        get_tts_integration_service
    ),
) -> TTSStatusResponse:
    """Get current narration status."""
    try:
        enabled = tts_integration_service.is_narration_enabled()
        backend_auto = tts_integration_service.is_backend_auto_narration_enabled()
        voice = tts_integration_service.get_current_voice()

        return TTSStatusResponse(
            narration_enabled=enabled,
            backend_auto_narration=backend_auto,
            voice=voice,
        )
    except Exception as e:
        logger.error(f"Error getting narration status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get narration status",
        )


@router.post("/synthesize", response_model=TTSSynthesizeResponse)
async def synthesize_speech(
    request: TTSSynthesizeRequest,
    tts_service: Optional[ITTSService] = Depends(get_tts_service),
) -> TTSSynthesizeResponse:
    """Synthesize speech from text."""
    if not tts_service:
        raise HTTPException(
            status_code=503,
            detail="TTS service not available",
        )

    try:
        # Use provided voice or default
        voice_id = request.voice or "af_heart"

        # Generate the audio file
        audio_path = tts_service.synthesize_speech(request.text, voice_id)
        if not audio_path:
            return TTSSynthesizeResponse(
                success=False,
                error="Failed to synthesize speech",
            )

        # Construct proper URL for the audio file
        audio_url = f"/static/{audio_path}"

        # Return the URL to the audio file (frontend expects audio_url)
        return TTSSynthesizeResponse(
            success=True,
            audio_file=audio_url,
        )
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        return TTSSynthesizeResponse(
            success=False,
            error=str(e),
        )
