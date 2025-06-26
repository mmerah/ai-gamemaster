import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from 'axios'

// Extend AxiosError to include our custom fields
interface CustomAxiosError extends AxiosError {
  userMessage?: string
}

// Error response data structure from FastAPI
interface ErrorResponseData {
  error?: string
  validation_errors?: Array<{
    loc: string[]
    msg: string
    type: string
  }>
  details?: unknown
}

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add timestamp to prevent caching for certain requests
    if (config.method === 'get' && config.url?.includes('/poll')) {
      config.params = {
        ...(config.params as Record<string, unknown>),
        _t: Date.now(),
      }
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: CustomAxiosError) => {
    // Handle common error scenarios
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response as {
        status: number
        data: ErrorResponseData
      }

      // Handle FastAPI error format
      let errorMessage = ''
      let details = null

      // FastAPI returns errors in { error: string } format due to custom exception handler
      if (data && typeof data === 'object') {
        if (data.error) {
          errorMessage = data.error
        }
        if (data.validation_errors) {
          // FastAPI validation errors
          details = data.validation_errors
        } else if (data.details) {
          // Other detailed errors
          details = data.details
        }
      }

      switch (status) {
        case 401:
          // Unauthorized - redirect to login or clear auth
          localStorage.removeItem('auth_token')
          console.error('Authentication failed')
          break
        case 403:
          // Forbidden
          console.error('Access forbidden')
          break
        case 404:
          // Not found
          console.error('Resource not found:', error.config?.url)
          break
        case 422:
          // Validation error - FastAPI format
          if (details && Array.isArray(details)) {
            // Format validation errors for display
            const firstError = details[0] as { loc?: string[]; msg?: string }
            const loc = firstError.loc ? firstError.loc.join(' -> ') : 'field'
            errorMessage =
              errorMessage ||
              `Validation error in ${loc}: ${firstError.msg || 'unknown error'}`
          }
          console.error('Validation error:', details || errorMessage)
          break
        case 500:
          // Server error
          console.error(
            'Server error:',
            errorMessage || 'Internal server error'
          )
          break
        default:
          console.error('API Error:', errorMessage || `HTTP ${status}`)
      }

      // Add user-friendly error message
      error.userMessage = errorMessage || getDefaultErrorMessage(status)
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network error:', error.message)
      error.userMessage = 'Network error. Please check your connection.'
    } else {
      // Something else happened
      console.error('Request error:', error.message)
      error.userMessage = 'An unexpected error occurred.'
    }

    return Promise.reject(error)
  }
)

function getDefaultErrorMessage(status: number): string {
  const messages: Record<number, string> = {
    400: 'Bad request. Please check your input.',
    401: 'Please log in to continue.',
    403: 'You do not have permission to perform this action.',
    404: 'The requested resource was not found.',
    422: 'Invalid data provided.',
    500: 'Server error. Please try again later.',
    502: 'Service temporarily unavailable.',
    503: 'Service temporarily unavailable.',
    504: 'Request timeout. Please try again.',
  }

  return messages[status] || 'An error occurred. Please try again.'
}

// Type-safe wrapper methods with proper request typing
export const api = {
  get<T>(url: string, config?: InternalAxiosRequestConfig) {
    return apiClient.get<T>(url, config)
  },

  post<T, D = Record<string, unknown>>(
    url: string,
    data?: D,
    config?: InternalAxiosRequestConfig
  ) {
    return apiClient.post<T>(url, data, config)
  },

  put<T, D = Record<string, unknown>>(
    url: string,
    data?: D,
    config?: InternalAxiosRequestConfig
  ) {
    return apiClient.put<T>(url, data, config)
  },

  patch<T, D = Record<string, unknown>>(
    url: string,
    data?: D,
    config?: InternalAxiosRequestConfig
  ) {
    return apiClient.patch<T>(url, data, config)
  },

  delete<T>(url: string, config?: InternalAxiosRequestConfig) {
    return apiClient.delete<T>(url, config)
  },
}

export { apiClient }
export type { CustomAxiosError }
