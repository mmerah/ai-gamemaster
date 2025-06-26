import { defineStore } from 'pinia'
import { ref, computed, Ref } from 'vue'
import eventService from '@/services/eventService'
import type {
  CombatantModel,
  CombatStateModel,
  CombatStartedEvent,
  CombatEndedEvent,
  TurnAdvancedEvent,
  CombatantHpChangedEvent,
  CombatantStatusChangedEvent,
  CombatantAddedEvent,
  CombatantRemovedEvent,
  CombatantInitiativeSetEvent,
  InitiativeOrderDeterminedEvent,
} from '@/types/unified'

// Extended combatant type for UI state
interface UICombatant
  extends Omit<CombatantModel, 'stats' | 'abilities' | 'attacks'> {
  hp: number
  is_defeated?: boolean
  lastHpChange?: {
    amount: number
    source?: string
    timestamp: string
  }
  lastConditionChange?: {
    added: string[]
    removed: string[]
    timestamp: string
  }
}

export const useCombatStore = defineStore('combat', () => {
  // State
  const isActive = ref(false)
  const roundNumber = ref(1)
  const currentTurnIndex = ref(0)
  const combatants: Ref<UICombatant[]> = ref([])

  // UI state
  const isInitiativeSettingComplete = ref(false)
  const lastEventSequence = ref(0)

  // Getters
  const isConnected = computed<boolean>(() => {
    return eventService.connected
  })

  const currentCombatant = computed<UICombatant | null>(() => {
    if (
      !isActive.value ||
      currentTurnIndex.value < 0 ||
      currentTurnIndex.value >= combatants.value.length
    ) {
      return null
    }
    const combatant = combatants.value[currentTurnIndex.value]
    return combatant ?? null
  })

  const playerCombatants = computed<UICombatant[]>(() => {
    return combatants.value.filter(c => c.is_player)
  })

  const npcCombatants = computed<UICombatant[]>(() => {
    return combatants.value.filter(c => !c.is_player)
  })

  const initiativeOrder = computed<UICombatant[]>(() => {
    return [...combatants.value].sort((a, b) => b.initiative - a.initiative)
  })

  const hasInitiativeSet = computed<boolean>(() => {
    const result =
      combatants.value.length > 0 &&
      combatants.value.every(c => c.initiative >= 0)
    console.log(
      'CombatStore: hasInitiativeSet computed -',
      result,
      'combatants:',
      combatants.value.length,
      'initiatives:',
      combatants.value.map(c => ({ name: c.name, init: c.initiative }))
    )
    return result
  })

  const currentTurnName = computed<string>(() => {
    if (!hasInitiativeSet.value) {
      return 'Rolling for initiative...'
    }
    const current = currentCombatant.value
    return current ? current.name : 'Unknown'
  })

  // Actions
  // Note: Event handlers are registered by eventRouter, not here
  // These methods are kept for potential future use or direct store initialization
  function initialize(): void {
    console.log(
      'CombatStore: Initialize called (note: eventRouter handles event registration)'
    )
  }

  function cleanup(): void {
    console.log('CombatStore: Cleanup called')
  }

  function handleCombatStarted(event: CombatStartedEvent): void {
    console.log(
      'CombatStore: Combat started with',
      event.combatants.length,
      'combatants'
    )
    console.log(
      'CombatStore: Initial combatants:',
      event.combatants.map(c => ({ name: c.name, initiative: c.initiative }))
    )

    isActive.value = true
    roundNumber.value = event.round_number || 1
    currentTurnIndex.value = 0
    combatants.value = event.combatants.map(c => ({
      ...c,
      hp: c.current_hp || 0,
      max_hp: c.max_hp,
      ac: c.armor_class,
      initiative: c.initiative ?? -1, // Use nullish coalescing to handle 0 initiative
      conditions: c.conditions || [],
    }))

    console.log(
      'CombatStore: After mapping - hasInitiativeSet:',
      hasInitiativeSet.value
    )
    console.log(
      'CombatStore: Mapped combatants:',
      combatants.value.map(c => ({ name: c.name, initiative: c.initiative }))
    )

    isInitiativeSettingComplete.value = false
    lastEventSequence.value = event.sequence_number
  }

  function handleCombatEnded(event: CombatEndedEvent): void {
    isActive.value = false
    combatants.value = []
    currentTurnIndex.value = 0
    roundNumber.value = 1
    isInitiativeSettingComplete.value = false
    lastEventSequence.value = event.sequence_number
  }

  function handleCombatantInitiativeSet(
    event: CombatantInitiativeSetEvent
  ): void {
    console.log(
      'CombatStore: Initiative set for',
      event.combatant_name,
      ':',
      event.initiative_value
    )
    const combatant = combatants.value.find(c => c.id === event.combatant_id)
    if (combatant) {
      combatant.initiative = event.initiative_value
      console.log(
        'CombatStore: Updated combatant initiative. hasInitiativeSet:',
        hasInitiativeSet.value
      )
    } else {
      console.warn(
        'CombatStore: Combatant not found for initiative update:',
        event.combatant_id
      )
    }
    lastEventSequence.value = event.sequence_number
  }

  function handleInitiativeOrderDetermined(
    event: InitiativeOrderDeterminedEvent
  ): void {
    console.log(
      'CombatStore: Initiative order determined with',
      event.ordered_combatants.length,
      'combatants'
    )
    console.log(
      'CombatStore: Combatants:',
      event.ordered_combatants.map(c => ({
        name: c.name,
        initiative: c.initiative,
      }))
    )

    // Update the combatants list with the ordered combatants
    combatants.value = event.ordered_combatants.map(c => {
      const existing = combatants.value.find(existing => existing.id === c.id)
      return {
        ...c,
        hp: existing?.hp || c.current_hp || 0,
        max_hp: c.max_hp,
        ac: c.armor_class,
        initiative: c.initiative, // Explicitly preserve initiative
        conditions: c.conditions || [],
      }
    })

    console.log(
      'CombatStore: After update - hasInitiativeSet:',
      hasInitiativeSet.value
    )
    console.log(
      'CombatStore: Combatant initiatives:',
      combatants.value.map(c => ({ name: c.name, initiative: c.initiative }))
    )

    isInitiativeSettingComplete.value = true
    currentTurnIndex.value = 0 // Reset to first combatant
    lastEventSequence.value = event.sequence_number
  }

  function handleTurnAdvanced(event: TurnAdvancedEvent): void {
    // Find the combatant by ID and set as current
    const combatantIndex = combatants.value.findIndex(
      c => c.id === event.new_combatant_id
    )
    if (combatantIndex >= 0) {
      currentTurnIndex.value = combatantIndex
    }

    roundNumber.value = event.round_number
    lastEventSequence.value = event.sequence_number
  }

  function handleCombatantHpChanged(event: CombatantHpChangedEvent): void {
    const combatant = combatants.value.find(c => c.id === event.combatant_id)
    if (combatant) {
      combatant.hp = event.new_hp
      combatant.current_hp = event.new_hp
      combatant.max_hp = event.max_hp || combatant.max_hp

      // Add visual feedback for damage/healing
      combatant.lastHpChange = {
        amount: event.change_amount,
        source: event.source,
        timestamp: event.timestamp,
      }

      // Auto-clear visual feedback after 3 seconds
      setTimeout(() => {
        if (
          combatant.lastHpChange &&
          combatant.lastHpChange.timestamp === event.timestamp
        ) {
          delete combatant.lastHpChange
        }
      }, 3000)
    }
    lastEventSequence.value = event.sequence_number
  }

  function handleCombatantStatusChanged(
    event: CombatantStatusChangedEvent
  ): void {
    const combatant = combatants.value.find(c => c.id === event.combatant_id)
    if (combatant) {
      // Update conditions to match the event's new_conditions
      combatant.conditions = [...event.new_conditions]

      // Track what changed for visual feedback
      if (
        event.added_conditions.length > 0 ||
        event.removed_conditions.length > 0
      ) {
        combatant.lastConditionChange = {
          added: event.added_conditions,
          removed: event.removed_conditions,
          timestamp: event.timestamp,
        }

        // Auto-clear visual feedback after 5 seconds
        setTimeout(() => {
          if (
            combatant.lastConditionChange &&
            combatant.lastConditionChange.timestamp === event.timestamp
          ) {
            delete combatant.lastConditionChange
          }
        }, 5000)
      }

      // Update defeated status
      combatant.is_defeated = event.is_defeated
    }
    lastEventSequence.value = event.sequence_number
  }

  function handleCombatantAdded(event: CombatantAddedEvent): void {
    const newCombatant: UICombatant = {
      id: event.combatant_id,
      name: event.combatant_name,
      is_player: event.is_player_controlled,
      hp: event.hp,
      current_hp: event.hp,
      max_hp: event.max_hp,
      armor_class: event.ac,
      initiative: -1,
      initiative_modifier: 0,
      conditions: [],
    }

    combatants.value.push(newCombatant)
    lastEventSequence.value = event.sequence_number
  }

  function handleCombatantRemoved(event: CombatantRemovedEvent): void {
    const index = combatants.value.findIndex(c => c.id === event.combatant_id)
    if (index >= 0) {
      combatants.value.splice(index, 1)

      // Adjust current turn index if needed
      if (index < currentTurnIndex.value) {
        currentTurnIndex.value--
      } else if (
        index === currentTurnIndex.value &&
        currentTurnIndex.value >= combatants.value.length
      ) {
        currentTurnIndex.value = 0
      }
    }
    lastEventSequence.value = event.sequence_number
  }

  function getCombatantById(id: string): UICombatant | undefined {
    return combatants.value.find(c => c.id === id)
  }

  function getCombatantsByType(isPlayer: boolean): UICombatant[] {
    return combatants.value.filter(c => c.is_player === isPlayer)
  }

  function isCombatantTurn(combatantId: string): boolean {
    const current = currentCombatant.value
    return current !== null && current.id === combatantId
  }

  function getNextCombatant(): UICombatant | null {
    if (!isActive.value || combatants.value.length === 0) {
      return null
    }

    const nextIndex = (currentTurnIndex.value + 1) % combatants.value.length
    const nextCombatant = combatants.value[nextIndex]
    return nextCombatant ?? null
  }

  function handleGameStateSnapshot(
    combatState: CombatStateModel | undefined
  ): void {
    if (!combatState) {
      resetCombat()
      return
    }

    isActive.value = combatState.is_active || false
    roundNumber.value = combatState.round_number || 1
    currentTurnIndex.value = combatState.current_turn_index || 0

    // Map combatants, handling field name differences
    combatants.value = (combatState.combatants || []).map(c => ({
      ...c,
      hp: c.current_hp || 0,
      max_hp: c.max_hp,
      ac: c.armor_class,
      initiative: c.initiative || -1,
      conditions: c.conditions || [],
      is_defeated: false,
    }))

    // Check if all combatants have initiative set
    isInitiativeSettingComplete.value =
      combatants.value.length > 0 &&
      combatants.value.every(c => c.initiative >= 0)
  }

  function resetCombat(): void {
    isActive.value = false
    combatants.value = []
    currentTurnIndex.value = 0
    roundNumber.value = 1
    isInitiativeSettingComplete.value = false
    lastEventSequence.value = 0
  }

  return {
    // State
    isActive,
    roundNumber,
    currentTurnIndex,
    combatants,
    isInitiativeSettingComplete,
    lastEventSequence,

    // Getters
    isConnected,
    currentCombatant,
    playerCombatants,
    npcCombatants,
    initiativeOrder,
    hasInitiativeSet,
    currentTurnName,

    // Actions
    initialize,
    cleanup,
    handleCombatStarted,
    handleCombatEnded,
    handleCombatantInitiativeSet,
    handleInitiativeOrderDetermined,
    handleTurnAdvanced,
    handleCombatantHpChanged,
    handleCombatantStatusChanged,
    handleCombatantAdded,
    handleCombatantRemoved,
    getCombatantById,
    getCombatantsByType,
    isCombatantTurn,
    getNextCombatant,
    handleGameStateSnapshot,
    resetCombat,
  }
})
