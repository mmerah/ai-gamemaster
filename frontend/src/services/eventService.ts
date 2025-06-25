/**
 * Event Service for handling Server-Sent Events (SSE)
 *
 * This service manages the SSE connection to the backend and handles:
 * - Automatic reconnection with exponential backoff
 * - Event routing to registered handlers
 * - Connection state management
 * - Error recovery
 *
 * @module eventService
 */

type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'failed'
type EventHandler<T = unknown> = (eventData: T) => void
type ConnectionStateCallback = (state: ConnectionState) => void
type UnsubscribeFunction = () => void

interface EventData {
  event_type: string
  timestamp?: string
  [key: string]: unknown
}


class EventService {
  private eventSource: EventSource | null
  private isConnected: boolean
  private reconnectAttempts: number
  private maxReconnectAttempts: number
  private reconnectDelay: number
  private maxReconnectDelay: number
  private handlers: Map<string, EventHandler<unknown>[]>
  private connectionStateCallbacks: Set<ConnectionStateCallback>
  private lastEventTime: string | null
  private reconnectTimer: ReturnType<typeof setTimeout> | null

  constructor() {
    this.eventSource = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.reconnectDelay = 1000 // Base delay in ms
    this.maxReconnectDelay = 30000 // Max delay of 30 seconds
    this.handlers = new Map()
    this.connectionStateCallbacks = new Set()
    this.lastEventTime = null
    this.reconnectTimer = null
  }

  /**
   * Connect to the SSE endpoint
   */
  connect(): void {
    if (this.isConnected || this.eventSource) {
      console.warn('EventService: Already connected or connecting')
      return
    }

    const url = '/api/game_event_stream'
    console.log('EventService: Connecting to SSE endpoint:', url)

    try {
      this.eventSource = new EventSource(url)

      // Connection opened
      this.eventSource.onopen = () => {
        console.log('EventService: SSE connection established')
        this.isConnected = true
        this.reconnectAttempts = 0
        this.notifyConnectionState('connected')

        // Emit a reconnection event if this was a reconnect
        if (this.lastEventTime) {
          this.emit('connection:restored', {
            lastEventTime: this.lastEventTime,
            reconnectAttempts: this.reconnectAttempts
          })
        }
      }

      // Handle messages
      this.eventSource.onmessage = (event: MessageEvent) => {
        try {
          // Parse the JSON event data
          const eventData = JSON.parse(event.data)
          this.lastEventTime = new Date().toISOString()
          this.handleEvent(eventData)
        } catch (error) {
          console.error('EventService: Failed to parse event data:', error, event.data)
          this.emit('error', { type: 'parse_error', error, data: event.data })
        }
      }

      // Handle errors
      this.eventSource.onerror = (error: Event) => {
        console.error('EventService: SSE connection error:', error)
        this.isConnected = false
        this.notifyConnectionState('disconnected')

        if (this.eventSource?.readyState === EventSource.CLOSED) {
          console.log('EventService: Connection closed, attempting reconnect...')
          this.emit('connection:lost', {
            lastEventTime: this.lastEventTime,
            willReconnect: this.reconnectAttempts < this.maxReconnectAttempts
          })
          this.reconnect()
        }
      }
    } catch (error) {
      console.error('EventService: Failed to create EventSource:', error)
      this.isConnected = false
    }
  }

