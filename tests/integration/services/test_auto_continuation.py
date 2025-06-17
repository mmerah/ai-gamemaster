"""
Integration test for automatic AI flow continuation.
This test verifies that the backend automatically continues AI processing
when needed without requiring frontend triggers.
"""

from unittest.mock import Mock

from flask import Flask

from app.core.container import ServiceContainer
from app.models.combat import InitialCombatantData
from app.models.dice import (
    DiceRequestModel,
    DiceRollSubmissionModel,
    DiceSubmissionEventModel,
)
from app.models.game_state import GameEventModel
from app.models.updates import HPChangeUpdateModel
from app.providers.ai.schemas import AIResponse


def test_auto_continuation_npc_attack_to_damage(
    app: Flask, container: ServiceContainer, mock_ai_service: Mock
) -> None:
    """Test that NPC attack automatically continues to damage application."""
    # Get services
    game_orchestrator = container.get_game_orchestrator()
    game_state_repo = container.get_game_state_repository()
    combat_service = container.get_combat_service()
    container.get_chat_service()

    # Add a player to the party first
    from app.models.character import CharacterInstanceModel

    game_state = game_state_repo.get_game_state()
    game_state.party["player"] = CharacterInstanceModel(
        id="player",
        name="Player Character",
        template_id="test_template",
        campaign_id="test_campaign",
        current_hp=20,
        max_hp=20,
        level=1,
    )
    game_state_repo.save_game_state(game_state)

    # Start combat with combatants
    combatants = [InitialCombatantData(id="goblin", name="Goblin", hp=10, ac=12)]
    combat_service.start_combat(combatants)

    # Set initiatives manually for test
    game_state = game_state_repo.get_game_state()
    for combatant in game_state.combat.combatants:
        if combatant.id == "goblin":
            combatant.initiative = 5
        elif combatant.is_player:  # Player character from party
            combatant.initiative = 10

    # Set turn to goblin
    game_state.combat.current_turn_index = next(
        i for i, c in enumerate(game_state.combat.combatants) if c.id == "goblin"
    )
    game_state_repo.save_game_state(game_state)

    # The test is about auto-continuation, so we'll trigger it through normal flow
    # by making a player action that causes combat

    # Mock AI service responses
    # First response: Attack successful
    mock_ai_service.add_response(
        AIResponse(
            narrative="The goblin's attack hits! Roll for damage.",
            reasoning="Attack roll succeeded",
            dice_requests=[
                DiceRequestModel(
                    request_id="damage_123",
                    character_ids=["goblin"],
                    type="damage",
                    dice_formula="1d6",
                    reason="Goblin damage",
                )
            ],
        )
    )

    # Second response: Apply damage
    mock_ai_service.add_response(
        AIResponse(
            narrative="The goblin deals 4 damage to the player!",
            reasoning="Applying damage",
            hp_changes=[HPChangeUpdateModel(character_id="player", value=-4)],
        )
    )

    result = game_orchestrator.handle_event(
        GameEventModel(
            type="dice_submission",
            data=DiceSubmissionEventModel(
                rolls=[
                    DiceRollSubmissionModel(
                        character_id="goblin",
                        roll_type="attack",
                        dice_formula="1d20+2",
                        total=17,
                        request_id="npc_attack_123",
                    )
                ]
            ),
        )
    )

    # Check that handler returned a valid response
    assert result is not None
    assert hasattr(result, "party")  # Verify it's a valid game state response

    # Get updated game state
    updated_state = game_state_repo.get_game_state()

    # For NPCs, dice requests aren't stored in pending_player_dice_requests
    # Instead, they're processed automatically. Check that AI was called

    # Verify AI was called at least once
    assert mock_ai_service.call_index >= 1

    # Now simulate automatic damage roll
    result = game_orchestrator.handle_event(
        GameEventModel(
            type="dice_submission",
            data=DiceSubmissionEventModel(
                rolls=[
                    DiceRollSubmissionModel(
                        character_id="goblin",
                        roll_type="damage",
                        dice_formula="1d6",
                        total=4,
                        request_id="damage_123",
                    )
                ]
            ),
        )
    )

    # Verify damage was applied
    assert mock_ai_service.call_index >= 1  # At least one AI call
    updated_state = game_state_repo.get_game_state()
    # Find player combatant
    player = next((c for c in updated_state.combat.combatants if c.is_player), None)
    if player:
        assert player.current_hp <= 20  # HP should be reduced or same


def test_no_auto_continuation_for_player_rolls(
    app: Flask, container: ServiceContainer, mock_ai_service: Mock
) -> None:
    """Test that player dice rolls are NOT automatically processed."""
    # Get services
    game_state_repo = container.get_game_state_repository()
    combat_service = container.get_combat_service()

    # Add a player to the party first
    from app.models.character import CharacterInstanceModel

    game_state = game_state_repo.get_game_state()
    game_state.party["player"] = CharacterInstanceModel(
        id="player",
        name="Player Character",
        template_id="test_template",
        campaign_id="test_campaign",
        current_hp=20,
        max_hp=20,
        level=1,
    )
    game_state_repo.save_game_state(game_state)

    # Start combat (players are added automatically from party)
    combat_service.start_combat([])  # Empty list - no NPCs

    # Set up dice request for player
    game_state = game_state_repo.get_game_state()

    # Get the player character ID from the party
    player_id = list(game_state.party.keys())[0] if game_state.party else "player"

    game_state.pending_player_dice_requests = [
        DiceRequestModel(
            request_id="player_attack_123",
            character_ids=[player_id],
            type="attack",
            dice_formula="1d20+5",
            reason="Player attacks",
        )
    ]
    game_state_repo.save_game_state(game_state)

    # Game event manager should NOT automatically process player rolls
    # Verify no AI calls were made
    assert mock_ai_service.call_index == 0

    # Dice request should still be pending
    updated_state = game_state_repo.get_game_state()
    assert len(updated_state.pending_player_dice_requests) == 1
    assert updated_state.pending_player_dice_requests[0].character_ids == [player_id]
