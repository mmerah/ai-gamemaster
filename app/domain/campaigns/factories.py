"""
Factory for creating campaign instances and initial game states.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from app.content.service import ContentService
from app.domain.characters.factories import CharacterFactory
from app.models.campaign import CampaignInstanceModel, CampaignTemplateModel
from app.models.character import CharacterInstanceModel
from app.models.combat import CombatStateModel
from app.models.game_state import ChatMessageModel, GameStateModel

logger = logging.getLogger(__name__)


class CampaignFactory:
    """Factory for creating campaign-related objects."""

    def __init__(
        self, content_service: ContentService, character_factory: CharacterFactory
    ):
        """
        Initialize the campaign factory with required services.

        Args:
            content_service: Service for accessing D&D 5e content
            character_factory: Factory for creating character instances
        """
        self.content_service = content_service
        self.character_factory = character_factory

    def _generate_id(self) -> str:
        """Generate a unique ID for new objects."""
        return str(uuid4())

    def _merge_content_packs(
        self,
        campaign_packs: List[str],
        character_packs: List[List[str]],
    ) -> List[str]:
        """Merge content packs from campaign template and character templates.

        The priority order is:
        1. Campaign template content packs (highest priority)
        2. Character template content packs (in order they appear)
        3. System default (dnd_5e_srd) if not already included

        Args:
            campaign_packs: Content pack IDs from the campaign template
            character_packs: List of content pack IDs from each character template

        Returns:
            Merged list of content pack IDs in priority order
        """
        merged_packs: List[str] = []
        seen_packs = set()

        # Add campaign packs first (highest priority)
        for pack_id in campaign_packs:
            if pack_id not in seen_packs:
                merged_packs.append(pack_id)
                seen_packs.add(pack_id)

        # Add character packs
        for char_packs in character_packs:
            for pack_id in char_packs:
                if pack_id not in seen_packs:
                    merged_packs.append(pack_id)
                    seen_packs.add(pack_id)

        # Ensure dnd_5e_srd is always included as a fallback
        if "dnd_5e_srd" not in seen_packs:
            merged_packs.append("dnd_5e_srd")

        return merged_packs

    def create_campaign_instance(
        self,
        template: CampaignTemplateModel,
        instance_name: Optional[str] = None,
        character_content_packs: Optional[List[List[str]]] = None,
    ) -> CampaignInstanceModel:
        """Create a campaign instance from a template.

        Args:
            template: The campaign template to create an instance from
            instance_name: Optional name for the instance, defaults to "{template.name} Campaign"
            character_content_packs: Optional list of content pack lists from characters

        Returns:
            A new campaign instance
        """
        # Generate instance ID
        instance_id = (
            f"{template.id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )

        # Merge content packs
        campaign_packs = getattr(template, "content_pack_ids", ["dnd_5e_srd"])
        merged_content_packs = self._merge_content_packs(
            campaign_packs, character_content_packs or []
        )

        # Create instance
        instance = CampaignInstanceModel(
            id=instance_id,
            name=instance_name or f"{template.name} Campaign",
            template_id=template.id,
            character_ids=[],  # Will be set by the service
            current_location=template.starting_location.name,
            session_count=0,
            in_combat=False,
            event_summary=[],
            event_log_path=f"campaigns/{instance_id}/event_log.json",
            content_pack_priority=merged_content_packs,
            created_date=datetime.now(timezone.utc),
            last_played=datetime.now(timezone.utc),
            # TTS settings from template (can be overridden at instance level)
            narration_enabled=template.narration_enabled,
            tts_voice=template.tts_voice,
        )

        return instance

    def create_initial_game_state(
        self,
        campaign_instance: CampaignInstanceModel,
        template: CampaignTemplateModel,
        party_characters: Dict[str, CharacterInstanceModel],
    ) -> GameStateModel:
        """Create initial game state for a new campaign.

        Args:
            campaign_instance: The campaign instance
            template: The campaign template
            party_characters: Dictionary of character ID to character instance

        Returns:
            Initial game state for the campaign
        """
        # Create initial chat history
        chat_history = []
        if template.opening_narrative:
            chat_message = ChatMessageModel(
                id=f"msg_{self._generate_id()}",
                role="assistant",
                content=template.opening_narrative,
                timestamp=datetime.now(timezone.utc).isoformat(),
                gm_thought="Campaign start. Setting initial scene.",
            )
            chat_history.append(chat_message)

        # Create game state
        game_state = GameStateModel(
            campaign_id=campaign_instance.id,
            campaign_name=campaign_instance.name,
            party=party_characters,
            current_location=template.starting_location,
            campaign_goal=template.campaign_goal,
            known_npcs=template.initial_npcs,
            active_quests=template.initial_quests,
            world_lore=template.world_lore,
            event_summary=campaign_instance.event_summary,
            # TTS settings hierarchy: instance override > template default
            narration_enabled=(
                campaign_instance.narration_enabled
                if campaign_instance.narration_enabled is not None
                else template.narration_enabled
            ),
            tts_voice=campaign_instance.tts_voice or template.tts_voice,
            active_ruleset_id=getattr(template, "ruleset_id", None),
            active_lore_id=getattr(template, "lore_id", None),
            event_log_path=campaign_instance.event_log_path,
            chat_history=chat_history,
            pending_player_dice_requests=[],
            combat=CombatStateModel(
                is_active=False, combatants=[], current_turn_index=0, round_number=1
            ),
            content_pack_priority=campaign_instance.content_pack_priority,
        )

        return game_state

    def create_game_state_from_instance(
        self,
        campaign_instance: CampaignInstanceModel,
        template: CampaignTemplateModel,
        party_characters: Dict[str, CharacterInstanceModel],
    ) -> GameStateModel:
        """Create game state from an existing campaign instance.

        This is used when loading a saved campaign instance.

        Args:
            campaign_instance: The existing campaign instance
            template: The campaign template
            party_characters: Dictionary of character ID to character instance

        Returns:
            Game state for the campaign instance
        """
        # Create initial chat history with opening narrative if needed
        chat_history = []
        if template.opening_narrative:
            chat_message = ChatMessageModel(
                id=f"msg_{self._generate_id()}",
                role="assistant",
                content=template.opening_narrative,
                timestamp=datetime.now(timezone.utc).isoformat(),
                gm_thought="Campaign start. Setting initial scene.",
            )
            chat_history.append(chat_message)

        # Create game state
        game_state = GameStateModel(
            campaign_id=campaign_instance.id,
            campaign_name=campaign_instance.name,
            party=party_characters,
            current_location=template.starting_location,
            campaign_goal=template.campaign_goal,
            known_npcs=template.initial_npcs,
            active_quests=template.initial_quests,
            world_lore=template.world_lore,
            event_summary=campaign_instance.event_summary,
            narration_enabled=(
                campaign_instance.narration_enabled
                if campaign_instance.narration_enabled is not None
                else template.narration_enabled
            ),
            tts_voice=campaign_instance.tts_voice or template.tts_voice,
            active_ruleset_id=getattr(template, "ruleset_id", None),
            active_lore_id=getattr(template, "lore_id", None),
            event_log_path=campaign_instance.event_log_path,
            chat_history=chat_history,
            pending_player_dice_requests=[],
            combat=CombatStateModel(
                is_active=False, combatants=[], current_turn_index=0, round_number=1
            ),
            content_pack_priority=campaign_instance.content_pack_priority,
        )

        return game_state

    def create_template_preview_state(
        self, template: CampaignTemplateModel
    ) -> GameStateModel:
        """Create a minimal game state for template preview.

        This is used when viewing a campaign template without starting an instance.

        Args:
            template: The campaign template to preview

        Returns:
            Minimal game state for template viewing
        """
        game_state = GameStateModel(
            campaign_id=template.id,
            campaign_name=template.name,
            party={},
            current_location=template.starting_location,
            campaign_goal=template.campaign_goal,
            known_npcs=template.initial_npcs,
            active_quests=template.initial_quests,
            world_lore=template.world_lore,
            event_summary=[],
            narration_enabled=template.narration_enabled,
            tts_voice=template.tts_voice,
            active_ruleset_id=getattr(template, "ruleset_id", None),
            active_lore_id=getattr(template, "lore_id", None),
            event_log_path=None,
            chat_history=[],
            pending_player_dice_requests=[],
            combat=CombatStateModel(
                is_active=False, combatants=[], current_turn_index=0, round_number=1
            ),
            content_pack_priority=getattr(template, "content_pack_ids", ["dnd_5e_srd"]),
        )

        return game_state
