import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { gameApi } from '../services/gameApi'
import { ttsApi } from '../services/ttsApi'

// Helper to format backend chat messages if they are not already in frontend format
function formatBackendMessageToFrontend(backendMsg, index) {
  // Check if message is already in frontend format (has 'type' field)
  if (backendMsg.type) {
    return backendMsg; // Already formatted
  }
  
  // Convert backend format to frontend format
  let type = 'system';
  if (backendMsg.role === 'assistant') type = 'gm';
  else if (backendMsg.role === 'user') type = 'user';
  else if (backendMsg.sender === 'GM') type = 'gm';
  else if (backendMsg.sender === 'Player' || backendMsg.sender === 'user') type = 'user';

  const formatted = {
    id: backendMsg.id || `${Date.now()}-${index}`,
    type: type,
    content: backendMsg.content || backendMsg.message || '',
    timestamp: backendMsg.timestamp || new Date().toISOString(),
    gm_thought: backendMsg.gm_thought
  };

  // Include TTS audio URL if available
  if (backendMsg.tts_audio_url) {
    formatted.tts_audio_url = backendMsg.tts_audio_url;
  }

  return formatted;
}

export const useGameStore = defineStore('game', () => {
  // State
  const gameState = reactive({
    campaignId: null,
    campaignName: 'No Campaign Loaded',
    chatHistory: [],
    party: [],
    combatState: { isActive: false },
    mapState: null,
    location: null,
    locationDescription: null,
    diceRequests: [],
    gameSettings: {},
    canRetryLastRequest: false,
    needsBackendTrigger: false,
  })

  // TTS State
  const ttsState = reactive({
    enabled: false,
    autoPlay: false,
    voiceId: null,
    availableVoices: [],
    isLoading: false
  })

  const isLoading = ref(false)
  const lastPollTime = ref(null)

  // Helper to update game state from API response
  function updateGameStateFromResponse(data) {
    if (!data) return;

    // Campaign info
    if (data.campaign_id) gameState.campaignId = data.campaign_id;
    if (data.campaign_name) gameState.campaignName = data.campaign_name;
    
    // Chat history - handle both formats
    if (data.chat_history) {
      gameState.chatHistory = data.chat_history.map((msg, index) => 
        formatBackendMessageToFrontend(msg, index)
      );
    }

    // Party: Map backend field names to frontend expectations
    if (data.party && Array.isArray(data.party)) {
      gameState.party = data.party.map(member => ({
        ...member,
        // Map backend field names to frontend expectations - ensure consistent naming
        currentHp: member.currentHp || member.current_hp || member.hp || 0,
        maxHp: member.maxHp || member.max_hp || member.maximum_hp || 0,
        hp: member.currentHp || member.current_hp || member.hp || 0, // Legacy compatibility
        char_class: member.class || member.char_class || 'Unknown',
        class: member.class || member.char_class || 'Unknown', // Ensure both formats work
        // Ensure all expected fields exist
        name: member.name || 'Unknown',
        race: member.race || 'Unknown',
        level: member.level || 1,
        ac: member.ac || 10,
        conditions: member.conditions || [],
        stats: member.stats || {}
      }));
    } else {
      gameState.party = [];
    }

    // Combat State - map backend field names
    if (data.combat_info) {
      gameState.combatState = {
        ...data.combat_info,
        isActive: data.combat_info.is_active || false,
        is_active: data.combat_info.is_active || false // Keep both for compatibility
      };
    } else {
      gameState.combatState = { isActive: false, is_active: false };
    }

    // Location info
    gameState.location = data.location || null;
    gameState.locationDescription = data.location_description || null;

    // Map State
    if (data.location && data.location_description) {
      gameState.mapState = {
        name: data.location,
        description: data.location_description,
        image: data.map_image || null,
        markers: data.map_markers || []
      };
    } else {
      gameState.mapState = null;
    }

    gameState.diceRequests = data.dice_requests || [];
    gameState.canRetryLastRequest = data.can_retry_last_request || false;
    gameState.needsBackendTrigger = data.needs_backend_trigger || false;
  }

  // TTS Functions
  async function loadTTSVoices() {
    if (ttsState.availableVoices.length > 0) return ttsState.availableVoices;
    
    ttsState.isLoading = true;
    try {
      const response = await ttsApi.getVoices();
      // Backend returns { voices: [...] }
      const voices = response.voices || [];
      ttsState.availableVoices = voices;
      return voices;
    } catch (error) {
      console.error('Failed to load TTS voices:', error);
      return [];
    } finally {
      ttsState.isLoading = false;
    }
  }

  function enableTTS(voiceId = null) {
    ttsState.enabled = true;
    if (voiceId) {
      ttsState.voiceId = voiceId;
    }
  }

  function disableTTS() {
    ttsState.enabled = false;
    ttsState.autoPlay = false;
  }

  function setTTSVoice(voiceId) {
    ttsState.voiceId = voiceId;
    if (voiceId) {
      ttsState.enabled = true;
    }
  }

  function setAutoPlay(enabled) {
    ttsState.autoPlay = enabled;
  }

  async function previewVoice(voiceId, sampleText = null) {
    try {
      return await ttsApi.previewVoice(voiceId, sampleText);
    } catch (error) {
      console.error('Failed to preview voice:', error);
      throw error;
    }
  }

  async function loadGameState() {
    isLoading.value = true
    try {
      const response = await gameApi.getGameState()
      updateGameStateFromResponse(response.data);
      lastPollTime.value = Date.now()
    } catch (error) {
      console.error('Failed to load game state:', error)
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error loading game state: ${error.message}`
      }, gameState.chatHistory.length));
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Alias for GameView.vue compatibility
  async function initializeGame() {
    return await loadGameState();
  }

  async function pollGameState() {
    try {
      const response = await gameApi.pollGameState({ t: lastPollTime.value });
      updateGameStateFromResponse(response.data);
      lastPollTime.value = Date.now()
    } catch (error) {
      console.error('Failed to poll game state:', error)
      throw error
    }
  }

  async function sendMessage(messageText) {
    isLoading.value = true;
    try {
      // Optimistically add user message
      gameState.chatHistory.push({
        id: `${Date.now()}-user`,
        type: 'user',
        content: messageText,
        timestamp: new Date().toISOString()
      });

      const response = await gameApi.sendMessage(messageText)
      
      updateGameStateFromResponse(response.data);
      return response.data
    } catch (error) {
      console.error('Failed to send message:', error)
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error sending message: ${error.message}`
      }, gameState.chatHistory.length));
      throw error
    } finally {
      isLoading.value = false;
    }
  }

  async function rollDice(diceExpression) {
    try {
      const result = Math.floor(Math.random() * parseInt(diceExpression.substring(1))) + 1;
      gameState.chatHistory.push({
        id: `${Date.now()}-dice`,
        type: 'dice',
        content: `Rolled ${diceExpression}: ${result}`,
        details: { expression: diceExpression, result: result, breakdown: `[${result}]` },
        timestamp: new Date().toISOString()
      });
      return { result };
    } catch (error) {
      console.error('Failed to roll dice:', error);
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error rolling dice: ${error.message}`
      }, gameState.chatHistory.length));
      throw error
    }
  }

  async function performRoll(rollParams) {
    try {
      const response = await gameApi.rollDice(rollParams);
      
      if (response.data && !response.data.error) {
        return response.data;
      } else {
        throw new Error(response.data?.error || "Failed to perform roll via API");
      }
    } catch (error) {
      console.error('Failed to perform roll:', error);
      throw error;
    }
  }

  async function performAndSubmitRoll(requestedRollData) {
    isLoading.value = true;
    try {
      const rollResponse = await gameApi.rollDice({
        character_id: requestedRollData.character_id_to_roll,
        roll_type: requestedRollData.type,
        dice_formula: requestedRollData.dice_formula,
        skill: requestedRollData.skill,
        ability: requestedRollData.ability,
        dc: requestedRollData.dc,
        reason: requestedRollData.reason,
        request_id: requestedRollData.request_id
      });

      if (rollResponse.data && !rollResponse.data.error) {
        const submitResponse = await gameApi.submitRolls([rollResponse.data]);
        updateGameStateFromResponse(submitResponse.data);
        return { singleRollResult: rollResponse.data, finalState: submitResponse.data };
      } else {
        throw new Error(rollResponse.data?.error || "Failed to perform roll via API");
      }
    } catch (error) {
      console.error('Failed to perform and submit roll:', error);
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error with dice roll: ${error.message}`
      }, gameState.chatHistory.length));
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function submitMultipleCompletedRolls(completedRollsArray) {
    isLoading.value = true;
    try {
      const response = await gameApi.submitRolls(completedRollsArray);
      updateGameStateFromResponse(response.data);
    } catch (error) {
      console.error('Failed to submit multiple rolls:', error);
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error submitting rolls: ${error.message}`
      }, gameState.chatHistory.length));
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function startCampaign(campaignId) {
    isLoading.value = true
    try {
      const response = await gameApi.startCampaign(campaignId)
      if (response.data && response.data.initial_state) {
        const initialStateFromServer = response.data.initial_state;
        
        // Prepare a state object that matches what updateGameStateFromResponse expects
        const formattedInitialState = {
          campaign_id: initialStateFromServer.campaign_id,
          campaign_name: initialStateFromServer.campaign_name || 'Campaign Loaded',
          chat_history: (initialStateFromServer.chat_history || []),
          party: Object.values(initialStateFromServer.party || {}),
          combat_info: initialStateFromServer.combat || { isActive: false },
          location: initialStateFromServer.current_location?.name,
          location_description: initialStateFromServer.current_location?.description,
          dice_requests: initialStateFromServer.pending_player_dice_requests || [],
          can_retry_last_request: false,
          needs_backend_trigger: initialStateFromServer.needs_backend_trigger || false,
        };
        
        updateGameStateFromResponse(formattedInitialState);
        console.log(`Loaded campaign: ${gameState.campaignName}`);
      } else {
        throw new Error("Initial state not found in campaign start response.");
      }
    } catch (error) {
      console.error('Failed to start campaign:', error)
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error starting campaign: ${error.message}`
      }, gameState.chatHistory.length));
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function resetGameState() {
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
      gameSettings: {},
      canRetryLastRequest: false,
      needsBackendTrigger: false,
    })
    lastPollTime.value = null
  }
  
  async function triggerNextStep() {
    isLoading.value = true;
    try {
      const response = await gameApi.triggerNextStep();
      updateGameStateFromResponse(response.data);
    } catch (error) {
      console.error('Failed to trigger next step:', error);
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error triggering next step: ${error.message}`
      }, gameState.chatHistory.length));
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function retryLastAIRequest() {
    isLoading.value = true;
    try {
      const response = await gameApi.retryLastAiRequest();
      updateGameStateFromResponse(response.data);
    } catch (error) {
      console.error('Failed to retry last AI request:', error);
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error retrying request: ${error.message}`
      }, gameState.chatHistory.length));
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    gameState,
    ttsState,
    isLoading,
    loadGameState,
    initializeGame,
    pollGameState,
    sendMessage,
    rollDice,
    performRoll,
    performAndSubmitRoll,
    submitMultipleCompletedRolls,
    startCampaign,
    resetGameState,
    triggerNextStep,
    retryLastAIRequest,
    // TTS functions
    loadTTSVoices,
    enableTTS,
    disableTTS,
    setTTSVoice,
    setAutoPlay,
    previewVoice,
  }
})
