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
import { logger } from '@/utils/logger'
import type {
  NarrativeAddedEvent,
  MessageSupersededEvent,
  CombatStartedEvent,
  CombatEndedEvent,
  TurnAdvancedEvent,
  CombatantInitiativeSetEvent,
  InitiativeOrderDeterminedEvent,
  CombatantAddedEvent,
  CombatantRemovedEvent,
  CombatantHpChangedEvent,
  CombatantStatusChangedEvent,
  PlayerDiceRequestAddedEvent,
  PlayerDiceRequestsClearedEvent,
  PartyMemberUpdatedEvent,
  ItemAddedEvent,
  LocationChangedEvent,
  QuestUpdatedEvent,
  BackendProcessingEvent,
  GameErrorEvent,
  GameStateSnapshotEvent,
  NpcDiceRollProcessedEvent,
} from '@/types/unified'
import type {
  StateReconcileEvent,
  ConnectionRestoredEvent,
} from '@/types/events'
import type { ChatStoreType } from './types'

// Store instances type with proper typing for methods
interface Stores {
  game: ReturnType<typeof useGameStore>
  combat: ReturnType<typeof useCombatStore>
  dice: ReturnType<typeof useDiceStore>
  ui: ReturnType<typeof useUiStore>
  party: ReturnType<typeof usePartyStore>
  chat: ReturnType<typeof useChatStore>
}

// Event handler types
type EventHandler<T> = (event: T) => void

/**
 * Central event router that distributes SSE events to appropriate stores
 * Uses a singleton pattern to ensure only one router instance exists
 */
class EventRouter {
  private initialized: boolean
  private stores: Partial<Stores>
  private eventHandlers: Map<string, EventHandler<unknown>>

  constructor() {
    this.initialized = false
    this.stores = {}
    this.eventHandlers = new Map()
  }

  /**
   * Initialize the event router and connect all stores
   */
  initialize(): void {
    if (this.initialized) {
      logger.warn('EventRouter already initialized')
      return
    }

    // Get store instances
    this.stores = {
      game: useGameStore(),
      combat: useCombatStore(),
      dice: useDiceStore(),
      ui: useUiStore(),
      party: usePartyStore(),
      chat: useChatStore(),
    }

    // Register event handlers
    this.registerEventHandlers()

    // Connect to SSE if not already connected
    if (!eventService.connected) {
      eventService.connect()
    }

    this.initialized = true
    logger.debug('EventRouter initialized')
  }

