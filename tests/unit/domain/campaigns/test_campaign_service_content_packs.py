"""Tests for content pack functionality in CampaignService."""

from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import Mock, patch

import pytest

from app.domain.campaigns.service import CampaignService
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
    def service(
        self,
        mock_campaign_template_repo: Mock,
        mock_character_template_repo: Mock,
        mock_campaign_instance_repo: Mock,
    ) -> CampaignService:
        """Create a CampaignService instance."""
        return CampaignService(
            mock_campaign_template_repo,
            mock_character_template_repo,
            mock_campaign_instance_repo,
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

    def test_merge_content_packs_campaign_priority(
        self,
        service: CampaignService,
    ) -> None:
        """Test that campaign packs have highest priority."""
        # Setup
        campaign_packs = ["campaign-pack-1", "campaign-pack-2"]
        character_packs = [
            ["char-pack-1", "shared-pack"],
            ["char-pack-2", "campaign-pack-1"],  # Duplicate
        ]

        # Execute
        result = service._merge_content_packs(campaign_packs, character_packs)

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
        service: CampaignService,
    ) -> None:
        """Test that system default is always included."""
        # Setup - no packs include system default
        campaign_packs = ["custom-pack-1"]
        character_packs = [["custom-pack-2"]]

        # Execute
        result = service._merge_content_packs(campaign_packs, character_packs)

        # Verify
        assert "dnd_5e_srd" in result
        assert result[-1] == "dnd_5e_srd"

    def test_merge_content_packs_system_default_not_duplicated(
        self,
        service: CampaignService,
    ) -> None:
        """Test that system default is not duplicated if already present."""
        # Setup - campaign includes system default
        campaign_packs = ["custom-pack", "dnd_5e_srd"]
        character_packs = [["dnd_5e_srd", "another-pack"]]

        # Execute
        result = service._merge_content_packs(campaign_packs, character_packs)

        # Verify
        # System default should appear only once
        assert result.count("dnd_5e_srd") == 1
        # Should maintain priority position from campaign
        assert result.index("dnd_5e_srd") == 1

    def test_merge_content_packs_empty_inputs(
        self,
        service: CampaignService,
    ) -> None:
        """Test merging with empty inputs."""
        # Execute
        result = service._merge_content_packs([], [])

        # Verify
        assert result == ["dnd_5e_srd"]

    def test_merge_content_packs_order_preserved(
        self,
        service: CampaignService,
    ) -> None:
        """Test that order within categories is preserved."""
        # Setup
        campaign_packs = ["pack-a", "pack-b", "pack-c"]
        character_packs = [
            ["pack-d", "pack-e"],
            ["pack-f", "pack-g"],
        ]

        # Execute
        result = service._merge_content_packs(campaign_packs, character_packs)

        # Verify order
        assert result[:3] == ["pack-a", "pack-b", "pack-c"]
        # Character packs maintain relative order
        d_index = result.index("pack-d")
        e_index = result.index("pack-e")
        f_index = result.index("pack-f")
        g_index = result.index("pack-g")
        assert d_index < e_index
        assert f_index < g_index

    @patch("os.makedirs")
    def test_create_campaign_instance_with_content_packs(
        self,
        mock_makedirs: Mock,
        service: CampaignService,
        mock_campaign_template_repo: Mock,
        mock_character_template_repo: Mock,
        mock_campaign_instance_repo: Mock,
        campaign_template: CampaignTemplateModel,
        character_template_1: CharacterTemplateModel,
        character_template_2: CharacterTemplateModel,
    ) -> None:
        """Test creating campaign instance merges content packs correctly."""
        # Setup
        mock_campaign_template_repo.get_template.return_value = campaign_template

        # Mock character template validation
        validation_result = Mock()
        validation_result.to_dict.return_value = {
            "char-1": True,
            "char-2": True,
        }
        mock_character_template_repo.validate_template_ids.return_value = (
            validation_result
        )

        # Mock getting character templates
        def get_template_side_effect(char_id: str) -> Optional[CharacterTemplateModel]:
            if char_id == "char-1":
                return character_template_1
            elif char_id == "char-2":
                return character_template_2
            return None

        mock_character_template_repo.get_template.side_effect = get_template_side_effect

        mock_campaign_instance_repo.create_instance.return_value = True

        # Execute
        result = service.create_campaign_instance(
            "test-campaign",
            "Test Instance",
            ["char-1", "char-2"],
        )

        # Verify
        assert result is not None
        assert result.content_pack_priority is not None

        # Check merged content packs
        expected_order = [
            # Campaign packs first
            "campaign-pack-1",
            "campaign-pack-2",
            "dnd_5e_srd",  # From campaign
            # Character packs (no duplicates)
            "char-pack-1",
            "shared-pack",
            "char-pack-2",
            "custom-spells",
        ]
        assert result.content_pack_priority == expected_order

    def test_create_campaign_instance_missing_content_packs(
        self,
        service: CampaignService,
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
        mock_campaign_template_repo.get_template.return_value = template

        # Character without content_pack_ids
        char_template = Mock(spec=CharacterTemplateModel)
        char_template.id = "old-char"
        # No content_pack_ids attribute

        validation_result = Mock()
        validation_result.to_dict.return_value = {"old-char": True}
        mock_character_template_repo.validate_template_ids.return_value = (
            validation_result
        )
        mock_character_template_repo.get_template.return_value = char_template
        mock_campaign_instance_repo.create_instance.return_value = True

        # Execute
        result = service.create_campaign_instance(
            "old-campaign",
            "Test Instance",
            ["old-char"],
        )

        # Verify - should default to system pack
        assert result is not None
        assert result.content_pack_priority == ["dnd_5e_srd"]
