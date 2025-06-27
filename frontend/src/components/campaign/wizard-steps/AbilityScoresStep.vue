<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold text-foreground">Ability Scores</h3>

    <!-- Method Selection -->
    <div class="flex flex-wrap gap-4 mb-6">
      <label
        v-for="method in scoreMethods"
        :key="method.value"
        class="flex items-center space-x-2"
      >
        <input
          v-model="currentMethod"
          type="radio"
          :value="method.value"
          class="text-primary focus:ring-primary"
        />
        <span class="text-foreground">{{ method.label }}</span>
      </label>
    </div>

    <!-- Method-specific UI -->
    <div v-if="currentMethod === 'point-buy'" class="space-y-4">
      <BaseAlert type="info">
        <div class="flex justify-between items-center">
          <span>Points Remaining: {{ pointBuyRemaining }}</span>
          <span class="text-sm">
            (8 = 0pts, 9-13 = 1pt each, 14 = 2pts, 15 = 2pts)
          </span>
        </div>
      </BaseAlert>
    </div>

    <div v-else-if="currentMethod === 'standard-array'" class="space-y-4">
      <BaseAlert type="info">
        Assign these scores to your abilities: 15, 14, 13, 12, 10, 8
      </BaseAlert>
    </div>

    <div v-else-if="currentMethod === 'roll'" class="space-y-4">
      <div class="flex items-center space-x-4">
        <AppButton size="sm" @click="rollAllScores">
          Roll All Scores
        </AppButton>
        <span class="text-sm text-foreground/60"> (4d6, drop lowest) </span>
      </div>
    </div>

    <!-- Ability Score Inputs -->
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <div v-for="ability in abilities" :key="ability.key" class="space-y-2">
        <label class="block text-sm font-medium text-foreground">
          {{ ability.name }}
        </label>
        <div class="flex items-center space-x-2">
          <AppNumberInput
            :model-value="currentScores[ability.key]"
            :min="currentMethod === 'point-buy' ? 8 : 3"
            :max="currentMethod === 'point-buy' ? 15 : 18"
            :disabled="currentMethod === 'standard-array'"
            class="w-20"
            @update:model-value="updateScore(ability.key, $event)"
          />
          <div class="text-sm">
            <span class="text-foreground/60">Mod:</span>
            <span class="font-medium ml-1">
              {{ getModifier(currentScores[ability.key]) >= 0 ? '+' : ''
              }}{{ getModifier(currentScores[ability.key]) }}
            </span>
          </div>
        </div>
        <div
          v-if="currentMethod === 'roll' && rollResults[ability.key]"
          class="text-xs text-foreground/40"
        >
          Rolled: {{ rollResults[ability.key].join(', ') }}
        </div>
      </div>
    </div>

    <!-- Racial Bonuses Display -->
    <div
      v-if="racialBonuses && Object.keys(racialBonuses).length > 0"
      class="mt-6"
    >
      <h4 class="text-sm font-medium text-foreground mb-2">
        Racial Bonuses Applied:
      </h4>
      <div class="flex flex-wrap gap-2">
        <BaseBadge
          v-for="(bonus, ability) in racialBonuses"
          :key="ability"
          variant="default"
        >
          {{ ability }}: +{{ bonus }}
        </BaseBadge>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import AppButton from '@/components/base/AppButton.vue'
import AppNumberInput from '@/components/base/AppNumberInput.vue'
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseBadge from '@/components/base/BaseBadge.vue'

export interface AbilityScoresStepProps {
  modelValue: {
    ability_score_method: 'point-buy' | 'standard-array' | 'roll'
    strength: number
    dexterity: number
    constitution: number
    intelligence: number
    wisdom: number
    charisma: number
  }
  racialBonuses?: Record<string, number>
}

const props = withDefaults(defineProps<AbilityScoresStepProps>(), {
  racialBonuses: () => ({}),
})

const emit = defineEmits<{
  'update:modelValue': [value: AbilityScoresStepProps['modelValue']]
}>()

// Local state
const rollResults = ref<Record<string, number[]>>({})

// Constants
const abilities = [
  { key: 'strength', name: 'Strength' },
  { key: 'dexterity', name: 'Dexterity' },
  { key: 'constitution', name: 'Constitution' },
  { key: 'intelligence', name: 'Intelligence' },
  { key: 'wisdom', name: 'Wisdom' },
  { key: 'charisma', name: 'Charisma' },
]

const scoreMethods = [
  { value: 'point-buy', label: 'Point Buy (27 points)' },
  { value: 'standard-array', label: 'Standard Array' },
  { value: 'roll', label: 'Roll Scores' },
]

const standardArray = [15, 14, 13, 12, 10, 8]

// Simple reactive data
const currentMethod = ref(props.modelValue.ability_score_method)
const currentScores = ref({
  strength: props.modelValue.strength,
  dexterity: props.modelValue.dexterity,
  constitution: props.modelValue.constitution,
  intelligence: props.modelValue.intelligence,
  wisdom: props.modelValue.wisdom,
  charisma: props.modelValue.charisma,
})

// Point buy calculation
const pointBuyRemaining = computed(() => {
  if (currentMethod.value !== 'point-buy') return 0

  let total = 27
  Object.values(currentScores.value).forEach(score => {
    if (score >= 8 && score <= 15) {
      const costs = { 8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9 }
      total -= costs[score as keyof typeof costs] || 0
    }
  })
  return total
})

// Methods
function getModifier(score: number): number {
  return Math.floor((score - 10) / 2)
}

function updateScore(abilityKey: string, value: number) {
  currentScores.value[abilityKey as keyof typeof currentScores.value] = value
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', {
    ability_score_method: currentMethod.value,
    ...currentScores.value,
  })
}

function rollAbilityScore(): { total: number; rolls: number[] } {
  const rolls = Array.from(
    { length: 4 },
    () => Math.floor(Math.random() * 6) + 1
  )
  rolls.sort((a, b) => b - a)
  const total = rolls.slice(0, 3).reduce((sum, roll) => sum + roll, 0)
  return { total, rolls }
}

function rollAllScores() {
  const newResults: Record<string, number[]> = {}

  abilities.forEach(ability => {
    const result = rollAbilityScore()
    currentScores.value[ability.key as keyof typeof currentScores.value] =
      result.total
    newResults[ability.key] = result.rolls
  })

  rollResults.value = newResults
  emitUpdate()
}

// Watch for method changes
watch(currentMethod, newMethod => {
  if (newMethod === 'standard-array') {
    // Auto-assign standard array in order
    abilities.forEach((ability, index) => {
      currentScores.value[ability.key as keyof typeof currentScores.value] =
        standardArray[index]
    })
  } else if (newMethod === 'point-buy') {
    // Reset to all 8s for point buy
    abilities.forEach(ability => {
      currentScores.value[ability.key as keyof typeof currentScores.value] = 8
    })
  }
  emitUpdate()
})

// Watch for external changes to props
watch(
  () => props.modelValue,
  newValue => {
    currentMethod.value = newValue.ability_score_method
    currentScores.value = {
      strength: newValue.strength,
      dexterity: newValue.dexterity,
      constitution: newValue.constitution,
      intelligence: newValue.intelligence,
      wisdom: newValue.wisdom,
      charisma: newValue.charisma,
    }
  },
  { deep: true }
)
</script>
