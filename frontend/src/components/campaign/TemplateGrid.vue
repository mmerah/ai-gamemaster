<template>
  <div>
    <div v-if="loading" class="text-center py-8">
      <BaseLoader size="lg" />
      <p class="text-foreground/60 mt-2">Loading templates...</p>
    </div>

    <div v-else-if="!templates.length" class="text-center py-12">
      <div class="text-6xl mb-4">🧙‍♂️</div>
      <p class="text-foreground/60">
        No character templates yet. Create your first character!
      </p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <AppCard
        v-for="template in templates"
        :key="template.id"
        class="hover:shadow-lg transition-shadow"
      >
        <!-- Template Header -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <h3 class="text-lg font-cinzel font-semibold text-foreground mb-1">
              {{ template.name }}
            </h3>
            <p class="text-sm text-foreground/60">
              {{ formatD5eTerm(template.race) }}
              {{ formatD5eTerm(template.char_class) }}
            </p>
          </div>
          <div class="flex space-x-1">
            <button
              class="p-1 text-accent hover:text-accent/80 transition-colors"
              title="Edit Template"
              @click="$emit('edit', template)"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
            <button
              class="p-1 text-blue-600 hover:text-blue-500 transition-colors"
              title="Duplicate Template"
              @click="$emit('duplicate', template)"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </button>
            <button
              class="p-1 text-red-600 hover:text-red-500 transition-colors"
              title="Delete Template"
              @click="$emit('delete', template.id)"
            >
              <svg
                class="w-4 h-4"
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
            </button>
          </div>
        </div>

        <!-- Template Portrait -->
        <div class="mb-4">
          <div
            v-if="template.portrait_path"
            class="w-full h-48 bg-card rounded overflow-hidden"
          >
            <img
              :src="template.portrait_path"
              :alt="`${template.name} portrait`"
              class="w-full h-full object-cover"
              @error="handleImageError"
            />
          </div>
          <div
            v-else
            class="w-full h-48 bg-card rounded flex items-center justify-center"
          >
            <div class="text-center">
              <svg
                class="w-16 h-16 mx-auto text-foreground/30"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              <p class="text-xs text-foreground/60 mt-2">No portrait</p>
            </div>
          </div>
        </div>

        <!-- Template Background -->
        <div v-if="template.background" class="mb-4">
          <p class="text-sm text-foreground/60">
            <span class="font-medium">Background:</span>
            {{ formatD5eTerm(template.background) }}
          </p>
        </div>

        <!-- Actions -->
        <div class="flex space-x-2">
          <AppButton class="flex-1" @click="$emit('view-adventures', template)">
            Adventures
          </AppButton>
          <AppButton
            variant="secondary"
            size="sm"
            title="Edit"
            @click="$emit('edit', template)"
          >
            ✏️
          </AppButton>
          <AppButton
            variant="secondary"
            size="sm"
            title="Duplicate"
            @click="$emit('duplicate', template)"
          >
            📋
          </AppButton>
        </div>
      </AppCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatD5eTerm } from '@/utils/stringFormatters'
import type { CharacterTemplateModel } from '@/types/unified'
import AppButton from '@/components/base/AppButton.vue'
import AppCard from '@/components/base/AppCard.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'

interface Props {
  templates: CharacterTemplateModel[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  edit: [template: CharacterTemplateModel]
  delete: [id: string]
  duplicate: [template: CharacterTemplateModel]
  'view-adventures': [template: CharacterTemplateModel]
}>()

// Handle broken portrait images
function handleImageError(event: Event): void {
  const target = event.target as HTMLImageElement
  if (target && target.parentElement) {
    target.style.display = 'none'
    target.parentElement.innerHTML = `
      <div class="w-full h-full flex items-center justify-center">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto text-foreground/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
          </svg>
          <p class="text-xs text-foreground/60 mt-2">Portrait not found</p>
        </div>
      </div>
    `
  }
}
</script>
