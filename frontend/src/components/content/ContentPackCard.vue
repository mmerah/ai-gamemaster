<template>
  <AppCard class="hover:shadow-xl transition-shadow">
    <div class="p-6">
      <!-- Header -->
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-xl font-cinzel font-semibold text-foreground">
            {{ pack.name }}
          </h3>
          <p class="text-sm text-foreground/60 mt-1">
            v{{ pack.version }} by {{ pack.author || 'Unknown' }}
          </p>
        </div>
        <BaseBadge
          :variant="pack.is_active ? 'success' : 'secondary'"
          size="sm"
        >
          {{ pack.is_active ? 'Available' : 'Hidden' }}
        </BaseBadge>
      </div>

      <!-- Description -->
      <p class="text-foreground/60 mb-4 line-clamp-2">
        {{ pack.description || 'No description available' }}
      </p>

      <!-- Statistics (if available) -->
      <div
        v-if="packWithStats && packWithStats.statistics"
        class="mb-4 text-sm text-foreground/60"
      >
        <div class="grid grid-cols-2 gap-2">
          <div v-for="(count, type) in packWithStats.statistics" :key="type">
            <template v-if="type !== 'total'">
              <span class="capitalize">{{ formatContentType(type) }}:</span>
              <span class="font-medium text-foreground ml-1">{{ count }}</span>
            </template>
          </div>
        </div>
        <div
          v-if="packWithStats.statistics.total"
          class="mt-2 pt-2 border-t border-border"
        >
          <span class="font-medium">Total Items:</span>
          <span class="font-medium text-foreground ml-1">{{
            packWithStats.statistics.total
          }}</span>
        </div>
      </div>

      <!-- Usage Statistics -->
      <div
        v-if="usageCount !== undefined"
        class="mb-4 text-sm text-foreground/60"
      >
        <div class="flex items-center gap-2">
          <svg
            class="w-4 h-4 text-foreground/60"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
            />
          </svg>
          <span>Used by</span>
          <span class="font-medium text-foreground">{{ usageCount }}</span>
          <span>{{ usageCount === 1 ? 'character' : 'characters' }}</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap gap-2">
        <!-- Available for Selection Toggle -->
        <AppButton
          v-if="!isSystemPack"
          :variant="pack.is_active ? 'secondary' : 'primary'"
          size="sm"
          :title="
            pack.is_active
              ? 'Hide from character creation'
              : 'Make available for character creation'
          "
          @click="toggleAvailability"
        >
          {{ pack.is_active ? 'Hide' : 'Make Available' }}
        </AppButton>

        <!-- View Details -->
        <router-link :to="`/content/${pack.id}`">
          <AppButton
            variant="secondary"
            size="sm"
            class="inline-flex items-center"
          >
            <svg
              class="w-4 h-4 mr-1"
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
          </AppButton>
        </router-link>

        <!-- Upload Content -->
        <AppButton
          v-if="!isSystemPack"
          variant="primary"
          size="sm"
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
        </AppButton>

        <!-- Delete -->
        <AppButton
          v-if="!isSystemPack"
          variant="danger"
          size="sm"
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
        </AppButton>
      </div>

      <!-- System Pack Notice -->
      <p v-if="isSystemPack" class="mt-3 text-xs text-foreground/60 italic">
        System content pack is always available and cannot be modified or
        deleted
      </p>
    </div>
  </AppCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ContentPack, ContentPackWithStats } from '../../types/content'
import AppCard from '../base/AppCard.vue'
import AppButton from '../base/AppButton.vue'
import BaseBadge from '../base/BaseBadge.vue'

// Props
const props = defineProps<{
  pack: ContentPack | ContentPackWithStats
  usageCount?: number
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
  return 'statistics' in props.pack
    ? (props.pack as ContentPackWithStats)
    : null
})

// Methods
function toggleAvailability() {
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
