import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { contentApi } from '../services/contentApi'
import type {
  D5eContentPack,
  ContentPackWithStatisticsResponse,
  ContentUploadResponse,
  ContentType,
} from '@/types/unified'
import type {
  ContentPackCreate,
  ContentPackUpdate,
  ContentTypeInfo,
} from '../types/content'
import { getAPIErrorMessage } from '@/utils/errorHelpers'

export const useContentStore = defineStore('content', () => {
  // State
  const contentPacks = ref<D5eContentPack[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const supportedTypes = ref<ContentTypeInfo[]>([])

  // Getters
  const activePacks = computed(() =>
    contentPacks.value.filter(pack => pack.is_active)
  )

  const userPacks = computed(() =>
    contentPacks.value.filter(pack => pack.id !== 'dnd_5e_srd')
  )

  const systemPack = computed(() =>
    contentPacks.value.find(pack => pack.id === 'dnd_5e_srd')
  )

  const packCount = computed(() => contentPacks.value.length)

  // Actions
  async function loadContentPacks(activeOnly: boolean = false) {
    loading.value = true
    error.value = null

    try {
      const response = await contentApi.getContentPacks(activeOnly)
      contentPacks.value = response.data
    } catch (err) {
      error.value = getAPIErrorMessage(err, 'Failed to load content packs')
      console.error('Error loading content packs:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadSupportedTypes() {
    try {
      const response = await contentApi.getSupportedTypes()
      supportedTypes.value = response.data
    } catch (err) {
      console.error('Error loading supported types:', err)
      // Use default types if API fails
      supportedTypes.value = [
        { type_id: 'spells', display_name: 'Spells' },
        { type_id: 'monsters', display_name: 'Monsters' },
        { type_id: 'equipment', display_name: 'Equipment' },
        { type_id: 'classes', display_name: 'Classes' },
        { type_id: 'races', display_name: 'Races' },
        { type_id: 'backgrounds', display_name: 'Backgrounds' },
        { type_id: 'feats', display_name: 'Feats' },
        { type_id: 'features', display_name: 'Features' },
        { type_id: 'magic_items', display_name: 'Magic Items' },
      ]
    }
  }

  async function getPackStatistics(
    packId: string
  ): Promise<ContentPackWithStatisticsResponse | null> {
    try {
      const response = await contentApi.getContentPackStatistics(packId)
      return response.data
    } catch (err) {
      console.error('Error getting pack statistics:', err)
      return null
    }
  }

  async function createPack(
    data: ContentPackCreate
  ): Promise<D5eContentPack | null> {
    try {
      const response = await contentApi.createPack(data)
      contentPacks.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = getAPIErrorMessage(err, 'Failed to create content pack')
      console.error('Error creating pack:', err)
      return null
    }
  }

  async function updatePack(
    packId: string,
    data: ContentPackUpdate
  ): Promise<D5eContentPack | null> {
    try {
      const response = await contentApi.updatePack(packId, data)
      const index = contentPacks.value.findIndex(p => p.id === packId)
      if (index !== -1) {
        contentPacks.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = getAPIErrorMessage(err, 'Failed to update content pack')
      console.error('Error updating pack:', err)
      return null
    }
  }

  async function activatePack(packId: string): Promise<boolean> {
    try {
      const response = await contentApi.activatePack(packId)
      if (response.data.success) {
        // Update the pack's active status locally
        const index = contentPacks.value.findIndex(p => p.id === packId)
        if (index !== -1 && contentPacks.value[index]) {
          contentPacks.value[index].is_active = true
        }
      }
      return response.data.success
    } catch (err) {
      error.value = getAPIErrorMessage(err, 'Failed to activate content pack')
      console.error('Error activating pack:', err)
      return false
    }
  }

  async function deactivatePack(packId: string): Promise<boolean> {
    try {
      const response = await contentApi.deactivatePack(packId)
      if (response.data.success) {
        // Update the pack's active status locally
        const index = contentPacks.value.findIndex(p => p.id === packId)
        if (index !== -1 && contentPacks.value[index]) {
          contentPacks.value[index].is_active = false
        }
      }
      return response.data.success
    } catch (err) {
      error.value = getAPIErrorMessage(err, 'Failed to deactivate content pack')
      console.error('Error deactivating pack:', err)
      return false
    }
  }

  async function deletePack(packId: string): Promise<boolean> {
    try {
      await contentApi.deletePack(packId)
      contentPacks.value = contentPacks.value.filter(p => p.id !== packId)
      return true
    } catch (err) {
      error.value = getAPIErrorMessage(err, 'Failed to delete content pack')
      console.error('Error deleting pack:', err)
      return false
    }
  }

  async function uploadContent(
    packId: string,
    contentType: ContentType,
    content: unknown // Content structure varies by type
  ): Promise<ContentUploadResponse | null> {
    try {
      const response = await contentApi.uploadContent(
        packId,
        contentType,
        content
      )
      return response.data
    } catch (err) {
      error.value = getAPIErrorMessage(err, 'Failed to upload content')
      console.error('Error uploading content:', err)
      return null
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    contentPacks,
    loading,
    error,
    supportedTypes,

    // Getters
    activePacks,
    userPacks,
    systemPack,
    packCount,

    // Actions
    loadContentPacks,
    loadSupportedTypes,
    getPackStatistics,
    createPack,
    updatePack,
    activatePack,
    deactivatePack,
    deletePack,
    uploadContent,
    clearError,
  }
})
