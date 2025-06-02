<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div 
      class="absolute inset-0 bg-black bg-opacity-50"
      @click="$emit('close')"
    />
    
    <!-- Modal -->
    <div class="relative bg-parchment rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div class="fantasy-panel">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-cinzel font-bold text-text-primary">
            {{ campaign ? 'Edit Campaign' : 'Create Campaign' }}
          </h2>
          <button
            @click="$emit('close')"
            class="text-text-secondary hover:text-text-primary"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Form -->
        <form @submit.prevent="handleSave">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Left Column -->
            <div class="space-y-4">
              <!-- Campaign Name -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Campaign Name *
                </label>
                <input
                  v-model="formData.name"
                  type="text"
                  required
                  class="fantasy-input w-full"
                  placeholder="Enter campaign name..."
                />
              </div>
              
              <!-- Description -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Description *
                </label>
                <textarea
                  v-model="formData.description"
                  rows="3"
                  required
                  class="fantasy-input w-full resize-none"
                  placeholder="Describe your campaign..."
                />
              </div>
              
              <!-- Campaign Goal -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Campaign Goal *
                </label>
                <textarea
                  v-model="formData.campaign_goal"
                  rows="2"
                  required
                  class="fantasy-input w-full resize-none"
                  placeholder="What is the main objective?"
                />
              </div>
              
              <!-- Starting Location -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Starting Location *
                </label>
                <input
                  v-model="formData.starting_location.name"
                  type="text"
                  required
                  class="fantasy-input w-full mb-2"
                  placeholder="Location name..."
                />
                <textarea
                  v-model="formData.starting_location.description"
                  rows="2"
                  required
                  class="fantasy-input w-full resize-none"
                  placeholder="Location description..."
                />
              </div>
            </div>
            
            <!-- Right Column -->
            <div class="space-y-4">
              <!-- Starting Level -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Starting Level *
                </label>
                <input
                  v-model.number="formData.starting_level"
                  type="number"
                  min="1"
                  max="20"
                  required
                  class="fantasy-input w-full"
                />
              </div>
              
              <!-- Difficulty -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Difficulty *
                </label>
                <select v-model="formData.difficulty" class="fantasy-input w-full" required>
                  <option value="easy">Easy</option>
                  <option value="normal">Normal</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
              
              <!-- Ruleset -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Ruleset
                </label>
                <select v-model="formData.ruleset_id" class="fantasy-input w-full">
                  <option value="dnd5e_standard">D&D 5e Standard</option>
                  <option value="dnd5e_homebrew">D&D 5e with Homebrew</option>
                </select>
              </div>
              
              <!-- Lore -->
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">
                  Lore Setting
                </label>
                <select v-model="formData.lore_id" class="fantasy-input w-full">
                  <option value="generic_fantasy">Generic Fantasy</option>
                  <option value="forgotten_realms">Forgotten Realms</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              
            </div>
          </div>
          
          <!-- Opening Narrative -->
          <div class="mt-6">
            <label class="block text-sm font-medium text-text-primary mb-1">
              Opening Narrative *
            </label>
            <textarea
              v-model="formData.opening_narrative"
              rows="4"
              required
              class="fantasy-input w-full resize-none"
              placeholder="Set the scene for your adventure..."
            />
          </div>
          
          <!-- Note about party selection -->
          <div class="mt-4 p-4 bg-amber-50/20 rounded-lg border border-gold/20">
            <p class="text-sm text-text-secondary font-crimson">
              <strong>Note:</strong> This creates a blank campaign. To create a campaign with pre-selected characters and content, use the campaign templates feature.
            </p>
          </div>
          
          <!-- Actions -->
          <div class="flex justify-end space-x-3 mt-6 pt-4 border-t border-gold/20">
            <button
              type="button"
              @click="$emit('close')"
              class="fantasy-button-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="fantasy-button"
            >
              {{ campaign ? 'Update' : 'Create' }} Campaign
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  campaign: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

const formData = ref({
  name: '',
  description: '',
  campaign_goal: '',
  starting_location: {
    name: '',
    description: ''
  },
  opening_narrative: '',
  starting_level: 1,
  difficulty: 'normal',
  ruleset_id: 'dnd5e_standard',
  lore_id: 'generic_fantasy'
})

watch(() => props.campaign, (newCampaign) => {
  if (newCampaign) {
    formData.value = {
      name: newCampaign.name || '',
      description: newCampaign.description || '',
      campaign_goal: newCampaign.campaign_goal || '',
      starting_location: {
        name: newCampaign.starting_location?.name || '',
        description: newCampaign.starting_location?.description || ''
      },
      opening_narrative: newCampaign.opening_narrative || '',
      starting_level: newCampaign.starting_level || 1,
      difficulty: newCampaign.difficulty || 'normal',
      ruleset_id: newCampaign.ruleset_id || 'dnd5e_standard',
      lore_id: newCampaign.lore_id || 'generic_fantasy'
    }
  } else {
    // Reset to defaults for new campaign
    formData.value = {
      name: '',
      description: '',
      campaign_goal: '',
      starting_location: {
        name: '',
        description: ''
      },
      opening_narrative: '',
      starting_level: 1,
      difficulty: 'normal',
      ruleset_id: 'dnd5e_standard',
      lore_id: 'generic_fantasy'
    }
  }
}, { immediate: true })

function handleSave() {
  emit('save', { ...formData.value })
}
</script>