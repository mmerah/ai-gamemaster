import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const usePartyStore = defineStore('party', () => {
  // State
  const members = ref([])
  
  // Computed
  const aliveMembers = computed(() => {
    return members.value.filter(m => (m.currentHp || m.hp || 0) > 0)
  })
  
  const totalPartyHp = computed(() => {
    return members.value.reduce((sum, m) => sum + (m.currentHp || m.hp || 0), 0)
  })
  
  const totalPartyMaxHp = computed(() => {
    return members.value.reduce((sum, m) => sum + (m.maxHp || m.max_hp || 0), 0)
  })
  
  // Actions
  function handlePartyMemberUpdated(event) {
    console.log('PartyStore: Party member updated:', event)
    
    const member = members.value.find(m => m.id === event.character_id)
    if (member && event.changes) {
      // Apply changes
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
      if (event.changes.armor_class !== undefined) {
        member.ac = event.changes.armor_class
        member.armor_class = event.changes.armor_class
      }
      
      console.log('Updated party member:', member)
    }
  }
  
  function handleCombatantHpChanged(event) {
    // Only update if it's a player character
    if (!event.is_player_controlled) return
    
    console.log('PartyStore: Player HP changed:', event)
    
    const member = members.value.find(m => m.id === event.combatant_id)
    if (member) {
      member.currentHp = event.new_hp
      member.hp = event.new_hp
      member.maxHp = event.max_hp
      member.max_hp = event.max_hp
      
      // Track HP change for visual feedback
      member.lastHpChange = {
        amount: event.change_amount,
        oldHp: event.old_hp,
        source: event.source,
        timestamp: event.timestamp
      }
      
      // Clear visual feedback after 3 seconds
      setTimeout(() => {
        if (member.lastHpChange && member.lastHpChange.timestamp === event.timestamp) {
          delete member.lastHpChange
        }
      }, 3000)
    }
  }
  
  function handleCombatantStatusChanged(event) {
    // Only update if it's a player character
    if (event.is_player_controlled === false) return
    
    console.log('PartyStore: Player status changed:', event)
    
    const member = members.value.find(m => m.id === event.combatant_id)
    if (member) {
      member.conditions = event.new_conditions || []
      member.statusEffects = event.new_conditions || []
    }
  }
  
  function handleItemAdded(event) {
    console.log('PartyStore: Item added:', event)
    
    const member = members.value.find(m => m.id === event.character_id)
    if (member) {
      // Initialize inventory if it doesn't exist
      if (!member.inventory) {
        member.inventory = []
      }
      
      // Add the item
      const existingItem = member.inventory.find(i => i.name === event.item_name)
      if (existingItem) {
        existingItem.quantity = (existingItem.quantity || 1) + (event.quantity || 1)
      } else {
        member.inventory.push({
          name: event.item_name,
          quantity: event.quantity || 1,
          description: event.item_description
        })
      }
    }
  }
  
  function handleGameStateSnapshot(snapshotData) {
    if (!snapshotData || !snapshotData.party_members) return
    
    console.log('PartyStore: Processing snapshot party members:', snapshotData.party_members)
    
    members.value = snapshotData.party_members.map(member => ({
      ...member,
      // Normalize HP fields
      currentHp: member.current_hp || member.currentHp || member.hp || 0,
      maxHp: member.max_hp || member.maxHp || member.maximum_hp || 0,
      hp: member.current_hp || member.currentHp || member.hp || 0,
      max_hp: member.max_hp || member.maxHp || member.maximum_hp || 0,
      
      // Normalize class fields
      char_class: member.class || member.char_class || 'Unknown',
      class: member.class || member.char_class || 'Unknown',
      
      // Normalize other fields
      ac: member.armor_class || member.ac || 10,
      armor_class: member.armor_class || member.ac || 10,
      
      // Arrays
      conditions: member.conditions || member.statusEffects || [],
      statusEffects: member.conditions || member.statusEffects || [],
      inventory: member.inventory || []
    }))
    
    console.log('Loaded party members from snapshot:', members.value)
  }
  
  function getMemberById(id) {
    return members.value.find(m => m.id === id)
  }
  
  function getMemberByName(name) {
    return members.value.find(m => m.name === name)
  }
  
  function resetParty() {
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
    resetParty
  }
})