"""
Unit tests for CampaignService.
"""
import unittest
import tempfile
import shutil
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from app.services.campaign_service import CampaignService
from app.repositories.campaign_template_repository import CampaignTemplateRepository, CampaignTemplateMetadata
from app.repositories.campaign_instance_repository import CampaignInstanceRepository
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.game.unified_models import CharacterTemplateModel, CampaignTemplateModel


class TestCampaignService(unittest.TestCase):
    """Test cases for CampaignService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_campaign_template_repo = Mock(spec=CampaignTemplateRepository)
        self.mock_character_template_repo = Mock(spec=CharacterTemplateRepository)
        self.mock_instance_repo = Mock(spec=CampaignInstanceRepository)
        self.service = CampaignService(self.mock_campaign_template_repo, self.mock_character_template_repo, self.mock_instance_repo)
        
        # Sample campaign data
        self.sample_campaign_data = {
            "id": "test_campaign",
            "name": "Test Campaign",
            "description": "A test campaign for unit testing",
            "starting_location": "Goblin Cave",
            "campaign_goal": "Defeat the goblin king"
        }
        
        # Sample character template
        self.sample_template = CharacterTemplateModel(
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
                {"id": "chain_mail", "name": "Chain Mail", "description": "Heavy armor", "quantity": 1},
                {"id": "shield", "name": "Shield", "description": "+2 AC", "quantity": 1},
                {"id": "longsword", "name": "Longsword", "description": "Martial weapon", "quantity": 1}
            ],
            starting_gold=100,
            spells_known=[],
            cantrips_known=[],
            racial_traits=[],
            class_features=[],
            feats=[],
            personality_traits=[],
            ideals=[],
            bonds=[],
            flaws=[]
        )

    def test_get_all_campaigns(self):
        """Test getting all campaigns."""
        expected_campaigns = [Mock(spec=CampaignTemplateMetadata)]
        self.mock_campaign_template_repo.get_all_template_metadata.return_value = expected_campaigns
        
        result = self.service.get_all_campaigns()
        
        self.assertEqual(result, expected_campaigns)
        self.mock_campaign_template_repo.get_all_template_metadata.assert_called_once()

    def test_get_campaign(self):
        """Test getting a specific campaign."""
        expected_campaign = Mock(spec=CampaignTemplateModel)
        self.mock_campaign_template_repo.get_template.return_value = expected_campaign
        
        result = self.service.get_campaign("test_campaign")
        
        self.assertEqual(result, expected_campaign)
        self.mock_campaign_template_repo.get_template.assert_called_once_with("test_campaign")

    def test_create_campaign_valid_data(self):
        """Test creating a campaign with valid data."""
        # Mock template validation
        self.mock_character_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        # Mock successful save
        self.mock_campaign_template_repo.save_template.return_value = True
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, CampaignTemplateModel)
        self.assertEqual(result.id, "test_campaign")
        self.assertEqual(result.name, "Test Campaign")
        
        # Check that starting_location was converted properly
        from app.game.unified_models import LocationModel
        self.assertIsInstance(result.starting_location, LocationModel)
        self.assertEqual(result.starting_location.name, "Goblin Cave")
        self.assertEqual(result.starting_location.description, "The adventure begins here.")

    def test_create_campaign_starting_location_string_conversion(self):
        """Test that string starting_location is converted to dict format."""
        self.mock_character_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        self.mock_campaign_template_repo.save_template.return_value = True
        
        # Test with string starting location
        campaign_data = self.sample_campaign_data.copy()
        campaign_data["starting_location"] = "Test Location"
        
        result = self.service.create_campaign(campaign_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.starting_location.name, "Test Location")
        self.assertEqual(result.starting_location.description, "The adventure begins here.")

    def test_create_campaign_empty_starting_location(self):
        """Test that empty starting_location gets default values."""
        self.mock_character_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": True
        }
        self.mock_campaign_template_repo.save_template.return_value = True
        
        # Test with empty starting location
        campaign_data = self.sample_campaign_data.copy()
        campaign_data["starting_location"] = ""
        
        result = self.service.create_campaign(campaign_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.starting_location.name, "Unknown Starting Point")
        self.assertEqual(result.starting_location.description, "The adventure's origin is yet to be defined.")

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

    def test_create_campaign_instance_invalid_template_ids(self):
        """Test creating a campaign instance with invalid character template IDs."""
        # Mock template validation with invalid templates
        self.mock_character_template_repo.validate_template_ids.return_value = {
            "char1": True, "char2": False  # char2 is invalid
        }
        
        # Mock template exists
        self.mock_campaign_template_repo.get_template.return_value = Mock(spec=CampaignTemplateModel)
        
        result = self.service.create_campaign_instance("test_campaign", "Test Instance", ["char1", "char2"])
        
        self.assertIsNone(result)
        self.mock_character_template_repo.validate_template_ids.assert_called_once_with(["char1", "char2"])

    def test_create_campaign_save_failure(self):
        """Test creating a campaign when save operation fails."""
        # Mock failed save
        self.mock_campaign_template_repo.save_template.return_value = False
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNone(result)

    def test_create_campaign_sets_defaults(self):
        """Test that campaign creation sets appropriate defaults."""
        self.mock_campaign_template_repo.save_template.return_value = True
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.starting_level, 1)
        self.assertEqual(result.difficulty, "normal")
        self.assertIsInstance(result.created_date, datetime)
        self.assertIsInstance(result.last_modified, datetime)
        from app.game.unified_models import HouseRulesModel
        self.assertIsInstance(result.house_rules, HouseRulesModel)
        self.assertEqual(result.initial_npcs, {})
        self.assertEqual(result.initial_quests, {})
        self.assertEqual(result.world_lore, [])
        # Check TTS defaults
        self.assertEqual(result.narration_enabled, False)
        self.assertEqual(result.tts_voice, "af_heart")


    def test_update_campaign_success(self):
        """Test updating a campaign template successfully."""
        campaign = CampaignTemplateModel(
            id="test_campaign",
            name="Test Campaign",
            description="Test",
            created_date=datetime.now(timezone.utc),
            starting_level=1,
            difficulty="normal",
            starting_location={"name": "Test", "description": "Test"},
            campaign_goal="Test goal",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            opening_narrative="Test",
            house_rules={}
        )
        
        self.mock_campaign_template_repo.save_template.return_value = True
        
        result = self.service.update_campaign(campaign)
        
        self.assertTrue(result)
        self.mock_campaign_template_repo.save_template.assert_called_once_with(campaign)

    def test_delete_campaign(self):
        """Test deleting a campaign."""
        self.mock_campaign_template_repo.delete_template.return_value = True
        
        result = self.service.delete_campaign("test_campaign")
        
        self.assertTrue(result)
        self.mock_campaign_template_repo.delete_template.assert_called_once_with("test_campaign")

    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_start_campaign_with_party_success(self, mock_open, mock_exists, mock_makedirs):
        """Test starting a campaign with party successfully."""
        # Mock file operations
        mock_exists.return_value = False  # Event log doesn't exist yet
        
        # Mock that this is NOT an instance (get_instance returns None)
        self.mock_instance_repo.get_instance.return_value = None
        self.mock_instance_repo.create_instance.return_value = True
        
        # Create mock campaign
        campaign = CampaignTemplateModel(
            id="test_campaign",
            name="Test Campaign",
            description="Test",
            created_date=datetime.now(timezone.utc),
            starting_level=1,
            difficulty="normal",
            starting_location={"name": "Test Location", "description": "Test description"},
            campaign_goal="Test goal",
            initial_npcs={"npc1": {"id": "npc1", "name": "Test NPC", "description": "A test NPC", "last_location": "Test Town"}},
            initial_quests={"quest1": {"id": "quest1", "title": "Test Quest", "description": "A test quest", "status": "active"}},
            world_lore=["Some lore"],
            opening_narrative="Welcome to the test campaign",
            house_rules={}
        )
        
        self.mock_campaign_template_repo.get_template.return_value = campaign
        self.mock_character_template_repo.get_template.return_value = self.sample_template
        self.mock_character_template_repo.validate_template_ids.return_value = {"char1": True}
        
        # Start campaign with party
        result = self.service.start_campaign("test_campaign", party_character_ids=["char1"])
        
        self.assertIsNotNone(result)
        self.assertIn("test_campaign", result["campaign_id"])  # Will have timestamp appended
        self.assertIn("Adventure", result["campaign_name"])
        self.assertIn("char1", result["party"])
        self.assertEqual(result["current_location"], campaign.starting_location)
        self.assertEqual(result["campaign_goal"], campaign.campaign_goal)
        
        # Check that template was converted to character instance
        char_instance = result["party"]["char1"]
        # Character instance now only contains dynamic state fields
        self.assertEqual(char_instance["template_id"], "char1")
        self.assertIn("current_hp", char_instance)
        self.assertIn("max_hp", char_instance)
        self.assertIn("inventory", char_instance)

    def test_start_campaign_nonexistent(self):
        """Test starting a campaign that doesn't exist."""
        # Mock that this is NOT an instance (get_instance returns None)
        self.mock_instance_repo.get_instance.return_value = None
        self.mock_campaign_template_repo.get_template.return_value = None
        
        result = self.service.start_campaign("nonexistent")
        
        self.assertIsNone(result)

    def test_start_campaign_with_missing_template(self):
        """Test starting a campaign with missing character template."""
        campaign = CampaignTemplateModel(
            id="test_campaign",
            name="Test Campaign",
            description="Test",
            created_date=datetime.now(timezone.utc),
            starting_level=1,
            difficulty="normal",
            starting_location={"name": "Test", "description": "Test"},
            campaign_goal="Test goal",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            opening_narrative="Test",
            house_rules={}
        )
        
        # Mock that this is NOT an instance (get_instance returns None)
        self.mock_instance_repo.get_instance.return_value = None
        self.mock_campaign_template_repo.get_template.return_value = campaign
        self.mock_character_template_repo.validate_template_ids.return_value = {
            "char1": True, "missing_char": True
        }
        
        def mock_get_template(template_id):
            if template_id == "char1":
                return self.sample_template
            return None  # missing_char not found
        
        self.mock_character_template_repo.get_template.side_effect = mock_get_template
        
        with patch('app.services.campaign_service.logger') as mock_logger:
            result = self.service.start_campaign("test_campaign", party_character_ids=["char1", "missing_char"])
            
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

    def test_template_to_character_instance_returns_instance_model_fields(self):
        """Test that template conversion returns CharacterInstanceModel fields."""
        result = self.service._template_to_character_instance(self.sample_template, "test_campaign")
        
        # Verify it returns CharacterInstanceModel fields
        self.assertIn("template_id", result)
        self.assertIn("campaign_id", result)
        self.assertIn("current_hp", result)
        self.assertIn("max_hp", result)
        self.assertIn("conditions", result)
        self.assertIn("inventory", result)
        self.assertIn("gold", result)
        
        # AC calculation is no longer part of CharacterInstanceModel
        # It should be calculated when needed from template + equipment
        self.assertNotIn("armor_class", result)
        
        # Verify the values
        self.assertEqual(result["template_id"], "char1")  # self.sample_template.id
        self.assertEqual(result["campaign_id"], "test_campaign")

    def test_template_to_character_instance_with_missing_d5e_data(self):
        """Test character instance creation when D&D 5e data is missing."""
        # Create service without D&D 5e data
        service_no_data = CampaignService(self.mock_campaign_template_repo, self.mock_character_template_repo, self.mock_instance_repo)
        service_no_data.d5e_classes = {}
        
        result = service_no_data._template_to_character_instance(self.sample_template)
        
        # The character factory is already created with loaded D&D data during initialization
        # Fighter has d10 hit die, CON modifier is +2 (14 CON)
        # Level 1: max_hp = 10 + 2 = 12
        self.assertEqual(result["max_hp"], 12)

    def test_get_campaign_summary(self):
        """Test getting campaign summary."""
        campaign = CampaignTemplateModel(
            id="test_campaign",
            name="Test Campaign",
            description="Test description",
            created_date=datetime.now(timezone.utc),
            starting_level=1,
            difficulty="normal",
            starting_location={"name": "Test", "description": "Test"},
            campaign_goal="Test goal",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            opening_narrative="Test",
            house_rules={}
        )
        
        self.mock_campaign_template_repo.get_template.return_value = campaign
        
        result = self.service.get_campaign_summary("test_campaign")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "test_campaign")
        self.assertEqual(result["name"], "Test Campaign")
        self.assertEqual(result["starting_level"], 1)
        self.assertEqual(result["difficulty"], "normal")

    def test_get_campaign_summary_nonexistent(self):
        """Test getting summary for nonexistent campaign."""
        self.mock_campaign_template_repo.get_template.return_value = None
        
        result = self.service.get_campaign_summary("nonexistent")
        
        self.assertIsNone(result)

    @patch('app.services.campaign_service.logger')
    def test_error_handling_in_create_campaign(self, mock_logger):
        """Test error handling in create_campaign method."""
        # Mock an exception during save
        self.mock_campaign_template_repo.save_template.side_effect = Exception("Test error")
        
        result = self.service.create_campaign(self.sample_campaign_data)
        
        self.assertIsNone(result)
        mock_logger.error.assert_called()

    @patch('app.services.campaign_service.logger')
    def test_error_handling_in_start_campaign(self, mock_logger):
        """Test error handling in start_campaign method."""
        # Mock that this is NOT an instance (get_instance returns None)
        self.mock_instance_repo.get_instance.return_value = None
        # Mock an exception during campaign retrieval
        self.mock_campaign_template_repo.get_template.side_effect = Exception("Test error")
        
        result = self.service.start_campaign("test_campaign")
        
        self.assertIsNone(result)
        mock_logger.error.assert_called()
    
    def test_get_campaign_overview(self):
        """Test get campaign overview returns both templates and instances."""
        # Arrange
        from app.game.unified_models import CampaignInstanceModel
        from datetime import datetime, timezone
        
        # Mock templates
        template = Mock(spec=CampaignTemplateMetadata)
        template.id = "template1"
        template.name = "Test Template"
        template.description = "A test template"
        template.created_date = datetime.now(timezone.utc)
        template.last_modified = datetime.now(timezone.utc)
        template.starting_level = 1
        template.difficulty = "normal"
        template.thumbnail = None
        template.tags = ["test"]
        self.mock_campaign_template_repo.get_all_template_metadata.return_value = [template]
        
        # Mock instances
        instance = CampaignInstanceModel(
            id="instance1",
            name="Test Instance",
            template_id="template1",
            character_ids=["char1", "char2"],
            current_location="Starting Town",
            session_count=5,
            in_combat=False,
            event_summary=[],
            event_log_path="/path/to/log",
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc)
        )
        self.service.instance_repo.get_all_instances = Mock(return_value=[instance])
        
        # Act
        result = self.service.get_campaign_overview()
        
        # Assert
        self.assertIn("templates", result)
        self.assertIn("instances", result)
        self.assertEqual(len(result["templates"]), 1)
        self.assertEqual(len(result["instances"]), 1)
        self.assertEqual(result["templates"][0]["id"], "template1")
        self.assertEqual(result["instances"][0]["id"], "instance1")
        self.assertEqual(result["instances"][0]["party_size"], 2)


if __name__ == '__main__':
    unittest.main()
