/**
 * Type-safe error handling utilities
 */

import type { AxiosError } from 'axios'

interface APIError {
  message?: string
  userMessage?: string
  details?: Record<string, unknown>
}

/**
 * Extract error message from various error types
 */
export function getErrorMessage(error: unknown): string {
  // Handle Axios errors
  if (isAxiosError(error)) {
    const data = error.response?.data as APIError | undefined
    return (
      data?.userMessage || data?.message || error.message || 'Network error'
    )
  }

  // Handle standard Error objects
  if (error instanceof Error) {
    return error.message
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error
  }

  // Unknown error type
  return 'Unknown error'
}

/**
 * Type guard for Axios errors
 */
export function isAxiosError(error: unknown): error is AxiosError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  )
}

/**
 * Extract user-friendly error message for API errors
 */
export function getAPIErrorMessage(
  error: unknown,
  defaultMessage: string
): string {
  if (isAxiosError(error)) {
    const data = error.response?.data as APIError | undefined
    return data?.userMessage || data?.message || defaultMessage
  }
  return getErrorMessage(error)
}
