"""
Unified models and type definitions for the AI Gamemaster application.

This module re-exports all models from domain-specific modules to maintain
backward compatibility with existing imports.
"""

# Base classes
from .base import BaseModelWithDatetimeSerializer

# Campaign models
from .campaign import CampaignInstanceModel, CampaignSummaryModel, CampaignTemplateModel

# Character models
from .character import (
    CharacterData,
    CharacterInstanceModel,
    CharacterModifierDataModel,
    CharacterTemplateModel,
    CombinedCharacterModel,
)

# Combat models
from .combat import (
    AttackModel,
    CombatantModel,
    CombatInfoResponseModel,
    CombatStateModel,
    CombatStatusDataModel,
    InitialCombatantData,
    NextCombatantInfoModel,
)

# Configuration models
from .config import ServiceConfigModel

# Dice models
from .dice import (
    DiceExecutionModel,
    DiceRequestModel,
    DiceRollMessageModel,
    DiceRollResultModel,
    DiceRollResultResponseModel,
    DiceRollSubmissionModel,
    DiceSubmissionEventModel,
)

# Game state models
from .game_state import (
    AIRequestContextModel,
    ChatMessageModel,
    GameEventModel,
    GameEventResponseModel,
    GameStateModel,
    PlayerActionEventModel,
)

# RAG models
from .rag import (
    EventMetadataModel,
    LoreDataModel,
    RAGContextDataModel,
    RulesetDataModel,
)

# Utility models
from .utils import (
    ArmorModel,
    BaseStatsModel,
    ClassFeatureModel,
    D5EClassModel,
    GoldRangeModel,
    HouseRulesModel,
    ItemModel,
    LocationModel,
    MigrationResultModel,
    NPCModel,
    ProficienciesModel,
    QuestModel,
    SharedHandlerStateModel,
    TemplateValidationResult,
    TemplateValidationResultsModel,
    TokenStatsModel,
    TraitModel,
    VoiceInfoModel,
)

# Export all symbols for backward compatibility
__all__ = [
    # Base
    "BaseModelWithDatetimeSerializer",
    # Campaign
    "CampaignInstanceModel",
    "CampaignSummaryModel",
    "CampaignTemplateModel",
    # Character
    "CharacterData",
    "CharacterInstanceModel",
    "CharacterModifierDataModel",
    "CharacterTemplateModel",
    "CombinedCharacterModel",
    # Combat
    "AttackModel",
    "CombatantModel",
    "CombatInfoResponseModel",
    "CombatStateModel",
    "CombatStatusDataModel",
    "InitialCombatantData",
    "NextCombatantInfoModel",
    # Config
    "ServiceConfigModel",
    # Dice
    "DiceExecutionModel",
    "DiceRequestModel",
    "DiceRollMessageModel",
    "DiceRollResultModel",
    "DiceRollResultResponseModel",
    "DiceRollSubmissionModel",
    "DiceSubmissionEventModel",
    # Game State
    "AIRequestContextModel",
    "ChatMessageModel",
    "GameEventModel",
    "GameEventResponseModel",
    "GameStateModel",
    "PlayerActionEventModel",
    # RAG
    "EventMetadataModel",
    "LoreDataModel",
    "RAGContextDataModel",
    "RulesetDataModel",
    # Utils
    "ArmorModel",
    "BaseStatsModel",
    "ClassFeatureModel",
    "D5EClassModel",
    "GoldRangeModel",
    "HouseRulesModel",
    "ItemModel",
    "LocationModel",
    "MigrationResultModel",
    "NPCModel",
    "ProficienciesModel",
    "QuestModel",
    "SharedHandlerStateModel",
    "TemplateValidationResult",
    "TemplateValidationResultsModel",
    "TokenStatsModel",
    "TraitModel",
    "VoiceInfoModel",
]
