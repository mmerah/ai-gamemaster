import { apiClient } from './apiClient'

export const campaignApi = {
  // Campaign Instances (ongoing games)
  async getCampaignInstances() {
    return apiClient.get('/api/campaign-instances')
  },

  // Campaign Templates - use the proper endpoints
  async getCampaigns() {
    return apiClient.get('/api/campaign_templates')
  },

  async getCampaign(id) {
    return apiClient.get(`/api/campaign_templates/${id}`)
  },

  async createCampaign(campaignData) {
    return apiClient.post('/api/campaign_templates', campaignData)
  },

  async updateCampaign(id, campaignData) {
    return apiClient.put(`/api/campaign_templates/${id}`, campaignData)
  },

  async deleteCampaign(id) {
    return apiClient.delete(`/api/campaign_templates/${id}`)
  },

  async startCampaign(id) {
    return apiClient.post(`/api/campaigns/${id}/start`)
  },

  // Templates
  async getTemplates() {
    return apiClient.get('/api/character_templates')
  },

  async getTemplate(id) {
    return apiClient.get(`/api/character_templates/${id}`)
  },

  async createTemplate(templateData) {
    return apiClient.post('/api/character_templates', templateData)
  },

  async updateTemplate(id, templateData) {
    return apiClient.put(`/api/character_templates/${id}`, templateData)
  },

  async deleteTemplate(id) {
    return apiClient.delete(`/api/character_templates/${id}`)
  },

  // D&D 5e Data
  async getD5eRaces() {
    return apiClient.get('/api/d5e/races')
  },

  async getD5eClasses() {
    return apiClient.get('/api/d5e/classes')
  },

}
