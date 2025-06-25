"""Tests for combat validation to prevent combat without party members."""

from unittest.mock import Mock

import pytest

from app.models.character.instance import CharacterInstanceModel
from app.models.combat.combatant import InitialCombatantData
from app.models.combat.state import CombatStateModel
from app.models.events.system import GameErrorEvent
from app.models.game_state.main import GameStateModel
from app.models.updates import CombatStartUpdateModel
from app.services.state_updaters.combat_state_updater import CombatStateUpdater


class TestCombatValidation:
    """Test combat validation prevents starting without party."""

    def test_start_combat_without_party_emits_error(self) -> None:
        """Test that starting combat without party members emits an error event."""
        # Create game state with empty party
        game_state = GameStateModel(
            campaign_id="test-campaign",
            campaign_name="Test Campaign",
            party={},  # Empty party!
            current_location={
                "name": "Test Location",
                "description": "A test location",
            },
            combat=CombatStateModel(is_active=False),
        )

        # Mock event queue
        event_queue = Mock()
        event_queue.put_event = Mock()

        # Create combat update with NPCs
        combat_update = CombatStartUpdateModel(
            combatants=[
                InitialCombatantData(
                    id="goblin1",
                    name="Goblin",
                    hp=7,
                    ac=15,
                    stats={"DEX": 14},
                )
            ]
        )

        # Try to start combat
        CombatStateUpdater.start_combat(
            game_state=game_state,
            update=combat_update,
            event_queue=event_queue,
            correlation_id="test-correlation",
        )

        # Verify combat did not start
        assert not game_state.combat.is_active
        assert len(game_state.combat.combatants) == 0

        # Verify error event was emitted
        event_queue.put_event.assert_called()

        # Get the emitted event
        emitted_event = None
        for call in event_queue.put_event.call_args_list:
            event = call[0][0]
            if isinstance(event, GameErrorEvent):
                emitted_event = event
                break

        assert emitted_event is not None
        assert (
            emitted_event.error_message
            == "Cannot start combat without party members. Please ensure characters are selected for the campaign."
        )
        assert emitted_event.error_type == "no_party_members"
        assert emitted_event.severity == "error"
        assert not emitted_event.recoverable

    def test_start_combat_with_party_succeeds(self) -> None:
        """Test that starting combat with party members succeeds."""
        # Create game state with party
        game_state = GameStateModel(
            campaign_id="test-campaign",
            campaign_name="Test Campaign",
            party={
                "hero1": CharacterInstanceModel(
                    id="hero1",
                    name="Test Hero",
                    template_id="hero-template",
                    campaign_id="test-campaign",
                    level=1,
                    current_hp=20,
                    max_hp=20,
                    conditions=[],
                )
            },
            current_location={
                "name": "Test Location",
                "description": "A test location",
            },
            combat=CombatStateModel(is_active=False),
        )

        # Mock character service
        char_service = Mock()
        char_data = Mock()
        char_data.template.name = "Test Hero"
        char_data.template.base_stats.DEX = 14
        char_data.template.portrait_path = None
        char_service.get_character = Mock(return_value=char_data)

        # Mock event queue
        event_queue = Mock()

        # Create combat update with NPCs
        combat_update = CombatStartUpdateModel(
            combatants=[
                InitialCombatantData(
                    id="goblin1",
                    name="Goblin",
                    hp=7,
                    ac=15,
                    stats={"DEX": 14},
                )
            ]
        )

        # Start combat
        CombatStateUpdater.start_combat(
            game_state=game_state,
            update=combat_update,
            event_queue=event_queue,
            character_service=char_service,
        )

        # Verify combat started
        assert game_state.combat.is_active
        assert len(game_state.combat.combatants) == 2  # 1 hero + 1 goblin

        # Verify both player and NPC are in combat
        combatant_ids = {c.id for c in game_state.combat.combatants}
        assert "hero1" in combatant_ids
        assert "goblin1" in combatant_ids
