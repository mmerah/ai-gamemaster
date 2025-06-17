"""
Factory for creating combat-related objects.

This module provides the CombatFactory class for creating combat states and combatants.
"""

import logging
from typing import Dict, List

from app.content.service import ContentService
from app.domain.characters.service import CharacterService
from app.domain.shared.calculators.dice_mechanics import (
    get_ability_modifier,
    roll_single_die,
)
from app.models.character import (
    CharacterData,
    CharacterInstanceModel,
    CombinedCharacterModel,
)
from app.models.combat.attack import AttackModel
from app.models.combat.combatant import CombatantModel, InitialCombatantData
from app.models.combat.state import CombatStateModel

logger = logging.getLogger(__name__)


class CombatFactory:
    """Factory for creating combat-related objects."""

    def __init__(self, content_service: ContentService):
        """
        Initialize the combat factory.

        Args:
            content_service: Service for accessing D&D 5e content
        """
        self.content_service = content_service

    def create_combat_state(
        self,
        party: Dict[str, CharacterInstanceModel],
        npc_combatants: List[InitialCombatantData],
        character_service: CharacterService,
    ) -> CombatStateModel:
        """
        Create a new combat state from party members and NPC data.

        This is the main factory method that handles the full combat initialization,
        creating combatants from both party characters and NPCs.

        Args:
            party: Dictionary of party members (character_id -> CharacterInstanceModel)
            npc_combatants: List of NPC combatant data
            character_service: Service to get full character data

        Returns:
            CombatStateModel: The newly created combat state with all combatants
        """
        all_combatants: List[CombatantModel] = []

        # Create combatants from party members
        for char_id, character_instance in party.items():
            char_data = character_service.get_character(char_id)
            if not char_data:
                logger.warning(
                    f"Could not find character data for {char_id}, skipping combat"
                )
                continue

            # Create a CombinedCharacterModel from the CharacterData
            combined_character = self._create_combined_character_from_data(char_data)

            combatant = self._create_combatant_from_character(
                combined_character, roll_initiative=False
            )
            all_combatants.append(combatant)

        # Create combatants from NPCs
        for npc_data in npc_combatants:
            combatant = self._create_combatant_from_data(npc_data)
            all_combatants.append(combatant)

        # Create and return the combat state
        return CombatStateModel(
            is_active=True,
            round_number=1,
            current_turn_index=-1,  # No initiative set yet
            combatants=all_combatants,
            current_turn_instruction_given=False,
        )

    def _create_combined_character_from_data(
        self, char_data: CharacterData
    ) -> CombinedCharacterModel:
        """
        Create a CombinedCharacterModel from CharacterData.

        Args:
            char_data: The character data tuple containing template and instance

        Returns:
            CombinedCharacterModel: The combined character model
        """
        return CombinedCharacterModel.from_template_and_instance(
            template=char_data.template,
            instance=char_data.instance,
            character_id=char_data.character_id,
        )

    def _create_combatant_from_character(
        self,
        character: CombinedCharacterModel,
        roll_initiative: bool = True,
    ) -> CombatantModel:
        """
        Create a combatant from a character model.

        Args:
            character: The character to convert to a combatant
            roll_initiative: Whether to roll initiative (True) or set to 0 (False)

        Returns:
            CombatantModel: The created combatant
        """
        try:
            # Get DEX modifier for initiative
            dex_modifier = get_ability_modifier(character.base_stats.DEX)

            # Roll initiative if requested
            initiative = 0
            if roll_initiative:
                initiative_roll = roll_single_die(20)
                initiative = initiative_roll + dex_modifier
                logger.debug(
                    f"Rolled initiative for {character.name}: "
                    f"{initiative_roll} + {dex_modifier} = {initiative}"
                )

            # Prepare attacks from character equipment
            attacks = self._prepare_character_attacks(character)

            # Extract abilities from class features if available
            abilities: List[str] = []
            if character.class_features:
                abilities = [f.name for f in character.class_features]

            return CombatantModel(
                id=character.id,
                name=character.name,
                initiative=initiative,
                initiative_modifier=dex_modifier,
                current_hp=character.current_hp,
                max_hp=character.max_hp,
                armor_class=character.armor_class,
                conditions=[],
                is_player=True,
                icon_path=character.portrait_path,
                stats={
                    "STR": character.base_stats.STR,
                    "DEX": character.base_stats.DEX,
                    "CON": character.base_stats.CON,
                    "INT": character.base_stats.INT,
                    "WIS": character.base_stats.WIS,
                    "CHA": character.base_stats.CHA,
                },
                abilities=abilities,
                attacks=attacks,
                conditions_immune=[],
                resistances=[],
                vulnerabilities=[],
            )

        except Exception as e:
            logger.error(
                f"Error creating combatant from character {character.name}: {e}",
                exc_info=True,
            )
            raise

    def _create_combatant_from_data(self, data: InitialCombatantData) -> CombatantModel:
        """
        Create a combatant from initial data.

        Args:
            data: Initial combatant data

        Returns:
            CombatantModel: The created combatant
        """
        try:
            # Get DEX modifier for initiative (default to 0 if not provided)
            dex_modifier = 0
            if data.stats and "DEX" in data.stats:
                dex_modifier = get_ability_modifier(data.stats["DEX"])

            # Roll initiative
            initiative_roll = roll_single_die(20)
            initiative = initiative_roll + dex_modifier
            logger.debug(
                f"Rolled initiative for {data.name}: "
                f"{initiative_roll} + {dex_modifier} = {initiative}"
            )

            # Determine if this is a player character
            # If icon_path contains "portraits", it's likely a player
            is_player = bool(data.icon_path and "portraits" in data.icon_path)

            return CombatantModel(
                id=data.id,
                name=data.name,
                initiative=initiative,
                initiative_modifier=dex_modifier,
                current_hp=data.hp,
                max_hp=data.hp,
                armor_class=data.ac,
                conditions=[],
                is_player=is_player,
                icon_path=data.icon_path,
                stats=data.stats,
                abilities=data.abilities[:] if data.abilities else [],
                attacks=data.attacks[:] if data.attacks else [],
                conditions_immune=[],
                resistances=[],
                vulnerabilities=[],
            )

        except Exception as e:
            logger.error(
                f"Error creating combatant from data for {data.name}: {e}",
                exc_info=True,
            )
            raise

    def _prepare_character_attacks(
        self, character: CombinedCharacterModel
    ) -> List[AttackModel]:
        """
        Prepare attack list from character's equipped weapons.

        Args:
            character: The character to prepare attacks for

        Returns:
            List[AttackModel]: List of available attacks
        """
        attacks = []

        # Add unarmed strike as a basic attack option
        str_modifier = get_ability_modifier(character.base_stats.STR)
        attacks.append(
            AttackModel(
                name="Unarmed Strike",
                description=f"Melee Weapon Attack: +{character.proficiency_bonus + str_modifier} to hit, reach 5 ft., one target. Hit: {1 + str_modifier} bludgeoning damage.",
                attack_type="melee",
                to_hit_bonus=character.proficiency_bonus + str_modifier,
                reach="5 ft",
                damage_formula=f"1+{str_modifier}",
                damage_type="bludgeoning",
            )
        )

        # TODO: Add weapon attacks based on equipped items
        # This would require parsing character equipment and looking up weapon stats

        return attacks
