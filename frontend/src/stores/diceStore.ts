/**
 * Dice Store - Manages dice roll requests and results
 *
 * This store handles all dice-related functionality in the game:
 * - Tracking pending dice requests from the GM
 * - Managing completed rolls before submission
 * - Handling the UI state for rolling and submitting
 *
 * @module diceStore
 */
import { defineStore } from 'pinia'
import { ref, computed, Ref } from 'vue'
import type {
  DiceRequestModel,
  DiceRollResultModel,
  PlayerDiceRequestAddedEvent,
  PlayerDiceRequestsClearedEvent,
  GameStateSnapshotEvent
} from '@/types/unified'
import type { UIDiceRequest, UIDiceRollResult } from '@/types/ui'

export const useDiceStore = defineStore('dice', () => {
  /**
   * State
   */

  /**
   * Array of pending dice roll requests from the GM
   */
  const pendingRequests: Ref<UIDiceRequest[]> = ref([])

  /**
   * Map storing completed roll results keyed by "{requestId}-{characterId}"
   */
  const completedRolls: Ref<Map<string, UIDiceRollResult>> = ref(new Map())

  /**
   * UI state - indicates if a roll is currently being performed
   */
  const isRolling = ref(false)

  /**
   * UI state - indicates if rolls are being submitted to the backend
   */
  const isSubmitting = ref(false)

  /**
   * Computed Properties
   */

  /**
   * Check if there are any pending dice requests
   */
  const hasPendingRequests = computed<boolean>(() => pendingRequests.value.length > 0)

  /**
   * Check if there are any completed rolls waiting to be submitted
   */
  const hasCompletedRolls = computed<boolean>(() => completedRolls.value.size > 0)

  /**
   * Check if all pending requests have been completed
   */
  const allRequestsCompleted = computed<boolean>(() => {
    if (pendingRequests.value.length === 0) return false

    return pendingRequests.value.every(request => {
      const characterId = request.character_id_to_roll || request.character_ids?.[0]
      if (!characterId) return false

      const key = `${request.request_id}-${characterId}`
      return completedRolls.value.has(key)
    })
  })

  // Actions
  function handlePlayerDiceRequestAdded(event: PlayerDiceRequestAddedEvent): void {
    console.log('DiceStore: Player dice request added:', event)
    console.log('Current pending requests before adding:', [...pendingRequests.value])

    // Check for duplicates - consider both request_id AND character_id
    // This handles cases where backend uses same request_id for multiple characters
    const exists = pendingRequests.value.some(r =>
      r.request_id === event.request_id &&
      r.character_ids?.[0] === event.character_id
    )

    if (!exists) {
      const diceRequest: UIDiceRequest = {
        request_id: event.request_id,
        character_ids: [event.character_id],
        character_id: event.character_id,  // For backward compatibility with UI components
        character_id_to_roll: event.character_id,
        character_name: event.character_name,
        type: event.roll_type,
        roll_type: event.roll_type,
        dice_formula: event.dice_formula,
        reason: event.purpose,
        purpose: event.purpose,
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

  function handlePlayerDiceRequestsCleared(event: PlayerDiceRequestsClearedEvent): void {
    console.log('DiceStore: Player dice requests cleared:', event)

    if (event.cleared_request_ids && event.cleared_request_ids.length > 0) {
      // Remove cleared requests
      pendingRequests.value = pendingRequests.value.filter(
        r => !event.cleared_request_ids.includes(r.request_id)
      )

      // Also clear any completed rolls for these requests
      event.cleared_request_ids.forEach(requestId => {
        // Remove all rolls associated with this request
        const keysToRemove: string[] = []
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

  function handleGameStateSnapshot(snapshotData: Partial<GameStateSnapshotEvent>): void {
    if (!snapshotData || !snapshotData.pending_dice_requests) return

    console.log('DiceStore: Processing snapshot dice requests:', snapshotData.pending_dice_requests)

    // Only set from snapshot if we don't have any pending requests
    if (pendingRequests.value.length === 0) {
      pendingRequests.value = snapshotData.pending_dice_requests.map(request => ({
        ...request,
        // Normalize field names for backward compatibility
        character_id: request.character_ids?.[0], // For UI component compatibility
        character_id_to_roll: request.character_ids?.[0],
        character_name: undefined, // Will be filled by UI
        roll_type: request.type, // Ensure roll_type is set for consistency
        purpose: request.reason,
        timestamp: undefined
      }))

      console.log('Loaded dice requests from snapshot:', pendingRequests.value.length)
    } else {
      console.log('Skipping snapshot dice requests - already have pending requests from events')
    }
  }

  function addCompletedRoll(requestId: string, characterId: string, rollResult: DiceRollResultModel): void {
    const key = `${requestId}-${characterId}`
    completedRolls.value.set(key, rollResult)
    console.log('Added completed roll:', key, rollResult)
  }

  function getCompletedRoll(requestId: string, characterId: string): DiceRollResultModel | undefined {
    const key = `${requestId}-${characterId}`
    return completedRolls.value.get(key)
  }

  function clearCompletedRolls(): void {
    completedRolls.value.clear()
  }

  function clearAllRequests(): void {
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
