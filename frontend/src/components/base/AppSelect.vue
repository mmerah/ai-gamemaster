<template>
  <div class="space-y-1">
    <label
      v-if="label"
      :for="inputId"
      class="block text-sm font-medium text-foreground"
    >
      {{ label }}
    </label>
    <select
      :id="inputId"
      :value="modelValue"
      class="w-full px-3 py-2 bg-card text-foreground border border-border rounded-md focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-300"
      :class="{
        'border-red-500 focus:ring-red-500 focus:border-red-500': error,
        'opacity-50 cursor-not-allowed': disabled,
      }"
      :disabled="disabled"
      v-bind="$attrs"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <slot />
    </select>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    <p v-if="hint && !error" class="text-sm text-foreground/60">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue?: string | number
  label?: string
  disabled?: boolean
  error?: string
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  disabled: false,
  error: '',
  hint: '',
})

defineEmits<{
  'update:modelValue': [value: string | number]
}>()

// Generate unique ID for accessibility
const inputId = computed(
  () => `app-select-${Math.random().toString(36).slice(2, 9)}`
)
</script>
