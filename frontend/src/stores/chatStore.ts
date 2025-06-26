/**
 * Chat Store - Manages all chat/narrative messages
 *
 * This store handles all narrative content in the game, including:
 * - Player messages
 * - GM narrative responses
 * - System messages (combat events, dice rolls, etc.)
 *
 * The store receives messages through SSE events (narrative_added) and
 * maintains them in chronological order for display in the chat UI.
 *
 * @module chatStore
 */
import { defineStore } from 'pinia'
import eventService from '@/services/eventService'
import type {
  ChatMessageModel,
  NarrativeAddedEvent,
  MessageSupersededEvent,
  GameStateSnapshotEvent,
} from '@/types/unified'

// Extended chat message for UI
interface UIChatMessage extends Omit<ChatMessageModel, 'is_dice_result'> {
  type: 'assistant' | 'user' | 'system'
  sequence_number?: number
  superseded?: boolean
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    /**
     * Array of all chat messages received via SSE events
     */
    messages: [] as UIChatMessage[],

    /**
     * Tracks SSE connection status
     */
    isConnected: false,
  }),

  getters: {
    /**
     * Get all messages sorted by timestamp
     */
    sortedMessages(): UIChatMessage[] {
      return [...this.messages].sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime()
        const timeB = new Date(b.timestamp).getTime()
        return timeA - timeB
      })
    },

    /**
     * Get only visible messages (non-system messages)
     */
    visibleMessages(): UIChatMessage[] {
      return this.sortedMessages.filter(
        msg => msg.role !== 'system' || msg.content.includes('Combat')
      )
    },
  },

  actions: {
    /**
     * Initialize the chat store and connect to SSE
     */
    initialize(): void {
      // Note: Event handlers are now registered by eventRouter
      // This method is kept for backward compatibility

      // Connect to SSE
      eventService.connect()
      this.isConnected = eventService.connected

      // Monitor connection status
      setInterval(() => {
        this.isConnected = eventService.connected
      }, 1000)
    },

    /**
     * Clean up when store is destroyed
     */
    cleanup(): void {
      // Note: Event handlers are now managed by eventRouter
      eventService.disconnect()
    },

    /**
     * Handle incoming narrative events
     */
    handleNarrativeEvent(event: NarrativeAddedEvent): void {
      console.log('ChatStore: Received narrative event:', event)

      // Add to messages
      this.addNarrative(event)
    },

    /**
     * Add a narrative message from an event
     */
    addNarrative(event: NarrativeAddedEvent): void {
      const message: UIChatMessage = {
        id: event.message_id || event.event_id,
        type: this.mapRoleToType(event.role),
        role: event.role as ChatMessageModel['role'],
        content: event.content,
        timestamp: event.timestamp,
        gm_thought: event.gm_thought,
        audio_path: event.audio_path
          ? `/static/${event.audio_path}`
          : undefined,
        sequence_number: event.sequence_number,
        superseded: false, // New messages are not superseded
      }

      // Check for duplicates by message_id
      const exists = this.messages.some(m => m.id === message.id)
      if (!exists) {
        this.messages.push(message)
      }
    },

    /**
     * Handle message superseded events
     */
    handleMessageSupersededEvent(event: MessageSupersededEvent): void {
      console.log('ChatStore: Received message superseded event:', event)

      // Find the message and mark it as superseded
      const message = this.messages.find(m => m.id === event.message_id)
      if (message) {
        message.superseded = true
        console.log(
          `ChatStore: Marked message ${event.message_id} as superseded`
        )
      } else {
        console.warn(
          `ChatStore: Could not find message ${event.message_id} to mark as superseded`
        )
      }
    },

    /**
     * Map role to frontend message type
     */
    mapRoleToType(role: string): 'assistant' | 'user' | 'system' {
      switch (role) {
        case 'assistant':
          return 'assistant'
        case 'user':
          return 'user'
        case 'system':
          return 'system'
        default:
          return 'system'
      }
    },

    /**
     * Add a system message
     */
    addSystemMessage(
      content: string,
      metadata?: Record<string, unknown>
    ): void {
      const message: UIChatMessage = {
        id: `system-${Date.now()}-${Math.random()}`,
        type: 'system',
        role: 'system',
        content,
        timestamp: new Date().toISOString(),
        ...metadata,
      }
      this.messages.push(message)
    },

    /**
     * Clear all messages
     */
    clearMessages(): void {
      this.messages = []
    },

    /**
     * Get message by ID
     */
    getMessageById(id: string): UIChatMessage | undefined {
      return this.messages.find(m => m.id === id)
    },

    /**
     * Get messages by role
     */
    getMessagesByRole(role: ChatMessageModel['role']): UIChatMessage[] {
      return this.messages.filter(m => m.role === role)
    },

    /**
     * Get recent messages
     */
    getRecentMessages(count: number = 10): UIChatMessage[] {
      return this.sortedMessages.slice(-count)
    },

    /**
     * Handle game state snapshot event
     */
    handleGameStateSnapshot(
      snapshotData: Partial<GameStateSnapshotEvent>
    ): void {
      console.log('ChatStore: Processing game state snapshot')

      // Load chat history from snapshot if available
      if (
        snapshotData.chat_history &&
        Array.isArray(snapshotData.chat_history)
      ) {
        // Clear existing messages if this is initial load
        if (this.messages.length === 0) {
          this.messages = snapshotData.chat_history.map(msg => ({
            id: msg.id || `${Date.now()}-${Math.random()}`,
            type: this.mapRoleToType(msg.role),
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp || new Date().toISOString(),
            gm_thought: msg.gm_thought,
            audio_path: msg.audio_path
              ? `/static/${msg.audio_path}`
              : undefined,
            superseded: false,
          }))
          console.log(
            `ChatStore: Loaded ${this.messages.length} messages from snapshot`
          )
        }
      }
    },
  },
})
