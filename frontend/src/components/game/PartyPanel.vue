<template>
  <div class="fantasy-panel">
    <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">
      Party
    </h3>

    <div v-if="!party.length" class="text-center text-text-secondary py-4">
      <p>No party members yet</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="member in party"
        :key="member.id"
        class="p-3 border border-gold/30 rounded-lg bg-gold/10"
      >
        <div class="flex items-start space-x-3">
          <div class="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-semibold">
            {{ member.name.charAt(0).toUpperCase() }}
          </div>

          <div class="flex-1 min-w-0">
            <h4 class="font-medium text-text-primary">
              {{ member.name }}
            </h4>
            <p class="text-sm text-text-secondary">
              {{ member.race }} {{ member.char_class || member.class }} (Level {{ member.level || 1 }})
            </p>

            <!-- Health Bar -->
            <div class="mt-2">
              <div class="flex items-center justify-between text-xs mb-1">
                <span>HP</span>
                <span>{{ member.currentHp || 0 }}/{{ member.maxHp || 0 }}</span>
              </div>
              <div class="w-full bg-parchment-dark rounded-full h-2">
                <div
                  class="bg-forest-light h-2 rounded-full transition-all"
                  :style="{ width: `${getHealthPercent(member)}%` }"
                />
              </div>
            </div>

            <!-- Status Effects -->
            <div v-if="member.statusEffects?.length" class="flex flex-wrap gap-1 mt-2">
              <span
                v-for="effect in member.statusEffects"
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
  </div>
</template>

<script setup lang="ts">
// Party member interface
interface PartyMember {
  id: string
  name: string
  race: string
  class: string
  level?: number
  currentHp?: number
  maxHp?: number
  statusEffects?: string[]
}

// Props interface
interface Props {
  party: PartyMember[]
}

const props = defineProps<Props>()

function getHealthPercent(member: PartyMember): number {
  if (!member.maxHp || member.maxHp === 0) return 0
  return Math.max(0, Math.min(100, (member.currentHp || 0) / member.maxHp * 100))
}
</script>
