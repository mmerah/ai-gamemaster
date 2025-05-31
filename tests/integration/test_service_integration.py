"""
Integration tests for service interactions.
"""
import unittest
from unittest.mock import Mock, patch
from tests.test_helpers import IsolatedTestCase, setup_test_environment
# Set up environment before importing app modules
setup_test_environment()
from app.core.container import ServiceContainer, reset_container
from app.core.interfaces import GameStateRepository
from tests.conftest import get_test_config


class TestServiceContainer(IsolatedTestCase, unittest.TestCase):
    """Test the service container functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.config = get_test_config()
        self.config['DEBUG'] = True
        # Ensure RAG is disabled for tests
        self.config['RAG_ENABLED'] = False
    
    def test_container_initialization(self):
        """Test that the container initializes properly."""
        container = ServiceContainer(self.config)
        container.initialize()
        
        # Test that all services are available
        self.assertIsNotNone(container.get_game_state_repository())
        self.assertIsNotNone(container.get_character_service())
        self.assertIsNotNone(container.get_dice_service())
        self.assertIsNotNone(container.get_combat_service())
        self.assertIsNotNone(container.get_chat_service())
        self.assertIsNotNone(container.get_ai_response_processor())
        self.assertIsNotNone(container.get_game_event_manager())
    
    def test_service_dependencies(self):
        """Test that services have proper dependencies injected."""
        container = ServiceContainer(self.config)
        container.initialize()
        
        # Test that services have the expected dependencies
        character_service = container.get_character_service()
        dice_service = container.get_dice_service()
        
        # These should have the same game state repository instance
        self.assertIs(
            character_service.game_state_repo,
            container.get_game_state_repository()
        )
        self.assertIs(
            dice_service.game_state_repo,
            container.get_game_state_repository()
        )
    
    def test_singleton_behavior(self):
        """Test that services are singletons within a container."""
        container = ServiceContainer(self.config)
        container.initialize()
        
        # Getting the same service twice should return the same instance
        repo1 = container.get_game_state_repository()
        repo2 = container.get_game_state_repository()
        self.assertIs(repo1, repo2)
    
    def test_container_reinitialization(self):
        """Test container behavior with reinitialization."""
        # Get original services
        container = ServiceContainer(self.config)
        container.initialize()
        original_repo = container.get_game_state_repository()
        
        # Reset and reinitialize
        reset_container()
        new_container = ServiceContainer(self.config)
        new_container.initialize()
        
        new_repo = new_container.get_game_state_repository()
        
        # Should be different instances
        self.assertIsNot(original_repo, new_repo)


class TestServiceIntegration(IsolatedTestCase, unittest.TestCase):
    """Test integration between multiple services."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer({
            'GAME_STATE_REPO_TYPE': 'memory',
            'TTS_PROVIDER': 'disabled',
            'RAG_ENABLED': False  # Disable RAG to avoid loading heavy ML dependencies
        })
        self.container.initialize()
    
    def test_character_service_with_dice_service(self):
        """Test character and dice service integration."""
        character_service = self.container.get_character_service()
        dice_service = self.container.get_dice_service()
        
        # Find a character
        char_id = character_service.find_character_by_name_or_id("Torvin Stonebeard")
        self.assertIsNotNone(char_id)
        
        # Use dice service with that character
        result = dice_service.perform_roll(
            character_id=char_id,
            roll_type="ability_check",
            dice_formula="1d20",
            reason="Strength check",
            ability="STR"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["character_id"], char_id)
    
    def test_combat_service_with_character_service(self):
        """Test combat and character service integration."""
        combat_service = self.container.get_combat_service()
        character_service = self.container.get_character_service()
        game_state_repo = self.container.get_game_state_repository()
        
        # Get current game state
        game_state = game_state_repo.get_game_state()
        
        # Start combat with CombatService interface
        from app.ai_services.schemas import InitialCombatantData
        monsters = [InitialCombatantData(id="goblin1", name="Goblin", hp=7, ac=15, stats={"DEX": 14})]
        updated_state = combat_service.start_combat(game_state, monsters)
        game_state_repo.save_game_state(updated_state)
        
        # Verify combat is active
        game_state = game_state_repo.get_game_state()
        self.assertTrue(game_state.combat.is_active)
        
        # Verify characters are still accessible
        char = character_service.get_character("char1")
        self.assertIsNotNone(char)
        
        # Check combat end conditions
        should_end = combat_service.check_combat_end_conditions(game_state)
        # Should not end yet as there are enemies
        self.assertFalse(should_end)
        
        # Characters should still be accessible
        char = character_service.get_character("char1")
        self.assertIsNotNone(char)
    
    def test_chat_service_integration(self):
        """Test chat service integration with other services."""
        chat_service = self.container.get_chat_service()
        character_service = self.container.get_character_service()
        
        # Add a message
        original_count = len(chat_service.get_chat_history())
        chat_service.add_message("user", "Hello!")
        
        # Verify message was added
        new_count = len(chat_service.get_chat_history())
        self.assertEqual(new_count, original_count + 1)
        
        # Character service should still work
        char = character_service.get_character("char1")
        self.assertIsNotNone(char)


if __name__ == '__main__':
    unittest.main()
