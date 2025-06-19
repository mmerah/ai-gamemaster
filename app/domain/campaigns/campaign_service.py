"""
Campaign service for managing campaigns and their lifecycle.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.content.service import ContentService
from app.core.domain_interfaces import ICampaignService
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICampaignTemplateRepository,
    ICharacterTemplateRepository,
)
from app.domain.campaigns.campaign_factory import CampaignFactory
from app.domain.characters.character_factory import CharacterFactory
from app.models.campaign import (
    CampaignInstanceModel,
)
from app.models.game_state import GameStateModel

logger = logging.getLogger(__name__)


class CampaignService(ICampaignService):
    """Service for managing campaign operations."""

    def __init__(
        self,
        campaign_factory: CampaignFactory,
        character_factory: CharacterFactory,
        campaign_template_repo: ICampaignTemplateRepository,
        character_template_repo: ICharacterTemplateRepository,
        campaign_instance_repo: ICampaignInstanceRepository,
        content_service: ContentService,
    ):
        self.campaign_factory = campaign_factory
        self.character_factory = character_factory
        self.campaign_template_repo = campaign_template_repo
        self.character_template_repo = character_template_repo
        self.instance_repo = campaign_instance_repo
        self.content_service = content_service

    def create_campaign_instance(
        self, template_id: str, instance_name: str, character_ids: List[str]
    ) -> Optional[CampaignInstanceModel]:
        """Create a new campaign instance from a template."""
        try:
            # Load the template
            template = self.campaign_template_repo.get(template_id)
            if not template:
                logger.error(f"Campaign template {template_id} not found")
                return None

            # Validate character templates exist by trying to get each one
            invalid_templates = []
            for char_id in character_ids:
                if not self.character_template_repo.get(char_id):
                    invalid_templates.append(char_id)
            if invalid_templates:
                logger.error(f"Invalid character template IDs: {invalid_templates}")
                return None

            # Load character templates to get their content packs
            character_packs = []
            for char_id in character_ids:
                char_template = self.character_template_repo.get(char_id)
                if char_template:
                    character_packs.append(
                        getattr(char_template, "content_pack_ids", ["dnd_5e_srd"])
                    )

            # Use factory to create campaign instance
            campaign_instance = self.campaign_factory.create_campaign_instance(
                template, instance_name, character_packs
            )

            # Set the character IDs
            campaign_instance.character_ids = character_ids

            # Save campaign instance to repository
            if self.instance_repo.save(campaign_instance):
                logger.info(
                    f"Campaign instance {campaign_instance.id} created successfully"
                )
                return campaign_instance
            else:
                logger.error(f"Failed to save campaign instance {campaign_instance.id}")
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
            template = self.campaign_template_repo.get(template_id)
            if not template:
                logger.error(f"Campaign template {template_id} not found")
                return None

            # Load character templates for the party
            party_characters = {}
            for char_id in party_character_ids:
                char_template = self.character_template_repo.get(char_id)
                if char_template:
                    # Convert template to character instance using factory
                    char_instance = self.character_factory.from_template(
                        char_template,
                        campaign_instance.id,
                        campaign_instance.content_pack_priority,
                    )
                    party_characters[char_id] = char_instance
                else:
                    logger.warning(f"Character template {char_id} not found")

            # Event log initialization should be handled by the repository or event system
            logger.debug(f"Event log path set to: {campaign_instance.event_log_path}")

            # Use factory to create initial game state
            game_state = self.campaign_factory.create_initial_game_state(
                campaign_instance, template, party_characters
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
        instance = self.instance_repo.get(campaign_id)
        if instance:
            # This is an instance - load its template and use its character IDs
            if not instance.template_id:
                logger.error(f"Campaign instance {campaign_id} has no template_id")
                return None
            template = self.campaign_template_repo.get(instance.template_id)
            if not template:
                logger.error(
                    f"Campaign template {instance.template_id} not found for instance {campaign_id}"
                )
                return None

            # Build the party characters
            party_characters = {}
            for char_id in instance.character_ids:
                char_template = self.character_template_repo.get(char_id)
                if char_template:
                    party_characters[char_id] = self.character_factory.from_template(
                        char_template, campaign_id, instance.content_pack_priority
                    )
                else:
                    logger.warning(
                        f"Character template {char_id} not found for campaign instance {campaign_id}"
                    )

            # Use factory to create game state from instance
            game_state = self.campaign_factory.create_game_state_from_instance(
                instance, template, party_characters
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
                template = self.campaign_template_repo.get(campaign_id)
                if not template:
                    logger.error(f"Campaign template {campaign_id} not found")
                    return None

                # Use factory to create template preview state
                game_state = self.campaign_factory.create_template_preview_state(
                    template
                )
                return game_state
            except Exception as e:
                logger.error(f"Error starting campaign {campaign_id}: {e}")
                return None

    def get_character_template_repository(self) -> ICharacterTemplateRepository:
        """Get the character template repository.

        Returns:
            Character template repository instance
        """
        return self.character_template_repo
