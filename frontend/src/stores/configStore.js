import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiClient } from '../services/apiClient'

export const useConfigStore = defineStore('config', () => {
  // State
  const configuration = ref({})
  const loading = ref(false)
  const error = ref(null)

  // Actions
  async function loadConfiguration() {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/api/config')
      configuration.value = response.data.config || {}
      return configuration.value
    } catch (err) {
      error.value = err.message || 'Failed to load configuration'
      console.error('Failed to load configuration:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function getConfigValue(key) {
    return configuration.value[key]
  }

  function isFeatureEnabled(feature) {
    const value = configuration.value[feature]
    return value === true || value === 'true' || value === 'enabled'
  }

  // Reset state
  function resetConfiguration() {
    configuration.value = {}
    error.value = null
  }

  return {
    // State
    configuration,
    loading,
    error,
    
    // Actions
    loadConfiguration,
    getConfigValue,
    isFeatureEnabled,
    resetConfiguration
  }
})