<template>
  <component :is="as" :class="[cardClasses, paddingClasses]" v-bind="$attrs">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  padding?: 'sm' | 'md' | 'lg' | 'none'
  as?: string
  variant?: 'default' | 'subtle'
}

const props = withDefaults(defineProps<Props>(), {
  padding: 'md',
  as: 'div',
  variant: 'default',
})

const cardClasses = computed(() => {
  const base =
    'bg-card text-foreground rounded-lg transition-colors duration-300'

  const variants = {
    default: 'border border-border shadow-lg',
    subtle: 'border border-border/50 shadow-sm',
  }

  return [base, variants[props.variant]]
})

const paddingClasses = computed(() => {
  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  }
  return paddings[props.padding]
})
</script>
