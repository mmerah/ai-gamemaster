<template>
  <div class="fantasy-panel">
    <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">
      Map
    </h3>

    <div v-if="location" class="space-y-3">
      <!-- Current Location -->
      <div class="text-sm font-medium text-text-primary">
        Current Location: {{ location }}
      </div>

      <!-- Map Placeholder -->
      <div
        class="relative bg-parchment-dark rounded-lg overflow-hidden border-2 border-primary-light"
      >
        <div
          class="w-full h-48 flex items-center justify-center bg-gradient-to-b from-parchment-dark to-parchment"
        >
          <span class="text-text-secondary font-medium">Map Placeholder</span>
        </div>
      </div>

      <!-- Location Description -->
      <div v-if="description" class="text-sm text-text-secondary">
        {{ description }}
      </div>
    </div>

    <div v-else class="text-center text-text-secondary py-8">
      <p>No location information available</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  location: {
    type: String,
    default: null,
  },
  description: {
    type: String,
    default: null,
  },
})
</script>
