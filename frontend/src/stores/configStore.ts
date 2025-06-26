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
import type { Settings } from '@/types/unified'
import { getErrorMessage } from '@/utils/errorHelpers'

export const useConfigStore = defineStore('config', () => {
  // State
  const configuration: Ref<Settings | null> = ref(null)
  const loading = ref(false)
  const error: Ref<string | null> = ref(null)

  // Actions
  async function loadConfiguration(): Promise<Settings | null> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get<Settings>('/api/config')
      configuration.value = response.data
      return configuration.value
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      console.error('Failed to load configuration:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function getConfigValue<K extends keyof Settings>(
    key: K
  ): Settings[K] | undefined {
    return configuration.value?.[key]
  }

  function isFeatureEnabled(feature: string): boolean {
    if (!configuration.value) return false

    // Check in nested settings objects for boolean flags
    // Use unknown first for safe type assertion
    const settings = configuration.value as unknown as Record<string, unknown>
    const value = settings[feature]
    return value === true || value === 'true' || value === 'enabled'
  }

  // Reset state
  function resetConfiguration(): void {
    configuration.value = null
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
    resetConfiguration,
  }
})
