import { apiClient } from './apiClient'
import type { AxiosResponse } from 'axios'
import type {
  GameStateModel,
  DiceRollResultModel
} from '@/types/unified'

// API Parameter Types
interface GameStateParams {
  emit_snapshot?: boolean
  _t?: number  // Timestamp for cache busting
}


interface RollDiceParams {
  character_id: string
  roll_type: string
  dice_formula: string
  skill?: string
  ability?: string
  dc?: number
  reason?: string
  request_id?: string
}


// Response Types - matching actual backend responses
interface GameStateResponse {
  game_state?: GameStateModel
  campaign_id?: string
  campaign_name?: string
  error?: string
  status_code?: number
}

interface PlayerActionResponse {
  message?: string
  game_state?: Partial<GameStateModel>
  needs_backend_trigger?: boolean
  error?: string
  status_code?: number
}

interface RollDiceResponse extends DiceRollResultModel {
  error?: string
}

interface TriggerNextStepResponse {
  message?: string
  processed?: boolean
  error?: string
  status_code?: number
}

interface RetryResponse {
  message?: string
  retried?: boolean
  error?: string
  status_code?: number
}

interface SaveGameResponse {
  message?: string
  saved?: boolean
  save_path?: string
  error?: string
  status_code?: number
}

export const gameApi = {
  /**
   * Get current game state
   */
  async getGameState(params: GameStateParams = {}): Promise<AxiosResponse<GameStateResponse>> {
    return apiClient.get<GameStateResponse>('/api/game_state', { params })
  },

  /**
   * Poll for game state updates (using same endpoint as getGameState for now)
   */
  async pollGameState(params: GameStateParams = {}): Promise<AxiosResponse<GameStateResponse>> {
    return apiClient.get<GameStateResponse>('/api/game_state', { params })
  },

  /**
   * Send a player action (message) to the game
   */
  async sendMessage(message: string): Promise<AxiosResponse<PlayerActionResponse>> {
    return apiClient.post<PlayerActionResponse>('/api/player_action', {
      action_type: 'free_text',
      value: message
    })
  },

  /**
   * Perform an immediate dice roll
   */
  async rollDice(diceData: RollDiceParams): Promise<AxiosResponse<RollDiceResponse>> {
    return apiClient.post<RollDiceResponse>('/api/perform_roll', diceData)
  },

  /**
   * Submit dice roll results
   */
  async submitRolls(rollResults: DiceRollResultModel[]): Promise<AxiosResponse<PlayerActionResponse>> {
    return apiClient.post<PlayerActionResponse>('/api/submit_rolls', {
      roll_results: rollResults
    })
  },

  /**
   * Respond to a dice request (using submit_rolls)
   */
  async respondToDiceRequest(_requestId: string, responseData: DiceRollResultModel): Promise<AxiosResponse<PlayerActionResponse>> {
    return apiClient.post<PlayerActionResponse>('/api/submit_rolls', {
      roll_results: [responseData]
    })
  },

  /**
   * Trigger next step (NPC turns, etc.)
   */
  async triggerNextStep(): Promise<AxiosResponse<TriggerNextStepResponse>> {
    return apiClient.post<TriggerNextStepResponse>('/api/trigger_next_step')
  },

  /**
   * Retry last AI request
   */
  async retryLastAiRequest(): Promise<AxiosResponse<RetryResponse>> {
    return apiClient.post<RetryResponse>('/api/retry_last_ai_request')
  },

  /**
   * Start a campaign (using campaign API)
   */
  async startCampaign(campaignId: string): Promise<AxiosResponse<GameStateResponse>> {
    return apiClient.post<GameStateResponse>(`/api/campaigns/${campaignId}/start`)
  },

  /**
   * Load a campaign (get campaign state)
   */
  async loadCampaign(campaignId: string): Promise<AxiosResponse<GameStateResponse>> {
    return apiClient.post<GameStateResponse>(`/api/campaigns/${campaignId}/start`)
  },

  /**
   * Player action (general action handler)
   */
  async sendPlayerAction(actionType: string, actionValue: string | Record<string, unknown>): Promise<AxiosResponse<PlayerActionResponse>> {
    return apiClient.post<PlayerActionResponse>('/api/player_action', {
      action_type: actionType,
      value: actionValue
    })
  },

  /**
   * Perform a dice roll with specific parameters
   */
  async performRoll(rollParams: RollDiceParams): Promise<AxiosResponse<RollDiceResponse>> {
    return apiClient.post<RollDiceResponse>('/api/perform_roll', rollParams)
  },

  /**
   * Save the current game state
   */
  async saveGameState(): Promise<AxiosResponse<SaveGameResponse>> {
    return apiClient.post<SaveGameResponse>('/api/game_state/save')
  }
}
