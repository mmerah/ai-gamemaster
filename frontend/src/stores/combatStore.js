import { defineStore } from 'pinia'
import eventService from '@/services/eventService'

export const useCombatStore = defineStore('combat', {
  state: () => ({
    // Combat state
    isActive: false,
    roundNumber: 1,
    currentTurnIndex: 0,
    combatants: [],
    
    // UI state
    isInitiativeSettingComplete: false,
    lastEventSequence: 0,
    
    // Track if we're connected to SSE
    isConnected: false
  }),

  getters: {
    /**
     * Get the currently active combatant
     */
    currentCombatant() {
      if (!this.isActive || this.currentTurnIndex < 0 || this.currentTurnIndex >= this.combatants.length) {
        return null
      }
      return this.combatants[this.currentTurnIndex]
    },

    /**
     * Get all player combatants
     */
    playerCombatants() {
      return this.combatants.filter(c => c.is_player)
    },

    /**
     * Get all NPC combatants
     */
    npcCombatants() {
      return this.combatants.filter(c => !c.is_player)
    },

    /**
     * Get combatants sorted by initiative (highest first)
     */
    initiativeOrder() {
      return [...this.combatants].sort((a, b) => b.initiative - a.initiative)
    },

    /**
     * Check if initiative has been set for all combatants
     */
    hasInitiativeSet() {
      return this.combatants.length > 0 && this.combatants.every(c => c.initiative >= 0)
    },

    /**
     * Get current turn's combatant name
     */
    currentTurnName() {
      // If initiative hasn't been set yet, indicate that
      if (!this.hasInitiativeSet) {
        return 'Rolling for initiative...'
      }
      const current = this.currentCombatant
      return current ? current.name : 'Unknown'
    }
  },

  actions: {
    /**
     * Initialize the combat store and connect to SSE
     */
    initialize() {
      // Register event handlers for combat events
      eventService.on('combat_started', this.handleCombatStarted.bind(this))
      eventService.on('combat_ended', this.handleCombatEnded.bind(this))
      eventService.on('combatant_initiative_set', this.handleCombatantInitiativeSet.bind(this))
      eventService.on('initiative_order_determined', this.handleInitiativeOrderDetermined.bind(this))
      eventService.on('turn_advanced', this.handleTurnAdvanced.bind(this))
      eventService.on('combatant_hp_changed', this.handleCombatantHpChanged.bind(this))
      eventService.on('combatant_status_changed', this.handleCombatantStatusChanged.bind(this))
      eventService.on('combatant_added', this.handleCombatantAdded.bind(this))
      eventService.on('combatant_removed', this.handleCombatantRemoved.bind(this))
      
      // Connect to SSE if not already connected
      if (!eventService.connected) {
        eventService.connect()
      }
      this.isConnected = eventService.connected
      
      // Monitor connection status
      setInterval(() => {
        this.isConnected = eventService.connected
      }, 1000)
    },

    /**
     * Clean up when store is destroyed
     */
    cleanup() {
      eventService.off('combat_started', this.handleCombatStarted)
      eventService.off('combat_ended', this.handleCombatEnded)
      eventService.off('combatant_initiative_set', this.handleCombatantInitiativeSet)
      eventService.off('initiative_order_determined', this.handleInitiativeOrderDetermined)
      eventService.off('turn_advanced', this.handleTurnAdvanced)
      eventService.off('combatant_hp_changed', this.handleCombatantHpChanged)
      eventService.off('combatant_status_changed', this.handleCombatantStatusChanged)
      eventService.off('combatant_added', this.handleCombatantAdded)
      eventService.off('combatant_removed', this.handleCombatantRemoved)
    },

    /**
     * Handle combat started event
     */
    handleCombatStarted(event) {
      console.log('CombatStore: Combat started:', event)
      
      this.isActive = true
      this.roundNumber = 1
      this.currentTurnIndex = 0
      this.combatants = event.combatants.map(c => ({
        id: c.id,
        name: c.name,
        is_player: c.is_player,
        hp: c.hp,
        max_hp: c.max_hp,
        ac: c.ac,
        initiative: c.initiative || -1,
        conditions: c.conditions || []
      }))
      this.isInitiativeSettingComplete = false
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle combat ended event
     */
    handleCombatEnded(event) {
      console.log('CombatStore: Combat ended:', event)
      
      this.isActive = false
      this.combatants = []
      this.currentTurnIndex = 0
      this.roundNumber = 1
      this.isInitiativeSettingComplete = false
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle individual combatant initiative set
     */
    handleCombatantInitiativeSet(event) {
      console.log('CombatStore: Combatant initiative set:', event)
      
      const combatant = this.combatants.find(c => c.id === event.combatant_id)
      if (combatant) {
        combatant.initiative = event.initiative_value
      }
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle initiative order determination
     */
    handleInitiativeOrderDetermined(event) {
      console.log('CombatStore: Initiative order determined:', event)
      
      // Update the combatants list with the ordered combatants
      this.combatants = event.ordered_combatants.map(c => {
        const existing = this.combatants.find(existing => existing.id === c.id)
        return {
          ...existing,
          id: c.id,
          name: c.name,
          is_player: c.is_player,
          initiative: c.initiative
        }
      })
      
      this.isInitiativeSettingComplete = true
      this.currentTurnIndex = 0 // Reset to first combatant
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle turn advancement
     */
    handleTurnAdvanced(event) {
      console.log('CombatStore: Turn advanced:', event)
      
      // Find the combatant by ID and set as current
      const combatantIndex = this.combatants.findIndex(c => c.id === event.new_combatant_id)
      if (combatantIndex >= 0) {
        this.currentTurnIndex = combatantIndex
      }
      
      this.roundNumber = event.round_number
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle HP changes to combatants
     */
    handleCombatantHpChanged(event) {
      console.log('CombatStore: Combatant HP changed:', event)
      
      const combatant = this.combatants.find(c => c.id === event.combatant_id)
      if (combatant) {
        combatant.hp = event.new_hp
        combatant.max_hp = event.max_hp || combatant.max_hp
        
        // Add visual feedback for damage/healing
        combatant.lastHpChange = {
          amount: event.change_amount,
          source: event.source,
          timestamp: event.timestamp
        }
        
        // Auto-clear visual feedback after 3 seconds
        setTimeout(() => {
          if (combatant.lastHpChange && combatant.lastHpChange.timestamp === event.timestamp) {
            delete combatant.lastHpChange
          }
        }, 3000)
      }
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle status/condition changes to combatants
     */
    handleCombatantStatusChanged(event) {
      console.log('CombatStore: Combatant status changed:', event)
      
      const combatant = this.combatants.find(c => c.id === event.combatant_id)
      if (combatant) {
        // Update conditions to match the event's new_conditions
        combatant.conditions = [...event.new_conditions]
        
        // Track what changed for visual feedback
        if (event.added_conditions.length > 0 || event.removed_conditions.length > 0) {
          combatant.lastConditionChange = {
            added: event.added_conditions,
            removed: event.removed_conditions,
            timestamp: event.timestamp
          }
          
          // Auto-clear visual feedback after 5 seconds
          setTimeout(() => {
            if (combatant.lastConditionChange && combatant.lastConditionChange.timestamp === event.timestamp) {
              delete combatant.lastConditionChange
            }
          }, 5000)
        }
        
        // Update defeated status
        combatant.is_defeated = event.is_defeated
      }
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle combatant added mid-combat
     */
    handleCombatantAdded(event) {
      console.log('CombatStore: Combatant added:', event)
      
      const newCombatant = {
        id: event.combatant_id,
        name: event.combatant_name,
        is_player: event.is_player,
        hp: event.hp,
        max_hp: event.max_hp,
        ac: event.ac,
        initiative: event.initiative || -1,
        conditions: event.conditions || []
      }
      
      this.combatants.push(newCombatant)
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Handle combatant removed mid-combat
     */
    handleCombatantRemoved(event) {
      console.log('CombatStore: Combatant removed:', event)
      
      const index = this.combatants.findIndex(c => c.id === event.combatant_id)
      if (index >= 0) {
        this.combatants.splice(index, 1)
        
        // Adjust current turn index if needed
        if (index < this.currentTurnIndex) {
          this.currentTurnIndex--
        } else if (index === this.currentTurnIndex && this.currentTurnIndex >= this.combatants.length) {
          this.currentTurnIndex = 0
        }
      }
      this.lastEventSequence = event.sequence_number
    },

    /**
     * Get combatant by ID
     */
    getCombatantById(id) {
      return this.combatants.find(c => c.id === id)
    },

    /**
     * Get combatants by type (player/npc)
     */
    getCombatantsByType(isPlayer) {
      return this.combatants.filter(c => c.is_player === isPlayer)
    },

    /**
     * Check if a specific combatant is on their turn
     */
    isCombatantTurn(combatantId) {
      const current = this.currentCombatant
      return current && current.id === combatantId
    },

    /**
     * Get the next combatant in initiative order
     */
    getNextCombatant() {
      if (!this.isActive || this.combatants.length === 0) {
        return null
      }
      
      const nextIndex = (this.currentTurnIndex + 1) % this.combatants.length
      return this.combatants[nextIndex]
    },

    /**
     * Reset combat state
     */
    resetCombat() {
      this.isActive = false
      this.combatants = []
      this.currentTurnIndex = 0
      this.roundNumber = 1
      this.isInitiativeSettingComplete = false
      this.lastEventSequence = 0
    }
  }
})