<template>
  <div>
    <label
      v-if="label"
      :for="textareaId"
      class="block text-sm font-medium text-foreground mb-1"
    >
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <textarea
      :id="textareaId"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :rows="rows"
      :class="textareaClasses"
      v-bind="$attrs"
      @input="
        $emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)
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
  modelValue?: string
  label?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
  rows?: number
  error?: string
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  required: false,
  rows: 3,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

// Generate unique ID for label association
const textareaId = computed(
  () => `textarea-${Math.random().toString(36).substr(2, 9)}`
)

const textareaClasses = computed(() => {
  const base =
    'w-full px-3 py-2 border rounded-md bg-background text-foreground placeholder-foreground/50 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed resize-none'

  const errorClass = props.error ? 'border-red-500' : 'border-border'

  return [base, errorClass]
})
</script>
