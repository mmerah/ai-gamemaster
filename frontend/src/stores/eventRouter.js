/**
 * Event Router - Central event distribution system
 * 
 * This module serves as the central hub for distributing Server-Sent Events (SSE)
 * to the appropriate stores in the application. It implements a pub/sub pattern
 * where events from the backend are routed to specific store handlers based on
 * their event type.
 * 
 * Key responsibilities:
 * - Initialize and connect all stores to the SSE event stream
 * - Route events to appropriate store handlers
 * - Maintain backward compatibility with legacy gameStore handlers
 * - Monitor and update connection status across stores
 * 
 * @module eventRouter
 */
import eventService from '@/services/eventService'
import { useGameStore } from './gameStore'
import { useCombatStore } from './combatStore'
import { useDiceStore } from './diceStore'
import { useUiStore } from './uiStore'
import { usePartyStore } from './partyStore'
import { useChatStore } from './chatStore'

/**
 * Central event router that distributes SSE events to appropriate stores
 * Uses a singleton pattern to ensure only one router instance exists
 */
class EventRouter {
  constructor() {
    this.initialized = false
    this.stores = {}
  }
  
  /**
   * Initialize the event router and connect all stores
   */
  initialize() {
    if (this.initialized) {
      console.warn('EventRouter already initialized')
      return
    }
    
    // Get store instances
    this.stores = {
      game: useGameStore(),
      combat: useCombatStore(),
      dice: useDiceStore(),
      ui: useUiStore(),
      party: usePartyStore(),
      chat: useChatStore()
    }
    
    // Register event handlers
    this.registerEventHandlers()
    
    // Connect to SSE if not already connected
    if (!eventService.connected) {
      eventService.connect()
    }
    
    this.initialized = true
    console.log('EventRouter initialized')
  }
  
  /**
   * Register all event handlers
   */
  registerEventHandlers() {
    // Chat/Narrative events
    eventService.on('narrative_added', (event) => {
      // Use the correct chatStore method
      if (this.stores.chat.handleNarrativeEvent) {
        this.stores.chat.handleNarrativeEvent(event)
      } else if (this.stores.chat.addNarrative) {
        this.stores.chat.addNarrative(event)
      }
      // Also keep in gameStore for backward compatibility
      if (this.stores.game.eventHandlers?.narrative_added) {
        this.stores.game.eventHandlers.narrative_added(event)
      }
    })
    
    // Combat events - now routed to combatStore
    eventService.on('combat_started', (event) => {
      this.stores.combat.handleCombatStarted(event)
    })
    
    eventService.on('combat_ended', (event) => {
      this.stores.combat.handleCombatEnded(event)
      // Clear dice requests when combat ends
      this.stores.dice.clearAllRequests()
    })
    
    eventService.on('turn_advanced', (event) => {
      this.stores.combat.handleTurnAdvanced(event)
    })
    
    eventService.on('combatant_initiative_set', (event) => {
      this.stores.combat.handleCombatantInitiativeSet(event)
    })
    
    eventService.on('initiative_order_determined', (event) => {
      this.stores.combat.handleInitiativeOrderDetermined(event)
    })
    
    eventService.on('combatant_added', (event) => {
      this.stores.combat.handleCombatantAdded(event)
    })
    
    eventService.on('combatant_removed', (event) => {
      this.stores.combat.handleCombatantRemoved(event)
    })
    
    // HP/Status events - route to both combat and party stores
    eventService.on('combatant_hp_changed', (event) => {
      this.stores.combat.handleCombatantHpChanged(event)
      this.stores.party.handleCombatantHpChanged(event)
    })
    
    eventService.on('combatant_status_changed', (event) => {
      this.stores.combat.handleCombatantStatusChanged(event)
      this.stores.party.handleCombatantStatusChanged(event)
    })
    
    // Dice events - now routed to diceStore
    eventService.on('player_dice_request_added', (event) => {
      this.stores.dice.handlePlayerDiceRequestAdded(event)
    })
    
    eventService.on('player_dice_requests_cleared', (event) => {
      this.stores.dice.handlePlayerDiceRequestsCleared(event)
    })
    
    eventService.on('npc_dice_roll_processed', (event) => {
      // Log for now, could add to a roll history store
      console.log('NPC dice roll processed:', event)
    })
    
    // Party/Inventory events
    eventService.on('party_member_updated', (event) => {
      this.stores.party.handlePartyMemberUpdated(event)
    })
    
    eventService.on('item_added', (event) => {
      this.stores.party.handleItemAdded(event)
      // Also add to chat as a system message if the method exists
      if (this.stores.chat.addSystemMessage) {
        this.stores.chat.addSystemMessage(
          `${event.character_name} received: ${event.item_name}${event.quantity > 1 ? ` x${event.quantity}` : ''}`
        )
      }
    })
    
    // Location events
    eventService.on('location_changed', (event) => {
      // Keep in gameStore for now
      if (this.stores.game.eventHandlers?.location_changed) {
        this.stores.game.eventHandlers.location_changed(event)
      }
    })
    
    // Quest events
    eventService.on('quest_updated', (event) => {
      // Add to chat as system message if the method exists
      if (this.stores.chat.addSystemMessage) {
        this.stores.chat.addSystemMessage(
          `Quest Updated: ${event.quest_title} - ${event.new_status}`
        )
      }
    })
    
    // UI/System events
    eventService.on('backend_processing', (event) => {
      this.stores.ui.handleBackendProcessing(event)
    })
    
    eventService.on('game_error', (event) => {
      this.stores.ui.handleGameError(event)
      // Also add to chat for visibility if the method exists
      if (this.stores.chat.addSystemMessage) {
        this.stores.chat.addSystemMessage(
          `Error: ${event.error_message}`,
          { severity: event.severity }
        )
      }
    })
    
    // Game state snapshot - distribute to all stores
    eventService.on('game_state_snapshot', (event) => {
      console.log('EventRouter: Distributing game state snapshot to all stores')
      
      // Each store handles its relevant portion
      this.stores.party.handleGameStateSnapshot(event)
      this.stores.dice.handleGameStateSnapshot(event)
      this.stores.ui.handleGameStateSnapshot(event)
      this.stores.chat.handleGameStateSnapshot(event)
      
      // Combat state from snapshot
      if (event.combat_state) {
        this.stores.combat.handleGameStateSnapshot(event.combat_state)
      }
      
      // Keep gameStore handler for backward compatibility
      if (this.stores.game.eventHandlers?.game_state_snapshot) {
        this.stores.game.eventHandlers.game_state_snapshot(event)
      }
    })
    
    // Handle state reconciliation requests
    eventService.on('state:reconcile', (event) => {
      console.log('EventRouter: State reconciliation requested', event)
      this.requestStateReconciliation(event.lastEventTime)
    })
    
    // Handle connection restoration
    eventService.on('connection:restored', (event) => {
      console.log('EventRouter: Connection restored, requesting fresh state')
      // Request a fresh game state snapshot after reconnection
      this.stores.game.loadGameState()
    })
  }
  
