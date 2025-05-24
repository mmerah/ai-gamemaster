"""
Unit tests for campaign and character validators.
"""
import pytest
from app.game.validators.campaign_validators import (
    CampaignValidator,
    CharacterValidator,
    GameStateValidator,
    ValidationError,
    validate_campaign_data,
    validate_character_template,
    validate_dice_roll_data
)


class TestCampaignValidator:
    """Test campaign data validation."""
    
    def test_valid_campaign_data(self):
        """Test validation with valid campaign data."""
        campaign_data = {
            "id": "test_campaign_123",
            "name": "Test Adventure",
            "description": "A thrilling adventure awaits!",
            "party_character_ids": ["char_1", "char_2"],
            "difficulty": "normal",
            "starting_level": 3
        }
        
        is_valid, errors = CampaignValidator.validate_campaign_data(campaign_data)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        campaign_data = {
            "name": "Test Campaign"
            # Missing: id, description, party_character_ids
        }
        
        is_valid, errors = CampaignValidator.validate_campaign_data(campaign_data)
        assert not is_valid
        assert len(errors) >= 3
        assert any("Missing required field: id" in error for error in errors)
        assert any("Missing required field: description" in error for error in errors)
        assert any("Missing required field: party_character_ids" in error for error in errors)
    
    def test_empty_required_fields(self):
        """Test validation with empty required fields."""
        campaign_data = {
            "id": "",
            "name": "",
            "description": "",
            "party_character_ids": []
        }
        
        is_valid, errors = CampaignValidator.validate_campaign_data(campaign_data)
        assert not is_valid
        assert len(errors) >= 4
    
    def test_invalid_campaign_id(self):
        """Test validation with invalid campaign ID."""
        campaign_data = {
            "id": "invalid@id!",
            "name": "Test Campaign",
            "description": "Test description",
            "party_character_ids": ["char_1"]
        }
        
        is_valid, errors = CampaignValidator.validate_campaign_data(campaign_data)
        assert not is_valid
        assert any("alphanumeric" in error for error in errors)
    
    def test_invalid_difficulty(self):
        """Test validation with invalid difficulty."""
        campaign_data = {
            "id": "test_campaign",
            "name": "Test Campaign",
            "description": "Test description",
            "party_character_ids": ["char_1"],
            "difficulty": "impossible"
        }
        
        is_valid, errors = CampaignValidator.validate_campaign_data(campaign_data)
        assert not is_valid
        assert any("Difficulty must be one of" in error for error in errors)
    
    def test_invalid_starting_level(self):
        """Test validation with invalid starting level."""
        campaign_data = {
            "id": "test_campaign",
            "name": "Test Campaign",
            "description": "Test description",
            "party_character_ids": ["char_1"],
            "starting_level": 25
        }
        
        is_valid, errors = CampaignValidator.validate_campaign_data(campaign_data)
        assert not is_valid
        assert any("Starting level must be between 1 and 20" in error for error in errors)
    
    def test_campaign_name_length(self):
        """Test campaign name length validation."""
        # Too long name
        long_name = "x" * 101
        campaign_data = {
            "id": "test_campaign",
            "name": long_name,
            "description": "Test description",
            "party_character_ids": ["char_1"]
        }
        
        is_valid, errors = CampaignValidator.validate_campaign_data(campaign_data)
        assert not is_valid
        assert any("name must be 1-100 characters" in error for error in errors)