  /**
   * Disconnect from the SSE endpoint
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.eventSource) {
      console.log('EventService: Closing SSE connection')
      this.eventSource.close()
      this.eventSource = null
      this.isConnected = false
      this.reconnectAttempts = 0
      this.notifyConnectionState('disconnected')
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   * Uses exponential backoff strategy: delay = baseDelay * 2^(attempts-1)
   * Capped at maxReconnectDelay (30 seconds)
   */
  reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('EventService: Max reconnect attempts reached')
      this.emit('connection:failed', {
        attempts: this.reconnectAttempts,
        lastEventTime: this.lastEventTime
      })
      this.notifyConnectionState('failed')
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    )

    console.log(`EventService: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    this.notifyConnectionState('reconnecting')

    this.reconnectTimer = setTimeout(() => {
      this.disconnect() // Clean up any existing connection
      this.connect()
    }, delay)
  }

  /**
   * Register a handler for a specific event type
   * @param {string} eventType - The event type to handle
   * @param {Function} handler - The handler function
   */
  on<T = unknown>(eventType: string, handler: EventHandler<T>): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, [])
    }
    this.handlers.get(eventType)!.push(handler as EventHandler<unknown>)
  }

  /**
   * Remove a handler for a specific event type
   * @param {string} eventType - The event type
   * @param {Function} handler - The handler function to remove
   */
  off<T = unknown>(eventType: string, handler?: EventHandler<T>): void {
    if (!handler) {
      // Remove all handlers for this event type
      this.handlers.delete(eventType)
      return
    }

    const handlers = this.handlers.get(eventType)
    if (handlers) {
      const index = handlers.indexOf(handler as EventHandler<unknown>)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * Handle incoming events by routing to registered handlers
   * @param {Object} eventData - The parsed event data
   */
  handleEvent(eventData: EventData): void {
    const eventType = eventData.event_type

    if (!eventType) {
      console.warn('EventService: Received event without event_type:', eventData)
      return
    }

    // Log the event for debugging
    console.debug(`EventService: Received ${eventType} event:`, eventData)

    // Call registered handlers for this event type
    const handlers = this.handlers.get(eventType) || []
    handlers.forEach(handler => {
      try {
        handler(eventData)
      } catch (error) {
        console.error(`EventService: Handler error for ${eventType}:`, error)
      }
    })

    // Also call wildcard handlers (*)
    const wildcardHandlers = this.handlers.get('*') || []
    wildcardHandlers.forEach(handler => {
      try {
        handler(eventData)
      } catch (error) {
        console.error('EventService: Wildcard handler error:', error)
      }
    })
  }

  /**
   * Emit an internal event (for connection state changes, errors, etc.)
   * @param {string} eventType - The internal event type
   * @param {Object} data - Event data
   */
  emit(eventType: string, data: Record<string, unknown>): void {
    this.handleEvent({
      event_type: eventType,
      ...data,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Register a callback for connection state changes
   * @param {Function} callback - Function called with (state: 'connecting'|'connected'|'disconnected'|'reconnecting'|'failed')
   */
  onConnectionStateChange(callback: ConnectionStateCallback): UnsubscribeFunction {
    this.connectionStateCallbacks.add(callback)
    // Immediately call with current state
    callback(this.getConnectionState())

    return () => {
      this.connectionStateCallbacks.delete(callback)
    }
  }

  /**
   * Notify all registered callbacks of connection state change
   * @param {string} state - The new connection state
   */
  notifyConnectionState(state: ConnectionState): void {
    this.connectionStateCallbacks.forEach(callback => {
      try {
        callback(state)
      } catch (error) {
        console.error('EventService: Error in connection state callback:', error)
      }
    })
  }

  /**
   * Get the current connection state
   * @returns {string} Current state: 'connecting'|'connected'|'disconnected'|'reconnecting'|'failed'
   */
  getConnectionState(): ConnectionState {
    if (this.isConnected && this.eventSource?.readyState === EventSource.OPEN) {
      return 'connected'
    }
    if (this.reconnectTimer) {
      return 'reconnecting'
    }
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return 'failed'
    }
    if (this.eventSource && this.eventSource.readyState === EventSource.CONNECTING) {
      return 'connecting'
    }
    return 'disconnected'
  }

  /**
   * Check if the service is connected
   * @returns {boolean}
   */
  get connected(): boolean {
    return this.isConnected && this.eventSource?.readyState === EventSource.OPEN
  }

  /**
   * Reset the connection (useful for testing or manual intervention)
   */
  reset(): void {
    this.disconnect()
    this.reconnectAttempts = 0
    this.lastEventTime = null
    this.connect()
  }
}

// Create singleton instance
const eventService = new EventService()

export default eventService
