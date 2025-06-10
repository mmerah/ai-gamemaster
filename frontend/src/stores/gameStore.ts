/**
 * Game Store - Main game state management
 *
 * This store manages the core game state including:
 * - Campaign and game session data
 * - Chat history and narrative
 * - Party and combat state
 * - Dice requests
 * - TTS (Text-to-Speech) configuration
 *
 * @module gameStore
 */
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { gameApi } from '../services/gameApi'
import { ttsApi } from '../services/ttsApi'
import eventService from '@/services/eventService'
import type {
  ChatMessageModel,
  DiceRequestModel,
  CombatStateModel,
  CombinedCharacterModel,
  CombatantModel,
  GameStateModel,
  NarrativeAddedEvent,
  CombatStartedEvent,
  CombatEndedEvent,
  TurnAdvancedEvent,
  CombatantHpChangedEvent,
  CombatantStatusChangedEvent,
  CombatantInitiativeSetEvent,
  InitiativeOrderDeterminedEvent,
  PlayerDiceRequestAddedEvent,
  PlayerDiceRequestsClearedEvent,
  CombatantAddedEvent,
  CombatantRemovedEvent,
  LocationChangedEvent,
  PartyMemberUpdatedEvent,
  QuestUpdatedEvent,
  ItemAddedEvent,
  BackendProcessingEvent,
  GameErrorEvent,
  GameStateSnapshotEvent
} from '@/types/unified'

// Import TTS types
interface Voice {
  id: string
  name: string
  language?: string
  gender?: string
  preview_url?: string
}

interface TTSResponse {
  audio_path: string
  audio_url?: string
  duration?: number
}

// Game API Response types
interface GameStateResponse {
  game_state?: GameStateModel
  campaign_id?: string
  campaign_name?: string
}

interface PlayerActionResponse {
  message?: string
  game_state?: Partial<GameStateModel>
  needs_backend_trigger?: boolean
}

interface RollDiceResponse {
  character_id: string
  roll_type: string
  total: number
  result_summary: string
  result_message?: string
  error?: string
}

interface GameActionResponse {
  message?: string
  processed?: boolean
  saved?: boolean
  save_path?: string
}

// UI-specific types
interface UIChatMessage {
  id: string
  type: 'gm' | 'user' | 'system' | 'dice'
  role?: ChatMessageModel['role']
  content: string
  timestamp: string
  gm_thought?: string
  audio_path?: string | null
  severity?: string
  details?: Record<string, unknown>
}

interface UIDiceRequest extends Partial<DiceRequestModel> {
  request_id: string
  character_id_to_roll?: string
  character_name?: string
  type: string
  roll_type?: string
  dice_formula?: string
  purpose?: string
  reason?: string
  dc?: number
  skill?: string
  ability?: string
}

interface UIMapMarker {
  id: string
  x: number
  y: number
  type: 'character' | 'enemy' | 'point_of_interest' | 'danger'
  name: string
  description?: string
}

interface UIMapState {
  name: string
  description: string
  image: string | null
  markers: UIMapMarker[]
}

interface UIGameSettings {
  narrationEnabled: boolean
  ttsVoice: string | null
  autoAdvanceTurns: boolean
  showDetailedRolls: boolean
  combatAnimations: boolean
}

interface UIGameState {
  campaignId: string | null
  campaignName: string
  chatHistory: UIChatMessage[]
  party: CombinedCharacterModel[]
  combatState: Partial<CombatStateModel> & { isActive: boolean }
  mapState: UIMapState | null
  location: string | null
  locationDescription: string | null
  diceRequests: UIDiceRequest[]
  gameSettings: UIGameSettings
  canRetryLastRequest: boolean
  needsBackendTrigger: boolean
}

interface UITTSState {
  enabled: boolean
  autoPlay: boolean
  voiceId: string | null
  availableVoices: Voice[]
  isLoading: boolean
}

// Event handler type - specific for game events
type EventHandler<T extends Record<string, unknown> = Record<string, unknown>> = (event: T) => void

