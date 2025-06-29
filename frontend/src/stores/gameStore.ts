/**
 * Game Store - Campaign-level game state management
 *
 * This store manages the core campaign and game session state:
 * - Campaign ID and name
 * - Game location and map state
 * - Game settings (narration, TTS, etc.)
 * - Campaign lifecycle operations
 *
 * Other game state is managed by specialized stores:
 * - Chat/narrative messages: chatStore
 * - Party members: partyStore
 * - Combat state: combatStore
 * - Dice requests: diceStore
 *
 * @module gameStore
 */
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { gameApi } from '../services/gameApi'
import { ttsApi } from '../services/ttsApi'
import { useChatStore } from './chatStore'
import { usePartyStore } from './partyStore'
import { useCombatStore } from './combatStore'
import { useDiceStore } from './diceStore'
import { getErrorMessage } from '@/utils/errorHelpers'
import type {
  DiceRequestModel,
  GameStateModel,
  GameStateSnapshotEvent,
  LocationChangedEvent,
  PerformRollRequest,
  DiceRollResultResponseModel,
} from '@/types/unified'
import type {
  SaveGameResponse,
  StartCampaignResponse,
  GameEventResponseModel,
} from '@/types/unified'
import { logger } from '@/utils/logger'

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

// UI-specific types

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
  mapState: UIMapState | null
  location: string | null
  locationDescription: string | null
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

