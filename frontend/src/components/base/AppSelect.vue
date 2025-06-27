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
      @change="onUpdate"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
        :disabled="option.disabled"
      >
        {{ option.label }}
      </option>
    </select>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    <p v-if="hint && !error" class="text-sm text-foreground/60">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
  // Add a flexible data property for other uses
  [key: string]: unknown
}

interface Props {
  modelValue?: string | number
  options: SelectOption[] // This is the new required prop
  label?: string
  placeholder?: string
  disabled?: boolean
  error?: string
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  placeholder: '',
  disabled: false,
  error: '',
  hint: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const inputId = computed(
  () => `app-select-${Math.random().toString(36).slice(2, 9)}`
)

const onUpdate = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const selectedValue = target.value
  const selectedOption = props.options.find(
    opt => String(opt.value) === selectedValue
  )

  // Emit the actual value type (number or string)
  if (selectedOption && typeof selectedOption.value === 'number') {
    emit('update:modelValue', Number(selectedValue))
  } else {
    emit('update:modelValue', selectedValue)
  }
}
</script>
