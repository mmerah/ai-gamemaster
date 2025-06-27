<template>
  <BasePanel>
    <template #header>
      <h3 class="text-lg font-cinzel font-semibold text-foreground">Map</h3>
    </template>

    <div v-if="location" class="space-y-3">
      <!-- Current Location -->
      <div class="text-sm font-medium text-foreground">
        Current Location: {{ location }}
      </div>

      <!-- Map Placeholder -->
      <div
        class="relative bg-card rounded-lg overflow-hidden border-2 border-primary-light"
      >
        <div
          class="w-full h-48 flex items-center justify-center bg-gradient-to-b from-card to-background"
        >
          <span class="text-foreground/60 font-medium">Map Placeholder</span>
        </div>
      </div>

      <!-- Location Description -->
      <div v-if="description" class="text-sm text-foreground/60">
        {{ description }}
      </div>
    </div>

    <div v-else class="text-center text-foreground/60 py-8">
      <p>No location information available</p>
    </div>
  </BasePanel>
</template>

<script setup lang="ts">
import BasePanel from '@/components/base/BasePanel.vue'

// Props interface
interface Props {
  location?: string | null
  description?: string | null
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  location: null,
  description: null,
})
</script>
