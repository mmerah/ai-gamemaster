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

export const useChatStore = defineStore('chat', {
  state: () => ({
    /**
     * Array of all chat messages received via SSE events
     * @type {Array<{id: string, role: string, type: string, content: string, timestamp: string}>}
     */
    messages: [],
    
    /**
     * Tracks SSE connection status
     * @type {boolean}
     */
    isConnected: false,
    
  }),

  getters: {
    /**
     * Get all messages sorted by timestamp
     */
    sortedMessages() {
      return [...this.messages].sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime()
        const timeB = new Date(b.timestamp).getTime()
        return timeA - timeB
      })
    },

    /**
     * Get only visible messages (non-system messages)
     */
    visibleMessages() {
      return this.sortedMessages.filter(msg => 
        msg.role !== 'system' || msg.content.includes('Combat')
      )
    },

  },

  actions: {
    /**
     * Initialize the chat store and connect to SSE
     */
    initialize() {
      // Register event handler for narrative events
      eventService.on('narrative_added', this.handleNarrativeEvent.bind(this))
      eventService.on('message_superseded', this.handleMessageSupersededEvent.bind(this))
      
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
    cleanup() {
      eventService.off('narrative_added', this.handleNarrativeEvent)
      eventService.off('message_superseded', this.handleMessageSupersededEvent)
      eventService.disconnect()
    },

    /**
     * Handle incoming narrative events
     */
    handleNarrativeEvent(event) {
      console.log('ChatStore: Received narrative event:', event)
      
      // Add to messages
      this.addNarrative(event)
    },

    /**
     * Add a narrative message from an event
     */
    addNarrative(event) {
      const message = {
        id: event.message_id || event.event_id,
        type: this.mapRoleToType(event.role),
        role: event.role,
        content: event.content,
        timestamp: event.timestamp,
        gm_thought: event.gm_thought,
        tts_audio_url: event.audio_path ? `/static/${event.audio_path}` : null,
        sequence_number: event.sequence_number,
        superseded: false  // New messages are not superseded
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
    handleMessageSupersededEvent(event) {
      console.log('ChatStore: Received message superseded event:', event)
      
      // Find the message and mark it as superseded
      const message = this.messages.find(m => m.id === event.message_id)
      if (message) {
        message.superseded = true
        console.log(`ChatStore: Marked message ${event.message_id} as superseded`)
      } else {
        console.warn(`ChatStore: Could not find message ${event.message_id} to mark as superseded`)
      }
    },

    /**
     * Map role to frontend message type
     */
    mapRoleToType(role) {
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
    },

    /**
     * Add message from old system for comparison
     */
    addOldSystemMessage(message) {
      this.oldSystemMessages.push(message)
    },

    /**
     * Clear all messages
     */
    clearMessages() {
      this.messages = []
    },

    /**
     * Get message by ID
     */
    getMessageById(id) {
      return this.messages.find(m => m.id === id)
    },

    /**
     * Get messages by role
     */
    getMessagesByRole(role) {
      return this.messages.filter(m => m.role === role)
    },

    /**
     * Get recent messages
     */
    getRecentMessages(count = 10) {
      return this.sortedMessages.slice(-count)
    },

    /**
     * Handle game state snapshot event
     */
    handleGameStateSnapshot(snapshotData) {
      console.log('ChatStore: Processing game state snapshot')
      
      // Load chat history from snapshot if available
      if (snapshotData.chat_history && Array.isArray(snapshotData.chat_history)) {
        // Clear existing messages if this is initial load
        if (this.messages.length === 0) {
          this.messages = snapshotData.chat_history.map(msg => ({
            id: msg.message_id || msg.id || `${Date.now()}-${Math.random()}`,
            type: this.mapRoleToType(msg.role),
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp || new Date().toISOString(),
            gm_thought: msg.gm_thought,
            tts_audio_url: msg.audio_path ? `/static/${msg.audio_path}` : null,
            superseded: false
          }))
          console.log(`ChatStore: Loaded ${this.messages.length} messages from snapshot`)
        }
      }
    }
  }
})