class TestCharacterValidator:
    """Test character template validation."""
    
    def test_valid_character_template(self):
        """Test validation with valid character template."""
        template_data = {
            "id": "test_character_123",
            "name": "Aragorn",
            "race": "Human",
            "char_class": "Ranger",
            "level": 5,
            "base_stats": {
                "STR": 16, "DEX": 14, "CON": 15,
                "INT": 12, "WIS": 13, "CHA": 10
            },
            "starting_equipment": [
                {"name": "Longsword", "quantity": 1},
                {"name": "Leather Armor", "quantity": 1}
            ],
            "proficiencies": {
                "skills": ["Survival", "Athletics"],
                "saving_throws": ["STR", "DEX"]
            }
        }
        
        is_valid, errors = CharacterValidator.validate_character_template(template_data)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        template_data = {
            "name": "Test Character"
            # Missing: id, race, char_class, base_stats
        }
        
        is_valid, errors = CharacterValidator.validate_character_template(template_data)
        assert not is_valid
        assert len(errors) >= 4
    
    def test_invalid_ability_scores(self):
        """Test validation with invalid ability scores."""
        template_data = {
            "id": "test_char",
            "name": "Test Character",
            "race": "Human",
            "char_class": "Fighter",
            "base_stats": {
                "STR": 35,  # Too high
                "DEX": 0,   # Too low
                "CON": "invalid",  # Not a number
                # Missing: INT, WIS, CHA
            }
        }
        
        is_valid, errors = CharacterValidator.validate_character_template(template_data)
        assert not is_valid
        assert len(errors) >= 5  # High STR, low DEX, invalid CON, missing abilities
    
    def test_invalid_level(self):
        """Test validation with invalid character level."""
        template_data = {
            "id": "test_char",
            "name": "Test Character",
            "race": "Human",
            "char_class": "Fighter",
            "level": 25,  # Too high
            "base_stats": {
                "STR": 16, "DEX": 14, "CON": 15,
                "INT": 12, "WIS": 13, "CHA": 10
            }
        }
        
        is_valid, errors = CharacterValidator.validate_character_template(template_data)
        assert not is_valid
        assert any("level must be between 1 and 20" in error for error in errors)
    
    def test_invalid_equipment_format(self):
        """Test validation with invalid equipment format."""
        template_data = {
            "id": "test_char",
            "name": "Test Character",
            "race": "Human",
            "char_class": "Fighter",
            "base_stats": {
                "STR": 16, "DEX": 14, "CON": 15,
                "INT": 12, "WIS": 13, "CHA": 10
            },
            "starting_equipment": [
                "Invalid equipment format",  # Should be dict
                {"quantity": 1}  # Missing name
            ]
        }
        
        is_valid, errors = CharacterValidator.validate_character_template(template_data)
        assert not is_valid
        assert any("equipment must be a list of item dictionaries" in error for error in errors)
    
    def test_invalid_proficiencies_format(self):
        """Test validation with invalid proficiencies format."""
        template_data = {
            "id": "test_char",
            "name": "Test Character",
            "race": "Human",
            "char_class": "Fighter",
            "base_stats": {
                "STR": 16, "DEX": 14, "CON": 15,
                "INT": 12, "WIS": 13, "CHA": 10
            },
            "proficiencies": "not a dict"  # Should be dictionary
        }
        
        is_valid, errors = CharacterValidator.validate_character_template(template_data)
        assert not is_valid
        assert any("Proficiencies must be a dictionary" in error for error in errors)


class TestGameStateValidator:
    """Test game state validation."""
    
    def test_valid_dice_roll_data(self):
        """Test validation with valid dice roll data."""
        roll_data = {
            "character_id": "test_char",
            "roll_type": "skill_check",
            "dice_formula": "1d20",
            "skill": "perception",
            "dc": 15
        }
        
        is_valid, errors = GameStateValidator.validate_dice_roll_data(roll_data)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_required_dice_fields(self):
        """Test validation with missing required dice roll fields."""
        roll_data = {
            "roll_type": "skill_check"
            # Missing: character_id, dice_formula
        }
        
        is_valid, errors = GameStateValidator.validate_dice_roll_data(roll_data)
        assert not is_valid
        assert len(errors) >= 2
    
    def test_invalid_dice_formula(self):
        """Test validation with invalid dice formula."""
        roll_data = {
            "character_id": "test_char",
            "roll_type": "skill_check",
            "dice_formula": "invalid_formula"
        }
        
        is_valid, errors = GameStateValidator.validate_dice_roll_data(roll_data)
        assert not is_valid
        assert any("Invalid dice formula" in error for error in errors)
    
    def test_invalid_roll_type(self):
        """Test validation with invalid roll type."""
        roll_data = {
            "character_id": "test_char",
            "roll_type": "invalid_roll",
            "dice_formula": "1d20"
        }
        
        is_valid, errors = GameStateValidator.validate_dice_roll_data(roll_data)
        assert not is_valid
        assert any("Invalid roll type" in error for error in errors)
    
    def test_valid_dice_formulas(self):
        """Test validation with various valid dice formulas."""
        valid_formulas = ["1d20", "2d6", "1d8+3", "3d4-1", "1d12 + 5"]
        
        for formula in valid_formulas:
            is_valid = GameStateValidator._is_valid_dice_formula(formula)
            assert is_valid, f"Formula '{formula}' should be valid"
    
    def test_invalid_dice_formulas(self):
        """Test validation with various invalid dice formulas."""
        invalid_formulas = ["", "not_dice", "1x20", "d", "20d"]
        
        for formula in invalid_formulas:
            is_valid = GameStateValidator._is_valid_dice_formula(formula)
            assert not is_valid, f"Formula '{formula}' should be invalid"


