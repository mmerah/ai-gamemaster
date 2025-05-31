import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { gameApi } from '../services/gameApi'
import { ttsApi } from '../services/ttsApi'
import eventService from '@/services/eventService'

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
  const isConnected = ref(false)
  
  // Event handlers
  const eventHandlers = {
    // Narrative events (handled by chatStore, included here for completeness)
    narrative_added: (event) => {
      const message = {
        id: event.message_id || event.event_id,
        type: mapRoleToType(event.role),
        content: event.content,
        timestamp: event.timestamp,
        gm_thought: event.gm_thought,
        tts_audio_url: event.audio_path ? `/static/${event.audio_path}` : null
      }
      
      // Check for duplicates
      const exists = gameState.chatHistory.some(m => m.id === message.id)
      if (!exists) {
        gameState.chatHistory.push(message)
        
        // Auto-play TTS if enabled
        if (ttsState.enabled && ttsState.autoPlay && message.tts_audio_url && event.role === 'assistant') {
          playNarrationAudio(message.tts_audio_url)
        }
      }
    },
    
    // Combat state events
    combat_started: (event) => {
      gameState.combatState = {
        isActive: true,
        is_active: true,
        combatants: event.combatants || [],
        round_number: event.round_number || 1,
        current_turn_index: -1
      }
    },
    
    combat_ended: (event) => {
      gameState.combatState = {
        isActive: false,
        is_active: false,
        reason: event.reason,
        outcome_description: event.outcome_description
      }
      // Clear any pending dice requests when combat ends
      gameState.diceRequests = []
    },
    
    // Turn management
    turn_advanced: (event) => {
      if (gameState.combatState.isActive) {
        const combatantIndex = gameState.combatState.combatants?.findIndex(
          c => c.id === event.new_combatant_id
        )
        if (combatantIndex !== -1) {
          gameState.combatState.current_turn_index = combatantIndex
          gameState.combatState.round_number = event.round_number
        }
      }
    },
    
    // Combatant updates
    combatant_hp_changed: (event) => {
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
    
    combatant_status_changed: (event) => {
      // Update combat state
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        const combatant = gameState.combatState.combatants.find(c => c.id === event.combatant_id)
        if (combatant) {
          combatant.conditions = event.new_conditions || []
          combatant.is_defeated = event.is_defeated || false
        }
      }
      
      // Update party member if it's a PC
      if (event.is_player_controlled !== false) {
        const partyMember = gameState.party.find(p => p.id === event.combatant_id)
        if (partyMember) {
          partyMember.conditions = event.new_conditions || []
        }
      }
    },
    
    // Initiative events
    combatant_initiative_set: (event) => {
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        const combatant = gameState.combatState.combatants.find(c => c.id === event.combatant_id)
        if (combatant) {
          combatant.initiative = event.initiative_value
        }
      }
    },
    
    initiative_order_determined: (event) => {
      if (gameState.combatState.isActive) {
        gameState.combatState.combatants = event.ordered_combatants
      }
    },
    
    // Dice events
    player_dice_request_added: (event) => {
      console.log('Processing player_dice_request_added event:', event)
      console.log('Current dice requests before adding:', [...gameState.diceRequests])
      
      // Check for duplicates
      const exists = gameState.diceRequests.some(r => r.request_id === event.request_id)
      if (!exists) {
        const diceRequest = {
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
    
    player_dice_requests_cleared: (event) => {
      if (event.cleared_request_ids && event.cleared_request_ids.length > 0) {
        gameState.diceRequests = gameState.diceRequests.filter(
          r => !event.cleared_request_ids.includes(r.request_id)
        )
      }
    },
    
    // Combatant management
    combatant_added: (event) => {
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        const newCombatant = {
          id: event.combatant_id,
          name: event.combatant_name,
          current_hp: event.hp,
          max_hp: event.max_hp,
          armor_class: event.ac,
          is_player: event.is_player_controlled,
          position_in_order: event.position_in_order
        }
        
        // Insert at correct position if specified
        if (event.position_in_order !== undefined) {
          gameState.combatState.combatants.splice(event.position_in_order, 0, newCombatant)
        } else {
          gameState.combatState.combatants.push(newCombatant)
        }
      }
    },
    
    combatant_removed: (event) => {
      if (gameState.combatState.isActive && gameState.combatState.combatants) {
        gameState.combatState.combatants = gameState.combatState.combatants.filter(
          c => c.id !== event.combatant_id
        )
      }
    },
    
    // Location events
    location_changed: (event) => {
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
    party_member_updated: (event) => {
      const member = gameState.party.find(p => p.id === event.character_id)
      if (member && event.changes) {
        Object.assign(member, event.changes)
        
        // Ensure consistent field naming
        if (event.changes.current_hp !== undefined) {
          member.currentHp = event.changes.current_hp
          member.hp = event.changes.current_hp
        }
        if (event.changes.max_hp !== undefined) {
          member.maxHp = event.changes.max_hp
          member.max_hp = event.changes.max_hp
        }
      }
    },
    
    // Quest events
    quest_updated: (event) => {
      // For now, just add to chat history as system message
      gameState.chatHistory.push({
        id: event.event_id,
        type: 'system',
        content: `Quest Updated: ${event.quest_title} - ${event.new_status}`,
        timestamp: event.timestamp
      })
    },
    
    // Item events
    item_added: (event) => {
      // For now, just add to chat history as system message
      gameState.chatHistory.push({
        id: event.event_id,
        type: 'system',
        content: `${event.character_name} received: ${event.item_name}${event.quantity > 1 ? ` x${event.quantity}` : ''}`,
        timestamp: event.timestamp
      })
    },
    
    // System events
    backend_processing: (event) => {
      isLoading.value = event.is_processing
      gameState.needsBackendTrigger = event.needs_backend_trigger || false
    },
    
    game_error: (event) => {
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
    
    game_state_snapshot: (event) => {
      // Full state sync - used for reconnection
      console.log('Received game state snapshot:', event)
      
      // Update all state from snapshot
      if (event.campaign_id) gameState.campaignId = event.campaign_id
      if (event.campaign_name) gameState.campaignName = event.campaign_name
      
      // Handle location - it comes as an object with name and description
      if (event.location) {
        if (typeof event.location === 'object') {
          gameState.location = event.location.name || 'Unknown Location'
          gameState.locationDescription = event.location.description || ''
        } else {
          gameState.location = event.location
        }
      }
      if (event.location_description) gameState.locationDescription = event.location_description
      
      // Update party
      if (event.party_members) {
        console.log('Processing party_members from snapshot:', event.party_members)
        gameState.party = event.party_members.map(member => {
          const processedMember = {
            ...member,
            currentHp: member.current_hp || member.hp || 0,
            maxHp: member.max_hp || member.maximum_hp || 0,
            hp: member.current_hp || member.hp || 0,
            char_class: member.class || member.char_class || 'Unknown',
            class: member.class || member.char_class || 'Unknown'
          }
          console.log(`Processed party member ${member.name}:`, processedMember)
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
            character_id_to_roll: request.character_id || request.character_id_to_roll,
            character_name: request.character_name,
            type: request.roll_type || request.type,
            roll_type: request.roll_type || request.type,
            dice_formula: request.dice_formula,
            purpose: request.purpose || request.reason,
            reason: request.purpose || request.reason,
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
          tts_audio_url: msg.audio_path ? `/static/${msg.audio_path}` : null
        }))
      }
    }
  }
  
  // Helper functions
  function mapRoleToType(role) {
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
  
  async function playNarrationAudio(audioUrl) {
    try {
      const audio = new Audio(audioUrl)
      await audio.play()
    } catch (error) {
      console.error('Failed to play narration audio:', error)
    }
  }
  
  // Initialize event handlers
  function initializeEventHandlers() {
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
  function cleanupEventHandlers() {
    Object.entries(eventHandlers).forEach(([eventType, handler]) => {
      eventService.off(eventType, handler)
    })
  }

  // TTS Functions
  async function loadTTSVoices() {
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

  function enableTTS(voiceId = null) {
    ttsState.enabled = true
    if (voiceId) {
      ttsState.voiceId = voiceId
    }
  }

  function disableTTS() {
    ttsState.enabled = false
    ttsState.autoPlay = false
  }

  function setTTSVoice(voiceId) {
    ttsState.voiceId = voiceId
    if (voiceId) {
      ttsState.enabled = true
    }
  }

  function setAutoPlay(enabled) {
    ttsState.autoPlay = enabled
  }

  async function previewVoice(voiceId, sampleText = null) {
    try {
      return await ttsApi.previewVoice(voiceId, sampleText)
    } catch (error) {
      console.error('Failed to preview voice:', error)
      throw error
    }
  }

  // Game Actions (these trigger backend changes, which then emit events)
  async function loadGameState() {
    isLoading.value = true
    try {
      // Request game state with snapshot event
      // The actual state updates will come via SSE events
      const response = await gameApi.getGameState({ emit_snapshot: true })
      
      // Just return the response - let SSE events handle all state updates
      // The game_state_snapshot event will be emitted and handled by eventRouter
      return response.data
    } catch (error) {
      console.error('Failed to load game state:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error loading game state: ${error.message}`,
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
  async function initializeGame() {
    return await loadGameState()
  }

  /**
   * Legacy polling function - no longer used
   * @deprecated State updates now come via SSE events
   */
  async function pollGameState() {
    console.log('pollGameState called but ignored - using SSE events')
  }

  async function sendMessage(messageText) {
    isLoading.value = true
    try {
      // Don't add message here - let the event handler do it to avoid duplicates
      const response = await gameApi.sendMessage(messageText)
      
      // The response will trigger events via SSE
      // No need to update state here
      return response.data
    } catch (error) {
      console.error('Failed to send message:', error)
      gameState.chatHistory.push({
        id: `error-${Date.now()}`,
        type: 'system',
        content: `Error sending message: ${error.message}`,
        timestamp: new Date().toISOString()
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function rollDice(diceExpression) {
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
    } catch (error) {
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

  async function performRoll(rollParams) {
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

  async function performAndSubmitRoll(requestedRollData) {
    isLoading.value = true
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
      })

      if (rollResponse.data && !rollResponse.data.error) {
        const submitResponse = await gameApi.submitRolls([rollResponse.data])
        // Events will update the state
        return { singleRollResult: rollResponse.data, finalState: submitResponse.data }
      } else {
        throw new Error(rollResponse.data?.error || "Failed to perform roll via API")
      }
    } catch (error) {
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

  async function submitMultipleCompletedRolls(completedRollsArray) {
    isLoading.value = true
    try {
      const response = await gameApi.submitRolls(completedRollsArray)
      // Events will update the state
      return response.data
    } catch (error) {
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

  async function startCampaign(campaignId) {
    isLoading.value = true
    try {
      const response = await gameApi.startCampaign(campaignId)
      
      // The backend will emit events to update the state
      // Just return the response
      return response.data
    } catch (error) {
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
  }
  
  async function triggerNextStep() {
    console.log('triggerNextStep called')
    isLoading.value = true
    try {
      const response = await gameApi.triggerNextStep()
      console.log('triggerNextStep response received:', response.data)
      // Events will update the state
      return response.data
    } catch (error) {
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

  async function retryLastAIRequest() {
    isLoading.value = true
    try {
      const response = await gameApi.retryLastAiRequest()
      // Events will update the state
      return response.data
    } catch (error) {
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