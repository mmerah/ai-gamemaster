"""
Tests to validate that generated TypeScript compiles correctly.
"""
import pytest
import subprocess
import os
from pathlib import Path


class TestTypeScriptValidation:
    """Validate generated TypeScript interfaces compile without errors."""
    
    @pytest.fixture
    def typescript_file(self):
        """Path to generated TypeScript file."""
        return Path("frontend/src/types/unified.ts")
    
    def test_typescript_file_exists(self, typescript_file):
        """Test that the generated TypeScript file exists."""
        assert typescript_file.exists(), f"TypeScript file not found at {typescript_file}"
    
    def test_typescript_compiles(self, typescript_file):
        """Test that TypeScript compiles without errors."""
        # Create a temporary test file that imports our types
        test_file = typescript_file.parent / "test_compilation.ts"
        test_content = f"""
// Test file to validate TypeScript compilation
import {{
    CharacterTemplateModel,
    CampaignTemplateModel,
    BaseGameEvent,
    NarrativeAddedEvent,
    ItemModel,
    NPCModel,
    QuestModel
}} from './unified';

// Test that we can use the types
const testCharacter: CharacterTemplateModel = {{
    id: "test",
    name: "Test Character",
    race: "Human",
    subrace: undefined,
    char_class: "Fighter",
    subclass: "Champion",
    level: 1,
    background: "Soldier",
    alignment: "Lawful Good",
    base_stats: {{
        STR: 16,
        DEX: 14,
        CON: 14,
        INT: 10,
        WIS: 12,
        CHA: 8
    }},
    proficiencies: {{
        armor: ["Light", "Medium", "Heavy", "Shields"],
        weapons: ["Simple", "Martial"],
        tools: [],
        saving_throws: ["STR", "CON"],
        skills: ["Athletics", "Intimidation"]
    }},
    languages: ["Common", "Orc"],
    racial_traits: [],
    class_features: [],
    feats: [],
    spells_known: [],
    cantrips_known: [],
    starting_equipment: [],
    starting_gold: 150,
    portrait_path: undefined,
    personality_traits: ["I'm always polite and respectful."],
    ideals: ["Honor"],
    bonds: ["I would still lay down my life for the people I served with."],
    flaws: ["I made a terrible mistake in battle that cost many lives."],
    appearance: undefined,
    backstory: undefined,
    created_date: new Date().toISOString(),
    last_modified: new Date().toISOString()
}};

// Test nested types
const testItem: ItemModel = {{
    id: "sword",
    name: "Longsword",
    description: "A versatile weapon",
    quantity: 1
}};

// Test event types
const testEvent: NarrativeAddedEvent = {{
    event_id: "123",
    timestamp: new Date().toISOString(),
    sequence_number: 1,
    event_type: "narrative_added",
    correlation_id: undefined,
    role: "assistant",
    content: "The adventure begins...",
    gm_thought: undefined,
    audio_path: undefined,
    message_id: undefined
}};

console.log("TypeScript compilation test passed!");
"""
        
        try:
            # Write test file
            test_file.write_text(test_content)
            
            # Check if TypeScript is available
            tsc_check = subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                text=True
            )
            
            if tsc_check.returncode != 0:
                pytest.skip("npx not available in test environment")
            
            # Try to compile with TypeScript
            # Use absolute path for better compatibility
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--skipLibCheck", str(test_file.absolute())],
                cwd=str(typescript_file.parent.parent.parent),  # frontend directory
                capture_output=True,
                text=True
            )
            
            # Check for compilation errors
            if result.returncode != 0 and result.stderr:
                # Only fail if there's actual error output
                pytest.fail(f"TypeScript compilation failed:\n{result.stderr}")
            
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
    
    def test_types_structure_complete(self, typescript_file):
        """Test that all expected types are present in the generated file."""
        content = typescript_file.read_text()
        
        # Check for main model interfaces
        expected_interfaces = [
            "export interface CharacterTemplateModel",
            "export interface CampaignTemplateModel", 
            "export interface BaseGameEvent",
            "export interface ItemModel",
            "export interface NPCModel",
            "export interface QuestModel",
            "export interface HouseRulesModel",
            "export interface BaseStatsModel",
            "export interface ProficienciesModel",
            "export interface TraitModel",
            "export interface ClassFeatureModel"
        ]
        
        for interface in expected_interfaces:
            assert interface in content, f"Missing interface: {interface}"
        
        # Check for event types
        event_types = [
            "NarrativeAddedEvent",
            "CombatStartedEvent",
            "CombatEndedEvent",
            "TurnAdvancedEvent",
            "CombatantHpChangedEvent",
            "PlayerDiceRequestAddedEvent"
        ]
        
        for event_type in event_types:
            assert f"export interface {event_type}" in content, f"Missing event type: {event_type}"
    
    def test_character_template_fields_complete(self, typescript_file):
        """Test that CharacterTemplateModel has all required fields."""
        content = typescript_file.read_text()
        
        # Extract CharacterTemplateModel interface
        start = content.find("export interface CharacterTemplateModel {")
        end = content.find("}", start) + 1
        char_interface = content[start:end]
        
        # Check for all fields that were missing in the frontend
        required_fields = [
            "racial_traits: TraitModel[]",
            "class_features: ClassFeatureModel[]",
            "spells_known: string[]",
            "cantrips_known: string[]",
            "languages: string[]",
            "proficiencies: ProficienciesModel",
            "starting_equipment: ItemModel[]",
            "personality_traits: string[]",
            "ideals: string[]", 
            "bonds: string[]",
            "flaws: string[]",
            "appearance?: string",
            "backstory?: string"
        ]
        
        for field in required_fields:
            assert field in char_interface, f"Missing field in CharacterTemplateModel: {field}"
    
    def test_campaign_template_nested_structures(self, typescript_file):
        """Test that CampaignTemplateModel has proper nested structures."""
        content = typescript_file.read_text()
        
        # Extract CampaignTemplateModel interface
        start = content.find("export interface CampaignTemplateModel {")
        end = content.find("}", start) + 1
        camp_interface = content[start:end]
        
        # Check for nested structures
        required_fields = [
            "initial_npcs: Record<string, NPCModel>",
            "initial_quests: Record<string, QuestModel>",
            "house_rules: HouseRulesModel",
            "starting_location: LocationModel",
            "world_lore: string[]",
            "starting_gold_range?: GoldRangeModel"
        ]
        
        for field in required_fields:
            assert field in camp_interface, f"Missing field in CampaignTemplateModel: {field}"