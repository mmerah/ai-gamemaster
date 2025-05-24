"""
Unit tests for CampaignService.
"""
import unittest
import tempfile
import shutil
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from app.services.campaign_service import CampaignService
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.game.enhanced_models import CampaignDefinition, CampaignMetadata, CharacterTemplate


class TestCampaignService(unittest.TestCase):
    """Test cases for CampaignService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_campaign_repo = Mock(spec=CampaignRepository)
        self.mock_template_repo = Mock(spec=CharacterTemplateRepository)
        self.service = CampaignService(self.mock_campaign_repo, self.mock_template_repo)
        
        # Sample campaign data
        self.sample_campaign_data = {
            "id": "test_campaign",
            "name": "Test Campaign",
            "description": "A test campaign for unit testing",
            "party_character_ids": ["char1", "char2"],
            "starting_location": "Goblin Cave",
            "campaign_goal": "Defeat the goblin king"
        }
        
        # Sample character template
        self.sample_template = CharacterTemplate(
            id="char1",
            name="Test Fighter",
            race="Human",
            char_class="Fighter",
            level=1,
            alignment="Lawful Good",
            background="Soldier",
            subclass=None,
            portrait_path="fighter.jpg",
            base_stats={
                "STR": 16, "DEX": 13, "CON": 14,
                "INT": 10, "WIS": 12, "CHA": 11
            },
            proficiencies={
                "armor": ["light", "medium", "heavy", "shields"],
                "weapons": ["simple", "martial"],
                "tools": [],
                "saving_throws": ["STR", "CON"],
                "skills": ["Athletics", "Intimidation"]
            },
            languages=["Common"],
            starting_equipment=[
                {"name": "Chain Mail", "quantity": 1},
                {"name": "Shield", "quantity": 1},
                {"name": "Longsword", "quantity": 1}
            ],
            starting_gold=100,
            special_features=[],
            spell_list=[],
            background_feature="Military Rank"
        )

    def test_get_all_campaigns(self):
        """Test getting all campaigns."""
        expected_campaigns = [Mock(spec=CampaignMetadata)]
        self.mock_campaign_repo.get_all_campaigns.return_value = expected_campaigns
        
        result = self.service.get_all_campaigns()
        
        self.assertEqual(result, expected_campaigns)
        self.mock_campaign_repo.get_all_campaigns.assert_called_once()

    def test_get_campaign(self):
        """Test getting a specific campaign."""
        expected_campaign = Mock(spec=CampaignDefinition)
        self.mock_campaign_repo.get_campaign.return_value = expected_campaign
        
        result = self.service.get_campaign("test_campaign")
        
        self.assertEqual(result, expected_campaign)
        self.mock_campaign_repo.get_campaign.assert_called_once_with("test_campaign")

    def test_create_campaign_valid_data(self):
        """Test creating a campaign with valid data."""
        # Mock template validation
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        # Mock successful save
        self.mock_campaign_repo.save_campaign.return_value = True
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, CampaignDefinition)
        self.assertEqual(result.id, "test_campaign")
        self.assertEqual(result.name, "Test Campaign")
        
        # Check that starting_location was converted properly
        self.assertIsInstance(result.starting_location, dict)
        self.assertEqual(result.starting_location["name"], "Goblin Cave")
        self.assertEqual(result.starting_location["description"], "The adventure begins here.")

    def test_create_campaign_starting_location_string_conversion(self):
        """Test that string starting_location is converted to dict format."""
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        self.mock_campaign_repo.save_campaign.return_value = True
        
        # Test with string starting location
        campaign_data = self.sample_campaign_data.copy()
        campaign_data["starting_location"] = "Test Location"
        
        result = self.service.create_campaign(campaign_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.starting_location["name"], "Test Location")
        self.assertEqual(result.starting_location["description"], "The adventure begins here.")

    def test_create_campaign_empty_starting_location(self):
        """Test that empty starting_location gets default values."""
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        self.mock_campaign_repo.save_campaign.return_value = True
        
        # Test with empty starting location
        campaign_data = self.sample_campaign_data.copy()
        campaign_data["starting_location"] = ""
        
        result = self.service.create_campaign(campaign_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.starting_location["name"], "Unknown Starting Point")
        self.assertEqual(result.starting_location["description"], "The adventure's origin is yet to be defined.")

    def test_create_campaign_missing_required_fields(self):
        """Test creating a campaign with missing required fields."""
        # Test missing ID
        incomplete_data = self.sample_campaign_data.copy()
        del incomplete_data["id"]
        
        result = self.service.create_campaign(incomplete_data)
        self.assertIsNone(result)
        
        # Test missing name
        incomplete_data = self.sample_campaign_data.copy()
        del incomplete_data["name"]
        
        result = self.service.create_campaign(incomplete_data)
        self.assertIsNone(result)

    def test_create_campaign_invalid_template_ids(self):
        """Test creating a campaign with invalid character template IDs."""
        # Mock template validation with invalid templates
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": False  # char2 is invalid
        }
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNone(result)
        self.mock_template_repo.validate_template_ids.assert_called_once_with(["char1", "char2"])

    def test_create_campaign_save_failure(self):
        """Test creating a campaign when save operation fails."""
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        # Mock failed save
        self.mock_campaign_repo.save_campaign.return_value = False
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNone(result)

    def test_create_campaign_sets_defaults(self):
        """Test that campaign creation sets appropriate defaults."""
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        self.mock_campaign_repo.save_campaign.return_value = True
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.starting_level, 1)
        self.assertEqual(result.difficulty, "normal")
        self.assertIsInstance(result.created_date, datetime)
        self.assertIsNone(result.last_played)
        self.assertEqual(result.house_rules, {})
        self.assertEqual(result.initial_npcs, {})
        self.assertEqual(result.initial_quests, {})
        self.assertEqual(result.world_lore, [])
        self.assertEqual(result.event_summary, [])

    def test_update_campaign(self):
        """Test updating an existing campaign."""
        campaign = CampaignDefinition(
            id="test_campaign",
            name="Test Campaign",
            description="Updated description",
            created_date=datetime.now(timezone.utc),
            last_played=None,
            starting_level=1,
            difficulty="normal",
            party_character_ids=["char1", "char2"],
            starting_location={"name": "Test", "description": "Test"},
            campaign_goal="Test goal",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            event_summary=[],
            opening_narrative="Test",
            house_rules={}
        )
        
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        self.mock_campaign_repo.save_campaign.return_value = True
        
        result = self.service.update_campaign(campaign)
        
        self.assertTrue(result)
        self.mock_campaign_repo.save_campaign.assert_called_once_with(campaign)

    def test_update_campaign_invalid_templates(self):
        """Test updating a campaign with invalid template references."""
        campaign = CampaignDefinition(
            id="test_campaign",
            name="Test Campaign",
            description="Test",
            created_date=datetime.now(timezone.utc),
            last_played=None,
            starting_level=1,
            difficulty="normal",
            party_character_ids=["char1", "invalid_char"],
            starting_location={"name": "Test", "description": "Test"},
            campaign_goal="Test goal",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            event_summary=[],
            opening_narrative="Test",
            house_rules={}
        )
        
        self.mock_template_repo.validate_template_ids.return_value = {
            "char1": True, "invalid_char": False
        }
        self.mock_campaign_repo.save_campaign.return_value = True
        
        # Should still proceed but log warning
        with patch('app.services.campaign_service.logger') as mock_logger:
            result = self.service.update_campaign(campaign)
            
            self.assertTrue(result)
            mock_logger.warning.assert_called()

    def test_delete_campaign(self):
        """Test deleting a campaign."""
        self.mock_campaign_repo.delete_campaign.return_value = True
        
        result = self.service.delete_campaign("test_campaign")
        
        self.assertTrue(result)
        self.mock_campaign_repo.delete_campaign.assert_called_once_with("test_campaign")

    def test_start_campaign_success(self):
        """Test starting a campaign successfully."""
        # Create mock campaign
        campaign = CampaignDefinition(
            id="test_campaign",
            name="Test Campaign",
            description="Test",
            created_date=datetime.now(timezone.utc),
            last_played=None,
            starting_level=1,
            difficulty="normal",
            party_character_ids=["char1"],
            starting_location={"name": "Test Location", "description": "Test description"},
            campaign_goal="Test goal",
            initial_npcs={"npc1": {"name": "Test NPC", "description": "A test NPC"}},
            initial_quests={"quest1": {"title": "Test Quest", "description": "A test quest", "status": "active"}},
            world_lore=["Some lore"],
            event_summary=["An event"],
            opening_narrative="Welcome to the test campaign",
            house_rules={}
        )
        
        self.mock_campaign_repo.get_campaign.return_value = campaign
        self.mock_template_repo.get_template.return_value = self.sample_template
        
        result = self.service.start_campaign("test_campaign")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["campaign_id"], "test_campaign")
        self.assertEqual(result["campaign_name"], "Test Campaign")
        self.assertIn("char1", result["party"])
        self.assertEqual(result["current_location"], campaign.starting_location)
        self.assertEqual(result["campaign_goal"], campaign.campaign_goal)
        
        # Check that template was converted to character instance
        char_instance = result["party"]["char1"]
        self.assertEqual(char_instance["name"], "Test Fighter")
        self.assertEqual(char_instance["race"], "Human")
        self.assertEqual(char_instance["char_class"], "Fighter")
        
        # Check that last played was updated
        self.mock_campaign_repo.update_last_played.assert_called_once_with("test_campaign")

    def test_start_campaign_nonexistent(self):
        """Test starting a campaign that doesn't exist."""
        self.mock_campaign_repo.get_campaign.return_value = None
        
        result = self.service.start_campaign("nonexistent")
        
        self.assertIsNone(result)

    def test_start_campaign_missing_template(self):
        """Test starting a campaign with missing character template."""
        campaign = CampaignDefinition(
            id="test_campaign",
            name="Test Campaign",
            description="Test",
            created_date=datetime.now(timezone.utc),
            last_played=None,
            starting_level=1,
            difficulty="normal",
            party_character_ids=["char1", "missing_char"],
            starting_location={"name": "Test", "description": "Test"},
            campaign_goal="Test goal",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            event_summary=[],
            opening_narrative="Test",
            house_rules={}
        )
        
        self.mock_campaign_repo.get_campaign.return_value = campaign
        
        def mock_get_template(template_id):
            if template_id == "char1":
                return self.sample_template
            return None  # missing_char not found
        
        self.mock_template_repo.get_template.side_effect = mock_get_template
        
        with patch('app.services.campaign_service.logger') as mock_logger:
            result = self.service.start_campaign("test_campaign")
            
            self.assertIsNotNone(result)
            self.assertIn("char1", result["party"])
            self.assertNotIn("missing_char", result["party"])
            mock_logger.warning.assert_called()

    def test_template_to_character_instance_hp_calculation(self):
        """Test HP calculation in template conversion."""
        # Test level 1 character
        result = self.service._template_to_character_instance(self.sample_template)
        
        # Fighter has d10 hit die, CON modifier is +2 (14 CON)
        # Level 1: max_hp = 10 + 2 = 12
        self.assertEqual(result["max_hp"], 12)
        self.assertEqual(result["current_hp"], 12)
        
        # Test higher level character
        high_level_template = self.sample_template.model_copy(deep=True)
        high_level_template.level = 3
        
        result = self.service._template_to_character_instance(high_level_template)
        
        # Level 3: max_hp = 10 + 2 (level 1) + 2 * (5.5 + 2) (levels 2-3) = 27
        self.assertEqual(result["max_hp"], 27)

    def test_template_to_character_instance_ac_calculation(self):
        """Test AC calculation in template conversion."""
        # Test with armor
        result = self.service._template_to_character_instance(self.sample_template)
        
        # Chain mail provides AC 16 (heavy armor, no dex bonus)
        self.assertEqual(result["armor_class"], 18)  # 16 + 2 (shield)
        
        # Test with no armor (unarmored)
        unarmored_template = self.sample_template.model_copy(deep=True)
        unarmored_template.starting_equipment = []
        
        result = self.service._template_to_character_instance(unarmored_template)
        
        # Unarmored AC = 10 + DEX mod = 10 + 1 = 11
        self.assertEqual(result["armor_class"], 11)

    def test_template_to_character_instance_with_missing_d5e_data(self):
        """Test character instance creation when D&D 5e data is missing."""
        # Create service without D&D 5e data
        service_no_data = CampaignService(self.mock_campaign_repo, self.mock_template_repo)
        service_no_data.d5e_classes = {}
        
        result = service_no_data._template_to_character_instance(self.sample_template)
        
        # The character factory is already created with loaded D&D data during initialization
        # Fighter has d10 hit die, CON modifier is +2 (14 CON)
        # Level 1: max_hp = 10 + 2 = 12
        self.assertEqual(result["max_hp"], 12)

    def test_get_campaign_summary(self):
        """Test getting campaign summary."""
        campaign = CampaignDefinition(
            id="test_campaign",
            name="Test Campaign",
            description="Test description",
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
            starting_level=1,
            difficulty="normal",
            party_character_ids=["char1", "char2"],
            starting_location={"name": "Test", "description": "Test"},
            campaign_goal="Test goal",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            event_summary=[],
            opening_narrative="Test",
            house_rules={}
        )
        
        self.mock_campaign_repo.get_campaign.return_value = campaign
        
        result = self.service.get_campaign_summary("test_campaign")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "test_campaign")
        self.assertEqual(result["name"], "Test Campaign")
        self.assertEqual(result["party_size"], 2)
        self.assertEqual(result["starting_level"], 1)
        self.assertEqual(result["difficulty"], "normal")

    def test_get_campaign_summary_nonexistent(self):
        """Test getting summary for nonexistent campaign."""
        self.mock_campaign_repo.get_campaign.return_value = None
        
        result = self.service.get_campaign_summary("nonexistent")
        
        self.assertIsNone(result)

    @patch('app.services.campaign_service.logger')
    def test_error_handling_in_create_campaign(self, mock_logger):
        """Test error handling in create_campaign method."""
        # Mock an exception during validation
        self.mock_template_repo.validate_template_ids.side_effect = Exception("Test error")
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNone(result)
        mock_logger.error.assert_called()

    @patch('app.services.campaign_service.logger')
    def test_error_handling_in_start_campaign(self, mock_logger):
        """Test error handling in start_campaign method."""
        # Mock an exception during campaign retrieval
        self.mock_campaign_repo.get_campaign.side_effect = Exception("Test error")
        
        result = self.service.start_campaign("test_campaign")
        
        self.assertIsNone(result)
        mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()
