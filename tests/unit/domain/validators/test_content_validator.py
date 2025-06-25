"""Unit tests for the content validator."""

from typing import List
from unittest.mock import Mock, patch

import pytest

from app.content.service import ContentService
from app.domain.validators.content_validator import (
    ContentValidationError,
    ContentValidator,
)
from app.models.campaign.template import CampaignTemplateModel
from app.models.character.template import CharacterTemplateModel
from app.models.combat.combatant import CombatantModel
from app.models.utils import (
    BaseStatsModel,
    HouseRulesModel,
    LocationModel,
    ProficienciesModel,
)


class TestContentValidator:
    """Test the ContentValidator class."""

    @pytest.fixture
    def mock_content_service(self) -> Mock:
        """Create a mock content service."""
        service = Mock(spec=ContentService)
        service._hub = Mock()

        # Setup repository mocks
        service._hub.races = Mock()
        service._hub.subraces = Mock()
        service._hub.classes = Mock()
        service._hub.subclasses = Mock()
        service._hub.backgrounds = Mock()
        service._hub.alignments = Mock()
        service._hub.languages = Mock()
        service._hub.spells = Mock()
        service._hub.conditions = Mock()
        service._hub.damage_types = Mock()
        service._hub.proficiencies = Mock()
        service._hub.ability_scores = Mock()
        service._hub.skills = Mock()
        service._hub.get_repository = Mock()

        return service

    @pytest.fixture
    def validator(self, mock_content_service: Mock) -> ContentValidator:
        """Create a content validator with mock service."""
        return ContentValidator(mock_content_service)

    def test_validate_character_template_valid(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test validation of a valid character template."""
        # Setup mocks to return valid content
        mock_content_service._hub.races.get_by_name_with_options.return_value = Mock(
            name="Human"
        )
        mock_content_service._hub.classes.get_by_name_with_options.return_value = Mock(
            name="Fighter"
        )
        mock_content_service._hub.backgrounds.get_by_name_with_options.return_value = (
            Mock(name="Soldier")
        )
        mock_content_service._hub.alignments.get_by_name_with_options.return_value = (
            Mock(name="Lawful Good")
        )

        # Mock for languages
        lang_repo = Mock()
        lang_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name)
            if name in ["Common", "Elvish"]
            else None
        )
        lang_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index)
            if index in ["common", "elvish"]
            else None
        )
        mock_content_service._hub.get_repository.return_value = lang_repo

        # Create a valid character template
        template = CharacterTemplateModel(
            id="test-char",
            name="Test Character",
            race="Human",
            char_class="Fighter",
            level=1,
            background="Soldier",
            alignment="Lawful Good",
            base_stats=BaseStatsModel(STR=15, DEX=14, CON=13, INT=12, WIS=10, CHA=8),
            proficiencies=ProficienciesModel(),
            languages=["Common", "Elvish"],
            content_pack_ids=["dnd_5e_srd"],
        )

        is_valid, errors = validator.validate_character_template(template)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_character_template_invalid_race(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test validation with invalid race."""
        # Setup mocks to return None for invalid race
        mock_content_service._hub.races.get_by_name_with_options.return_value = None
        mock_content_service._hub.races.get_by_index_with_options.return_value = None
        mock_content_service._hub.classes.get_by_name_with_options.return_value = Mock()
        mock_content_service._hub.backgrounds.get_by_name_with_options.return_value = (
            Mock()
        )
        mock_content_service._hub.alignments.get_by_name_with_options.return_value = (
            Mock()
        )

        template = CharacterTemplateModel(
            id="test-char",
            name="Test Character",
            race="InvalidRace",
            char_class="Fighter",
            level=1,
            background="Soldier",
            alignment="Lawful Good",
            base_stats=BaseStatsModel(STR=15, DEX=14, CON=13, INT=12, WIS=10, CHA=8),
            proficiencies=ProficienciesModel(),
        )

        is_valid, errors = validator.validate_character_template(template)

        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].field == "race"
        assert errors[0].value == "InvalidRace"
        assert "not found" in errors[0].message

    def test_validate_character_template_invalid_spells(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test validation with invalid spells."""
        # Setup valid content mocks
        mock_content_service._hub.races.get_by_name_with_options.return_value = Mock()
        mock_content_service._hub.classes.get_by_name_with_options.return_value = Mock()
        mock_content_service._hub.backgrounds.get_by_name_with_options.return_value = (
            Mock()
        )
        mock_content_service._hub.alignments.get_by_name_with_options.return_value = (
            Mock()
        )

        # Mock for spells
        spell_repo = Mock()
        spell_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name) if name == "Fireball" else None
        )
        spell_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index) if index == "fireball" else None
        )
        mock_content_service._hub.get_repository.return_value = spell_repo

        template = CharacterTemplateModel(
            id="test-char",
            name="Test Character",
            race="Human",
            char_class="Wizard",
            level=5,
            background="Sage",
            alignment="Neutral",
            base_stats=BaseStatsModel(STR=8, DEX=14, CON=13, INT=16, WIS=12, CHA=10),
            proficiencies=ProficienciesModel(),
            spells_known=["Fireball", "InvalidSpell", "FakeSpell"],
        )

        is_valid, errors = validator.validate_character_template(template)

        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].field == "spells_known"
        assert "InvalidSpell" in errors[0].value
        assert "FakeSpell" in errors[0].value
        assert "Invalid spells" in errors[0].message

    def test_validate_proficiencies(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test validation of proficiencies."""
        # Mock proficiency data
        prof_data = [
            Mock(type="Armor", name="Light armor", index="light-armor"),
            Mock(type="Armor", name="Medium armor", index="medium-armor"),
            Mock(type="Weapons", name="Simple weapons", index="simple-weapons"),
            Mock(type="Weapons", name="Martial weapons", index="martial-weapons"),
            Mock(type="Tools", name="Thieves' tools", index="thieves-tools"),
        ]
        mock_content_service._hub.proficiencies.list_all_with_options.return_value = (
            prof_data
        )

        # Mock for skills
        skill_repo = Mock()
        skill_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name)
            if name in ["Athletics", "Acrobatics"]
            else None
        )
        skill_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index)
            if index in ["athletics", "acrobatics"]
            else None
        )

        # Mock for ability scores
        ability_repo = Mock()
        ability_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name) if name in ["STR", "DEX"] else None
        )
        ability_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index)
            if index in ["str", "dex"]
            else None
        )

        mock_content_service._hub.get_repository.side_effect = lambda cat: (
            skill_repo
            if cat == "skills"
            else ability_repo
            if cat == "ability-scores"
            else None
        )

        proficiencies = ProficienciesModel(
            armor=["Light armor", "InvalidArmor"],
            weapons=["Simple weapons", "FakeWeapon"],
            tools=["Thieves' tools", "FakeTool"],
            saving_throws=["STR", "DEX", "INVALID"],
            skills=["Athletics", "Acrobatics", "FakeSkill"],
        )

        is_valid, errors = validator.validate_proficiencies(proficiencies)

        assert is_valid is False
        assert len(errors) == 5

        # Check error fields
        error_fields = {error.field for error in errors}
        assert "proficiencies.armor" in error_fields
        assert "proficiencies.weapons" in error_fields
        assert "proficiencies.tools" in error_fields
        assert "proficiencies.saving_throws" in error_fields
        assert "proficiencies.skills" in error_fields

    def test_validate_campaign_template(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test validation of campaign template."""
        # Mock repositories
        race_repo = Mock()
        race_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name)
            if name in ["Human", "Elf", "Dwarf"]
            else None
        )
        race_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index)
            if index in ["human", "elf", "dwarf"]
            else None
        )

        class_repo = Mock()
        class_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name)
            if name in ["Fighter", "Wizard"]
            else None
        )
        class_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index)
            if index in ["fighter", "wizard"]
            else None
        )

        mock_content_service._hub.get_repository.side_effect = lambda cat: (
            race_repo if cat == "races" else class_repo if cat == "classes" else None
        )

        template = CampaignTemplateModel(
            id="test-campaign",
            name="Test Campaign",
            description="A test campaign",
            campaign_goal="Test the validator",
            starting_location=LocationModel(name="Test Town", description="A town"),
            opening_narrative="Once upon a time...",
            starting_level=1,
            allowed_races=["Human", "Elf", "Dwarf", "InvalidRace"],
            allowed_classes=["Fighter", "Wizard", "InvalidClass"],
            house_rules=HouseRulesModel(),
            content_pack_ids=["dnd_5e_srd"],
        )

        is_valid, errors = validator.validate_campaign_template(template)

        assert is_valid is False
        assert len(errors) == 2

        # Check race error
        race_error = next((e for e in errors if e.field == "allowed_races"), None)
        assert race_error is not None
        assert "InvalidRace" in race_error.value

        # Check class error
        class_error = next((e for e in errors if e.field == "allowed_classes"), None)
        assert class_error is not None
        assert "InvalidClass" in class_error.value

    def test_validate_combatant(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test validation of combatant."""
        # Mock repositories
        condition_repo = Mock()
        condition_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name)
            if name in ["Poisoned", "Stunned"]
            else None
        )
        condition_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index)
            if index in ["poisoned", "stunned"]
            else None
        )

        damage_repo = Mock()
        damage_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name)
            if name in ["Fire", "Cold", "Slashing"]
            else None
        )
        damage_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index)
            if index in ["fire", "cold", "slashing"]
            else None
        )

        mock_content_service._hub.get_repository.side_effect = lambda cat: (
            condition_repo
            if cat == "conditions"
            else damage_repo
            if cat == "damage-types"
            else None
        )

        combatant = CombatantModel(
            id="test-combatant",
            name="Test Monster",
            initiative=15,
            current_hp=50,
            max_hp=50,
            armor_class=15,
            is_player=False,
            conditions=["Poisoned", "InvalidCondition"],
            conditions_immune=["Stunned", "FakeCondition"],
            resistances=["Fire", "Cold", "InvalidDamage"],
            vulnerabilities=["Slashing", "FakeDamage"],
        )

        is_valid, errors = validator.validate_combatant(combatant)

        assert is_valid is False
        assert len(errors) == 4

        # Check all error types are present
        error_fields = {error.field for error in errors}
        assert "conditions" in error_fields
        assert "conditions_immune" in error_fields
        assert "resistances" in error_fields
        assert "vulnerabilities" in error_fields

    def test_validate_content_exists(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test checking if specific content exists."""
        # Mock spell repository
        spell_repo = Mock()
        spell_repo.get_by_name_with_options.side_effect = (
            lambda name, **kwargs: Mock(name=name) if name == "Fireball" else None
        )
        spell_repo.get_by_index_with_options.side_effect = (
            lambda index, **kwargs: Mock(index=index) if index == "fireball" else None
        )

        mock_content_service._hub.get_repository.return_value = spell_repo

        # Test existing spell
        assert validator.validate_content_exists("spell", "Fireball") is True
        assert validator.validate_content_exists("spell", "fireball") is True

        # Test non-existing spell
        assert validator.validate_content_exists("spell", "InvalidSpell") is False

        # Test unknown content type
        assert validator.validate_content_exists("unknown", "Something") is False

    def test_get_valid_options(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test getting valid options for a content type."""
        # Create race mocks with proper name attributes
        human = Mock()
        human.name = "Human"

        elf = Mock()
        elf.name = "Elf"

        dwarf = Mock()
        dwarf.name = "Dwarf"

        halfling = Mock()
        halfling.name = "Halfling"

        race_data = [human, elf, dwarf, halfling]

        race_repo = Mock()
        race_repo.list_all_with_options.return_value = race_data
        mock_content_service._hub.get_repository.return_value = race_repo

        options = validator.get_valid_options("races")

        assert len(options) == 4
        assert "Human" in options
        assert "Elf" in options
        assert "Dwarf" in options
        assert "Halfling" in options

    def test_validation_with_content_pack_priority(
        self, validator: ContentValidator, mock_content_service: Mock
    ) -> None:
        """Test validation respects content pack priority."""
        # Setup mock to check content_pack_priority parameter
        mock_content_service._hub.races.get_by_name_with_options.return_value = Mock()

        template = CharacterTemplateModel(
            id="test-char",
            name="Test Character",
            race="Human",
            char_class="Fighter",
            level=1,
            background="Soldier",
            alignment="Lawful Good",
            base_stats=BaseStatsModel(STR=15, DEX=14, CON=13, INT=12, WIS=10, CHA=8),
            proficiencies=ProficienciesModel(),
            content_pack_ids=["custom_pack", "dnd_5e_srd"],
        )

        # Validate without explicit priority (should use template's content_pack_ids)
        validator.validate_character_template(template)

        # Check that the mock was called with the template's content pack IDs
        mock_content_service._hub.races.get_by_name_with_options.assert_called_with(
            "Human", content_pack_priority=["custom_pack", "dnd_5e_srd"]
        )

        # Reset mock
        mock_content_service._hub.races.get_by_name_with_options.reset_mock()

        # Validate with explicit priority
        custom_priority = ["other_pack", "dnd_5e_srd"]
        validator.validate_character_template(
            template, content_pack_priority=custom_priority
        )

        # Check that the mock was called with the custom priority
        mock_content_service._hub.races.get_by_name_with_options.assert_called_with(
            "Human", content_pack_priority=custom_priority
        )
