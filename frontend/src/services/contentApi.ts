import { apiClient } from './apiClient'
import type { AxiosResponse } from 'axios'
import type { 
  D5eContentPack,
  ContentPackWithStatisticsResponse,
  ContentUploadResponse,
  ContentType
} from '@/types/unified'
import type { 
  ContentPackCreate, 
  ContentPackUpdate,
  ContentTypeInfo
} from '../types/content'

export const contentApi = {
  // Get all content packs
  async getContentPacks(activeOnly: boolean = false): Promise<AxiosResponse<D5eContentPack[]>> {
    const params = activeOnly ? { active_only: 'true' } : {}
    return apiClient.get<D5eContentPack[]>('/api/content/packs', { params })
  },

  // Get a specific content pack
  async getContentPack(packId: string): Promise<AxiosResponse<D5eContentPack>> {
    return apiClient.get<D5eContentPack>(`/api/content/packs/${packId}`)
  },

  // Get content pack statistics
  async getContentPackStatistics(packId: string): Promise<AxiosResponse<ContentPackWithStatisticsResponse>> {
    return apiClient.get<ContentPackWithStatisticsResponse>(`/api/content/packs/${packId}/statistics`)
  },

  // Create a new content pack
  async createPack(data: ContentPackCreate): Promise<AxiosResponse<D5eContentPack>> {
    return apiClient.post<D5eContentPack>('/api/content/packs', data)
  },

  // Update an existing content pack
  async updatePack(packId: string, data: ContentPackUpdate): Promise<AxiosResponse<D5eContentPack>> {
    return apiClient.put<D5eContentPack>(`/api/content/packs/${packId}`, data)
  },

  // Activate a content pack
  async activatePack(packId: string): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return apiClient.post<{ success: boolean; message: string }>(`/api/content/packs/${packId}/activate`)
  },

  // Deactivate a content pack
  async deactivatePack(packId: string): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return apiClient.post<{ success: boolean; message: string }>(`/api/content/packs/${packId}/deactivate`)
  },

  // Delete a content pack
  async deletePack(packId: string): Promise<AxiosResponse<void>> {
    return apiClient.delete<void>(`/api/content/packs/${packId}`)
  },

  // Upload content to a pack
  async uploadContent(
    packId: string, 
    contentType: ContentType, 
    content: unknown  // Content structure varies by type
  ): Promise<AxiosResponse<ContentUploadResponse>> {
    return apiClient.post<ContentUploadResponse>(
      `/api/content/packs/${packId}/upload/${contentType}`,
      content
    )
  },

  // Get supported content types
  async getSupportedTypes(): Promise<AxiosResponse<ContentTypeInfo[]>> {
    return apiClient.get<ContentTypeInfo[]>('/api/content/supported-types')
  },

  // Get content items from a pack
  async getPackContent(
    packId: string, 
    contentType?: string,
    offset: number = 0,
    limit: number = 50
  ): Promise<AxiosResponse<{
    items: unknown[] | Record<string, unknown[]>
    total?: number
    totals?: Record<string, number>
    content_type: string
    offset: number
    limit: number
  }>> {
    const params: Record<string, string | number> = { offset, limit }
    if (contentType) {
      params.content_type = contentType
    }
    
    return apiClient.get(`/api/content/packs/${packId}/content`, { params })
  }
}