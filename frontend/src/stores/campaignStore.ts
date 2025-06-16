/**
 * Campaign Store - Manages campaign instances and templates
 *
 * This store handles:
 * - Campaign instances (active games)
 * - Campaign templates (starter templates)
 * - D&D 5e reference data (races, classes)
 * - Campaign lifecycle operations
 *
 * @module campaignStore
 */
import { defineStore } from 'pinia'
import { ref, Ref } from 'vue'
import { useRouter } from 'vue-router'
import { campaignApi } from '../services/campaignApi'
import type {
  CampaignInstanceModel,
  CampaignTemplateModel
} from '@/types/unified'

// D&D 5e data types
interface D5eRaceData {
  [key: string]: any
}

interface D5eClassData {
  [key: string]: any
}

interface CharacterCreationOptions {
  races: any[]
  classes: any[]
  backgrounds: any[]
  alignments: any[]
  languages: any[]
  skills: any[]
  ability_scores: any[]
}

export const useCampaignStore = defineStore('campaign', () => {
  // Router instance
  const router = useRouter()

  // State
  const campaigns: Ref<CampaignInstanceModel[]> = ref([])
  const templates: Ref<CampaignTemplateModel[]> = ref([])
  const activeCampaign: Ref<CampaignInstanceModel | null> = ref(null)
  const campaignsLoading = ref(false)
  const templatesLoading = ref(false)
  const d5eRaces: Ref<D5eRaceData | null> = ref(null)
  const d5eClasses: Ref<D5eClassData | null> = ref(null)
  const d5eDataLoading = ref(false)
  const characterCreationOptions: Ref<CharacterCreationOptions | null> = ref(null)

  // Actions
  async function loadCampaigns(): Promise<void> {
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

  async function loadTemplates(): Promise<void> {
    templatesLoading.value = true
    try {
      const response = await campaignApi.getCampaigns()
      templates.value = response.data.campaigns || []
    } catch (error) {
      console.error('Failed to load templates:', error)
      throw error
    } finally {
      templatesLoading.value = false
    }
  }

  async function createCampaign(campaignData: Partial<CampaignInstanceModel>): Promise<CampaignInstanceModel> {
    try {
      const response = await campaignApi.createCampaign(campaignData as Partial<CampaignTemplateModel>)
      const campaign = response.data as unknown as CampaignInstanceModel
      campaigns.value.unshift(campaign)
      return campaign
    } catch (error) {
      console.error('Failed to create campaign:', error)
      throw error
    }
  }

  async function updateCampaign(campaignId: string, campaignData: Partial<CampaignInstanceModel>): Promise<CampaignInstanceModel> {
    try {
      const response = await campaignApi.updateCampaign(campaignId, campaignData as Partial<CampaignTemplateModel>)
      const campaign = response.data as unknown as CampaignInstanceModel
      const index = campaigns.value.findIndex(c => c.id === campaignId)
      if (index !== -1) {
        campaigns.value[index] = campaign
      }
      return campaign
    } catch (error) {
      console.error('Failed to update campaign:', error)
      throw error
    }
  }

  async function deleteCampaign(campaignId: string): Promise<void> {
    try {
      await campaignApi.deleteCampaign(campaignId)
      campaigns.value = campaigns.value.filter(c => c.id !== campaignId)
    } catch (error) {
      console.error('Failed to delete campaign:', error)
      throw error
    }
  }

  async function createTemplate(templateData: Partial<CampaignTemplateModel>): Promise<CampaignTemplateModel> {
    try {
      const response = await campaignApi.createCampaign(templateData)
      templates.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create template:', error)
      throw error
    }
  }

  async function updateTemplate(templateId: string, templateData: Partial<CampaignTemplateModel>): Promise<CampaignTemplateModel> {
    try {
      const response = await campaignApi.updateCampaign(templateId, templateData)
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

  async function deleteTemplate(templateId: string): Promise<void> {
    try {
      await campaignApi.deleteCampaign(templateId)
      templates.value = templates.value.filter(t => t.id !== templateId)
    } catch (error) {
      console.error('Failed to delete template:', error)
      throw error
    }
  }

  async function setActiveCampaign(campaignId: string): Promise<CampaignInstanceModel> {
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

  async function startCampaign(campaignId: string): Promise<void> {
    try {
      // First, start the campaign on the backend to load its game state
      await campaignApi.startCampaign(campaignId)

      // Set the active campaign
      await setActiveCampaign(campaignId)

      // Navigate to the game view
      router.push({ name: 'game' })
    } catch (error) {
      console.error('Failed to start campaign:', error)
      throw error
    }
  }

  async function getCampaignByIdAsync(campaignId: string): Promise<CampaignInstanceModel> {
    // First check if we have it locally
    const localCampaign = campaigns.value.find(c => c.id === campaignId)
    if (localCampaign) {
      return localCampaign
    }

    // Otherwise fetch it from the API
    try {
      const response = await campaignApi.getCampaign(campaignId)
      const campaign = response.data as unknown as CampaignInstanceModel

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
  async function loadD5eRaces(): Promise<D5eRaceData> {
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

  async function loadD5eClasses(): Promise<D5eClassData> {
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

  // Load character creation options with content pack filtering
  async function loadCharacterCreationOptions(params?: {
    contentPackIds?: string[]
    campaignId?: string
  }): Promise<CharacterCreationOptions> {
    d5eDataLoading.value = true
    try {
      const response = await campaignApi.getCharacterCreationOptions(params)
      const options = response.data.options
      
      // Store the options
      characterCreationOptions.value = options
      
      // Also convert to the legacy format for backward compatibility
      // Convert array of races to the object format expected by useD5eData
      if (options.races && options.races.length > 0) {
        const racesObject: D5eRaceData = {}
        options.races.forEach((race: any) => {
          const key = race.index || race.name.toLowerCase().replace(/\s+/g, '-')
          racesObject[key] = race
        })
        d5eRaces.value = { races: racesObject }
      }
      
      // Convert array of classes to the object format expected by useD5eData
      if (options.classes && options.classes.length > 0) {
        const classesObject: D5eClassData = {}
        options.classes.forEach((cls: any) => {
          const key = cls.index || cls.name.toLowerCase().replace(/\s+/g, '-')
          classesObject[key] = cls
        })
        d5eClasses.value = { classes: classesObject }
      }
      
      return options
    } catch (error) {
      console.error('Failed to load character creation options:', error)
      throw error
    } finally {
      d5eDataLoading.value = false
    }
  }

  // Getters
  function getCampaignById(id: string): CampaignInstanceModel | undefined {
    return campaigns.value.find(campaign => campaign.id === id)
  }

  function getTemplateById(id: string): CampaignTemplateModel | undefined {
    return templates.value.find(template => template.id === id)
  }

  // Note: Campaign templates don't have race/class - those are character template properties
  // Keeping these for backward compatibility but they will return empty arrays
  function getTemplatesByRace(_race: string): CampaignTemplateModel[] {
    return []
  }

  function getTemplatesByClass(_characterClass: string): CampaignTemplateModel[] {
    return []
  }

  function sortedCampaigns(): CampaignInstanceModel[] {
    return [...campaigns.value].sort((a, b) => {
      const dateA = new Date(a.created_date || 0).getTime()
      const dateB = new Date(b.created_date || 0).getTime()
      return dateB - dateA
    })
  }

  function sortedTemplates(): CampaignTemplateModel[] {
    return [...templates.value].sort((a, b) => {
      return a.name.localeCompare(b.name)
    })
  }

  // Campaign statistics
  interface CampaignStats {
    total: number
    active: number
    completed: number
    paused: number
  }

  function campaignStats(): CampaignStats {
    return {
      total: campaigns.value.length,
      active: campaigns.value.filter(c => (c as any).status === 'active').length,
      completed: campaigns.value.filter(c => (c as any).status === 'completed').length,
      paused: campaigns.value.filter(c => (c as any).status === 'paused').length
    }
  }

  // Template statistics
  interface TemplateStats {
    total: number
    byRace: Record<string, number>
    byClass: Record<string, number>
  }

  function templateStats(): TemplateStats {
    const raceCount: Record<string, number> = {}
    const classCount: Record<string, number> = {}

    // Campaign templates don't have race/class properties
    // Those belong to character templates

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
    characterCreationOptions,

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
    loadCharacterCreationOptions,

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
