"""External service interfaces for the AI Game Master.

This module defines interfaces for external services like
text-to-speech and other third-party integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.utils import VoiceInfoModel


class ITTSService(ABC):
    """Interface for Text-to-Speech services."""

    @abstractmethod
    def synthesize_speech(self, text: str, voice_id: str) -> Optional[str]:
        """
        Synthesizes speech from text using the given voice_id.
        Returns the relative path (from static folder root) to the audio file on success, None on failure.
        Example returned path: "tts_cache/unique_filename.wav"
        """
        pass

    @abstractmethod
    def get_available_voices(
        self, lang_code: Optional[str] = None
    ) -> List[VoiceInfoModel]:
        """
        Returns a list of available voices. Each voice is a VoiceInfoModel with id and name fields.
        Optionally filtered by language code. For now, only English voices are supported.
        """
        pass


class ITTSIntegrationService(ABC):
    """Interface for TTS integration with game state management."""

    @abstractmethod
    def is_narration_enabled(self) -> bool:
        """Check if narration is enabled for the current game session."""
        pass

    @abstractmethod
    def get_current_voice(self) -> str:
        """Get the current TTS voice ID."""
        pass

    @abstractmethod
    def set_narration_enabled(self, enabled: bool) -> bool:
        """Enable/disable narration for the current game session."""
        pass

    @abstractmethod
    def generate_tts_for_message(
        self, message_content: str, message_id: str
    ) -> Optional[str]:
        """Generate TTS audio for a message if narration is enabled."""
        pass

    @abstractmethod
    def get_available_voices(self) -> List[VoiceInfoModel]:
        """Get available TTS voices."""
        pass

    @abstractmethod
    def preview_voice(
        self, voice_id: str, sample_text: Optional[str] = None
    ) -> Optional[str]:
        """Generate a preview audio for a voice with sample text."""
        pass

    @abstractmethod
    def is_backend_auto_narration_enabled(self) -> bool:
        """Check if backend auto-narration is enabled."""
        pass
