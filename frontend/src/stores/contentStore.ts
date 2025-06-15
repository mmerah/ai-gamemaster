import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { contentApi } from '../services/contentApi'
import type { 
  ContentPack, 
  ContentPackCreate, 
  ContentPackUpdate, 
  ContentPackWithStats,
  ContentUploadResult,
  ContentType 
} from '../types/content'

export const useContentStore = defineStore('content', () => {
  // State
  const contentPacks = ref<ContentPack[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const supportedTypes = ref<string[]>([])

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
      contentPacks.value = response.packs
    } catch (err: any) {
      error.value = err.userMessage || err.response?.data?.message || 'Failed to load content packs'
      console.error('Error loading content packs:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadSupportedTypes() {
    try {
      supportedTypes.value = await contentApi.getSupportedTypes()
    } catch (err) {
      console.error('Error loading supported types:', err)
      // Use default types if API fails
      supportedTypes.value = [
        'spells', 'monsters', 'equipment', 'classes', 'races',
        'backgrounds', 'feats', 'features', 'magic_items'
      ]
    }
  }

  async function getPackStatistics(packId: string): Promise<ContentPackWithStats | null> {
    try {
      return await contentApi.getContentPackStatistics(packId)
    } catch (err) {
      console.error('Error getting pack statistics:', err)
      return null
    }
  }

  async function createPack(data: ContentPackCreate): Promise<ContentPack | null> {
    try {
      const newPack = await contentApi.createPack(data)
      contentPacks.value.push(newPack)
      return newPack
    } catch (err: any) {
      error.value = err.userMessage || err.response?.data?.message || 'Failed to create content pack'
      console.error('Error creating pack:', err)
      return null
    }
  }

  async function updatePack(packId: string, data: ContentPackUpdate): Promise<ContentPack | null> {
    try {
      const updatedPack = await contentApi.updatePack(packId, data)
      const index = contentPacks.value.findIndex(p => p.id === packId)
      if (index !== -1) {
        contentPacks.value[index] = updatedPack
      }
      return updatedPack
    } catch (err: any) {
      error.value = err.userMessage || err.response?.data?.message || 'Failed to update content pack'
      console.error('Error updating pack:', err)
      return null
    }
  }

  async function activatePack(packId: string): Promise<boolean> {
    try {
      const updatedPack = await contentApi.activatePack(packId)
      const index = contentPacks.value.findIndex(p => p.id === packId)
      if (index !== -1) {
        contentPacks.value[index] = updatedPack
      }
      return true
    } catch (err: any) {
      error.value = err.userMessage || err.response?.data?.message || 'Failed to activate content pack'
      console.error('Error activating pack:', err)
      return false
    }
  }

  async function deactivatePack(packId: string): Promise<boolean> {
    try {
      const updatedPack = await contentApi.deactivatePack(packId)
      const index = contentPacks.value.findIndex(p => p.id === packId)
      if (index !== -1) {
        contentPacks.value[index] = updatedPack
      }
      return true
    } catch (err: any) {
      error.value = err.userMessage || err.response?.data?.message || 'Failed to deactivate content pack'
      console.error('Error deactivating pack:', err)
      return false
    }
  }

  async function deletePack(packId: string): Promise<boolean> {
    try {
      await contentApi.deletePack(packId)
      contentPacks.value = contentPacks.value.filter(p => p.id !== packId)
      return true
    } catch (err: any) {
      error.value = err.userMessage || err.response?.data?.message || 'Failed to delete content pack'
      console.error('Error deleting pack:', err)
      return false
    }
  }

  async function uploadContent(
    packId: string, 
    contentType: ContentType, 
    content: any
  ): Promise<ContentUploadResult | null> {
    try {
      return await contentApi.uploadContent(packId, contentType, content)
    } catch (err: any) {
      error.value = err.userMessage || err.response?.data?.message || 'Failed to upload content'
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
    clearError
  }
})