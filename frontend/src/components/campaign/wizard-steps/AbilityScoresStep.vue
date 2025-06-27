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
          v-model="localMethod"
          type="radio"
          :value="method.value"
          class="text-primary focus:ring-primary"
        />
        <span class="text-foreground">{{ method.label }}</span>
      </label>
    </div>

    <!-- Method-specific UI -->
    <div v-if="localMethod === 'point-buy'" class="space-y-4">
      <BaseAlert type="info">
        <div class="flex justify-between items-center">
          <span>Points Remaining: {{ pointBuyRemaining }}</span>
          <span class="text-sm">
            (8 = 0pts, 9-13 = 1pt each, 14 = 2pts, 15 = 2pts)
          </span>
        </div>
      </BaseAlert>
    </div>

    <div v-else-if="localMethod === 'standard-array'" class="space-y-4">
      <BaseAlert type="info">
        Assign these scores to your abilities: 15, 14, 13, 12, 10, 8
      </BaseAlert>
    </div>

    <div v-else-if="localMethod === 'roll'" class="space-y-4">
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
            v-model="localScores[ability.key]"
            :min="localMethod === 'point-buy' ? 8 : 3"
            :max="localMethod === 'point-buy' ? 15 : 18"
            :disabled="localMethod === 'standard-array'"
            class="w-20"
          />
          <div class="text-sm">
            <span class="text-foreground/60">Mod:</span>
            <span class="font-medium ml-1">
              {{ getModifier(localScores[ability.key]) >= 0 ? '+' : ''
              }}{{ getModifier(localScores[ability.key]) }}
            </span>
          </div>
        </div>
        <div
          v-if="localMethod === 'roll' && rollResults[ability.key]"
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
          variant="secondary"
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
  pointBuyRemaining: number
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

// Computed properties for two-way binding
const localMethod = computed({
  get: () => props.modelValue.ability_score_method,
  set: value =>
    emit('update:modelValue', {
      ...props.modelValue,
      ability_score_method: value,
    }),
})

const localScores = computed({
  get: () => ({
    strength: props.modelValue.strength,
    dexterity: props.modelValue.dexterity,
    constitution: props.modelValue.constitution,
    intelligence: props.modelValue.intelligence,
    wisdom: props.modelValue.wisdom,
    charisma: props.modelValue.charisma,
  }),
  set: scores => emit('update:modelValue', { ...props.modelValue, ...scores }),
})

// Methods
function getModifier(score: number): number {
  return Math.floor((score - 10) / 2)
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
  const newScores: Record<string, number> = {}
  const newResults: Record<string, number[]> = {}

  abilities.forEach(ability => {
    const result = rollAbilityScore()
    newScores[ability.key] = result.total
    newResults[ability.key] = result.rolls
  })

  rollResults.value = newResults
  emit('update:modelValue', { ...props.modelValue, ...newScores })
}

// Watch for method changes
watch(localMethod, newMethod => {
  if (newMethod === 'standard-array') {
    // Auto-assign standard array in order
    const newScores: Record<string, number> = {}
    abilities.forEach((ability, index) => {
      newScores[ability.key] = standardArray[index]
    })
    emit('update:modelValue', { ...props.modelValue, ...newScores })
  } else if (newMethod === 'point-buy') {
    // Reset to all 10s for point buy
    const newScores: Record<string, number> = {}
    abilities.forEach(ability => {
      newScores[ability.key] = 10
    })
    emit('update:modelValue', { ...props.modelValue, ...newScores })
  }
})
</script>
