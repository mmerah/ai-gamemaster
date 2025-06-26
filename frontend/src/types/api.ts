/**
 * Additional API types not in unified.ts
 */

export interface ErrorResponse {
  error: string
  details?: unknown
  userMessage?: string
}

/**
 * Generic API response wrapper used by API services
 */
export interface ApiResponse<T = unknown> {
  data: T
  error?: string
  message?: string
}
