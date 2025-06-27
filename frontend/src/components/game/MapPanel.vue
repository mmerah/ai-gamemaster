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

      <!-- Map Visualization -->
      <div
        class="relative bg-card rounded-lg overflow-hidden border-2 border-primary-light"
      >
        <div class="w-full h-48 bg-gradient-to-b from-card to-background p-4">
          <!-- Simple ASCII-style map representation -->
          <div class="grid grid-cols-3 grid-rows-3 gap-1 h-full">
            <div
              v-for="i in 9"
              :key="i"
              class="flex items-center justify-center rounded transition-all duration-300"
              :class="[
                i === 5
                  ? 'bg-primary/20 border-2 border-primary text-primary-foreground font-bold'
                  : 'bg-background/50 border border-border/30 text-foreground/40 hover:bg-primary/10',
              ]"
            >
              <span v-if="i === 5" class="text-xs">You</span>
              <span v-else class="text-2xl opacity-20">{{
                getMapSymbol(i)
              }}</span>
            </div>
          </div>

          <!-- Compass -->
          <div class="absolute top-2 right-2 text-xs text-foreground/40">
            <div class="text-center">N</div>
            <div class="flex justify-between w-8">
              <span>W</span>
              <span>E</span>
            </div>
            <div class="text-center">S</div>
          </div>
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

// Map symbols for visual variety
const mapSymbols = ['⛰', '🌲', '🏔', '🌳', '🏛', '🗿', '⛺', '🏰', '🌊']

function getMapSymbol(position: number): string {
  // Generate consistent symbols based on position
  const index = (position - 1) % mapSymbols.length
  return mapSymbols[index]
}
</script>
