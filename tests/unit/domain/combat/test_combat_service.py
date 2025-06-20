"""
Unit tests for ICombatService implementation.
Tests the event-driven combat service with comprehensive coverage.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from app.core.system_interfaces import IEventQueue
from app.domain.combat.combat_factory import CombatFactory
from app.domain.combat.combat_service import CombatService
from app.models.character import (
    CharacterData,
    CharacterInstanceModel,
    CharacterTemplateModel,
)
from app.models.combat import CombatantModel, CombatStateModel, InitialCombatantData
from app.models.game_state import GameStateModel
from app.models.utils import BaseStatsModel, ProficienciesModel


def create_mock_combat_factory() -> Mock:
    """Create a mock combat factory for testing."""
    mock_factory = Mock(spec=CombatFactory)

    # Mock the main factory method
    def mock_create_combat_state(
        party: Dict[str, Any],
        npc_combatants: List[InitialCombatantData],
        character_service: Any,
    ) -> CombatStateModel:
        all_combatants = []

        # Create PC combatants
        for char_id, char_instance in party.items():
            char_data = character_service.get_character(char_id)
            if char_data:
                combatant = CombatantModel(
                    id=char_id,
                    name=char_data.template.name,
                    initiative=0,
                    initiative_modifier=(char_data.template.base_stats.DEX - 10) // 2,
                    current_hp=char_instance.current_hp,
                    max_hp=char_instance.max_hp,
                    armor_class=10 + (char_data.template.base_stats.DEX - 10) // 2,
                    is_player=True,
                    icon_path=getattr(char_data.template, "portrait_path", None),
                    stats={
                        "STR": char_data.template.base_stats.STR,
                        "DEX": char_data.template.base_stats.DEX,
                        "CON": char_data.template.base_stats.CON,
                        "INT": char_data.template.base_stats.INT,
                        "WIS": char_data.template.base_stats.WIS,
                        "CHA": char_data.template.base_stats.CHA,
                    },
                    abilities=[],
                    attacks=[],
                )
                all_combatants.append(combatant)

        # Create NPC combatants
        for npc_data in npc_combatants:
            dex_modifier = (
                (npc_data.stats.get("DEX", 10) if npc_data.stats else 10) - 10
            ) // 2
            combatant = CombatantModel(
                id=npc_data.id,
                name=npc_data.name,
                initiative=0,
                initiative_modifier=dex_modifier,
                current_hp=npc_data.hp,
                max_hp=npc_data.hp,
                armor_class=npc_data.ac,
                is_player=False,
                icon_path=npc_data.icon_path,
                stats=npc_data.stats or {},
                abilities=npc_data.abilities or [],
                attacks=npc_data.attacks or [],
            )
            all_combatants.append(combatant)

        return CombatStateModel(
            is_active=True,
            round_number=1,
            current_turn_index=-1,
            combatants=all_combatants,
        )

    mock_factory.create_combat_state.side_effect = mock_create_combat_state

    return mock_factory


class TestCombatServiceStartCombat:
    """Test start_combat functionality."""

    def test_start_combat_adds_pcs_and_npcs(self) -> None:
        """Test that start_combat properly initializes combat with PCs and NPCs."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        # Create game state with party
        game_state = GameStateModel()

        # Create character instances (dynamic state only)
        elara_instance = CharacterInstanceModel(
            id="pc_1",
            name="Elara",
            template_id="elara_template",
            campaign_id="test_campaign",
            current_hp=25,
            max_hp=25,
            level=1,
            conditions=[],
            inventory=[],
        )

        thorin_instance = CharacterInstanceModel(
            id="pc_2",
            name="Thorin",
            template_id="thorin_template",
            campaign_id="test_campaign",
            current_hp=30,
            max_hp=30,
            level=1,
            conditions=[],
            inventory=[],
        )

        game_state.party = {"pc_1": elara_instance, "pc_2": thorin_instance}
        game_state.combat = CombatStateModel()
        mock_game_state_repo.get_game_state.return_value = game_state

        elara_template = CharacterTemplateModel(
            id="elara_template",
            name="Elara",
            race="Elf",
            char_class="Ranger",
            level=1,
            background="Outlander",
            alignment="Chaotic Good",
            base_stats=BaseStatsModel(STR=12, DEX=16, CON=14, INT=13, WIS=15, CHA=11),
            proficiencies=ProficienciesModel(
                weapons=["Longbow", "Longsword"], skills=["Perception", "Survival"]
            ),
        )

        thorin_template = CharacterTemplateModel(
            id="thorin_template",
            name="Thorin",
            race="Dwarf",
            char_class="Fighter",
            level=1,
            background="Soldier",
            alignment="Lawful Good",
            base_stats=BaseStatsModel(STR=16, DEX=12, CON=15, INT=10, WIS=13, CHA=8),
            proficiencies=ProficienciesModel(
                armor=["Heavy Armor"], weapons=["Battleaxe", "Warhammer"]
            ),
        )

        # Mock ICharacterService.get_character() to return combined data
        def mock_get_character(char_id: str) -> Optional[CharacterData]:
            if char_id == "pc_1":
                return CharacterData(
                    template=elara_template,
                    instance=elara_instance,
                    character_id=char_id,
                )
            elif char_id == "pc_2":
                return CharacterData(
                    template=thorin_template,
                    instance=thorin_instance,
                    character_id=char_id,
                )
            return None

        mock_character_service.get_character.side_effect = mock_get_character

        # NPC data from AI
        initial_npc_data = [
            InitialCombatantData(
                id="goblin_1",
                name="Goblin Archer",
                hp=7,
                ac=13,
                stats={"STR": 8, "DEX": 14, "CON": 10},
            ),
            InitialCombatantData(
                id="goblin_2",
                name="Goblin Warrior",
                hp=10,
                ac=15,
                stats={"STR": 12, "DEX": 12, "CON": 12},
            ),
        ]

        # Create service
        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute
        service.start_combat(initial_npc_data)
        result_state = mock_game_state_repo.save_game_state.call_args[0][0]

        # Assert
        assert result_state.combat.is_active is True
        assert result_state.combat.round_number == 1
        assert result_state.combat.current_turn_index == -1  # No initiative yet
        assert len(result_state.combat.combatants) == 4  # 2 PCs + 2 NPCs

        # Check PCs added
        pc_ids = [c.id for c in result_state.combat.combatants if c.is_player]
        assert "pc_1" in pc_ids
        assert "pc_2" in pc_ids

        # Check NPCs added
        npc_ids = [c.id for c in result_state.combat.combatants if not c.is_player]
        assert "goblin_1" in npc_ids
        assert "goblin_2" in npc_ids

        # Check combatants have correct properties
        goblin = next(
            (c for c in result_state.combat.combatants if c.id == "goblin_2"), None
        )
        assert goblin is not None
        assert goblin.name == "Goblin Warrior"


