"""
Tests for the RobustJsonOutputParser.
"""

import pytest
from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException

from app.utils.robust_json_parser import RobustJsonOutputParser


class SampleResponse(BaseModel):
    """Sample Pydantic model for testing."""
    narrative: str = Field(description="The narrative text")
    end_turn: bool = Field(description="Whether to end turn")
    dice_requests: list = Field(default_factory=list)


class TestRobustJsonOutputParser:
    """Test cases for RobustJsonOutputParser."""
    
    def test_parse_clean_json(self):
        """Test parsing clean, well-formatted JSON."""
        parser = RobustJsonOutputParser()
        text = '{"narrative": "You enter the dungeon", "end_turn": false, "dice_requests": []}'
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == "You enter the dungeon"
        assert result["end_turn"] is False
        assert result["dice_requests"] == []
    
    def test_parse_json_with_trailing_commas(self):
        """Test parsing JSON with trailing commas."""
        parser = RobustJsonOutputParser()
        text = '{"narrative": "Test", "end_turn": true, "dice_requests": [],}'
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == "Test"
        assert result["end_turn"] is True
    
    def test_parse_json_in_markdown_block(self):
        """Test extracting JSON from markdown code blocks."""
        parser = RobustJsonOutputParser()
        text = """
        Here is the response:
        
        ```json
        {
            "narrative": "The goblin attacks!",
            "end_turn": false,
            "dice_requests": ["attack"]
        }
        ```
        
        That's the action.
        """
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == "The goblin attacks!"
        assert result["end_turn"] is False
        assert result["dice_requests"] == ["attack"]
    
    def test_parse_json_with_surrounding_text(self):
        """Test extracting JSON with surrounding text."""
        parser = RobustJsonOutputParser()
        text = """
        Let me process this action for you.
        {"narrative": "You swing your sword", "end_turn": true, "dice_requests": []}
        The action has been processed.
        """
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == "You swing your sword"
        assert result["end_turn"] is True
    
    def test_parse_json_with_nested_objects(self):
        """Test parsing JSON with nested objects."""
        parser = RobustJsonOutputParser()
        text = '''{
            "narrative": "Combat continues",
            "end_turn": false,
            "dice_requests": [],
            "game_state_updates": [
                {"type": "hp_change", "character_id": "123", "amount": -5}
            ]
        }'''
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == "Combat continues"
        assert len(result["game_state_updates"]) == 1
        assert result["game_state_updates"][0]["type"] == "hp_change"
    
    def test_parse_multiline_json_with_commas(self):
        """Test parsing multiline JSON with trailing commas."""
        parser = RobustJsonOutputParser()
        text = '''{
            "narrative": "Test narrative",
            "end_turn": false,
            "dice_requests": [
                "attack",
                "damage",
            ],
        }'''
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["dice_requests"] == ["attack", "damage"]
    
    def test_parse_with_pydantic_validation(self):
        """Test parsing with Pydantic model validation."""
        parser = RobustJsonOutputParser(pydantic_object=SampleResponse)
        text = '{"narrative": "Valid response", "end_turn": true}'
        
        result = parser.parse_with_fallbacks(text)
        
        # The parser returns dict, not Pydantic model
        assert result["narrative"] == "Valid response"
        assert result["end_turn"] is True
        assert result.get("dice_requests") is None or result["dice_requests"] == []
    
    def test_parse_markdown_without_json_label(self):
        """Test parsing markdown code block without 'json' label."""
        parser = RobustJsonOutputParser()
        text = """
        ```
        {
            "narrative": "Action taken",
            "end_turn": false,
            "dice_requests": []
        }
        ```
        """
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == "Action taken"
    
    def test_parse_with_balanced_braces(self):
        """Test extraction using balanced brace matching."""
        parser = RobustJsonOutputParser()
        text = 'Some text before {"narrative": "Nested {braces} work", "end_turn": true} and after'
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == "Nested {braces} work"
        assert result["end_turn"] is True
    
    def test_parse_failure_no_json(self):
        """Test that parser raises exception when no JSON found."""
        parser = RobustJsonOutputParser()
        text = "This is just plain text with no JSON"
        
        with pytest.raises(OutputParserException, match="Failed to parse JSON"):
            parser.parse_with_fallbacks(text)
    
    def test_parse_failure_invalid_json(self):
        """Test that parser raises exception for truly unparseable content."""
        parser = RobustJsonOutputParser()
        # Use a string that looks like JSON but has syntax errors throughout
        text = '{invalid json with : no quotes and bad , , syntax throughout}'
        
        with pytest.raises(OutputParserException, match="Failed to parse JSON"):
            parser.parse_with_fallbacks(text)
    
    def test_clean_json_string(self):
        """Test the JSON cleaning functionality."""
        parser = RobustJsonOutputParser()
        
        # Test trailing comma in object
        cleaned = parser._clean_json_string('{"a": 1, "b": 2,}')
        assert cleaned == '{"a": 1, "b": 2}'
        
        # Test trailing comma in array
        cleaned = parser._clean_json_string('["a", "b", "c",]')
        assert cleaned == '["a", "b", "c"]'
        
        # Test multiline with trailing commas
        cleaned = parser._clean_json_string('''
        {
            "items": [
                1,
                2,
            ],
        }
        ''')
        assert ',\n]' not in cleaned
        assert ',\n}' not in cleaned
    
    def test_empty_json_object(self):
        """Test parsing empty JSON object."""
        parser = RobustJsonOutputParser()
        text = '{}'
        
        result = parser.parse_with_fallbacks(text)
        
        assert result == {}
    
    def test_json_with_special_characters(self):
        """Test parsing JSON with special characters in strings."""
        parser = RobustJsonOutputParser()
        text = '{"narrative": "The goblin says: \\"Hello, adventurer!\\"", "end_turn": false}'
        
        result = parser.parse_with_fallbacks(text)
        
        assert result["narrative"] == 'The goblin says: "Hello, adventurer!"'