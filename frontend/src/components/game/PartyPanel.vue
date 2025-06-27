<template>
  <BasePanel>
    <template #header>
      <h3 class="text-lg font-cinzel font-semibold text-foreground">Party</h3>
    </template>

    <div v-if="!party.length" class="text-center text-foreground/60 py-4">
      <p>No party members yet</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="member in party"
        :key="member.id"
        class="p-3 border border-accent/30 rounded-lg bg-accent/10"
      >
        <div class="flex items-start space-x-3">
          <div
            class="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-semibold"
          >
            {{ member.name.charAt(0).toUpperCase() }}
          </div>

          <div class="flex-1 min-w-0">
            <h4 class="font-medium text-foreground">
              {{ member.name }}
            </h4>
            <p class="text-sm text-foreground/60">
              {{ member.race }} {{ member.char_class }} (Level
              {{ member.level || 1 }})
              <!-- Use char_class -->
            </p>

            <!-- Health Bar -->
            <div class="mt-2">
              <div class="flex items-center justify-between text-xs mb-1">
                <span>HP</span>
                <span
                  >{{ member.current_hp || 0 }}/{{ member.max_hp || 0 }}</span
                >
                <!-- Use snake_case -->
              </div>
              <div class="w-full bg-card rounded-full h-2">
                <div
                  class="bg-green-600 dark:bg-green-500 h-2 rounded-full transition-all"
                  :style="{ width: `${getHealthPercent(member)}%` }"
                />
              </div>
            </div>

            <!-- Status Effects -->
            <div
              v-if="member.conditions?.length"
              class="flex flex-wrap gap-1 mt-2"
            >
              <!-- Use conditions -->
              <span
                v-for="effect in member.conditions"
                :key="effect"
                class="text-xs px-2 py-1 bg-accent/20 text-accent rounded"
              >
                {{ effect }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BasePanel>
</template>

<script setup lang="ts">
import BasePanel from '@/components/base/BasePanel.vue'
import type { UIPartyMember } from '@/types/ui' // Import the correct type

interface Props {
  party: UIPartyMember[] // Use the correct type
}

const props = defineProps<Props>()

function getHealthPercent(member: UIPartyMember): number {
  if (!member.max_hp || member.max_hp === 0) return 0 // Use snake_case
  return Math.max(
    0,
    Math.min(100, ((member.current_hp || 0) / member.max_hp) * 100) // Use snake_case
  )
}
</script>
