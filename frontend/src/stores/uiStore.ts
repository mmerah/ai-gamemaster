/**
 * UI Store - Manages UI state and connection status
 *
 * This store handles all UI-related state including:
 * - Loading indicators
 * - Connection status
 * - Error management
 * - Backend processing states
 *
 * @module uiStore
 */
import { defineStore } from 'pinia'
import { ref, Ref } from 'vue'
import eventService from '@/services/eventService'
import type {
  BackendProcessingEvent,
  GameErrorEvent,
  GameStateSnapshotEvent
} from '@/types/unified'
import type {
  ConnectionLostEvent,
  ConnectionRestoredEvent,
  ConnectionFailedEvent,
  ParseErrorEvent
} from '@/types/events'

// Error types
interface UIError {
  id: string | number
  message: string
  details?: unknown
  severity: 'warning' | 'error' | 'critical'
  type?: string
  errorType?: string
  recoverable?: boolean
  timestamp: string
}

// Connection status type
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'failed'

export const useUiStore = defineStore('ui', () => {
  // Loading states
  const isBackendProcessing = ref(false)
  const needsBackendTrigger = ref(false)
  const canRetryLastRequest = ref(false)

  // Error state
  const lastError: Ref<UIError | null> = ref(null)
  const errorQueue: Ref<UIError[]> = ref([])

  // Connection state
  const isConnected = ref(false)
  const connectionStatus: Ref<ConnectionStatus> = ref('disconnected')
  const reconnectAttempts = ref(0)
  const lastConnectionTime: Ref<string | null> = ref(null)

  // Actions
  function handleBackendProcessing(event: BackendProcessingEvent): void {
    console.log('UIStore: Backend processing event:', event)
    isBackendProcessing.value = event.is_processing
    needsBackendTrigger.value = event.needs_backend_trigger || false
  }

  function handleGameError(event: GameErrorEvent): void {
    console.log('UIStore: Game error event:', event)

    const error: UIError = {
      id: event.event_id,
      message: event.error_message,
      details: event.context,
      severity: event.severity,
      errorType: event.error_type,
      recoverable: event.recoverable,
      timestamp: event.timestamp
    }

    lastError.value = error
    errorQueue.value.push(error)

    // Keep only last 10 errors
    if (errorQueue.value.length > 10) {
      errorQueue.value = errorQueue.value.slice(-10)
    }

    // Enable retry if the error is recoverable
    if (event.recoverable) {
      canRetryLastRequest.value = true
    }
  }

  function handleGameStateSnapshot(snapshotData: Partial<GameStateSnapshotEvent>): void {
    if (!snapshotData) return

    // Update flags from snapshot if they exist
    // These properties might be added by the backend but aren't in the type definition
    const snapshot = snapshotData as Partial<GameStateSnapshotEvent> & {
      can_retry_last_request?: boolean
      needs_backend_trigger?: boolean
    }

    if (snapshot.can_retry_last_request !== undefined) {
      canRetryLastRequest.value = snapshot.can_retry_last_request
    }

    if (snapshot.needs_backend_trigger !== undefined) {
      needsBackendTrigger.value = snapshot.needs_backend_trigger
    }
  }

  /**
   * Initialize connection state monitoring
   */
  let unsubscribeConnectionState: (() => void) | null = null

  function initializeConnectionMonitoring(): void {
    // Subscribe to connection state changes
    unsubscribeConnectionState = eventService.onConnectionStateChange((state: string) => {
      connectionStatus.value = state as ConnectionStatus
      isConnected.value = (state === 'connected')

      if (state === 'connected') {
        lastConnectionTime.value = new Date().toISOString()
        reconnectAttempts.value = 0
      }
    })

    // Listen for connection events
    eventService.on('connection:lost', handleConnectionLost)
    eventService.on('connection:restored', handleConnectionRestored)
    eventService.on('connection:failed', handleConnectionFailed)
    eventService.on('error', handleEventError)
  }

  /**
   * Handle connection lost event
   */
  function handleConnectionLost(event: ConnectionLostEvent): void {
    console.warn('UIStore: Connection lost', event)
    addError({
      type: 'connection',
      message: 'Connection to server lost. Attempting to reconnect...',
      severity: 'warning',
      recoverable: true
    })
  }

  /**
   * Handle connection restored event
   */
  function handleConnectionRestored(event: ConnectionRestoredEvent): void {
    console.log('UIStore: Connection restored', event)
    reconnectAttempts.value = event.reconnectAttempts || 0

    // Clear connection-related errors
    errorQueue.value = errorQueue.value.filter(e => e.type !== 'connection')

    // Request state reconciliation
    eventService.emit('state:reconcile', {
      lastEventTime: event.lastEventTime
    })
  }

  /**
   * Handle connection failed event
   */
  function handleConnectionFailed(event: ConnectionFailedEvent): void {
    console.error('UIStore: Connection failed', event)
    addError({
      type: 'connection',
      message: 'Failed to connect to server after multiple attempts',
      severity: 'error',
      recoverable: false
    })
  }

  /**
   * Handle general event errors
   */
  function handleEventError(event: ParseErrorEvent): void {
    console.error('UIStore: Event error', event)
    addError({
      type: event.type || 'unknown',
      message: event.message || 'An unexpected error occurred',
      severity: 'error',
      recoverable: true,
      details: event
    })
  }

  /**
   * Add an error to the queue
   */
  function addError(error: Partial<UIError>): void {
    const errorEntry: UIError = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      message: error.message || 'Unknown error',
      severity: error.severity || 'error',
      ...error
    }

    lastError.value = errorEntry
    errorQueue.value.push(errorEntry)

    // Keep only last 10 errors
    if (errorQueue.value.length > 10) {
      errorQueue.value = errorQueue.value.slice(-10)
    }
  }

  function setConnectionStatus(status: ConnectionStatus): void {
    connectionStatus.value = status
    isConnected.value = (status === 'connected')
  }

  function clearLastError(): void {
    lastError.value = null
  }

  function clearErrorQueue(): void {
    errorQueue.value = []
  }

  function disableRetry(): void {
    canRetryLastRequest.value = false
  }

  function resetUIState(): void {
    isBackendProcessing.value = false
    needsBackendTrigger.value = false
    canRetryLastRequest.value = false
    lastError.value = null
    errorQueue.value = []
  }

  /**
   * Cleanup function
   */
  function cleanup(): void {
    if (unsubscribeConnectionState) {
      unsubscribeConnectionState()
    }
    eventService.off('connection:lost', handleConnectionLost)
    eventService.off('connection:restored', handleConnectionRestored)
    eventService.off('connection:failed', handleConnectionFailed)
    eventService.off('error', handleEventError)
  }

  // Initialize on store creation
  initializeConnectionMonitoring()

  return {
    // State
    isBackendProcessing,
    needsBackendTrigger,
    canRetryLastRequest,
    lastError,
    errorQueue,
    isConnected,
    connectionStatus,
    reconnectAttempts,
    lastConnectionTime,

    // Actions
    handleBackendProcessing,
    handleGameError,
    handleGameStateSnapshot,
    setConnectionStatus,
    clearLastError,
    clearErrorQueue,
    disableRetry,
    resetUIState,
    addError,

    // Lifecycle
    cleanup
  }
})
