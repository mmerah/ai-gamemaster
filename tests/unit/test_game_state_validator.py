"""
Unit tests for GameStateModel model validator that converts dicts to Pydantic models.
"""
import unittest
from datetime import datetime, timezone
from app.game.unified_models import GameStateModel, ChatMessage, DiceRequest, MonsterBaseStats


class TestGameStateValidator(unittest.TestCase):
    """Test GameStateModel model validator for dict to Pydantic model conversion."""
    
    def test_chat_history_dict_to_chatmessage_conversion(self):
        """Test that chat_history dicts are converted to ChatMessage objects."""
        # Create GameStateModel with dict chat messages
        game_state_data = {
            "chat_history": [
                {
                    "role": "assistant",
                    "content": "Welcome to the adventure!",
                    "gm_thought": "Setting the scene"
                },
                {
                    "role": "user", 
                    "content": "I look around",
                    "is_dice_result": False
                }
            ]
        }
        
        game_state = GameStateModel(**game_state_data)
        
        # Verify conversion
        self.assertEqual(len(game_state.chat_history), 2)
        
        # Check first message
        msg1 = game_state.chat_history[0]
        self.assertIsInstance(msg1, ChatMessage)
        self.assertEqual(msg1.role, "assistant")
        self.assertEqual(msg1.content, "Welcome to the adventure!")
        self.assertEqual(msg1.gm_thought, "Setting the scene")
        self.assertIsNotNone(msg1.id)  # Auto-generated
        self.assertIsNotNone(msg1.timestamp)  # Auto-generated
        
        # Check second message
        msg2 = game_state.chat_history[1]
        self.assertIsInstance(msg2, ChatMessage)
        self.assertEqual(msg2.role, "user")
        self.assertEqual(msg2.content, "I look around")
        self.assertEqual(msg2.is_dice_result, False)
    
    def test_pending_dice_requests_dict_to_dicerequest_conversion(self):
        """Test that pending_player_dice_requests dicts are converted to DiceRequest objects."""
        game_state_data = {
            "pending_player_dice_requests": [
                {
                    "request_id": "req_1",
                    "character_ids": ["char1"],
                    "type": "attack",
                    "dice_formula": "1d20+5",
                    "reason": "Sword attack"
                },
                {
                    "request_id": "req_2",
                    "character_ids": ["char2"],
                    "type": "ability_check",
                    "dice_formula": "1d20+3",
                    "reason": "Perception check",
                    "ability": "wisdom",
                    "dc": 15
                }
            ]
        }
        
        game_state = GameStateModel(**game_state_data)
        
        # Verify conversion
        self.assertEqual(len(game_state.pending_player_dice_requests), 2)
        
        # Check first request
        req1 = game_state.pending_player_dice_requests[0]
        self.assertIsInstance(req1, DiceRequest)
        self.assertEqual(req1.request_id, "req_1")
        self.assertEqual(req1.character_ids, ["char1"])
        self.assertEqual(req1.type, "attack")
        self.assertEqual(req1.dice_formula, "1d20+5")
        
        # Check second request
        req2 = game_state.pending_player_dice_requests[1]
        self.assertIsInstance(req2, DiceRequest)
        self.assertEqual(req2.ability, "wisdom")
        self.assertEqual(req2.dc, 15)
    
    def test_monster_stats_dict_to_monsterbasestats_conversion(self):
        """Test that combat.monster_stats dicts are converted to MonsterBaseStats objects."""
        game_state_data = {
            "combat": {
                "is_active": True,
                "combatants": [],
                "monster_stats": {
                    "goblin1": {
                        "name": "Goblin",
                        "initial_hp": 7,
                        "ac": 13,
                        "stats": {"STR": 8, "DEX": 14},
                        "abilities": ["nimble_escape"]
                    },
                    "orc1": {
                        # Missing optional fields
                        "name": "Orc",
                        "initial_hp": 15,
                        "ac": 16
                    }
                }
            }
        }
        
        game_state = GameStateModel(**game_state_data)
        
        # Verify conversion
        self.assertEqual(len(game_state.combat.monster_stats), 2)
        
        # Check goblin
        goblin = game_state.combat.monster_stats["goblin1"]
        self.assertIsInstance(goblin, MonsterBaseStats)
        self.assertEqual(goblin.name, "Goblin")
        self.assertEqual(goblin.initial_hp, 7)
        self.assertEqual(goblin.ac, 13)
        self.assertEqual(goblin.stats["STR"], 8)
        self.assertEqual(goblin.abilities, ["nimble_escape"])
        
        # Check orc with defaults
        orc = game_state.combat.monster_stats["orc1"]
        self.assertIsInstance(orc, MonsterBaseStats)
        self.assertEqual(orc.name, "Orc")
        self.assertEqual(orc.initial_hp, 15)
        self.assertEqual(orc.ac, 16)
    
    def test_mixed_types_preservation(self):
        """Test that already-converted Pydantic objects are preserved."""
        # Create proper objects
        chat_msg = ChatMessage(
            id="test_msg",
            role="assistant",
            content="Test",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        dice_req = DiceRequest(
            request_id="test_req",
            character_ids=["char1"],
            type="attack",
            dice_formula="1d20",
            reason="Test"
        )
        
        game_state_data = {
            "chat_history": [
                chat_msg,  # Already a ChatMessage
                {"role": "user", "content": "Dict message"}  # Dict to convert
            ],
            "pending_player_dice_requests": [
                dice_req,  # Already a DiceRequest
                {"request_id": "req2", "character_ids": ["char2"], "type": "save", "dice_formula": "1d20", "reason": "Test"}
            ]
        }
        
        game_state = GameStateModel(**game_state_data)
        
        # Verify both are proper types
        self.assertIsInstance(game_state.chat_history[0], ChatMessage)
        self.assertIsInstance(game_state.chat_history[1], ChatMessage)
        self.assertEqual(game_state.chat_history[0].id, "test_msg")  # Preserved
        self.assertEqual(game_state.chat_history[1].content, "Dict message")  # Converted
        
        self.assertIsInstance(game_state.pending_player_dice_requests[0], DiceRequest)
        self.assertIsInstance(game_state.pending_player_dice_requests[1], DiceRequest)
    
    def test_empty_lists_handling(self):
        """Test that empty lists work correctly."""
        game_state_data = {
            "chat_history": [],
            "pending_player_dice_requests": [],
            "combat": {
                "monster_stats": {}
            }
        }
        
        game_state = GameStateModel(**game_state_data)
        
        self.assertEqual(len(game_state.chat_history), 0)
        self.assertEqual(len(game_state.pending_player_dice_requests), 0)
        self.assertEqual(len(game_state.combat.monster_stats), 0)
    
    def test_missing_required_fields_get_defaults(self):
        """Test that missing required fields in dicts get appropriate defaults."""
        game_state_data = {
            "chat_history": [
                {
                    # Missing id and timestamp
                    "role": "assistant",
                    "content": "Hello"
                }
            ],
            "combat": {
                "monster_stats": {
                    "monster1": {
                        # Missing name, initial_hp, ac (will use defaults)
                    }
                }
            }
        }
        
        game_state = GameStateModel(**game_state_data)
        
        # Check chat message got defaults
        msg = game_state.chat_history[0]
        self.assertIsNotNone(msg.id)
        self.assertIsNotNone(msg.timestamp)
        self.assertTrue(msg.id.startswith("msg_"))
        
        # Check monster stats got defaults
        monster = game_state.combat.monster_stats["monster1"]
        self.assertEqual(monster.name, "monster1")  # Uses key as name
        self.assertEqual(monster.initial_hp, 1)  # Default
        self.assertEqual(monster.ac, 10)  # Default


if __name__ == '__main__':
    unittest.main()