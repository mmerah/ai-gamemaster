"""
TTS Integration Service for automatic speech synthesis of AI narratives.
"""
import logging
from typing import Optional
from app.core.interfaces import BaseTTSService, GameStateRepository

logger = logging.getLogger(__name__)


class TTSIntegrationService:
    """Service that handles automatic TTS generation for AI narratives."""
    
    def __init__(self, tts_service: Optional[BaseTTSService], game_state_repo: GameStateRepository):
        self.tts_service = tts_service
        self.game_state_repo = game_state_repo
    
    def is_narration_enabled(self) -> bool:
        """Check if narration is enabled following the hierarchy:
        1. Game state (highest priority - runtime override)
        2. Campaign instance (if no game state override)
        3. Campaign template (default)
        """
        try:
            game_state = self.game_state_repo.get_game_state()
            if not game_state:
                return False
            
            # Game state narration_enabled is always authoritative
            # It's initialized from the hierarchy when the game starts
            # and can be toggled during gameplay
            return getattr(game_state, 'narration_enabled', False)
        except Exception as e:
            logger.error(f"Error checking narration status: {e}")
            return False
    
    def get_current_voice(self) -> str:
        """Get the current TTS voice following the same hierarchy as narration_enabled."""
        try:
            game_state = self.game_state_repo.get_game_state()
            if not game_state:
                return 'af_heart'
            
            # Game state tts_voice is always authoritative
            # It's initialized from the hierarchy when the game starts
            return getattr(game_state, 'tts_voice', 'af_heart')
        except Exception as e:
            logger.error(f"Error getting current voice: {e}")
            return 'af_heart'
    
    def set_narration_enabled(self, enabled: bool) -> bool:
        """Enable/disable narration for the current game session."""
        try:
            game_state = self.game_state_repo.get_game_state()
            if not game_state:
                return False
                
            # Update game state's narration setting directly
            game_state.narration_enabled = enabled
            self.game_state_repo.save_game_state(game_state)
            
            logger.info(f"Narration {'enabled' if enabled else 'disabled'} for current game session")
            return True
        except Exception as e:
            logger.error(f"Error setting narration status: {e}")
            return False
    
    def generate_tts_for_message(self, message_content: str, message_id: str) -> Optional[str]:
        """
        Generate TTS audio for a message if narration is enabled.
        Returns the audio path if successful, None otherwise.
        """
        if not self.tts_service:
            logger.debug("TTS service not available")
            return None
        
        if not self.is_narration_enabled():
            logger.debug("Narration is disabled for this campaign")
            return None
        
        if not message_content or not message_content.strip():
            logger.debug("Empty message content, skipping TTS")
            return None
        
        # Get the voice for this campaign
        voice_id = self.get_current_voice()
        
        try:
            # Generate the TTS audio
            audio_path = self.tts_service.synthesize_speech(message_content, voice_id)
            if audio_path:
                logger.info(f"Generated TTS audio for message {message_id}: {audio_path}")
                return audio_path
            else:
                logger.warning(f"Failed to generate TTS audio for message {message_id}")
                return None
        except Exception as e:
            logger.error(f"Error generating TTS for message {message_id}: {e}")
            return None
    
    def get_available_voices(self) -> list:
        """Get available TTS voices."""
        if not self.tts_service:
            return []
        
        try:
            return self.tts_service.get_available_voices()
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return []
    
    def preview_voice(self, voice_id: str, sample_text: str = None) -> Optional[str]:
        """Generate a preview audio for a voice with sample text."""
        if not self.tts_service:
            return None
        
        if not sample_text:
            sample_text = "Welcome to your adventure! The path ahead is filled with mystery and excitement."
        
        try:
            audio_path = self.tts_service.synthesize_speech(sample_text, voice_id)
            if audio_path:
                logger.info(f"Generated voice preview for {voice_id}: {audio_path}")
                return audio_path
            else:
                logger.warning(f"Failed to generate voice preview for {voice_id}")
                return None
        except Exception as e:
            logger.error(f"Error generating voice preview for {voice_id}: {e}")
            return None
