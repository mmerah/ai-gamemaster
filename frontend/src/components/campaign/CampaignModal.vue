<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div 
      class="absolute inset-0 bg-black bg-opacity-50"
      @click="$emit('close')"
    />
    
    <!-- Modal -->
    <div class="relative bg-parchment rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
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
                Description
              </label>
              <textarea
                v-model="formData.description"
                rows="3"
                class="fantasy-input w-full resize-none"
                placeholder="Describe your campaign..."
              />
            </div>
            
            <!-- Status -->
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                Status
              </label>
              <select v-model="formData.status" class="fantasy-input w-full">
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
              </select>
            </div>
            
            <!-- Party Selection -->
            <div v-if="templates.length">
              <label class="block text-sm font-medium text-text-primary mb-2">
                Select Party Members
              </label>
              <div class="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto">
                <label
                  v-for="template in templates"
                  :key="template.id"
                  class="flex items-center space-x-3 p-2 border border-gold/30 rounded hover:bg-gold/10"
                >
                  <input
                    type="checkbox"
                    :value="template.id"
                    v-model="formData.partyTemplates"
                    class="rounded"
                  />
                  <span class="text-sm">{{ template.name }} ({{ template.race }} {{ template.class }})</span>
                </label>
              </div>
            </div>
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
  },
  templates: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'save'])

const formData = ref({
  name: '',
  description: '',
  status: 'draft',
  partyTemplates: []
})

watch(() => props.campaign, (newCampaign) => {
  if (newCampaign) {
    formData.value = {
      name: newCampaign.name || '',
      description: newCampaign.description || '',
      status: newCampaign.status || 'draft',
      partyTemplates: newCampaign.partyTemplates || []
    }
  } else {
    formData.value = {
      name: '',
      description: '',
      status: 'draft',
      partyTemplates: []
    }
  }
}, { immediate: true })

function handleSave() {
  emit('save', { ...formData.value })
}
</script>
