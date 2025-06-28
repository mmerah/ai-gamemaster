<template>
  <div class="campaign-manager-view min-h-screen bg-background">
    <!-- Header -->
    <div class="bg-primary text-primary-foreground p-6">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-cinzel font-bold text-accent">
            Campaign Manager
          </h1>
          <p class="text-primary-foreground/80 mt-2">
            Manage your campaigns and adventures
          </p>
        </div>
        <AppButton variant="secondary" @click="$router.push('/')">
          <svg
            class="w-5 h-5 inline mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Back to Launch
        </AppButton>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto p-6">
      <!-- Ongoing Campaigns Section -->
      <div class="mb-12">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-cinzel font-semibold text-foreground">
            Ongoing Campaigns
          </h2>
          <AppButton variant="primary" @click="showCreateCampaignModal = true">
            <svg
              class="w-5 h-5 mr-2 inline"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create New Campaign
          </AppButton>
        </div>

        <!-- Campaigns Grid -->
        <CampaignGrid
          :campaigns="campaigns"
          :loading="campaignsLoading"
          @edit="editCampaign"
          @delete="deleteCampaign"
          @play="playCampaign"
        />
      </div>

      <!-- Campaign Templates Section -->
      <div>
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-cinzel font-semibold text-foreground">
            Campaign Templates
          </h2>
          <AppButton
            variant="secondary"
            @click="showCreateTemplateModal = true"
          >
            <svg
              class="w-5 h-5 mr-2 inline"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create Template
          </AppButton>
        </div>

        <!-- Campaign Templates Grid -->
        <CampaignTemplateGrid
          :templates="campaignTemplates"
          :loading="templatesLoading"
          @use="useCampaignTemplate"
          @edit="editCampaignTemplate"
          @delete="deleteCampaignTemplate"
        />
      </div>
    </div>

    <!-- Modals -->
    <CampaignModal
      v-if="showCreateCampaignModal"
      :visible="showCreateCampaignModal"
      :campaign="editingCampaign"
      @close="closeCampaignModal"
      @save="saveCampaign"
    />

    <CampaignTemplateModal
      v-if="showCreateTemplateModal"
      :visible="showCreateTemplateModal"
      :template="editingTemplate"
      @close="closeTemplateModal"
      @save="saveTemplate"
    />

    <CampaignFromTemplateModal
      v-if="showCreateFromTemplateModal"
      :visible="showCreateFromTemplateModal"
      :template="selectedTemplateForCampaign"
      @close="closeCreateFromTemplateModal"
      @create="createCampaignFromTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, Ref } from 'vue'
import { useCampaignStore } from '../stores/campaignStore'
import { useCampaignTemplateStore } from '../stores/campaignTemplateStore'
import type {
  CampaignInstanceModel,
  CampaignTemplateModel,
} from '@/types/unified'
import { campaignApi } from '@/services/campaignApi'
import { logger } from '@/utils/logger'
import CampaignGrid from '../components/campaign/CampaignGrid.vue'
import CampaignModal from '../components/campaign/CampaignModal.vue'
import CampaignTemplateGrid from '../components/campaign/CampaignTemplateGrid.vue'
import CampaignTemplateModal from '../components/campaign/CampaignTemplateModal.vue'
import CampaignFromTemplateModal from '../components/campaign/CampaignFromTemplateModal.vue'
import AppButton from '../components/base/AppButton.vue'

const campaignStore = useCampaignStore()
const templateStore = useCampaignTemplateStore()

// Reactive refs
const showCreateCampaignModal = ref(false)
const editingCampaign: Ref<CampaignTemplateModel | null> = ref(null)
const showCreateTemplateModal = ref(false)
const editingTemplate: Ref<CampaignTemplateModel | null> = ref(null)
const showCreateFromTemplateModal = ref(false)
const selectedTemplateForCampaign: Ref<CampaignTemplateModel | null> = ref(null)

// Store getters - use computed for reactivity
const campaigns = computed(() => campaignStore.campaigns)
const campaignsLoading = computed(() => campaignStore.campaignsLoading)
const campaignTemplates = computed(() => templateStore.templates)
const templatesLoading = computed(() => templateStore.templatesLoading)

