/**
 * UI-Specific Type Extensions
 *
 * This file contains type extensions and UI-specific interfaces that build upon
 * the auto-generated unified types from the backend. These types add frontend-specific
 * functionality while maintaining compatibility with the backend model-only architecture.
 *
 * @module ui-types
 */

import type {
  ChatMessageModel,
  DiceRequestModel,
  DiceRollResultResponseModel,
  CombinedCharacterModel,
  CombatantModel,
  CombatStateModel,
  CampaignTemplateModel,
  CharacterTemplateModel,
  LocationModel,
  QuestModel,
} from './unified'

// ===== Chat & Messaging =====

export interface UIChatMessage
  extends Omit<ChatMessageModel, 'is_dice_result'> {
  type: 'assistant' | 'user' | 'system' | 'dice'
  sequence_number?: number
  superseded?: boolean
  severity?: 'info' | 'warning' | 'error' | 'success'
  details?: Record<string, unknown>
}

// ===== Dice & Rolling =====

export interface UIDiceRequest extends Omit<DiceRequestModel, 'character_ids'> {
  character_id?: string // For backward compatibility with UI components
  character_id_to_roll?: string
  character_name?: string
  roll_type?: string // Alternative field name for consistency
  purpose?: string
  timestamp?: string
}

export interface GroupedDiceCharacter {
  character_id: string
  character_name: string
  skill?: string
  ability?: string
}

export interface GroupedDiceRequest {
  request_id: string
  roll_type?: string
  type: string
  reason?: string
  dice_formula?: string
  dc?: number
  characters: GroupedDiceCharacter[]
}

export interface UIDiceRollResult extends DiceRollResultResponseModel {
  success?: boolean
  criticalSuccess?: boolean
  criticalFailure?: boolean
  displayClass?: string
}

// ===== Party & Characters =====

export interface UIPartyMember extends CombinedCharacterModel {
  // UI-specific computed properties
  isOnline?: boolean
  lastActivity?: string
  uiState?: {
    selected: boolean
    highlighted: boolean
    displayMode: 'compact' | 'detailed'
  }
}

export interface UICharacterStats {
  strength: number
  dexterity: number
  constitution: number
  intelligence: number
  wisdom: number
  charisma: number
}

export interface UICharacterProficiencies {
  skills: string[]
  languages: string[]
  weapons: string[]
  armor: string[]
  tools: string[]
  saving_throws: string[]
}

// ===== Combat =====

export interface UICombatant extends CombatantModel {
  // UI-specific properties
  isCurrentTurn?: boolean
  wasJustAdded?: boolean
  animationState?: 'none' | 'taking-damage' | 'healing' | 'entering' | 'leaving'
  displayPosition?: { x: number; y: number }
}

export interface UICombatState extends Omit<CombatStateModel, 'combatants'> {
  combatants?: UICombatant[]
  isActive: boolean // Ensure this is always present for UI
  // UI-specific state
  selectedCombatantId?: string
  combatLogExpanded?: boolean
  initiativeVisible?: boolean
}

// ===== Map & Location =====

export interface UIMapMarker {
  id: string
  x: number
  y: number
  type:
    | 'character'
    | 'enemy'
    | 'point_of_interest'
    | 'danger'
    | 'treasure'
    | 'exit'
  name: string
  description?: string
  iconUrl?: string
  isInteractive?: boolean
  isVisible?: boolean
}

export interface UIMapState {
  name: string
  description: string
  image: string | null
  markers: UIMapMarker[]
  // UI-specific map state
  zoom?: number
  centerX?: number
  centerY?: number
  selectedMarkerId?: string
  markersVisible?: boolean
}

export interface UILocation extends LocationModel {
  // UI-specific properties
  mapImageUrl?: string
  ambientSoundUrl?: string
  visitCount?: number
  lastVisited?: string
  isBookmarked?: boolean
}

// ===== Game Settings =====

export interface UIGameSettings {
  // Display settings
  theme: 'light' | 'dark' | 'auto'
  fontSize: 'small' | 'medium' | 'large'
  showDetailedRolls: boolean
  combatAnimations: boolean
  autoScrollChat: boolean

  // Audio settings
  narrationEnabled: boolean
  ttsVoice: string | null
  ttsSpeed: number
  soundEffectsEnabled: boolean
  musicEnabled: boolean
  masterVolume: number