export const useGameStore = defineStore('game', () => {
  // State
  const gameState = reactive<UIGameState>({
    campaignId: null,
    campaignName: 'No Campaign Loaded',
    chatHistory: [],
    party: [],
    combatState: { isActive: false },
    mapState: null,
    location: null,
    locationDescription: null,
    diceRequests: [],
    gameSettings: {
      narrationEnabled: false,
      ttsVoice: null,
      autoAdvanceTurns: false,
      showDetailedRolls: true,
      combatAnimations: true
    },
    canRetryLastRequest: false,
    needsBackendTrigger: false,
  })

  // TTS State
  const ttsState = reactive<UITTSState>({
    enabled: false,
    autoPlay: false,
    voiceId: null,
    availableVoices: [],
    isLoading: false
  })

  const isLoading = ref(false)
  const isConnected = ref(false)

  // Event handlers
  const eventHandlers: Record<string, EventHandler> = {
    // Narrative events (handled by chatStore, included here for completeness)
    narrative_added: (event: NarrativeAddedEvent) => {
      const message: UIChatMessage = {
        id: event.message_id || event.event_id,
        type: mapRoleToType(event.role),
        content: event.content,
        timestamp: event.timestamp,
        gm_thought: event.gm_thought,
        audio_path: event.audio_path ? `/static/${event.audio_path}` : null
      }

      // Check for duplicates
      const exists = gameState.chatHistory.some(m => m.id === message.id)
      if (!exists) {
        gameState.chatHistory.push(message)

        // Note: TTS auto-play is handled by ChatHistory component to avoid double playing
      }
    },

    // Combat state events
    combat_started: (event: CombatStartedEvent) => {
      gameState.combatState = {
        isActive: true,
        is_active: true,
        combatants: event.combatants || [],
        round_number: event.round_number || 1,
        current_turn_index: -1
      }
    },

    combat_ended: (event: CombatEndedEvent) => {
      gameState.combatState = {
        isActive: false,
        is_active: false,
        reason: event.reason,
        outcome_description: event.outcome_description,
        combatants: [],
        round_number: 0,
        current_turn_index: -1
      }
      // Clear any pending dice requests when combat ends
      gameState.diceRequests = []
    },

    // Turn management
    turn_advanced: (event: TurnAdvancedEvent) => {
      if (gameState.combatState.isActive) {
        const combatantIndex = gameState.combatState.combatants?.findIndex(
          c => c.id === event.new_combatant_id
        )
        if (combatantIndex !== undefined && combatantIndex !== -1) {
          gameState.combatState.current_turn_index = combatantIndex
          gameState.combatState.round_number = event.round_number
        }
      }
    },

    // Combatant updates
    combatant_hp_changed: (event: CombatantHpChangedEvent) => {
      // Update combat state if in combat
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        const combatant = gameState.combatState.combatants.find(c => c.id === event.combatant_id)
        if (combatant) {
          combatant.current_hp = event.new_hp
          combatant.max_hp = event.max_hp
        }
      }

      // Update party member if it's a PC
      if (event.is_player_controlled) {
        const partyMember = gameState.party.find(p => p.id === event.combatant_id)
        if (partyMember) {
          partyMember.currentHp = event.new_hp
          partyMember.hp = event.new_hp
          partyMember.maxHp = event.max_hp
          partyMember.max_hp = event.max_hp
        }
      }
    },

    combatant_status_changed: (event: CombatantStatusChangedEvent) => {
      // Update combat state
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        const combatant = gameState.combatState.combatants.find(c => c.id === event.combatant_id)
        if (combatant) {
          combatant.conditions = event.new_conditions || []
          // Note: is_defeated is part of the CombatantModel interface
          if ('is_defeated' in combatant && event.is_defeated !== undefined) {
            (combatant as CombatantModel & { is_defeated: boolean }).is_defeated = event.is_defeated
          }
        }
      }

      // Update party member if it's a PC
      // Note: CombatantStatusChangedEvent doesn't have is_player_controlled
      const partyMember = gameState.party.find(p => p.id === event.combatant_id)
      if (partyMember) {
        partyMember.conditions = event.new_conditions || []
      }
    },

    // Initiative events
    combatant_initiative_set: (event: CombatantInitiativeSetEvent) => {
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        const combatant = gameState.combatState.combatants.find(c => c.id === event.combatant_id)
        if (combatant) {
          combatant.initiative = event.initiative_value
        }
      }
    },

    initiative_order_determined: (event: InitiativeOrderDeterminedEvent) => {
      if (gameState.combatState.isActive) {
        gameState.combatState.combatants = event.ordered_combatants
      }
    },

    // Dice events
    player_dice_request_added: (event: PlayerDiceRequestAddedEvent) => {
      console.log('Processing player_dice_request_added event:', event)
      console.log('Current dice requests before adding:', [...gameState.diceRequests])

      // Check for duplicates
      const exists = gameState.diceRequests.some(r => r.request_id === event.request_id)
      if (!exists) {
        const diceRequest: UIDiceRequest = {
          request_id: event.request_id,
          character_id_to_roll: event.character_id,
          character_name: event.character_name,
          type: event.roll_type,
          roll_type: event.roll_type,
          dice_formula: event.dice_formula,
          purpose: event.purpose,
          reason: event.purpose,
          dc: event.dc,
          skill: event.skill,
          ability: event.ability
        }
        console.log('Adding dice request:', diceRequest)

        // Use spread operator to ensure reactivity
        gameState.diceRequests = [...gameState.diceRequests, diceRequest]

        console.log('Updated dice requests after adding:', gameState.diceRequests)
        console.log('Total dice requests:', gameState.diceRequests.length)
      } else {
        console.log('Dice request already exists, skipping:', event.request_id)
      }
    },

    player_dice_requests_cleared: (event: PlayerDiceRequestsClearedEvent) => {
      if (event.cleared_request_ids && event.cleared_request_ids.length > 0) {
        gameState.diceRequests = gameState.diceRequests.filter(
          r => !event.cleared_request_ids.includes(r.request_id)
        )
      }
    },

    // Combatant management
    combatant_added: (event: CombatantAddedEvent) => {
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        const newCombatant: CombatantModel = {
          id: event.combatant_id,
          name: event.combatant_name,
          current_hp: event.hp,
          max_hp: event.max_hp,
          armor_class: event.ac,
          is_player: event.is_player_controlled,
          initiative: 0,
          initiative_modifier: 0,
          conditions: []
        }

        // Insert at correct position if specified
        if (event.position_in_order !== undefined) {
          gameState.combatState.combatants.splice(event.position_in_order, 0, newCombatant)
        } else {
          gameState.combatState.combatants.push(newCombatant)
        }
      }
    },

    combatant_removed: (event: CombatantRemovedEvent) => {
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        gameState.combatState.combatants = gameState.combatState.combatants.filter(
          c => c.id !== event.combatant_id
        )
      }
    },

    // Location events
    location_changed: (event: LocationChangedEvent) => {
      gameState.location = event.new_location_name
      gameState.locationDescription = event.new_location_description

      // Update map state
      if (event.new_location_name && event.new_location_description) {
        gameState.mapState = {
          name: event.new_location_name,
          description: event.new_location_description,
          image: null,
          markers: []
        }
      }
    },

    // Party events
    party_member_updated: (event: PartyMemberUpdatedEvent) => {
      const member = gameState.party.find(p => p.id === event.character_id)
      if (member && event.changes) {
        Object.assign(member, event.changes)

        // Ensure consistent field naming
        if ('current_hp' in event.changes) {
          member.currentHp = event.changes.current_hp as number
          member.hp = event.changes.current_hp as number
        }
        if ('max_hp' in event.changes) {
          member.maxHp = event.changes.max_hp as number
          member.max_hp = event.changes.max_hp as number
        }
      }
    },

    // Quest events
    quest_updated: (event: QuestUpdatedEvent) => {
      // For now, just add to chat history as system message
      gameState.chatHistory.push({
        id: event.event_id,
        type: 'system',
        content: `Quest Updated: ${event.quest_title} - ${event.new_status}`,
        timestamp: event.timestamp
      })
    },

    // Item events
    item_added: (event: ItemAddedEvent) => {
      // For now, just add to chat history as system message
      gameState.chatHistory.push({
        id: event.event_id,
        type: 'system',
        content: `${event.character_name} received: ${event.item_name}${event.quantity > 1 ? ` x${event.quantity}` : ''}`,
        timestamp: event.timestamp
      })
    },

    // System events
    backend_processing: (event: BackendProcessingEvent) => {
      isLoading.value = event.is_processing
      gameState.needsBackendTrigger = event.needs_backend_trigger || false
    },

    game_error: (event: GameErrorEvent) => {
      console.error('Game error event:', event)
      gameState.chatHistory.push({
        id: event.event_id,
        type: 'system',
        content: `Error: ${event.error_message}`,
        timestamp: event.timestamp,
        severity: event.severity
      })

      // Enable retry if the error is recoverable
      if (event.recoverable) {
        gameState.canRetryLastRequest = true
      }
    },

    game_state_snapshot: (event: GameStateSnapshotEvent) => {
      // Full state sync - used for reconnection
      console.log('Received game state snapshot:', event)

      // Update all state from snapshot
      if (event.campaign_id) gameState.campaignId = event.campaign_id
      if ('campaign_name' in event && typeof event.campaign_name === 'string') {
        gameState.campaignName = event.campaign_name
      }

      // Handle location - it comes as an object with name and description
      if (event.location) {
        if (typeof event.location === 'object') {
          gameState.location = event.location.name || 'Unknown Location'
          gameState.locationDescription = event.location.description || ''
        } else {
          gameState.location = event.location
        }
      }
      if ('location_description' in event && typeof event.location_description === 'string') {
        gameState.locationDescription = event.location_description
      }

      // Update party
      if (event.party_members) {
        console.log('Processing party_members from snapshot:', event.party_members)

        // party_members should be CombinedCharacterModel[]
        const partyArray = Array.isArray(event.party_members)
          ? event.party_members
          : [event.party_members]

        gameState.party = partyArray.map(member => {
          // member should already be a CombinedCharacterModel with flat structure
          const processedMember: CombinedCharacterModel = {
            ...member,
            // Ensure consistent field names across the interface
            current_hp: member.current_hp || 0,
            max_hp: member.max_hp || 0,
            armor_class: member.armor_class || 10
          }
          console.log(`Processed party member ${member.name || 'Unknown'}:`, processedMember)
          return processedMember
        })
        console.log('Final gameState.party:', gameState.party)
      }

      // Update combat state
      if (event.combat_state) {
        gameState.combatState = {
          ...event.combat_state,
          isActive: event.combat_state.is_active || false,
          is_active: event.combat_state.is_active || false
        }
      }

      // Update dice requests
      if (event.pending_dice_requests) {
        console.log('WARNING: Snapshot is updating dice requests. Current count:', gameState.diceRequests.length)
        console.log('Processing pending_dice_requests from snapshot:', event.pending_dice_requests)

        // Only update if we don't already have dice requests (to avoid overwriting events)
        if (gameState.diceRequests.length === 0) {
          gameState.diceRequests = event.pending_dice_requests.map(request => ({
            ...request,
            // Ensure consistent field names
            request_id: request.request_id,
            character_id_to_roll: request.character_ids?.[0],
            character_name: undefined, // Will be filled by UI
            type: request.type,
            roll_type: request.type,
            dice_formula: request.dice_formula,
            purpose: request.reason,
            reason: request.reason,
            dc: request.dc,
            skill: request.skill,
            ability: request.ability
          }))
          console.log('Processed dice requests from snapshot:', gameState.diceRequests)
        } else {
          console.log('Skipping snapshot dice requests update - already have requests from events')
        }
      }

      // Update chat history if provided
      if (event.chat_history && Array.isArray(event.chat_history)) {
        gameState.chatHistory = event.chat_history.map(msg => ({
          id: msg.id || `${Date.now()}-${Math.random()}`,
          type: mapRoleToType(msg.role),
          content: msg.content,
          timestamp: msg.timestamp || new Date().toISOString(),
          gm_thought: msg.gm_thought,
          audio_path: msg.audio_path ? `/static/${msg.audio_path}` : null
        }))
      } else {
        // If no chat history provided, initialize as empty
        gameState.chatHistory = []
      }

      // If this is a fresh game state with no chat history, trigger initial narrative
      if (gameState.chatHistory.length === 0 && event.reason !== 'reconnection') {
        console.log('Fresh game state detected - setting needsBackendTrigger for initial narrative')
        gameState.needsBackendTrigger = true
      }

      // Update TTS state from game state
      if ('narration_enabled' in event && typeof event.narration_enabled === 'boolean') {
        ttsState.enabled = event.narration_enabled
        gameState.gameSettings.narrationEnabled = event.narration_enabled
      }
      if ('tts_voice' in event && typeof event.tts_voice === 'string') {
        ttsState.voiceId = event.tts_voice
        gameState.gameSettings.ttsVoice = event.tts_voice
      }
    }
  }

  // Helper functions
  function mapRoleToType(role: string): 'gm' | 'user' | 'system' {
    switch (role) {
      case 'assistant':
        return 'gm'
      case 'user':
        return 'user'
      case 'system':
        return 'system'
      default:
        return 'system'
    }
  }


  // Initialize event handlers
  function initializeEventHandlers(): void {
    // Register all event handlers
    Object.entries(eventHandlers).forEach(([eventType, handler]) => {
      eventService.on(eventType, handler)
    })

    // Connect to SSE
    eventService.connect()
    isConnected.value = eventService.connected

    // Monitor connection status
    setInterval(() => {
      isConnected.value = eventService.connected
    }, 1000)
  }

  // Cleanup event handlers
  function cleanupEventHandlers(): void {
    Object.entries(eventHandlers).forEach(([eventType, handler]) => {
      eventService.off(eventType, handler)
    })
  }

  // TTS Functions
  async function loadTTSVoices(): Promise<Voice[]> {
    if (ttsState.availableVoices.length > 0) return ttsState.availableVoices

    ttsState.isLoading = true
    try {
      const response = await ttsApi.getVoices()
      const voices = response.voices || []
      ttsState.availableVoices = voices
      return voices
    } catch (error) {
      console.error('Failed to load TTS voices:', error)
      return []
    } finally {
      ttsState.isLoading = false
    }
  }

  function enableTTS(voiceId: string | null = null): void {
    ttsState.enabled = true
    if (voiceId) {
      ttsState.voiceId = voiceId
    }
  }

  function disableTTS(): void {
    ttsState.enabled = false
    ttsState.autoPlay = false
  }

  function setTTSVoice(voiceId: string): void {
    ttsState.voiceId = voiceId
    if (voiceId) {
      ttsState.enabled = true
    }
  }

  function setAutoPlay(enabled: boolean): void {
    ttsState.autoPlay = enabled
  }

  async function previewVoice(voiceId: string, sampleText: string | null = null): Promise<TTSResponse> {
    try {
      return await ttsApi.previewVoice(voiceId, sampleText)
    } catch (error) {
      console.error('Failed to preview voice:', error)
      throw error
    }
  }

  // Game Actions (these trigger backend changes, which then emit events)
  async function loadGameState(): Promise<GameStateResponse> {
    isLoading.value = true
    try {
      // Request game state with snapshot event
      // The actual state updates will come via SSE events
      const response = await gameApi.getGameState({ emit_snapshot: true })

      // Just return the response - let SSE events handle all state updates
      // The game_state_snapshot event will be emitted and handled by eventRouter
      return response.data
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      console.error('Failed to load game state:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error loading game state: ${errorMessage}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Initialize the game - loads initial state and triggers SSE snapshot
   * Event handlers are now managed by eventRouter
   * @returns {Promise} Initial game state data
   */
  async function initializeGame(): Promise<GameStateResponse> {
    return await loadGameState()
  }

  /**
   * Legacy polling function - no longer used
   * @deprecated State updates now come via SSE events
   */
  async function pollGameState(): Promise<void> {
    console.log('pollGameState called but ignored - using SSE events')
  }

  async function sendMessage(messageText: string): Promise<PlayerActionResponse> {
    isLoading.value = true
    try {
      // Don't add message here - let the event handler do it to avoid duplicates
      const response = await gameApi.sendMessage(messageText)

      // The response will trigger events via SSE
      // No need to update state here
      return response.data
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      console.error('Failed to send message:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error sending message: ${errorMessage}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function rollDice(diceExpression: string): Promise<{ result: number }> {
    try {
      const result = Math.floor(Math.random() * parseInt(diceExpression.substring(1))) + 1
      gameState.chatHistory.push({
        id: `${Date.now()}-dice`,
        type: 'dice',
        content: `Rolled ${diceExpression}: ${result}`,
        details: { expression: diceExpression, result: result, breakdown: `[${result}]` },
        timestamp: new Date().toISOString()
      })
      return { result }
    } catch (error: any) {
      console.error('Failed to roll dice:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error rolling dice: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    }
  }

  async function performRoll(rollParams: {
    character_id: string
    roll_type: string
    dice_formula: string
    skill?: string
    ability?: string
    dc?: number
    reason?: string
    request_id?: string
  }): Promise<RollDiceResponse> {
    try {
      const response = await gameApi.rollDice(rollParams)

      if (response.data && !response.data.error) {
        return response.data
      } else {
        throw new Error(response.data?.error || "Failed to perform roll via API")
      }
    } catch (error) {
      console.error('Failed to perform roll:', error)
      throw error
    }
  }

  async function performAndSubmitRoll(requestedRollData: UIDiceRequest): Promise<any> {
    isLoading.value = true
    try {
      const rollResponse = await gameApi.rollDice({
        character_id: requestedRollData.character_id_to_roll || '',
        roll_type: requestedRollData.type || '',
        dice_formula: requestedRollData.dice_formula || '',
        skill: requestedRollData.skill,
        ability: requestedRollData.ability,
        dc: requestedRollData.dc,
        reason: requestedRollData.reason,
        request_id: requestedRollData.request_id
      })

      if (rollResponse.data && !rollResponse.data.error) {
        const submitResponse = await gameApi.submitRolls([rollResponse.data])
        // Events will update the state
        return { singleRollResult: rollResponse.data, finalState: submitResponse.data }
      } else {
        throw new Error(rollResponse.data?.error || "Failed to perform roll via API")
      }
    } catch (error: any) {
      console.error('Failed to perform and submit roll:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error with dice roll: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function submitMultipleCompletedRolls(completedRollsArray: any[]): Promise<any> {
    isLoading.value = true
    try {
      const response = await gameApi.submitRolls(completedRollsArray)
      // Events will update the state
      return response.data
    } catch (error: any) {
      console.error('Failed to submit multiple rolls:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error submitting rolls: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function startCampaign(campaignId: string): Promise<any> {
    isLoading.value = true
    try {
      const response = await gameApi.startCampaign(campaignId)

      // The backend will emit events to update the state
      // Just return the response
      return response.data
    } catch (error: any) {
      console.error('Failed to start campaign:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error starting campaign: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function resetGameState(): void {
    Object.assign(gameState, {
      campaignId: null,
      campaignName: 'No Campaign Loaded',
      chatHistory: [],
      party: [],
      combatState: { isActive: false },
      mapState: null,
      location: null,
      locationDescription: null,
      diceRequests: [],
      gameSettings: {
        narrationEnabled: false,
        ttsVoice: null,
        autoAdvanceTurns: false,
        showDetailedRolls: true,
        combatAnimations: true
      },
      canRetryLastRequest: false,
      needsBackendTrigger: false,
    })
  }

  async function triggerNextStep(): Promise<any> {
    console.log('triggerNextStep called')
    isLoading.value = true
    try {
      const response = await gameApi.triggerNextStep()
      console.log('triggerNextStep response received:', response.data)
      // Events will update the state
      return response.data
    } catch (error: any) {
      console.error('Failed to trigger next step:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error triggering next step: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function retryLastAIRequest(): Promise<any> {
    isLoading.value = true
    try {
      const response = await gameApi.retryLastAiRequest()
      // Events will update the state
      return response.data
    } catch (error: any) {
      console.error('Failed to retry last AI request:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error retrying request: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function saveGame(): Promise<any> {
    isLoading.value = true
    try {
      const response = await gameApi.saveGameState()
      console.log('Game saved successfully')
      return response.data
    } catch (error: any) {
      console.error('Failed to save game:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error saving game: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  return {
    gameState,
    ttsState,
    isLoading,
    isConnected,
    loadGameState,
    initializeGame,
    pollGameState, // No-op for compatibility
    sendMessage,
    rollDice,
    performRoll,
    performAndSubmitRoll,
    submitMultipleCompletedRolls,
    startCampaign,
    resetGameState,
    triggerNextStep,
    retryLastAIRequest,
    saveGame,
    // TTS functions
    loadTTSVoices,
    enableTTS,
    disableTTS,
    setTTSVoice,
    setAutoPlay,
    previewVoice,
    // Event management
    initializeEventHandlers,
    cleanupEventHandlers,
    // Export event handlers for eventRouter
    eventHandlers
  }
})
