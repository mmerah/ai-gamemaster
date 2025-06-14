"""
Unit tests for InMemoryGameStateRepository to verify type-safe campaign loading.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.models.character import CharacterInstanceModel
from app.models.game_state import GameStateModel
from app.repositories.game.game_state import InMemoryGameStateRepository


@pytest.fixture
def temp_save_dir(tmp_path: Path) -> Path:
    """Create a temporary save directory structure for testing."""
    save_dir = tmp_path / "saves"

    # Create directory structure
    (save_dir / "campaigns").mkdir(parents=True)
    (save_dir / "campaign_templates").mkdir(parents=True)
    (save_dir / "character_templates").mkdir(parents=True)

    return save_dir


@pytest.fixture
def sample_campaign_template(temp_save_dir: Path) -> dict[str, Any]:
    """Create a sample campaign template."""
    template = {
        "id": "test_template",
        "name": "Test Campaign Template",
        "description": "A test campaign",
        "starting_location": {
            "name": "Test Village",
            "description": "A peaceful village for testing",
        },
        "campaign_goal": "Test the campaign system",
        "opening_narrative": "Welcome to the test campaign!",
        "initial_npcs": {
            "npc1": {
                "id": "npc1",
                "name": "Test NPC",
                "description": "A helpful test NPC",
                "last_location": "Test Village",
            }
        },
        "initial_quests": {
            "quest1": {
                "id": "quest1",
                "title": "Test Quest",
                "description": "Complete the test",
                "status": "active",
            }
        },
        "world_lore": ["Test lore item 1", "Test lore item 2"],
        "narration_enabled": True,
        "tts_voice": "test_voice",
        "ruleset_id": "test_rules",
        "lore_id": "test_lore",
        "version": 1,
    }

    template_path = temp_save_dir / "campaign_templates" / "test_template.json"
    with open(template_path, "w") as f:
        json.dump(template, f)

    return template


@pytest.fixture
def sample_character_templates(temp_save_dir: Path) -> list[dict[str, Any]]:
    """Create sample character templates."""
    templates = [
        {
            "id": "test_fighter",
            "name": "Test Fighter",
            "race": "Human",
            "char_class": "Fighter",
            "level": 1,
            "background": "Soldier",
            "alignment": "Lawful Good",
            "base_stats": {
                "STR": 16,
                "DEX": 14,
                "CON": 15,
                "INT": 10,
                "WIS": 12,
                "CHA": 8,
            },
            "starting_gold": 50,
            "version": 1,
        },
        {
            "id": "test_wizard",
            "name": "Test Wizard",
            "race": "Elf",
            "char_class": "Wizard",
            "level": 1,
            "background": "Sage",
            "alignment": "Neutral Good",
            "base_stats": {
                "STR": 8,
                "DEX": 14,
                "CON": 12,
                "INT": 16,
                "WIS": 13,
                "CHA": 10,
            },
            "starting_gold": 30,
            "version": 1,
        },
    ]

    for template in templates:
        template_path = temp_save_dir / "character_templates" / f"{template['id']}.json"
        with open(template_path, "w") as f:
            json.dump(template, f)

    return templates


@pytest.fixture
def sample_campaign_instance(
    temp_save_dir: Path, sample_campaign_template: dict[str, Any]
) -> dict[str, Any]:
    """Create a sample campaign instance."""
    instance = {
        "id": "test_campaign_123",
        "name": "My Test Campaign",
        "template_id": "test_template",
        "character_ids": ["test_fighter", "test_wizard"],
        "current_location": "Test Village",
        "session_count": 0,
        "in_combat": False,
        "event_summary": [],
        "starting_level": 3,
        "narration_enabled": False,  # Override template setting
        "tts_voice": "override_voice",
        "created_date": datetime.now(timezone.utc).isoformat(),
        "last_played": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }

    instance_dir = temp_save_dir / "campaigns" / "test_campaign_123"
    instance_dir.mkdir(parents=True)
    instance_path = instance_dir / "instance.json"

    with open(instance_path, "w") as f:
        json.dump(instance, f)

    return instance


def test_in_memory_repository_initialization(temp_save_dir: Path) -> None:
    """Test that InMemoryGameStateRepository initializes with minimal default state."""
    repo = InMemoryGameStateRepository(str(temp_save_dir))

    state = repo.get_game_state()
    assert state.campaign_id is None
    assert state.campaign_name == "Default Campaign"
    assert state.current_location.name == "Tavern"
    assert len(state.chat_history) == 1
    assert (
        state.chat_history[0].content
        == "Welcome! Please load or create a campaign to begin your adventure."
    )


def test_load_campaign_from_instance(
    temp_save_dir: Path,
    sample_campaign_template: dict[str, Any],
    sample_character_templates: list[dict[str, Any]],
    sample_campaign_instance: dict[str, Any],
) -> None:
    """Test loading a campaign from campaign instance definition."""
    repo = InMemoryGameStateRepository(str(temp_save_dir))

    # Create a saved game state file for the campaign
    campaign_dir = temp_save_dir / "campaigns" / "test_campaign_123"
    game_state_data = {
        "campaign_id": "test_campaign_123",
        "campaign_name": "My Test Campaign",
        "campaign_goal": "Test the campaign system",
        "current_location": {
            "name": "Test Village",
            "description": "A peaceful village for testing",
        },
        "world_lore": ["Test lore item 1", "Test lore item 2"],
        "active_ruleset_id": "test_rules",
        "active_lore_id": "test_lore",
        "narration_enabled": False,
        "tts_voice": "override_voice",
        "known_npcs": {
            "npc1": {
                "id": "npc1",
                "name": "Test NPC",
                "description": "A helpful test NPC",
                "last_location": "Test Village",
            }
        },
        "active_quests": {
            "quest1": {
                "id": "quest1",
                "title": "Test Quest",
                "description": "Complete the test",
                "status": "active",
            }
        },
        "party": {
            "char1": {
                "template_id": "test_fighter",
                "campaign_id": "test_campaign_123",
                "level": 3,
                "current_hp": 30,
                "max_hp": 30,
                "conditions": [],
                "inventory": [],
                "gold": 50,
            },
            "char2": {
                "template_id": "test_wizard",
                "campaign_id": "test_campaign_123",
                "level": 3,
                "current_hp": 18,
                "max_hp": 18,
                "conditions": [],
                "inventory": [],
                "gold": 50,
            },
        },
        "chat_history": [
            {
                "id": "msg1",
                "role": "assistant",
                "content": "Welcome to the test campaign!",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "pending_player_dice_requests": [],
        "combat": {
            "is_active": False,
            "combatants": [],
            "current_turn_index": -1,
            "round_number": 1,
        },
        "event_summary": [],
        "session_count": 0,
        "in_combat": False,
        "version": 1,
    }

    with open(campaign_dir / "active_game_state.json", "w") as f:
        json.dump(game_state_data, f)

    # Load campaign state
    state = repo.load_campaign_state("test_campaign_123")

    assert state is not None
    assert state.campaign_id == "test_campaign_123"
    assert state.campaign_name == "My Test Campaign"

    # Check campaign template data was loaded
    assert state.campaign_goal == "Test the campaign system"
    assert state.current_location.name == "Test Village"
    assert state.current_location.description == "A peaceful village for testing"
    assert len(state.world_lore) == 2
    assert state.active_ruleset_id == "test_rules"
    assert state.active_lore_id == "test_lore"

    # Check NPCs and quests
    assert "npc1" in state.known_npcs
    assert state.known_npcs["npc1"].name == "Test NPC"
    assert "quest1" in state.active_quests
    assert state.active_quests["quest1"].title == "Test Quest"

    # Check TTS settings (instance should override template)
    assert state.narration_enabled is False  # Instance override
    assert state.tts_voice == "override_voice"  # Instance override

    # Check party was created from character templates
    assert len(state.party) == 2
    assert "char1" in state.party
    assert "char2" in state.party

    # Check character instances
    char1 = state.party["char1"]
    assert isinstance(char1, CharacterInstanceModel)
    assert char1.template_id == "test_fighter"
    assert char1.campaign_id == "test_campaign_123"
    assert char1.level == 3  # From campaign starting_level
    assert char1.max_hp > 0
    assert char1.current_hp == char1.max_hp

    char2 = state.party["char2"]
    assert char2.template_id == "test_wizard"
    assert char2.level == 3

    # Check opening narrative was added
    assert len(state.chat_history) == 1
    assert state.chat_history[0].content == "Welcome to the test campaign!"

    # Verify it's now the active state
    assert repo.get_game_state().campaign_id == "test_campaign_123"


def test_load_campaign_caches_in_memory(
    temp_save_dir: Path,
    sample_campaign_template: dict[str, Any],
    sample_character_templates: list[dict[str, Any]],
    sample_campaign_instance: dict[str, Any],
) -> None:
    """Test that loaded campaigns are cached in memory."""
    repo = InMemoryGameStateRepository(str(temp_save_dir))

    # Create a saved game state file
    campaign_dir = temp_save_dir / "campaigns" / "test_campaign_123"
    game_state_data = {
        "campaign_id": "test_campaign_123",
        "campaign_name": "Test Campaign",
        "current_location": {"name": "Tavern", "description": "A cozy tavern."},
        "campaign_goal": "Test caching",
        "party": {},
        "known_npcs": {},
        "active_quests": {},
        "world_lore": [],
        "event_summary": [],
        "chat_history": [],
        "pending_player_dice_requests": [],
        "combat": {
            "is_active": False,
            "combatants": [],
            "current_turn_index": -1,
            "round_number": 1,
        },
        "session_count": 0,
        "in_combat": False,
        "narration_enabled": False,
        "tts_voice": "af_heart",
        "version": 1,
    }

    with open(campaign_dir / "active_game_state.json", "w") as f:
        json.dump(game_state_data, f)

    # Load campaign state
    state1 = repo.load_campaign_state("test_campaign_123")

    # Delete the game state file to ensure it's loading from memory
    game_state_path = (
        Path(temp_save_dir)
        / "campaigns"
        / "test_campaign_123"
        / "active_game_state.json"
    )
    game_state_path.unlink()

    # Should still be able to load from memory
    state2 = repo.load_campaign_state("test_campaign_123")

    assert state2 is not None
    assert state2.campaign_id == "test_campaign_123"

    # Should be a deep copy, not the same object
    assert state1 is not state2
    assert state1 is not None and state2 is not None  # Type guard for mypy
    assert state1.campaign_id == state2.campaign_id


def test_save_game_state_updates_memory(temp_save_dir: Path) -> None:
    """Test that saving game state updates in-memory storage."""
    repo = InMemoryGameStateRepository(str(temp_save_dir))

    # Create a game state with campaign ID
    state = GameStateModel(
        campaign_id="test_save_123",
        campaign_name="Test Save Campaign",
        campaign_goal="Test saving",
    )

    # Save it
    repo.save_game_state(state)

    # Should be the active state
    assert repo.get_game_state().campaign_id == "test_save_123"

    # Should be in campaign saves
    loaded = repo.load_campaign_state("test_save_123")
    assert loaded is not None
    assert loaded.campaign_goal == "Test saving"


def test_load_nonexistent_campaign(temp_save_dir: Path) -> None:
    """Test loading a campaign that doesn't exist."""
    repo = InMemoryGameStateRepository(str(temp_save_dir))

    state = repo.load_campaign_state("nonexistent_campaign")
    assert state is None


