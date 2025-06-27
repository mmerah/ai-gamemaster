<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-300"
          @click="handleBackdropClick"
        />

        <!-- Modal Container -->
        <div
          class="relative w-full transition-all duration-300 transform"
          :class="sizeClasses"
        >
          <AppCard
            padding="none"
            class="max-h-[90vh] overflow-hidden flex flex-col"
          >
            <!-- Header -->
            <div
              v-if="$slots.header || title"
              class="px-6 py-4 border-b border-border flex items-center justify-between"
            >
              <slot name="header">
                <h2 class="text-xl font-semibold text-foreground">
                  {{ title }}
                </h2>
              </slot>
              <button
                v-if="showCloseButton"
                class="text-foreground/60 hover:text-foreground transition-colors duration-300"
                @click="$emit('close')"
              >
                <svg
                  class="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
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

            <!-- Body -->
            <div class="flex-1 overflow-y-auto px-6 py-4">
              <slot />
            </div>

            <!-- Footer -->
            <div v-if="$slots.footer" class="px-6 py-4 border-t border-border">
              <slot name="footer" />
            </div>
          </AppCard>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppCard from './AppCard.vue'

interface Props {
  visible: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  showCloseButton?: boolean
  closeOnBackdrop?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showCloseButton: true,
  closeOnBackdrop: true,
})

const emit = defineEmits<{
  close: []
}>()

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
    full: 'max-w-full mx-4',
  }
  return sizes[props.size]
})

const handleBackdropClick = () => {
  if (props.closeOnBackdrop) {
    emit('close')
  }
}
</script>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.3s ease;
}

.modal-enter-from .relative {
  transform: scale(0.9);
}

.modal-leave-to .relative {
  transform: scale(0.9);
}
</style>
