"""
Unit tests for AI service schema validation.
"""
import unittest
from app.ai_services.schemas import AIResponse, DiceRequest, HPChangeUpdate


class TestAIServiceSchemas(unittest.TestCase):
    """Test AI service schema validation."""
    
    def test_ai_response_schema(self):
        """Test AIResponse schema validation."""
        # Valid response
        response_data = {
            "reasoning": "Test reasoning",
            "narrative": "Test narrative",
            "dice_requests": [],
            "location_update": None,
            "game_state_updates": [],
            "end_turn": None
        }
        
        response = AIResponse(**response_data)
        self.assertEqual(response.reasoning, "Test reasoning")
        self.assertEqual(response.narrative, "Test narrative")
        self.assertEqual(len(response.dice_requests), 0)
    
    def test_dice_request_schema(self):
        """Test DiceRequest schema validation."""
        dice_data = {
            "request_id": "test_roll_1",
            "character_ids": ["char1"],
            "type": "skill_check",
            "dice_formula": "1d20",
            "reason": "Test roll",
            "skill": "Perception",
            "dc": 15
        }
        
        dice_request = DiceRequest(**dice_data)
        self.assertEqual(dice_request.request_id, "test_roll_1")
        self.assertEqual(dice_request.type, "skill_check")
        self.assertEqual(dice_request.skill, "Perception")
        self.assertEqual(dice_request.dc, 15)
    
    def test_game_state_update_schema(self):
        """Test GameStateUpdate schema validation."""
        update_data = {
            "type": "hp_change",
            "character_id": "char1",
            "value": -5,
            "details": {"source": "Goblin attack"}
        }
        
        update = HPChangeUpdate(**update_data)
        self.assertEqual(update.type, "hp_change")
        self.assertEqual(update.character_id, "char1")
        self.assertEqual(update.value, -5)


if __name__ == '__main__':
    unittest.main()
