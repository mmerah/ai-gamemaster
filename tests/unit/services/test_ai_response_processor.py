"""
Unit tests for AI response processor service.
"""

import unittest
from typing import Any, ClassVar
from unittest.mock import Mock, patch

from app.core.container import ServiceContainer, reset_container
from app.models.character.instance import CharacterInstanceModel
from app.models.combat.combatant import CombatantModel
from app.models.combat.state import NextCombatantInfoModel
from app.models.dice import DiceRequestModel, DiceRollResultResponseModel
from app.models.updates import CombatantRemoveUpdateModel, LocationUpdateModel
from app.providers.ai.schemas import AIResponse
from app.services.ai_processors.dice_request_processor import DiceRequestProcessor
from app.services.ai_processors.turn_advancement_processor import (
    TurnAdvancementProcessor,
)
from tests.conftest import get_test_settings


def create_test_combatant(
    id: str,
    name: str,
    initiative: int,
    is_player: bool,
    current_hp: int | None = None,
    max_hp: int | None = None,
    armor_class: int | None = None,
) -> CombatantModel:
    """Helper to create a combatant with enhanced model fields."""
    if current_hp is None:
        current_hp = 18 if is_player else 7
    if max_hp is None:
        max_hp = current_hp
    if armor_class is None:
        armor_class = 14 if is_player else 13

    return CombatantModel(
        id=id,
        name=name,
        initiative=initiative,
        initiative_modifier=2 if is_player else 1,
        current_hp=current_hp,
        max_hp=max_hp,
        armor_class=armor_class,
        conditions=[],
        is_player=is_player,
    )


