"""
Unit tests for all game models (including combat models).
Tests the unified models that are now the single source of truth.
"""
import pytest
from pydantic import ValidationError
from app.game.unified_models import (
    BaseStatsModel, ProficienciesModel, CharacterTemplateModel,
    CharacterInstanceModel, NPCModel, QuestModel,
    CombatantModel, CombatStateModel, GameStateModel
)


class TestBaseStats:
    """Test BaseStatsModel."""
    
    def test_base_stats_creation(self):
        """Test base stats model creation."""
        stats = BaseStatsModel(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8)
        
        assert stats.STR == 16
        assert stats.DEX == 14
        assert stats.CON == 15
        assert stats.INT == 10
        assert stats.WIS == 12
        assert stats.CHA == 8


class TestProficiencies:
    """Test ProficienciesModel."""
    
    def test_proficiencies_creation(self):
        """Test proficiencies model creation."""
        prof = ProficienciesModel(
            armor=["Light armor"],
            weapons=["Simple weapons"],
            saving_throws=["DEX", "INT"],
            skills=["Stealth", "Investigation"]
        )
        
        assert "Light armor" in prof.armor
        assert "Simple weapons" in prof.weapons
        assert "DEX" in prof.saving_throws
        assert "Stealth" in prof.skills


class TestCharacterTemplate:
    """Test CharacterTemplateModel."""
    
    def test_character_template_creation(self):
        """Test character template model creation."""
        template = CharacterTemplateModel(
            id="test_char",
            name="Test Character",
            race="Human",
            char_class="Fighter",
            level=1,
            background="Soldier",
            alignment="Lawful Good",
            base_stats=BaseStatsModel(STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8),
            proficiencies=ProficienciesModel(
                armor=["Light armor", "Medium armor", "Heavy armor", "Shields"],
                weapons=["Simple weapons", "Martial weapons"],
                saving_throws=["STR", "CON"],
                skills=["Acrobatics", "Athletics"]
            )
        )
        
        assert template.name == "Test Character"
        assert template.race == "Human"
        assert template.char_class == "Fighter"
        assert template.level == 1
        assert template.base_stats.STR == 16


class TestCharacterInstance:
    """Test CharacterInstanceModel."""
    
    def test_character_instance_creation(self):
        """Test character instance model creation."""
        instance = CharacterInstanceModel(
            template_id="test_char",
            campaign_id="test_campaign",
            current_hp=20,
            max_hp=20,
            temp_hp=0,
            level=1,
            experience_points=0,
            spell_slots_used={},
            hit_dice_used=0,
            death_saves={"successes": 0, "failures": 0},
            inventory=[],
            gold=100,
            conditions=[],
            exhaustion_level=0,
            notes="",
            achievements=[],
            relationships={}
        )
        
        assert instance.current_hp == 20
        assert instance.max_hp == 20
        assert instance.gold == 100
        assert instance.gold == 100


