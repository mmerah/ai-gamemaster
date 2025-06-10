"""
Unit tests for TTS Integration Service including hierarchy behavior.
"""

from typing import Dict
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture

from app.models.models import GameStateModel, VoiceInfoModel
from app.services.tts_integration_service import TTSIntegrationService


class TestTTSIntegrationService:
    """Test TTS integration service functionality."""

    @pytest.fixture
    def mock_tts_service(self) -> Mock:
        """Create a mock TTS service."""
        mock = Mock()
        mock.synthesize_speech = Mock(return_value="/path/to/audio.mp3")
        mock.get_available_voices = Mock(
            return_value=[
                VoiceInfoModel(id="af_heart", name="Heart"),
                VoiceInfoModel(id="am_adam", name="Adam"),
            ]
        )
        return mock

    @pytest.fixture
    def mock_game_state_repo(self) -> Mock:
        """Create a mock game state repository."""
        return Mock()

    @pytest.fixture
    def tts_integration_service(
        self, mock_tts_service: Mock, mock_game_state_repo: Mock
    ) -> TTSIntegrationService:
        """Create TTS integration service instance."""
        return TTSIntegrationService(mock_tts_service, mock_game_state_repo)

    def test_is_narration_enabled_with_game_state(
        self, tts_integration_service: TTSIntegrationService, mock_game_state_repo: Mock
    ) -> None:
        """Test checking narration status when game state exists."""
        # Create a game state with narration enabled
        game_state = GameStateModel(narration_enabled=True, tts_voice="af_heart")
        mock_game_state_repo.get_game_state.return_value = game_state

        assert tts_integration_service.is_narration_enabled() is True

    def test_is_narration_enabled_no_game_state(
        self, tts_integration_service: TTSIntegrationService, mock_game_state_repo: Mock
    ) -> None:
        """Test checking narration status when no game state exists."""
        mock_game_state_repo.get_game_state.return_value = None

        assert tts_integration_service.is_narration_enabled() is False

    def test_is_narration_enabled_disabled_in_game_state(
        self, tts_integration_service: TTSIntegrationService, mock_game_state_repo: Mock
    ) -> None:
        """Test checking narration status when explicitly disabled."""
        game_state = GameStateModel(narration_enabled=False, tts_voice="af_heart")
        mock_game_state_repo.get_game_state.return_value = game_state

        assert tts_integration_service.is_narration_enabled() is False

    def test_get_current_voice_from_game_state(
        self, tts_integration_service: TTSIntegrationService, mock_game_state_repo: Mock
    ) -> None:
        """Test getting current voice from game state."""
        game_state = GameStateModel(narration_enabled=True, tts_voice="am_adam")
        mock_game_state_repo.get_game_state.return_value = game_state

        assert tts_integration_service.get_current_voice() == "am_adam"

    def test_get_current_voice_default(
        self, tts_integration_service: TTSIntegrationService, mock_game_state_repo: Mock
    ) -> None:
        """Test default voice when no game state."""
        mock_game_state_repo.get_game_state.return_value = None

        assert tts_integration_service.get_current_voice() == "af_heart"

    def test_set_narration_enabled_success(
        self, tts_integration_service: TTSIntegrationService, mock_game_state_repo: Mock
    ) -> None:
        """Test enabling narration updates game state."""
        game_state = GameStateModel(narration_enabled=False, tts_voice="af_heart")
        mock_game_state_repo.get_game_state.return_value = game_state

        result = tts_integration_service.set_narration_enabled(True)

        assert result is True
        assert game_state.narration_enabled is True
        mock_game_state_repo.save_game_state.assert_called_once_with(game_state)

    def test_set_narration_enabled_no_game_state(
        self, tts_integration_service: TTSIntegrationService, mock_game_state_repo: Mock
    ) -> None:
        """Test setting narration when no game state exists."""
        mock_game_state_repo.get_game_state.return_value = None

        result = tts_integration_service.set_narration_enabled(True)

        assert result is False
        mock_game_state_repo.save_game_state.assert_not_called()

    def test_generate_tts_for_message_success(
        self,
        tts_integration_service: TTSIntegrationService,
        mock_game_state_repo: Mock,
        mock_tts_service: Mock,
    ) -> None:
        """Test successful TTS generation."""
        game_state = GameStateModel(narration_enabled=True, tts_voice="af_heart")
        mock_game_state_repo.get_game_state.return_value = game_state

        result = tts_integration_service.generate_tts_for_message(
            "Hello world", "msg123"
        )

        assert result == "/path/to/audio.mp3"
        mock_tts_service.synthesize_speech.assert_called_once_with(
            "Hello world", "af_heart"
        )

    def test_generate_tts_narration_disabled(
        self,
        tts_integration_service: TTSIntegrationService,
        mock_game_state_repo: Mock,
        mock_tts_service: Mock,
    ) -> None:
        """Test TTS generation skipped when narration disabled."""
        game_state = GameStateModel(narration_enabled=False, tts_voice="af_heart")
        mock_game_state_repo.get_game_state.return_value = game_state

        result = tts_integration_service.generate_tts_for_message(
            "Hello world", "msg123"
        )

        assert result is None
        mock_tts_service.synthesize_speech.assert_not_called()

    def test_generate_tts_no_tts_service(self, mock_game_state_repo: Mock) -> None:
        """Test TTS generation when service not available."""
        service = TTSIntegrationService(None, mock_game_state_repo)

        result = service.generate_tts_for_message("Hello world", "msg123")

        assert result is None

    def test_generate_tts_empty_message(
        self,
        tts_integration_service: TTSIntegrationService,
        mock_game_state_repo: Mock,
        mock_tts_service: Mock,
    ) -> None:
        """Test TTS generation with empty message."""
        game_state = GameStateModel(narration_enabled=True, tts_voice="af_heart")
        mock_game_state_repo.get_game_state.return_value = game_state

        result = tts_integration_service.generate_tts_for_message("", "msg123")

        assert result is None
        mock_tts_service.synthesize_speech.assert_not_called()

    def test_get_available_voices(
        self, tts_integration_service: TTSIntegrationService, mock_tts_service: Mock
    ) -> None:
        """Test getting available voices."""
        voices = tts_integration_service.get_available_voices()

        assert len(voices) == 2
        assert voices[0].id == "af_heart"  # VoiceInfoModel has .id attribute
        mock_tts_service.get_available_voices.assert_called_once()

    def test_get_available_voices_no_service(self, mock_game_state_repo: Mock) -> None:
        """Test getting voices when service not available."""
        service = TTSIntegrationService(None, mock_game_state_repo)

        voices = service.get_available_voices()

        assert voices == []

    def test_preview_voice_success(
        self, tts_integration_service: TTSIntegrationService, mock_tts_service: Mock
    ) -> None:
        """Test voice preview generation."""
        result = tts_integration_service.preview_voice("af_heart", "Test message")

        assert result == "/path/to/audio.mp3"
        mock_tts_service.synthesize_speech.assert_called_once_with(
            "Test message", "af_heart"
        )

    def test_preview_voice_default_text(
        self, tts_integration_service: TTSIntegrationService, mock_tts_service: Mock
    ) -> None:
        """Test voice preview with default text."""
        result = tts_integration_service.preview_voice("af_heart")

        assert result == "/path/to/audio.mp3"
        mock_tts_service.synthesize_speech.assert_called_once()
        call_args = mock_tts_service.synthesize_speech.call_args[0]
        assert "Welcome to your adventure" in call_args[0]
        assert call_args[1] == "af_heart"


