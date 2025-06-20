"""
Unit tests for combat end validation in state processors.
"""

import logging
import unittest
from unittest.mock import Mock

from app.models.combat import CombatantModel, CombatStateModel
from app.models.events import CombatEndedEvent, GameErrorEvent
from app.models.game_state import GameStateModel
from app.models.updates import CombatEndUpdateModel
from app.services.state_updaters.combat_state_updater import CombatStateUpdater

# Suppress debug logging during tests
logging.getLogger("app.game.state_processors").setLevel(logging.WARNING)


class TestCombatEndValidation(unittest.TestCase):
    """Test combat end validation to prevent ending combat when enemies remain."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.game_state = GameStateModel()
        self.event_queue = Mock()
        self.game_manager = Mock()
        self.game_manager.get_correlation_id.return_value = "test-correlation-123"

    def test_combat_end_allowed_when_no_enemies_remain(self) -> None:
        """Test that combat can end when all enemies are defeated."""
        # Set up combat with only defeated enemies
        self.game_state.combat = CombatStateModel(is_active=True)
        self.game_state.combat.combatants = [
            CombatantModel(
                id="player1",
                name="Hero",
                initiative=10,
                initiative_modifier=2,
                current_hp=15,
                max_hp=20,
                armor_class=14,
                is_player=True,
            ),
            CombatantModel(
                id="enemy1",
                name="Goblin",
                initiative=8,
                initiative_modifier=1,
                current_hp=0,  # Defeated
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        # Attempt to end combat
        update = CombatEndUpdateModel(reason="All enemies defeated")
        CombatStateUpdater.end_combat(
            self.game_state,
            update,
            self.event_queue,
            "test-correlation-123",
        )

        # Verify combat ended
        self.assertFalse(self.game_state.combat.is_active)
        self.event_queue.put_event.assert_called_once()
        event = self.event_queue.put_event.call_args[0][0]
        self.assertIsInstance(event, CombatEndedEvent)
        self.assertEqual(event.reason, "All enemies defeated")

    def test_combat_end_blocked_when_enemies_remain(self) -> None:
        """Test that combat cannot end when active enemies remain."""
        # Set up combat with active enemies
        self.game_state.combat = CombatStateModel(is_active=True)
        self.game_state.combat.combatants = [
            CombatantModel(
                id="player1",
                name="Hero",
                initiative=10,
                initiative_modifier=2,
                current_hp=15,
                max_hp=20,
                armor_class=14,
                is_player=True,
            ),
            CombatantModel(
                id="enemy1",
                name="Goblin Spear",
                initiative=16,
                initiative_modifier=2,
                current_hp=7,  # Still alive
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
            CombatantModel(
                id="enemy2",
                name="Goblin Dagger",
                initiative=14,
                initiative_modifier=2,
                current_hp=0,  # Defeated
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        # Attempt to end combat
        update = CombatEndUpdateModel(reason="All enemies defeated")
        CombatStateUpdater.end_combat(
            self.game_state,
            update,
            self.event_queue,
            "test-correlation-123",
        )

        # Verify combat NOT ended
        self.assertTrue(self.game_state.combat.is_active)
        self.event_queue.put_event.assert_called_once()
        event = self.event_queue.put_event.call_args[0][0]
        self.assertIsInstance(event, GameErrorEvent)
        self.assertEqual(event.error_type, "invalid_combat_end")
        self.assertIn("1 active enemies remain", event.error_message)
        # Context doesn't have active_enemies, just verify the error message contains the info
        self.assertIn("1 active enemies remain", event.error_message)

    def test_combat_end_blocked_with_multiple_active_enemies(self) -> None:
        """Test error message when multiple enemies remain."""
        # Set up combat with multiple active enemies
        self.game_state.combat = CombatStateModel(is_active=True)
        self.game_state.combat.combatants = [
            CombatantModel(
                id="player1",
                name="Hero",
                initiative=10,
                initiative_modifier=2,
                current_hp=15,
                max_hp=20,
                armor_class=14,
                is_player=True,
            ),
            CombatantModel(
                id="enemy1",
                name="Goblin Spear",
                initiative=16,
                initiative_modifier=2,
                current_hp=7,  # Still alive
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
            CombatantModel(
                id="enemy2",
                name="Goblin Dagger",
                initiative=14,
                initiative_modifier=2,
                current_hp=5,  # Still alive
                max_hp=7,
                armor_class=13,
                is_player=False,
            ),
        ]

        # Attempt to end combat
        update = CombatEndUpdateModel(reason="Victory")
        CombatStateUpdater.end_combat(
            self.game_state,
            update,
            self.event_queue,
            "test-correlation-123",
        )

        # Verify combat NOT ended
        self.assertTrue(self.game_state.combat.is_active)
        event = self.event_queue.put_event.call_args[0][0]
        self.assertIsInstance(event, GameErrorEvent)
        self.assertIn("2 active enemies remain", event.error_message)
        # Context doesn't have active_enemies, error message already verified above

    def test_combat_end_when_not_active(self) -> None:
        """Test trying to end combat when it's not active."""
        # Combat not active
        self.game_state.combat = CombatStateModel(is_active=False)

        # Attempt to end combat
        update = CombatEndUpdateModel(reason="Test")
        CombatStateUpdater.end_combat(
            self.game_state,
            update,
            self.event_queue,
            "test-correlation-123",
        )

        # Verify no events emitted
        self.event_queue.put_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