class TestConvenienceFunctions:
    """Test convenience validation functions."""
    
    def test_validate_campaign_data_function(self):
        """Test the convenience campaign validation function."""
        valid_data = {
            "id": "test_campaign",
            "name": "Test Campaign",
            "description": "Test description",
            "party_character_ids": ["char_1"]
        }
        
        is_valid, errors = validate_campaign_data(valid_data)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_character_template_function(self):
        """Test the convenience character template validation function."""
        valid_data = {
            "id": "test_char",
            "name": "Test Character",
            "race": "Human",
            "char_class": "Fighter",
            "base_stats": {
                "STR": 16, "DEX": 14, "CON": 15,
                "INT": 12, "WIS": 13, "CHA": 10
            }
        }
        
        is_valid, errors = validate_character_template(valid_data)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_dice_roll_data_function(self):
        """Test the convenience dice roll validation function."""
        valid_data = {
            "character_id": "test_char",
            "roll_type": "skill_check",
            "dice_formula": "1d20"
        }
        
        is_valid, errors = validate_dice_roll_data(valid_data)
        assert is_valid
        assert len(errors) == 0


class TestValidatorEdgeCases:
    """Test edge cases for validators."""
    
    def test_campaign_id_edge_cases(self):
        """Test edge cases for campaign ID validation."""
        # Valid IDs
        assert CampaignValidator._is_valid_id("campaign_123")
        assert CampaignValidator._is_valid_id("test-campaign-1")
        assert CampaignValidator._is_valid_id("c")
        
        # Invalid IDs
        assert not CampaignValidator._is_valid_id("")
        assert not CampaignValidator._is_valid_id("campaign with spaces")
        assert not CampaignValidator._is_valid_id("campaign@special!")
        assert not CampaignValidator._is_valid_id("x" * 51)  # Too long
    
    def test_character_name_edge_cases(self):
        """Test edge cases for character name validation."""
        # Valid names
        assert CharacterValidator._is_valid_name("Aragorn")
        assert CharacterValidator._is_valid_name("Sir Galahad the Bold")
        assert CharacterValidator._is_valid_name("X")
        
        # Invalid names
        assert not CharacterValidator._is_valid_name("")
        assert not CharacterValidator._is_valid_name("   ")  # Only whitespace
        assert not CharacterValidator._is_valid_name("x" * 51)  # Too long
        assert not CharacterValidator._is_valid_name(123)  # Not a string
    
    def test_level_validation_edge_cases(self):
        """Test edge cases for level validation."""
        # Valid levels
        assert CampaignValidator._is_valid_level(1)
        assert CampaignValidator._is_valid_level(20)
        assert CampaignValidator._is_valid_level("5")  # String number
        
        # Invalid levels
        assert not CampaignValidator._is_valid_level(0)
        assert not CampaignValidator._is_valid_level(21)
        assert not CampaignValidator._is_valid_level(-1)
        assert not CampaignValidator._is_valid_level("not_a_number")
        assert not CampaignValidator._is_valid_level(None)
    
    def test_party_list_validation(self):
        """Test party character IDs list validation."""
        # Valid party lists
        assert CampaignValidator._is_valid_party_list(["char1", "char2"])
        assert CampaignValidator._is_valid_party_list(["single_char"])
        
        # Invalid party lists
        assert not CampaignValidator._is_valid_party_list([])  # Empty
        assert not CampaignValidator._is_valid_party_list("not_a_list")
        assert not CampaignValidator._is_valid_party_list([123, "char2"])  # Non-string
        assert not CampaignValidator._is_valid_party_list(["", "char2"])  # Empty string
        assert not CampaignValidator._is_valid_party_list(["  ", "char2"])  # Only whitespace
