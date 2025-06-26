/**
 * Campaign Template Store - Manages campaign templates separately
 *
 * This store handles campaign template operations independently from
 * the main campaign store, providing dedicated functionality for:
 * - Loading and managing campaign templates
 * - Creating campaigns from templates
 * - Template CRUD operations
 *
 * @module campaignTemplateStore
 */
import { defineStore } from 'pinia'
import { ref, Ref } from 'vue'
import { apiClient } from '../services/apiClient'
import type {
  CampaignTemplateModel,
  CampaignInstanceModel,
  CreateCampaignFromTemplateRequest,
} from '@/types/unified'

interface TTSOverrides {
  narrationEnabled?: boolean
  ttsVoice?: string
}

export const useCampaignTemplateStore = defineStore('campaignTemplate', () => {
  // State
  const templates: Ref<CampaignTemplateModel[]> = ref([])
  const templatesLoading = ref(false)
  const error: Ref<string | null> = ref(null)

  // Actions
  async function loadTemplates(): Promise<void> {
    templatesLoading.value = true
    error.value = null
    try {
      const response = await apiClient.get<CampaignTemplateModel[]>(
        '/api/campaign_templates'
      )
      templates.value = response.data || []
    } catch (err) {
      console.error('Failed to load campaign templates:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    } finally {
      templatesLoading.value = false
    }
  }

  async function getTemplate(
    templateId: string
  ): Promise<CampaignTemplateModel> {
    try {
      const response = await apiClient.get<CampaignTemplateModel>(
        `/api/campaign_templates/${templateId}`
      )
      return response.data
    } catch (err) {
      console.error('Failed to load campaign template:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    }
  }

  async function createTemplate(
    templateData: Partial<CampaignTemplateModel>
  ): Promise<CampaignTemplateModel> {
    try {
      const response = await apiClient.post<CampaignTemplateModel>(
        '/api/campaign_templates',
        templateData
      )
      templates.value.unshift(response.data)
      return response.data
    } catch (err) {
      console.error('Failed to create campaign template:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    }
  }

  async function updateTemplate(
    templateId: string,
    templateData: Partial<CampaignTemplateModel>
  ): Promise<CampaignTemplateModel> {
    try {
      const response = await apiClient.put<CampaignTemplateModel>(
        `/api/campaign_templates/${templateId}`,
        templateData
      )
      const index = templates.value.findIndex(t => t.id === templateId)
      if (index !== -1) {
        templates.value[index] = response.data
      }
      return response.data
    } catch (err) {
      console.error('Failed to update campaign template:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    }
  }

  async function deleteTemplate(templateId: string): Promise<void> {
    try {
      await apiClient.delete(`/api/campaign_templates/${templateId}`)
      templates.value = templates.value.filter(t => t.id !== templateId)
    } catch (err) {
      console.error('Failed to delete campaign template:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    }
  }

  async function createCampaignFromTemplate(
    templateId: string,
    campaignName: string,
    characterTemplateIds: string[] = [],
    ttsOverrides: TTSOverrides = {}
  ): Promise<CampaignInstanceModel> {
    try {
      const payload: CreateCampaignFromTemplateRequest = {
        campaign_name: campaignName,
        character_ids: characterTemplateIds, // Backend expects 'character_ids', not 'character_template_ids'
      }

      // Add TTS overrides if provided
      if (ttsOverrides.narrationEnabled !== undefined) {
        payload.narration_enabled = ttsOverrides.narrationEnabled
      }
      if (ttsOverrides.ttsVoice !== undefined) {
        payload.tts_voice = ttsOverrides.ttsVoice
      }

      const response = await apiClient.post<{
        campaign: CampaignInstanceModel
      }>(`/api/campaign_templates/${templateId}/create_campaign`, payload)
      return response.data.campaign
    } catch (err) {
      console.error('Failed to create campaign from template:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
      throw err
    }
  }

  return {
    // State
    templates,
    templatesLoading,
    error,

    // Actions
    loadTemplates,
    getTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    createCampaignFromTemplate,
  }
})