export const useGameStore = defineStore('game', () => {
  // Get specialized store instances
  const chatStore = useChatStore()
  const partyStore = usePartyStore()
  const combatStore = useCombatStore()
  const diceStore = useDiceStore()

  // State
  const gameState = reactive<UIGameState>({
    campaignId: null,
    campaignName: 'No Campaign Loaded',
    mapState: null,
    location: null,
    locationDescription: null,
    gameSettings: {
      narrationEnabled: false,
      ttsVoice: null,
      autoAdvanceTurns: false,
      showDetailedRolls: true,
      combatAnimations: true,
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
    isLoading: false,
  })

  const isLoading = ref(false)

  // TTS Functions
  async function loadTTSVoices(): Promise<Voice[]> {
    if (ttsState.availableVoices.length > 0) return ttsState.availableVoices

    ttsState.isLoading = true
    try {
      const response = await ttsApi.getVoices()
      const voices = response.data.voices || []
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

  async function previewVoice(
    voiceId: string,
    sampleText: string | null = null
  ): Promise<TTSResponse> {
    try {
      const response = await ttsApi.previewVoice(voiceId, sampleText)
      return response.data
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
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to load game state:', error)
      chatStore.addSystemMessage(`Error loading game state: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Initialize the game - loads initial state and triggers SSE snapshot
   * @returns {Promise} Initial game state data
   */
  async function initializeGame(): Promise<GameStateResponse> {
    return await loadGameState()
  }

  async function sendMessage(
    messageText: string
  ): Promise<PlayerActionResponse> {
    isLoading.value = true
    try {
      // Don't add message here - let the event handler do it to avoid duplicates
      const response = await gameApi.sendMessage(messageText)

      // The response will trigger events via SSE
      // No need to update state here
      return response.data
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to send message:', error)
      chatStore.addSystemMessage(`Error sending message: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * @deprecated SSE events automatically update state, no polling needed
   */
  async function pollGameState(): Promise<void> {
    // No-op for backward compatibility
    logger.warn(
      'pollGameState is deprecated. State updates are handled via SSE events.'
    )
  }

  async function rollDice(diceExpression: string): Promise<{ result: number }> {
    try {
      const result =
        Math.floor(Math.random() * parseInt(diceExpression.substring(1))) + 1
      chatStore.addSystemMessage(`Rolled ${diceExpression}: ${result}`, {
        details: {
          expression: diceExpression,
          result: result,
          breakdown: `[${result}]`,
        },
      })
      return { result }
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to roll dice:', error)
      chatStore.addSystemMessage(`Error rolling dice: ${errorMessage}`)
      throw error
    }
  }

  async function performRoll(
    rollParams: PerformRollRequest
  ): Promise<DiceRollResultResponseModel> {
    try {
      const response = await gameApi.rollDice(rollParams)

      if (response.data && !response.data.error) {
        return response.data
      } else {
        throw new Error(
          response.data?.error || 'Failed to perform roll via API'
        )
      }
    } catch (error) {
      console.error('Failed to perform roll:', error)
      throw error
    }
  }

  async function performAndSubmitRoll(
    requestedRollData: UIDiceRequest
  ): Promise<{
    singleRollResult: DiceRollResultResponseModel
    finalState: GameEventResponseModel
  }> {
    isLoading.value = true
    try {
      const rollResponse = await gameApi.rollDice({
        character_id: requestedRollData.character_id_to_roll || '',
        roll_type: requestedRollData.type || '',
        dice_formula: requestedRollData.dice_formula || '',
        skill: requestedRollData.skill,
        ability: requestedRollData.ability,
        dc: requestedRollData.dc,
        reason: requestedRollData.reason || '',
        request_id: requestedRollData.request_id,
      })

      if (rollResponse.data && !rollResponse.data.error) {
        // Submit the roll response directly
        const submitResponse = await gameApi.submitRolls([rollResponse.data])
        // Events will update the state
        return {
          singleRollResult: rollResponse.data,
          finalState: submitResponse.data,
        }
      } else {
        throw new Error(
          rollResponse.data?.error || 'Failed to perform roll via API'
        )
      }
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to perform and submit roll:', error)
      chatStore.addSystemMessage(`Error with dice roll: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function submitMultipleCompletedRolls(
    completedRollsArray: DiceRollResultResponseModel[]
  ): Promise<GameEventResponseModel> {
    isLoading.value = true
    try {
      const response = await gameApi.submitRolls(completedRollsArray)
      // Events will update the state
      return response.data
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to submit multiple rolls:', error)
      chatStore.addSystemMessage(`Error submitting rolls: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function startCampaign(
    campaignId: string
  ): Promise<StartCampaignResponse> {
    isLoading.value = true
    try {
      const response = await gameApi.startCampaign(campaignId)

      // The backend will emit events to update the state
      // Just return the response
      return response.data
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to start campaign:', error)
      chatStore.addSystemMessage(`Error starting campaign: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function resetGameState(): void {
    // Reset core game state
    Object.assign(gameState, {
      campaignId: null,
      campaignName: 'No Campaign Loaded',
      mapState: null,
      location: null,
      locationDescription: null,
      gameSettings: {
        narrationEnabled: false,
        ttsVoice: null,
        autoAdvanceTurns: false,
        showDetailedRolls: true,
        combatAnimations: true,
      },
      canRetryLastRequest: false,
      needsBackendTrigger: false,
    })

    // Clear specialized stores
    chatStore.clearMessages()
    partyStore.resetParty()
    combatStore.resetCombat()
    diceStore.clearAllRequests()
  }

  async function triggerNextStep(): Promise<GameEventResponseModel> {
    logger.debug('triggerNextStep called')
    isLoading.value = true
    try {
      const response = await gameApi.triggerNextStep()
      logger.debug('triggerNextStep response received:', response.data)
      // Events will update the state
      return response.data
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to trigger next step:', error)
      chatStore.addSystemMessage(`Error triggering next step: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function retryLastAIRequest(): Promise<GameEventResponseModel> {
    isLoading.value = true
    try {
      const response = await gameApi.retryLastAiRequest()
      // Events will update the state
      return response.data
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to retry last AI request:', error)
      chatStore.addSystemMessage(`Error retrying request: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function saveGame(): Promise<SaveGameResponse> {
    isLoading.value = true
    try {
      const response = await gameApi.saveGameState()
      logger.debug('Game saved successfully')
      return response.data
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      console.error('Failed to save game:', error)
      chatStore.addSystemMessage(`Error saving game: ${errorMessage}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Event Handlers
  const eventHandlers = {
    /**
     * Handle game state snapshot event
     * Updates location and other campaign-level state
     */
    game_state_snapshot: (event: GameStateSnapshotEvent) => {
      logger.debug('GameStore: Handling game state snapshot', event)

      // Update campaign info
      if (event.campaign_id) {
        gameState.campaignId = event.campaign_id
      }

      // Update location from location object
      if (event.location) {
        gameState.location = event.location.name
        gameState.locationDescription = event.location.description
      }
    },

    /**
     * Handle location changed event
     * Updates current location information
     */
    location_changed: (event: LocationChangedEvent) => {
      logger.debug('GameStore: Location changed', event)
      gameState.location = event.new_location_name
      gameState.locationDescription = event.new_location_description || null
    },
  }

  /**
   * Clean up event handlers (for compatibility)
   */
  function cleanupEventHandlers(): void {
    logger.debug('GameStore: Cleanup event handlers called')
  }

  return {
    gameState,
    ttsState,
    isLoading,
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
    // Event handlers
    eventHandlers,
    cleanupEventHandlers,
  }
})
