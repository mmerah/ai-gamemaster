/**
 * Additional event types for internal SSE events
 * These complement the events defined in unified.ts
 */

import type { BaseGameEvent } from './unified'

/**
 * Event fired when state reconciliation is needed after reconnection
 */
export interface StateReconcileEvent extends BaseGameEvent {
  event_type: 'state:reconcile'
  lastEventTime: string
}

/**
 * Event fired when SSE connection is restored
 */
export interface ConnectionRestoredEvent extends BaseGameEvent {
  event_type: 'connection:restored'
  lastEventTime: string
  reconnectAttempts: number
}

/**
 * Event fired when connection is lost
 */
export interface ConnectionLostEvent extends BaseGameEvent {
  event_type: 'connection:lost'
  lastEventTime: string | null
  willReconnect: boolean
}

/**
 * Event fired when connection fails completely
 */
export interface ConnectionFailedEvent extends BaseGameEvent {
  event_type: 'connection:failed'
  attempts: number
  lastEventTime: string | null
}

/**
 * Error event for parsing failures
 */
export interface ParseErrorEvent extends BaseGameEvent {
  event_type: 'error'
  type: 'parse_error'
  error: unknown
  data: string
  message?: string
}

/**
 * Union type of all internal events
 */
export type InternalEvent =
  | StateReconcileEvent
  | ConnectionRestoredEvent
  | ConnectionLostEvent
  | ConnectionFailedEvent
  | ParseErrorEvent

/**
 * Type guard to check if an event is an internal event
 */
export function isInternalEvent(event: unknown): event is InternalEvent {
  return (
    typeof event === 'object' &&
    event !== null &&
    'event_type' in event &&
    [
      'state:reconcile',
      'connection:restored',
      'connection:lost',
      'connection:failed',
      'error',
    ].includes((event as { event_type: string }).event_type)
  )
}
