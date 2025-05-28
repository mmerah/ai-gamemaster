import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { gameApi } from '../services/gameApi'
import { ttsApi } from '../services/ttsApi'
import { useAnimationSteps } from '../composables/useAnimationSteps'

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
  
  // Animation state
  const {
    animationSteps,
    currentStep,
    currentStepIndex,
    isAnimating,
    hasMoreSteps,
    totalSteps,
    animationSpeed,
    setAnimationSteps,
    playAnimation,
    skipToEnd,
    stopAnimation,
    reset: resetAnimation
  } = useAnimationSteps()

  // Helper to update game state from API response
  function updateGameStateFromResponse(data) {
    if (!data) return;
    
    // Check if we have animation steps
    if (data.animation_steps && data.animation_steps.length > 0) {
      // Store the final state to apply after animation
      const finalState = {
        campaign_id: data.campaign_id,
        campaign_name: data.campaign_name,
        chat_history: data.chat_history,
        party: data.party,
        combat_info: data.combat_info,
        location: data.location,
        location_description: data.location_description,
        dice_requests: data.dice_requests,
        can_retry_last_request: data.can_retry_last_request,
        needs_backend_trigger: data.needs_backend_trigger
      };
      
      // Set animation steps
      setAnimationSteps(data.animation_steps);
      
      // Play animation with intermediate updates
      playAnimation(async (step, index) => {
        updateIntermediateState(step);
        
        // Optional: Play narration audio if available
        if (step.narration_url && ttsState.enabled) {
          await playNarrationAudio(step.narration_url);
        }
      }).then(() => {
        // Apply final state when animation completes
        applyFinalState(finalState);
      });
    } else {
      // No animation, update immediately
      applyFinalState(data);
    }
  }
  
  // Helper to update intermediate animation state
  function updateIntermediateState(step) {
    // Add narrative to chat history
    if (step.narrative) {
      const animatedMsg = {
        id: `${Date.now()}-gm-animated`,
        type: 'gm',
        content: step.narrative,
        timestamp: new Date().toISOString(),
        animated: true
      };
      
      // Check if this message already exists to avoid duplicates
      const exists = gameState.chatHistory.some(msg => 
        msg.content === step.narrative && msg.type === 'gm'
      );
      
      if (!exists) {
        gameState.chatHistory.push(animatedMsg);
      }
    }
    
    // Update combat info
    if (step.combat_info) {
      gameState.combatState = {
        ...step.combat_info,
        isActive: step.combat_info.is_active || false,
        is_active: step.combat_info.is_active || false
      };
    }
    
    // Update party state (HP, conditions, etc.)
    if (step.party && Array.isArray(step.party)) {
      gameState.party = step.party.map(member => ({
        ...member,
        currentHp: member.currentHp || member.current_hp || member.hp || 0,
        maxHp: member.maxHp || member.max_hp || member.maximum_hp || 0,
        hp: member.currentHp || member.current_hp || member.hp || 0,
        char_class: member.class || member.char_class || 'Unknown',
        class: member.class || member.char_class || 'Unknown',
        name: member.name || 'Unknown',
        race: member.race || 'Unknown',
        level: member.level || 1,
        ac: member.ac || 10,
        conditions: member.conditions || [],
        stats: member.stats || {}
      }));
    }
    
    // Update recent chat messages from step
    if (step.chat_history && Array.isArray(step.chat_history)) {
      // Only add new messages not already in our history
      step.chat_history.forEach((msg, index) => {
        const formatted = formatBackendMessageToFrontend(msg, index);
        const exists = gameState.chatHistory.some(existing => 
          existing.content === formatted.content && 
          existing.type === formatted.type
        );
        if (!exists) {
          gameState.chatHistory.push(formatted);
        }
      });
    }
  }
  
  // Helper to apply final state
  function applyFinalState(data) {
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
  
  async function playNarrationAudio(audioUrl) {
    try {
      const audio = new Audio(audioUrl);
      await audio.play();
    } catch (error) {
      console.error('Failed to play narration audio:', error);
      // Don't throw - we don't want to interrupt animation if audio fails
    }
  }
  
  function skipAnimation() {
    skipToEnd();
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
    console.log('triggerNextStep called, setting isLoading to true');
    isLoading.value = true;
    try {
      const response = await gameApi.triggerNextStep();
      console.log('triggerNextStep response received:', response.data);
      updateGameStateFromResponse(response.data);
      console.log('After update - needsBackendTrigger:', gameState.needsBackendTrigger);
    } catch (error) {
      console.error('Failed to trigger next step:', error);
      gameState.chatHistory.push(formatBackendMessageToFrontend({ 
        role: 'system', 
        content: `Error triggering next step: ${error.message}`
      }, gameState.chatHistory.length));
      throw error;
    } finally {
      console.log('triggerNextStep finally block, setting isLoading to false');
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
    // Animation functions
    isAnimating,
    currentStep,
    currentStepIndex,
    totalSteps,
    animationSpeed,
    skipAnimation,
    hasMoreSteps
  }
})
