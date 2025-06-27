<template>
  <div :class="[panelClasses, paddingClasses]" v-bind="$attrs">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  padding?: 'sm' | 'md' | 'lg' | 'none'
  variant?: 'default' | 'transparent'
}

const props = withDefaults(defineProps<Props>(), {
  padding: 'md',
  variant: 'default',
})

const panelClasses = computed(() => {
  const base = 'rounded-lg transition-all duration-300'

  const variants = {
    default: 'bg-card/90 backdrop-blur-sm border border-border/20',
    transparent: 'bg-transparent',
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
