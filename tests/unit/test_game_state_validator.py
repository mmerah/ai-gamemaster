"""
Unit tests for GameStateModel model validator that converts dicts to Pydantic models.
"""

import unittest
from datetime import datetime, timezone

from app.models import (
    ChatMessageModel,
    DiceRequestModel,
    GameStateModel,
)


class TestGameStateValidator(unittest.TestCase):
    """Test GameStateModel model validator for dict to Pydantic model conversion."""

    def test_chat_history_dict_to_chatmessage_conversion(self) -> None:
        """Test that chat_history dicts are converted to ChatMessage objects."""
        # Create GameStateModel with dict chat messages
        game_state_data = {
            "chat_history": [
                {
                    "role": "assistant",
                    "content": "Welcome to the adventure!",
                    "gm_thought": "Setting the scene",
                },
                {"role": "user", "content": "I look around", "is_dice_result": False},
            ]
        }

        game_state = GameStateModel(**game_state_data)

        # Verify conversion
        self.assertEqual(len(game_state.chat_history), 2)

        # Check first message
        msg1 = game_state.chat_history[0]
        self.assertIsInstance(msg1, ChatMessageModel)
        self.assertEqual(msg1.role, "assistant")
        self.assertEqual(msg1.content, "Welcome to the adventure!")
        self.assertEqual(msg1.gm_thought, "Setting the scene")
        self.assertIsNotNone(msg1.id)  # Auto-generated
        self.assertIsNotNone(msg1.timestamp)  # Auto-generated

        # Check second message
        msg2 = game_state.chat_history[1]
        self.assertIsInstance(msg2, ChatMessageModel)
        self.assertEqual(msg2.role, "user")
        self.assertEqual(msg2.content, "I look around")
        self.assertEqual(msg2.is_dice_result, False)

    def test_pending_dice_requests_dict_to_dicerequest_conversion(self) -> None:
        """Test that pending_player_dice_requests dicts are converted to DiceRequestModel objects."""
        game_state_data = {
            "pending_player_dice_requests": [
                {
                    "request_id": "req_1",
                    "character_ids": ["char1"],
                    "type": "attack",
                    "dice_formula": "1d20+5",
                    "reason": "Sword attack",
                },
                {
                    "request_id": "req_2",
                    "character_ids": ["char2"],
                    "type": "ability_check",
                    "dice_formula": "1d20+3",
                    "reason": "Perception check",
                    "ability": "wisdom",
                    "dc": 15,
                },
            ]
        }

        game_state = GameStateModel(**game_state_data)

        # Verify conversion
        self.assertEqual(len(game_state.pending_player_dice_requests), 2)

        # Check first request
        req1 = game_state.pending_player_dice_requests[0]
        self.assertIsInstance(req1, DiceRequestModel)
        self.assertEqual(req1.request_id, "req_1")
        self.assertEqual(req1.character_ids, ["char1"])
        self.assertEqual(req1.type, "attack")
        self.assertEqual(req1.dice_formula, "1d20+5")

        # Check second request
        req2 = game_state.pending_player_dice_requests[1]
        self.assertIsInstance(req2, DiceRequestModel)
        self.assertEqual(req2.ability, "wisdom")
        self.assertEqual(req2.dc, 15)

    def test_mixed_types_preservation(self) -> None:
        """Test that already-converted Pydantic objects are preserved."""
        # Create proper objects
        chat_msg = ChatMessageModel(
            id="test_msg",
            role="assistant",
            content="Test",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        dice_req = DiceRequestModel(
            request_id="test_req",
            character_ids=["char1"],
            type="attack",
            dice_formula="1d20",
            reason="Test",
        )

        game_state_data = {
            "chat_history": [
                chat_msg,  # Already a ChatMessage
                {"role": "user", "content": "Dict message"},  # Dict to convert
            ],
            "pending_player_dice_requests": [
                dice_req,  # Already a DiceRequest
                {
                    "request_id": "req2",
                    "character_ids": ["char2"],
                    "type": "save",
                    "dice_formula": "1d20",
                    "reason": "Test",
                },
            ],
        }

        game_state = GameStateModel(**game_state_data)

        # Verify both are proper types
        self.assertIsInstance(game_state.chat_history[0], ChatMessageModel)
        self.assertIsInstance(game_state.chat_history[1], ChatMessageModel)
        self.assertEqual(game_state.chat_history[0].id, "test_msg")  # Preserved
        self.assertEqual(
            game_state.chat_history[1].content, "Dict message"
        )  # Converted

        self.assertIsInstance(
            game_state.pending_player_dice_requests[0], DiceRequestModel
        )
        self.assertIsInstance(
            game_state.pending_player_dice_requests[1], DiceRequestModel
        )

    def test_empty_lists_handling(self) -> None:
        """Test that empty lists work correctly."""
        game_state_data = {
            "chat_history": [],
            "pending_player_dice_requests": [],
            "combat": {"combatants": []},
        }

        game_state = GameStateModel(**game_state_data)

        self.assertEqual(len(game_state.chat_history), 0)
        self.assertEqual(len(game_state.pending_player_dice_requests), 0)
        self.assertEqual(len(game_state.combat.combatants), 0)

    def test_missing_required_fields_get_defaults(self) -> None:
        """Test that missing required fields in dicts get appropriate defaults."""
        game_state_data = {
            "chat_history": [
                {
                    # Missing id and timestamp
                    "role": "assistant",
                    "content": "Hello",
                }
            ]
        }

        game_state = GameStateModel(**game_state_data)

        # Check chat message got defaults
        msg = game_state.chat_history[0]
        self.assertIsNotNone(msg.id)
        self.assertIsNotNone(msg.timestamp)
        self.assertTrue(msg.id.startswith("msg_"))


if __name__ == "__main__":
    unittest.main()