  /**
   * Request state reconciliation from the backend
   * This is called after reconnection to ensure state consistency
   * @param {string} lastEventTime - The timestamp of the last received event
   */
  async requestStateReconciliation(lastEventTime) {
    try {
      console.log('EventRouter: Requesting state reconciliation from:', lastEventTime)
      
      // For now, just request a fresh game state
      // In the future, the backend could send only missed events
      await this.stores.game.loadGameState()
      
      console.log('EventRouter: State reconciliation completed')
    } catch (error) {
      console.error('EventRouter: State reconciliation failed:', error)
      this.stores.ui.addError({
        type: 'reconciliation',
        message: 'Failed to sync game state after reconnection',
        severity: 'error',
        recoverable: true
      })
    }
  }
  
  /**
   * Clean up event handlers
   */
  cleanup() {
    // Remove all event listeners
    eventService.off('narrative_added')
    eventService.off('combat_started')
    eventService.off('combat_ended')
    eventService.off('turn_advanced')
    eventService.off('combatant_initiative_set')
    eventService.off('initiative_order_determined')
    eventService.off('combatant_added')
    eventService.off('combatant_removed')
    eventService.off('combatant_hp_changed')
    eventService.off('combatant_status_changed')
    eventService.off('player_dice_request_added')
    eventService.off('player_dice_requests_cleared')
    eventService.off('npc_dice_roll_processed')
    eventService.off('party_member_updated')
    eventService.off('item_added')
    eventService.off('location_changed')
    eventService.off('quest_updated')
    eventService.off('backend_processing')
    eventService.off('game_error')
    eventService.off('game_state_snapshot')
    
    this.initialized = false
  }
}

// Export singleton instance
export const eventRouter = new EventRouter()

// Export initialization function for use in main app
export function initializeEventRouter() {
  eventRouter.initialize()
}