class TestCombatant:
    """Test the enhanced CombatantModel model."""
    
    def test_combatant_creation_with_required_fields(self):
        """Test creating a combatant with all required fields."""
        combatant = CombatantModel(
            id="goblin_1",
            name="Goblin Archer",
            initiative=15,
            initiative_modifier=2,
            current_hp=7,
            max_hp=7,
            armor_class=13,
            is_player=False
        )
        
        assert combatant.id == "goblin_1"
        assert combatant.name == "Goblin Archer"
        assert combatant.initiative == 15
        assert combatant.initiative_modifier == 2
        assert combatant.current_hp == 7
        assert combatant.max_hp == 7
        assert combatant.armor_class == 13
        assert combatant.is_player is False
        assert combatant.conditions == []  # Default empty list
        assert combatant.icon_path is None  # Optional field
    
    def test_combatant_with_optional_fields(self):
        """Test creating a combatant with optional fields."""
        combatant = CombatantModel(
            id="pc_1",
            name="Elara",
            initiative=18,
            initiative_modifier=3,
            current_hp=25,
            max_hp=30,
            armor_class=16,
            is_player=True,
            conditions=["blessed", "inspired"],
            icon_path="/images/elara.png"
        )
        
        assert combatant.conditions == ["blessed", "inspired"]
        assert combatant.icon_path == "/images/elara.png"
    
    def test_combatant_validation_negative_hp(self):
        """Test that negative HP is not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            CombatantModel(
                id="test",
                name="Test",
                initiative=10,
                initiative_modifier=0,
                current_hp=-5,  # Invalid
                max_hp=10,
                armor_class=10,
                is_player=False
            )
        
        assert "current_hp" in str(exc_info.value)
    
    def test_combatant_validation_current_exceeds_max_hp(self):
        """Test that current HP cannot exceed max HP."""
        with pytest.raises(ValidationError) as exc_info:
            CombatantModel(
                id="test",
                name="Test",
                initiative=10,
                initiative_modifier=0,
                current_hp=20,  # Exceeds max
                max_hp=10,
                armor_class=10,
                is_player=False
            )
        
        assert "current_hp (20) cannot exceed max_hp (10)" in str(exc_info.value)
    
    def test_combatant_is_defeated_property(self):
        """Test the is_defeated property."""
        # Alive combatant
        alive = CombatantModel(
            id="test1",
            name="Alive",
            initiative=10,
            initiative_modifier=0,
            current_hp=5,
            max_hp=10,
            armor_class=10,
            is_player=False
        )
        assert alive.is_defeated is False
        
        # Defeated combatant
        defeated = CombatantModel(
            id="test2",
            name="Defeated",
            initiative=10,
            initiative_modifier=0,
            current_hp=0,
            max_hp=10,
            armor_class=10,
            is_player=False
        )
        assert defeated.is_defeated is True
    
    def test_combatant_is_incapacitated_property(self):
        """Test the is_incapacitated property."""
        # Normal combatant
        normal = CombatantModel(
            id="test1",
            name="Normal",
            initiative=10,
            initiative_modifier=0,
            current_hp=10,
            max_hp=10,
            armor_class=10,
            is_player=False
        )
        assert normal.is_incapacitated is False
        
        # Incapacitated by HP
        defeated = CombatantModel(
            id="test2",
            name="Defeated",
            initiative=10,
            initiative_modifier=0,
            current_hp=0,
            max_hp=10,
            armor_class=10,
            is_player=False
        )
        assert defeated.is_incapacitated is True
        
        # Incapacitated by condition
        stunned = CombatantModel(
            id="test3",
            name="Stunned",
            initiative=10,
            initiative_modifier=0,
            current_hp=10,
            max_hp=10,
            armor_class=10,
            is_player=False,
            conditions=["stunned"]
        )
        assert stunned.is_incapacitated is True


class TestCombatState:
    """Test the enhanced CombatStateModel model."""
    
    def test_combat_state_initialization(self):
        """Test creating a combat state with defaults."""
        combat = CombatStateModel()
        
        assert combat.is_active is False
        assert combat.combatants == []
        assert combat.current_turn_index == -1
        assert combat.round_number == 1
        assert combat.monster_stats == {}
    
    def test_combat_state_with_combatants(self):
        """Test creating a combat state with combatants."""
        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=7,
                max_hp=7,
                armor_class=13,
                is_player=False
            )
        ]
        
        combat = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=0,
            round_number=1
        )
        
        assert combat.is_active is True
        assert len(combat.combatants) == 2
        assert combat.combatants[0].name == "Elara"
        assert combat.current_turn_index == 0
    
    def test_combat_state_get_current_combatant(self):
        """Test getting the current combatant."""
        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=7,
                max_hp=7,
                armor_class=13,
                is_player=False
            )
        ]
        
        # Active combat with valid index
        combat = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=1
        )
        
        current = combat.get_current_combatant()
        assert current is not None
        assert current.name == "Goblin"
        
        # Inactive combat
        inactive_combat = CombatStateModel(is_active=False, combatants=combatants)
        assert inactive_combat.get_current_combatant() is None
        
        # Invalid index
        invalid_combat = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=5  # Out of bounds
        )
        assert invalid_combat.get_current_combatant() is None
    
    def test_combat_state_get_combatant_by_id(self):
        """Test finding a combatant by ID."""
        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=7,
                max_hp=7,
                armor_class=13,
                is_player=False
            )
        ]
        
        combat = CombatStateModel(combatants=combatants)
        
        # Find existing combatant
        goblin = combat.get_combatant_by_id("goblin_1")
        assert goblin is not None
        assert goblin.name == "Goblin"
        
        # Non-existent combatant
        assert combat.get_combatant_by_id("orc_1") is None
    
    def test_combat_state_is_players_turn(self):
        """Test checking if it's a player's turn."""
        combatants = [
            CombatantModel(
                id="pc_1",
                name="Elara",
                initiative=20,
                initiative_modifier=3,
                current_hp=25,
                max_hp=25,
                armor_class=16,
                is_player=True
            ),
            CombatantModel(
                id="goblin_1",
                name="Goblin",
                initiative=15,
                initiative_modifier=2,
                current_hp=7,
                max_hp=7,
                armor_class=13,
                is_player=False
            )
        ]
        
        # Player's turn
        combat_pc_turn = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=0
        )
        assert combat_pc_turn.is_players_turn is True
        
        # NPC's turn
        combat_npc_turn = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=1
        )
        assert combat_npc_turn.is_players_turn is False
        
        # Inactive combat
        inactive = CombatStateModel(
            is_active=False,
            combatants=combatants
        )
        assert inactive.is_players_turn is False
    
    def test_initiative_ordering_with_ties(self):
        """Test that combatants are ordered correctly with initiative ties."""
        combatants = [
            CombatantModel(
                id="pc_1",
                name="Low Init",
                initiative=10,
                initiative_modifier=1,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                is_player=True
            ),
            CombatantModel(
                id="pc_2",
                name="High Init High Dex",
                initiative=15,
                initiative_modifier=3,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                is_player=True
            ),
            CombatantModel(
                id="pc_3",
                name="High Init Low Dex",
                initiative=15,
                initiative_modifier=1,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                is_player=True
            ),
            CombatantModel(
                id="pc_4",
                name="Highest Init",
                initiative=20,
                initiative_modifier=2,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                is_player=True
            )
        ]
        
        combat = CombatStateModel(combatants=combatants)
        sorted_combatants = combat.get_initiative_order()
        
        # Should be ordered by initiative desc, then modifier desc
        assert sorted_combatants[0].name == "Highest Init"  # 20
        assert sorted_combatants[1].name == "High Init High Dex"  # 15, mod 3
        assert sorted_combatants[2].name == "High Init Low Dex"  # 15, mod 1
        assert sorted_combatants[3].name == "Low Init"  # 10
    
    def test_turn_advancement_skips_incapacitated(self):
        """Test that turn advancement skips incapacitated combatants."""
        combatants = [
            CombatantModel(
                id="pc_1",
                name="Active",
                initiative=20,
                initiative_modifier=2,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                is_player=True
            ),
            CombatantModel(
                id="pc_2",
                name="Defeated",
                initiative=15,
                initiative_modifier=1,
                current_hp=0,  # Defeated
                max_hp=20,
                armor_class=15,
                is_player=True
            ),
            CombatantModel(
                id="pc_3",
                name="Stunned",
                initiative=10,
                initiative_modifier=0,
                current_hp=20,
                max_hp=20,
                armor_class=15,
                is_player=True,
                conditions=["stunned"]  # Incapacitated
            ),
            CombatantModel(
                id="pc_4",
                name="Also Active",
                initiative=5,
                initiative_modifier=0,
                current_hp=15,
                max_hp=20,
                armor_class=15,
                is_player=True
            )
        ]
        
        combat = CombatStateModel(
            is_active=True,
            combatants=combatants,
            current_turn_index=0,
            round_number=1
        )
        
        # Advance from first active combatant
        next_index, new_round = combat.get_next_active_combatant_index()
        assert next_index == 3  # Should skip defeated and stunned
        assert new_round == 1  # Same round
        
        # Advance from last combatant
        combat.current_turn_index = 3
        next_index, new_round = combat.get_next_active_combatant_index()
        assert next_index == 0  # Back to first
        assert new_round == 2  # New round


class TestKnownNPC:
    """Test NPCModel model."""
    
    def test_known_npc_creation(self):
        """Test known NPC model creation."""
        npc = NPCModel(
            id="npc1",
            name="Test NPC",
            description="A test character",
            last_location="Test Town"
        )
        
        assert npc.id == "npc1"
        assert npc.name == "Test NPC"
        assert npc.description == "A test character"
        assert npc.last_location == "Test Town"


class TestQuest:
    """Test QuestModel model."""
    
    def test_quest_creation(self):
        """Test quest model creation."""
        quest = QuestModel(
            id="quest1",
            title="Test QuestModel",
            description="A test quest",
            status="active"
        )
        
        assert quest.id == "quest1"
        assert quest.title == "Test QuestModel"
        assert quest.status == "active"
        assert quest.description == "A test quest"


class TestGameState:
    """Test GameStateModel model."""
    
    def test_game_state_initialization(self):
        """Test game state model initialization."""
        game_state = GameStateModel()
        assert game_state.party is not None
        assert game_state.combat is not None
        assert game_state.chat_history is not None
        assert game_state.known_npcs is not None
        assert game_state.active_quests is not None
        assert game_state.world_lore is not None
        assert game_state.event_summary is not None