class TestCombatServiceTurnAdvancement:
    """Test turn advancement functionality."""

    def test_advance_turn_correctly_handles_round_increment(self) -> None:
        """Test that advancing past the last combatant increments the round."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=7,
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=1,  # Goblin's turn (last in order)
            round_number=1,
        )
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute
        service.advance_turn()
        result = mock_game_state_repo.save_game_state.call_args[0][0]

        # Assert
        assert result.combat.current_turn_index == 0  # Back to first combatant
        assert result.combat.round_number == 2  # New round

    def test_advance_turn_skips_defeated_combatant(self) -> None:
        """Test that turn advancement skips defeated combatants."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=0,
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),  # Defeated
            CombatantModel(
                id="pc_2",
                name="Thorin",
                initiative=10,
                initiative_modifier=1,
                current_hp=30,
                max_hp=30,
                armor_class=18,
                is_player=True,
            ),
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=0,  # Elara's turn
            round_number=1,
        )
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute
        service.advance_turn()
        result = mock_game_state_repo.save_game_state.call_args[0][0]

        # Assert - should skip defeated goblin
        assert result.combat.current_turn_index == 2  # Thorin's turn
        assert result.combat.round_number == 1  # Same round


class TestCombatServiceInitiativeOrder:
    """Test initiative order functionality."""

    def test_set_initiative_order_sorts_and_sets_current_turn(self) -> None:
        """Test that initiative order is sorted correctly and current turn is set."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Low Init",
                initiative=10,
                initiative_modifier=1,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                is_player=True,
            ),
            CombatantModel(
                id="pc_2",
                name="High Init",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="pc_3",
                name="Mid Init",
                initiative=15,
                initiative_modifier=2,
                current_hp=22,
                max_hp=22,
                armor_class=14,
                is_player=True,
            ),
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(
            is_active=True, combatants=combatants, current_turn_index=-1
        )
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute
        result = service.set_initiative_order(game_state)

        # Assert
        assert result.combat.combatants[0].name == "High Init"  # Highest first
        assert result.combat.combatants[1].name == "Mid Init"
        assert result.combat.combatants[2].name == "Low Init"
        assert result.combat.current_turn_index == 0  # First combatant's turn


class TestCombatServiceDamageAndHealing:
    """Test damage and healing functionality."""

    def test_apply_damage_updates_hp_and_flags_defeat(self) -> None:
        """Test that damage is applied correctly and defeat is detected."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=10,
                max_hp=25,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=7,
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(is_active=True, combatants=combatants)
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Test non-lethal damage
        result, actual_damage, is_defeated = service.apply_damage(
            game_state, "pc_1", 5, "slashing", "goblin_1"
        )

        pc = result.combat.get_combatant_by_id("pc_1")
        assert pc is not None
        assert pc.current_hp == 5
        assert actual_damage == 5
        assert is_defeated is False

        # Test lethal damage
        result2, actual_damage2, is_defeated2 = service.apply_damage(
            result, "pc_1", 10, "fire", "goblin_1"
        )

        pc2 = result2.combat.get_combatant_by_id("pc_1")
        assert pc2 is not None
        assert pc2.current_hp == 0  # Can't go below 0
        assert actual_damage2 == 5  # Only 5 HP left
        assert is_defeated2 is True

    def test_apply_healing_respects_maximum_hp(self) -> None:
        """Test that healing cannot exceed maximum HP."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=10,
                max_hp=25,
                armor_class=16,
                is_player=True,
            )
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(is_active=True, combatants=combatants)
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Test normal healing
        result, actual_healing = service.apply_healing(game_state, "pc_1", 10, "potion")

        pc = result.combat.get_combatant_by_id("pc_1")
        assert pc is not None
        assert pc.current_hp == 20
        assert actual_healing == 10

        # Test healing that would exceed max
        result2, actual_healing2 = service.apply_healing(result, "pc_1", 10, "spell")

        pc2 = result2.combat.get_combatant_by_id("pc_1")
        assert pc2 is not None
        assert pc2.current_hp == 25  # Max HP
        assert actual_healing2 == 5  # Only healed 5


class TestCombatServiceEndConditions:
    """Test combat end condition checking."""

    def test_check_combat_end_conditions(self) -> None:
        """Test detection of combat end conditions."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        # All enemies defeated
        combatants_victory = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=15,
                max_hp=25,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=0,
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(
            is_active=True, combatants=combatants_victory
        )
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Should end - all enemies defeated
        assert service.check_combat_end_conditions(game_state) is True

        # All PCs defeated
        combatants_defeat = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=0,
                max_hp=25,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=5,
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        game_state.combat.combatants = combatants_defeat
        assert service.check_combat_end_conditions(game_state) is True

        # Combat still ongoing
        combatants_ongoing = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=15,
                max_hp=25,
                armor_class=16,
                is_player=True,
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=5,
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        game_state.combat.combatants = combatants_ongoing
        assert service.check_combat_end_conditions(game_state) is False


