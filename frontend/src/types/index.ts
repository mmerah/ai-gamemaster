/**
 * Types Index - Central type exports
 *
 * This file provides a clean interface for importing types throughout the frontend.
 * It combines auto-generated backend types with UI-specific extensions.
 *
 * @module types
 */

// Re-export all unified types from the auto-generated file
export * from './unified'

// Re-export all API types
export * from './api'

// Re-export all UI-specific types
export * from './ui'

// Re-export all content types except CONTENT_TYPES to avoid conflict
export type {
  ContentPack,
  ContentPackCreate,
  ContentPackUpdate,
  ContentPackWithStats,
  ContentUploadResult,
  ContentTypeString
} from './content'
export { CONTENT_TYPE_STRINGS } from './content'

// Convenience type collections for common use cases
export type {
  // Character-related types
  CombinedCharacterModel,
  CharacterTemplateModel,
  CharacterInstanceModel
} from './unified'

export type {
  UIPartyMember,
  UICharacterStats,
  UICharacterProficiencies
} from './ui'

export type {
  // Chat & messaging types  
  ChatMessageModel
} from './unified'

export type {
  UIChatMessage,
  UINotification
} from './ui'

export type {
  // Dice & rolling types
  DiceRequestModel,
  DiceRollResultResponseModel
} from './unified'

export type {
  UIDiceRequest,
  GroupedDiceRequest,
  GroupedDiceCharacter,
  UIDiceRollResult
} from './ui'

export type {
  // Combat types
  CombatStateModel,
  CombatantModel
} from './unified'

export type {
  UICombatState,
  UICombatant
} from './ui'

export type {
  // Game state types
  GameStateModel,
  LocationModel,
  QuestModel
} from './unified'

export type {
  UILocation,
  UIQuest,
  UIGameSettings
} from './ui'

export type {
  // Event types - backend events
  NarrativeAddedEvent,
  CombatStartedEvent,
  CombatEndedEvent,
  TurnAdvancedEvent,
  CombatantHpChangedEvent,
  CombatantStatusChangedEvent,
  PlayerDiceRequestAddedEvent,
  PlayerDiceRequestsClearedEvent,
  BackendProcessingEvent,
  GameErrorEvent,
  GameStateSnapshotEvent
} from './unified'

export type {
  // Event types - UI events
  UIEventEmit,
  UIEventHandler
} from './ui'

export type {
  // Form & validation types
  UIFormState,
  UIValidationError,
  UILoadingState,
  UIModalState
} from './ui'

export type {
  // Utility types
  UIComponentSize,
  UIVariant,
  UIPosition,
  UIAlignment,
  UIAsyncAction,
  UIStateUpdater
} from './ui'
