import axios from 'axios'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add timestamp to prevent caching for certain requests
    if (config.method === 'get' && config.url.includes('/poll')) {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle common error scenarios
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
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
          console.error('Resource not found:', error.config.url)
          break
        case 422:
          // Validation error
          console.error('Validation error:', data.errors || data.message)
          break
        case 500:
          // Server error
          console.error('Server error:', data.message || 'Internal server error')
          break
        default:
          console.error('API Error:', data.message || `HTTP ${status}`)
      }
      
      // Add user-friendly error message
      error.userMessage = data.message || getDefaultErrorMessage(status)
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

function getDefaultErrorMessage(status) {
  const messages = {
    400: 'Bad request. Please check your input.',
    401: 'Please log in to continue.',
    403: 'You do not have permission to perform this action.',
    404: 'The requested resource was not found.',
    422: 'Invalid data provided.',
    500: 'Server error. Please try again later.',
    502: 'Service temporarily unavailable.',
    503: 'Service temporarily unavailable.',
    504: 'Request timeout. Please try again.'
  }
  
  return messages[status] || 'An error occurred. Please try again.'
}

export { apiClient }
