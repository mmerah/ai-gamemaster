import { apiClient } from './apiClient'
import type { AxiosResponse } from 'axios'
import type {
  GameStateModel,
  DiceRollResultResponseModel,
  SaveGameResponse,
  PerformRollRequest,
  GameEventResponseModel,
  StartCampaignResponse
} from '@/types/unified'


// API Parameter Types
interface GameStateParams {
  emit_snapshot?: boolean
  _t?: number  // Timestamp for cache busting
}


export const gameApi = {
  /**
   * Get current game state
   */
  async getGameState(params: GameStateParams = {}): Promise<AxiosResponse<GameStateModel>> {
    return apiClient.get<GameStateModel>('/api/game_state', { params })
  },

  /**
   * Poll for game state updates (using same endpoint as getGameState for now)
   */
  async pollGameState(params: GameStateParams = {}): Promise<AxiosResponse<GameStateModel>> {
    return apiClient.get<GameStateModel>('/api/game_state', { params })
  },

  /**
   * Send a player action (message) to the game
   */
  async sendMessage(message: string): Promise<AxiosResponse<GameEventResponseModel>> {
    return apiClient.post<GameEventResponseModel>('/api/player_action', {
      action_type: 'free_text',
      value: message
    })
  },

  /**
   * Perform an immediate dice roll
   */
  async rollDice(diceData: PerformRollRequest): Promise<AxiosResponse<DiceRollResultResponseModel>> {
    return apiClient.post<DiceRollResultResponseModel>('/api/perform_roll', diceData)
  },

  /**
   * Submit dice roll results
   */
  async submitRolls(rollResults: DiceRollResultResponseModel[]): Promise<AxiosResponse<GameEventResponseModel>> {
    return apiClient.post<GameEventResponseModel>('/api/submit_rolls', {
      roll_results: rollResults
    })
  },

  /**
   * Respond to a dice request (using submit_rolls)
   */
  async respondToDiceRequest(_requestId: string, responseData: DiceRollResultResponseModel): Promise<AxiosResponse<GameEventResponseModel>> {
    return apiClient.post<GameEventResponseModel>('/api/submit_rolls', {
      roll_results: [responseData]
    })
  },

  /**
   * Trigger next step (NPC turns, etc.)
   */
  async triggerNextStep(): Promise<AxiosResponse<GameEventResponseModel>> {
    return apiClient.post<GameEventResponseModel>('/api/trigger_next_step')
  },

  /**
   * Retry last AI request
   */
  async retryLastAiRequest(): Promise<AxiosResponse<GameEventResponseModel>> {
    return apiClient.post<GameEventResponseModel>('/api/retry_last_ai_request')
  },

  /**
   * Start a campaign (using campaign API)
   */
  async startCampaign(campaignId: string): Promise<AxiosResponse<StartCampaignResponse>> {
    return apiClient.post<StartCampaignResponse>(`/api/campaigns/${campaignId}/start`)
  },

  /**
   * Load a campaign (get campaign state)
   */
  async loadCampaign(campaignId: string): Promise<AxiosResponse<StartCampaignResponse>> {
    return apiClient.post<StartCampaignResponse>(`/api/campaigns/${campaignId}/start`)
  },

  /**
   * Player action (general action handler)
   */
  async sendPlayerAction(actionType: string, actionValue: string | Record<string, unknown>): Promise<AxiosResponse<GameEventResponseModel>> {
    return apiClient.post<GameEventResponseModel>('/api/player_action', {
      action_type: actionType,
      value: actionValue
    })
  },

  /**
   * Perform a dice roll with specific parameters
   */
  async performRoll(rollParams: PerformRollRequest): Promise<AxiosResponse<DiceRollResultResponseModel>> {
    return apiClient.post<DiceRollResultResponseModel>('/api/perform_roll', rollParams)
  },

  /**
   * Save the current game state
   */
  async saveGameState(): Promise<AxiosResponse<SaveGameResponse>> {
    return apiClient.post<SaveGameResponse>('/api/game_state/save')
  }
}
