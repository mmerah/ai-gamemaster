<template>
  <div class="characters-manager-screen min-h-screen bg-parchment">
    <!-- Header -->
    <div class="bg-primary-dark shadow-xl">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-cinzel font-bold text-gold">Characters</h1>
            <p class="text-parchment/80 mt-2 font-crimson">Create and manage your character templates</p>
          </div>
          <button
            @click="$router.push('/')"
            class="fantasy-button-secondary px-4 py-2"
          >
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Back to Launch
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Action Bar -->
      <div class="flex justify-between items-center mb-8">
        <h2 class="text-2xl font-cinzel font-semibold text-text-primary">
          Character Templates
        </h2>
        <button
          @click="showCreateTemplateModal = true"
          class="fantasy-button"
        >
          <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Create Character
        </button>
      </div>

      <!-- Error Message -->
      <transition name="fade">
        <div v-if="errorMessage" class="mb-6 bg-crimson/10 border border-crimson/30 rounded-lg p-4">
          <div class="flex items-center">
            <svg class="w-5 h-5 text-crimson mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <p class="text-crimson">{{ errorMessage }}</p>
          </div>
        </div>
      </transition>

      <!-- Templates Grid -->
      <TemplateGrid
        :templates="templates"
        :loading="templatesLoading"
        @edit="editTemplate"
        @delete="deleteTemplate"
        @duplicate="duplicateTemplate"
        @view-adventures="viewCharacterAdventures"
      />

      <!-- Character Adventures Panel -->
      <transition name="slide-fade">
        <div v-if="selectedCharacter" class="mt-8 fantasy-panel">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-cinzel font-semibold text-text-primary">
              {{ selectedCharacter.name }}'s Adventures
            </h3>
            <button
              @click="selectedCharacter = null"
              class="text-text-secondary hover:text-gold transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <!-- Loading Adventures -->
          <div v-if="adventuresLoading" class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gold mb-4"></div>
            <p class="text-text-secondary font-crimson">Loading adventures...</p>
          </div>

          <!-- Adventures List -->
          <div v-else-if="characterAdventures.length > 0" class="space-y-4">
            <div
              v-for="adventure in characterAdventures"
              :key="adventure.campaign_id"
              class="border border-gold/20 rounded-lg p-4 hover:border-gold/40 transition-colors"
            >
              <div class="flex justify-between items-start">
                <div>
                  <h4 class="font-cinzel font-semibold text-text-primary">
                    {{ adventure.campaign_name }}
                  </h4>
                  <div class="mt-2 space-y-1 text-sm text-text-secondary font-crimson">
                    <p>Level {{ adventure.character_level }} {{ adventure.character_class }}</p>
                    <p>HP: {{ adventure.current_hp }}/{{ adventure.max_hp }}</p>
                    <p>Last played: {{ formatDate(adventure.last_played) }}</p>
                  </div>
                </div>
                <button
                  @click="continueCampaign(adventure.campaign_id)"
                  class="fantasy-button-secondary px-3 py-1 text-sm"
                >
                  Continue
                </button>
              </div>
            </div>
          </div>

          <!-- No Adventures -->
          <div v-else class="text-center py-8">
            <p class="text-text-secondary font-crimson">
              This character hasn't started any adventures yet.
            </p>
          </div>
        </div>
      </transition>
    </div>

    <!-- Modals -->
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
import { useRouter } from 'vue-router'
import { useCampaignStore } from '../stores/campaignStore'
import { campaignApi } from '../services/campaignApi'
import TemplateGrid from '../components/campaign/TemplateGrid.vue'
import TemplateModal from '../components/campaign/TemplateModal.vue'

const router = useRouter()
const campaignStore = useCampaignStore() // Only for navigation

// Reactive refs
const showCreateTemplateModal = ref(false)
const editingTemplate = ref(null)
const selectedCharacter = ref(null)
const characterAdventures = ref([])
const adventuresLoading = ref(false)
const errorMessage = ref(null)

// Character templates state
const templates = ref([])
const templatesLoading = ref(false)

// Load character templates function
async function loadCharacterTemplates() {
  templatesLoading.value = true
  try {
    const response = await campaignApi.getTemplates()
    templates.value = response.data || []
  } catch (error) {
    console.error('Failed to load character templates:', error)
    templates.value = []
  } finally {
    templatesLoading.value = false
  }
}

onMounted(() => {
  // Load character templates
  loadCharacterTemplates()
})

// Template methods
function editTemplate(template) {
  editingTemplate.value = { ...template }
  showCreateTemplateModal.value = true
}

async function deleteTemplate(templateId) {
  if (confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
    try {
      await campaignApi.deleteTemplate(templateId)
      await loadCharacterTemplates() // Reload the list
    } catch (error) {
      console.error('Failed to delete template:', error)
      errorMessage.value = error.response?.data?.error || error.message || 'Failed to delete character template. Please try again.'
      // Clear error after 5 seconds
      setTimeout(() => {
        errorMessage.value = null
      }, 5000)
    }
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
      await campaignApi.updateTemplate(editingTemplate.value.id, templateData)
    } else {
      await campaignApi.createTemplate(templateData)
    }
    await loadCharacterTemplates() // Reload the list
    closeTemplateModal()
  } catch (error) {
    console.error('Failed to save template:', error)
    errorMessage.value = error.response?.data?.error || error.message || 'Failed to save character template. Please try again.'
    // Clear error after 5 seconds
    setTimeout(() => {
      errorMessage.value = null
    }, 5000)
  }
}

// Adventures methods
async function viewCharacterAdventures(template) {
  selectedCharacter.value = template
  adventuresLoading.value = true

  try {
    const response = await fetch(`/api/character_templates/${template.id}/adventures`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()

    // Transform the data to match our component's expected format
    characterAdventures.value = data.adventures.map(adventure => ({
      campaign_id: adventure.campaign_id,
      campaign_name: adventure.campaign_name,
      character_level: adventure.character_data.level,
      character_class: adventure.character_data.char_class || adventure.character_data.class,
      current_hp: adventure.character_data.current_hp,
      max_hp: adventure.character_data.max_hp,
      last_played: adventure.last_played
    }))
  } catch (error) {
    console.error('Failed to load character adventures:', error)
    characterAdventures.value = []
  } finally {
    adventuresLoading.value = false
  }
}

function continueCampaign(campaignId) {
  campaignStore.startCampaign(campaignId)
}

function formatDate(dateString) {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`

  return date.toLocaleDateString()
}
</script>

<style scoped>
.characters-manager-screen {
  font-family: 'Crimson Text', serif;
}

.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  transform: translateY(-10px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
