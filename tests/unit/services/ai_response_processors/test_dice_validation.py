"""Tests for dice request validation with empty party."""

import logging
from unittest.mock import Mock

import pytest

from app.models.combat import CombatantModel, CombatStateModel
from app.models.dice import DiceRequestModel
from app.models.game_state import GameStateModel
from app.providers.ai.schemas import AIResponse
from app.services.ai_response_processors.dice_request_handler import DiceRequestHandler


class TestDiceValidation:
    """Test dice request validation with empty party."""

    def test_expand_all_with_empty_party_logs_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that expanding 'all' with empty party logs an error."""
        # Create game state with empty party and active combat
        game_state = GameStateModel(
            campaign_id="test-campaign",
            campaign_name="Test Campaign",
            party={},  # Empty party!
            current_location={
                "name": "Test Location",
                "description": "A test location",
            },
            combat=CombatStateModel(
                is_active=True,
                combatants=[],  # Empty combat - no combatants at all!
            ),
        )

        # Mock repositories and services
        game_state_repo = Mock()
        game_state_repo.get_game_state.return_value = game_state

        character_service = Mock()
        character_service.get_character_name = Mock(return_value="Goblin")
        character_service.find_character_by_name_or_id = Mock(return_value="goblin1")

        dice_service = Mock()
        dice_service.perform_roll = Mock(
            return_value=Mock(total=10, breakdown="1d20 -> [10] = 10", error=None)
        )

        chat_service = Mock()
        event_queue = Mock()

        # Create handler
        handler = DiceRequestHandler(
            game_state_repo=game_state_repo,
            character_service=character_service,
            dice_service=dice_service,
            chat_service=chat_service,
            event_queue=event_queue,
        )

        # Create AI response with 'all' dice request
        ai_response = AIResponse(
            reasoning="Test",
            narrative="Rolling initiative",
            dice_requests=[
                DiceRequestModel(
                    request_id="test-init",
                    character_ids=["all"],
                    type="initiative",
                    dice_formula="1d20",
                    reason="Roll initiative",
                )
            ],
        )

        # Process dice requests
        with caplog.at_level(logging.ERROR):
            player_requests, npc_rolls, needs_rerun = handler.process_dice_requests(
                ai_response=ai_response,
                combat_just_started=False,
            )

        # Verify error was logged
        assert (
            "No valid characters found for 'all' keyword in active combat"
            in caplog.text
        )
        assert "This may indicate an empty party" in caplog.text

        # Verify no rolls were processed (empty combat)
        assert len(player_requests) == 0  # No player requests
        assert not npc_rolls  # No NPC rolls either
        assert not needs_rerun  # Nothing to continue

    def test_expand_all_with_party_succeeds(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that expanding 'all' with party members works correctly."""
        from app.models.character import CharacterInstanceModel

        # Create game state with party and combat
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
            combat=CombatStateModel(
                is_active=True,
                combatants=[
                    CombatantModel(
                        id="hero1",
                        name="Hero",
                        initiative=-1,
                        current_hp=20,
                        max_hp=20,
                        armor_class=16,
                        is_player=True,
                    ),
                    CombatantModel(
                        id="goblin1",
                        name="Goblin",
                        initiative=-1,
                        current_hp=7,
                        max_hp=7,
                        armor_class=15,
                        is_player=False,
                    ),
                ],
            ),
        )

        # Mock repositories
        game_state_repo = Mock()
        game_state_repo.get_game_state.return_value = game_state

        character_service = Mock()
        character_service.find_character_by_name_or_id = Mock(
            side_effect=lambda x: x if x in ["hero1", "goblin1"] else None
        )

        # Create just the character resolver to test the expansion logic
        from app.services.ai_response_processors.dice_request_handler import (
            _CharacterResolver,
        )

        resolver = _CharacterResolver(game_state_repo, character_service)

        # Test expanding 'all' keyword
        with caplog.at_level(logging.INFO):
            resolved_ids = resolver.resolve_character_ids(["all"])

        # Verify both characters were resolved
        assert len(resolved_ids) == 2
        assert "hero1" in resolved_ids
        assert "goblin1" in resolved_ids

        # Verify log message contains the expansion with both combatants
        assert "Expanding 'all' in dice request to ACTIVE combatants:" in caplog.text
        assert "hero1" in caplog.text
        assert "goblin1" in caplog.text
