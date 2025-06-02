"""
Unit tests for CharacterTemplateModel CRUD operations with unified model.
Tests all fields are properly handled through create, read, update, delete operations.
"""
import unittest
import tempfile
import shutil
import os
import json
from datetime import datetime, timezone
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.game.unified_models import CharacterTemplateModel, ItemModel, TraitModel, ClassFeatureModel, BaseStatsModel, ProficienciesModel


class TestCharacterTemplateUnifiedCRUD(unittest.TestCase):
    """Test CharacterTemplateModel CRUD operations with all fields from unified model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = CharacterTemplateRepository(templates_dir=self.temp_dir)
        
        # Create comprehensive test character with ALL fields
        self.test_character = CharacterTemplateModel(
            # Identity fields
            id="test_wizard",
            name="Elara Starweaver",
            race="Elf",
            subrace="High Elf",
            char_class="Wizard",
            subclass="School of Evocation",
            level=5,
            background="Sage",
            alignment="Lawful Good",
            
            # Stats
            base_stats=BaseStatsModel(
                STR=8,
                DEX=16,
                CON=14,
                INT=18,
                WIS=12,
                CHA=11
            ),
            
            # Proficiencies - ALL types
            proficiencies=ProficienciesModel(
                armor=[],  # Wizards don't get armor proficiency
                weapons=["Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"],
                tools=["Herbalism kit"],
                saving_throws=["Intelligence", "Wisdom"],
                skills=["Arcana", "History", "Investigation", "Insight"]
            ),
            
            # Languages
            languages=["Common", "Elvish", "Draconic", "Celestial"],
            
            # Racial traits
            racial_traits=[
                TraitModel(
                    name="Darkvision",
                    description="You can see in dim light within 60 feet as if it were bright light"
                ),
                TraitModel(
                    name="Keen Senses",
                    description="You have proficiency in the Perception skill"
                ),
                TraitModel(
                    name="Fey Ancestry",
                    description="You have advantage on saving throws against being charmed"
                ),
                TraitModel(
                    name="Trance",
                    description="Elves don't need to sleep. Instead, they meditate deeply for 4 hours a day"
                )
            ],
            
            # Class features
            class_features=[
                ClassFeatureModel(
                    name="Spellcasting",
                    description="You can cast wizard spells using Intelligence as your spellcasting ability",
                    level_acquired=1
                ),
                ClassFeatureModel(
                    name="Arcane Recovery",
                    description="Once per day, you can recover spell slots during a short rest",
                    level_acquired=1
                ),
                ClassFeatureModel(
                    name="Evocation Savant",
                    description="Gold and time to copy evocation spells is halved",
                    level_acquired=2
                ),
                ClassFeatureModel(
                    name="Sculpt Spells",
                    description="Create pockets of safety in your evocation spells",
                    level_acquired=2
                )
            ],
            
            # Feats
            feats=[
                TraitModel(name="War Caster", description="Advantage on CON saves for concentration, cast with hands full"),
                TraitModel(name="Alert", description="+5 to initiative, can't be surprised while conscious")
            ],
            
            # Spells
            spells_known=[
                "Fireball", "Lightning Bolt", "Counterspell", "Shield",
                "Misty Step", "Scorching Ray", "Web", "Mirror Image",
                "Magic Missile", "Detect Magic", "Identify", "Sleep"
            ],
            cantrips_known=["Fire Bolt", "Ray of Frost", "Prestidigitation", "Mage Hand"],
            
            # Equipment with quantities
            starting_equipment=[
                ItemModel(id="spellbook", name="Spellbook", description="Your wizard spellbook", quantity=1),
                ItemModel(id="quarterstaff", name="Quarterstaff", description="A wooden staff", quantity=1),
                ItemModel(id="component_pouch", name="Component Pouch", description="Material components for spells", quantity=1),
                ItemModel(id="scholars_pack", name="Scholar's Pack", description="Includes books, ink, and parchment", quantity=1),
                ItemModel(id="robes", name="Fine Robes", description="Elegant wizard robes", quantity=1),
                ItemModel(id="dagger", name="Dagger", description="A small blade", quantity=2),
                ItemModel(id="potion_healing", name="Potion of Healing", description="Restores 2d4+2 HP", quantity=3)
            ],
            
            # Gold
            starting_gold=150,
            
            # Appearance and story
            portrait_path="/images/portraits/elara_starweaver.jpg",
            appearance="Tall and slender with silver hair that seems to shimmer with starlight. Violet eyes that glow faintly when casting spells. Wears flowing midnight blue robes embroidered with constellations.",
            backstory="Born under a rare celestial alignment, Elara showed prodigious magical talent from a young age. She studied at the Arcanum for decades before setting out to uncover ancient magical secrets. Her research into the weave of magic itself has led to breakthrough discoveries in evocation magic.",
            
            # Personality
            personality_traits=[
                "I use polysyllabic words that convey the impression of great erudition",
                "I'm constantly taking notes about everything I observe"
            ],
            ideals=[
                "Knowledge. The path to power and self-improvement is through knowledge",
                "Logic. Emotions must not cloud our logical thinking"
            ],
            bonds=[
                "I have an ancient tome that holds terrible secrets that must not fall into the wrong hands",
                "My life's work is a series of tomes related to a specific field of lore"
            ],
            flaws=[
                "I speak without really thinking through my words, invariably insulting others",
                "I can't keep a secret to save my life, or anyone else's"
            ],
            
            # Metadata
            created_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc)
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_character_with_all_fields(self):
        """Test creating a character template with all unified model fields."""
        # Save the character
        result = self.repo.save_template(self.test_character)
        self.assertTrue(result)
        
        # Verify file was created
        template_file = os.path.join(self.temp_dir, "test_wizard.json")
        self.assertTrue(os.path.exists(template_file))
        
        # Load and verify JSON structure
        with open(template_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # Verify all identity fields
        self.assertEqual(saved_data["id"], "test_wizard")
        self.assertEqual(saved_data["name"], "Elara Starweaver")
        self.assertEqual(saved_data["race"], "Elf")
        self.assertEqual(saved_data["subrace"], "High Elf")
        self.assertEqual(saved_data["char_class"], "Wizard")
        self.assertEqual(saved_data["subclass"], "School of Evocation")
        self.assertEqual(saved_data["level"], 5)
        
        # Verify stats
        self.assertEqual(saved_data["base_stats"]["STR"], 8)
        self.assertEqual(saved_data["base_stats"]["INT"], 18)
        
        # Verify all proficiency types
        self.assertIn("armor", saved_data["proficiencies"])
        self.assertIn("weapons", saved_data["proficiencies"])
        self.assertIn("tools", saved_data["proficiencies"])
        self.assertIn("saving_throws", saved_data["proficiencies"])
        self.assertIn("skills", saved_data["proficiencies"])
        self.assertEqual(len(saved_data["proficiencies"]["weapons"]), 5)
        self.assertIn("Intelligence", saved_data["proficiencies"]["saving_throws"])
        
        # Verify languages
        self.assertEqual(len(saved_data["languages"]), 4)
        self.assertIn("Draconic", saved_data["languages"])
        
        # Verify racial traits
        self.assertEqual(len(saved_data["racial_traits"]), 4)
        self.assertEqual(saved_data["racial_traits"][0]["name"], "Darkvision")
        
        # Verify class features
        self.assertEqual(len(saved_data["class_features"]), 4)
        self.assertEqual(saved_data["class_features"][2]["level_acquired"], 2)
        
        # Verify feats
        self.assertEqual(len(saved_data["feats"]), 2)
        self.assertEqual(saved_data["feats"][0]["name"], "War Caster")
        
        # Verify spells
        self.assertEqual(len(saved_data["spells_known"]), 12)
        self.assertIn("Fireball", saved_data["spells_known"])
        self.assertEqual(len(saved_data["cantrips_known"]), 4)
        
        # Verify equipment with quantities
        self.assertEqual(len(saved_data["starting_equipment"]), 7)
        dagger = next((item for item in saved_data["starting_equipment"] if item["name"] == "Dagger"), None)
        self.assertIsNotNone(dagger)
        self.assertEqual(dagger["quantity"], 2)
        
        # Verify personality fields
        self.assertEqual(len(saved_data["personality_traits"]), 2)
        self.assertEqual(len(saved_data["ideals"]), 2)
        self.assertEqual(len(saved_data["bonds"]), 2)
        self.assertEqual(len(saved_data["flaws"]), 2)
        
        # Verify appearance and backstory
        self.assertIn("silver hair", saved_data["appearance"])
        self.assertIn("Arcanum", saved_data["backstory"])
    
    def test_read_character_preserves_all_fields(self):
        """Test reading a character template preserves all fields."""
        # Save the character
        self.repo.save_template(self.test_character)
        
        # Read it back
        loaded_character = self.repo.get_template("test_wizard")
        self.assertIsNotNone(loaded_character)
        
        # Verify all fields are preserved
        self.assertEqual(loaded_character.name, "Elara Starweaver")
        self.assertEqual(loaded_character.subrace, "High Elf")
        self.assertEqual(loaded_character.subclass, "School of Evocation")
        
        # Check complex fields
        self.assertEqual(len(loaded_character.racial_traits), 4)
        self.assertEqual(loaded_character.racial_traits[0].name, "Darkvision")
        
        self.assertEqual(len(loaded_character.class_features), 4)
        self.assertEqual(loaded_character.class_features[2].level_acquired, 2)
        
        self.assertEqual(len(loaded_character.languages), 4)
        self.assertEqual(len(loaded_character.spells_known), 12)
        self.assertEqual(len(loaded_character.starting_equipment), 7)
        
        # Check equipment quantities
        dagger = next((item for item in loaded_character.starting_equipment if item.name == "Dagger"), None)
        self.assertIsNotNone(dagger)
        self.assertEqual(dagger.quantity, 2)
        
        # Check all proficiency types exist
        self.assertIsNotNone(loaded_character.proficiencies.armor)
        self.assertIsNotNone(loaded_character.proficiencies.weapons)
        self.assertIsNotNone(loaded_character.proficiencies.tools)
        self.assertIsNotNone(loaded_character.proficiencies.saving_throws)
        self.assertIsNotNone(loaded_character.proficiencies.skills)
    
    def test_update_character_all_fields(self):
        """Test updating a character template with changes to various fields."""
        # Save initial character
        self.repo.save_template(self.test_character)
        
        # Load and modify
        character = self.repo.get_template("test_wizard")
        
        # Update various fields
        character.level = 6
        character.subclass = "School of Divination"  # Changed school
        
        # Add a new class feature
        character.class_features.append(
            ClassFeatureModel(
                name="Potent Cantrip",
                description="Add INT modifier to cantrip damage",
                level_acquired=6
            )
        )
        
        # Add new spells
        character.spells_known.extend(["Haste", "Fly"])
        
        # Add new equipment
        character.starting_equipment.append(
            ItemModel(
                id="staff_power",
                name="Staff of Power",
                description="A powerful magical staff",
                quantity=1
            )
        )
        
        # Update personality (replace instead of append to stay within limit of 2)
        character.personality_traits[1] = "I often get lost in my own thoughts and contemplations"
        
        # Update gold
        character.starting_gold = 500
        
        # Save updated character
        character.last_modified = datetime.now(timezone.utc)
        result = self.repo.save_template(character)
        self.assertTrue(result)
        
        # Load again and verify updates
        updated = self.repo.get_template("test_wizard")
        self.assertEqual(updated.level, 6)
        self.assertEqual(updated.subclass, "School of Divination")
        self.assertEqual(len(updated.class_features), 5)
        self.assertEqual(len(updated.spells_known), 14)
        self.assertEqual(len(updated.starting_equipment), 8)
        self.assertEqual(len(updated.personality_traits), 2)
        self.assertEqual(updated.starting_gold, 500)
    
    def test_delete_character_with_all_fields(self):
        """Test deleting a character template removes all data."""
        # Save character
        self.repo.save_template(self.test_character)
        
        # Verify it exists
        character = self.repo.get_template("test_wizard")
        self.assertIsNotNone(character)
        
        # Delete it
        result = self.repo.delete_template("test_wizard")
        self.assertTrue(result)
        
        # Verify it's gone
        character = self.repo.get_template("test_wizard")
        self.assertIsNone(character)
        
        # Verify file is deleted
        template_file = os.path.join(self.temp_dir, "test_wizard.json")
        self.assertFalse(os.path.exists(template_file))
    
    def test_metadata_includes_all_relevant_fields(self):
        """Test that character metadata includes subrace, subclass, and other important fields."""
        # Save character
        self.repo.save_template(self.test_character)
        
        # Get metadata
        templates = self.repo.get_all_templates()
        self.assertEqual(len(templates), 1)
        
        metadata = templates[0]
        self.assertEqual(metadata.id, "test_wizard")
        self.assertEqual(metadata.name, "Elara Starweaver")
        self.assertEqual(metadata.race, "Elf")
        self.assertEqual(metadata.char_class, "Wizard")
        self.assertEqual(metadata.level, 5)
        
        # Check description includes subrace and subclass
        self.assertIn("High Elf", metadata.description)
        self.assertIn("School of Evocation", metadata.description)
        self.assertIn("Sage", metadata.description)
    
    def test_character_without_optional_fields(self):
        """Test creating a character with minimal required fields only."""
        minimal_character = CharacterTemplateModel(
            id="minimal_fighter",
            name="Simple Fighter",
            race="Human",
            char_class="Fighter",
            level=1,
            background="Soldier",
            alignment="Neutral",
            base_stats=BaseStatsModel(STR=16, DEX=14, CON=14, INT=10, WIS=12, CHA=10),
            proficiencies=ProficienciesModel(),
            languages=["Common"],
            racial_traits=[],
            class_features=[],
            feats=[],
            spells_known=[],
            cantrips_known=[],
            starting_equipment=[],
            starting_gold=50,
            personality_traits=["Brave"],
            ideals=["Honor"],
            bonds=["My squad"],
            flaws=["Reckless"]
        )
        
        # Save and verify
        result = self.repo.save_template(minimal_character)
        self.assertTrue(result)
        
        # Load and check optional fields are None/empty
        loaded = self.repo.get_template("minimal_fighter")
        self.assertIsNone(loaded.subrace)
        self.assertIsNone(loaded.subclass)
        self.assertIsNone(loaded.portrait_path)
        self.assertIsNone(loaded.appearance)
        self.assertIsNone(loaded.backstory)
        self.assertEqual(len(loaded.racial_traits), 0)
        self.assertEqual(len(loaded.feats), 0)


if __name__ == '__main__':
    unittest.main()