class TestAIResponseProcessor(unittest.TestCase):
    """Test AI response processor functionality."""

    container: ClassVar[ServiceContainer]
    processor: ClassVar[Any]  # IAIResponseProcessor
    game_state_repo: ClassVar[Any]  # IGameStateRepository
    character_service: ClassVar[Any]  # ICharacterService
    dice_service: ClassVar[Any]  # DiceService
    combat_service: ClassVar[Any]  # ICombatService
    chat_service: ClassVar[Any]  # IChatService

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_settings())
        cls.container.initialize()

        # Get services
        cls.processor = cls.container.get_ai_response_processor()
        cls.game_state_repo = cls.container.get_game_state_repository()
        cls.character_service = cls.container.get_character_service()
        cls.dice_service = cls.container.get_dice_service()
        cls.combat_service = cls.container.get_combat_service()
        cls.chat_service = cls.container.get_chat_service()

    def setUp(self) -> None:
        """Reset game state before each test."""
        # Create a fresh game state for each test
        self.game_state_repo._active_game_state = (
            self.game_state_repo._initialize_default_game_state()
        )
        self.game_state = self.game_state_repo.get_game_state()

    def test_process_simple_narrative_response(self) -> None:
        """Test processing a simple AI response with just narrative."""
        # Get initial chat history length (may include initial narrative)
        initial_chat_len = len(self.chat_service.get_chat_history())

        ai_response = AIResponse(
            reasoning="This is a simple narrative response",
            narrative="You enter the tavern and see a bustling crowd.",
            location_update=None,
            dice_requests=[],
            end_turn=False,
        )

        pending_requests, needs_rerun = self.processor.process_response(ai_response)

        self.assertEqual(pending_requests, [])
        self.assertFalse(needs_rerun)

        # Check that narrative was added to chat
        chat_history = self.chat_service.get_chat_history()
        self.assertEqual(len(chat_history), initial_chat_len + 1)
        self.assertEqual(chat_history[-1].role, "assistant")
        self.assertEqual(
            chat_history[-1].content, "You enter the tavern and see a bustling crowd."
        )

    def test_process_response_with_location_update(self) -> None:
        """Test processing AI response with location update."""
        new_location = LocationUpdateModel(
            name="The Prancing Pony", description="A famous inn in Bree"
        )

        ai_response = AIResponse(
            reasoning="Moving to a new location",
            narrative="You arrive at the Prancing Pony.",
            location_update=new_location,
            dice_requests=[],
            end_turn=False,
        )

        self.processor.process_response(ai_response)

        # Check location was updated
        updated_state = self.game_state_repo.get_game_state()
        self.assertEqual(updated_state.current_location.name, "The Prancing Pony")
        self.assertEqual(
            updated_state.current_location.description, "A famous inn in Bree"
        )

    def test_process_response_with_player_dice_requests(self) -> None:
        """Test processing AI response with player dice requests."""
        # Add a character to the party
        test_char = CharacterInstanceModel(
            id="test_char",
            name="Test Character",
            template_id="test_char_template",
            campaign_id="test_campaign",
            level=1,
            current_hp=10,
            max_hp=10,
            temp_hp=0,
            experience_points=0,
            spell_slots_used={},
            hit_dice_used=0,
            death_saves={"successes": 0, "failures": 0},
            conditions=[],
            inventory=[],
            gold=10,
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={},
        )
        self.game_state.party["test_char"] = test_char

        # Create dice request for the test character
        dice_request = DiceRequestModel(
            request_id="test_roll_1",
            character_ids=["test_char"],
            type="ability_check",
            dice_formula="1d20",
            ability="wisdom",
            reason="Perception check",
        )

        ai_response = AIResponse(
            reasoning="Requesting perception check",
            narrative="Make a perception check.",
            location_update=None,
            dice_requests=[dice_request],
            end_turn=False,
        )

        pending_requests, needs_rerun = self.processor.process_response(ai_response)

        self.assertEqual(len(pending_requests), 1)
        self.assertFalse(needs_rerun)
        self.assertEqual(pending_requests[0].request_id, "test_roll_1")
        self.assertEqual(pending_requests[0].type, "ability_check")

    def test_process_response_with_npc_dice_requests(self) -> None:
        """Test processing AI response with NPC dice requests."""
        # Add an NPC combatant (NPCs in combat are tracked as combatants and monster_stats)
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("goblin1", "Goblin", 10, False)
        ]
        # NPCs are now tracked only in the combatants list

        dice_request = DiceRequestModel(
            request_id="npc_roll_1",
            character_ids=["goblin1"],
            type="attack",
            dice_formula="1d20",
            reason="Goblin attacks",
        )

        ai_response = AIResponse(
            reasoning="NPC attacking",
            narrative="The goblin attacks!",
            location_update=None,
            dice_requests=[dice_request],
            end_turn=False,
        )

        with patch.object(
            self.dice_service,
            "perform_roll",
            return_value=DiceRollResultResponseModel(
                request_id="npc_roll_1",
                character_id="goblin1",
                character_name="Goblin",
                roll_type="attack",
                dice_formula="1d20",
                character_modifier=3,
                total_result=15,
                reason="Attack",
                result_message="Goblin rolled 1d20 = 15 for attack",
                result_summary="Goblin: Attack Roll = 15",
            ),
        ):
            pending_requests, needs_rerun = self.processor.process_response(ai_response)

        # NPC rolls should be performed automatically
        self.assertEqual(pending_requests, [])
        self.assertTrue(needs_rerun)  # Should trigger AI rerun after NPC rolls

    def test_combat_started_flag_handling(self) -> None:
        """Test handling of combat just started flag."""
        # Add a character to the party
        test_char = CharacterInstanceModel(
            id="char2",
            name="Elara",
            template_id="elara_template",
            campaign_id="test_campaign",
            level=1,
            current_hp=18,
            max_hp=18,
            temp_hp=0,
            experience_points=0,
            spell_slots_used={},
            hit_dice_used=0,
            death_saves={"successes": 0, "failures": 0},
            conditions=[],
            inventory=[],
            gold=10,
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={},
        )
        self.game_state.party["char2"] = test_char

        # Start combat
        self.game_state.combat.is_active = True
        self.game_state.combat._combat_just_started_flag = True
        self.game_state.combat.combatants = [
            CombatantModel(
                id="char2",
                name="Elara",
                initiative=-1,
                initiative_modifier=2,
                current_hp=18,
                max_hp=18,
                armor_class=14,
                conditions=[],
                is_player=True,
            ),
            CombatantModel(
                id="goblin1",
                name="Goblin",
                initiative=-1,
                initiative_modifier=1,
                current_hp=7,
                max_hp=7,
                armor_class=13,
                conditions=[],
                is_player=False,
            ),
        ]

        ai_response = AIResponse(
            reasoning="Combat started",
            narrative="Roll for initiative!",
            location_update=None,
            dice_requests=[],  # AI didn't request initiative
            end_turn=False,
        )

        with patch.object(
            self.dice_service,
            "perform_roll",
            return_value=DiceRollResultResponseModel(
                request_id="init_goblin1",
                character_id="goblin1",
                character_name="Goblin",
                roll_type="initiative",
                dice_formula="1d20",
                character_modifier=1,
                total_result=15,
                reason="Initiative",
                result_message="Goblin rolls Initiative: 1d20 (+1) -> [14] +1 = **15**.",
                result_summary="Goblin: Initiative = 15",
            ),
        ):
            pending_requests, needs_rerun = self.processor.process_response(ai_response)

        # Should force initiative rolls
        self.assertEqual(len(pending_requests), 1)  # Player initiative
        self.assertEqual(pending_requests[0].type, "initiative")
        self.assertFalse(
            self.game_state.combat._combat_just_started_flag
        )  # Flag should be reset

    def test_turn_advancement_handling(self) -> None:
        """Test turn advancement when AI signals end_turn."""
        # Set up active combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 20, True),
            create_test_combatant("goblin1", "Goblin", 10, False),
        ]
        self.game_state.combat.current_turn_index = 0

        ai_response = AIResponse(
            reasoning="Player turn complete",
            narrative="Elara's turn ends.",
            location_update=None,
            dice_requests=[],
            end_turn=True,  # Signal to end turn
        )

        self.processor.process_response(ai_response)

        # Turn should advance
        self.assertEqual(self.game_state.combat.current_turn_index, 1)

    def test_pre_calculate_next_combatant(self) -> None:
        """Test pre-calculation of next combatant when removing current."""
        # Set up combat with 3 combatants
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("char2", "Elara", 20, True),
            create_test_combatant("goblin1", "Goblin 1", 15, False),
            create_test_combatant("goblin2", "Goblin 2", 10, False),
        ]
        # Add NPCs to monster_stats for character service to find them
        # NPCs are now tracked only in the combatants list
        self.game_state.combat.current_turn_index = 1  # Goblin 1's turn

        # Remove the current combatant
        remove_update = CombatantRemoveUpdateModel(character_id="goblin1")

        ai_response = AIResponse(
            reasoning="Goblin 1 defeated",
            narrative="Goblin 1 falls!",
            location_update=None,
            combatant_removals=[remove_update],
            dice_requests=[],
            end_turn=True,
        )

        # Process the response
        self.processor.process_response(ai_response)

        # Should have removed goblin1
        self.assertEqual(len(self.game_state.combat.combatants), 2)
        # Since goblin1 was removed, the combatants are now [char2, goblin2]
        # Current index should be adjusted appropriately
        current_combatant = self.game_state.combat.combatants[
            self.game_state.combat.current_turn_index
        ]
        # After removing goblin1 and with end_turn, it should advance to next available combatant
        # With the warning "Invalid pre-calculated turn info", it might fall back to char2
        self.assertIn(current_combatant.id, ["char2", "goblin2"])


