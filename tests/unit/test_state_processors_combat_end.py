"""
Unit tests for combat end validation in state processors.
"""
import unittest
from unittest.mock import Mock, MagicMock
from app.game.models import GameState, CombatState, Combatant
from app.game.state_processors import end_combat
from app.ai_services.schemas import CombatEndUpdate
from app.events.game_update_events import CombatEndedEvent, GameErrorEvent
import logging

# Suppress debug logging during tests
logging.getLogger('app.game.state_processors').setLevel(logging.WARNING)


class TestCombatEndValidation(unittest.TestCase):
    """Test combat end validation to prevent ending combat when enemies remain."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState()
        self.game_manager = Mock()
        self.game_manager.event_queue = Mock()
        self.game_manager._current_correlation_id = "test-correlation-123"
        
    def test_combat_end_allowed_when_no_enemies_remain(self):
        """Test that combat can end when all enemies are defeated."""
        # Set up combat with only defeated enemies
        self.game_state.combat = CombatState(is_active=True)
        self.game_state.combat.combatants = [
            Combatant(
                id="player1",
                name="Hero",
                initiative=10,
                initiative_modifier=2,
                current_hp=15,
                max_hp=20,
                armor_class=14,
                is_player=True
            ),
            Combatant(
                id="enemy1",
                name="Goblin",
                initiative=8,
                initiative_modifier=1,
                current_hp=0,  # Defeated
                max_hp=7,
                armor_class=13,
                is_player=False
            )
        ]
        
        # Attempt to end combat
        update = CombatEndUpdate(type="combat_end", details={"reason": "All enemies defeated"})
        end_combat(self.game_state, update, self.game_manager)
        
        # Verify combat ended
        self.assertFalse(self.game_state.combat.is_active)
        self.game_manager.event_queue.put_event.assert_called_once()
        event = self.game_manager.event_queue.put_event.call_args[0][0]
        self.assertIsInstance(event, CombatEndedEvent)
        self.assertEqual(event.reason, "All enemies defeated")
    
    def test_combat_end_blocked_when_enemies_remain(self):
        """Test that combat cannot end when active enemies remain."""
        # Set up combat with active enemies
        self.game_state.combat = CombatState(is_active=True)
        self.game_state.combat.combatants = [
            Combatant(
                id="player1",
                name="Hero",
                initiative=10,
                initiative_modifier=2,
                current_hp=15,
                max_hp=20,
                armor_class=14,
                is_player=True
            ),
            Combatant(
                id="enemy1",
                name="Goblin Spear",
                initiative=16,
                initiative_modifier=2,
                current_hp=7,  # Still alive
                max_hp=7,
                armor_class=13,
                is_player=False
            ),
            Combatant(
                id="enemy2",
                name="Goblin Dagger",
                initiative=14,
                initiative_modifier=2,
                current_hp=0,  # Defeated
                max_hp=7,
                armor_class=13,
                is_player=False
            )
        ]
        
        # Attempt to end combat
        update = CombatEndUpdate(type="combat_end", details={"reason": "All enemies defeated"})
        end_combat(self.game_state, update, self.game_manager)
        
        # Verify combat NOT ended
        self.assertTrue(self.game_state.combat.is_active)
        self.game_manager.event_queue.put_event.assert_called_once()
        event = self.game_manager.event_queue.put_event.call_args[0][0]
        self.assertIsInstance(event, GameErrorEvent)
        self.assertEqual(event.error_type, "invalid_combat_end")
        self.assertIn("1 active enemies remain", event.error_message)
        self.assertEqual(len(event.context["active_enemies"]), 1)
        self.assertEqual(event.context["active_enemies"][0]["name"], "Goblin Spear")
    
    def test_combat_end_blocked_with_multiple_active_enemies(self):
        """Test error message when multiple enemies remain."""
        # Set up combat with multiple active enemies
        self.game_state.combat = CombatState(is_active=True)
        self.game_state.combat.combatants = [
            Combatant(
                id="player1",
                name="Hero",
                initiative=10,
                initiative_modifier=2,
                current_hp=15,
                max_hp=20,
                armor_class=14,
                is_player=True
            ),
            Combatant(
                id="enemy1",
                name="Goblin Spear",
                initiative=16,
                initiative_modifier=2,
                current_hp=7,  # Still alive
                max_hp=7,
                armor_class=13,
                is_player=False
            ),
            Combatant(
                id="enemy2",
                name="Goblin Dagger",
                initiative=14,
                initiative_modifier=2,
                current_hp=5,  # Still alive
                max_hp=7,
                armor_class=13,
                is_player=False
            )
        ]
        
        # Attempt to end combat
        update = CombatEndUpdate(type="combat_end", details={"reason": "Victory"})
        end_combat(self.game_state, update, self.game_manager)
        
        # Verify combat NOT ended
        self.assertTrue(self.game_state.combat.is_active)
        event = self.game_manager.event_queue.put_event.call_args[0][0]
        self.assertIsInstance(event, GameErrorEvent)
        self.assertIn("2 active enemies remain", event.error_message)
        self.assertEqual(len(event.context["active_enemies"]), 2)
        
    def test_combat_end_when_not_active(self):
        """Test trying to end combat when it's not active."""
        # Combat not active
        self.game_state.combat = CombatState(is_active=False)
        
        # Attempt to end combat
        update = CombatEndUpdate(type="combat_end", details={"reason": "Test"})
        end_combat(self.game_state, update, self.game_manager)
        
        # Verify no events emitted
        self.game_manager.event_queue.put_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()