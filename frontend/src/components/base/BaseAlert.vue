<template>
  <Transition name="alert">
    <div v-if="visible" :class="[alertClasses, borderClasses]" role="alert">
      <div class="flex">
        <div v-if="showIcon" class="flex-shrink-0">
          <component :is="iconComponent" class="h-5 w-5" />
        </div>
        <div class="flex-1" :class="{ 'ml-3': showIcon }">
          <h3 v-if="title" class="font-medium" :class="titleClasses">
            {{ title }}
          </h3>
          <div
            v-if="$slots.default"
            class="text-sm"
            :class="[contentClasses, { 'mt-1': title }]"
          >
            <slot />
          </div>
        </div>
        <div v-if="dismissible" class="flex-shrink-0 ml-4">
          <button
            type="button"
            :class="dismissButtonClasses"
            @click="$emit('dismiss')"
          >
            <span class="sr-only">Dismiss</span>
            <svg
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ErrorIcon from './icons/ErrorIcon.vue'
import InfoIcon from './icons/InfoIcon.vue'
import SuccessIcon from './icons/SuccessIcon.vue'
import WarningIcon from './icons/WarningIcon.vue'

interface Props {
  variant?: 'info' | 'success' | 'warning' | 'error'
  title?: string
  visible?: boolean
  dismissible?: boolean
  showIcon?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'info',
  title: undefined,
  visible: true,
  dismissible: false,
  showIcon: true,
})

defineEmits<{
  dismiss: []
}>()

const alertClasses = computed(() => {
  const base = 'p-4 rounded-lg transition-all duration-300'

  const variants = {
    info: 'bg-blue-50 dark:bg-blue-900/20',
    success: 'bg-green-50 dark:bg-green-900/20',
    warning: 'bg-yellow-50 dark:bg-yellow-900/20',
    error: 'bg-red-50 dark:bg-red-900/20',
  }

  return [base, variants[props.variant]]
})

const borderClasses = computed(() => {
  const variants = {
    info: 'border border-blue-200 dark:border-blue-800',
    success: 'border border-green-200 dark:border-green-800',
    warning: 'border border-yellow-200 dark:border-yellow-800',
    error: 'border border-red-200 dark:border-red-800',
  }

  return variants[props.variant]
})

const titleClasses = computed(() => {
  const variants = {
    info: 'text-blue-800 dark:text-blue-300',
    success: 'text-green-800 dark:text-green-300',
    warning: 'text-yellow-800 dark:text-yellow-300',
    error: 'text-red-800 dark:text-red-300',
  }

  return variants[props.variant]
})

const contentClasses = computed(() => {
  const variants = {
    info: 'text-blue-700 dark:text-blue-200',
    success: 'text-green-700 dark:text-green-200',
    warning: 'text-yellow-700 dark:text-yellow-200',
    error: 'text-red-700 dark:text-red-200',
  }

  return variants[props.variant]
})

const dismissButtonClasses = computed(() => {
  const variants = {
    info: 'text-blue-400 hover:text-blue-500',
    success: 'text-green-400 hover:text-green-500',
    warning: 'text-yellow-400 hover:text-yellow-500',
    error: 'text-red-400 hover:text-red-500',
  }

  return [
    'inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-300',
    variants[props.variant],
  ]
})

const iconComponent = computed(() => {
  const icons = {
    info: InfoIcon,
    success: SuccessIcon,
    warning: WarningIcon,
    error: ErrorIcon,
  }

  return icons[props.variant]
})
</script>

<style scoped>
.alert-enter-active,
.alert-leave-active {
  transition: all 0.3s ease;
}

.alert-enter-from {
  transform: translateY(-10px);
  opacity: 0;
}

.alert-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
</style>
