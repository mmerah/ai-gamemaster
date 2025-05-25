<template>
  <div>
    <div v-if="loading" class="text-center py-8">
      <div class="spinner"></div>
      <p class="text-text-secondary mt-2">Loading campaigns...</p>
    </div>
    
    <div v-else-if="!campaigns.length" class="text-center py-12">
      <div class="text-6xl mb-4">🏰</div>
      <p class="text-text-secondary">No campaigns yet. Create your first adventure!</p>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="campaign in campaigns"
        :key="campaign.id"
        class="fantasy-panel hover:shadow-lg transition-shadow"
      >
        <!-- Campaign Header -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-1">
              {{ campaign.name }}
            </h3>
            <p class="text-sm text-text-secondary">
              Created {{ formatDate(campaign.created_at) }}
            </p>
          </div>
          <div class="flex space-x-1">
            <button
              @click="$emit('edit', campaign)"
              class="p-1 text-gold hover:text-gold-light transition-colors"
              title="Edit Campaign"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              @click="$emit('delete', campaign.id)"
              class="p-1 text-crimson hover:text-crimson-light transition-colors"
              title="Delete Campaign"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Campaign Description -->
        <div v-if="campaign.description" class="mb-4">
          <p class="text-sm text-text-primary line-clamp-3">
            {{ campaign.description }}
          </p>
        </div>
        
        <!-- Campaign Info -->
        <div class="space-y-2 mb-4">
          <div class="flex items-center text-sm">
            <span class="text-text-secondary w-16">Status:</span>
            <span :class="getStatusColor(campaign.status)" class="font-medium capitalize">
              {{ campaign.status || 'draft' }}
            </span>
          </div>
          <div v-if="campaign.party?.length" class="flex items-center text-sm">
            <span class="text-text-secondary w-16">Party:</span>
            <span class="text-text-primary">{{ campaign.party.length }} members</span>
          </div>
          <div v-if="campaign.lastPlayed" class="flex items-center text-sm">
            <span class="text-text-secondary w-16">Last:</span>
            <span class="text-text-primary">{{ formatDate(campaign.lastPlayed) }}</span>
          </div>
        </div>
        
        <!-- Actions -->
        <div class="flex space-x-2">
          <button
            @click="$emit('play', campaign.id)"
            class="fantasy-button flex-1"
          >
            ⚔️ Play
          </button>
          <button
            @click="$emit('edit', campaign)"
            class="fantasy-button-secondary px-3"
          >
            ⚙️
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  campaigns: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit', 'delete', 'play'])

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

function getStatusColor(status) {
  switch (status) {
    case 'active':
      return 'text-forest-light'
    case 'completed':
      return 'text-royal-blue'
    case 'paused':
      return 'text-accent'
    default:
      return 'text-text-secondary'
  }
}
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
