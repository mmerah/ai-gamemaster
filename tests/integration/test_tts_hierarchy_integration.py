"""
Integration tests for TTS settings hierarchy behavior.
Tests the complete flow from template -> instance -> game state.
"""
import pytest
from datetime import datetime, timezone
from app.core.container import ServiceContainer
from app.game.unified_models import (
    CampaignTemplateModel, CampaignInstanceModel, GameStateModel,
    LocationModel, HouseRulesModel
)


class TestTTSHierarchyIntegration:
    """Test the complete TTS settings hierarchy flow."""
    
    def _create_game_state_from_template(self, campaign_service, game_state_repo, template_id, instance_name, party_character_ids=None):
        """Helper method to create game state from template, handling the conversion properly."""
        if party_character_ids is None:
            party_character_ids = []
            
        # Clear any existing game state
        try:
            game_state_repo.delete_game_state()
        except:
            pass
            
        # Get initial state from campaign service
        initial_state = campaign_service.start_campaign_from_template(
            template_id=template_id,
            instance_name=instance_name,
            party_character_ids=party_character_ids
        )
        
        if not initial_state:
            return None
            
        # Convert to game state model (copied from route logic)
        from app.game.unified_models import GameStateModel, CharacterInstanceModel, NPCModel, QuestModel, CombatStateModel
        
        party_instances = {}
        for char_id_key, char_data in initial_state.get("party", {}).items():
            party_instances[char_id_key] = CharacterInstanceModel(**char_data)
        
        known_npcs = {}
        for npc_id_key, npc_data in initial_state.get("known_npcs", {}).items():
            if isinstance(npc_data, dict):
                known_npcs[npc_id_key] = NPCModel(**npc_data)
            elif isinstance(npc_data, NPCModel):
                known_npcs[npc_id_key] = npc_data
        
        active_quests = {}
        for q_id_key, q_data in initial_state.get("active_quests", {}).items():
            if isinstance(q_data, dict):
                active_quests[q_id_key] = QuestModel(**q_data)
            elif isinstance(q_data, QuestModel):
                active_quests[q_id_key] = q_data
        
        combat_data = initial_state.get("combat", {})
        if isinstance(combat_data, dict):
            combat_data.pop("_combat_just_started_flag", None)
            combat_state_obj = CombatStateModel(**combat_data)
        else:
            combat_state_obj = combat_data
        
        game_state_data_for_model = {
            "party": party_instances,
            "current_location": initial_state.get("current_location", {"name": "Unknown", "description": ""}),
            "chat_history": initial_state.get("chat_history", []),
            "pending_player_dice_requests": initial_state.get("pending_player_dice_requests", []),
            "combat": combat_state_obj,
            "campaign_goal": initial_state.get("campaign_goal", "No specific goal set."),
            "known_npcs": known_npcs,
            "active_quests": active_quests,
            "world_lore": initial_state.get("world_lore", []),
            "event_summary": initial_state.get("event_summary", []),
            "campaign_id": initial_state.get("campaign_id"),
            "narration_enabled": initial_state.get("narration_enabled", False),
            "tts_voice": initial_state.get("tts_voice", "af_heart")
        }
        final_game_state = GameStateModel(**game_state_data_for_model)
        game_state_repo.save_game_state(final_game_state)
        
        return final_game_state
    
    @pytest.fixture
    def container(self, tmp_path):
        """Create a service container with file-based repositories."""
        config = {
            'GAME_STATE_REPO_TYPE': 'file',
            'CAMPAIGNS_DIR': str(tmp_path / 'campaigns'),
            'CHARACTER_TEMPLATES_DIR': str(tmp_path / 'character_templates'),
            'CAMPAIGN_TEMPLATES_DIR': str(tmp_path / 'campaign_templates'),
            'TTS_PROVIDER': 'disabled',  # Disable actual TTS for tests
            'RAG_ENABLED': 'false'
        }
        container = ServiceContainer(config)
        container.initialize()
        return container
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample campaign template with TTS settings."""
        return CampaignTemplateModel(
            id="template_1",
            name="Adventure Template",
            description="A test template",
            campaign_goal="Test the TTS hierarchy",
            starting_location=LocationModel(
                name="Test Town",
                description="A place for testing"
            ),
            opening_narrative="Welcome to the test!",
            narration_enabled=True,  # Template default: enabled
            tts_voice="af_heart",    # Template default voice
            house_rules=HouseRulesModel()
        )
    
    def test_hierarchy_template_to_instance_to_game_state(self, container, sample_template):
        """Test the complete hierarchy flow."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        tts_service = container.get_tts_integration_service()
        
        # Save the template
        template_repo.save_template(sample_template)
        
        # Create game state from template
        game_state = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Campaign 1"
        )
        
        # Verify game state inherited template settings
        assert game_state is not None
        assert game_state.narration_enabled is True  # From template
        assert game_state.tts_voice == "af_heart"    # From template
        
        # Verify TTS service sees these settings
        assert tts_service.is_narration_enabled() is True
        assert tts_service.get_current_voice() == "af_heart"
    
    def test_hierarchy_with_instance_override(self, container, sample_template):
        """Test instance overriding template settings."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        tts_service = container.get_tts_integration_service()
        
        # Create template with different settings to simulate override
        override_template = sample_template.model_copy()
        override_template.narration_enabled = False  # Override: disable
        override_template.tts_voice = "am_adam"     # Override: different voice
        template_repo.save_template(override_template)
        
        # Create game state from modified template
        game_state = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Campaign Override"
        )
        
        # Verify game state uses overridden settings
        assert game_state.narration_enabled is False  # From override
        assert game_state.tts_voice == "am_adam"      # From override
        
        # Verify TTS service sees overridden settings
        assert tts_service.is_narration_enabled() is False
        assert tts_service.get_current_voice() == "am_adam"
    
    def test_hierarchy_with_partial_instance_override(self, container, sample_template):
        """Test instance overriding only some settings."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        
        # Create template with partial override - narration disabled, voice unchanged
        partial_template = sample_template.model_copy()
        partial_template.narration_enabled = False  # Override narration only
        # Keep template voice (af_heart) unchanged
        template_repo.save_template(partial_template)
        
        # Create game state from template
        game_state = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Partial Override"
        )
        
        # Verify mixed inheritance
        assert game_state.narration_enabled is False  # Changed setting
        assert game_state.tts_voice == "af_heart"    # From original template
    
    def test_runtime_toggle_preserves_defaults(self, container, sample_template):
        """Test that runtime toggles don't affect template/instance defaults."""
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        tts_service = container.get_tts_integration_service()
        
        # Save template
        template_repo.save_template(sample_template)
        
        # Create first game state
        game_state = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Runtime Toggle"
        )
        
        # Initial state from template
        assert tts_service.is_narration_enabled() is True
        
        # Toggle narration off during gameplay
        tts_service.set_narration_enabled(False)
        assert tts_service.is_narration_enabled() is False
        
        # Verify template unchanged
        saved_template = template_repo.get_template("template_1")
        assert saved_template.narration_enabled is True  # Unchanged
        
        # If we start a new game from same template, it should use original settings
        import time
        time.sleep(1)  # Ensure different timestamp
        game_state2 = self._create_game_state_from_template(
            campaign_service, game_state_repo, "template_1", "Test Runtime Toggle 2"
        )
        
        # New game should have original settings
        assert tts_service.is_narration_enabled() is True  # Back to template default
    
    def test_hierarchy_with_missing_template(self, container):
        """Test behavior when template is missing (standalone campaign)."""
        campaign_service = container.get_campaign_service()
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
            tts_voice="bf_emma"
        )
        instance_repo.create_instance(instance)
        
        # Create game state directly (simulating load game)
        game_state = GameStateModel(
            campaign_id=instance.id,
            campaign_name=instance.name,
            narration_enabled=instance.narration_enabled or False,
            tts_voice=instance.tts_voice or "af_heart"
        )
        game_state_repo.save_game_state(game_state)
        
        # Verify TTS service uses instance settings
        assert tts_service.is_narration_enabled() is True
        assert tts_service.get_current_voice() == "bf_emma"