<template>
  <div class="fantasy-card hover:shadow-xl transition-shadow">
    <div class="p-6">
      <!-- Header -->
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-xl font-cinzel font-semibold text-text-primary">
            {{ pack.name }}
          </h3>
          <p class="text-sm text-text-secondary mt-1">
            v{{ pack.version }} by {{ pack.author || 'Unknown' }}
          </p>
        </div>
        <span
          :class="[
            'px-2 py-1 text-xs font-medium rounded',
            pack.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          ]"
        >
          {{ pack.is_active ? 'Active' : 'Inactive' }}
        </span>
      </div>

      <!-- Description -->
      <p class="text-text-secondary mb-4 line-clamp-2">
        {{ pack.description || 'No description available' }}
      </p>

      <!-- Statistics (if available) -->
      <div v-if="packWithStats && packWithStats.statistics" class="mb-4 text-sm text-text-secondary">
        <div class="grid grid-cols-2 gap-2">
          <div v-for="(count, type) in packWithStats.statistics" :key="type">
            <template v-if="type !== 'total'">
              <span class="capitalize">{{ formatContentType(type) }}:</span>
              <span class="font-medium text-text-primary ml-1">{{ count }}</span>
            </template>
          </div>
        </div>
        <div v-if="packWithStats.statistics.total" class="mt-2 pt-2 border-t border-gray-300">
          <span class="font-medium">Total Items:</span>
          <span class="font-medium text-text-primary ml-1">{{ packWithStats.statistics.total }}</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap gap-2">
        <!-- Activate/Deactivate -->
        <button
          v-if="!isSystemPack"
          :class="[
            'px-3 py-1 text-sm font-medium rounded transition-colors',
            pack.is_active
              ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              : 'bg-green-600 text-white hover:bg-green-700'
          ]"
          @click="toggleActive"
        >
          {{ pack.is_active ? 'Deactivate' : 'Activate' }}
        </button>

        <!-- View Details -->
        <router-link
          :to="`/content/${pack.id}`"
          class="px-3 py-1 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 transition-colors inline-block"
        >
          <svg
            class="w-4 h-4 inline mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          View
        </router-link>

        <!-- Upload Content -->
        <button
          v-if="!isSystemPack"
          class="px-3 py-1 text-sm font-medium rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          @click="$emit('upload', pack)"
        >
          <svg
            class="w-4 h-4 inline mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          Upload
        </button>

        <!-- Delete -->
        <button
          v-if="!isSystemPack"
          class="px-3 py-1 text-sm font-medium rounded bg-red-600 text-white hover:bg-red-700 transition-colors"
          @click="confirmDelete"
        >
          <svg
            class="w-4 h-4 inline mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          Delete
        </button>
      </div>

      <!-- System Pack Notice -->
      <p v-if="isSystemPack" class="mt-3 text-xs text-text-secondary italic">
        System content pack cannot be modified or deleted
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ContentPack, ContentPackWithStats } from '../../types/content'

// Props
const props = defineProps<{
  pack: ContentPack | ContentPackWithStats
}>()

// Emits
const emit = defineEmits<{
  activate: [packId: string]
  deactivate: [packId: string]
  delete: [packId: string]
  upload: [pack: ContentPack]
}>()

// Computed
const isSystemPack = computed(() => props.pack.id === 'dnd_5e_srd')

const packWithStats = computed(() => {
  return 'statistics' in props.pack ? props.pack as ContentPackWithStats : null
})

// Methods
function toggleActive() {
  if (props.pack.is_active) {
    emit('deactivate', props.pack.id)
  } else {
    emit('activate', props.pack.id)
  }
}

function confirmDelete() {
  emit('delete', props.pack.id)
}

function formatContentType(type: string): string {
  // Convert snake_case to Title Case
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>