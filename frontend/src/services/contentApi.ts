import { apiClient } from './apiClient'
import type { 
  ContentPack, 
  ContentPackCreate, 
  ContentPackUpdate, 
  ContentPackWithStats,
  ContentUploadResult,
  ContentType 
} from '../types/content'

interface ContentPacksResponse {
  packs: ContentPack[]
}

interface SupportedTypesResponse {
  types: string[]
}

class ContentApi {
  // Get all content packs
  async getContentPacks(activeOnly: boolean = false): Promise<ContentPacksResponse> {
    const params = activeOnly ? { active_only: 'true' } : {}
    const response = await apiClient.get('/api/content/packs', { params })
    return response.data
  }

  // Get a specific content pack
  async getContentPack(packId: string): Promise<ContentPack> {
    const response = await apiClient.get(`/api/content/packs/${packId}`)
    return response.data
  }

  // Get content pack statistics
  async getContentPackStatistics(packId: string): Promise<ContentPackWithStats> {
    const response = await apiClient.get(`/api/content/packs/${packId}/statistics`)
    return response.data
  }

  // Create a new content pack
  async createPack(data: ContentPackCreate): Promise<ContentPack> {
    const response = await apiClient.post('/api/content/packs', data)
    return response.data
  }

  // Update an existing content pack
  async updatePack(packId: string, data: ContentPackUpdate): Promise<ContentPack> {
    const response = await apiClient.put(`/api/content/packs/${packId}`, data)
    return response.data
  }

  // Activate a content pack
  async activatePack(packId: string): Promise<ContentPack> {
    const response = await apiClient.post(`/api/content/packs/${packId}/activate`)
    return response.data
  }

  // Deactivate a content pack
  async deactivatePack(packId: string): Promise<ContentPack> {
    const response = await apiClient.post(`/api/content/packs/${packId}/deactivate`)
    return response.data
  }

  // Delete a content pack
  async deletePack(packId: string): Promise<void> {
    await apiClient.delete(`/api/content/packs/${packId}`)
  }

  // Upload content to a pack
  async uploadContent(
    packId: string, 
    contentType: ContentType, 
    content: any
  ): Promise<ContentUploadResult> {
    const response = await apiClient.post(
      `/api/content/packs/${packId}/upload/${contentType}`,
      content
    )
    return response.data
  }

  // Get supported content types
  async getSupportedTypes(): Promise<string[]> {
    const response = await apiClient.get('/api/content/supported-types')
    return response.data.types
  }
}

export const contentApi = new ContentApi()