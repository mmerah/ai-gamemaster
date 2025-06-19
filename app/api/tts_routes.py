"""
Text-to-Speech API routes.
"""

import logging
from typing import Tuple, Union

from flask import Blueprint, Response, jsonify, request

from app.api.dependencies import get_tts_integration_service, get_tts_service
from app.api.error_handlers import with_error_handling

logger = logging.getLogger(__name__)

# Create blueprint for TTS API routes
tts_bp = Blueprint("tts", __name__, url_prefix="/api/tts")


@tts_bp.route("/voices")
@with_error_handling("get_tts_voices")
def get_tts_voices() -> Union[Response, Tuple[Response, int]]:
    """Get available TTS voices."""
    tts_service = get_tts_service()
    if not tts_service:
        return jsonify({"error": "TTS service not available"}), 503

    # Assuming lang_code 'a' for English for now, or make it a query param
    voices = tts_service.get_available_voices(lang_code="a")
    # Convert models to dicts for JSON response
    voices_dicts = [voice.model_dump() for voice in voices]
    return jsonify({"voices": voices_dicts})


@tts_bp.route("/narration/toggle", methods=["POST"])
@with_error_handling("toggle_narration")
def toggle_narration() -> Union[Response, Tuple[Response, int]]:
    """Toggle narration on/off for the current session."""
    tts_integration_service = get_tts_integration_service()

    data = request.get_json()
    if not data or "enabled" not in data:
        return jsonify({"error": "No enabled flag provided"}), 400

    enabled = bool(data.get("enabled"))
    success = tts_integration_service.set_narration_enabled(enabled)

    if success:
        return jsonify(
            {
                "success": True,
                "narration_enabled": enabled,
                "message": f"Narration {'enabled' if enabled else 'disabled'}",
            }
        )
    else:
        return jsonify({"error": "Failed to update narration setting"}), 500


@tts_bp.route("/narration/status")
@with_error_handling("get_narration_status")
def get_narration_status() -> Union[Response, Tuple[Response, int]]:
    """Get current narration status."""
    tts_integration_service = get_tts_integration_service()

    enabled = tts_integration_service.is_narration_enabled()

    return jsonify({"narration_enabled": enabled})


@tts_bp.route("/synthesize", methods=["POST"])
@with_error_handling("synthesize_speech")
def synthesize_speech() -> Union[Response, Tuple[Response, int]]:
    """Synthesize speech from text."""
    tts_service = get_tts_service()
    if not tts_service:
        return jsonify({"error": "TTS service not available"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    text = data.get("text")
    voice_id = data.get("voice_id", "af_heart")  # Default voice

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Generate the audio file
    audio_path = tts_service.synthesize_speech(text, voice_id)
    if not audio_path:
        return jsonify({"error": "Failed to synthesize speech"}), 500

    # Construct proper URL for the audio file
    audio_url = f"/static/{audio_path}"

    # Return the URL to the audio file (frontend expects audio_url)
    return jsonify({"audio_url": audio_url, "voice_id": voice_id, "text": text})
