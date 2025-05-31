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
import { ref, onMounted, onUnmounted } from 'vue'
import eventService from '@/services/eventService'

export const useUiStore = defineStore('ui', () => {
  // Loading states
  const isBackendProcessing = ref(false)
  const needsBackendTrigger = ref(false)
  const canRetryLastRequest = ref(false)
  
  // Error state
  const lastError = ref(null)
  const errorQueue = ref([])
  
  // Connection state
  const isConnected = ref(false)
  const connectionStatus = ref('disconnected') // 'connecting'|'connected'|'disconnected'|'reconnecting'|'failed'
  const reconnectAttempts = ref(0)
  const lastConnectionTime = ref(null)
  
  // Actions
  function handleBackendProcessing(event) {
    console.log('UIStore: Backend processing event:', event)
    isBackendProcessing.value = event.is_processing
    needsBackendTrigger.value = event.needs_backend_trigger || false
  }
  
  function handleGameError(event) {
    console.log('UIStore: Game error event:', event)
    
    const error = {
      id: event.event_id,
      message: event.error_message,
      details: event.error_details,
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
  
  function handleGameStateSnapshot(snapshotData) {
    if (!snapshotData) return
    
    // Update flags from snapshot
    if (snapshotData.can_retry_last_request !== undefined) {
      canRetryLastRequest.value = snapshotData.can_retry_last_request
    }
    
    if (snapshotData.needs_backend_trigger !== undefined) {
      needsBackendTrigger.value = snapshotData.needs_backend_trigger
    }
  }
  
  /**
   * Initialize connection state monitoring
   */
  let unsubscribeConnectionState = null
  
  function initializeConnectionMonitoring() {
    // Subscribe to connection state changes
    unsubscribeConnectionState = eventService.onConnectionStateChange((state) => {
      connectionStatus.value = state
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
  function handleConnectionLost(event) {
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
  function handleConnectionRestored(event) {
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
  function handleConnectionFailed(event) {
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
  function handleEventError(event) {
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
  function addError(error) {
    const errorEntry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...error
    }
    
    lastError.value = errorEntry
    errorQueue.value.push(errorEntry)
    
    // Keep only last 10 errors
    if (errorQueue.value.length > 10) {
      errorQueue.value = errorQueue.value.slice(-10)
    }
  }
  
  function setConnectionStatus(status) {
    connectionStatus.value = status
    isConnected.value = (status === 'connected')
  }
  
  function clearLastError() {
    lastError.value = null
  }
  
  function clearErrorQueue() {
    errorQueue.value = []
  }
  
  function disableRetry() {
    canRetryLastRequest.value = false
  }
  
  function resetUIState() {
    isBackendProcessing.value = false
    needsBackendTrigger.value = false
    canRetryLastRequest.value = false
    lastError.value = null
    errorQueue.value = []
  }
  
  /**
   * Cleanup function
   */
  function cleanup() {
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