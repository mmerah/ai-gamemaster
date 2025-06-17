"""Tests for CampaignFactory."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from unittest.mock import Mock, patch

import pytest

from app.content.service import ContentService
from app.domain.campaigns.campaign_factory import CampaignFactory
from app.domain.characters.character_factory import CharacterFactory
from app.models.campaign import CampaignInstanceModel, CampaignTemplateModel
from app.models.character import CharacterInstanceModel
from app.models.combat import CombatStateModel
from app.models.game_state import GameStateModel
from app.models.utils import LocationModel, NPCModel, QuestModel


class TestCampaignFactory:
    """Test the CampaignFactory class."""

    @pytest.fixture
    def mock_content_service(self) -> Mock:
        """Create a mock content service."""
        return Mock(spec=ContentService)

    @pytest.fixture
    def mock_character_factory(self) -> Mock:
        """Create a mock character factory."""
        return Mock(spec=CharacterFactory)

    @pytest.fixture
    def factory(
        self,
        mock_content_service: Mock,
        mock_character_factory: Mock,
    ) -> CampaignFactory:
        """Create a CampaignFactory instance."""
        return CampaignFactory(mock_content_service, mock_character_factory)

    @pytest.fixture
    def campaign_template(self) -> CampaignTemplateModel:
        """Create a sample campaign template."""
        return CampaignTemplateModel(
            id="test-campaign",
            name="Test Campaign",
            description="A test campaign",
            campaign_goal="Test the factory",
            starting_location=LocationModel(
                name="Test Town",
                description="A small test town",
            ),
            opening_narrative="Welcome to the test campaign!",
            starting_level=1,
            difficulty="normal",
            narration_enabled=True,
            tts_voice="alloy",
            ruleset_id="dnd5e_standard",
            lore_id="generic_fantasy",
            content_pack_ids=["campaign-pack", "dnd_5e_srd"],
            initial_npcs={
                "npc-1": NPCModel(
                    id="npc-1",
                    name="Innkeeper Bob",
                    description="A friendly innkeeper",
                    last_location="Test Town",
                )
            },
            initial_quests={
                "quest-1": QuestModel(
                    id="quest-1",
                    title="Find the Missing Cat",
                    description="The innkeeper's cat has gone missing",
                    status="active",
                )
            },
            world_lore=[
                "The town was founded 100 years ago",
                "A peaceful farming community",
            ],
        )

    def test_merge_content_packs_campaign_priority(
        self,
        factory: CampaignFactory,
    ) -> None:
        """Test that campaign packs have highest priority."""
        # Setup
        campaign_packs = ["campaign-pack-1", "campaign-pack-2"]
        character_packs = [
            ["char-pack-1", "shared-pack"],
            ["char-pack-2", "campaign-pack-1"],  # Duplicate
        ]

        # Execute
        result = factory._merge_content_packs(campaign_packs, character_packs)

        # Verify
        # Campaign packs should come first
        assert result[0] == "campaign-pack-1"
        assert result[1] == "campaign-pack-2"
        # Character packs should follow (no duplicates)
        assert "char-pack-1" in result
        assert "char-pack-2" in result
        assert "shared-pack" in result
        # System default should be last
        assert result[-1] == "dnd_5e_srd"
        # No duplicates
        assert len(result) == len(set(result))

    def test_merge_content_packs_system_default_included(
        self,
        factory: CampaignFactory,
    ) -> None:
        """Test that system default is always included."""
        # Setup - no packs include system default
        campaign_packs = ["custom-pack-1"]
        character_packs = [["custom-pack-2"]]

        # Execute
        result = factory._merge_content_packs(campaign_packs, character_packs)

        # Verify
        assert "dnd_5e_srd" in result
        assert result[-1] == "dnd_5e_srd"

    def test_merge_content_packs_empty_inputs(
        self,
        factory: CampaignFactory,
    ) -> None:
        """Test merging with empty inputs."""
        # Execute
        result = factory._merge_content_packs([], [])

        # Verify
        assert result == ["dnd_5e_srd"]

    def test_create_campaign_instance(
        self,
        factory: CampaignFactory,
        campaign_template: CampaignTemplateModel,
    ) -> None:
        """Test creating a campaign instance from a template."""
        # Setup
        character_packs = [["char-pack-1"], ["char-pack-2"]]

        # Execute
        with patch("app.domain.campaigns.campaign_factory.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 30, 45)
            result = factory.create_campaign_instance(
                campaign_template,
                "My Adventure",
                character_packs,
            )

        # Verify
        assert isinstance(result, CampaignInstanceModel)
        assert result.id == "test-campaign_20240115_103045"
        assert result.name == "My Adventure"
        assert result.template_id == "test-campaign"
        assert result.current_location == "Test Town"
        assert result.session_count == 0
        assert result.in_combat is False
        assert result.event_summary == []
        assert (
            result.event_log_path
            == "campaigns/test-campaign_20240115_103045/event_log.json"
        )
        assert result.content_pack_priority == [
            "campaign-pack",
            "dnd_5e_srd",
            "char-pack-1",
            "char-pack-2",
        ]
        # TTS settings from template
        assert result.narration_enabled is True
        assert result.tts_voice == "alloy"

    def test_create_campaign_instance_default_name(
        self,
        factory: CampaignFactory,
        campaign_template: CampaignTemplateModel,
    ) -> None:
        """Test creating a campaign instance with default name."""
        # Execute
        result = factory.create_campaign_instance(campaign_template)

        # Verify
        assert result.name == "Test Campaign Campaign"

    def test_create_initial_game_state(
        self,
        factory: CampaignFactory,
        campaign_template: CampaignTemplateModel,
    ) -> None:
        """Test creating initial game state."""
        # Setup
        campaign_instance = CampaignInstanceModel(
            id="instance-1",
            name="My Adventure",
            template_id="test-campaign",
            character_ids=["char-1", "char-2"],
            current_location="Test Town",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path="campaigns/instance-1/event_log.json",
            content_pack_priority=["campaign-pack", "dnd_5e_srd"],
            narration_enabled=False,  # Override template
            tts_voice="nova",  # Override template
        )

        party_characters: Dict[str, CharacterInstanceModel] = {
            "char-1": Mock(spec=CharacterInstanceModel),
            "char-2": Mock(spec=CharacterInstanceModel),
        }

        # Execute
        result = factory.create_initial_game_state(
            campaign_instance,
            campaign_template,
            party_characters,
        )

        # Verify
        assert isinstance(result, GameStateModel)
        assert result.campaign_id == "instance-1"
        assert result.campaign_name == "My Adventure"
        assert result.party == party_characters
        assert result.current_location == campaign_template.starting_location
        assert result.campaign_goal == "Test the factory"
        assert result.known_npcs == campaign_template.initial_npcs
        assert result.active_quests == campaign_template.initial_quests
        assert result.world_lore == campaign_template.world_lore
        assert result.event_summary == []
        # TTS settings hierarchy: instance overrides template
        assert result.narration_enabled is False
        assert result.tts_voice == "nova"
        assert result.active_ruleset_id == "dnd5e_standard"
        assert result.active_lore_id == "generic_fantasy"
        assert result.event_log_path == "campaigns/instance-1/event_log.json"
        # Chat history should have opening narrative
        assert len(result.chat_history) == 1
        assert result.chat_history[0].content == "Welcome to the test campaign!"
        assert result.chat_history[0].role == "assistant"
        # Combat should be inactive
        assert isinstance(result.combat, CombatStateModel)
        assert result.combat.is_active is False
        assert result.combat.combatants == []
        assert result.content_pack_priority == ["campaign-pack", "dnd_5e_srd"]

    def test_create_initial_game_state_no_opening_narrative(
        self,
        factory: CampaignFactory,
    ) -> None:
        """Test creating game state without opening narrative."""
        # Setup
        template = CampaignTemplateModel(
            id="test-campaign",
            name="Test Campaign",
            description="A test campaign",
            campaign_goal="Test the factory",
            starting_location=LocationModel(name="Test Town", description="A town"),
            opening_narrative="",  # Empty opening narrative
            starting_level=1,
            difficulty="normal",
        )

        campaign_instance = CampaignInstanceModel(
            id="instance-1",
            name="My Adventure",
            template_id="test-campaign",
            character_ids=[],
            current_location="Test Town",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path="campaigns/instance-1/event_log.json",
            content_pack_priority=["dnd_5e_srd"],
        )

        # Execute
        result = factory.create_initial_game_state(
            campaign_instance,
            template,
            {},
        )

        # Verify
        assert len(result.chat_history) == 0

    def test_create_game_state_from_instance(
        self,
        factory: CampaignFactory,
        campaign_template: CampaignTemplateModel,
    ) -> None:
        """Test creating game state from existing instance."""
        # Setup
        campaign_instance = CampaignInstanceModel(
            id="instance-1",
            name="Ongoing Adventure",
            template_id="test-campaign",
            character_ids=["char-1"],
            current_location="Test Town",
            session_count=1,
            in_combat=False,
            event_summary=["Session 1: Met the innkeeper"],
            event_log_path="campaigns/instance-1/event_log.json",
            content_pack_priority=["campaign-pack", "dnd_5e_srd"],
            narration_enabled=True,
            tts_voice="echo",
        )

        party_characters: Dict[str, CharacterInstanceModel] = {
            "char-1": Mock(spec=CharacterInstanceModel)
        }

        # Execute
        result = factory.create_game_state_from_instance(
            campaign_instance,
            campaign_template,
            party_characters,
        )

        # Verify
        assert isinstance(result, GameStateModel)
        assert result.campaign_id == "instance-1"
        assert result.campaign_name == "Ongoing Adventure"
        assert result.event_summary == ["Session 1: Met the innkeeper"]
        # Should still have opening narrative in chat history
        assert len(result.chat_history) == 1
        assert result.chat_history[0].content == "Welcome to the test campaign!"

    def test_create_template_preview_state(
        self,
        factory: CampaignFactory,
        campaign_template: CampaignTemplateModel,
    ) -> None:
        """Test creating minimal state for template preview."""
        # Execute
        result = factory.create_template_preview_state(campaign_template)

        # Verify
        assert isinstance(result, GameStateModel)
        assert result.campaign_id == "test-campaign"
        assert result.campaign_name == "Test Campaign"
        assert result.party == {}  # No party for preview
        assert result.current_location == campaign_template.starting_location
        assert result.campaign_goal == "Test the factory"
        assert result.known_npcs == campaign_template.initial_npcs
        assert result.active_quests == campaign_template.initial_quests
        assert result.world_lore == campaign_template.world_lore
        assert result.event_summary == []
        assert result.narration_enabled is True
        assert result.tts_voice == "alloy"
        assert result.active_ruleset_id == "dnd5e_standard"
        assert result.active_lore_id == "generic_fantasy"
        assert result.event_log_path is None  # No event log for preview
        assert result.chat_history == []  # No chat for preview
        assert result.combat.is_active is False
        assert result.content_pack_priority == ["campaign-pack", "dnd_5e_srd"]

    def test_generate_id(
        self,
        factory: CampaignFactory,
    ) -> None:
        """Test ID generation."""
        # Execute
        id1 = factory._generate_id()
        id2 = factory._generate_id()

        # Verify
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2  # Should be unique
        assert len(id1) == 36  # UUID4 format
