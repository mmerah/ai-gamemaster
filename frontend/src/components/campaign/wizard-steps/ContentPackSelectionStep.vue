<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">Select Content Packs</h3>
    <p class="text-sm text-foreground/60">
      Choose which content packs to use for this character. The System Pack
      contains the core D&D 5e rules.
    </p>

    <div class="space-y-4">
      <BaseLoader v-if="loadingContentPacks" size="lg" />

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label
          v-for="pack in availableContentPacks"
          :key="pack.id"
          class="relative"
        >
          <input
            type="checkbox"
            :value="pack.id"
            :checked="modelValue.includes(pack.id)"
            :disabled="!pack.is_active"
            class="sr-only peer"
            @change="togglePack(pack.id)"
          />
          <AppCard
            class="cursor-pointer transition-all peer-checked:ring-2 peer-checked:ring-primary peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"
            :class="{
              'bg-primary/5': modelValue.includes(pack.id),
            }"
          >
            <div class="flex items-start space-x-3">
              <div
                class="w-5 h-5 rounded border-2 transition-colors mt-0.5"
                :class="
                  modelValue.includes(pack.id)
                    ? 'bg-primary border-primary'
                    : 'border-foreground/20'
                "
              >
                <svg
                  v-if="modelValue.includes(pack.id)"
                  class="w-3 h-3 text-primary-foreground m-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <h4 class="font-medium text-foreground">
                    {{ pack.name }}
                  </h4>
                  <BaseBadge v-if="pack.id === 'dnd_5e_srd'" variant="primary">
                    System
                  </BaseBadge>
                </div>
                <p class="text-sm text-foreground/60 mt-1">
                  {{ pack.description }}
                </p>
                <div class="flex flex-wrap gap-1 mt-2">
                  <BaseBadge
                    v-for="(count, type) in getPackStats(pack)"
                    :key="type"
                    variant="secondary"
                    size="sm"
                  >
                    {{ count }} {{ type }}
                  </BaseBadge>
                </div>
                <p v-if="!pack.is_active" class="text-xs text-red-600 mt-2">
                  This pack is currently disabled
                </p>
              </div>
            </div>
          </AppCard>
        </label>
      </div>

      <BaseAlert v-if="modelValue.length === 0" type="warning">
        At least one content pack must be selected to create a character.
      </BaseAlert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { D5eContentPack } from '@/types/unified'
import AppCard from '@/components/base/AppCard.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseLoader from '@/components/base/BaseLoader.vue'

export interface ContentPackSelectionStepProps {
  modelValue: string[]
  availableContentPacks: D5eContentPack[]
  loadingContentPacks: boolean
}

const props = defineProps<ContentPackSelectionStepProps>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

function togglePack(packId: string) {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(packId)

  if (index > -1) {
    newValue.splice(index, 1)
  } else {
    newValue.push(packId)
  }

  emit('update:modelValue', newValue)
}

function getPackStats(pack: D5eContentPack) {
  // D5eContentPack doesn't have statistics fields like classes_count
  // This function would need to be updated to work with the actual API response
  // For now, return an empty object
  return {}
}
</script>
