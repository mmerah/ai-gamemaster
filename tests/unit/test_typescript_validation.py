"""
Tests to validate that generated TypeScript compiles correctly.
"""

from pathlib import Path

import pytest


class TestTypeScriptValidation:
    """Validate generated TypeScript interfaces compile without errors."""

    @pytest.fixture
    def typescript_file(self) -> Path:
        """Path to generated TypeScript file."""
        return Path("frontend/src/types/unified.ts")

    def test_typescript_file_exists(self, typescript_file: Path) -> None:
        """Test that the generated TypeScript file exists."""
        assert typescript_file.exists(), (
            f"TypeScript file not found at {typescript_file}"
        )

    def test_typescript_syntax_valid(self, typescript_file: Path) -> None:
        """Test that TypeScript syntax is valid without full compilation."""
        content = typescript_file.read_text()

        # Basic syntax checks
        # 1. Check for balanced braces
        open_braces = content.count("{")
        close_braces = content.count("}")
        assert open_braces == close_braces, (
            f"Unbalanced braces: {open_braces} open, {close_braces} close"
        )

        # 2. Check for proper interface declarations
        interface_lines = [
            line for line in content.split("\n") if "export interface" in line
        ]
        for line in interface_lines:
            assert line.strip().endswith("{"), f"Invalid interface declaration: {line}"

        # 3. Check for common syntax errors
        assert ";;" not in content, "Double semicolon found"
        assert "interface interface" not in content, "Double interface keyword"
        assert "export export" not in content, "Double export keyword"

        # 4. Check for proper type declarations
        # Every line with a colon should have a type after it
        type_lines = [
            line for line in content.split("\n") if ":" in line and "//" not in line
        ]
        for line in type_lines:
            if "interface" not in line and "{" not in line:
                # Should have type after colon
                parts = line.split(":")
                if len(parts) >= 2:
                    type_part = parts[1].strip()
                    assert type_part and not type_part.startswith(","), (
                        f"Missing type in: {line}"
                    )

        # 5. Verify no Python-specific syntax leaked in
        assert "Optional[" not in content, "Python Optional type found"
        assert "List[" not in content, "Python List type found"
        assert "Dict[" not in content, "Python Dict type found"
        assert "from typing" not in content, "Python import found"

    def test_types_structure_complete(self, typescript_file: Path) -> None:
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
            "export interface ClassFeatureModel",
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
            "PlayerDiceRequestAddedEvent",
        ]

        for event_type in event_types:
            assert f"export interface {event_type}" in content, (
                f"Missing event type: {event_type}"
            )

    def test_character_template_fields_complete(self, typescript_file: Path) -> None:
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
            "backstory?: string",
        ]

        for field in required_fields:
            assert field in char_interface, (
                f"Missing field in CharacterTemplateModel: {field}"
            )

    def test_campaign_template_nested_structures(self, typescript_file: Path) -> None:
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
            "starting_gold_range?: GoldRangeModel",
        ]

        for field in required_fields:
            assert field in camp_interface, (
                f"Missing field in CampaignTemplateModel: {field}"
            )
