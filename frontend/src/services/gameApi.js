import { apiClient } from './apiClient'

export const gameApi = {
  // Get current game state
  async getGameState(params = {}) {
    return apiClient.get('/api/game_state', { params })
  },

  // Poll for game state updates (using same endpoint as getGameState for now)
  async pollGameState(params = {}) {
    return apiClient.get('/api/game_state', { params })
  },

  // Send a player action (message) to the game - FIXED to match backend expectations
  async sendMessage(message) {
    return apiClient.post('/api/player_action', {
      action_type: 'free_text',
      value: message
    })
  },

  // Perform an immediate dice roll
  async rollDice(diceData) {
    return apiClient.post('/api/perform_roll', diceData)
  },

  // Submit dice roll results - FIXED to match backend expectations
  async submitRolls(rollResults) {
    return apiClient.post('/api/submit_rolls', {
      roll_results: rollResults
    })
  },

  // Respond to a dice request (using submit_rolls)
  async respondToDiceRequest(requestId, responseData) {
    return apiClient.post('/api/submit_rolls', {
      roll_results: [responseData]
    })
  },

  // Trigger next step (NPC turns, etc.)
  async triggerNextStep() {
    return apiClient.post('/api/trigger_next_step')
  },

  // Retry last AI request
  async retryLastAiRequest() {
    return apiClient.post('/api/retry_last_ai_request')
  },

  // Start a campaign (using campaign API)
  async startCampaign(campaignId) {
    return apiClient.post(`/api/campaigns/${campaignId}/start`)
  },

  // Load a campaign (get campaign state)
  async loadCampaign(campaignId) {
    return apiClient.post(`/api/campaigns/${campaignId}/start`)
  },

  // Player action (general action handler) - FIXED to match backend expectations
  async sendPlayerAction(actionType, actionValue) {
    return apiClient.post('/api/player_action', {
      action_type: actionType,
      value: actionValue
    })
  },

  // Perform a dice roll with specific parameters
  async performRoll(rollParams) {
    return apiClient.post('/api/perform_roll', rollParams)
  },
  
  // Save the current game state
  async saveGameState() {
    return apiClient.post('/api/game_state/save')
  }
}