  /**
   * Register all event handlers
   */
  private registerEventHandlers(): void {
    // Chat/Narrative events
    eventService.on('narrative_added', (event: NarrativeAddedEvent) => {
      // Route to chatStore
      this.stores.chat?.handleNarrativeEvent(event)
    })

    eventService.on('message_superseded', (event: MessageSupersededEvent) => {
      this.stores.chat?.handleMessageSupersededEvent(event)
    })

    // Combat events - now routed to combatStore
    eventService.on('combat_started', (event: CombatStartedEvent) => {
      this.stores.combat?.handleCombatStarted(event)
    })

    eventService.on('combat_ended', (event: CombatEndedEvent) => {
      this.stores.combat?.handleCombatEnded(event)
      // Clear dice requests when combat ends
      this.stores.dice?.clearAllRequests()
    })

    eventService.on('turn_advanced', (event: TurnAdvancedEvent) => {
      this.stores.combat?.handleTurnAdvanced(event)
    })

    eventService.on(
      'combatant_initiative_set',
      (event: CombatantInitiativeSetEvent) => {
        this.stores.combat?.handleCombatantInitiativeSet(event)
      }
    )

    eventService.on(
      'initiative_order_determined',
      (event: InitiativeOrderDeterminedEvent) => {
        this.stores.combat?.handleInitiativeOrderDetermined(event)
      }
    )

    eventService.on('combatant_added', (event: CombatantAddedEvent) => {
      this.stores.combat?.handleCombatantAdded(event)
    })

    eventService.on('combatant_removed', (event: CombatantRemovedEvent) => {
      this.stores.combat?.handleCombatantRemoved(event)
    })

    // HP/Status events - route to both combat and party stores
    eventService.on(
      'combatant_hp_changed',
      (event: CombatantHpChangedEvent) => {
        this.stores.combat?.handleCombatantHpChanged(event)
        this.stores.party?.handleCombatantHpChanged(event)
      }
    )

    eventService.on(
      'combatant_status_changed',
      (event: CombatantStatusChangedEvent) => {
        this.stores.combat?.handleCombatantStatusChanged(event)
        this.stores.party?.handleCombatantStatusChanged(event)
      }
    )

    // Dice events - now routed to diceStore
    eventService.on(
      'player_dice_request_added',
      (event: PlayerDiceRequestAddedEvent) => {
        this.stores.dice?.handlePlayerDiceRequestAdded(event)
      }
    )

    eventService.on(
      'player_dice_requests_cleared',
      (event: PlayerDiceRequestsClearedEvent) => {
        this.stores.dice?.handlePlayerDiceRequestsCleared(event)
      }
    )

    eventService.on(
      'npc_dice_roll_processed',
      (event: NpcDiceRollProcessedEvent) => {
        // Log for now, could add to a roll history store
        logger.debug('NPC dice roll processed:', event)
      }
    )

    // Party/Inventory events
    eventService.on(
      'party_member_updated',
      (event: PartyMemberUpdatedEvent) => {
        this.stores.party?.handlePartyMemberUpdated(event)

        // Add system message for gold changes
        // Note: The backend sends the new gold total, not a delta
        // To show meaningful messages, we'd need to track the previous value
        if (
          event.changes?.gold !== undefined &&
          event.gold_source &&
          this.stores.chat
        ) {
          let message = `${event.character_name}'s gold updated`
          if (event.gold_source) {
            message += ` from ${event.gold_source}`
          }
          const chatStore = this.stores.chat as ChatStoreType
          chatStore.addSystemMessage(message)
        }
      }
    )

    eventService.on('item_added', (event: ItemAddedEvent) => {
      this.stores.party?.handleItemAdded(event)
      // Also add to chat as a system message
      if (this.stores.chat) {
        const chatStore = this.stores.chat as ChatStoreType
        chatStore.addSystemMessage(
          `${event.character_name} received: ${event.item_name}${event.quantity > 1 ? ` x${event.quantity}` : ''}`
        )
      }
    })

    // Location events
    eventService.on('location_changed', (event: LocationChangedEvent) => {
      // Keep in gameStore for now
      if (this.stores.game?.eventHandlers?.location_changed) {
        this.stores.game.eventHandlers.location_changed(event)
      }
    })

    // Quest events
    eventService.on('quest_updated', (event: QuestUpdatedEvent) => {
      // Add to chat as system message
      if (this.stores.chat) {
        const chatStore = this.stores.chat as ChatStoreType
        chatStore.addSystemMessage(
          `Quest Updated: ${event.quest_title} - ${event.new_status}`
        )
      }
    })

    // UI/System events
    eventService.on('backend_processing', (event: BackendProcessingEvent) => {
      this.stores.ui?.handleBackendProcessing(event)
    })

    eventService.on('game_error', (event: GameErrorEvent) => {
      this.stores.ui?.handleGameError(event)
      // Also add to chat for visibility
      if (this.stores.chat) {
        const chatStore = this.stores.chat as ChatStoreType
        chatStore.addSystemMessage(`Error: ${event.error_message}`, {
          severity: event.severity,
        })
      }
    })

    // Game state snapshot - distribute to all stores
    eventService.on('game_state_snapshot', (event: GameStateSnapshotEvent) => {
      logger.debug(
        'EventRouter: Distributing game state snapshot to all stores'
      )

      // Each store handles its relevant portion
      this.stores.party?.handleGameStateSnapshot(event)
      this.stores.dice?.handleGameStateSnapshot(event)
      this.stores.ui?.handleGameStateSnapshot(event)
      this.stores.chat?.handleGameStateSnapshot(event)

      // Combat state from snapshot
      if (event.combat_state) {
        this.stores.combat?.handleGameStateSnapshot(event.combat_state)
      }

      // Keep gameStore handler for backward compatibility
      if (this.stores.game?.eventHandlers?.game_state_snapshot) {
        this.stores.game.eventHandlers.game_state_snapshot(event)
      }
    })

    // Handle state reconciliation requests
    eventService.on('state:reconcile', (event: StateReconcileEvent) => {
      logger.debug('EventRouter: State reconciliation requested', event)
      this.requestStateReconciliation(event.lastEventTime)
    })

    // Handle connection restoration
    eventService.on(
      'connection:restored',
      (_event: ConnectionRestoredEvent) => {
        logger.debug('EventRouter: Connection restored, requesting fresh state')
        // Request a fresh game state snapshot after reconnection
        this.stores.game?.loadGameState()
      }
    )
  }

  /**
   * Request state reconciliation from the backend
   * This is called after reconnection to ensure state consistency
   * @param {string} lastEventTime - The timestamp of the last received event
   */
  async requestStateReconciliation(lastEventTime: string): Promise<void> {
    try {
      logger.debug(
        'EventRouter: Requesting state reconciliation from:',
        lastEventTime
      )

      // For now, just request a fresh game state
      // In the future, the backend could send only missed events
      await this.stores.game?.loadGameState()

      logger.debug('EventRouter: State reconciliation completed')
    } catch (error) {
      console.error('EventRouter: State reconciliation failed:', error)
      this.stores.ui?.addError({
        type: 'reconciliation',
        message: 'Failed to sync game state after reconnection',
        severity: 'error',
        recoverable: true,
      })
    }
  }

  /**
   * Clean up event handlers
   */
  cleanup(): void {
    // Since we don't have references to all handlers, we'll need to
    // disconnect the entire event source and reconnect later if needed
    if (eventService.disconnect) {
      eventService.disconnect()
    }

    this.eventHandlers.clear()
    this.initialized = false
  }
}

// Export singleton instance
export const eventRouter = new EventRouter()

// Export initialization function for use in main app
export function initializeEventRouter(): void {
  eventRouter.initialize()
}