def test_load_campaign_missing_template(
    temp_save_dir: Path, sample_character_templates: list[dict[str, Any]]
) -> None:
    """Test loading a campaign when the template is missing."""
    # Create instance without corresponding template
    instance = {
        "id": "bad_campaign",
        "name": "Bad Campaign",
        "template_id": "missing_template",
        "character_ids": ["test_fighter"],
        "version": 1,
    }

    instance_dir = Path(temp_save_dir) / "campaigns" / "bad_campaign"
    instance_dir.mkdir(parents=True)
    with open(instance_dir / "instance.json", "w") as f:
        json.dump(instance, f)

    repo = InMemoryGameStateRepository(str(temp_save_dir))
    state = repo.load_campaign_state("bad_campaign")
    assert state is None


def test_tts_settings_hierarchy(
    temp_save_dir: Path,
    sample_campaign_template: dict[str, Any],
    sample_character_templates: list[dict[str, Any]],
) -> None:
    """Test TTS settings hierarchy: instance > template."""
    # Test 1: Instance with overrides
    campaign_dir1 = Path(temp_save_dir) / "campaigns" / "campaign_with_override"
    campaign_dir1.mkdir(parents=True)

    # Create game state with overridden TTS settings
    game_state1 = {
        "campaign_id": "campaign_with_override",
        "campaign_name": "Campaign with Override",
        "campaign_goal": "Test the campaign system",
        "current_location": {
            "name": "Test Village",
            "description": "A peaceful village for testing",
        },
        "world_lore": ["Test lore item 1", "Test lore item 2"],
        "active_ruleset_id": "test_rules",
        "active_lore_id": "test_lore",
        "narration_enabled": False,  # Override from instance
        "tts_voice": "custom_voice",  # Override from instance
        "known_npcs": {},
        "active_quests": {},
        "party": {},
        "chat_history": [],
        "pending_player_dice_requests": [],
        "combat": {
            "is_active": False,
            "combatants": [],
            "current_turn_index": -1,
            "round_number": 1,
        },
        "event_summary": [],
        "session_count": 0,
        "in_combat": False,
        "version": 1,
    }

    with open(campaign_dir1 / "active_game_state.json", "w") as f:
        json.dump(game_state1, f)

    repo = InMemoryGameStateRepository(str(temp_save_dir))
    state = repo.load_campaign_state("campaign_with_override")

    assert state is not None
    assert state.narration_enabled is False
    assert state.tts_voice == "custom_voice"

    # Test 2: Instance without overrides (should use template defaults)
    campaign_dir2 = Path(temp_save_dir) / "campaigns" / "campaign_no_override"
    campaign_dir2.mkdir(parents=True)

    # Create game state using template defaults
    game_state2 = {
        "campaign_id": "campaign_no_override",
        "campaign_name": "Campaign No Override",
        "campaign_goal": "Test the campaign system",
        "current_location": {
            "name": "Test Village",
            "description": "A peaceful village for testing",
        },
        "world_lore": ["Test lore item 1", "Test lore item 2"],
        "active_ruleset_id": "test_rules",
        "active_lore_id": "test_lore",
        "narration_enabled": True,  # From template
        "tts_voice": "test_voice",  # From template
        "known_npcs": {},
        "active_quests": {},
        "party": {},
        "chat_history": [],
        "pending_player_dice_requests": [],
        "combat": {
            "is_active": False,
            "combatants": [],
            "current_turn_index": -1,
            "round_number": 1,
        },
        "event_summary": [],
        "session_count": 0,
        "in_combat": False,
        "version": 1,
    }

    with open(campaign_dir2 / "active_game_state.json", "w") as f:
        json.dump(game_state2, f)

    state2 = repo.load_campaign_state("campaign_no_override")

    assert state2 is not None
    # Should use template defaults
    assert state2.narration_enabled is True  # From template
    assert state2.tts_voice == "test_voice"  # From template