class TestTTSHierarchyBehavior:
    """Test the TTS settings hierarchy behavior."""

    @pytest.fixture
    def mock_dependencies(self) -> Dict[str, Mock]:
        """Create mock dependencies for hierarchy tests."""
        mock_tts_service = Mock()
        mock_tts_service.synthesize_speech = Mock(return_value="/path/to/audio.mp3")

        mock_game_state_repo = Mock()
        mock_campaign_service = Mock()

        return {
            "tts_service": mock_tts_service,
            "game_state_repo": mock_game_state_repo,
            "campaign_service": mock_campaign_service,
        }

    def test_hierarchy_game_state_takes_precedence(
        self, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that game state settings are used when present."""
        # This test verifies that the TTS service uses game state values
        # The hierarchy is already applied when game state is created
        service = TTSIntegrationService(
            mock_dependencies["tts_service"], mock_dependencies["game_state_repo"]
        )

        # Game state has narration enabled and specific voice
        game_state = GameStateModel(narration_enabled=True, tts_voice="am_adam")
        mock_dependencies["game_state_repo"].get_game_state.return_value = game_state

        # Verify narration is enabled
        assert service.is_narration_enabled() is True

        # Verify correct voice is used
        assert service.get_current_voice() == "am_adam"

        # Verify TTS generation uses game state voice
        service.generate_tts_for_message("Test", "msg1")
        mock_dependencies["tts_service"].synthesize_speech.assert_called_with(
            "Test", "am_adam"
        )

    def test_runtime_toggle_only_affects_game_state(
        self, mock_dependencies: Dict[str, Mock]
    ) -> None:
        """Test that runtime toggles only modify game state, not campaign/template."""
        service = TTSIntegrationService(
            mock_dependencies["tts_service"], mock_dependencies["game_state_repo"]
        )

        # Initial game state from hierarchy: template(False) -> instance(None) -> game(False)
        game_state = GameStateModel(
            narration_enabled=False,  # Inherited from template
            tts_voice="af_heart",
        )
        mock_dependencies["game_state_repo"].get_game_state.return_value = game_state

        # User enables narration during gameplay
        result = service.set_narration_enabled(True)

        assert result is True
        assert game_state.narration_enabled is True

        # Verify only game state is saved, not campaign or template
        mock_dependencies["game_state_repo"].save_game_state.assert_called_once_with(
            game_state
        )
        # No calls to update campaign instance or template


class TestTTSErrorHandling:
    """Test error handling in TTS integration service."""

    def test_is_narration_enabled_handles_exceptions(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test that exceptions are handled gracefully."""
        mock_repo = Mock()
        mock_repo.get_game_state.side_effect = Exception("Database error")

        service = TTSIntegrationService(Mock(), mock_repo)

        result = service.is_narration_enabled()

        assert result is False
        assert "Error checking narration status" in caplog.text

    def test_set_narration_enabled_handles_save_errors(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handling of save errors."""
        mock_repo = Mock()
        game_state = GameStateModel(narration_enabled=False, tts_voice="af_heart")
        mock_repo.get_game_state.return_value = game_state
        mock_repo.save_game_state.side_effect = Exception("Save failed")

        service = TTSIntegrationService(Mock(), mock_repo)

        result = service.set_narration_enabled(True)

        assert result is False
        assert "Error setting narration status" in caplog.text

    def test_generate_tts_handles_synthesis_errors(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handling of TTS synthesis errors."""
        mock_tts = Mock()
        mock_tts.synthesize_speech.side_effect = Exception("Synthesis failed")

        mock_repo = Mock()
        game_state = GameStateModel(narration_enabled=True, tts_voice="af_heart")
        mock_repo.get_game_state.return_value = game_state

        service = TTSIntegrationService(mock_tts, mock_repo)

        result = service.generate_tts_for_message("Test", "msg1")

        assert result is None
        assert "Error generating TTS for message msg1" in caplog.text
