<template>
  <div>
    <div v-if="loading" class="text-center py-8">
      <div class="spinner"></div>
      <p class="text-text-secondary mt-2">Loading templates...</p>
    </div>
    
    <div v-else-if="!templates.length" class="text-center py-12">
      <div class="text-6xl mb-4">🧙‍♂️</div>
      <p class="text-text-secondary">No character templates yet. Create your first character!</p>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="template in templates"
        :key="template.id"
        class="fantasy-panel hover:shadow-lg transition-shadow"
      >
        <!-- Template Header -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-1">
              {{ template.name }}
            </h3>
            <p class="text-sm text-text-secondary">
              {{ template.race }} {{ template.class }}
            </p>
          </div>
          <div class="flex space-x-1">
            <button
              @click="$emit('edit', template)"
              class="p-1 text-gold hover:text-gold-light transition-colors"
              title="Edit Template"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              @click="$emit('duplicate', template)"
              class="p-1 text-royal-blue hover:text-royal-blue-light transition-colors"
              title="Duplicate Template"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            <button
              @click="$emit('delete', template.id)"
              class="p-1 text-crimson hover:text-crimson-light transition-colors"
              title="Delete Template"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Template Stats -->
        <div class="mb-4">
          <div class="grid grid-cols-3 gap-2 text-center">
            <div class="bg-parchment-dark rounded p-2">
              <div class="text-lg font-bold text-text-primary">{{ template.level || 1 }}</div>
              <div class="text-xs text-text-secondary">Level</div>
            </div>
            <div class="bg-parchment-dark rounded p-2">
              <div class="text-lg font-bold text-text-primary">{{ template.abilities?.strength || 10 }}</div>
              <div class="text-xs text-text-secondary">STR</div>
            </div>
            <div class="bg-parchment-dark rounded p-2">
              <div class="text-lg font-bold text-text-primary">{{ template.hitPoints || 0 }}</div>
              <div class="text-xs text-text-secondary">HP</div>
            </div>
          </div>
        </div>
        
        <!-- Template Background -->
        <div v-if="template.background" class="mb-4">
          <p class="text-sm text-text-secondary">
            <span class="font-medium">Background:</span> {{ template.background }}
          </p>
        </div>
        
        <!-- Actions -->
        <div class="flex space-x-2">
          <button
            @click="$emit('edit', template)"
            class="fantasy-button flex-1"
          >
            Edit
          </button>
          <button
            @click="$emit('duplicate', template)"
            class="fantasy-button-secondary px-3"
          >
            📋
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  templates: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit', 'delete', 'duplicate'])
</script>
