<template>
  <BasePanel>
    <template #header>
      <h3 class="text-lg font-cinzel font-semibold text-foreground">
        Combat Status
        <span v-if="!combatStore.isConnected" class="text-xs text-red-500 ml-2">
          (Disconnected)
        </span>
      </h3>
    </template>

    <div v-if="combatStore.isActive" class="space-y-4">
      <!-- Initiative Status -->
      <div
        v-if="!combatStore.hasInitiativeSet"
        class="p-3 border border-accent/30 rounded-lg bg-accent/10"
      >
        <p class="text-sm text-accent font-medium">
          ⏳ Rolling for initiative...
        </p>
      </div>

      <!-- Current Turn -->
      <div v-else class="p-3 border border-red-500/30 rounded-lg bg-red-500/10">
        <div class="flex justify-between items-center">
          <span class="font-medium text-foreground">Current Turn</span>
          <span class="text-sm text-foreground/60"
            >Round {{ combatStore.roundNumber }}</span
          >
        </div>
        <p class="text-lg text-red-500 font-semibold mt-1">
          {{ combatStore.currentTurnName }}
        </p>
      </div>

      <!-- Initiative Order -->
      <div v-if="combatStore.hasInitiativeSet">
        <h4 class="text-sm font-medium text-foreground mb-2">
          Initiative Order
        </h4>
        <div class="space-y-2">
          <div
            v-for="(combatant, index) in combatStore.combatants"
            :key="combatant.id"
            :class="[
              'p-2 rounded text-sm transition-colors',
              index === combatStore.currentTurnIndex
                ? 'bg-accent/20 border border-accent/30'
                : 'bg-card',
            ]"
          >
            <div class="flex items-center justify-between">
              <span class="font-medium">
                {{ combatant.name }}
                <span
                  v-if="combatant.is_player"
                  class="text-xs text-blue-500 ml-1"
                  >(PC)</span
                >
              </span>
              <span class="text-xs">
                Init:
                {{ combatant.initiative >= 0 ? combatant.initiative : '?' }}
              </span>
            </div>
            <div class="text-xs text-foreground/60">
              HP: {{ combatant.hp }} / {{ combatant.max_hp }}
              <span v-if="combatant.conditions.length > 0" class="ml-2">
                • {{ combatant.conditions.join(', ') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Debug Info -->
      <div v-if="showDebug" class="p-2 bg-gray-100 rounded text-xs">
        <p>Last Event: #{{ combatStore.lastEventSequence }}</p>
        <p>Combatants: {{ combatStore.combatants.length }}</p>
        <p>Initiative Set: {{ combatStore.hasInitiativeSet }}</p>
      </div>
    </div>

    <div v-else class="text-center text-foreground/60 py-4">
      <p>Not currently in combat</p>
      <p
        v-if="combatStore.isConnected"
        class="text-xs text-green-600 dark:text-green-400 mt-1"
      >
        ✓ Connected to events
      </p>
    </div>
  </BasePanel>
</template>

<script setup lang="ts">
import BasePanel from '@/components/base/BasePanel.vue'
import { useCombatStore } from '@/stores/combatStore'

// Props interface
interface Props {
  showDebug?: boolean
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  showDebug: false,
})

// Use the combat store
const combatStore = useCombatStore()

// The combatStore is already initialized by the eventRouter in GameView
// No need to initialize or cleanup here to avoid duplicate event handlers
</script>