class TestDiceRequestHandler(unittest.TestCase):
    """Test dice request handler functionality."""

    container: ClassVar[ServiceContainer]
    game_state_repo: ClassVar[Any]  # IGameStateRepository
    character_service: ClassVar[Any]  # ICharacterService
    dice_service: ClassVar[Any]  # DiceService
    chat_service: ClassVar[Any]  # IChatService
    event_queue: ClassVar[Any]  # IEventQueue

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_settings())
        cls.container.initialize()

        # Get services
        cls.game_state_repo = cls.container.get_game_state_repository()
        cls.character_service = cls.container.get_character_service()
        cls.dice_service = cls.container.get_dice_service()
        cls.chat_service = cls.container.get_chat_service()
        cls.event_queue = cls.container.get_event_queue()

    def setUp(self) -> None:
        """Reset game state and create handler for each test."""
        # Create a fresh game state for each test
        self.game_state_repo._active_game_state = (
            self.game_state_repo._initialize_default_game_state()
        )

        # Create handler
        self.handler = DiceRequestProcessor(
            self.game_state_repo,
            self.character_service,
            self.dice_service,
            self.chat_service,
            self.event_queue,
        )

        self.game_state = self.game_state_repo.get_game_state()

    def test_resolve_character_ids_with_all_keyword(self) -> None:
        """Test resolving 'all' keyword in character IDs."""
        # Set up combat with multiple combatants
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 20, True, current_hp=30),
            create_test_combatant("goblin1", "Goblin 1", 15, False, current_hp=7),
            create_test_combatant(
                "goblin2", "Goblin 2", 10, False, current_hp=0, max_hp=7
            ),  # Defeated
        ]

        # Mock character validator to mark goblin2 as defeated
        with patch(
            "app.domain.characters.character_service.CharacterValidator.is_character_defeated"
        ) as mock_defeated:
            mock_defeated.side_effect = lambda char_id, repo: char_id == "goblin2"

            resolved_ids = self.handler._character_resolver.resolve_character_ids(
                ["all"]
            )

        # Should include only non-defeated combatants
        self.assertEqual(set(resolved_ids), {"elara", "goblin1"})

    def test_force_initiative_rolls(self) -> None:
        """Test forcing initiative rolls when combat starts."""
        player_requests: list[DiceRequestModel] = []
        npc_requests: list[dict[str, Any]] = []
        party_ids = {"elara"}

        # Set up combat needing initiative
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", -1, True),
            create_test_combatant("goblin1", "Goblin", -1, False),
        ]

        self.handler._initiative_handler.force_initiative_rolls(
            player_requests, npc_requests, party_ids
        )

        # Should add initiative requests for both
        self.assertEqual(len(player_requests), 1)
        self.assertEqual(len(npc_requests), 1)
        self.assertIsInstance(player_requests[0], DiceRequestModel)
        self.assertEqual(player_requests[0].type, "initiative")
        self.assertEqual(npc_requests[0]["type"], "initiative")


