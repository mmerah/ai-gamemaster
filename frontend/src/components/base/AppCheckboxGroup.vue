<template>
  <div class="space-y-2">
    <div
      v-if="label || showSelectAll"
      class="flex items-center justify-between"
    >
      <label v-if="label" class="text-sm font-medium text-foreground">
        {{ label }}
      </label>
      <div v-if="showSelectAll" class="flex gap-2">
        <button
          type="button"
          class="text-sm text-primary hover:text-primary/80 transition-colors"
          @click="selectAll"
        >
          Select All
        </button>
        <span class="text-foreground/40">|</span>
        <button
          type="button"
          class="text-sm text-primary hover:text-primary/80 transition-colors"
          @click="selectNone"
        >
          Select None
        </button>
      </div>
    </div>
    <div
      class="grid gap-2"
      :class="{
        'grid-cols-1': columns === 1,
        'grid-cols-2': columns === 2,
        'grid-cols-3': columns === 3,
        'grid-cols-4': columns === 4,
      }"
    >
      <label
        v-for="option in options"
        :key="option.value"
        class="flex items-start space-x-2 cursor-pointer"
        :class="{ 'opacity-50 cursor-not-allowed': option.disabled }"
      >
        <input
          type="checkbox"
          :value="option.value"
          :checked="modelValue.includes(option.value)"
          :disabled="
            disabled ||
            option.disabled ||
            (maxSelections &&
              !modelValue.includes(option.value) &&
              modelValue.length >= maxSelections)
          "
          class="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background disabled:cursor-not-allowed"
          @change="handleChange(option.value)"
        />
        <div class="flex-1">
          <span class="text-sm text-foreground">{{ option.label }}</span>
          <p v-if="option.description" class="text-xs text-foreground/60">
            {{ option.description }}
          </p>
        </div>
      </label>
    </div>
    <p v-if="hint || selectionHint" class="text-sm text-foreground/60">
      {{ hint }}{{ hint && selectionHint ? ' • ' : '' }}{{ selectionHint }}
    </p>
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
export interface CheckboxOption {
  value: string
  label: string
  description?: string
  disabled?: boolean
}

export interface AppCheckboxGroupProps {
  modelValue: string[]
  options: CheckboxOption[]
  label?: string
  columns?: 1 | 2 | 3 | 4
  disabled?: boolean
  showSelectAll?: boolean
  maxSelections?: number
  hint?: string
  error?: string
}

const props = withDefaults(defineProps<AppCheckboxGroupProps>(), {
  columns: 1,
  showSelectAll: true,
  label: undefined,
  disabled: false,
  maxSelections: undefined,
  hint: undefined,
  error: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const handleChange = (value: string) => {
  const currentValues = [...props.modelValue]
  const index = currentValues.indexOf(value)

  if (index > -1) {
    currentValues.splice(index, 1)
  } else {
    // Check if we've reached the max selections limit
    if (props.maxSelections && currentValues.length >= props.maxSelections) {
      return
    }
    currentValues.push(value)
  }

  emit('update:modelValue', currentValues)
}

const selectAll = () => {
  let allValues = props.options
    .filter(option => !option.disabled)
    .map(option => option.value)

  // Respect maxSelections limit
  if (props.maxSelections && allValues.length > props.maxSelections) {
    allValues = allValues.slice(0, props.maxSelections)
  }

  emit('update:modelValue', allValues)
}

const selectNone = () => {
  emit('update:modelValue', [])
}

const selectionHint = computed(() => {
  if (props.maxSelections) {
    return `${props.modelValue.length} / ${props.maxSelections} selected`
  }
  return ''
})
</script>
