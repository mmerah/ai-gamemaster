"""
Unit tests for CharacterTemplateRepository.
"""
import unittest
import tempfile
import shutil
import os
import json
from datetime import datetime, timezone
from unittest.mock import patch
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.game.models import CharacterTemplate, CharacterTemplateMetadata


class TestCharacterTemplateRepository(unittest.TestCase):
    """Test cases for CharacterTemplateRepository."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = CharacterTemplateRepository(templates_dir=self.temp_dir)
        
        # Sample character template data
        self.sample_template = CharacterTemplate(
            id="test_template",
            name="Test Character",
            race="Human",
            char_class="Fighter",
            level=1,
            alignment="Lawful Good",
            background="Soldier",
            subclass_name=None,
            portrait_path="test_portrait.jpg",
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
            starting_gold=100
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_ensure_directory_exists(self):
        """Test that the repository creates the templates directory."""
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_get_all_templates_empty(self):
        """Test getting templates when no templates exist."""
        templates = self.repo.get_all_templates()
        self.assertEqual(templates, [])

    def test_save_and_get_template(self):
        """Test saving and retrieving a character template."""
        # Save template
        result = self.repo.save_template(self.sample_template)
        self.assertTrue(result)
        
        # Check template file was created
        template_file = os.path.join(self.temp_dir, "test_template.json")
        self.assertTrue(os.path.exists(template_file))
        
        # Retrieve template
        retrieved_template = self.repo.get_template("test_template")
        self.assertIsNotNone(retrieved_template)
        self.assertEqual(retrieved_template.id, "test_template")
        self.assertEqual(retrieved_template.name, "Test Character")
        self.assertEqual(retrieved_template.race, "Human")
        self.assertEqual(retrieved_template.char_class, "Fighter")

    def test_get_all_templates_with_data(self):
        """Test getting all templates when templates exist."""
        # Save a template first
        self.repo.save_template(self.sample_template)
        
        templates = self.repo.get_all_templates()
        self.assertEqual(len(templates), 1)
        self.assertIsInstance(templates[0], CharacterTemplateMetadata)
        self.assertEqual(templates[0].id, "test_template")
        self.assertEqual(templates[0].race, "Human")
        self.assertEqual(templates[0].char_class, "Fighter")

    def test_get_nonexistent_template(self):
        """Test getting a template that doesn't exist."""
        template = self.repo.get_template("nonexistent")
        self.assertIsNone(template)

    def test_delete_template(self):
        """Test deleting a character template."""
        # First save a template
        self.repo.save_template(self.sample_template)
        
        # Verify it exists
        templates = self.repo.get_all_templates()
        self.assertEqual(len(templates), 1)
        
        # Delete it
        result = self.repo.delete_template("test_template")
        self.assertTrue(result)
        
        # Verify it's gone
        templates = self.repo.get_all_templates()
        self.assertEqual(len(templates), 0)
        
        # Verify file is removed
        template_file = os.path.join(self.temp_dir, "test_template.json")
        self.assertFalse(os.path.exists(template_file))

    def test_delete_nonexistent_template(self):
        """Test deleting a template that doesn't exist."""
        result = self.repo.delete_template("nonexistent")
        self.assertFalse(result)

    def test_get_templates_by_class(self):
        """Test filtering templates by class."""
        # Create multiple templates with different classes
        fighter_template = self.sample_template
        
        wizard_template = CharacterTemplate(
            id="wizard_template",
            name="Test Wizard",
            race="Elf",
            char_class="Wizard",
            level=1,
            alignment="Neutral Good",
            background="Scholar",
            subclass_name=None,
            portrait_path="wizard_portrait.jpg",
            base_stats={
                "STR": 8, "DEX": 14, "CON": 13,
                "INT": 16, "WIS": 12, "CHA": 10
            },
            proficiencies={
                "armor": [],
                "weapons": ["simple"],
                "tools": [],
                "saving_throws": ["INT", "WIS"],
                "skills": ["Arcana", "History"]
            },
            languages=["Common", "Elvish"],
            starting_equipment=[
                {"name": "Quarterstaff", "quantity": 1},
                {"name": "Spellbook", "quantity": 1}
            ],
            starting_gold=50
        )
        
        # Save both templates
        self.repo.save_template(fighter_template)
        self.repo.save_template(wizard_template)
        
        # Test filtering by class
        fighters = self.repo.get_templates_by_class("Fighter")
        self.assertEqual(len(fighters), 1)
        self.assertEqual(fighters[0].char_class, "Fighter")
        
        wizards = self.repo.get_templates_by_class("Wizard")
        self.assertEqual(len(wizards), 1)
        self.assertEqual(wizards[0].char_class, "Wizard")
        
        # Test case insensitive
        fighters_lower = self.repo.get_templates_by_class("fighter")
        self.assertEqual(len(fighters_lower), 1)

    def test_get_templates_by_race(self):
        """Test filtering templates by race."""
        # Create templates with different races
        human_template = self.sample_template
        
        elf_template = CharacterTemplate(
            id="elf_template",
            name="Test Elf",
            race="Elf",
            char_class="Ranger",
            level=1,
            alignment="Chaotic Good",
            background="Outlander",
            subclass_name=None,
            portrait_path="elf_portrait.jpg",
            base_stats={
                "STR": 13, "DEX": 16, "CON": 12,
                "INT": 14, "WIS": 15, "CHA": 10
            },
            proficiencies={
                "armor": ["light", "medium", "shields"],
                "weapons": ["simple", "martial"],
                "tools": [],
                "saving_throws": ["STR", "DEX"],
                "skills": ["Animal Handling", "Survival"]
            },
            languages=["Common", "Elvish"],
            starting_equipment=[
                {"name": "Leather Armor", "quantity": 1},
                {"name": "Longbow", "quantity": 1}
            ],
            starting_gold=75
        )
        
        # Save both templates
        self.repo.save_template(human_template)
        self.repo.save_template(elf_template)
        
        # Test filtering by race
        humans = self.repo.get_templates_by_race("Human")
        self.assertEqual(len(humans), 1)
        self.assertEqual(humans[0].race, "Human")
        
        elves = self.repo.get_templates_by_race("Elf")
        self.assertEqual(len(elves), 1)
        self.assertEqual(elves[0].race, "Elf")

    def test_validate_template_ids(self):
        """Test template ID validation."""
        # Save a template
        self.repo.save_template(self.sample_template)
        
        # Test validation
        validation_result = self.repo.validate_template_ids([
            "test_template",  # exists
            "nonexistent"     # doesn't exist
        ])
        
        self.assertTrue(validation_result["test_template"])
        self.assertFalse(validation_result["nonexistent"])

    def test_templates_index_creation(self):
        """Test that templates index is created and updated correctly."""
        # Save template
        self.repo.save_template(self.sample_template)
        
        # Check index file exists
        index_file = os.path.join(self.temp_dir, "templates.json")
        self.assertTrue(os.path.exists(index_file))
        
        # Check index content
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        self.assertEqual(index_data["version"], "1.0")
        self.assertEqual(len(index_data["templates"]), 1)
        self.assertEqual(index_data["templates"][0]["id"], "test_template")

    def test_template_metadata_generation(self):
        """Test that template metadata is generated correctly."""
        # Create template with subclass and background
        template_with_subclass = CharacterTemplate(
            id="champion_template",
            name="Champion Fighter",
            race="Human",
            char_class="Fighter",
            level=3,
            alignment="Lawful Good",
            background="Noble",
            subclass_name="Champion",
            portrait_path="champion.jpg",
            base_stats={
                "STR": 16, "DEX": 13, "CON": 14,
                "INT": 10, "WIS": 12, "CHA": 14
            },
            proficiencies={
                "armor": ["light", "medium", "heavy", "shields"],
                "weapons": ["simple", "martial"],
                "tools": [],
                "saving_throws": ["STR", "CON"],
                "skills": ["Athletics", "History"]
            },
            languages=["Common"],
            starting_equipment=[],
            starting_gold=100
        )
        
        self.repo.save_template(template_with_subclass)
        templates = self.repo.get_all_templates()
        
        self.assertEqual(len(templates), 1)
        template_meta = templates[0]
        
        # Check that description includes subclass and background
        self.assertIn("Champion", template_meta.description)
        self.assertIn("Noble", template_meta.description)
        self.assertIn("Human", template_meta.description)
        self.assertIn("Fighter", template_meta.description)

    def test_timezone_aware_datetime_in_index(self):
        """Test that timezone-aware datetime is used in index updates."""
        with patch('app.repositories.character_template_repository.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Save template
            self.repo.save_template(self.sample_template)
            
            # Check that timezone-aware datetime was used
            mock_datetime.now.assert_called_with(timezone.utc)

    @patch('app.repositories.character_template_repository.logger')
    def test_error_handling_malformed_template_data(self, mock_logger):
        """Test error handling when template index contains malformed data."""
        # Create malformed index data
        index_data = {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "templates": [
                {
                    "id": "malformed_template",
                    "name": "Malformed Template",
                    # Missing required fields like race, char_class, etc.
                }
            ]
        }
        
        index_file = os.path.join(self.temp_dir, "templates.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f)
        
        # Should handle error gracefully
        templates = self.repo.get_all_templates()
        self.assertEqual(len(templates), 0)  # Malformed template should be skipped
        mock_logger.error.assert_called()

    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    @patch('app.repositories.character_template_repository.logger')
    def test_error_handling_save_failure(self, mock_logger, mock_open):
        """Test error handling when save operation fails."""
        result = self.repo.save_template(self.sample_template)
        self.assertFalse(result)
        mock_logger.error.assert_called()

    def test_template_file_naming(self):
        """Test that template files are named correctly."""
        self.repo.save_template(self.sample_template)
        
        # Check that file is named with template ID
        expected_file = os.path.join(self.temp_dir, "test_template.json")
        self.assertTrue(os.path.exists(expected_file))
        
        # Check that file contains correct data
        with open(expected_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data["id"], "test_template")
        self.assertEqual(data["name"], "Test Character")

    def test_update_existing_template(self):
        """Test updating an existing template."""
        # Save initial template
        self.repo.save_template(self.sample_template)
        
        # Modify template
        updated_template = self.sample_template.model_copy(deep=True)
        updated_template.name = "Updated Test Character"
        updated_template.level = 2
        
        # Save updated template
        result = self.repo.save_template(updated_template)
        self.assertTrue(result)
        
        # Check that there's still only one template in index
        templates = self.repo.get_all_templates()
        self.assertEqual(len(templates), 1)
        
        # Check that the template was updated
        retrieved = self.repo.get_template("test_template")
        self.assertEqual(retrieved.name, "Updated Test Character")
        self.assertEqual(retrieved.level, 2)


if __name__ == '__main__':
    unittest.main()
