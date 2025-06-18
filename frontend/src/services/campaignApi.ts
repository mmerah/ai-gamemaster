import { apiClient } from './apiClient'
import type { AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types/api'
import type {
  CampaignTemplateModel,
  CampaignInstanceModel,
  CharacterTemplateModel,
  GameStateModel,
  D5eRace,
  D5eClass,
  D5eBackground,
  D5eAlignment,
  D5eLanguage,
  D5eSkill,
  D5eAbilityScore
} from '@/types/unified'

// Request Types
interface CreateCampaignFromTemplateRequest {
  campaign_name: string
  character_template_ids: string[]
  narrationEnabled?: boolean
  ttsVoice?: string
}

// Response Types
interface CampaignInstancesResponse {
  campaigns: CampaignInstanceModel[]
}

interface CampaignTemplatesResponse {
  campaigns: CampaignTemplateModel[]
}

interface CharacterTemplatesResponse {
  templates: CharacterTemplateModel[]
}

interface CreateCampaignResponse {
  campaign: CampaignInstanceModel
}

interface D5eRacesResponse {
  races: Record<string, D5eRace>
}

interface D5eClassesResponse {
  classes: Record<string, D5eClass>
}

interface CharacterCreationOptionsResponse {
  options: {
    races: D5eRace[]
    classes: D5eClass[]
    backgrounds: D5eBackground[]
    alignments: D5eAlignment[]
    languages: D5eLanguage[]
    skills: D5eSkill[]
    ability_scores: D5eAbilityScore[]
  }
  metadata: {
    content_pack_ids: string[]
    total_races: number
    total_classes: number
    total_backgrounds: number
  }
}

export const campaignApi = {
  // Campaign Instances (ongoing games)
  async getCampaignInstances(): Promise<AxiosResponse<CampaignInstancesResponse>> {
    return apiClient.get<CampaignInstancesResponse>('/api/campaign-instances')
  },

  // Campaign Templates - use the proper endpoints
  async getCampaigns(): Promise<AxiosResponse<CampaignTemplatesResponse>> {
    return apiClient.get<CampaignTemplatesResponse>('/api/campaign_templates')
  },

  async getCampaign(id: string): Promise<AxiosResponse<CampaignTemplateModel>> {
    return apiClient.get<CampaignTemplateModel>(`/api/campaign_templates/${id}`)
  },

  async createCampaign(campaignData: Partial<CampaignTemplateModel>): Promise<AxiosResponse<CampaignTemplateModel>> {
    return apiClient.post<CampaignTemplateModel>('/api/campaign_templates', campaignData)
  },

  async updateCampaign(id: string, campaignData: Partial<CampaignTemplateModel>): Promise<AxiosResponse<CampaignTemplateModel>> {
    return apiClient.put<CampaignTemplateModel>(`/api/campaign_templates/${id}`, campaignData)
  },

  async deleteCampaign(id: string): Promise<AxiosResponse<void>> {
    return apiClient.delete<void>(`/api/campaign_templates/${id}`)
  },

  async startCampaign(id: string): Promise<AxiosResponse<ApiResponse<GameStateModel>>> {
    return apiClient.post<ApiResponse<GameStateModel>>(`/api/campaigns/${id}/start`)
  },

  // Character Templates
  async getTemplates(): Promise<AxiosResponse<CharacterTemplatesResponse>> {
    return apiClient.get<CharacterTemplatesResponse>('/api/character_templates')
  },

  async getTemplate(id: string): Promise<AxiosResponse<CharacterTemplateModel>> {
    return apiClient.get<CharacterTemplateModel>(`/api/character_templates/${id}`)
  },

  async createTemplate(templateData: Partial<CharacterTemplateModel>): Promise<AxiosResponse<CharacterTemplateModel>> {
    return apiClient.post<CharacterTemplateModel>('/api/character_templates', templateData)
  },

  async updateTemplate(id: string, templateData: Partial<CharacterTemplateModel>): Promise<AxiosResponse<CharacterTemplateModel>> {
    return apiClient.put<CharacterTemplateModel>(`/api/character_templates/${id}`, templateData)
  },

  async deleteTemplate(id: string): Promise<AxiosResponse<void>> {
    return apiClient.delete<void>(`/api/character_templates/${id}`)
  },

  // D&D 5e Data
  async getD5eRaces(): Promise<AxiosResponse<D5eRacesResponse>> {
    const response = await apiClient.get<D5eRace[]>('/api/d5e/content?type=races')
    // Convert array to object format expected by frontend
    const races: Record<string, D5eRace> = {}
    response.data.forEach((race: D5eRace) => {
      races[race.index] = race
    })
    return {
      ...response,
      data: { races }
    }
  },

  async getD5eClasses(): Promise<AxiosResponse<D5eClassesResponse>> {
    const response = await apiClient.get<D5eClass[]>('/api/d5e/content?type=classes')
    // Convert array to object format expected by frontend
    const classes: Record<string, D5eClass> = {}
    response.data.forEach((clazz: D5eClass) => {
      classes[clazz.index] = clazz
    })
    return {
      ...response,
      data: { classes }
    }
  },

  // Character Creation Options with content pack filtering
  async getCharacterCreationOptions(params?: {
    contentPackIds?: string[]
    campaignId?: string
  }): Promise<AxiosResponse<CharacterCreationOptionsResponse>> {
    const queryParams = new URLSearchParams()
    
    if (params?.contentPackIds && params.contentPackIds.length > 0) {
      queryParams.append('content_pack_ids', params.contentPackIds.join(','))
    }
    
    if (params?.campaignId) {
      queryParams.append('campaign_id', params.campaignId)
    }
    
    const url = `/api/character_templates/options${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get<CharacterCreationOptionsResponse>(url)
  },

  // Create campaign from template
  async createCampaignFromTemplate(
    templateId: string,
    data: CreateCampaignFromTemplateRequest
  ): Promise<AxiosResponse<CreateCampaignResponse>> {
    const payload = {
      campaign_name: data.campaign_name,
      character_template_ids: data.character_template_ids,
      narrationEnabled: data.narrationEnabled,
      ttsVoice: data.ttsVoice
    }

    return apiClient.post<CreateCampaignResponse>(
      `/api/campaign_templates/${templateId}/create_campaign`,
      payload
    )
  }
}
