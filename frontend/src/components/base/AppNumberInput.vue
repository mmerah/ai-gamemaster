<template>
  <div class="space-y-1">
    <label v-if="label" class="block text-sm font-medium text-foreground">
      {{ label }}
    </label>
    <div class="flex items-center">
      <button
        type="button"
        class="px-3 py-2 border border-border rounded-l-md bg-background hover:bg-card transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="disabled || (min !== undefined && modelValue <= min)"
        @click="decrement"
      >
        <svg
          class="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M20 12H4"
          />
        </svg>
      </button>
      <input
        :id="inputId"
        type="number"
        :value="modelValue"
        :min="min"
        :max="max"
        :step="step"
        :disabled="disabled"
        :placeholder="placeholder"
        class="flex-1 px-3 py-2 text-center border-y border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        @input="handleInput"
        @blur="handleBlur"
      />
      <button
        type="button"
        class="px-3 py-2 border border-border rounded-r-md bg-background hover:bg-card transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="disabled || (max !== undefined && modelValue >= max)"
        @click="increment"
      >
        <svg
          class="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
      </button>
    </div>
    <p v-if="hint" class="text-sm text-foreground/60">{{ hint }}</p>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

export interface AppNumberInputProps {
  modelValue: number
  label?: string
  placeholder?: string
  min?: number
  max?: number
  step?: number
  disabled?: boolean
  hint?: string
  error?: string
}

const props = withDefaults(defineProps<AppNumberInputProps>(), {
  label: undefined,
  placeholder: undefined,
  min: undefined,
  max: undefined,
  step: 1,
  disabled: false,
  hint: undefined,
  error: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const inputId = computed(
  () => `number-input-${Math.random().toString(36).substr(2, 9)}`
)

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)

  if (!isNaN(value)) {
    emit('update:modelValue', value)
  }
}

const handleBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)

  if (isNaN(value)) {
    emit('update:modelValue', props.min ?? 0)
  } else if (props.min !== undefined && value < props.min) {
    emit('update:modelValue', props.min)
  } else if (props.max !== undefined && value > props.max) {
    emit('update:modelValue', props.max)
  }
}

const increment = () => {
  const newValue = props.modelValue + props.step
  if (props.max === undefined || newValue <= props.max) {
    emit('update:modelValue', newValue)
  }
}

const decrement = () => {
  const newValue = props.modelValue - props.step
  if (props.min === undefined || newValue >= props.min) {
    emit('update:modelValue', newValue)
  }
}
</script>
