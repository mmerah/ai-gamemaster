import { apiClient } from './apiClient'

export const campaignApi = {
  // Campaigns
  async getCampaigns() {
    return apiClient.get('/api/campaigns')
  },

  async getCampaign(id) {
    return apiClient.get(`/api/campaigns/${id}`)
  },

  async createCampaign(campaignData) {
    return apiClient.post('/api/campaigns', campaignData)
  },

  async updateCampaign(id, campaignData) {
    return apiClient.put(`/api/campaigns/${id}`, campaignData)
  },

  async deleteCampaign(id) {
    return apiClient.delete(`/api/campaigns/${id}`)
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

  async getD5eSpells() {
    return apiClient.get('/api/d5e/spells')
  },

  async getD5eEquipment() {
    return apiClient.get('/api/d5e/equipment')
  }
}
