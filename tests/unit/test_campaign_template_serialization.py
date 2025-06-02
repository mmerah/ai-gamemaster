"""
Unit tests for campaign template JSON serialization/deserialization.
Ensures no data loss when converting between Python models and JSON.
"""
import unittest
import json
from datetime import datetime, timezone
from app.game.unified_models import (
    CampaignTemplateModel, NPCModel, QuestModel, LocationModel, 
    HouseRulesModel, GoldRangeModel
)


class TestCampaignTemplateSerializationTest(unittest.TestCase):
    """Test campaign template serialization and deserialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create comprehensive test campaign
        self.test_campaign = CampaignTemplateModel(
            id="serialization_test",
            name="Serialization Test Campaign",
            description="A campaign for testing serialization",
            campaign_goal="Test all data types serialize correctly",
            starting_location=LocationModel(
                name="Test City",
                description="A test location"
            ),
            opening_narrative="This is a test...",
            starting_level=2,
            difficulty="normal",
            ruleset_id="test_rules",
            lore_id="test_lore",
            initial_npcs={
                "test_npc": NPCModel(
                    id="test_npc",
                    name="Test NPC",
                    description="An NPC for testing",
                    last_location="Test Location"
                )
            },
            initial_quests={
                "test_quest": QuestModel(
                    id="test_quest",
                    title="Test Quest",
                    description="A quest for testing",
                    status="active"
                )
            },
            world_lore=["First lore item", "Second lore item"],
            house_rules=HouseRulesModel(
                critical_hit_tables=True,
                flanking_rules=False,
                milestone_leveling=True,
                death_saves_public=True
            ),
            allowed_races=["Human", "Elf"],
            allowed_classes=["Fighter", "Wizard"],
            starting_gold_range=GoldRangeModel(min=100, max=200),
            theme_mood="Test Theme",
            world_map_path="/test/path.jpg",
            session_zero_notes="Test notes",
            xp_system="standard",
            tags=["test", "serialization"]
        )
    
    def test_json_round_trip(self):
        """Test that campaign can be serialized to JSON and back without data loss."""
        # Serialize to dict
        campaign_dict = self.test_campaign.model_dump()
        
        # Convert to JSON string
        json_string = json.dumps(campaign_dict, default=str)
        
        # Parse back from JSON
        parsed_dict = json.loads(json_string)
        
        # Create new campaign from parsed data
        restored_campaign = CampaignTemplateModel(**parsed_dict)
        
        # Verify all fields match
        self.assertEqual(restored_campaign.id, self.test_campaign.id)
        self.assertEqual(restored_campaign.name, self.test_campaign.name)
        self.assertEqual(restored_campaign.description, self.test_campaign.description)
        self.assertEqual(restored_campaign.campaign_goal, self.test_campaign.campaign_goal)
        self.assertEqual(restored_campaign.starting_level, self.test_campaign.starting_level)
        self.assertEqual(restored_campaign.difficulty, self.test_campaign.difficulty)
        self.assertEqual(restored_campaign.xp_system, self.test_campaign.xp_system)
        
        # Verify nested structures
        self.assertEqual(restored_campaign.starting_location.name, self.test_campaign.starting_location.name)
        self.assertEqual(restored_campaign.starting_location.description, self.test_campaign.starting_location.description)
        
        # Verify NPCs
        self.assertEqual(len(restored_campaign.initial_npcs), len(self.test_campaign.initial_npcs))
        test_npc = restored_campaign.initial_npcs["test_npc"]
        self.assertEqual(test_npc.name, "Test NPC")
        self.assertEqual(test_npc.description, "An NPC for testing")
        self.assertEqual(test_npc.last_location, "Test Location")
        
        # Verify Quests
        self.assertEqual(len(restored_campaign.initial_quests), len(self.test_campaign.initial_quests))
        test_quest = restored_campaign.initial_quests["test_quest"]
        self.assertEqual(test_quest.title, "Test Quest")
        self.assertEqual(test_quest.description, "A quest for testing")
        self.assertEqual(test_quest.status, "active")
        
        # Verify arrays
        self.assertEqual(restored_campaign.world_lore, self.test_campaign.world_lore)
        self.assertEqual(restored_campaign.allowed_races, self.test_campaign.allowed_races)
        self.assertEqual(restored_campaign.allowed_classes, self.test_campaign.allowed_classes)
        self.assertEqual(restored_campaign.tags, self.test_campaign.tags)
        
        # Verify house rules
        self.assertEqual(restored_campaign.house_rules.critical_hit_tables, True)
        self.assertEqual(restored_campaign.house_rules.flanking_rules, False)
        self.assertEqual(restored_campaign.house_rules.milestone_leveling, True)
        self.assertEqual(restored_campaign.house_rules.death_saves_public, True)
        
        # Verify gold range
        self.assertEqual(restored_campaign.starting_gold_range.min, 100)
        self.assertEqual(restored_campaign.starting_gold_range.max, 200)
        
    def test_datetime_serialization(self):
        """Test that datetime fields serialize correctly."""
        # Test with specific datetime
        test_date = datetime(2025, 5, 31, 12, 0, 0, tzinfo=timezone.utc)
        campaign = CampaignTemplateModel(
            id="datetime_test",
            name="DateTime Test",
            description="Testing datetime serialization",
            campaign_goal="Test dates",
            starting_location=LocationModel(name="Test", description="Test"),
            opening_narrative="Test...",
            created_date=test_date,
            last_modified=test_date
        )
        
        # Serialize
        campaign_dict = campaign.model_dump()
        json_string = json.dumps(campaign_dict, default=str)
        parsed_dict = json.loads(json_string)
        
        # Verify datetime is serialized as string
        self.assertIsInstance(parsed_dict['created_date'], str)
        self.assertIsInstance(parsed_dict['last_modified'], str)
        
        # Should be able to parse back (note: will be string, not datetime)
        restored_campaign = CampaignTemplateModel(**parsed_dict)
        # Dates will be strings after JSON round trip - this is expected
        
    def test_optional_fields_serialization(self):
        """Test serialization of optional fields."""
        # Campaign with only required fields
        minimal_campaign = CampaignTemplateModel(
            id="minimal_test",
            name="Minimal Campaign",
            description="Testing minimal serialization",
            campaign_goal="Test minimal fields",
            starting_location=LocationModel(name="Start", description="Starting location"),
            opening_narrative="Beginning..."
        )
        
        # Serialize
        campaign_dict = minimal_campaign.model_dump()
        json_string = json.dumps(campaign_dict, default=str)
        parsed_dict = json.loads(json_string)
        
        # Create from parsed data
        restored_campaign = CampaignTemplateModel(**parsed_dict)
        
        # Verify optional fields have correct defaults
        self.assertIsNone(restored_campaign.theme_mood)
        self.assertIsNone(restored_campaign.world_map_path)
        self.assertIsNone(restored_campaign.session_zero_notes)
        self.assertIsNone(restored_campaign.allowed_races)
        self.assertIsNone(restored_campaign.allowed_classes)
        self.assertIsNone(restored_campaign.starting_gold_range)
        self.assertEqual(len(restored_campaign.initial_npcs), 0)
        self.assertEqual(len(restored_campaign.initial_quests), 0)
        self.assertEqual(len(restored_campaign.world_lore), 0)
        self.assertEqual(len(restored_campaign.tags), 0)
        
    def test_empty_collections_serialization(self):
        """Test serialization of empty collections."""
        campaign = CampaignTemplateModel(
            id="empty_test",
            name="Empty Collections Test",
            description="Testing empty collections",
            campaign_goal="Test empty lists and dicts",
            starting_location=LocationModel(name="Empty", description="Empty location"),
            opening_narrative="Empty...",
            initial_npcs={},
            initial_quests={},
            world_lore=[],
            tags=[]
        )
        
        # Serialize and restore
        campaign_dict = campaign.model_dump()
        json_string = json.dumps(campaign_dict, default=str)
        parsed_dict = json.loads(json_string)
        restored_campaign = CampaignTemplateModel(**parsed_dict)
        
        # Verify empty collections are preserved
        self.assertEqual(len(restored_campaign.initial_npcs), 0)
        self.assertEqual(len(restored_campaign.initial_quests), 0)
        self.assertEqual(len(restored_campaign.world_lore), 0)
        self.assertEqual(len(restored_campaign.tags), 0)
        self.assertIsInstance(restored_campaign.initial_npcs, dict)
        self.assertIsInstance(restored_campaign.initial_quests, dict)
        self.assertIsInstance(restored_campaign.world_lore, list)
        self.assertIsInstance(restored_campaign.tags, list)
        
    def test_large_nested_structures(self):
        """Test serialization with large numbers of NPCs and quests."""
        # Create campaign with many NPCs and quests
        large_campaign = CampaignTemplateModel(
            id="large_test",
            name="Large Campaign",
            description="Testing large nested structures",
            campaign_goal="Test performance with many nested objects",
            starting_location=LocationModel(name="Large City", description="A big city"),
            opening_narrative="Many characters await..."
        )
        
        # Add many NPCs
        for i in range(50):
            npc_id = f"npc_{i:03d}"
            large_campaign.initial_npcs[npc_id] = NPCModel(
                id=npc_id,
                name=f"NPC {i}",
                description=f"Description for NPC {i}",
                last_location=f"Location {i % 10}"
            )
        
        # Add many quests
        for i in range(30):
            quest_id = f"quest_{i:03d}"
            large_campaign.initial_quests[quest_id] = QuestModel(
                id=quest_id,
                title=f"Quest {i}",
                description=f"Description for quest {i}",
                status="active" if i % 2 == 0 else "inactive"
            )
        
        # Serialize and restore
        campaign_dict = large_campaign.model_dump()
        json_string = json.dumps(campaign_dict, default=str)
        parsed_dict = json.loads(json_string)
        restored_campaign = CampaignTemplateModel(**parsed_dict)
        
        # Verify counts
        self.assertEqual(len(restored_campaign.initial_npcs), 50)
        self.assertEqual(len(restored_campaign.initial_quests), 30)
        
        # Spot check some entries
        self.assertEqual(restored_campaign.initial_npcs["npc_025"].name, "NPC 25")
        self.assertEqual(restored_campaign.initial_quests["quest_015"].title, "Quest 15")


if __name__ == '__main__':
    unittest.main()