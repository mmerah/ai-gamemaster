"""Tests for content pack functionality in CampaignService."""

from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import Mock, patch

import pytest

from app.content.service import ContentService
from app.domain.campaigns.factories import CampaignFactory
from app.domain.campaigns.service import CampaignService
from app.domain.characters.factories import CharacterFactory
from app.models.campaign import CampaignInstanceModel, CampaignTemplateModel
from app.models.character import CharacterTemplateModel
from app.models.utils import LocationModel
from app.repositories.game.campaign_instance_repository import (
    CampaignInstanceRepository,
)
from app.repositories.game.campaign_template_repository import (
    CampaignTemplateRepository,
)
from app.repositories.game.character_template_repository import (
    CharacterTemplateRepository,
)


class TestCampaignServiceContentPacks:
    """Test content pack functionality in CampaignService."""

    @pytest.fixture
    def mock_campaign_template_repo(self) -> Mock:
        """Create a mock campaign template repository."""
        return Mock(spec=CampaignTemplateRepository)

    @pytest.fixture
    def mock_character_template_repo(self) -> Mock:
        """Create a mock character template repository."""
        return Mock(spec=CharacterTemplateRepository)

    @pytest.fixture
    def mock_campaign_instance_repo(self) -> Mock:
        """Create a mock campaign instance repository."""
        repo = Mock(spec=CampaignInstanceRepository)
        repo.base_dir = "/tmp/test_campaigns"
        return repo

    @pytest.fixture
    def mock_content_service(self) -> Mock:
        """Create a mock content service."""
        return Mock(spec=ContentService)

    @pytest.fixture
    def mock_campaign_factory(self) -> Mock:
        """Create a mock campaign factory."""
        return Mock(spec=CampaignFactory)

    @pytest.fixture
    def mock_character_factory(self) -> Mock:
        """Create a mock character factory."""
        return Mock(spec=CharacterFactory)

    @pytest.fixture
    def service(
        self,
        mock_campaign_factory: Mock,
        mock_character_factory: Mock,
        mock_campaign_template_repo: Mock,
        mock_character_template_repo: Mock,
        mock_campaign_instance_repo: Mock,
        mock_content_service: Mock,
    ) -> CampaignService:
        """Create a CampaignService instance."""
        return CampaignService(
            mock_campaign_factory,
            mock_character_factory,
            mock_campaign_template_repo,
            mock_character_template_repo,
            mock_campaign_instance_repo,
            mock_content_service,
        )

    @pytest.fixture
    def campaign_template(self) -> CampaignTemplateModel:
        """Create a sample campaign template with content packs."""
        return CampaignTemplateModel(
            id="test-campaign",
            name="Test Campaign",
            description="A test campaign",
            campaign_goal="Test the content pack system",
            starting_location=LocationModel(
                name="Test Town",
                description="A small test town",
            ),
            opening_narrative="Welcome to the test campaign!",
            starting_level=1,
            difficulty="normal",
            ruleset_id="dnd5e_standard",
            lore_id="generic_fantasy",
            content_pack_ids=["campaign-pack-1", "campaign-pack-2", "dnd_5e_srd"],
        )

    @pytest.fixture
    def character_template_1(self) -> CharacterTemplateModel:
        """Create a sample character template with content packs."""
        from app.models.utils import BaseStatsModel, ProficienciesModel

        return CharacterTemplateModel(
            id="char-1",
            name="Test Character 1",
            race="human",
            char_class="fighter",
            level=1,
            background="soldier",
            alignment="lawful_good",
            base_stats=BaseStatsModel(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8),
            proficiencies=ProficienciesModel(),
            content_pack_ids=["char-pack-1", "shared-pack", "dnd_5e_srd"],
        )

    @pytest.fixture
    def character_template_2(self) -> CharacterTemplateModel:
        """Create another character template with different content packs."""
        from app.models.utils import BaseStatsModel, ProficienciesModel

        return CharacterTemplateModel(
            id="char-2",
            name="Test Character 2",
            race="elf",
            char_class="wizard",
            level=1,
            background="sage",
            alignment="neutral_good",
            base_stats=BaseStatsModel(STR=8, DEX=14, CON=12, INT=16, WIS=14, CHA=10),
            proficiencies=ProficienciesModel(),
            content_pack_ids=["char-pack-2", "shared-pack", "custom-spells"],
        )

    def test_create_campaign_instance_with_content_packs(
        self,
        service: CampaignService,
        mock_campaign_factory: Mock,
        mock_campaign_template_repo: Mock,
        mock_character_template_repo: Mock,
        mock_campaign_instance_repo: Mock,
        campaign_template: CampaignTemplateModel,
        character_template_1: CharacterTemplateModel,
        character_template_2: CharacterTemplateModel,
    ) -> None:
        """Test creating campaign instance uses factory correctly."""
        # Setup
        mock_campaign_template_repo.get.return_value = campaign_template

        # Mock getting character templates
        def get_template_side_effect(char_id: str) -> Optional[CharacterTemplateModel]:
            if char_id == "char-1":
                return character_template_1
            elif char_id == "char-2":
                return character_template_2
            return None

        mock_character_template_repo.get.side_effect = get_template_side_effect

        # Mock factory creating campaign instance
        mock_instance = CampaignInstanceModel(
            id="test-instance-1",
            name="Test Instance",
            template_id="test-campaign",
            character_ids=[],  # Will be set by service
            current_location="Test Town",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path="campaigns/test-instance-1/event_log.json",
            content_pack_priority=[
                "campaign-pack-1",
                "campaign-pack-2",
                "dnd_5e_srd",
                "char-pack-1",
                "shared-pack",
                "char-pack-2",
                "custom-spells",
            ],
        )
        mock_campaign_factory.create_campaign_instance.return_value = mock_instance
        mock_campaign_instance_repo.save.return_value = True

        # Execute
        result = service.create_campaign_instance(
            "test-campaign",
            "Test Instance",
            ["char-1", "char-2"],
        )

        # Verify
        assert result is not None
        assert result.character_ids == ["char-1", "char-2"]

        # Verify factory was called with correct arguments
        mock_campaign_factory.create_campaign_instance.assert_called_once_with(
            campaign_template,
            "Test Instance",
            [
                ["char-pack-1", "shared-pack", "dnd_5e_srd"],  # From char-1
                ["char-pack-2", "shared-pack", "custom-spells"],  # From char-2
            ],
        )

        # Verify instance was saved
        mock_campaign_instance_repo.save.assert_called_once_with(mock_instance)

    def test_create_campaign_instance_missing_content_packs(
        self,
        service: CampaignService,
        mock_campaign_factory: Mock,
        mock_campaign_template_repo: Mock,
        mock_character_template_repo: Mock,
        mock_campaign_instance_repo: Mock,
    ) -> None:
        """Test creating instance when templates lack content_pack_ids."""
        # Setup - template without content_pack_ids
        template = CampaignTemplateModel(
            id="old-campaign",
            name="Old Campaign",
            description="Campaign without content packs",
            campaign_goal="Test backwards compatibility",
            starting_location=LocationModel(name="Town", description="A town"),
            opening_narrative="Welcome!",
            starting_level=1,
            difficulty="normal",
            # No content_pack_ids field
        )
        mock_campaign_template_repo.get.return_value = template

        # Character without content_pack_ids
        char_template = Mock(spec=CharacterTemplateModel)
        char_template.id = "old-char"
        # No content_pack_ids attribute

        mock_character_template_repo.get.return_value = char_template

        # Mock factory creating instance with default content pack
        mock_instance = CampaignInstanceModel(
            id="old-instance-1",
            name="Test Instance",
            template_id="old-campaign",
            character_ids=[],
            current_location="Town",
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path="campaigns/old-instance-1/event_log.json",
            content_pack_priority=["dnd_5e_srd"],  # Default when no packs specified
        )
        mock_campaign_factory.create_campaign_instance.return_value = mock_instance
        mock_campaign_instance_repo.save.return_value = True

        # Execute
        result = service.create_campaign_instance(
            "old-campaign",
            "Test Instance",
            ["old-char"],
        )

        # Verify - should have been called with empty packs list
        assert result is not None
        mock_campaign_factory.create_campaign_instance.assert_called_once_with(
            template,
            "Test Instance",
            [["dnd_5e_srd"]],  # Default when character has no content_pack_ids
        )
