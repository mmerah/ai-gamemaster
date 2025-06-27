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
      <div class="bg-card rounded-lg overflow-hidden border border-border">
        <div
          class="w-full h-48 bg-gradient-to-b from-card to-background p-4 flex items-center justify-center"
        >
          <p class="text-foreground/40 text-sm">
            Map visualization coming soon...
          </p>
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
