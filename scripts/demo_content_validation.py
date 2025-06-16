#!/usr/bin/env python3
"""Demonstration of D&D 5e content validation.

This script shows how the ContentValidator works with real content from the database.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.content.connection import DatabaseManager
from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.service import ContentService
from app.domain.validators import ContentValidator
from app.models.campaign import CampaignTemplateModel
from app.models.character import CharacterTemplateModel
from app.models.combat import AttackModel, CombatantModel
from app.models.utils import BaseStatsModel, LocationModel, ProficienciesModel


def demo_character_validation(validator: ContentValidator) -> None:
    """Demonstrate character validation."""
    print("\n=== Character Validation Demo ===\n")

    # Valid character
    print("1. Testing VALID character:")
    valid_character = CharacterTemplateModel(
        id="test-1",
        name="Aragorn",
        race="Human",
        char_class="Fighter",
        level=5,
        background="Acolyte",
        alignment="Neutral Good",
        base_stats=BaseStatsModel(STR=16, DEX=14, CON=15, INT=10, WIS=13, CHA=12),
        proficiencies=ProficienciesModel(
            armor=["Light Armor", "Medium Armor", "Heavy Armor", "Shields"],
            weapons=["Simple Weapons", "Martial Weapons"],
            skills=["Athletics", "Survival"],
            saving_throws=["STR", "CON"],
        ),
        languages=["Common", "Elvish"],
    )

    result = validator.validate_character_template(valid_character)
    print(f"  Valid: {result.is_valid}")
    if result.errors:
        print(f"  Errors: {result.errors}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")

    # Invalid character - wizard with wrong content
    print("\n2. Testing INVALID character (Wizard with errors):")
    invalid_character = CharacterTemplateModel(
        id="test-2",
        name="Merlin",
        race="Dark Elf",  # Invalid - should be "Drow" or use subrace
        char_class="Wizard",
        subclass="School of Necromancy",  # At level 1, should trigger warning
        level=1,
        background="Soldier",  # Invalid - not in SRD
        alignment="Chaotic Evil",
        base_stats=BaseStatsModel(STR=8, DEX=14, CON=12, INT=18, WIS=13, CHA=10),
        proficiencies=ProficienciesModel(
            skills=["Arcana", "Tracking"],  # "Tracking" is invalid
            saving_throws=["INT", "WIS"],
        ),
        spells_known=["Cure Wounds"],  # Invalid - not a wizard spell
        cantrips_known=["Magic Missile"],  # Invalid - not a cantrip (it's level 1)
        languages=["Common", "Draconic", "Undercommon"],  # Undercommon might be invalid
    )

    result = validator.validate_character_template(invalid_character)
    print(f"  Valid: {result.is_valid}")
    if result.errors:
        for error in result.errors:
            print(f"  Error: {error}")
    if result.warnings:
        for warning in result.warnings:
            print(f"  Warning: {warning}")


def demo_campaign_validation(validator: ContentValidator) -> None:
    """Demonstrate campaign validation."""
    print("\n\n=== Campaign Validation Demo ===\n")

    # Valid campaign
    print("1. Testing VALID campaign:")
    valid_campaign = CampaignTemplateModel(
        id="campaign-1",
        name="The Lost Mine",
        description="A classic D&D adventure",
        campaign_goal="Find the lost mine of Phandelver",
        starting_location=LocationModel(
            name="Neverwinter", description="A bustling city on the Sword Coast"
        ),
        opening_narrative="You have been hired to escort a wagon...",
        starting_level=1,
        difficulty="normal",
        allowed_races=["Human", "Elf", "Dwarf", "Halfling"],
        allowed_classes=["Fighter", "Wizard", "Cleric", "Rogue"],
    )

    result = validator.validate_campaign_template(valid_campaign)
    print(f"  Valid: {result.is_valid}")
    if result.errors:
        print(f"  Errors: {result.errors}")

    # Invalid campaign
    print("\n2. Testing INVALID campaign:")
    invalid_campaign = CampaignTemplateModel(
        id="campaign-2",
        name="Epic Campaign",
        description="An impossible campaign",
        campaign_goal="Defeat all gods",
        starting_location=LocationModel(name="Olympus", description="Home of gods"),
        opening_narrative="You start as gods...",
        starting_level=20,  # Max level
        difficulty="impossible",  # Invalid difficulty
        allowed_races=["Dragon", "Angel"],  # Invalid races
        allowed_classes=["Archmage", "Deity"],  # Invalid classes
    )

    result = validator.validate_campaign_template(invalid_campaign)
    print(f"  Valid: {result.is_valid}")
    if result.errors:
        for error in result.errors:
            print(f"  Error: {error}")


def demo_combatant_validation(validator: ContentValidator) -> None:
    """Demonstrate combatant validation."""
    print("\n\n=== Combatant Validation Demo ===\n")

    # Valid combatant
    print("1. Testing VALID combatant:")
    valid_combatant = CombatantModel(
        id="orc-1",
        name="Orc Warrior",
        initiative=10,
        current_hp=15,
        max_hp=15,
        armor_class=13,
        is_player=False,
        conditions=["Prone"],
        resistances=["Poison"],
        attacks=[
            AttackModel(
                name="Greataxe",
                description="Melee Weapon Attack: +5 to hit",
                attack_type="melee",
                damage_type="slashing",
            )
        ],
    )

    result = validator.validate_combatant(valid_combatant)
    print(f"  Valid: {result.is_valid}")
    if result.errors:
        print(f"  Errors: {result.errors}")

    # Invalid combatant
    print("\n2. Testing INVALID combatant:")
    invalid_combatant = CombatantModel(
        id="monster-1",
        name="Strange Monster",
        initiative=15,
        current_hp=50,
        max_hp=50,
        armor_class=18,
        is_player=False,
        conditions=["Confused", "Dizzy"],  # Invalid conditions
        resistances=["Magic", "Physical"],  # Invalid damage types
        vulnerabilities=["Water"],  # Invalid damage type
        attacks=[
            AttackModel(
                name="Energy Blast",
                description="Special attack",
                attack_type="ranged",
                damage_type="cosmic",  # Invalid damage type
            )
        ],
    )

    result = validator.validate_combatant(invalid_combatant)
    print(f"  Valid: {result.is_valid}")
    if result.errors:
        for error in result.errors:
            print(f"  Error: {error}")


def main() -> None:
    """Run the validation demo."""
    print("D&D 5e Content Validation Demo")
    print("==============================")

    # Initialize services
    print("\nInitializing content service...")
    database_manager = DatabaseManager("sqlite:///data/content.db")
    repository_hub = D5eDbRepositoryHub(database_manager)
    content_service = ContentService(repository_hub)

    # Create validator
    print("Creating validator...")
    validator = ContentValidator(content_service)

    # Run demos
    demo_character_validation(validator)
    demo_campaign_validation(validator)
    demo_combatant_validation(validator)

    print("\n\nDemo complete!")


if __name__ == "__main__":
    main()