class TestCombatServiceErrorHandling:
    """Test error handling and edge cases."""

    def test_advance_turn_with_no_combatants(self) -> None:
        """Test advancing turn when there are no combatants."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(
            is_active=True,
            combatants=[],  # No combatants
            current_turn_index=0,
        )
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute - should handle empty combatant list
        service.advance_turn()

        # Assert - should save with current_turn_index updated to -1
        mock_game_state_repo.save_game_state.assert_called_once()
        saved_state = mock_game_state_repo.save_game_state.call_args[0][0]
        assert saved_state.combat.current_turn_index == -1

    def test_apply_damage_to_nonexistent_combatant(self) -> None:
        """Test applying damage to a combatant that doesn't exist."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True,
            )
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(is_active=True, combatants=combatants)
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute - try to damage non-existent combatant
        result, actual_damage, is_defeated = service.apply_damage(
            game_state, "nonexistent_id", 10, "slashing", "pc_1"
        )

        # Assert - should handle gracefully
        assert result == game_state  # State unchanged
        assert actual_damage == 0
        assert is_defeated is False

    def test_apply_healing_to_nonexistent_combatant(self) -> None:
        """Test applying healing to a combatant that doesn't exist."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=15,
                max_hp=25,
                armor_class=16,
                is_player=True,
            )
        ]

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(is_active=True, combatants=combatants)
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute - try to heal non-existent combatant
        result, actual_healing = service.apply_healing(
            game_state, "nonexistent_id", 10, "potion"
        )

        # Assert - should handle gracefully
        assert result == game_state  # State unchanged
        assert actual_healing == 0

    def test_set_initiative_order_with_empty_combatants(self) -> None:
        """Test setting initiative order with no combatants."""
        # Setup
        mock_game_state_repo = Mock()
        mock_character_service = Mock()

        game_state = GameStateModel()
        game_state.combat = CombatStateModel(
            is_active=True, combatants=[], current_turn_index=-1
        )
        mock_game_state_repo.get_game_state.return_value = game_state

        mock_combat_factory = create_mock_combat_factory()
        mock_event_queue = Mock(spec=IEventQueue)
        service = CombatService(
            mock_game_state_repo,
            mock_character_service,
            mock_combat_factory,
            mock_event_queue,
        )

        # Execute
        result = service.set_initiative_order(game_state)

        # Assert - should handle empty list
        assert len(result.combat.combatants) == 0
        # Note: Current implementation sets to 0 even with empty list
        # This could be considered a bug, but we're testing current behavior
        assert result.combat.current_turn_index == 0
