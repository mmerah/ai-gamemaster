"""Processor for quest-related state updates."""

import logging
from typing import Optional

from app.core.interfaces import AIResponseProcessor
from app.models.events import QuestUpdatedEvent
from app.models.game_state import GameStateModel
from app.models.updates import QuestUpdateModel

from .utils import get_correlation_id

logger = logging.getLogger(__name__)


class QuestUpdater:
    """Handles quest-related state updates."""

    @staticmethod
    def apply_quest_update(
        game_state: GameStateModel,
        update: QuestUpdateModel,
        game_manager: Optional[AIResponseProcessor],
    ) -> None:
        """Applies updates to an existing quest."""
        quest = game_state.active_quests.get(update.quest_id)
        if not quest:
            logger.warning(
                f"QuestUpdateModel for unknown quest_id '{update.quest_id}'. Ignoring."
            )
            return

        # Track original values for event
        old_status = quest.status

        updated = False
        status_changed = False
        description_changed = False

        # Apply status update
        if update.status and quest.status != update.status:
            logger.info(
                f"Updating quest '{quest.title}' (ID: {update.quest_id}) status: '{quest.status}' -> '{update.status}'."
            )
            quest.status = update.status
            status_changed = True
            updated = True

        # Apply flattened fields update - log any quest-specific fields
        if any(
            [
                update.objectives_completed,
                update.objectives_total,
                update.rewards_experience,
                update.rewards_gold,
                update.rewards_items,
                update.rewards_reputation,
            ]
        ):
            # Log the flattened fields but note that QuestModel doesn't support all of them
            logger.info(
                f"Quest update for '{quest.title}' (ID: {update.quest_id}) includes additional fields"
            )
            logger.warning(
                "QuestModel doesn't support all flattened fields - only status is applied"
            )
            # Still mark as updated to emit the event
            updated = True

        if not updated:
            logger.debug(
                f"QuestUpdateModel for '{update.quest_id}' received but no changes applied."
            )

        # Emit QuestUpdatedEvent if quest was updated
        if updated and game_manager and game_manager.event_queue:
            event = QuestUpdatedEvent(
                quest_id=update.quest_id,
                quest_title=quest.title,
                old_status=old_status if status_changed else None,
                new_status=quest.status if status_changed else old_status,
                description_update=quest.description if description_changed else None,
                correlation_id=get_correlation_id(game_manager),
            )
            game_manager.event_queue.put_event(event)
            logger.debug(f"Emitted QuestUpdatedEvent for quest '{quest.title}'")
