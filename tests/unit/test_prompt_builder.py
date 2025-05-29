"""
Tests for the PromptBuilder.
"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.game.prompt_builder import PromptBuilder, build_ai_prompt_context
from app.game.models import GameState, CombatState, CharacterInstance, KnownNPC, Quest
from app.game import initial_data


class TestPromptBuilder:
    """Test cases for PromptBuilder."""
    
    @pytest.fixture
    def mock_game_state(self):
        """Create a mock GameState with test data."""
        state = Mock(spec=GameState)
        
        # Basic attributes
        state.campaign_id = "test_campaign"
        state.campaign_goal = "Test the prompt builder"
        state.world_lore = ["Ancient magic exists", "Dragons rule the mountains"]
        state.event_summary = ["Party defeated goblins", "Found mysterious artifact"]
        
        # Location
        state.current_location = {
            "name": "Mystic Forest",
            "description": "A dark forest filled with ancient trees"
        }
        
        # Party members
        char1 = Mock(spec=CharacterInstance)
        char1.id = "player1"
        char1.name = "Thorin"
        char1.race = "Dwarf"
        char1.char_class = "Fighter"
        char1.level = 5
        char1.current_hp = 35
        char1.max_hp = 45
        char1.armor_class = 18
        char1.temporary_hp = 0
        char1.conditions = []
        
        char2 = Mock(spec=CharacterInstance)
        char2.id = "player2"
        char2.name = "Elara"
        char2.race = "Elf"
        char2.char_class = "Wizard"
        char2.level = 5
        char2.current_hp = 20
        char2.max_hp = 28
        char2.armor_class = 13
        char2.temporary_hp = 5
        char2.conditions = ["Blessed"]
        
        state.party = {"player1": char1, "player2": char2}
        
        # NPCs
        npc1 = Mock(spec=KnownNPC)
        npc1.id = "npc1"
        npc1.name = "Gandor the Wise"
        npc1.description = "An old wizard with knowledge of ancient lore"
        npc1.last_location = "Village Inn"
        
        state.known_npcs = {"npc1": npc1}
        
        # Quests
        quest1 = Mock(spec=Quest)
        quest1.id = "quest1"
        quest1.title = "Find the Lost Amulet"
        quest1.description = "Retrieve the ancient amulet from the goblin caves"
        quest1.status = "active"
        
        quest2 = Mock(spec=Quest)
        quest2.id = "quest2"
        quest2.title = "Defeat the Dragon"
        quest2.description = "Slay the dragon terrorizing the village"
        quest2.status = "completed"
        
        state.active_quests = {"quest1": quest1, "quest2": quest2}
        
        # Combat state
        combat = Mock(spec=CombatState)
        combat.is_active = False
        combat.round_number = 0
        combat.combatants = []
        combat.current_turn_index = 0
        combat.monster_stats = {}
        state.combat = combat
        
        # Chat history - reflects actual game structure
        state.chat_history = [
            {"role": "user", "content": "I look around the forest"},
            {"role": "assistant", "content": "You see ancient trees towering above", 
             "ai_response_json": '{"narrative": "You see ancient trees towering above", "dice_requests": []}'},
            {"role": "user", "content": "I search for clues"},
            {"role": "user", "content": "**Thorin Rolls Submitted:**\nPerception Check: 15 (Success)", 
             "is_dice_result": True,
             "detailed_content": "**Thorin Rolls Submitted:**\nPerception Check: 1d20+3 = 12+3 = 15 vs DC 10 (Success)"},
        ]
        
        return state
    
    @pytest.fixture
    def mock_handler(self):
        """Create a mock handler with necessary attributes."""
        handler = Mock()
        handler.character_service = Mock()
        handler.character_service.get_character.return_value = None
        handler.rag_service = None  # No RAG by default
        return handler
    
    @pytest.fixture
    def builder(self):
        """Create a PromptBuilder instance."""
        return PromptBuilder()
    
    def test_initialization(self, builder):
        """Test that the builder initializes correctly."""
        assert builder.prompt_template is not None
        assert len(builder.prompt_template.messages) == 6  # System + 5 placeholders
    
    def test_format_character_for_prompt(self, builder, mock_game_state):
        """Test character formatting."""
        char = mock_game_state.party["player1"]
        result = builder.format_character_for_prompt(char)
        
        assert "ID: player1" in result
        assert "Name: Thorin" in result
        assert "Dwarf Fighter 5" in result
        assert "HP: 35/45" in result
        assert "AC: 18" in result
    
    def test_format_character_with_conditions(self, builder, mock_game_state):
        """Test character formatting with conditions and temp HP."""
        char = mock_game_state.party["player2"]
        result = builder.format_character_for_prompt(char)
        
        assert "Temp HP: 5" in result
        assert "Conditions: Blessed" in result
    
    def test_format_combat_state_inactive(self, builder, mock_game_state, mock_handler):
        """Test combat state formatting when combat is not active."""
        result = builder.format_combat_state_for_prompt(mock_game_state.combat, mock_handler)
        assert result == "Combat Status: Not Active"
    
    def test_format_combat_state_active(self, builder, mock_handler):
        """Test combat state formatting during active combat."""
        # Create active combat state
        combat = Mock(spec=CombatState)
        combat.is_active = True
        combat.round_number = 3
        combat.current_turn_index = 1
        
        # Create combatants
        combatant1 = Mock()
        combatant1.id = "goblin1"
        combatant1.name = "Goblin Warrior"
        combatant1.initiative = 15
        
        combatant2 = Mock()
        combatant2.id = "player1"
        combatant2.name = "Thorin"
        combatant2.initiative = 12
        
        combat.combatants = [combatant1, combatant2]
        combat.monster_stats = {
            "goblin1": {
                "hp": 10,
                "initial_hp": 15,
                "conditions": []
            }
        }
        
        result = builder.format_combat_state_for_prompt(combat, mock_handler)
        
        assert "Combat Status: Active" in result
        assert "Round: 3" in result
        assert "Current Turn: Thorin" in result
        assert "-> " in result  # Current turn indicator
        assert "Goblin Warrior" in result
        assert "HP: 10/15" in result
    
    def test_format_known_npcs(self, builder, mock_game_state):
        """Test NPC formatting."""
        result = builder.format_known_npcs(mock_game_state.known_npcs)
        
        assert "Known NPCs:" in result
        assert "Gandor the Wise" in result
        assert "An old wizard" in result
        assert "Last Seen: Village Inn" in result
    
    def test_format_known_npcs_empty(self, builder):
        """Test NPC formatting with no NPCs."""
        result = builder.format_known_npcs({})
        assert result == "Known NPCs: None"
    
    def test_format_active_quests(self, builder, mock_game_state):
        """Test quest formatting."""
        result = builder.format_active_quests(mock_game_state.active_quests)
        
        assert "Active Quests:" in result
        assert "Find the Lost Amulet" in result
        assert "quest1" in result
        # Completed quest should not appear
        assert "Defeat the Dragon" not in result
    
    def test_format_list_context(self, builder):
        """Test list context formatting."""
        items = ["First item", "Second item", "Third item"]
        result = builder.format_list_context("Test List", items)
        
        assert "Test List:" in result
        assert "- First item" in result
        assert "- Second item" in result
        assert "- Third item" in result
    
    def test_format_list_context_empty(self, builder):
        """Test list context formatting with empty list."""
        result = builder.format_list_context("Empty List", [])
        assert result == "Empty List: None"
    
    def test_format_message_for_history_user(self, builder):
        """Test formatting user messages."""
        msg = {"role": "user", "content": "Hello world"}
        result = builder._format_message_for_history(msg)
        
        assert isinstance(result, HumanMessage)
        assert result.content == "Hello world"
    
    def test_format_message_for_history_assistant(self, builder):
        """Test formatting assistant messages with AI response JSON."""
        msg = {
            "role": "assistant",
            "content": "Simple content",
            "ai_response_json": '{"narrative": "Full JSON response"}'
        }
        result = builder._format_message_for_history(msg)
        
        assert isinstance(result, AIMessage)
        assert result.content == '{"narrative": "Full JSON response"}'
    
    def test_format_message_for_history_skip_error(self, builder):
        """Test that system error messages are skipped."""
        # System error messages with is_dice_result=True and starting with "(Error" are filtered
        msg = {
            "role": "system",
            "content": "(Error: Something went wrong)",
            "is_dice_result": True
        }
        result = builder._format_message_for_history(msg)
        
        assert result is None
        
        # But dice results as user messages should not be filtered
        dice_msg = {
            "role": "user",
            "content": "**Player Rolls Submitted:**\nAttack: 18",
            "is_dice_result": True
        }
        dice_result = builder._format_message_for_history(dice_msg)
        
        assert dice_result is not None
        assert isinstance(dice_result, HumanMessage)
        assert "Player Rolls Submitted" in dice_result.content
    
    @patch('app.services.rag.rag_context_builder.rag_context_builder.get_rag_context_for_prompt')
    def test_build_ai_prompt_context_basic(self, mock_rag_func, builder, mock_game_state, mock_handler):
        """Test basic prompt building."""
        # Mock RAG context
        mock_rag_func.return_value = None
        
        # Mock system prompt
        with patch.object(initial_data, 'SYSTEM_PROMPT', 'You are a game master'):
            result = builder.build_ai_prompt_context(mock_game_state, mock_handler)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check system message
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a game master"
        
        # Check for context sections
        content_str = " ".join(msg["content"] for msg in result)
        assert "Campaign Goal: Test the prompt builder" in content_str
        assert "World Lore:" in content_str
        assert "Ancient magic exists" in content_str
        assert "Active Quests:" in content_str
        assert "Known NPCs:" in content_str
        assert "Party Members & Status:" in content_str
        assert "Current Location: Mystic Forest" in content_str
        assert "Combat Status: Not Active" in content_str
    
    @patch('app.services.rag.rag_context_builder.rag_context_builder.get_rag_context_for_prompt')
    def test_build_ai_prompt_context_with_rag(self, mock_rag_func, builder, mock_game_state, mock_handler):
        """Test prompt building with RAG context."""
        # Mock RAG context
        mock_rag_func.return_value = "RAG CONTEXT:\nRelevant rules about combat"
        
        with patch.object(initial_data, 'SYSTEM_PROMPT', 'You are a game master'):
            result = builder.build_ai_prompt_context(mock_game_state, mock_handler, "I attack the goblin")
        
        # Check that RAG context is included
        rag_messages = [msg for msg in result if "RAG CONTEXT:" in msg.get("content", "")]
        assert len(rag_messages) == 1
        assert "Relevant rules about combat" in rag_messages[0]["content"]
        
        # Verify RAG was called with correct parameters
        mock_rag_func.assert_called_once_with(
            mock_game_state,
            None,  # handler.rag_service
            "I attack the goblin",
            mock_game_state.chat_history,
            True  # force_new_query because player_action_input is provided
        )
    
    @patch('app.game.prompt_builder.trim_messages')
    @patch('app.services.rag.rag_context_builder.rag_context_builder.get_rag_context_for_prompt')
    def test_build_ai_prompt_context_token_truncation(self, mock_rag_func, mock_trim, builder, mock_game_state, mock_handler):
        """Test that messages are truncated based on token budget."""
        # Add more chat history
        mock_game_state.chat_history = [
            {"role": "user", "content": f"Message {i}"} for i in range(20)
        ]
        
        # Mock RAG
        mock_rag_func.return_value = None
        
        # Mock trim_messages to simulate truncation
        def mock_trim_side_effect(messages, **kwargs):
            # Return only last 5 messages
            return messages[-5:] if len(messages) > 5 else messages
        
        mock_trim.side_effect = mock_trim_side_effect
        
        with patch.object(initial_data, 'SYSTEM_PROMPT', 'You are a game master'):
            result = builder.build_ai_prompt_context(mock_game_state, mock_handler)
        
        # Verify trim_messages was called
        assert mock_trim.called
        
        # Check result structure
        assert isinstance(result, list)
        assert result[0]["role"] == "system"
    
    def test_build_ai_prompt_context_empty_history(self, builder, mock_handler):
        """Test prompt building with minimal game state."""
        # Create minimal game state
        state = Mock(spec=GameState)
        state.campaign_id = "test"
        state.campaign_goal = "Test"
        state.world_lore = []
        state.event_summary = []
        state.current_location = {"name": "Start", "description": "Beginning"}
        state.party = {}
        state.known_npcs = {}
        state.active_quests = {}
        state.chat_history = []
        
        combat = Mock(spec=CombatState)
        combat.is_active = False
        state.combat = combat
        
        with patch('app.services.rag.rag_context_builder.rag_context_builder.get_rag_context_for_prompt') as mock_rag:
            mock_rag.return_value = None
            with patch.object(initial_data, 'SYSTEM_PROMPT', 'System'):
                result = builder.build_ai_prompt_context(state, mock_handler)
        
        assert len(result) >= 2  # At least system + dynamic context
        assert result[0]["role"] == "system"
    
    def test_module_level_function(self, mock_game_state, mock_handler):
        """Test the module-level backward compatibility function."""
        with patch('app.services.rag.rag_context_builder.rag_context_builder.get_rag_context_for_prompt') as mock_rag:
            mock_rag.return_value = None
            with patch.object(initial_data, 'SYSTEM_PROMPT', 'System'):
                # Use the module-level function
                result = build_ai_prompt_context(mock_game_state, mock_handler)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["role"] == "system"
    
    def test_calculate_message_tokens_with_tokenizer(self, builder):
        """Test token calculation when tokenizer is available."""
        msg = HumanMessage(content="Hello world")
        
        with patch('app.game.prompt_builder.tokenizer') as mock_tokenizer:
            mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
            result = builder._calculate_message_tokens(msg)
        
        assert result == 5 + 4  # 5 tokens + 4 overhead
    
    def test_calculate_message_tokens_no_tokenizer(self, builder):
        """Test token calculation when tokenizer is not available."""
        msg = HumanMessage(content="Hello world")
        
        with patch('app.game.prompt_builder.tokenizer', None):
            result = builder._calculate_message_tokens(msg)
        
        assert result == 0
    
    def test_chat_history_truncation(self, builder, mock_handler):
        """Test that chat history is properly split into main and recent."""
        state = Mock(spec=GameState)
        state.campaign_id = "test"
        state.campaign_goal = "Test"
        state.world_lore = []
        state.event_summary = []
        state.current_location = {"name": "Start", "description": "Beginning"}
        state.party = {}
        state.known_npcs = {}
        state.active_quests = {}
        
        # Create chat history with more than LAST_X_HISTORY_MESSAGES
        state.chat_history = [
            {"role": "user", "content": f"Old message {i}"} for i in range(10)
        ]
        
        combat = Mock(spec=CombatState)
        combat.is_active = False
        state.combat = combat
        
        with patch('app.services.rag.rag_context_builder.rag_context_builder.get_rag_context_for_prompt') as mock_rag:
            mock_rag.return_value = None
            with patch.object(initial_data, 'SYSTEM_PROMPT', 'System'):
                result = builder.build_ai_prompt_context(state, mock_handler)
        
        # Check that recent messages (last 4) are in the result
        content_str = " ".join(msg["content"] for msg in result)
        assert "Old message 9" in content_str  # Most recent
        assert "Old message 8" in content_str
        assert "Old message 7" in content_str
        assert "Old message 6" in content_str