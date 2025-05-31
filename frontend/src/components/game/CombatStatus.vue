<template>
  <div class="fantasy-panel">
    <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">
      Combat Status
      <span v-if="!combatStore.isConnected" class="text-xs text-red-500 ml-2">(Disconnected)</span>
    </h3>

    <div v-if="combatStore.isActive" class="space-y-4">
      <!-- Current Turn -->
      <div class="p-3 border border-crimson/30 rounded-lg bg-crimson/10">
        <div class="flex justify-between items-center">
          <span class="font-medium text-text-primary">Current Turn</span>
          <span class="text-sm text-text-secondary">Round {{ combatStore.roundNumber }}</span>
        </div>
        <p class="text-lg text-crimson font-semibold mt-1">
          {{ combatStore.currentTurnName }}
        </p>
      </div>

      <!-- Initiative Status -->
      <div v-if="!combatStore.hasInitiativeSet" class="p-3 border border-amber-500/30 rounded-lg bg-amber-500/10">
        <p class="text-sm text-amber-600 font-medium">⏳ Setting initiative...</p>
      </div>

      <!-- Initiative Order -->
      <div v-if="combatStore.hasInitiativeSet">
        <h4 class="text-sm font-medium text-text-primary mb-2">Initiative Order</h4>
        <div class="space-y-2">
          <div
            v-for="(combatant, index) in combatStore.combatants"
            :key="combatant.id"
            :class="[
              'p-2 rounded text-sm transition-colors',
              index === combatStore.currentTurnIndex
                ? 'bg-gold/20 border border-gold/30' 
                : 'bg-parchment-dark'
            ]"
          >
            <div class="flex items-center justify-between">
              <span class="font-medium">
                {{ combatant.name }}
                <span v-if="combatant.is_player" class="text-xs text-blue-500 ml-1">(PC)</span>
              </span>
              <span class="text-xs">
                Init: {{ combatant.initiative >= 0 ? combatant.initiative : '?' }}
              </span>
            </div>
            <div class="text-xs text-text-secondary">
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

    <div v-else class="text-center text-text-secondary py-4">
      <p>Not currently in combat</p>
      <p v-if="combatStore.isConnected" class="text-xs text-green-600 mt-1">✓ Connected to events</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useCombatStore } from '@/stores/combatStore'

// Props (optional for development/debug mode)
const props = defineProps({
  showDebug: {
    type: Boolean,
    default: false
  }
})

// Use the combat store
const combatStore = useCombatStore()

// Initialize store on component mount
onMounted(() => {
  combatStore.initialize()
})

// Clean up on component unmount
onUnmounted(() => {
  combatStore.cleanup()
})
</script>
