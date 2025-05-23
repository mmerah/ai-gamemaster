"""
Unit tests for game model validation and functionality.
"""
import unittest
from app.game.models import (
    GameState, CharacterInstance, CharacterSheet, AbilityScores, 
    Proficiencies, CombatState, KnownNPC, Quest, Combatant
)


class TestGameModels(unittest.TestCase):
    """Test game model validation and functionality."""
    
    def test_character_sheet_creation(self):
        """Test character sheet model."""
        sheet = CharacterSheet(
            id="test_char",
            name="Test Character",
            race="Human",
            char_class="Fighter",
            level=1,
            base_stats=AbilityScores(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8),
            proficiencies=Proficiencies(
                armor=["Light armor", "Medium armor", "Heavy armor", "Shields"],
                weapons=["Simple weapons", "Martial weapons"],
                saving_throws=["STR", "CON"],
                skills=["Acrobatics", "Athletics"]
            )
        )
        
        self.assertEqual(sheet.name, "Test Character")
        self.assertEqual(sheet.race, "Human")
        self.assertEqual(sheet.char_class, "Fighter")
        self.assertEqual(sheet.level, 1)
        self.assertEqual(sheet.base_stats.STR, 16)
    
    def test_character_instance_creation(self):
        """Test character instance model."""
        sheet = CharacterSheet(
            id="test_char", name="Test", race="Human", char_class="Fighter", level=1,
            base_stats=AbilityScores(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8),
            proficiencies=Proficiencies()
        )
        
        instance = CharacterInstance(
            **sheet.model_dump(),
            current_hp=20, max_hp=20, armor_class=16,
            temporary_hp=0, conditions=[], inventory=[], gold=100
        )
        
        self.assertEqual(instance.current_hp, 20)
        self.assertEqual(instance.max_hp, 20)
        self.assertEqual(instance.armor_class, 16)
        self.assertEqual(instance.gold, 100)
    
    def test_ability_scores_model(self):
        """Test ability scores model."""
        stats = AbilityScores(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8)
        
        self.assertEqual(stats.STR, 16)
        self.assertEqual(stats.DEX, 14)
        self.assertEqual(stats.CON, 15)
        self.assertEqual(stats.INT, 10)
        self.assertEqual(stats.WIS, 12)
        self.assertEqual(stats.CHA, 8)
    
    def test_proficiencies_model(self):
        """Test proficiencies model."""
        prof = Proficiencies(
            armor=["Light armor"],
            weapons=["Simple weapons"],
            saving_throws=["DEX", "INT"],
            skills=["Stealth", "Investigation"]
        )
        
        self.assertIn("Light armor", prof.armor)
        self.assertIn("Simple weapons", prof.weapons)
        self.assertIn("DEX", prof.saving_throws)
        self.assertIn("Stealth", prof.skills)
    
    def test_combat_state_model(self):
        """Test combat state model."""
        combat = CombatState()
        self.assertFalse(combat.is_active)
        self.assertEqual(len(combat.combatants), 0)
        self.assertEqual(len(combat.monster_stats), 0)
        self.assertEqual(combat.current_turn_index, 0)
        self.assertEqual(combat.round_number, 1)
    
    def test_combatant_model(self):
        """Test combatant model."""
        combatant = Combatant(
            id="char1",
            name="Test Character",
            initiative=15,
            is_player=True
        )
        
        self.assertEqual(combatant.id, "char1")
        self.assertEqual(combatant.name, "Test Character")
        self.assertEqual(combatant.initiative, 15)
        self.assertTrue(combatant.is_player)
    
    def test_known_npc_model(self):
        """Test known NPC model."""
        npc = KnownNPC(
            id="npc1",
            name="Test NPC",
            description="A test character",
            last_location="Test Town"
        )
        
        self.assertEqual(npc.id, "npc1")
        self.assertEqual(npc.name, "Test NPC")
        self.assertEqual(npc.description, "A test character")
        self.assertEqual(npc.last_location, "Test Town")
    
    def test_quest_model(self):
        """Test quest model."""
        quest = Quest(
            id="quest1",
            title="Test Quest",
            description="A test quest",
            status="active",
            details={"objectives": ["Find the thing", "Return the thing"]}
        )
        
        self.assertEqual(quest.id, "quest1")
        self.assertEqual(quest.title, "Test Quest")
        self.assertEqual(quest.status, "active")
        self.assertEqual(len(quest.details["objectives"]), 2)
    
    def test_game_state_model(self):
        """Test game state model."""
        game_state = GameState()
        self.assertIsNotNone(game_state.party)
        self.assertIsNotNone(game_state.combat)
        self.assertIsNotNone(game_state.chat_history)
        self.assertIsNotNone(game_state.known_npcs)
        self.assertIsNotNone(game_state.active_quests)
        self.assertIsNotNone(game_state.world_lore)
        self.assertIsNotNone(game_state.event_summary)


if __name__ == '__main__':
    unittest.main()
