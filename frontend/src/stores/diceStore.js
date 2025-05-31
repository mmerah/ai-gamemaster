/**
 * Dice Store - Manages dice roll requests and results
 * 
 * This store handles all dice-related functionality in the game:
 * - Tracking pending dice requests from the GM
 * - Managing completed rolls before submission
 * - Handling the UI state for rolling and submitting
 * 
 * The store uses the Composition API pattern for better TypeScript support
 * and more flexible state management.
 * 
 * @module diceStore
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useDiceStore = defineStore('dice', () => {
  /**
   * State
   */
  
  /**
   * Array of pending dice roll requests from the GM
   * @type {Ref<Array<{request_id: string, character_id: string, roll_type: string, dice_formula: string}>>}
   */
  const pendingRequests = ref([])
  
  /**
   * Map storing completed roll results keyed by "{requestId}-{characterId}"
   * @type {Ref<Map<string, object>>}
   */
  const completedRolls = ref(new Map())
  
  /**
   * UI state - indicates if a roll is currently being performed
   * @type {Ref<boolean>}
   */
  const isRolling = ref(false)
  
  /**
   * UI state - indicates if rolls are being submitted to the backend
   * @type {Ref<boolean>}
   */
  const isSubmitting = ref(false)
  
  /**
   * Computed Properties
   */
  
  /**
   * Check if there are any pending dice requests
   * @type {ComputedRef<boolean>}
   */
  const hasPendingRequests = computed(() => pendingRequests.value.length > 0)
  
  /**
   * Check if there are any completed rolls waiting to be submitted
   * @type {ComputedRef<boolean>}
   */
  const hasCompletedRolls = computed(() => completedRolls.value.size > 0)
  
  const allRequestsCompleted = computed(() => {
    if (pendingRequests.value.length === 0) return false
    
    return pendingRequests.value.every(request => {
      const key = `${request.request_id}-${request.character_id_to_roll || request.character_id}`
      return completedRolls.value.has(key)
    })
  })
  
  // Actions
  function handlePlayerDiceRequestAdded(event) {
    console.log('DiceStore: Player dice request added:', event)
    console.log('Current pending requests before adding:', [...pendingRequests.value])
    
    // Check for duplicates - consider both request_id AND character_id
    // This handles cases where backend uses same request_id for multiple characters
    const exists = pendingRequests.value.some(r => 
      r.request_id === event.request_id && 
      r.character_id === event.character_id
    )
    if (!exists) {
      const diceRequest = {
        request_id: event.request_id,
        character_id: event.character_id,
        character_id_to_roll: event.character_id,
        character_name: event.character_name,
        roll_type: event.roll_type,
        type: event.roll_type,
        dice_formula: event.dice_formula,
        purpose: event.purpose,
        reason: event.purpose,
        dc: event.dc,
        skill: event.skill,
        ability: event.ability,
        timestamp: event.timestamp
      }
      
      // Use array spread to ensure reactivity
      pendingRequests.value = [...pendingRequests.value, diceRequest]
      
      console.log('Added dice request:', diceRequest)
      console.log('Total pending requests:', pendingRequests.value.length)
    } else {
      console.log('Dice request already exists, skipping:', event.request_id)
    }
  }
  
  function handlePlayerDiceRequestsCleared(event) {
    console.log('DiceStore: Player dice requests cleared:', event)
    
    if (event.cleared_request_ids && event.cleared_request_ids.length > 0) {
      // Remove cleared requests
      pendingRequests.value = pendingRequests.value.filter(
        r => !event.cleared_request_ids.includes(r.request_id)
      )
      
      // Also clear any completed rolls for these requests
      event.cleared_request_ids.forEach(requestId => {
        // Remove all rolls associated with this request
        const keysToRemove = []
        completedRolls.value.forEach((_, key) => {
          if (key.startsWith(`${requestId}-`)) {
            keysToRemove.push(key)
          }
        })
        keysToRemove.forEach(key => completedRolls.value.delete(key))
      })
      
      console.log('Remaining pending requests:', pendingRequests.value.length)
    }
  }
  
  function handleGameStateSnapshot(snapshotData) {
    if (!snapshotData || !snapshotData.pending_dice_requests) return
    
    console.log('DiceStore: Processing snapshot dice requests:', snapshotData.pending_dice_requests)
    
    // Only set from snapshot if we don't have any pending requests
    if (pendingRequests.value.length === 0) {
      pendingRequests.value = snapshotData.pending_dice_requests.map(request => ({
        ...request,
        // Normalize field names
        request_id: request.request_id,
        character_id: request.character_id || request.character_id_to_roll,
        character_id_to_roll: request.character_id || request.character_id_to_roll,
        character_name: request.character_name,
        roll_type: request.roll_type || request.type,
        type: request.roll_type || request.type,
        dice_formula: request.dice_formula,
        purpose: request.purpose || request.reason,
        reason: request.purpose || request.reason,
        dc: request.dc,
        skill: request.skill,
        ability: request.ability
      }))
      
      console.log('Loaded dice requests from snapshot:', pendingRequests.value.length)
    } else {
      console.log('Skipping snapshot dice requests - already have pending requests from events')
    }
  }
  
  function addCompletedRoll(requestId, characterId, rollResult) {
    const key = `${requestId}-${characterId}`
    completedRolls.value.set(key, rollResult)
    console.log('Added completed roll:', key, rollResult)
  }
  
  function getCompletedRoll(requestId, characterId) {
    const key = `${requestId}-${characterId}`
    return completedRolls.value.get(key)
  }
  
  function clearCompletedRolls() {
    completedRolls.value.clear()
  }
  
  function clearAllRequests() {
    pendingRequests.value = []
    completedRolls.value.clear()
    isRolling.value = false
    isSubmitting.value = false
  }
  
  return {
    // State
    pendingRequests,
    completedRolls,
    isRolling,
    isSubmitting,
    
    // Computed
    hasPendingRequests,
    hasCompletedRolls,
    allRequestsCompleted,
    
    // Actions
    handlePlayerDiceRequestAdded,
    handlePlayerDiceRequestsCleared,
    handleGameStateSnapshot,
    addCompletedRoll,
    getCompletedRoll,
    clearCompletedRolls,
    clearAllRequests
  }
})