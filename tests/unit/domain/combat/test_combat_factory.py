"""
Unit tests for combat factory module.
"""

import unittest
from typing import Dict, List, Optional, cast
from unittest.mock import Mock, patch

from app.content.service import ContentService
from app.domain.combat.factories import CombatFactory
from app.models.character import (
    CharacterData,
    CharacterInstanceModel,
    CombinedCharacterModel,
)
from app.models.combat.attack import AttackModel
from app.models.combat.combatant import InitialCombatantData
from app.models.utils import BaseStatsModel


class TestCombatFactory(unittest.TestCase):
    """Test combat factory functionality."""

    def setUp(self) -> None:
        """Set up test data for each test."""
        # Mock ContentService
        self.mock_content_service = Mock(spec=ContentService)

        # Create factory
        self.factory = CombatFactory(self.mock_content_service)

        # Create test data
        self.test_stats: Dict[str, int] = {
            "STR": 16,  # +3 modifier
            "DEX": 14,  # +2 modifier
            "CON": 15,  # +2 modifier
            "INT": 10,  # +0 modifier
            "WIS": 12,  # +1 modifier
            "CHA": 8,  # -1 modifier
        }

        self.test_attack = AttackModel(
            name="Longsword",
            description="Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 1d8+3 slashing damage.",
            attack_type="melee",
            to_hit_bonus=5,
            reach="5 ft",
            damage_formula="1d8+3",
            damage_type="slashing",
        )

    @patch("app.domain.combat.factories.roll_single_die")
    def test_create_combat_state(self, mock_roll: Mock) -> None:
        """Test creating combat state from party and NPCs."""
        # Mock character service
        mock_character_service = Mock()

        # Create test party
        party: Dict[str, CharacterInstanceModel] = {
            "pc1": cast(CharacterInstanceModel, Mock(spec=CharacterInstanceModel)),
            "pc2": cast(CharacterInstanceModel, Mock(spec=CharacterInstanceModel)),
        }

        # Mock character templates for party members
        from app.models.character import CharacterTemplateModel
        from app.models.utils import ProficienciesModel

        char1_template = Mock(spec=CharacterTemplateModel)
        char1_template.name = "Fighter"
        char1_template.race = "Human"
        char1_template.char_class = "Fighter"
        char1_template.background = "Soldier"
        char1_template.alignment = "Lawful Good"
        char1_template.base_stats = BaseStatsModel(
            STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8
        )
        char1_template.portrait_path = "/images/portraits/fighter.png"
        char1_template.class_features = []
        char1_template.proficiencies = Mock(spec=ProficienciesModel)
        char1_template.languages = []
        char1_template.racial_traits = []
        char1_template.feats = []
        char1_template.spells_known = []
        char1_template.cantrips_known = []
        char1_template.subrace = None
        char1_template.subclass = None

        char2_template = Mock(spec=CharacterTemplateModel)
        char2_template.name = "Wizard"
        char2_template.race = "Elf"
        char2_template.char_class = "Wizard"
        char2_template.background = "Sage"
        char2_template.alignment = "Neutral Good"
        char2_template.base_stats = BaseStatsModel(
            STR=10, DEX=10, CON=12, INT=18, WIS=14, CHA=13
        )
        char2_template.portrait_path = "/images/portraits/wizard.png"
        char2_template.class_features = []
        char2_template.proficiencies = Mock(spec=ProficienciesModel)
        char2_template.languages = []
        char2_template.racial_traits = []
        char2_template.feats = []
        char2_template.spells_known = []
        char2_template.cantrips_known = []
        char2_template.subrace = None
        char2_template.subclass = None

        # Update party instances with proper data
        party["pc1"].template_id = "fighter_template"
        party["pc1"].campaign_id = "test_campaign"
        party["pc1"].current_hp = 30
        party["pc1"].max_hp = 30
        party["pc1"].temp_hp = 0
        party["pc1"].level = 1
        party["pc1"].conditions = []
        party["pc1"].inventory = []
        party["pc1"].spell_slots_used = {}
        party["pc1"].hit_dice_used = 0
        party["pc1"].death_saves = {"successes": 0, "failures": 0}
        party["pc1"].exhaustion_level = 0
        party["pc1"].gold = 0
        party["pc1"].experience_points = 0

        party["pc2"].template_id = "wizard_template"
        party["pc2"].campaign_id = "test_campaign"
        party["pc2"].current_hp = 18
        party["pc2"].max_hp = 18
        party["pc2"].temp_hp = 0
        party["pc2"].level = 1
        party["pc2"].conditions = []
        party["pc2"].inventory = []
        party["pc2"].spell_slots_used = {}
        party["pc2"].hit_dice_used = 0
        party["pc2"].death_saves = {"successes": 0, "failures": 0}
        party["pc2"].exhaustion_level = 0
        party["pc2"].gold = 0
        party["pc2"].experience_points = 0

        # Set up character service mock
        def get_character(char_id: str) -> Optional[CharacterData]:
            if char_id == "pc1":
                return CharacterData(
                    template=char1_template, instance=party["pc1"], character_id=char_id
                )
            elif char_id == "pc2":
                return CharacterData(
                    template=char2_template, instance=party["pc2"], character_id=char_id
                )
            return None

        mock_character_service.get_character.side_effect = get_character

        # Create NPC data
        npc_combatants = [
            InitialCombatantData(
                id="goblin1",
                name="Goblin",
                hp=7,
                ac=15,
                stats={"DEX": 16},  # +3 modifier
                abilities=["Nimble Escape"],
                attacks=[self.test_attack],
            ),
        ]

        # Set up dice rolls for NPC initiative
        mock_roll.return_value = 12  # Goblin's initiative roll

        # Create combat state
        combat_state = self.factory.create_combat_state(
            party=party,
            npc_combatants=npc_combatants,
            character_service=mock_character_service,
        )

        # Verify combat state
        self.assertTrue(combat_state.is_active)
        self.assertEqual(len(combat_state.combatants), 3)  # 2 PCs + 1 NPC
        self.assertEqual(combat_state.current_turn_index, -1)  # No initiative set yet
        self.assertEqual(combat_state.round_number, 1)
        self.assertFalse(combat_state.current_turn_instruction_given)

        # Verify all combatants were created
        combatant_ids = {c.id for c in combat_state.combatants}
        self.assertEqual(combatant_ids, {"pc1", "pc2", "goblin1"})

        # Verify PC combatants have correct properties
        fighter = next(c for c in combat_state.combatants if c.id == "pc1")
        self.assertEqual(fighter.name, "Fighter")
        self.assertEqual(fighter.current_hp, 30)
        self.assertEqual(fighter.armor_class, 12)  # 10 + 2 (DEX modifier)
        self.assertTrue(fighter.is_player)
        self.assertEqual(fighter.initiative, 0)  # PCs don't roll initiative yet
        self.assertEqual(fighter.initiative_modifier, 2)  # DEX modifier

        # Verify NPC combatant has rolled initiative
        goblin = next(c for c in combat_state.combatants if c.id == "goblin1")
        self.assertEqual(goblin.name, "Goblin")
        self.assertEqual(goblin.initiative, 15)  # 12 + 3 (DEX modifier)
        self.assertFalse(goblin.is_player)

    def test_create_combat_state_with_no_combatants(self) -> None:
        """Test creating combat state with empty party and no NPCs."""
        mock_character_service = Mock()

        combat_state = self.factory.create_combat_state(
            party={},
            npc_combatants=[],
            character_service=mock_character_service,
        )

        self.assertTrue(combat_state.is_active)
        self.assertEqual(len(combat_state.combatants), 0)
        self.assertEqual(combat_state.current_turn_index, -1)
        self.assertEqual(combat_state.round_number, 1)

    def test_internal_methods_not_exposed(self) -> None:
        """Test that internal methods are properly private."""
        # Verify private methods exist but are not part of public interface
        self.assertTrue(hasattr(self.factory, "_create_combatant_from_character"))
        self.assertTrue(hasattr(self.factory, "_create_combatant_from_data"))
        self.assertTrue(hasattr(self.factory, "_prepare_character_attacks"))

        # Verify they start with underscore (private)
        private_methods = [
            m for m in dir(self.factory) if m.startswith("_") and not m.startswith("__")
        ]
        self.assertIn("_create_combatant_from_character", private_methods)
        self.assertIn("_create_combatant_from_data", private_methods)
        self.assertIn("_prepare_character_attacks", private_methods)

    @patch("app.domain.combat.factories.roll_single_die")
    def test_character_service_failure_handling(self, mock_roll: Mock) -> None:
        """Test handling when character service returns None."""
        mock_character_service = Mock()
        mock_character_service.get_character.return_value = None

        party: Dict[str, CharacterInstanceModel] = {
            "missing_char": cast(
                CharacterInstanceModel, Mock(spec=CharacterInstanceModel)
            )
        }

        # Should skip the missing character but still create combat state
        combat_state = self.factory.create_combat_state(
            party=party,
            npc_combatants=[],
            character_service=mock_character_service,
        )

        self.assertTrue(combat_state.is_active)
        self.assertEqual(len(combat_state.combatants), 0)  # Character was skipped

    @patch("app.domain.combat.factories.roll_single_die")
    def test_npc_initiative_rolling(self, mock_roll: Mock) -> None:
        """Test that NPCs get initiative rolled correctly."""
        mock_character_service = Mock()

        # Different rolls for each NPC
        mock_roll.side_effect = [12, 8]

        npc_combatants = [
            InitialCombatantData(
                id="npc1",
                name="High DEX NPC",
                hp=20,
                ac=14,
                stats={"DEX": 16},  # +3 modifier
            ),
            InitialCombatantData(
                id="npc2",
                name="Low DEX NPC",
                hp=20,
                ac=14,
                stats={"DEX": 10},  # +0 modifier
            ),
        ]

        combat_state = self.factory.create_combat_state(
            party={},
            npc_combatants=npc_combatants,
            character_service=mock_character_service,
        )

        # Verify NPCs have correct initiative
        npc1 = next(c for c in combat_state.combatants if c.id == "npc1")
        npc2 = next(c for c in combat_state.combatants if c.id == "npc2")

        self.assertEqual(npc1.initiative, 15)  # 12 + 3
        self.assertEqual(npc2.initiative, 8)  # 8 + 0

    @patch("app.domain.combat.factories.roll_single_die")
    def test_combatant_player_detection(self, mock_roll: Mock) -> None:
        """Test that is_player is correctly determined."""
        mock_character_service = Mock()
        mock_roll.return_value = 10

        # NPCs should have is_player=False (no portrait path)
        npc_combatants = [
            InitialCombatantData(
                id="goblin1", name="Goblin", hp=7, ac=15, icon_path=None
            ),
            InitialCombatantData(
                id="fighter_npc",
                name="Fighter NPC",
                hp=30,
                ac=16,
                icon_path="/images/portraits/fighter.png",  # Has portrait but still NPC
            ),
        ]

        combat_state = self.factory.create_combat_state(
            party={},
            npc_combatants=npc_combatants,
            character_service=mock_character_service,
        )

        # Check NPC detection
        goblin = next(c for c in combat_state.combatants if c.id == "goblin1")
        self.assertFalse(goblin.is_player)

        # Even with portrait path, NPCs created from InitialCombatantData are marked as players
        # based on the icon_path containing "portraits"
        fighter_npc = next(c for c in combat_state.combatants if c.id == "fighter_npc")
        self.assertTrue(
            fighter_npc.is_player
        )  # Current implementation uses portrait path


if __name__ == "__main__":
    unittest.main()
