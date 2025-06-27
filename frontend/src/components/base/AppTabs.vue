<template>
  <div class="space-y-4">
    <div
      class="flex border-b border-border"
      :class="{ 'justify-center': center }"
    >
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="px-4 py-2 font-medium transition-colors relative"
        :class="[
          activeTab === tab.id
            ? 'text-primary border-b-2 border-primary'
            : 'text-foreground/60 hover:text-foreground',
          { 'opacity-50 cursor-not-allowed': tab.disabled },
        ]"
        :disabled="tab.disabled"
        @click="!tab.disabled && $emit('update:activeTab', tab.id)"
      >
        <div class="flex items-center gap-2">
          <span v-if="tab.icon" class="text-lg">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
          <BaseBadge v-if="tab.badge" variant="secondary" class="ml-2">
            {{ tab.badge }}
          </BaseBadge>
        </div>
      </button>
    </div>
    <div v-if="$slots.default" class="tab-content">
      <slot />
    </div>
  </div>
</template>

<script lang="ts" setup>
import BaseBadge from './BaseBadge.vue'

export interface Tab {
  id: string
  label: string
  icon?: string
  badge?: string | number
  disabled?: boolean
}

export interface AppTabsProps {
  tabs: Tab[]
  activeTab: string
  center?: boolean
}

defineProps<AppTabsProps>()

defineEmits<{
  'update:activeTab': [tabId: string]
}>()
</script>