onMounted(() => {
  // Load campaigns and templates
  campaignStore.loadCampaigns()
  templateStore.loadTemplates()
})

// Campaign methods
async function editCampaign(campaign: CampaignInstanceModel): void {
  if (!campaign.template_id) {
    logger.error('Campaign instance is missing a template_id', campaign)
    alert('This campaign cannot be edited as it is not linked to a template.')
    return
  }
  try {
    const response = await campaignApi.getCampaign(campaign.template_id)
    editingCampaign.value = response.data
    showCreateCampaignModal.value = true
  } catch (error) {
    logger.error(
      `Failed to fetch campaign template with id ${campaign.template_id}:`,
      error
    )
    alert('Failed to load campaign data for editing. Please try again.')
  }
}

function deleteCampaign(campaignId: string): void {
  if (
    confirm(
      'Are you sure you want to delete this campaign? This action cannot be undone.'
    )
  ) {
    campaignStore.deleteCampaign(campaignId)
  }
}

function playCampaign(campaignId: string): void {
  // Start the campaign and navigate to game view
  campaignStore.startCampaign(campaignId)
}

function closeCampaignModal(): void {
  showCreateCampaignModal.value = false
  editingCampaign.value = null
}

async function saveCampaign(
  campaignData: Partial<CampaignTemplateModel>
): Promise<void> {
  try {
    if (editingCampaign.value) {
      // We are editing a template, so use the template store
      await templateStore.updateTemplate(editingCampaign.value.id, campaignData)
    } else {
      // This is a new campaign from scratch, which creates a template
      await templateStore.createTemplate(campaignData)
    }
    closeCampaignModal()
  } catch (error) {
    console.error('Failed to save campaign:', error)
    alert('Failed to save campaign. Please check the console for details.')
  }
}

// Template methods
function useCampaignTemplate(template: CampaignTemplateModel): void {
  selectedTemplateForCampaign.value = template
  showCreateFromTemplateModal.value = true
}

function editCampaignTemplate(template: CampaignTemplateModel): void {
  editingTemplate.value = { ...template }
  showCreateTemplateModal.value = true
}

function deleteCampaignTemplate(templateId: string): void {
  if (
    confirm(
      'Are you sure you want to delete this template? This action cannot be undone.'
    )
  ) {
    templateStore.deleteTemplate(templateId)
  }
}

function closeTemplateModal(): void {
  showCreateTemplateModal.value = false
  editingTemplate.value = null
}

async function saveTemplate(
  templateData: Partial<CampaignTemplateModel>
): Promise<void> {
  try {
    if (editingTemplate.value) {
      await templateStore.updateTemplate(editingTemplate.value.id, templateData)
    } else {
      await templateStore.createTemplate(templateData)
    }
    closeTemplateModal()
  } catch (error) {
    console.error('Failed to save template:', error)
  }
}

// Create from template methods
function closeCreateFromTemplateModal(): void {
  showCreateFromTemplateModal.value = false
  selectedTemplateForCampaign.value = null
}

interface CreateFromTemplateData {
  templateId: string
  campaignName: string
  characterTemplateIds: string[]
  characterLevels?: Record<string, number>
  narrationEnabled?: boolean
  ttsVoice?: string
}

async function createCampaignFromTemplate(
  data: CreateFromTemplateData
): Promise<void> {
  try {
    // Extract TTS overrides if provided
    const ttsOverrides: { narrationEnabled?: boolean; ttsVoice?: string } = {}
    if (data.narrationEnabled !== undefined) {
      ttsOverrides.narrationEnabled = data.narrationEnabled
    }
    if (data.ttsVoice !== undefined) {
      ttsOverrides.ttsVoice = data.ttsVoice
    }

    await templateStore.createCampaignFromTemplate(
      data.templateId,
      data.campaignName,
      data.characterTemplateIds,
      ttsOverrides,
      data.characterLevels
    )
    closeCreateFromTemplateModal()
    // Reload campaigns to show the new one
    await campaignStore.loadCampaigns()
  } catch (error) {
    console.error('Failed to create campaign from template:', error)
    alert('Failed to create campaign from template. Please try again.')
  }
}
</script>
