import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiClient } from '../services/apiClient'

export const useCampaignTemplateStore = defineStore('campaignTemplate', () => {
  // State
  const templates = ref([])
  const templatesLoading = ref(false)
  const error = ref(null)

  // Actions
  async function loadTemplates() {
    templatesLoading.value = true
    error.value = null
    try {
      const response = await apiClient.get('/api/campaign_templates')
      templates.value = response.data.campaigns || []
    } catch (err) {
      console.error('Failed to load campaign templates:', err)
      error.value = err.message
      throw err
    } finally {
      templatesLoading.value = false
    }
  }

  async function getTemplate(templateId) {
    try {
      const response = await apiClient.get(`/api/campaign_templates/${templateId}`)
      return response.data
    } catch (err) {
      console.error('Failed to load campaign template:', err)
      error.value = err.message
      throw err
    }
  }

  async function createTemplate(templateData) {
    try {
      const response = await apiClient.post('/api/campaign_templates', templateData)
      templates.value.unshift(response.data)
      return response.data
    } catch (err) {
      console.error('Failed to create campaign template:', err)
      error.value = err.message
      throw err
    }
  }

  async function updateTemplate(templateId, templateData) {
    try {
      const response = await apiClient.put(`/api/campaign_templates/${templateId}`, templateData)
      const index = templates.value.findIndex(t => t.id === templateId)
      if (index !== -1) {
        templates.value[index] = response.data
      }
      return response.data
    } catch (err) {
      console.error('Failed to update campaign template:', err)
      error.value = err.message
      throw err
    }
  }

  async function deleteTemplate(templateId) {
    try {
      await apiClient.delete(`/api/campaign_templates/${templateId}`)
      templates.value = templates.value.filter(t => t.id !== templateId)
    } catch (err) {
      console.error('Failed to delete campaign template:', err)
      error.value = err.message
      throw err
    }
  }

  async function createCampaignFromTemplate(templateId, campaignName, characterTemplateIds = [], ttsOverrides = {}) {
    try {
      const payload = {
        campaign_name: campaignName,
        character_template_ids: characterTemplateIds
      }
      
      // Add TTS overrides if provided
      if (ttsOverrides.narrationEnabled !== undefined) {
        payload.narrationEnabled = ttsOverrides.narrationEnabled
      }
      if (ttsOverrides.ttsVoice !== undefined) {
        payload.ttsVoice = ttsOverrides.ttsVoice
      }
      
      const response = await apiClient.post(`/api/campaign_templates/${templateId}/create_campaign`, payload)
      return response.data.campaign
    } catch (err) {
      console.error('Failed to create campaign from template:', err)
      error.value = err.message
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
    createCampaignFromTemplate
  }
})