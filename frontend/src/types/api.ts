/**
 * Common API types used across the application
 */

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T = any> {
  data: T
  error?: string
  message?: string
  status?: number
}

/**
 * API Error response
 */
export interface ApiError {
  error: string
  message?: string
  details?: Record<string, any>
  status?: number
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  page?: number
  limit?: number
  sort?: string
  order?: 'asc' | 'desc'
}

/**
 * Common query parameters
 */
export interface QueryParams {
  [key: string]: string | number | boolean | undefined
}

/**
 * File upload response
 */
export interface FileUploadResponse {
  filename: string
  path: string
  size: number
  mime_type?: string
}
