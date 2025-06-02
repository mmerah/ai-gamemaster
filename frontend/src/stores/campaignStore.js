import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { campaignApi } from '../services/campaignApi'

export const useCampaignStore = defineStore('campaign', () => {
  // Router instance
  const router = useRouter()
  
  // State
  const campaigns = ref([])
  const templates = ref([])
  const activeCampaign = ref(null)
  const campaignsLoading = ref(false)
  const templatesLoading = ref(false)
  const d5eRaces = ref(null)
  const d5eClasses = ref(null)
  const d5eDataLoading = ref(false)

  // Actions
  async function loadCampaigns() {
    campaignsLoading.value = true
    try {
      // Load campaign instances (ongoing games)
      const response = await campaignApi.getCampaignInstances()
      campaigns.value = response.data.campaigns || []
    } catch (error) {
      console.error('Failed to load campaign instances:', error)
      throw error
    } finally {
      campaignsLoading.value = false
    }
  }

  async function loadTemplates() {
    templatesLoading.value = true
    try {
      const response = await campaignApi.getTemplates()
      templates.value = response.data.templates || []
    } catch (error) {
      console.error('Failed to load templates:', error)
      throw error
    } finally {
      templatesLoading.value = false
    }
  }

  async function createCampaign(campaignData) {
    try {
      const response = await campaignApi.createCampaign(campaignData)
      campaigns.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create campaign:', error)
      throw error
    }
  }

  async function updateCampaign(campaignId, campaignData) {
    try {
      const response = await campaignApi.updateCampaign(campaignId, campaignData)
      const index = campaigns.value.findIndex(c => c.id === campaignId)
      if (index !== -1) {
        campaigns.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to update campaign:', error)
      throw error
    }
  }

  async function deleteCampaign(campaignId) {
    try {
      await campaignApi.deleteCampaign(campaignId)
      campaigns.value = campaigns.value.filter(c => c.id !== campaignId)
    } catch (error) {
      console.error('Failed to delete campaign:', error)
      throw error
    }
  }

  async function createTemplate(templateData) {
    try {
      const response = await campaignApi.createTemplate(templateData)
      templates.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create template:', error)
      throw error
    }
  }

  async function updateTemplate(templateId, templateData) {
    try {
      const response = await campaignApi.updateTemplate(templateId, templateData)
      const index = templates.value.findIndex(t => t.id === templateId)
      if (index !== -1) {
        templates.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to update template:', error)
      throw error
    }
  }

  async function deleteTemplate(templateId) {
    try {
      await campaignApi.deleteTemplate(templateId)
      templates.value = templates.value.filter(t => t.id !== templateId)
    } catch (error) {
      console.error('Failed to delete template:', error)
      throw error
    }
  }

  async function setActiveCampaign(campaignId) {
    try {
      const campaign = campaigns.value.find(c => c.id === campaignId)
      if (campaign) {
        activeCampaign.value = campaign
        // This could also trigger navigation to the game view
        return campaign
      }
      throw new Error('Campaign not found')
    } catch (error) {
      console.error('Failed to set active campaign:', error)
      throw error
    }
  }

  async function startCampaign(campaignId) {
    try {
      // First, start the campaign on the backend to load its game state
      const response = await campaignApi.startCampaign(campaignId)
      
      // Set the active campaign
      await setActiveCampaign(campaignId)
      
      // Navigate to the game view
      router.push({ name: 'game' })
    } catch (error) {
      console.error('Failed to start campaign:', error)
      throw error
    }
  }

  async function getCampaignByIdAsync(campaignId) {
    // First check if we have it locally
    const localCampaign = campaigns.value.find(c => c.id === campaignId)
    if (localCampaign) {
      return localCampaign
    }
    
    // Otherwise fetch it from the API
    try {
      const response = await campaignApi.getCampaign(campaignId)
      const campaign = response.data
      
      // Add it to our local campaigns array
      const index = campaigns.value.findIndex(c => c.id === campaignId)
      if (index === -1) {
        campaigns.value.push(campaign)
      } else {
        campaigns.value[index] = campaign
      }
      
      return campaign
    } catch (error) {
      console.error('Failed to fetch campaign:', error)
      throw error
    }
  }

  // D&D 5e Data helpers
  async function loadD5eRaces() {
    if (d5eRaces.value) {
      return d5eRaces.value
    }
    
    d5eDataLoading.value = true
    try {
      const response = await campaignApi.getD5eRaces()
      d5eRaces.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to load D&D 5e races:', error)
      throw error
    } finally {
      d5eDataLoading.value = false
    }
  }

  async function loadD5eClasses() {
    if (d5eClasses.value) {
      return d5eClasses.value
    }
    
    d5eDataLoading.value = true
    try {
      const response = await campaignApi.getD5eClasses()
      d5eClasses.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to load D&D 5e classes:', error)
      throw error
    } finally {
      d5eDataLoading.value = false
    }
  }

  // Getters
  const getCampaignById = (id) => {
    return campaigns.value.find(campaign => campaign.id === id)
  }

  const getTemplateById = (id) => {
    return templates.value.find(template => template.id === id)
  }

  const getTemplatesByRace = (race) => {
    return templates.value.filter(template => template.race === race)
  }

  const getTemplatesByClass = (characterClass) => {
    return templates.value.filter(template => template.class === characterClass)
  }

  const sortedCampaigns = () => {
    return [...campaigns.value].sort((a, b) => {
      return new Date(b.created_date) - new Date(a.created_date)
    })
  }

  const sortedTemplates = () => {
    return [...templates.value].sort((a, b) => {
      return a.name.localeCompare(b.name)
    })
  }

  // Campaign statistics
  const campaignStats = () => {
    return {
      total: campaigns.value.length,
      active: campaigns.value.filter(c => c.status === 'active').length,
      completed: campaigns.value.filter(c => c.status === 'completed').length,
      paused: campaigns.value.filter(c => c.status === 'paused').length
    }
  }

  // Template statistics
  const templateStats = () => {
    const raceCount = {}
    const classCount = {}
    
    templates.value.forEach(template => {
      raceCount[template.race] = (raceCount[template.race] || 0) + 1
      classCount[template.class] = (classCount[template.class] || 0) + 1
    })

    return {
      total: templates.value.length,
      byRace: raceCount,
      byClass: classCount
    }
  }

  return {
    // State
    campaigns,
    templates,
    activeCampaign,
    campaignsLoading,
    templatesLoading,
    d5eRaces,
    d5eClasses,
    d5eDataLoading,
    
    // Actions
    loadCampaigns,
    loadTemplates,
    createCampaign,
    updateCampaign,
    deleteCampaign,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    setActiveCampaign,
    startCampaign,
    getCampaignByIdAsync,
    loadD5eRaces,
    loadD5eClasses,
    
    // Getters
    getCampaignById,
    getTemplateById,
    getTemplatesByRace,
    getTemplatesByClass,
    sortedCampaigns,
    sortedTemplates,
    campaignStats,
    templateStats
  }
})
