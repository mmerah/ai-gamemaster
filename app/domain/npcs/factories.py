"""
Factory for creating NPC-related objects.

This module provides the NPCFactory class for creating NPCs.

NOTE: This factory is currently not integrated into the application flow.
NPCs are currently created directly by the AI response processing system
as part of the dynamic game narrative. This factory is maintained for
future use when NPC creation is refactored to be more structured and
separated from AI response handling.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from app.content.service import ContentService
from app.models.utils import NPCModel

logger = logging.getLogger(__name__)


class NPCFactory:
    """Factory for creating NPCs."""

    def __init__(self, content_service: ContentService):
        """
        Initialize the NPC factory.

        Args:
            content_service: Service for accessing D&D 5e content
        """
        self.content_service = content_service

    def create_npc(
        self,
        name: str,
        description: str,
        last_location: str = "Unknown",
        npc_id: Optional[str] = None,
        content_pack_priority: Optional[List[str]] = None,
    ) -> NPCModel:
        """
        Create a new NPC.

        Args:
            name: The NPC's name
            description: The NPC's description
            last_location: The NPC's last known location
            npc_id: Optional NPC ID, will generate if not provided
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            NPCModel: The newly created NPC
        """
        try:
            # Generate ID if not provided
            if npc_id is None:
                npc_id = self._generate_npc_id()

            return NPCModel(
                id=npc_id,
                name=name,
                description=description,
                last_location=last_location,
            )

        except Exception as e:
            logger.error(f"Error creating NPC '{name}': {e}", exc_info=True)
            raise

    def create_shopkeeper(
        self,
        name: str,
        shop_type: str,
        location: str,
        npc_id: Optional[str] = None,
    ) -> NPCModel:
        """
        Create a shopkeeper NPC.

        Args:
            name: The shopkeeper's name
            shop_type: Type of shop (e.g., "general store", "blacksmith", "alchemist")
            location: The shop's location
            npc_id: Optional NPC ID

        Returns:
            NPCModel: The newly created shopkeeper
        """
        description = f"The proprietor of a {shop_type} in {location}"
        return self.create_npc(
            name=name,
            description=description,
            last_location=location,
            npc_id=npc_id,
        )

    def create_quest_giver(
        self,
        name: str,
        role: str,
        location: str,
        npc_id: Optional[str] = None,
    ) -> NPCModel:
        """
        Create a quest giver NPC.

        Args:
            name: The quest giver's name
            role: Their role (e.g., "village elder", "mysterious stranger", "guard captain")
            location: Where they can be found
            npc_id: Optional NPC ID

        Returns:
            NPCModel: The newly created quest giver
        """
        description = f"A {role} who might have tasks for adventurers"
        return self.create_npc(
            name=name,
            description=description,
            last_location=location,
            npc_id=npc_id,
        )

    def create_from_monster(
        self,
        monster_index: str,
        custom_name: Optional[str] = None,
        location: str = "Unknown",
        content_pack_priority: Optional[List[str]] = None,
    ) -> Optional[NPCModel]:
        """
        Create an NPC based on a D&D 5e monster stat block.

        Args:
            monster_index: The monster index from D&D 5e content
            custom_name: Optional custom name (otherwise uses monster name)
            location: Where the NPC is located
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Optional[NPCModel]: The created NPC, or None if monster not found
        """
        try:
            # Look up the monster
            monster = self.content_service._hub.monsters.get_by_name_with_options(
                monster_index, content_pack_priority=content_pack_priority
            )
            if not monster:
                logger.warning(f"Monster '{monster_index}' not found in content")
                return None

            # Use custom name or monster name
            name = custom_name or monster.name

            # Build description from monster data
            size_type = f"{monster.size} {monster.type}"
            if monster.alignment:
                size_type += f", {monster.alignment}"

            description = f"A {size_type}"
            if hasattr(monster, "languages") and monster.languages:
                description += f". Speaks: {monster.languages}"

            return self.create_npc(
                name=name,
                description=description,
                last_location=location,
            )

        except Exception as e:
            logger.error(
                f"Error creating NPC from monster '{monster_index}': {e}",
                exc_info=True,
            )
            return None

    def _generate_npc_id(self) -> str:
        """
        Generate a unique NPC ID.

        Returns:
            str: A unique NPC ID
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid4())[:8]
        return f"npc_{timestamp}_{unique_id}"
