<template>
  <div class="campaign-manager-view min-h-screen bg-parchment">
    <!-- Header -->
    <div class="bg-primary-dark text-parchment p-6">
      <div class="max-w-7xl mx-auto">
        <h1 class="text-3xl font-cinzel font-bold text-gold">Campaign Manager</h1>
        <p class="text-parchment/80 mt-2">Manage your campaigns and character templates</p>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto p-6">
      <!-- Tab Navigation -->
      <div class="mb-8">
        <nav class="flex space-x-8">
          <button
            @click="activeTab = 'campaigns'"
            :class="[
              'pb-2 font-medium text-lg transition-colors',
              activeTab === 'campaigns' 
                ? 'text-gold border-b-2 border-gold' 
                : 'text-text-secondary hover:text-gold'
            ]"
          >
            Campaigns
          </button>
          <button
            @click="activeTab = 'templates'"
            :class="[
              'pb-2 font-medium text-lg transition-colors',
              activeTab === 'templates' 
                ? 'text-gold border-b-2 border-gold' 
                : 'text-text-secondary hover:text-gold'
            ]"
          >
            Character Templates
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div>
        <!-- Campaigns Tab -->
        <div v-if="activeTab === 'campaigns'" class="space-y-6">
          <!-- Action Bar -->
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-cinzel font-semibold text-text-primary">Your Campaigns</h2>
            <button
              @click="showCreateCampaignModal = true"
              class="fantasy-button"
            >
              <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Create Campaign
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

        <!-- Templates Tab -->
        <div v-if="activeTab === 'templates'" class="space-y-6">
          <!-- Action Bar -->
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-cinzel font-semibold text-text-primary">Character Templates</h2>
            <button
              @click="showCreateTemplateModal = true"
              class="fantasy-button"
            >
              <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Create Template
            </button>
          </div>

          <!-- Templates Grid -->
          <TemplateGrid 
            :templates="templates" 
            :loading="templatesLoading"
            @edit="editTemplate"
            @delete="deleteTemplate"
            @duplicate="duplicateTemplate"
          />
        </div>
      </div>
    </div>

    <!-- Modals -->
    <CampaignModal
      v-if="showCreateCampaignModal"
      :visible="showCreateCampaignModal"
      :campaign="editingCampaign"
      :templates="templates"
      @close="closeCampaignModal"
      @save="saveCampaign"
    />

    <TemplateModal
      v-if="showCreateTemplateModal"
      :visible="showCreateTemplateModal"
      :template="editingTemplate"
      @close="closeTemplateModal"
      @save="saveTemplate"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCampaignStore } from '../stores/campaignStore'
import CampaignGrid from '../components/campaign/CampaignGrid.vue'
import TemplateGrid from '../components/campaign/TemplateGrid.vue'
import CampaignModal from '../components/campaign/CampaignModal.vue'
import TemplateModal from '../components/campaign/TemplateModal.vue'

const campaignStore = useCampaignStore()

// Reactive refs
const activeTab = ref('campaigns')
const showCreateCampaignModal = ref(false)
const showCreateTemplateModal = ref(false)
const editingCampaign = ref(null)
const editingTemplate = ref(null)

// Store getters
const campaigns = campaignStore.campaigns
const templates = campaignStore.templates
const campaignsLoading = campaignStore.campaignsLoading
const templatesLoading = campaignStore.templatesLoading

onMounted(() => {
  // Load initial data
  campaignStore.loadCampaigns()
  campaignStore.loadTemplates()
  
  // Load D&D 5e data for character templates
  campaignStore.loadD5eRaces()
  campaignStore.loadD5eClasses()
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
  // Navigate to game with this campaign
  campaignStore.setActiveCampaign(campaignId)
  // The router should navigate to the game view
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
function editTemplate(template) {
  editingTemplate.value = { ...template }
  showCreateTemplateModal.value = true
}

function deleteTemplate(templateId) {
  if (confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
    campaignStore.deleteTemplate(templateId)
  }
}

function duplicateTemplate(template) {
  const duplicated = {
    ...template,
    name: `${template.name} (Copy)`,
    id: undefined // Will be assigned by backend
  }
  editingTemplate.value = duplicated
  showCreateTemplateModal.value = true
}

function closeTemplateModal() {
  showCreateTemplateModal.value = false
  editingTemplate.value = null
}

async function saveTemplate(templateData) {
  try {
    if (editingTemplate.value && editingTemplate.value.id) {
      await campaignStore.updateTemplate(editingTemplate.value.id, templateData)
    } else {
      await campaignStore.createTemplate(templateData)
    }
    closeTemplateModal()
  } catch (error) {
    console.error('Failed to save template:', error)
  }
}
</script>

<style scoped>
.campaign-manager-view {
  font-family: 'Crimson Text', serif;
}
</style>
