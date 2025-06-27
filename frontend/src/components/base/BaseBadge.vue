<template>
  <span :class="[badgeClasses, sizeClasses]" v-bind="$attrs">
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'md',
})

const badgeClasses = computed(() => {
  const base =
    'inline-flex items-center font-medium rounded-full transition-colors duration-300'

  const variants = {
    default: 'bg-card text-foreground border border-border',
    primary: 'bg-primary text-primary-foreground',
    success: 'bg-green-600 text-white',
    warning: 'bg-yellow-600 text-white',
    danger: 'bg-red-600 text-white',
    info: 'bg-blue-600 text-white',
  }

  return [base, variants[props.variant]]
})

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-0.5',
    lg: 'text-base px-3 py-1',
  }
  return sizes[props.size]
})
</script>
