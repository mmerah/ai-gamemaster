"""
Integration tests for TTS settings hierarchy behavior.
Tests the complete flow from template -> instance -> game state.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, cast

import pytest

from app.core.container import ServiceContainer
from app.models.campaign import CampaignInstanceModel, CampaignTemplateModel
from app.models.game_state import GameStateModel
from app.models.utils import HouseRulesModel, LocationModel
from tests.conftest import get_test_config


class TestTTSHierarchyIntegration:
    """Test the complete TTS settings hierarchy flow."""

    def _create_game_state_from_template(
        self,
        campaign_service: Any,
        game_state_repo: Any,
        template_id: str,
        instance_name: str,
        party_character_ids: Optional[List[str]] = None,
    ) -> Optional[GameStateModel]:
        """Helper method to create game state from template, handling the conversion properly."""
        if party_character_ids is None:
            party_character_ids = []

        # Clear any existing game state
        try:
            game_state_repo.delete_game_state()
        except Exception:
            pass

        # Get initial state from campaign service
        game_state = cast(
            Optional[GameStateModel],
            campaign_service.start_campaign_from_template(
                template_id=template_id,
                instance_name=instance_name,
                party_character_ids=party_character_ids,
            ),
        )

        if not game_state:
            return None

        # Save the game state
        game_state_repo.save_game_state(game_state)

        return game_state

    @pytest.fixture
    def container(self, tmp_path: Any) -> ServiceContainer:
        """Create a service container with file-based repositories."""
        container = ServiceContainer(
            get_test_config(
                GAME_STATE_REPO_TYPE="file",
                SAVES_DIR=str(tmp_path),
                CAMPAIGNS_DIR=str(tmp_path / "campaigns"),
                CHARACTER_TEMPLATES_DIR=str(tmp_path / "character_templates"),
                CAMPAIGN_TEMPLATES_DIR=str(tmp_path / "campaign_templates"),
                TTS_PROVIDER="disabled",  # Disable actual TTS for tests
                RAG_ENABLED=False,
            )
        )
        container.initialize()
        return container

    @pytest.fixture
    def sample_template(self) -> CampaignTemplateModel:
        """Create a sample campaign template with TTS settings."""
        return CampaignTemplateModel(
            id="template_1",
            name="Adventure Template",
            description="A test template",
            campaign_goal="Test the TTS hierarchy",
            starting_location=LocationModel(
                name="Test Town", description="A place for testing"
            ),
            opening_narrative="Welcome to the test!",
            narration_enabled=True,  # Template default: enabled
            tts_voice="af_heart",  # Template default voice
            house_rules=HouseRulesModel(),
        )

    def test_hierarchy_template_to_instance_to_game_state(
        self, container: ServiceContainer, sample_template: CampaignTemplateModel
    ) -> None:
        """Test the complete hierarchy flow."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        tts_service = container.get_tts_integration_service()

        # Save the template
        template_repo.save(sample_template)

        # Create game state from template
        game_state = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Campaign 1"
        )

        # Verify game state inherited template settings
        assert game_state is not None
        assert game_state.narration_enabled is True  # From template
        assert game_state.tts_voice == "af_heart"  # From template

        # Verify TTS service sees these settings
        assert tts_service.is_narration_enabled() is True
        assert tts_service.get_current_voice() == "af_heart"

    def test_hierarchy_with_instance_override(
        self, container: ServiceContainer, sample_template: CampaignTemplateModel
    ) -> None:
        """Test instance overriding template settings."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        tts_service = container.get_tts_integration_service()

        # Create template with different settings to simulate override
        override_template = sample_template.model_copy()
        override_template.narration_enabled = False  # Override: disable
        override_template.tts_voice = "am_adam"  # Override: different voice
        template_repo.save(override_template)

        # Create game state from modified template
        game_state = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Campaign Override"
        )

        # Verify game state uses overridden settings
        assert game_state is not None
        assert game_state.narration_enabled is False  # From override
        assert game_state.tts_voice == "am_adam"  # From override

        # Verify TTS service sees overridden settings
        assert tts_service.is_narration_enabled() is False
        assert tts_service.get_current_voice() == "am_adam"

    def test_hierarchy_with_partial_instance_override(
        self, container: ServiceContainer, sample_template: CampaignTemplateModel
    ) -> None:
        """Test instance overriding only some settings."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()

        # Create template with partial override - narration disabled, voice unchanged
        partial_template = sample_template.model_copy()
        partial_template.narration_enabled = False  # Override narration only
        # Keep template voice (af_heart) unchanged
        template_repo.save(partial_template)

        # Create game state from template
        game_state = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Partial Override"
        )

        # Verify mixed inheritance
        assert game_state is not None
        assert game_state.narration_enabled is False  # Changed setting
        assert game_state.tts_voice == "af_heart"  # From original template

    def test_runtime_toggle_preserves_defaults(
        self, container: ServiceContainer, sample_template: CampaignTemplateModel
    ) -> None:
        """Test that runtime toggles don't affect template/instance defaults."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        tts_service = container.get_tts_integration_service()

        # Save template
        template_repo.save(sample_template)

        # Create first game state
        self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Runtime Toggle"
        )

        # Initial state from template
        assert tts_service.is_narration_enabled() is True

        # Toggle narration off during gameplay
        tts_service.set_narration_enabled(False)
        assert tts_service.is_narration_enabled() is False

        # Verify template unchanged
        saved_template = template_repo.get("template_1")
        assert saved_template is not None
        assert saved_template.narration_enabled is True  # Unchanged

        # If we start a new game from same template, it should use original settings
        import time

        time.sleep(1)  # Ensure different timestamp
        self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Runtime Toggle 2"
        )

        # New game should have original settings
        assert tts_service.is_narration_enabled() is True  # Back to template default

    def test_hierarchy_with_missing_template(self, container: ServiceContainer) -> None:
        """Test behavior when template is missing (standalone campaign)."""
        container.get_campaign_service()
        instance_repo = container.get_campaign_instance_repository()
        game_state_repo = container.get_game_state_repository()
        tts_service = container.get_tts_integration_service()

        # Create instance without template
        instance = CampaignInstanceModel(
            id="standalone_1",
            name="Standalone Campaign",
            template_id=None,  # No template
            character_ids=[],
            current_location="Unknown",
            event_log_path="events.json",
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
            narration_enabled=True,  # Instance settings only
            tts_voice="bf_emma",
        )
        instance_repo.save(instance)

        # Create game state directly (simulating load game)
        game_state = GameStateModel(
            campaign_id=instance.id,
            campaign_name=instance.name,
            narration_enabled=instance.narration_enabled or False,
            tts_voice=instance.tts_voice or "af_heart",
        )
        game_state_repo.save_game_state(game_state)

        # Verify TTS service uses instance settings
        assert tts_service.is_narration_enabled() is True
        assert tts_service.get_current_voice() == "bf_emma"
