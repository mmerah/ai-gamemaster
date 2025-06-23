/**
 * Config Store - Manages application configuration
 *
 * This store handles loading and accessing application configuration
 * from the backend, including feature flags and settings.
 *
 * @module configStore
 */
import { defineStore } from 'pinia'
import { ref, Ref } from 'vue'
import { apiClient } from '../services/apiClient'

interface Configuration {
  [key: string]: any
}

export const useConfigStore = defineStore('config', () => {
  // State
  const configuration: Ref<Configuration> = ref({})
  const loading = ref(false)
  const error: Ref<string | null> = ref(null)

  // Actions
  async function loadConfiguration(): Promise<Configuration> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get('/api/config')
      configuration.value = response.data || {}
      return configuration.value
    } catch (err: any) {
      error.value = err.message || 'Failed to load configuration'
      console.error('Failed to load configuration:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function getConfigValue(key: string): any {
    return configuration.value[key]
  }

  function isFeatureEnabled(feature: string): boolean {
    const value = configuration.value[feature]
    return value === true || value === 'true' || value === 'enabled'
  }

  // Reset state
  function resetConfiguration(): void {
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
