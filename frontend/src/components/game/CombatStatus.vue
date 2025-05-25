<template>
  <div class="fantasy-panel">
    <h3 class="text-lg font-cinzel font-semibold text-text-primary mb-4">Combat Status</h3>

    <div v-if="combatState?.is_active" class="space-y-4">
      <!-- Current Turn -->
      <div class="p-3 border border-crimson/30 rounded-lg bg-crimson/10">
        <div class="flex justify-between items-center">
          <span class="font-medium text-text-primary">Current Turn</span>
          <span class="text-sm text-text-secondary">Round {{ combatState.round || 1 }}</span>
        </div>
        <p class="text-lg text-crimson font-semibold mt-1">
          {{ combatState.current_turn || 'Waiting...' }}
        </p>
      </div>

      <!-- Initiative Order -->
      <div>
        <h4 class="text-sm font-medium text-text-primary mb-2">Initiative Order</h4>
        <div class="space-y-2">
          <div
            v-for="combatant in combatState.turn_order || []"
            :key="combatant.id"
            :class="[
              'p-2 rounded text-sm',
              isCombatantActive(combatant.id)
                ? 'bg-gold/20 border border-gold/30' 
                : 'bg-parchment-dark'
            ]"
          >
            <div class="flex items-center justify-between">
              <span class="font-medium">{{ combatant.name }}</span>
              <span class="text-xs">Init: {{ combatant.initiative }}</span>
            </div>
            <div class="text-xs text-text-secondary">
              HP: {{ getCombatantHpDetails(combatant).currentHp }} / {{ getCombatantHpDetails(combatant).maxHp }}
              <span v-if="getCombatantConditions(combatant).length > 0" class="ml-2">
                • {{ getCombatantConditions(combatant).join(', ') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center text-text-secondary py-4">
      <p>Not currently in combat</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  combatState: {
    type: Object,
    required: true
  },
  party: {
    type: Array,
    required: true
  }
});

function getCombatantHpDetails(combatant) {
  // Check if this is a player character
  const player = props.party.find(p => p.id === combatant.id);
  if (player) {
    return { 
      currentHp: player.hp || 0, 
      maxHp: player.maxHp || player.max_hp || 0 
    };
  } else {
    // This is an NPC/Monster
    const monster = props.combatState.monster_status?.[combatant.id];
    if (monster) {
      return { 
        currentHp: monster.hp || 0, 
        maxHp: monster.initial_hp || 0 
      };
    }
  }
  return { currentHp: 0, maxHp: 0 };
}

function getCombatantConditions(combatant) {
  // Check if this is a player character
  const player = props.party.find(p => p.id === combatant.id);
  if (player) {
    return player.conditions || [];
  } else {
    // This is an NPC/Monster
    const monster = props.combatState.monster_status?.[combatant.id];
    if (monster) {
      return monster.conditions || [];
    }
  }
  return [];
}

function isCombatantActive(combatantId) {
  return props.combatState.current_turn_id === combatantId;
}
</script>
