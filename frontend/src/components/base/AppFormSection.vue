<template>
  <div class="space-y-4">
    <div
      v-if="title || description || collapsible || $slots.actions"
      class="flex items-start justify-between"
    >
      <div class="flex-1">
        <h3
          v-if="title"
          class="text-lg font-semibold text-foreground"
          :class="{ 'cursor-pointer select-none': collapsible }"
          @click="collapsible && toggleCollapsed()"
        >
          {{ title }}
        </h3>
        <p v-if="description" class="mt-1 text-sm text-foreground/60">
          {{ description }}
        </p>
      </div>
      <div class="flex items-center space-x-2 ml-4">
        <!-- Actions slot for buttons -->
        <slot name="actions" />
        <!-- Collapse button -->
        <button
          v-if="collapsible"
          type="button"
          class="p-1 text-foreground/60 hover:text-foreground transition-colors"
          @click="toggleCollapsed"
        >
          <svg
            class="w-5 h-5 transition-transform"
            :class="{ 'rotate-180': !isCollapsed }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      </div>
    </div>

    <transition
      name="collapse"
      @enter="onEnter"
      @after-enter="onAfterEnter"
      @leave="onLeave"
    >
      <div v-show="!isCollapsed" ref="content">
        <slot />
      </div>
    </transition>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'

export interface AppFormSectionProps {
  title?: string
  description?: string
  collapsible?: boolean
  defaultCollapsed?: boolean
}

const props = withDefaults(defineProps<AppFormSectionProps>(), {
  collapsible: false,
  defaultCollapsed: false,
  title: undefined,
  description: undefined,
})

const emit = defineEmits<{
  toggle: [collapsed: boolean]
}>()

const isCollapsed = ref(props.defaultCollapsed)
const content = ref<HTMLElement>()

const toggleCollapsed = () => {
  isCollapsed.value = !isCollapsed.value
  emit('toggle', isCollapsed.value)
}

const onEnter = (el: Element) => {
  const element = el as HTMLElement
  element.style.height = '0'
  element.style.overflow = 'hidden'
  element.offsetHeight // Force reflow
  element.style.height = element.scrollHeight + 'px'
}

const onAfterEnter = (el: Element) => {
  const element = el as HTMLElement
  element.style.height = ''
  element.style.overflow = ''
}

const onLeave = (el: Element) => {
  const element = el as HTMLElement
  element.style.height = element.scrollHeight + 'px'
  element.style.overflow = 'hidden'
  element.offsetHeight // Force reflow
  element.style.height = '0'
}
</script>

<style scoped>
.collapse-enter-active,
.collapse-leave-active {
  transition: height 0.3s ease;
}
</style>