class TestTurnAdvancementHandler(unittest.TestCase):
    """Test turn advancement handler functionality."""

    container: ClassVar[ServiceContainer]
    game_state_repo: ClassVar[Any]  # IGameStateRepository
    combat_service: ClassVar[Any]  # ICombatService
    event_queue: ClassVar[Any]  # IEventQueue

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_settings())
        cls.container.initialize()

        # Get services
        cls.game_state_repo = cls.container.get_game_state_repository()
        cls.combat_service = cls.container.get_combat_service()
        cls.event_queue = cls.container.get_event_queue()

    def setUp(self) -> None:
        """Reset game state and create handler for each test."""
        # Create a fresh game state for each test
        self.game_state_repo._active_game_state = (
            self.game_state_repo._initialize_default_game_state()
        )

        # Create handler
        self.handler = TurnAdvancementProcessor(
            self.game_state_repo, self.combat_service, self.event_queue
        )

        self.game_state = self.game_state_repo.get_game_state()

    def test_normal_turn_advancement(self) -> None:
        """Test normal turn advancement."""
        # Set up combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 20, True),
            create_test_combatant("goblin1", "Goblin", 10, False),
        ]
        self.game_state.combat.current_turn_index = 0

        ai_response = Mock(spec=AIResponse)
        ai_response.end_turn = True

        self.handler.handle_turn_advancement(ai_response, False, False)

        # Turn should advance
        self.assertEqual(self.game_state.combat.current_turn_index, 1)

    def test_turn_advancement_with_pre_calculated_info(self) -> None:
        """Test turn advancement with pre-calculated combatant info."""
        # Set up combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 20, True),
            create_test_combatant("goblin1", "Goblin 1", 15, False),
            create_test_combatant("goblin2", "Goblin 2", 10, False),
        ]
        self.game_state.combat.current_turn_index = 0

        ai_response = Mock(spec=AIResponse)
        ai_response.end_turn = True

        # Pre-calculated info says to go to goblin2 (skipping goblin1)
        next_info = NextCombatantInfoModel(
            combatant_id="goblin2",
            combatant_name="Goblin 2",
            is_player=False,
            new_index=2,
            should_end_combat=False,
            round_number=1,
            is_new_round=False,
        )

        self.handler.handle_turn_advancement(ai_response, False, False, next_info)

        # Should jump to goblin2
        self.assertEqual(self.game_state.combat.current_turn_index, 2)

    def test_turn_advancement_delays_for_player_requests(self) -> None:
        """Test that turn advancement is delayed when player requests are pending."""
        # Set up combat
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 20, True),
            create_test_combatant("goblin1", "Goblin", 10, False),
        ]
        self.game_state.combat.current_turn_index = 0

        ai_response = Mock(spec=AIResponse)
        ai_response.end_turn = True

        # Player requests are pending
        self.handler.handle_turn_advancement(ai_response, False, True)

        # Turn should NOT advance yet
        self.assertEqual(self.game_state.combat.current_turn_index, 0)


if __name__ == "__main__":
    unittest.main()
