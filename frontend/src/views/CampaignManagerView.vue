<template>
  <div class="campaign-manager-view min-h-screen bg-parchment">
    <!-- Header -->
    <div class="bg-primary-dark text-parchment p-6">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-cinzel font-bold text-gold">
            Campaign Manager
          </h1>
          <p class="text-parchment/80 mt-2">
            Manage your campaigns and adventures
          </p>
        </div>
        <button
          class="fantasy-button-secondary px-4 py-2"
          @click="$router.push('/')"
        >
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
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto p-6">
      <!-- Ongoing Campaigns Section -->
      <div class="mb-12">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-cinzel font-semibold text-text-primary">
            Ongoing Campaigns
          </h2>
          <button
            class="fantasy-button"
            @click="showCreateCampaignModal = true"
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
            Create New Campaign
          </button>
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
          <h2 class="text-2xl font-cinzel font-semibold text-text-primary">
            Campaign Templates
          </h2>
          <button
            class="fantasy-button-secondary"
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
          </button>
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

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCampaignStore } from '../stores/campaignStore'
import { useCampaignTemplateStore } from '../stores/campaignTemplateStore'
import CampaignGrid from '../components/campaign/CampaignGrid.vue'
import CampaignModal from '../components/campaign/CampaignModal.vue'
import CampaignTemplateGrid from '../components/campaign/CampaignTemplateGrid.vue'
import CampaignTemplateModal from '../components/campaign/CampaignTemplateModal.vue'
import CampaignFromTemplateModal from '../components/campaign/CampaignFromTemplateModal.vue'

const campaignStore = useCampaignStore()
const templateStore = useCampaignTemplateStore()

// Reactive refs
const showCreateCampaignModal = ref(false)
const editingCampaign = ref(null)
const showCreateTemplateModal = ref(false)
const editingTemplate = ref(null)
const showCreateFromTemplateModal = ref(false)
const selectedTemplateForCampaign = ref(null)

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
function editCampaign(campaign) {
  editingCampaign.value = { ...campaign }
  showCreateCampaignModal.value = true
}

function deleteCampaign(campaignId) {
  if (confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
    campaignStore.deleteCampaign(campaignId)
  }
}

function playCampaign(campaignId) {
  // Start the campaign and navigate to game view
  campaignStore.startCampaign(campaignId)
}

function closeCampaignModal() {
  showCreateCampaignModal.value = false
  editingCampaign.value = null
}

async function saveCampaign(campaignData) {
  try {
    if (editingCampaign.value) {
      await campaignStore.updateCampaign(editingCampaign.value.id, campaignData)
    } else {
      await campaignStore.createCampaign(campaignData)
    }
    closeCampaignModal()
  } catch (error) {
    console.error('Failed to save campaign:', error)
  }
}

// Template methods
function useCampaignTemplate(template) {
  selectedTemplateForCampaign.value = template
  showCreateFromTemplateModal.value = true
}

function editCampaignTemplate(template) {
  editingTemplate.value = { ...template }
  showCreateTemplateModal.value = true
}

function deleteCampaignTemplate(templateId) {
  if (confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
    templateStore.deleteTemplate(templateId)
  }
}

function closeTemplateModal() {
  showCreateTemplateModal.value = false
  editingTemplate.value = null
}

async function saveTemplate(templateData) {
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
function closeCreateFromTemplateModal() {
  showCreateFromTemplateModal.value = false
  selectedTemplateForCampaign.value = null
}

async function createCampaignFromTemplate(data) {
  try {
    // Extract TTS overrides if provided
    const ttsOverrides = {}
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
      ttsOverrides
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

<style scoped>
.campaign-manager-view {
  font-family: 'Crimson Text', serif;
}
</style>
