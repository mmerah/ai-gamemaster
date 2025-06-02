"""
Unit tests for CharacterTemplateModel JSON serialization/deserialization.
Ensures unified model can round-trip through JSON without data loss.
"""
import unittest
import json
from datetime import datetime, timezone
from app.game.unified_models import (
    CharacterTemplateModel, ItemModel, TraitModel, ClassFeatureModel, 
    BaseStatsModel, ProficienciesModel
)


class TestCharacterTemplateSerialization(unittest.TestCase):
    """Test JSON serialization/deserialization of CharacterTemplateModel."""
    
    def setUp(self):
        """Set up test character data."""
        self.test_character = CharacterTemplateModel(
            # Identity fields
            id="test_ranger",
            name="Torvin Stonebeard",
            race="Dwarf",
            subrace="Mountain Dwarf",
            char_class="Ranger",
            subclass="Hunter",
            level=3,
            background="Outlander",
            alignment="Neutral Good",
            
            # Stats
            base_stats=BaseStatsModel(
                STR=14,
                DEX=16,
                CON=16,
                INT=10,
                WIS=14,
                CHA=8
            ),
            
            # Proficiencies
            proficiencies=ProficienciesModel(
                armor=["Light armor", "Medium armor", "Shields"],
                weapons=["Simple weapons", "Martial weapons"],
                tools=["Smith's tools"],
                saving_throws=["Strength", "Dexterity"],
                skills=["Animal Handling", "Athletics", "Perception", "Survival"]
            ),
            
            # Other fields
            languages=["Common", "Dwarvish", "Orc"],
            racial_traits=[
                TraitModel(name="Darkvision", description="See in darkness 60ft"),
                TraitModel(name="Dwarven Resilience", description="Resistance to poison")
            ],
            class_features=[
                ClassFeatureModel(
                    name="Favored Enemy",
                    description="Advantage on tracking orcs",
                    level_acquired=1
                ),
                ClassFeatureModel(
                    name="Natural Explorer",
                    description="Double proficiency in mountains",
                    level_acquired=1
                )
            ],
            feats=[],
            spells_known=["Hunter's Mark", "Cure Wounds"],
            cantrips_known=[],
            starting_equipment=[
                ItemModel(id="scale_mail", name="Scale Mail", description="AC 14 + Dex (max 2)", quantity=1),
                ItemModel(id="longbow", name="Longbow", description="1d8 piercing", quantity=1),
                ItemModel(id="arrows", name="Arrows", description="Ammunition", quantity=40),
                ItemModel(id="shortsword", name="Shortsword", description="1d6 piercing", quantity=2)
            ],
            starting_gold=75,
            portrait_path="/images/portraits/torvin.jpg",
            personality_traits=["I watch over my friends as if they were a litter of newborn pups"],
            ideals=["Life is like the seasons, in constant change"],
            bonds=["My family was killed by orcs, I will have my revenge"],
            flaws=["I am slow to trust members of other races"],
            appearance="Stocky dwarf with iron-gray beard braided with metal rings",
            backstory="Raised in mountain stronghold, became ranger after orc raid"
        )
    
    def test_model_to_json_serialization(self):
        """Test converting CharacterTemplateModel to JSON."""
        # Use model_dump() to get dict, then json.dumps for JSON string
        character_dict = self.test_character.model_dump()
        json_str = json.dumps(character_dict, default=str)  # default=str handles datetime
        
        # Parse it back
        parsed = json.loads(json_str)
        
        # Verify key fields
        self.assertEqual(parsed["id"], "test_ranger")
        self.assertEqual(parsed["name"], "Torvin Stonebeard")
        self.assertEqual(parsed["subrace"], "Mountain Dwarf")
        self.assertEqual(parsed["subclass"], "Hunter")
        
        # Verify nested structures
        self.assertEqual(parsed["base_stats"]["STR"], 14)
        self.assertEqual(len(parsed["proficiencies"]["skills"]), 4)
        self.assertIn("Perception", parsed["proficiencies"]["skills"])
        
        # Verify lists
        self.assertEqual(len(parsed["languages"]), 3)
        self.assertEqual(len(parsed["racial_traits"]), 2)
        self.assertEqual(parsed["racial_traits"][0]["name"], "Darkvision")
        
        # Verify equipment
        self.assertEqual(len(parsed["starting_equipment"]), 4)
        arrows = next((item for item in parsed["starting_equipment"] if item["name"] == "Arrows"), None)
        self.assertIsNotNone(arrows)
        self.assertEqual(arrows["quantity"], 40)
    
    def test_json_to_model_deserialization(self):
        """Test loading CharacterTemplateModel from JSON."""
        # Create JSON data
        json_data = {
            "id": "test_bard",
            "name": "Melody Songweaver",
            "race": "Half-Elf",
            "subrace": None,
            "char_class": "Bard",
            "subclass": "College of Lore",
            "level": 4,
            "background": "Entertainer",
            "alignment": "Chaotic Good",
            "base_stats": {
                "STR": 10,
                "DEX": 14,
                "CON": 13,
                "INT": 12,
                "WIS": 12,
                "CHA": 18
            },
            "proficiencies": {
                "armor": ["Light armor"],
                "weapons": ["Simple weapons", "Hand crossbows", "Longswords", "Rapiers", "Shortswords"],
                "tools": ["Lute", "Flute", "Drum"],
                "saving_throws": ["Dexterity", "Charisma"],
                "skills": ["Acrobatics", "Deception", "Performance", "Persuasion", "Sleight of Hand"]
            },
            "languages": ["Common", "Elvish", "Draconic"],
            "racial_traits": [
                {"name": "Darkvision", "description": "See in dim light 60ft"},
                {"name": "Fey Ancestry", "description": "Advantage against charmed"}
            ],
            "class_features": [
                {"name": "Bardic Inspiration", "description": "d8 inspiration dice", "level_acquired": 1},
                {"name": "Jack of All Trades", "description": "Half proficiency to non-proficient checks", "level_acquired": 2},
                {"name": "Expertise", "description": "Double proficiency on two skills", "level_acquired": 3},
                {"name": "Cutting Words", "description": "Reduce enemy roll with inspiration", "level_acquired": 3}
            ],
            "feats": [{"name": "Actor", "description": "+1 CHA, advantage on deception and performance"}],
            "spells_known": ["Charm Person", "Healing Word", "Thunderwave", "Invisibility", "Shatter"],
            "cantrips_known": ["Vicious Mockery", "Minor Illusion"],
            "starting_equipment": [
                {"id": "rapier", "name": "Rapier", "description": "Finesse weapon", "quantity": 1},
                {"id": "lute", "name": "Lute", "description": "Musical instrument", "quantity": 1}
            ],
            "starting_gold": 125,
            "portrait_path": None,
            "personality_traits": ["I change my mood as quickly as I change keys in a song"],
            "ideals": ["Beauty. Art should inspire and bring joy"],
            "bonds": ["I want to be famous, whatever it takes"],
            "flaws": ["A scandal prevents me from returning home"],
            "appearance": "Lithe figure with auburn hair and mischievous green eyes",
            "backstory": None,
            "created_date": datetime.now(timezone.utc).isoformat(),
            "last_modified": datetime.now(timezone.utc).isoformat()
        }
        
        # Convert to model
        character = CharacterTemplateModel(**json_data)
        
        # Verify all fields loaded correctly
        self.assertEqual(character.id, "test_bard")
        self.assertEqual(character.name, "Melody Songweaver")
        self.assertEqual(character.race, "Half-Elf")
        self.assertIsNone(character.subrace)
        self.assertEqual(character.char_class, "Bard")
        self.assertEqual(character.subclass, "College of Lore")
        
        # Check complex fields
        self.assertEqual(character.base_stats.CHA, 18)
        self.assertEqual(len(character.proficiencies.tools), 3)
        self.assertIn("Lute", character.proficiencies.tools)
        
        # Check lists
        self.assertEqual(len(character.class_features), 4)
        self.assertEqual(character.class_features[2].name, "Expertise")
        self.assertEqual(character.class_features[2].level_acquired, 3)
        
        # Check feats
        self.assertEqual(len(character.feats), 1)
        self.assertEqual(character.feats[0].name, "Actor")
        
        # Check optional fields
        self.assertIsNone(character.portrait_path)
        self.assertIsNotNone(character.appearance)
        self.assertIsNone(character.backstory)
    
    def test_round_trip_serialization(self):
        """Test that data survives a round trip through JSON."""
        # Convert to dict, then JSON, then back to dict, then to model
        dict1 = self.test_character.model_dump()
        json_str = json.dumps(dict1, default=str)
        dict2 = json.loads(json_str)
        character2 = CharacterTemplateModel(**dict2)
        
        # Compare key fields
        self.assertEqual(character2.id, self.test_character.id)
        self.assertEqual(character2.name, self.test_character.name)
        self.assertEqual(character2.level, self.test_character.level)
        
        # Compare complex fields
        self.assertEqual(character2.base_stats.STR, self.test_character.base_stats.STR)
        self.assertEqual(len(character2.proficiencies.skills), len(self.test_character.proficiencies.skills))
        self.assertEqual(len(character2.racial_traits), len(self.test_character.racial_traits))
        self.assertEqual(character2.racial_traits[0].name, self.test_character.racial_traits[0].name)
        
        # Compare equipment
        self.assertEqual(len(character2.starting_equipment), len(self.test_character.starting_equipment))
        arrows1 = next((item for item in self.test_character.starting_equipment if item.name == "Arrows"), None)
        arrows2 = next((item for item in character2.starting_equipment if item.name == "Arrows"), None)
        self.assertEqual(arrows2.quantity, arrows1.quantity)
    
    def test_datetime_serialization(self):
        """Test that datetime fields serialize correctly."""
        # Create character with explicit datetime
        now = datetime.now(timezone.utc)
        self.test_character.created_date = now
        self.test_character.last_modified = now
        
        # Serialize
        dict_data = self.test_character.model_dump()
        json_str = json.dumps(dict_data, default=str)
        
        # Deserialize
        parsed = json.loads(json_str)
        
        # Check datetime was serialized as string
        self.assertIsInstance(parsed["created_date"], str)
        self.assertIsInstance(parsed["last_modified"], str)
        # Should contain date/time elements
        self.assertIn("20", parsed["created_date"])  # Year
        self.assertIn(":", parsed["created_date"])  # Time separator
        
        # Can load back into model
        character2 = CharacterTemplateModel(**parsed)
        self.assertIsInstance(character2.created_date, datetime)
        self.assertIsInstance(character2.last_modified, datetime)
    
    def test_empty_lists_serialization(self):
        """Test that empty lists serialize and deserialize correctly."""
        # Create character with many empty lists
        minimal_character = CharacterTemplateModel(
            id="minimal",
            name="Minimal Character",
            race="Human",
            char_class="Fighter",
            level=1,
            background="Folk Hero",
            alignment="Neutral",
            base_stats=BaseStatsModel(STR=15, DEX=13, CON=14, INT=10, WIS=11, CHA=12),
            proficiencies=ProficienciesModel(
                armor=[],
                weapons=[],
                tools=[],
                saving_throws=["Strength", "Constitution"],
                skills=[]
            ),
            languages=["Common"],
            racial_traits=[],
            class_features=[],
            feats=[],
            spells_known=[],
            cantrips_known=[],
            starting_equipment=[],
            starting_gold=0,
            personality_traits=[],
            ideals=[],
            bonds=[],
            flaws=[]
        )
        
        # Serialize and deserialize
        dict_data = minimal_character.model_dump()
        json_str = json.dumps(dict_data, default=str)
        parsed = json.loads(json_str)
        loaded_character = CharacterTemplateModel(**parsed)
        
        # Verify empty lists remain empty
        self.assertEqual(len(loaded_character.racial_traits), 0)
        self.assertEqual(len(loaded_character.class_features), 0)
        self.assertEqual(len(loaded_character.feats), 0)
        self.assertEqual(len(loaded_character.starting_equipment), 0)
        self.assertEqual(len(loaded_character.proficiencies.armor), 0)
        
        # But non-empty lists are preserved
        self.assertEqual(len(loaded_character.proficiencies.saving_throws), 2)
        self.assertEqual(len(loaded_character.languages), 1)


if __name__ == '__main__':
    unittest.main()