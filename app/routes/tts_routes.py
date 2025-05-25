"""
Text-to-Speech API routes.
"""
import logging
from flask import Blueprint, request, jsonify
from app.core.container import get_container

logger = logging.getLogger(__name__)

# Create blueprint for TTS API routes
tts_bp = Blueprint('tts', __name__, url_prefix='/api/tts')

@tts_bp.route('/voices')
def get_tts_voices():
    """Get available TTS voices."""
    try:
        container = get_container()
        tts_service = container.get_tts_service()
        if not tts_service:
            return jsonify({"error": "TTS service not available"}), 503
        
        # Assuming lang_code 'a' for English for now, or make it a query param
        voices = tts_service.get_available_voices(lang_code='a') 
        return jsonify({"voices": voices})
        
    except Exception as e:
        logger.error(f"Error getting TTS voices: {e}", exc_info=True)
        return jsonify({"error": "Failed to get TTS voices"}), 500

@tts_bp.route('/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthesize speech from text."""
    try:
        container = get_container()
        tts_service = container.get_tts_service()
        if not tts_service:
            return jsonify({"error": "TTS service not available"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        text = data.get('text')
        voice_id = data.get('voice_id', 'af_heart')  # Default voice
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Generate the audio file
        audio_path = tts_service.synthesize_speech(text, voice_id)
        if not audio_path:
            return jsonify({"error": "Failed to synthesize speech"}), 500
        
        # Construct proper URL for the audio file
        audio_url = f"/static/{audio_path}"
        
        # Return the URL to the audio file (frontend expects audio_url)
        return jsonify({
            "audio_url": audio_url,
            "voice_id": voice_id,
            "text": text
        })
        
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}", exc_info=True)
        return jsonify({"error": "Failed to synthesize speech"}), 500
