import { defineStore } from 'pinia'
import { ref, computed, Ref } from 'vue'
import { logger } from '@/utils/logger'
import type {
  PartyMemberUpdatedEvent,
  CombatantHpChangedEvent,
  CombatantStatusChangedEvent,
  ItemAddedEvent,
  GameStateSnapshotEvent,
  ItemModel,
} from '@/types/unified'
import type { UIPartyMember } from '@/types/ui'

// Extended party member with party-specific UI state
interface PartyMemberWithState extends UIPartyMember {
  // Add camelCase aliases for UI compatibility
  currentHp?: number
  maxHp?: number
  ac?: number
  lastHpChange?: {
    amount: number
    oldHp: number
    source?: string
    timestamp: string
  }
  statusEffects?: string[] // Alias for conditions
}

export const usePartyStore = defineStore('party', () => {
  // State
  const members: Ref<PartyMemberWithState[]> = ref([])

  // Computed
  const aliveMembers = computed<PartyMemberWithState[]>(() => {
    return members.value.filter(m => {
      const currentHp = m.current_hp || 0
      return currentHp > 0
    })
  })

  const totalPartyHp = computed<number>(() => {
    return members.value.reduce((sum, m) => {
      const currentHp = m.current_hp || 0
      return sum + currentHp
    }, 0)
  })

  const totalPartyMaxHp = computed<number>(() => {
    return members.value.reduce((sum, m) => {
      const maxHp = m.max_hp || 0
      return sum + maxHp
    }, 0)
  })

  // Actions
  function handlePartyMemberUpdated(event: PartyMemberUpdatedEvent): void {
    logger.debug('PartyStore: Party member updated:', event)

    const member = members.value.find(m => m.id === event.character_id)
    if (member && event.changes) {
      // Log the member state before changes
      logger.debug('Member before changes:', {
        id: member.id,
        name: member.name,
        current_hp: member.current_hp,
        currentHp: member.currentHp,
        max_hp: member.max_hp,
        maxHp: member.maxHp,
        gold: member.gold,
      })

      // Apply changes - but only update fields that are present in the changes
      // This prevents undefined or null values from overwriting existing data
      if (
        'gold' in event.changes &&
        event.changes.gold !== undefined &&
        event.changes.gold !== null
      ) {
        member.gold = event.changes.gold
      }
      if (
        'conditions' in event.changes &&
        event.changes.conditions !== undefined &&
        event.changes.conditions !== null
      ) {
        member.conditions = event.changes.conditions
        member.statusEffects = event.changes.conditions
      }
      if (
        'level' in event.changes &&
        event.changes.level !== undefined &&
        event.changes.level !== null
      ) {
        member.level = event.changes.level
      }
      if (
        'experience_points' in event.changes &&
        event.changes.experience_points !== undefined &&
        event.changes.experience_points !== null
      ) {
        member.experience_points = event.changes.experience_points
      }
      if (
        'exhaustion_level' in event.changes &&
        event.changes.exhaustion_level !== undefined &&
        event.changes.exhaustion_level !== null
      ) {
        member.exhaustion_level = event.changes.exhaustion_level
      }

      // Ensure consistent field naming - update both snake_case and camelCase
      // Only update HP fields if they are present in the changes and not null
      if (
        'current_hp' in event.changes &&
        event.changes.current_hp !== undefined &&
        event.changes.current_hp !== null
      ) {
        member.current_hp = event.changes.current_hp as number
        member.currentHp = event.changes.current_hp as number
        member.hp = event.changes.current_hp as number
      }
      if (
        'max_hp' in event.changes &&
        event.changes.max_hp !== undefined &&
        event.changes.max_hp !== null
      ) {
        member.max_hp = event.changes.max_hp as number
        member.maxHp = event.changes.max_hp as number
      }
      if (
        'armor_class' in event.changes &&
        event.changes.armor_class !== undefined &&
        event.changes.armor_class !== null
      ) {
        member.armor_class = event.changes.armor_class as number
        member.ac = event.changes.armor_class as number
      }
      if (
        'temp_hp' in event.changes &&
        event.changes.temp_hp !== undefined &&
        event.changes.temp_hp !== null
      ) {
        member.temp_hp = event.changes.temp_hp as number
      }

      logger.debug('Updated party member after changes:', {
        id: member.id,
        name: member.name,
        current_hp: member.current_hp,
        currentHp: member.currentHp,
        max_hp: member.max_hp,
        maxHp: member.maxHp,
        gold: member.gold,
      })
    }
  }

  function handleCombatantHpChanged(event: CombatantHpChangedEvent): void {
    // Only update if it's a player character
    if (!event.is_player_controlled) return

    logger.debug('PartyStore: Player HP changed:', event)

    const member = members.value.find(m => m.id === event.combatant_id)
    if (member) {
      // Update both snake_case and camelCase fields
      member.current_hp = event.new_hp
      member.currentHp = event.new_hp
      member.hp = event.new_hp
      member.max_hp = event.max_hp
      member.maxHp = event.max_hp

      // Track HP change for visual feedback
      member.lastHpChange = {
        amount: event.change_amount,
        oldHp: event.old_hp,
        source: event.source || undefined,
        timestamp: event.timestamp,
      }

      // Clear visual feedback after 3 seconds
      setTimeout(() => {
        if (
          member.lastHpChange &&
          member.lastHpChange.timestamp === event.timestamp
        ) {
          delete member.lastHpChange
        }
      }, 3000)
    }
  }

  function handleCombatantStatusChanged(
    event: CombatantStatusChangedEvent
  ): void {
    // Only update if it's a player character
    // Note: CombatantStatusChangedEvent doesn't have is_player_controlled field,
    // so we need to check if the combatant is in our party
    const member = members.value.find(m => m.id === event.combatant_id)
    if (!member) return

    logger.debug('PartyStore: Player status changed:', event)

    member.conditions = event.new_conditions || []
    member.statusEffects = event.new_conditions || []
  }

  function handleItemAdded(event: ItemAddedEvent): void {
    logger.debug('PartyStore: Item added:', event)

    const member = members.value.find(m => m.id === event.character_id)
    if (member) {
      // Initialize inventory if it doesn't exist
      if (!member.inventory) {
        member.inventory = []
      }

      // Add the item
      const existingItem = member.inventory.find(
        i => 'name' in i && i.name === event.item_name
      )

      if (existingItem && 'quantity' in existingItem) {
        existingItem.quantity =
          (existingItem.quantity || 1) + (event.quantity || 1)
      } else {
        const newItem: ItemModel = {
          id: `item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          name: event.item_name,
          description: event.item_description || '',
          quantity: event.quantity || 1,
        }
        member.inventory.push(newItem)
      }
    }
  }

  function handleGameStateSnapshot(
    snapshotData: Partial<GameStateSnapshotEvent>
  ): void {
    if (!snapshotData || !snapshotData.party_members) return

    logger.debug(
      'PartyStore: Processing snapshot party members:',
      snapshotData.party_members
    )

    // party_members can be a single CharacterInstanceModel or an array of CombinedCharacterModel
    const partyArray = Array.isArray(snapshotData.party_members)
      ? snapshotData.party_members
      : Object.values(snapshotData.party_members)

    members.value = partyArray.map(member => {
      // Safely cast to unknown first, then to our expected type
      const baseMember = member as unknown as PartyMemberWithState

      // Ensure required UI fields are present
      const result: PartyMemberWithState = {
        ...baseMember,
        // Add camelCase aliases for UI compatibility
        currentHp: baseMember.current_hp || baseMember.currentHp || 0,
        maxHp: baseMember.max_hp || baseMember.maxHp || 0,
        ac: baseMember.armor_class || baseMember.ac || 10,

        // Add status effects alias
        statusEffects: baseMember.conditions || baseMember.statusEffects || [],

        // Ensure inventory is initialized
        inventory: baseMember.inventory || [],
      }

      return result
    })

    logger.debug('Loaded party members from snapshot:', members.value)
  }

  function getMemberById(id: string): UIPartyMember | undefined {
    return members.value.find(m => m.id === id)
  }

  function getMemberByName(name: string): UIPartyMember | undefined {
    return members.value.find(m => m.name === name)
  }

  function resetParty(): void {
    members.value = []
  }

  return {
    // State
    members,

    // Computed
    aliveMembers,
    totalPartyHp,
    totalPartyMaxHp,

    // Actions
    handlePartyMemberUpdated,
    handleCombatantHpChanged,
    handleCombatantStatusChanged,
    handleItemAdded,
    handleGameStateSnapshot,
    getMemberById,
    getMemberByName,
    resetParty,
  }
})
