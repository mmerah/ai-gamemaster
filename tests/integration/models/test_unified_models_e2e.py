"""
UNIFIED MODELS END-TO-END TEST

Tests the complete flow with unified models:
- Character template creation with all fields
- Campaign template creation with all fields
- Campaign instance creation from templates
- Game start with proper model transformations
- Gameplay actions with unified event models
- Save/load with unified GameStateModel

This ensures the entire system works cohesively with the unified type system.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from app.domain.characters.service import CharacterServiceImpl
from app.events.definitions import create_game_state_snapshot_event
from app.models.campaign import CampaignTemplateModel
from app.models.character import CharacterInstanceModel, CharacterTemplateModel
from app.models.game_state import ChatMessageModel, GameStateModel
from app.models.updates import LocationUpdateModel, QuestUpdateModel
from app.models.utils import (
    BaseStatsModel,
    ItemModel,
    LocationModel,
    NPCModel,
    ProficienciesModel,
    QuestModel,
    TraitModel,
)
from app.providers.ai.schemas import AIResponse


@pytest.fixture
def temp_save_dir(tmp_path: Path) -> Dict[str, Path]:
    """Create temporary directories for testing."""
    dirs = {
        "character_templates": tmp_path / "character_templates",
        "campaign_templates": tmp_path / "campaign_templates",
        "campaigns": tmp_path / "campaigns",
    }
    for dir in dirs.values():
        dir.mkdir(parents=True, exist_ok=True)
    return dirs


@pytest.fixture
def app_with_temp_dirs(
    temp_save_dir: Dict[str, Path], tmp_path: Path, mock_ai_service: Any
) -> Generator[Any, None, None]:
    """Create a Flask app with test configuration using specific temp directories."""
    from app import create_app
    from app.core.container import reset_container
    from tests.conftest import get_test_config

    reset_container()

    config = get_test_config()
    # Update config fields directly
    config.GAME_STATE_REPO_TYPE = (
        "file"  # Use file type to actually test file operations
    )
    config.SAVES_DIR = str(tmp_path)  # Base directory for FileGameStateRepository
    config.CAMPAIGNS_DIR = str(tmp_path / "campaigns")
    config.CHARACTER_TEMPLATES_DIR = str(temp_save_dir["character_templates"])
    config.CAMPAIGN_TEMPLATES_DIR = str(temp_save_dir["campaign_templates"])
    config.AI_SERVICE = mock_ai_service  # Use centralized mock

    app = create_app(config)

    with app.app_context():
        yield app
        reset_container()


class TestUnifiedModelsE2E:
    """Comprehensive tests for unified models throughout the system."""

    def test_complete_flow_with_unified_models(
        self,
        app_with_temp_dirs: Any,
        temp_save_dir: Dict[str, Path],
        mock_ai_service: Any,
    ) -> None:
        """Test the complete flow from templates to gameplay with unified models."""
        app = app_with_temp_dirs
        client = app.test_client()

        # Get container from the app context
        from app.core.container import get_container

        container = get_container()

        # Create event recorder
        from tests.test_helpers import EventRecorder

        event_recorder = EventRecorder()
        event_queue = container.get_event_queue()
        event_recorder.attach_to_queue(event_queue)

        # Clear any initial events
        event_recorder.clear()

        # ========== PHASE 1: Create Character Templates ==========
        print("\n1. Creating character templates with all unified model fields...")

        character_templates = []

        warrior_template = CharacterTemplateModel(
            id="test_warrior_" + str(uuid.uuid4())[:8],
            name="Thorin Ironforge",
            race="Dwarf",
            subrace="Mountain Dwarf",
            char_class="Fighter",
            subclass="Champion",
            level=3,
            background="Soldier",
            alignment="Lawful Good",
            base_stats=BaseStatsModel(STR=16, DEX=12, CON=14, INT=10, WIS=13, CHA=8),
            proficiencies=ProficienciesModel(
                armor=["light", "medium", "heavy", "shields"],
                weapons=["simple", "martial"],
                skills=["athletics", "intimidation", "perception", "survival"],
                saving_throws=["STR", "CON"],
            ),
            languages=["Common", "Dwarvish"],
            personality_traits=[
                "I face problems head-on. A simple, direct solution is the best path to success.",
                "I can stare down a hell hound without flinching.",
            ],
            ideals=[
                "Greater Good. Our lot is to lay down our lives in defense of others."
            ],
            bonds=["I would still lay down my life for the people I served with."],
            flaws=["I'd rather eat my armor than admit when I'm wrong."],
            appearance="A stout dwarf with a magnificent braided beard and battle-worn armor.",
            backstory="Veteran of many battles, Thorin seeks redemption for a tactical error that cost lives.",
            feats=[
                TraitModel(
                    name="Tough",
                    description="Your hit point maximum increases by an amount equal to twice your level.",
                )
            ],
            starting_equipment=[
                ItemModel(
                    id="chainmail",
                    name="Chainmail",
                    description="Heavy armor providing AC 16",
                    quantity=1,
                ),
                ItemModel(
                    id="shield", name="Shield", description="+2 AC bonus", quantity=1
                ),
                ItemModel(
                    id="battleaxe",
                    name="Battleaxe",
                    description="1d8 slashing damage",
                    quantity=1,
                ),
                ItemModel(
                    id="handaxe",
                    name="Handaxe",
                    description="1d6 slashing damage, light, thrown",
                    quantity=2,
                ),
                ItemModel(
                    id="explorers_pack",
                    name="Explorer's Pack",
                    description="Includes bedroll, mess kit, tinderbox, torches, rations, waterskin, rope",
                    quantity=1,
                ),
            ],
            portrait_path="/images/portraits/thorin.png",
            starting_gold=50,
        )

        # Save warrior template
        char_template_repo = container.get_character_template_repository()
        char_template_repo.save_template(warrior_template)
        character_templates.append(warrior_template)

        # Create a mage template
        mage_template = CharacterTemplateModel(
            id="test_mage_" + str(uuid.uuid4())[:8],
            name="Elara Moonwhisper",
            race="Elf",
            subrace="High Elf",
            char_class="Wizard",
            subclass="School of Evocation",
            level=3,
            background="Sage",
            alignment="Neutral Good",
            base_stats=BaseStatsModel(STR=8, DEX=14, CON=12, INT=16, WIS=13, CHA=10),
            proficiencies=ProficienciesModel(
                armor=[],
                weapons=[
                    "daggers",
                    "darts",
                    "slings",
                    "quarterstaffs",
                    "light crossbows",
                ],
                skills=["arcana", "history", "investigation", "insight"],
                saving_throws=["INT", "WIS"],
            ),
            languages=["Common", "Elvish", "Draconic", "Celestial"],
            personality_traits=[
                "I use polysyllabic words that convey the impression of great erudition.",
                "I'm used to helping out those who aren't as smart as I am.",
            ],
            ideals=[
                "Knowledge. The path to power and self-improvement is through knowledge."
            ],
            bonds=[
                "I have an ancient text that holds terrible secrets that must not fall into the wrong hands."
            ],
            flaws=[
                "I speak without really thinking through my words, invariably insulting others."
            ],
            appearance="A graceful elf with silver hair and eyes that sparkle with arcane energy.",
            backstory="Trained in the ancient libraries of her people, Elara seeks lost magical knowledge.",
            feats=[],
            starting_equipment=[
                ItemModel(
                    id="quarterstaff",
                    name="Quarterstaff",
                    description="1d6 bludgeoning damage, versatile (1d8)",
                    quantity=1,
                ),
                ItemModel(
                    id="component_pouch",
                    name="Component Pouch",
                    description="Contains material components for spells",
                    quantity=1,
                ),
                ItemModel(
                    id="scholars_pack",
                    name="Scholar's Pack",
                    description="Includes book, ink, parchment, small knife",
                    quantity=1,
                ),
                ItemModel(
                    id="spellbook",
                    name="Spellbook",
                    description="Contains your wizard spells",
                    quantity=1,
                ),
            ],
            portrait_path="/images/portraits/elara.png",
            starting_gold=75,
            spells_known=["Magic Missile", "Shield", "Burning Hands", "Detect Magic"],
            cantrips_known=["Fire Bolt", "Mage Hand", "Prestidigitation"],
        )

        char_template_repo.save_template(mage_template)
        character_templates.append(mage_template)

        # Verify templates were saved
        all_templates = char_template_repo.get_all_templates()
        assert len(all_templates) >= 2, "Should have at least 2 character templates"

        # ========== PHASE 2: Create Campaign Template ==========
        print("\n2. Creating campaign template with all unified model fields...")

        campaign_template = CampaignTemplateModel(
            id="test_campaign_" + str(uuid.uuid4())[:8],
            name="The Lost Mine of Phandelver",
            description="A classic D&D adventure involving a lost mine and dark forces.",
            campaign_goal="Find the lost mine and defeat the evil threatening Phandalin.",
            opening_narrative="You've been hired to escort a wagon to Phandalin...",
            starting_location=LocationModel(
                name="Neverwinter - High Road",
                description="The well-traveled road leading from Neverwinter to Phandalin.",
            ),
            starting_level=3,
            difficulty="normal",
            xp_system="milestone",
            ruleset_id="dnd_5e_standard",
            lore_id="generic_fantasy",
            theme_mood="Classic heroic fantasy with mystery elements",
            session_zero_notes="Discuss character connections and motivations for taking the job.",
            tags=["exploration", "combat", "mystery", "classic"],
            narration_enabled=True,
            tts_voice="af_heart",
            initial_npcs={
                "gundren": NPCModel(
                    id="gundren",
                    name="Gundren Rockseeker",
                    description="A friendly dwarf merchant who hired you. Enthusiastic and secretive about his discovery.",
                    last_location="Unknown (kidnapped)",
                )
            },
            initial_quests={
                "escort_wagon": QuestModel(
                    id="escort_wagon",
                    title="Escort the Wagon",
                    description="Safely deliver Gundren's wagon to Barthen's Provisions in Phandalin. Reward: 10 gold pieces each.",
                    status="active",
                )
            },
            created_date=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )

        # Save campaign template
        campaign_template_repo = container.get_campaign_template_repository()
        campaign_template_repo.save_template(campaign_template)

        # Verify template was saved
        saved_template = campaign_template_repo.get_template(campaign_template.id)
        assert saved_template is not None, "Campaign template should be saved"
        assert saved_template.name == campaign_template.name

        # ========== PHASE 3: Create Campaign Instance ==========
        print("\n3. Creating campaign instance from templates...")

        campaign_service = container.get_campaign_service()

        # Just start campaign from template without mocking
        game_state = campaign_service.start_campaign_from_template(
            template_id=campaign_template.id,
            instance_name="Our Phandelver Adventure",
            party_character_ids=[t.id for t in character_templates],
        )

        # ========== PHASE 4: Verify Game State Structure ==========
        print("\n4. Verifying game state uses unified models...")

        assert isinstance(game_state, GameStateModel), "Should return GameStateModel"
        assert game_state.campaign_id is not None
        assert (
            game_state.current_location.name == campaign_template.starting_location.name
        )
        assert len(game_state.party) == 2, "Should have 2 party members"

        # Verify character instances
        for char_id, char_instance in game_state.party.items():
            assert isinstance(char_instance, CharacterInstanceModel)
            assert char_instance.template_id in [t.id for t in character_templates]
            assert char_instance.campaign_id == game_state.campaign_id
            assert char_instance.current_hp > 0
            assert char_instance.level == 3

        # Verify quests
        assert len(game_state.active_quests) >= 1
        first_quest_id = list(game_state.active_quests.keys())[0]
        assert isinstance(game_state.active_quests[first_quest_id], QuestModel)
        assert game_state.active_quests[first_quest_id].title == "Escort the Wagon"

        # Verify NPCs
        assert len(game_state.known_npcs) >= 1
        first_npc_id = list(game_state.known_npcs.keys())[0]
        assert isinstance(game_state.known_npcs[first_npc_id], NPCModel)
        assert game_state.known_npcs[first_npc_id].name == "Gundren Rockseeker"

        # ========== PHASE 5: Test Gameplay with Unified Events ==========
        print("\n5. Testing gameplay actions with unified event models...")

        # The mock_ai_service is already injected via fixture

        # Mock game state repository to return our game state
        game_state_repo = container.get_game_state_repository()
        with patch.object(game_state_repo, "get_game_state", return_value=game_state):
            # Test location change
            mock_ai_service.add_response(
                AIResponse(
                    narrative="You travel south along the High Road. After a few hours, you spot overturned wagons ahead.",
                    reasoning="Moving the story forward",
                    location_update=LocationUpdateModel(
                        name="Triboar Trail - Ambush Site",
                        description="A narrow trail with overturned wagons and signs of struggle.",
                    ),
                )
            )

            response = client.post(
                "/api/player_action",
                json={
                    "action_type": "free_text",
                    "value": "We continue down the road, keeping watch for trouble.",
                },
            )
            assert response.status_code == 200

            # Verify location change event
            location_events = [
                e for e in event_recorder.events if e.event_type == "location_changed"
            ]
            assert len(location_events) > 0
            location_events[-1]
            # Event recorder events are BaseGameUpdateEvent instances

            # Test quest update without combat (simpler for this test)
            event_recorder.clear()

            mock_ai_service.add_response(
                AIResponse(
                    narrative="As you approach the overturned wagons, you notice signs of a struggle. Blood stains and torn fabric suggest your employer Gundren may have been taken. You find a torn map piece with 'Cragmaw Hideout' marked on it.",
                    reasoning="Quest discovery and update",
                    quest_updates=[
                        QuestUpdateModel(
                            quest_id="escort_wagon",
                            status="completed",
                            objectives_completed=1,
                            objectives_total=1,
                            rewards_experience=100,
                            rewards_gold=10,
                            rewards_items=[],
                            description="Found map to Cragmaw Hideout where Gundren may be held",
                        )
                    ],
                )
            )

            response = client.post(
                "/api/player_action",
                json={
                    "action_type": "free_text",
                    "value": "We search the overturned wagons for clues.",
                },
            )
            assert response.status_code == 200

            # Verify quest updated event
            quest_events = [
                e for e in event_recorder.events if e.event_type == "quest_updated"
            ]
            assert len(quest_events) > 0

        # ========== PHASE 6: Test Save/Load with Unified Models ==========
        print("\n6. Testing save/load functionality with unified models...")

        # Create a test game state with all the updates applied
        # (In a real scenario, this would be the state after all the game events)
        test_game_state = GameStateModel(
            campaign_id="test_save_campaign",
            current_location=LocationModel(
                name="Triboar Trail - Ambush Site",
                description="A narrow trail with overturned wagons and signs of struggle.",
            ),
            party=game_state.party,  # Use the party from initial setup
            active_quests={
                "escort_wagon": QuestModel(
                    id="escort_wagon",
                    title="Escort the Wagon",
                    description="Safely deliver Gundren's wagon to Barthen's Provisions in Phandalin.",
                    status="completed",  # Updated status
                )
            },
            known_npcs=game_state.known_npcs,
            campaign_goal=game_state.campaign_goal,
            chat_history=[
                ChatMessageModel(
                    id=str(uuid.uuid4()),
                    role="user",
                    content="We search the overturned wagons for clues.",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
                ChatMessageModel(
                    id=str(uuid.uuid4()),
                    role="assistant",
                    content="As you approach the overturned wagons, you notice signs of a struggle.",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
            ],
        )

        # Save the test game state
        game_state_repo.save_game_state(test_game_state)

        # The FileGameStateRepository uses base_save_dir (tmp_path) + "campaigns" + campaign_id
        # So the save path is: tmp_path / "campaigns" / test_game_state.campaign_id / "active_game_state.json"
        from pathlib import Path

        saves_dir = app.config.get("SAVES_DIR")
        assert saves_dir is not None, "SAVES_DIR must be configured"
        campaign_id_for_save = test_game_state.campaign_id
        assert campaign_id_for_save is not None
        save_path = (
            Path(saves_dir)
            / "campaigns"
            / campaign_id_for_save
            / "active_game_state.json"
        )
        assert save_path.exists(), f"Game state should be saved at {save_path}"

        # Load and verify structure matches unified models
        with open(save_path) as f:
            saved_data = json.load(f)

        # Verify saved data has expected unified model structure
        assert "current_location" in saved_data
        assert "name" in saved_data["current_location"]
        assert "party" in saved_data
        assert "active_quests" in saved_data
        assert "known_npcs" in saved_data
        assert "chat_history" in saved_data

        # Load game state and verify it reconstructs properly
        campaign_id = test_game_state.campaign_id
        assert campaign_id is not None
        loaded_state = game_state_repo.load_campaign_state(campaign_id)
        assert isinstance(loaded_state, GameStateModel)
        assert loaded_state.campaign_id == test_game_state.campaign_id
        assert (
            loaded_state.current_location.name == test_game_state.current_location.name
        )
        assert len(loaded_state.party) == len(test_game_state.party)

        # Verify quest was saved with completed status
        assert "escort_wagon" in loaded_state.active_quests
        assert loaded_state.active_quests["escort_wagon"].status == "completed"

        print("\n✓ Complete unified models flow test passed!")

    def test_game_state_snapshot_event_typing(self, app_with_temp_dirs: Any) -> None:
        """Test that GameStateSnapshotEvent uses proper typed models."""
        # Get container from the app context
        from app.core.container import get_container

        container = get_container()

        # Create event recorder
        from tests.test_helpers import EventRecorder

        event_recorder = EventRecorder()
        event_queue = container.get_event_queue()
        event_recorder.attach_to_queue(event_queue)

        # Create a sample game state with typed models
        game_state = GameStateModel(
            campaign_id="test_campaign",
            current_location=LocationModel(
                name="Test Town", description="A peaceful town"
            ),
            party={
                "char1": CharacterInstanceModel(
                    template_id="template1",
                    campaign_id="test_campaign",
                    current_hp=20,
                    max_hp=20,
                    level=1,
                )
            },
            active_quests={
                "quest1": QuestModel(
                    id="quest1",
                    title="Test Quest",
                    description="A test quest",
                    status="active",
                )
            },
            known_npcs={},
            campaign_goal="Test the system",
        )

        # Mock game state repository
        game_state_repo = container.get_game_state_repository()
        with patch.object(game_state_repo, "get_game_state", return_value=game_state):
            # Trigger a game state snapshot event
            event_queue = container.get_event_queue()

            snapshot_event = create_game_state_snapshot_event(game_state, reason="test")
            event_queue.put_event(snapshot_event)

            # Verify the snapshot event has typed fields
            snapshot_events = [
                e
                for e in event_recorder.events
                if e.event_type == "game_state_snapshot"
            ]
            assert len(snapshot_events) > 0

            event_data = snapshot_events[-1]

            # The snapshot should have properly typed components
            if hasattr(event_data, "data"):
                # Location should be a LocationModel
                assert hasattr(event_data.data, "location")
                if event_data.data.location:
                    assert hasattr(event_data.data.location, "name")
                    assert hasattr(event_data.data.location, "description")

                # Party members should be CharacterInstanceModel
                assert hasattr(event_data.data, "party_members")

                # Quests should be QuestModel
                assert hasattr(event_data.data, "active_quests")

        print("\n✓ GameStateSnapshotEvent typing test passed!")

    def test_character_instance_template_integration(
        self, app_with_temp_dirs: Any, temp_save_dir: Dict[str, Path]
    ) -> None:
        """Test that CharacterInstance and CharacterTemplate work together properly."""

        # Get container from the app context
        from app.core.container import get_container

        container = get_container()

        # Create a character template
        template = CharacterTemplateModel(
            id="test_template",
            name="Test Character",
            race="Human",
            char_class="Fighter",
            level=5,
            background="Soldier",
            alignment="Lawful Good",
            base_stats=BaseStatsModel(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8),
            proficiencies=ProficienciesModel(),
            languages=["Common"],
            portrait_path="/test.png",
            starting_gold=100,
        )

        # Save template
        char_template_repo = container.get_character_template_repository()
        char_template_repo.save_template(template)

        # Create character instance
        from app.domain.characters.factories import CharacterFactory

        char_factory = CharacterFactory()
        instance = char_factory.from_template(template, "test_campaign")

        # Verify instance has correct data
        assert instance.template_id == template.id
        assert instance.campaign_id == "test_campaign"
        assert instance.current_hp > 0
        assert instance.max_hp > 0
        assert instance.level == template.level

        # Test character service integration
        char_service = container.get_character_service()

        # Mock the game state to include our character instance
        game_state_repo = container.get_game_state_repository()
        mock_game_state = MagicMock()
        mock_game_state.party = {"test_char": instance}

        # Need to patch the template_repo used by the service
        with patch.object(
            game_state_repo, "get_game_state", return_value=mock_game_state
        ):
            assert isinstance(char_service, CharacterServiceImpl)
            with patch.object(
                char_service.template_repo, "get_template", return_value=template
            ):
                # Get full character data
                char_data = char_service.get_character("test_char")

                # Should have both instance and template data
                assert char_data is not None
                assert char_data.template.name == template.name
                assert char_data.instance.current_hp == instance.current_hp
                assert char_data.template.race == template.race
                assert char_data.template.char_class == template.char_class

        print("\n✓ Character instance/template integration test passed!")
