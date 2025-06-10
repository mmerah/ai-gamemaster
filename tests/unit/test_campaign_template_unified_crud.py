"""
Unit tests for CampaignTemplateModel CRUD operations with unified model.
Tests all fields are properly handled through create, read, update, delete operations.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone

from app.models.models import (
    CampaignTemplateModel,
    GoldRangeModel,
    HouseRulesModel,
    LocationModel,
    NPCModel,
    QuestModel,
)
from app.repositories.campaign_template_repository import CampaignTemplateRepository


class TestCampaignTemplateUnifiedCRUD(unittest.TestCase):
    """Test CampaignTemplateModel CRUD operations with all fields from unified model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        # Create a mock config that points to our temp directory
        from app.models.models import ServiceConfigModel

        self.config = ServiceConfigModel(CAMPAIGN_TEMPLATES_DIR=self.temp_dir)
        self.repo = CampaignTemplateRepository(self.config)

        # Create comprehensive test campaign with ALL fields
        self.test_campaign = CampaignTemplateModel(
            # Identity
            id="test_epic_campaign",
            name="The Dragon's Shadow",
            description="An epic campaign to save the realm from an ancient dragon's return",
            # Core Campaign Info
            campaign_goal="Defeat the Shadow Dragon before it plunges the world into eternal darkness",
            starting_location=LocationModel(
                name="City of Goldenheart",
                description="A magnificent city of white stone and golden spires, capital of the kingdom",
            ),
            opening_narrative="As dawn breaks over the city of Goldenheart, dark clouds gather on the horizon. The ancient seals are weakening, and whispers speak of the Shadow Dragon's imminent return. Heroes must rise to face this ancient evil before darkness consumes all.",
            # Mechanics
            starting_level=3,
            difficulty="hard",
            ruleset_id="dnd5e_enhanced",
            lore_id="high_fantasy",
            # Initial Content - NPCs
            initial_npcs={
                "king_aldric": NPCModel(
                    id="king_aldric",
                    name="King Aldric the Wise",
                    description="The aging but wise king of Goldenheart, deeply concerned about the growing darkness",
                    last_location="Royal Palace",
                ),
                "sage_merinda": NPCModel(
                    id="sage_merinda",
                    name="Sage Merinda",
                    description="Ancient elven scholar who knows the history of the Shadow Dragon",
                    last_location="Grand Library",
                ),
                "captain_thorne": NPCModel(
                    id="captain_thorne",
                    name="Captain Marcus Thorne",
                    description="Grizzled captain of the royal guard, veteran of many battles",
                    last_location="Barracks",
                ),
            },
            # Initial Content - Quests
            initial_quests={
                "gather_information": QuestModel(
                    id="gather_information",
                    title="Gather Information on the Shadow Dragon",
                    description="Speak with Sage Merinda and research the ancient texts about the Shadow Dragon's weaknesses",
                    status="active",
                ),
                "find_ancient_weapon": QuestModel(
                    id="find_ancient_weapon",
                    title="Seek the Dragonbane Sword",
                    description="Legend speaks of a weapon forged specifically to defeat shadow dragons. Find clues to its location.",
                    status="inactive",
                ),
                "rally_allies": QuestModel(
                    id="rally_allies",
                    title="Rally the Kingdom's Allies",
                    description="Convince neighboring kingdoms and noble houses to join the fight against the Shadow Dragon",
                    status="inactive",
                ),
            },
            # World Building
            world_lore=[
                "The Shadow Dragon was sealed away 1000 years ago by the Circle of Five",
                "The sealing required a great sacrifice - the lives of the five greatest heroes of that age",
                "Ancient draconic magic corrupts the land, turning fertile fields into shadowy wastelands",
                "Dragons are said to return every millennium when the celestial alignment is right",
                "The Dragonbane Sword was forged from a fallen star and blessed by all five gods",
            ],
            # Rules & Restrictions
            house_rules=HouseRulesModel(
                critical_hit_tables=True,
                flanking_rules=True,
                milestone_leveling=True,
                death_saves_public=False,
            ),
            allowed_races=[
                "Human",
                "Elf",
                "Dwarf",
                "Halfling",
                "Dragonborn",
                "Tiefling",
            ],
            allowed_classes=[
                "Fighter",
                "Wizard",
                "Cleric",
                "Rogue",
                "Ranger",
                "Paladin",
            ],
            starting_gold_range=GoldRangeModel(min=150, max=300),
            # Additional Info
            theme_mood="Epic High Fantasy",
            world_map_path="/static/images/maps/goldenheart_kingdom.jpg",
            session_zero_notes="Discuss player backstories and how they connect to the kingdom. Establish tone expectations for a high-stakes campaign. Review house rules and character creation guidelines.",
            xp_system="milestone",
            # Metadata
            created_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
            tags=["epic", "dragons", "high-fantasy", "kingdom", "ancient-evil"],
        )

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_campaign_with_all_fields(self) -> None:
        """Test creating a campaign template with all unified model fields."""
        # Save the campaign
        result = self.repo.save_template(self.test_campaign)
        self.assertTrue(result)

        # Verify file was created
        template_file = os.path.join(self.temp_dir, "test_epic_campaign.json")
        self.assertTrue(os.path.exists(template_file))

        # Load and verify JSON structure
        with open(template_file, encoding="utf-8") as f:
            saved_data = json.load(f)

        # Verify all identity fields
        self.assertEqual(saved_data["id"], "test_epic_campaign")
        self.assertEqual(saved_data["name"], "The Dragon's Shadow")
        self.assertEqual(
            saved_data["description"],
            "An epic campaign to save the realm from an ancient dragon's return",
        )

        # Verify core campaign info
        self.assertEqual(
            saved_data["campaign_goal"],
            "Defeat the Shadow Dragon before it plunges the world into eternal darkness",
        )
        self.assertEqual(saved_data["starting_level"], 3)
        self.assertEqual(saved_data["difficulty"], "hard")

        # Verify starting location structure
        self.assertIn("starting_location", saved_data)
        self.assertEqual(saved_data["starting_location"]["name"], "City of Goldenheart")
        self.assertIn("description", saved_data["starting_location"])

        # Verify NPCs structure
        self.assertIn("initial_npcs", saved_data)
        self.assertEqual(len(saved_data["initial_npcs"]), 3)
        self.assertIn("king_aldric", saved_data["initial_npcs"])
        self.assertEqual(
            saved_data["initial_npcs"]["king_aldric"]["name"], "King Aldric the Wise"
        )
        self.assertEqual(
            saved_data["initial_npcs"]["king_aldric"]["last_location"], "Royal Palace"
        )

        # Verify Quests structure
        self.assertIn("initial_quests", saved_data)
        self.assertEqual(len(saved_data["initial_quests"]), 3)
        self.assertIn("gather_information", saved_data["initial_quests"])
        self.assertEqual(
            saved_data["initial_quests"]["gather_information"]["status"], "active"
        )

        # Verify world lore
        self.assertEqual(len(saved_data["world_lore"]), 5)
        self.assertIn("Circle of Five", saved_data["world_lore"][0])

        # Verify house rules structure
        self.assertIn("house_rules", saved_data)
        self.assertTrue(saved_data["house_rules"]["critical_hit_tables"])
        self.assertFalse(saved_data["house_rules"]["death_saves_public"])

        # Verify restrictions
        self.assertEqual(len(saved_data["allowed_races"]), 6)
        self.assertEqual(len(saved_data["allowed_classes"]), 6)
        self.assertIn("Dragonborn", saved_data["allowed_races"])

        # Verify gold range
        self.assertIn("starting_gold_range", saved_data)
        self.assertEqual(saved_data["starting_gold_range"]["min"], 150)
        self.assertEqual(saved_data["starting_gold_range"]["max"], 300)

        # Verify additional info
        self.assertEqual(saved_data["theme_mood"], "Epic High Fantasy")
        self.assertEqual(saved_data["xp_system"], "milestone")
        self.assertEqual(len(saved_data["tags"]), 5)

    def test_read_campaign_preserves_all_fields(self) -> None:
        """Test reading a campaign template preserves all fields."""
        # Save the campaign
        self.repo.save_template(self.test_campaign)

        # Read it back
        loaded_campaign = self.repo.get_template("test_epic_campaign")
        self.assertIsNotNone(loaded_campaign)
        assert loaded_campaign is not None  # Type guard

        # Verify all fields are preserved
        self.assertEqual(loaded_campaign.name, "The Dragon's Shadow")
        self.assertEqual(loaded_campaign.starting_level, 3)
        self.assertEqual(loaded_campaign.difficulty, "hard")

        # Check starting location
        self.assertEqual(loaded_campaign.starting_location.name, "City of Goldenheart")

        # Check NPCs
        self.assertEqual(len(loaded_campaign.initial_npcs), 3)
        self.assertIn("king_aldric", loaded_campaign.initial_npcs)
        self.assertEqual(
            loaded_campaign.initial_npcs["king_aldric"].name, "King Aldric the Wise"
        )

        # Check quests
        self.assertEqual(len(loaded_campaign.initial_quests), 3)
        self.assertIn("gather_information", loaded_campaign.initial_quests)
        self.assertEqual(
            loaded_campaign.initial_quests["gather_information"].status, "active"
        )

        # Check world lore
        self.assertEqual(len(loaded_campaign.world_lore), 5)

        # Check house rules
        self.assertTrue(loaded_campaign.house_rules.critical_hit_tables)
        self.assertFalse(loaded_campaign.house_rules.death_saves_public)

        # Check restrictions
        assert loaded_campaign.allowed_races is not None
        assert loaded_campaign.allowed_classes is not None
        self.assertEqual(len(loaded_campaign.allowed_races), 6)
        self.assertEqual(len(loaded_campaign.allowed_classes), 6)

        # Check gold range
        self.assertIsNotNone(loaded_campaign.starting_gold_range)
        assert loaded_campaign.starting_gold_range is not None  # Type guard
        self.assertEqual(loaded_campaign.starting_gold_range.min, 150)
        self.assertEqual(loaded_campaign.starting_gold_range.max, 300)

    def test_update_campaign_all_fields(self) -> None:
        """Test updating a campaign template with changes to various fields."""
        # Save initial campaign
        self.repo.save_template(self.test_campaign)

        # Load and modify
        campaign = self.repo.get_template("test_epic_campaign")
        assert campaign is not None  # Type guard

        # Update various fields
        campaign.starting_level = 5
        campaign.difficulty = "deadly"

        # Add a new NPC
        campaign.initial_npcs["blacksmith_gareth"] = NPCModel(
            id="blacksmith_gareth",
            name="Gareth the Forgemaster",
            description="Master blacksmith who may know about reforging ancient weapons",
            last_location="Forge District",
        )

        # Add a new quest
        campaign.initial_quests["forge_weapon"] = QuestModel(
            id="forge_weapon",
            title="Reforge the Dragonbane Sword",
            description="Work with Gareth to reforge the legendary weapon",
            status="inactive",
        )

        # Add new world lore
        campaign.world_lore.append(
            "The Forge of Stars where the Dragonbane Sword was created still exists"
        )

        # Update house rules
        campaign.house_rules.flanking_rules = False

        # Update restrictions
        assert campaign.allowed_races is not None  # Type guard
        campaign.allowed_races.append("Gnome")

        # Update gold range
        assert campaign.starting_gold_range is not None  # Type guard
        campaign.starting_gold_range.max = 500

        # Save updated campaign
        campaign.last_modified = datetime.now(timezone.utc)
        result = self.repo.save_template(campaign)
        self.assertTrue(result)

        # Load again and verify updates
        updated = self.repo.get_template("test_epic_campaign")
        assert updated is not None  # Type guard
        self.assertEqual(updated.starting_level, 5)
        self.assertEqual(updated.difficulty, "deadly")
        self.assertEqual(len(updated.initial_npcs), 4)
        self.assertEqual(len(updated.initial_quests), 4)
        self.assertEqual(len(updated.world_lore), 6)
        self.assertFalse(updated.house_rules.flanking_rules)
        assert updated.allowed_races is not None  # Type guard
        self.assertEqual(len(updated.allowed_races), 7)
        assert updated.starting_gold_range is not None  # Type guard
        self.assertEqual(updated.starting_gold_range.max, 500)

    def test_delete_campaign_with_all_fields(self) -> None:
        """Test deleting a campaign template removes all data."""
        # Save campaign
        self.repo.save_template(self.test_campaign)

        # Verify it exists
        campaign = self.repo.get_template("test_epic_campaign")
        self.assertIsNotNone(campaign)

        # Delete it
        result = self.repo.delete_template("test_epic_campaign")
        self.assertTrue(result)

        # Verify it's gone
        campaign = self.repo.get_template("test_epic_campaign")
        self.assertIsNone(campaign)

        # Verify file is deleted
        template_file = os.path.join(self.temp_dir, "test_epic_campaign.json")
        self.assertFalse(os.path.exists(template_file))

    def test_campaign_without_optional_fields(self) -> None:
        """Test creating a campaign with minimal required fields only."""
        minimal_campaign = CampaignTemplateModel(
            id="minimal_campaign",
            name="Simple Adventure",
            description="A basic adventure template",
            campaign_goal="Complete the quest",
            starting_location=LocationModel(
                name="Village", description="A small village"
            ),
            opening_narrative="Adventure begins...",
            starting_level=1,
            difficulty="normal",
            ruleset_id="dnd5e_standard",
            lore_id="generic_fantasy",
            xp_system="milestone",
        )

        # Save and verify
        result = self.repo.save_template(minimal_campaign)
        self.assertTrue(result)

        # Load and check optional fields are None/empty
        loaded = self.repo.get_template("minimal_campaign")
        assert loaded is not None  # Type guard
        self.assertIsNone(loaded.theme_mood)
        self.assertIsNone(loaded.world_map_path)
        self.assertIsNone(loaded.session_zero_notes)
        self.assertIsNone(loaded.allowed_races)
        self.assertIsNone(loaded.allowed_classes)
        self.assertIsNone(loaded.starting_gold_range)
        self.assertEqual(len(loaded.initial_npcs), 0)
        self.assertEqual(len(loaded.initial_quests), 0)
        self.assertEqual(len(loaded.world_lore), 0)
        self.assertEqual(len(loaded.tags), 0)

    def test_nested_structure_serialization(self) -> None:
        """Test that nested structures serialize and deserialize correctly."""
        # Save campaign with complex nested structures
        self.repo.save_template(self.test_campaign)

        # Load it back
        loaded_campaign = self.repo.get_template("test_epic_campaign")
        assert loaded_campaign is not None  # Type guard

        # Verify all nested structure types
        self.assertIsInstance(loaded_campaign.starting_location, LocationModel)
        self.assertIsInstance(loaded_campaign.house_rules, HouseRulesModel)
        self.assertIsInstance(loaded_campaign.starting_gold_range, GoldRangeModel)

        # Verify NPC dict contains NPCModel instances
        for npc_id, npc in loaded_campaign.initial_npcs.items():
            self.assertIsInstance(npc, NPCModel)
            self.assertEqual(npc.id, npc_id)

        # Verify Quest dict contains QuestModel instances
        for quest_id, quest in loaded_campaign.initial_quests.items():
            self.assertIsInstance(quest, QuestModel)
            self.assertEqual(quest.id, quest_id)


if __name__ == "__main__":
    unittest.main()
