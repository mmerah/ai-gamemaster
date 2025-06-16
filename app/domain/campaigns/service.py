"""
Campaign service for managing campaigns and their lifecycle.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from app.content.service import ContentService
from app.domain.characters.factories import create_character_factory
from app.models.campaign import (
    CampaignInstanceModel,
    CampaignSummaryModel,
    CampaignTemplateModel,
)
from app.models.character import CharacterInstanceModel, CharacterTemplateModel
from app.models.combat import CombatStateModel
from app.models.game_state import GameStateModel
from app.repositories.game.campaign_instance_repository import (
    CampaignInstanceRepository,
)
from app.repositories.game.campaign_template_repository import (
    CampaignTemplateRepository,
)
from app.repositories.game.character_template_repository import (
    CharacterTemplateRepository,
)
from app.repositories.game.in_memory_campaign_instance_repository import (
    InMemoryCampaignInstanceRepository,
)

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing campaign operations."""

    def __init__(
        self,
        campaign_template_repo: CampaignTemplateRepository,
        character_template_repo: CharacterTemplateRepository,
        campaign_instance_repo: InMemoryCampaignInstanceRepository
        | CampaignInstanceRepository,
        content_service: ContentService,
    ):
        self.campaign_template_repo = campaign_template_repo
        self.character_template_repo = character_template_repo
        self.instance_repo = campaign_instance_repo
        self.content_service = content_service
        # Create character factory with content service
        self.character_factory = create_character_factory(content_service)

    def get_campaign(self, campaign_id: str) -> Optional[CampaignTemplateModel]:
        """Get a specific campaign by ID."""
        return self.campaign_template_repo.get_template(campaign_id)

    def create_campaign(
        self, campaign_template: CampaignTemplateModel
    ) -> Optional[CampaignTemplateModel]:
        """Create a new campaign template."""
        try:
            if self.campaign_template_repo.save_template(campaign_template):
                logger.info(f"Campaign {campaign_template.id} created successfully")
                return campaign_template
            else:
                logger.error(f"Failed to save campaign {campaign_template.id}")
                return None

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return None

    def update_campaign(self, campaign: CampaignTemplateModel) -> bool:
        """Update an existing campaign template."""
        try:
            return self.campaign_template_repo.save_template(campaign)

        except Exception as e:
            logger.error(f"Error updating campaign {campaign.id}: {e}")
            return False

    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign."""
        return self.campaign_template_repo.delete_template(campaign_id)

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
        self, template_id: str, instance_name: str, character_ids: List[str]
    ) -> Optional[CampaignInstanceModel]:
        """Create a new campaign instance from a template."""
        try:
            # Load the template
            template = self.campaign_template_repo.get_template(template_id)
            if not template:
                logger.error(f"Campaign template {template_id} not found")
                return None

            # Validate character templates exist
            template_validation_result = (
                self.character_template_repo.validate_template_ids(character_ids)
            )
            if hasattr(template_validation_result, "to_dict"):
                template_validation = template_validation_result.to_dict()
            elif hasattr(template_validation_result, "results"):
                # If it has results attribute, convert results list to dict
                template_validation = {
                    result.template_id: result.exists
                    for result in template_validation_result.results
                }
            else:
                # Fallback - assume empty validation
                template_validation = {}
            invalid_templates = [
                tid for tid, valid in template_validation.items() if not valid
            ]
            if invalid_templates:
                logger.error(f"Invalid character template IDs: {invalid_templates}")
                return None

            # Load character templates to get their content packs
            character_packs = []
            for char_id in character_ids:
                char_template = self.character_template_repo.get_template(char_id)
                if char_template:
                    character_packs.append(
                        getattr(char_template, "content_pack_ids", ["dnd_5e_srd"])
                    )

            # Merge content packs from campaign and characters
            merged_content_packs = self._merge_content_packs(
                getattr(template, "content_pack_ids", ["dnd_5e_srd"]), character_packs
            )

            # Create campaign instance
            instance_id = (
                f"{template_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            )
            event_log_path = os.path.join(
                self.instance_repo.base_dir, instance_id, "event_log.json"
            )

            campaign_instance = CampaignInstanceModel(
                id=instance_id,
                name=instance_name,
                template_id=template_id,
                character_ids=character_ids,
                current_location=template.starting_location.name,
                session_count=0,
                in_combat=False,
                event_summary=[],
                event_log_path=event_log_path,
                content_pack_priority=merged_content_packs,
                created_date=datetime.now(timezone.utc),
                last_played=datetime.now(timezone.utc),
            )

            # Save campaign instance to repository
            if self.instance_repo.create_instance(campaign_instance):
                logger.info(f"Campaign instance {instance_id} created successfully")
                return campaign_instance
            else:
                logger.error(f"Failed to save campaign instance {instance_id}")
                return None

        except Exception as e:
            logger.error(f"Error creating campaign instance: {e}")
            return None

    def start_campaign_from_template(
        self, template_id: str, instance_name: str, party_character_ids: List[str]
    ) -> Optional[GameStateModel]:
        """Create and start a new campaign instance from a template."""
        try:
            # Create campaign instance
            campaign_instance = self.create_campaign_instance(
                template_id, instance_name, party_character_ids
            )
            if not campaign_instance:
                return None

            # Load the template for additional data
            template = self.campaign_template_repo.get_template(template_id)
            if not template:
                logger.error(f"Campaign template {template_id} not found")
                return None

            # Load character templates for the party
            party_characters = {}
            for char_id in party_character_ids:
                char_template = self.character_template_repo.get_template(char_id)
                if char_template:
                    # Convert template to character instance
                    char_instance = self._template_to_character_instance(
                        char_template,
                        campaign_instance.id,
                        campaign_instance.content_pack_priority,
                    )
                    party_characters[char_id] = char_instance
                else:
                    logger.warning(f"Character template {char_id} not found")

            # Ensure event log directory and file exist
            event_log_dir = os.path.dirname(campaign_instance.event_log_path)
            os.makedirs(event_log_dir, exist_ok=True)
            if not os.path.exists(campaign_instance.event_log_path):
                try:
                    with open(
                        campaign_instance.event_log_path, "w", encoding="utf-8"
                    ) as f:
                        json.dump({"events": []}, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.error(
                        f"Failed to initialize event log for campaign {campaign_instance.id}: {e}"
                    )

            # Create initial chat history
            chat_history = []
            if template.opening_narrative:
                from app.models.game_state import ChatMessageModel

                chat_message = ChatMessageModel(
                    id=f"msg_{uuid4()}",
                    role="assistant",
                    content=template.opening_narrative,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    gm_thought="Campaign start. Setting initial scene.",
                )
                chat_history.append(chat_message)

            # Create GameStateModel directly
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

        except Exception as e:
            logger.error(f"Error starting campaign from template {template_id}: {e}")
            return None

    def start_campaign(
        self, campaign_id: str, party_character_ids: Optional[List[str]] = None
    ) -> Optional[GameStateModel]:
        """Start a campaign (backward compatibility method).

        This method handles both campaign instances and templates:
        - If campaign_id is an instance ID, loads that instance
        - If campaign_id is a template ID and party_character_ids provided, creates new instance
        - Otherwise treats as template view
        """
        # First check if this is a campaign instance
        instance = self.instance_repo.get_instance(campaign_id)
        if instance:
            # This is an instance - load its template and use its character IDs
            if not instance.template_id:
                logger.error(f"Campaign instance {campaign_id} has no template_id")
                return None
            template = self.campaign_template_repo.get_template(instance.template_id)
            if not template:
                logger.error(
                    f"Campaign template {instance.template_id} not found for instance {campaign_id}"
                )
                return None

            # Build the party characters
            party_characters = {}
            for char_id in instance.character_ids:
                char_template = self.character_template_repo.get_template(char_id)
                if char_template:
                    party_characters[char_id] = self._template_to_character_instance(
                        char_template, campaign_id, instance.content_pack_priority
                    )
                else:
                    logger.warning(
                        f"Character template {char_id} not found for campaign instance {campaign_id}"
                    )

            # Create initial chat history with opening narrative
            chat_history = []
            if template.opening_narrative:
                from app.models.game_state import ChatMessageModel

                chat_message = ChatMessageModel(
                    id=f"msg_{uuid4()}",
                    role="assistant",
                    content=template.opening_narrative,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    gm_thought="Campaign start. Setting initial scene.",
                )
                chat_history.append(chat_message)

            # Create GameStateModel for compatibility
            game_state = GameStateModel(
                campaign_id=instance.id,
                campaign_name=instance.name,
                party=party_characters,
                current_location=template.starting_location,
                campaign_goal=template.campaign_goal,
                known_npcs=template.initial_npcs,
                active_quests=template.initial_quests,
                world_lore=template.world_lore,
                event_summary=instance.event_summary,
                narration_enabled=(
                    instance.narration_enabled
                    if instance.narration_enabled is not None
                    else template.narration_enabled
                ),
                tts_voice=instance.tts_voice or template.tts_voice,
                active_ruleset_id=getattr(template, "ruleset_id", None),
                active_lore_id=getattr(template, "lore_id", None),
                event_log_path=instance.event_log_path,
                chat_history=chat_history,
                pending_player_dice_requests=[],
                combat=CombatStateModel(),
                content_pack_priority=instance.content_pack_priority,
            )
            return game_state

        elif party_character_ids:
            # Create a new instance from template
            instance_name = (
                f"Adventure - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
            )
            return self.start_campaign_from_template(
                campaign_id, instance_name, party_character_ids
            )
        else:
            # Try to load as a template and return minimal state
            try:
                template = self.campaign_template_repo.get_template(campaign_id)
                if not template:
                    logger.error(f"Campaign template {campaign_id} not found")
                    return None

                # Return minimal state for template viewing
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
                    combat=CombatStateModel(),
                )
                return game_state
            except Exception as e:
                logger.error(f"Error starting campaign {campaign_id}: {e}")
                return None

    def get_campaign_summary(self, campaign_id: str) -> Optional[CampaignSummaryModel]:
        """Get a summary of campaign progress."""
        try:
            campaign = self.campaign_template_repo.get_template(campaign_id)
            if not campaign:
                return None

            # TODO: Load actual game state to get current progress
            # For now, return basic campaign info
            return CampaignSummaryModel(
                id=campaign.id,
                name=campaign.name,
                description=campaign.description,
                starting_level=campaign.starting_level,
                difficulty=campaign.difficulty,
                created_date=campaign.created_date,
                last_modified=campaign.last_modified,
            )

        except Exception as e:
            logger.error(f"Error getting campaign summary for {campaign_id}: {e}")
            return None

    def _template_to_character_instance(
        self,
        template: CharacterTemplateModel,
        campaign_id: str = "default",
        content_pack_priority: Optional[List[str]] = None,
    ) -> CharacterInstanceModel:
        """Convert a character template to a character instance for the game."""
        # Use the character factory for conversion
        return self.character_factory.from_template(
            template, campaign_id, content_pack_priority
        )
