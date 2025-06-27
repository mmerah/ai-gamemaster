<template>
  <div>
    <label
      v-if="label"
      :for="inputId"
      class="block text-sm font-medium text-foreground mb-1"
    >
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <input
      :id="inputId"
      :value="modelValue"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :class="inputClasses"
      v-bind="$attrs"
      @input="
        $emit('update:modelValue', ($event.target as HTMLInputElement).value)
      "
    />
    <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>
    <p v-if="hint && !error" class="mt-1 text-sm text-foreground/60">
      {{ hint }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  type?: string
  disabled?: boolean
  required?: boolean
  error?: string
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: undefined,
  label: undefined,
  placeholder: undefined,
  type: 'text',
  disabled: false,
  required: false,
  error: undefined,
  hint: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

// Generate unique ID for label association
const inputId = computed(
  () => `input-${Math.random().toString(36).substr(2, 9)}`
)

const inputClasses = computed(() => {
  const base =
    'w-full px-3 py-2 border rounded-md bg-background text-foreground placeholder-foreground/50 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed'

  const errorClass = props.error ? 'border-red-500' : 'border-border'

  return [base, errorClass]
})
</script>