  // Gameplay settings
  autoAdvanceTurns: boolean
  confirmCriticalActions: boolean
  quickRollMode: boolean
  showInitiativeNumbers: boolean

  // Accessibility
  highContrast: boolean
  reducedMotion: boolean
  screenReaderSupport: boolean
}

// ===== TTS (Text-to-Speech) =====

export interface UIVoice {
  id: string
  name: string
  language?: string
  gender?: string
  preview_url?: string
  isAvailable?: boolean
  isFavorite?: boolean
}

export interface UITTSState {
  enabled: boolean
  autoPlay: boolean
  voiceId: string | null
  availableVoices: UIVoice[]
  isLoading: boolean
  currentlyPlaying?: string
  queue: string[]
}

// ===== Campaign Management =====

export interface UICampaignTemplate extends CampaignTemplateModel {
  // UI-specific properties
  isFavorite?: boolean
  lastPlayed?: string
  playCount?: number
  thumbnailUrl?: string
  estimatedDuration?: string
  playerCount?: { min: number; max: number }
  uiTags?: string[]
}

export interface UICharacterTemplate extends CharacterTemplateModel {
  // UI-specific properties
  isFavorite?: boolean
  lastUsed?: string
  useCount?: number
  portraitUrl?: string
  createdByUser?: boolean
  isOfficial?: boolean
  uiTags?: string[]
}

// ===== Quest Management =====

export interface UIQuest extends QuestModel {
  // UI-specific properties
  isExpanded?: boolean
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category?: string
  estimatedTime?: string
  prerequisites?: string[]
  rewards?: {
    experience?: number
    gold?: number
    items?: string[]
    reputation?: string
  }
}

// ===== UI State Management =====

export interface UIModalState {
  isOpen: boolean
  title?: string
  content?: string
  confirmText?: string
  cancelText?: string
  onConfirm?: () => void | Promise<void>
  onCancel?: () => void
  type?: 'info' | 'warning' | 'error' | 'confirm'
}

export interface UINotification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  actions?: Array<{
    label: string
    action: () => void
    primary?: boolean
  }>
  timestamp: string
}

export interface UILoadingState {
  isLoading: boolean
  message?: string
  progress?: number
  canCancel?: boolean
  operation?: string
}

// ===== RAG Testing Types =====

export interface QueryPreset {
  id: string
  name: string
  query: string
  description?: string
  gameStateOverrides?: {
    in_combat?: boolean
    current_location?: string
    addCombatants?: boolean
    addPartyMembers?: boolean
  }
}

// ===== Form & Input Types =====

export interface UIValidationError {
  field: string
  message: string
  code?: string
}

export interface UIFormState<T = Record<string, unknown>> {
  data: T
  errors: UIValidationError[]
  isValid: boolean
  isDirty: boolean
  isSubmitting: boolean
  touchedFields: Set<string>
}

// ===== Event System =====

export interface UIEventEmit {
  // Character events
  'character-selected': (characterId: string) => void
  'character-action': (characterId: string, action: string) => void

  // Dice events
  'dice-roll-requested': (request: UIDiceRequest) => void
  'dice-rolled': (result: UIDiceRollResult) => void

  // Combat events
  'combatant-selected': (combatantId: string) => void
  'initiative-changed': (combatantId: string, initiative: number) => void

  // Navigation events
  'navigate-to': (route: string, params?: Record<string, unknown>) => void
  'modal-open': (modalType: string, data?: Record<string, unknown>) => void
  'modal-close': () => void

  // Settings events
  'setting-changed': (key: string, value: unknown) => void
  'voice-selected': (voiceId: string) => void
}

// ===== API Response Extensions =====

export interface UIApiResponse<T = unknown> {
  data: T
  error?: string
  status_code?: number
  timestamp?: string
  requestId?: string
}

export interface UIErrorResponse {
  error: string
  message?: string
  details?: Record<string, unknown>
  code?: string | number
  timestamp: string
  canRetry?: boolean
  retryAfter?: number
}

// ===== Utility Types =====

export type UIComponentSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type UIVariant =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
export type UIPosition = 'top' | 'bottom' | 'left' | 'right' | 'center'
export type UIAlignment = 'start' | 'center' | 'end' | 'stretch'

// Export commonly used type combinations
export type UIEventHandler<T = unknown> = (event: T) => void | Promise<void>
export type UIAsyncAction<T = void> = () => Promise<T>
export type UIStateUpdater<T> = (current: T) => T | Partial<T>
